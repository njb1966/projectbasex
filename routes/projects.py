import json
import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from database import get_db
from utils.embeddings import embed_note
from utils.git import get_git_info, get_recent_commits

projects_bp = Blueprint('projects', __name__)

VALID_STATUSES = ['idea', 'planning', 'active', 'needs-attention', 'idle-review', 'paused', 'completed', 'archived']
VALID_CATEGORIES = ['code', 'web', 'business', 'writing']


def _next_id(db):
    rows = db.execute("SELECT id FROM projects WHERE id LIKE 'PRJ-%'").fetchall()
    if rows:
        max_num = max(int(r['id'].split('-')[1]) for r in rows)
        return f"PRJ-{max_num + 1:03d}"
    return "PRJ-001"


@projects_bp.route('/projects/new', methods=['GET', 'POST'])
def new_project():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            return render_template('project_new.html',
                                   error='Project name is required.',
                                   valid_statuses=VALID_STATUSES,
                                   valid_categories=VALID_CATEGORIES,
                                   form=request.form)
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as db:
            new_id = _next_id(db)
            db.execute("""
                INSERT INTO projects
                (id, name, description, status, category, priority,
                 original_plan, directory_path, created_date, last_modified, tags, tech_stack)
                VALUES (?, ?, ?, ?, ?, 'P3', ?, ?, ?, ?, '[]', '[]')
            """, (
                new_id,
                name,
                request.form.get('description', ''),
                request.form.get('status', 'idea'),
                request.form.get('category', 'code'),
                request.form.get('original_plan', ''),
                request.form.get('directory_path', ''),
                now,
                now,
            ))
            db.execute(
                "INSERT INTO timeline (id, project_id, event_type, description, timestamp) VALUES (?, ?, 'created', 'Project created', ?)",
                (str(uuid.uuid4()), new_id, now)
            )
        return redirect(url_for('projects.detail', project_id=new_id))

    return render_template('project_new.html',
                           valid_statuses=VALID_STATUSES,
                           valid_categories=VALID_CATEGORIES,
                           form={})


@projects_bp.route('/projects/<project_id>')
def detail(project_id):
    with get_db() as db:
        project = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not project:
            return "Project not found", 404
        notes = db.execute(
            "SELECT * FROM notes WHERE project_id = ? ORDER BY created_date DESC",
            (project_id,)
        ).fetchall()
        timeline = db.execute(
            "SELECT * FROM timeline WHERE project_id = ? ORDER BY timestamp DESC LIMIT 30",
            (project_id,)
        ).fetchall()

    project = dict(project)
    project['tags'] = json.loads(project.get('tags') or '[]')
    project['tech_stack'] = json.loads(project.get('tech_stack') or '[]')

    git_info    = get_git_info(project.get('directory_path'))
    git_commits = get_recent_commits(project.get('directory_path'))

    return render_template(
        'project_detail.html',
        project=project,
        notes=[dict(n) for n in notes],
        timeline=[_parse_timeline_event(dict(t)) for t in timeline],
        valid_statuses=VALID_STATUSES,
        valid_categories=VALID_CATEGORIES,
        git_info=git_info,
        git_commits=git_commits,
    )


@projects_bp.route('/projects/<project_id>/edit', methods=['POST'])
def edit_project(project_id):
    now = datetime.now(timezone.utc).isoformat()
    raw_stack = request.form.get('tech_stack', '')
    tech_stack = json.dumps([t.strip() for t in raw_stack.split(',') if t.strip()])

    raw_tags = request.form.get('tags', '')
    tags = json.dumps([t.strip() for t in raw_tags.split(',') if t.strip()])

    with get_db() as db:
        db.execute("""
            UPDATE projects
            SET description = ?, original_plan = ?, directory_path = ?, tech_stack = ?, tags = ?, last_modified = ?
            WHERE id = ?
        """, (
            request.form.get('description', ''),
            request.form.get('original_plan', ''),
            request.form.get('directory_path', ''),
            tech_stack,
            tags,
            now,
            project_id,
        ))
    return redirect(url_for('projects.detail', project_id=project_id) + '?tab=overview')


@projects_bp.route('/projects/<project_id>/status', methods=['POST'])
def update_status(project_id):
    data = request.get_json()
    new_status = data.get('status')
    reason = (data.get('reason') or '').strip()

    if new_status not in VALID_STATUSES:
        return jsonify({'error': 'Invalid status'}), 400

    now = datetime.now(timezone.utc).isoformat()
    with get_db() as db:
        old = db.execute("SELECT status FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not old:
            return jsonify({'error': 'Not found'}), 404

        db.execute(
            "UPDATE projects SET status = ?, last_modified = ? WHERE id = ?",
            (new_status, now, project_id)
        )

        desc = f"Status: {old['status']} → {new_status}"
        if reason:
            desc += f" ({reason})"
        db.execute(
            "INSERT INTO timeline (id, project_id, event_type, description, timestamp) VALUES (?, ?, 'status_change', ?, ?)",
            (str(uuid.uuid4()), project_id, desc, now)
        )

    return jsonify({'status': new_status, 'ok': True})


@projects_bp.route('/projects/<project_id>/notes', methods=['POST'])
def add_note(project_id):
    data = request.get_json()
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'Content required'}), 400

    now = datetime.now(timezone.utc).isoformat()
    note_id = str(uuid.uuid4())
    with get_db() as db:
        db.execute(
            "INSERT INTO notes (id, project_id, content, created_date) VALUES (?, ?, ?, ?)",
            (note_id, project_id, content, now)
        )
        db.execute("UPDATE projects SET last_modified = ? WHERE id = ?", (now, project_id))

    with get_db() as db:
        db.execute(
            "INSERT INTO timeline (id, project_id, event_type, description, timestamp) VALUES (?, ?, 'note_added', ?, ?)",
            (str(uuid.uuid4()), project_id, content[:120] + ('…' if len(content) > 120 else ''), now)
        )

    embed_note(project_id, note_id, content)

    return jsonify({'id': note_id, 'content': content, 'created_date': now, 'ok': True})


@projects_bp.route('/projects/<project_id>/notes/<note_id>', methods=['DELETE'])
def delete_note(project_id, note_id):
    with get_db() as db:
        db.execute("DELETE FROM notes WHERE id = ? AND project_id = ?", (note_id, project_id))
    return jsonify({'ok': True})


def _parse_timeline_event(event):
    """Add parsed fields to a timeline event dict for richer template rendering."""
    if event['event_type'] == 'status_change':
        desc = event['description']
        # Format: "Status: old → new" or "Status: old → new (reason)"
        try:
            body = desc.replace('Status: ', '')
            reason = None
            if ' (' in body and body.endswith(')'):
                arrow_part, reason = body.rsplit(' (', 1)
                reason = reason.rstrip(')')
            else:
                arrow_part = body
            parts = arrow_part.split(' → ')
            event['status_from'] = parts[0].strip() if len(parts) == 2 else None
            event['status_to']   = parts[1].strip() if len(parts) == 2 else None
            event['reason']      = reason
        except Exception:
            event['status_from'] = event['status_to'] = event['reason'] = None
    return event
