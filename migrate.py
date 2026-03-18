#!/usr/bin/env python3
"""
One-time migration from ~/ai-pm/db/projects.json into ProjectBaseX SQLite.
Safe to re-run — uses INSERT OR IGNORE on project IDs.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from database import get_db, init_db

SOURCE = os.path.expanduser('~/ai-pm/db/projects.json')

STATUS_MAP = {
    'review':    'idle-review',
    'active':    'active',
    'paused':    'paused',
    'archived':  'archived',
    'completed': 'completed',
    'intake':    'idea',
}

def migrate():
    if not os.path.exists(SOURCE):
        print(f"Source not found: {SOURCE}")
        return

    init_db()

    with open(SOURCE) as f:
        data = json.load(f)

    projects = data.get('projects', [])
    migrated = 0
    skipped = 0

    with get_db() as db:
        for p in projects:
            status = STATUS_MAP.get(p.get('status', 'idea'), p.get('status', 'idea'))
            tags = json.dumps(p.get('tags', []))
            tech_stack = json.dumps(p.get('tech_stack', []))
            created = p.get('created_date') or datetime.now(timezone.utc).isoformat()
            last_modified = created

            try:
                result = db.execute("""
                    INSERT OR IGNORE INTO projects
                    (id, name, slug, description, status, category, priority,
                     original_plan, directory_path, created_date, last_modified,
                     completed_date, tags, tech_stack)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p['id'],
                    p['name'],
                    p.get('slug', ''),
                    p.get('description', ''),
                    status,
                    p.get('category', 'code'),
                    p.get('priority', 'P3'),
                    None,
                    p.get('repository', ''),
                    created,
                    last_modified,
                    p.get('completed_date') or None,
                    tags,
                    tech_stack,
                ))

                if result.rowcount == 0:
                    skipped += 1
                    continue

                # Migrate notes field as a seed note if non-empty
                notes_text = (p.get('notes') or '').strip()
                if notes_text:
                    db.execute(
                        "INSERT INTO notes (id, project_id, content, created_date) VALUES (?, ?, ?, ?)",
                        (str(uuid.uuid4()), p['id'], notes_text, created)
                    )

                # Seed timeline with creation event
                db.execute(
                    "INSERT INTO timeline (id, project_id, event_type, description, timestamp) VALUES (?, ?, 'created', 'Project migrated from ai-pm', ?)",
                    (str(uuid.uuid4()), p['id'], created)
                )

                migrated += 1

            except Exception as e:
                print(f"  ERROR {p.get('id', '?')}: {e}")
                skipped += 1

    print(f"Done: {migrated} migrated, {skipped} skipped.")

if __name__ == '__main__':
    migrate()
