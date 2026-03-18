import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify
from database import get_db

ideas_bp = Blueprint('ideas', __name__)

VALID_IDEA_STATUSES = ['new', 'exploring', 'implemented', 'rejected']


@ideas_bp.route('/ideas')
def index():
    with get_db() as db:
        ideas = db.execute("""
            SELECT i.*, p.name as project_name
            FROM ideas i
            LEFT JOIN projects p ON i.related_project_id = p.id
            ORDER BY i.captured_date DESC
        """).fetchall()
        projects = db.execute(
            "SELECT id, name FROM projects WHERE status NOT IN ('completed', 'archived') ORDER BY name"
        ).fetchall()

    return render_template(
        'ideas.html',
        ideas=[dict(i) for i in ideas],
        projects=[dict(p) for p in projects],
    )


@ideas_bp.route('/ideas', methods=['POST'])
def create():
    data = request.get_json()
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'Title required'}), 400

    now = datetime.now(timezone.utc).isoformat()
    idea_id = str(uuid.uuid4())
    with get_db() as db:
        db.execute("""
            INSERT INTO ideas (id, title, description, sparked_by, related_project_id, captured_date, status)
            VALUES (?, ?, ?, ?, ?, ?, 'new')
        """, (
            idea_id,
            title,
            data.get('description', ''),
            data.get('sparked_by', ''),
            data.get('related_project_id') or None,
            now,
        ))

    return jsonify({'id': idea_id, 'title': title, 'ok': True})


@ideas_bp.route('/ideas/<idea_id>/status', methods=['POST'])
def update_status(idea_id):
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in VALID_IDEA_STATUSES:
        return jsonify({'error': 'Invalid status'}), 400
    with get_db() as db:
        db.execute("UPDATE ideas SET status = ? WHERE id = ?", (new_status, idea_id))
    return jsonify({'ok': True})
