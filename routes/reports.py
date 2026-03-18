"""
Activity reports: weekly and monthly summary views.
"""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request
from database import get_db

reports_bp = Blueprint('reports', __name__)

PERIOD_DAYS = {'week': 7, 'month': 30}

STATUS_ORDER = ['needs-attention', 'active', 'planning', 'idea', 'idle-review', 'paused', 'completed', 'archived']


@reports_bp.route('/reports')
def summary():
    period = request.args.get('period', 'week')
    if period not in PERIOD_DAYS:
        period = 'week'

    days = PERIOD_DAYS[period]
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    with get_db() as db:
        # All projects (for portfolio snapshot)
        all_projects = [dict(r) for r in db.execute(
            "SELECT id, name, status, category, last_modified, created_date FROM projects ORDER BY name"
        ).fetchall()]

        # Notes added in period
        notes = db.execute(
            """
            SELECT n.id, n.project_id, n.content, n.created_date, p.name AS project_name
            FROM notes n
            JOIN projects p ON p.id = n.project_id
            WHERE n.created_date >= ?
            ORDER BY n.created_date DESC
            """,
            (cutoff,)
        ).fetchall()

        # Timeline events in period (status changes, created)
        events = db.execute(
            """
            SELECT t.event_type, t.description, t.timestamp, t.project_id, p.name AS project_name
            FROM timeline t
            JOIN projects p ON p.id = t.project_id
            WHERE t.timestamp >= ?
            ORDER BY t.timestamp DESC
            """,
            (cutoff,)
        ).fetchall()

    # Portfolio health breakdown
    status_counts = {}
    for p in all_projects:
        s = p['status']
        status_counts[s] = status_counts.get(s, 0) + 1

    health = [
        {'status': s, 'count': status_counts.get(s, 0)}
        for s in STATUS_ORDER
        if status_counts.get(s, 0) > 0
    ]

    # Group notes by project
    notes_by_project = {}
    for n in notes:
        pid = n['project_id']
        if pid not in notes_by_project:
            notes_by_project[pid] = {'name': n['project_name'], 'notes': []}
        notes_by_project[pid]['notes'].append(dict(n))

    # Active projects touched in period (has notes or events)
    touched_ids = {n['project_id'] for n in notes} | {e['project_id'] for e in events}

    return render_template(
        'reports.html',
        period=period,
        days=days,
        notes=notes,
        events=[dict(e) for e in events],
        notes_by_project=notes_by_project,
        health=health,
        total_projects=len(all_projects),
        touched_count=len(touched_ids),
    )
