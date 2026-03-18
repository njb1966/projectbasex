import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_PATH = os.environ.get(
        'DB_PATH',
        os.path.join(os.path.dirname(__file__), 'db', 'projectbasex.db')
    )
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-local-secret-change-for-production')
    DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'
    PORT = int(os.environ.get('PORT', '5000'))
    PROJECTS_ROOT = os.environ.get('PROJECTS_ROOT', os.path.expanduser('~/Projects'))
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    AI_MODEL = os.environ.get('AI_MODEL', 'claude-sonnet-4-6')
