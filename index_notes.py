#!/usr/bin/env python3
"""
Index all existing notes for RAG retrieval.
Run once after upgrading to Phase 3, then notes auto-index on creation.

Usage:
    venv/bin/python index_notes.py
    venv/bin/python index_notes.py PRJ-005   # single project
"""
import sys
from database import init_db, get_db
from utils.embeddings import embed_note, ollama_available

def main():
    if not ollama_available():
        print("Ollama is not running. Start it with: ollama serve")
        sys.exit(1)

    init_db()

    project_filter = sys.argv[1] if len(sys.argv) > 1 else None

    with get_db() as db:
        if project_filter:
            notes = db.execute(
                "SELECT id, project_id, content FROM notes WHERE project_id=?",
                (project_filter,)
            ).fetchall()
        else:
            notes = db.execute("SELECT id, project_id, content FROM notes").fetchall()

        already = set(
            r['source_ref'] for r in
            db.execute("SELECT source_ref FROM embeddings WHERE source_type='note'").fetchall()
        )

    to_index = [n for n in notes if n['id'] not in already]
    total    = len(to_index)

    if total == 0:
        print("All notes already indexed.")
        return

    print(f"Indexing {total} notes...")
    for i, note in enumerate(to_index, 1):
        print(f"  [{i}/{total}] {note['project_id']} — {note['content'][:50].strip()!r}")
        embed_note(note['project_id'], note['id'], note['content'])

    print(f"Done. {total} notes indexed.")

if __name__ == '__main__':
    main()
