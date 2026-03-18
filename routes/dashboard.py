from flask import Blueprint, render_template
from database import get_db
from utils.recommendations import recommend
from utils.git import is_git_repo

dashboard_bp = Blueprint('dashboard', __name__)

STATUSES = ['needs-attention', 'active', 'planning', 'idea', 'idle-review', 'paused', 'completed', 'archived']
COLLAPSED_BY_DEFAULT = {'completed', 'archived'}


@dashboard_bp.route('/')
def index():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM projects ORDER BY last_modified DESC, created_date DESC"
        ).fetchall()

    projects = [dict(r) for r in rows]
    grouped = {s: [] for s in STATUSES}

    for p in projects:
        s = p['status']
        if s not in grouped:
            grouped[s] = []
        grouped[s].append(p)

    stats = {s: len(grouped.get(s, [])) for s in STATUSES}
    recommendations = recommend(projects, top_n=3)

    # Fast git check per project (filesystem only, no subprocess)
    git_status = {p['id']: is_git_repo(p.get('directory_path')) for p in projects}

    return render_template(
        'dashboard.html',
        grouped=grouped,
        stats=stats,
        total=len(projects),
        statuses=STATUSES,
        collapsed_by_default=COLLAPSED_BY_DEFAULT,
        recommendations=recommendations,
        git_status=git_status,
    )
