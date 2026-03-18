from flask import Flask
from datetime import datetime, timezone
from config import Config
from database import init_db
from routes.dashboard import dashboard_bp
from routes.projects import projects_bp
from routes.ideas import ideas_bp
from routes.chat import chat_bp
from routes.reports import reports_bp


def timeago(dt_str):
    if not dt_str:
        return 'never'
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - dt
        days = diff.days
        if days < 0:
            return 'just now'
        if days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                mins = diff.seconds // 60
                return 'just now' if mins < 2 else f'{mins}m ago'
            return f'{hours}h ago'
        if days == 1:
            return 'yesterday'
        if days < 7:
            return f'{days} days ago'
        if days < 30:
            weeks = days // 7
            return f'{weeks}w ago'
        if days < 365:
            months = days // 30
            return f'{months}mo ago'
        return dt.strftime('%b %Y')
    except Exception:
        return dt_str


def _dateformat(dt_str):
    if not dt_str:
        return ''
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%b %-d, %Y')
    except Exception:
        return dt_str


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    init_db()

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(ideas_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(reports_bp)

    app.jinja_env.filters['timeago'] = timeago
    app.jinja_env.filters['status_label'] = lambda s: s.replace('-', ' ').title()
    app.jinja_env.filters['dateformat'] = _dateformat

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG, port=Config.PORT)
