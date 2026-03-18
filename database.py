import sqlite3
import os
from contextlib import contextmanager
from config import Config

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    slug            TEXT,
    description     TEXT,
    status          TEXT NOT NULL DEFAULT 'idea',
    category        TEXT NOT NULL DEFAULT 'code',
    priority        TEXT DEFAULT 'P3',
    original_plan   TEXT,
    directory_path  TEXT,
    created_date    TEXT,
    last_modified   TEXT,
    completed_date  TEXT,
    tags            TEXT DEFAULT '[]',
    tech_stack      TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS notes (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL,
    content         TEXT NOT NULL,
    created_date    TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ideas (
    id                  TEXT PRIMARY KEY,
    title               TEXT NOT NULL,
    description         TEXT,
    sparked_by          TEXT,
    related_project_id  TEXT,
    captured_date       TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS conversations (
    id           TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL,
    mode         TEXT NOT NULL DEFAULT 'general',
    started      TEXT NOT NULL,
    last_message TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS embeddings (
    id           TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL,
    source_type  TEXT NOT NULL,
    source_ref   TEXT,
    chunk_text   TEXT NOT NULL,
    embedding    BLOB NOT NULL,
    content_hash TEXT NOT NULL,
    created_date TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_embeddings_project ON embeddings(project_id);

CREATE TABLE IF NOT EXISTS timeline (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    description TEXT,
    timestamp   TEXT NOT NULL,
    metadata    TEXT DEFAULT '{}',
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
"""

def init_db():
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    _upgrade_db()

def _upgrade_db():
    """Add columns introduced after initial schema — safe to run repeatedly."""
    additions = [
        "ALTER TABLE messages      ADD COLUMN input_tokens  INTEGER DEFAULT 0",
        "ALTER TABLE messages      ADD COLUMN output_tokens INTEGER DEFAULT 0",
        "ALTER TABLE conversations ADD COLUMN total_input_tokens  INTEGER DEFAULT 0",
        "ALTER TABLE conversations ADD COLUMN total_output_tokens INTEGER DEFAULT 0",
    ]
    conn = sqlite3.connect(Config.DB_PATH)
    for sql in additions:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
