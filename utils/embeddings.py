"""
RAG pipeline for ProjectBaseX.

Embeddings are generated locally via Ollama (nomic-embed-text),
stored as raw float32 bytes in SQLite, and retrieved with cosine
similarity in numpy. No external API calls, no data leaves the machine.

Sources indexed:
  - notes:  each note is one chunk, re-indexed when content changes
  - files:  root-level .md/.txt files chunked by paragraph, cached by content hash
"""
import hashlib
import uuid
import numpy as np
import httpx
from datetime import datetime, timezone
from database import get_db

OLLAMA_URL  = 'http://localhost:11434/api/embeddings'
EMBED_MODEL = 'nomic-embed-text'
TOP_K       = 6
CHUNK_SIZE  = 1200   # chars per file chunk
CHUNK_OVERLAP = 150


# ─── Ollama ───────────────────────────────────────────────────────────────────

def embed_text(text):
    """Return embedding vector from Ollama. Raises on failure."""
    r = httpx.post(
        OLLAMA_URL,
        json={'model': EMBED_MODEL, 'prompt': text},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()['embedding']


def ollama_available():
    try:
        httpx.get('http://localhost:11434', timeout=2)
        return True
    except Exception:
        return False


# ─── Storage helpers ──────────────────────────────────────────────────────────

def _to_bytes(vec):
    return np.array(vec, dtype=np.float32).tobytes()

def _from_bytes(data):
    return np.frombuffer(data, dtype=np.float32)

def _hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


# ─── Indexing ─────────────────────────────────────────────────────────────────

def embed_note(project_id, note_id, content):
    """Embed a note and store it. Safe to call on every note save — no-ops if unchanged."""
    if not content.strip() or not ollama_available():
        return
    h = _hash(content)
    with get_db() as db:
        existing = db.execute(
            "SELECT content_hash FROM embeddings WHERE source_type='note' AND source_ref=?",
            (note_id,)
        ).fetchone()
        if existing and existing['content_hash'] == h:
            return  # unchanged
        try:
            vec = embed_text(content)
            db.execute("DELETE FROM embeddings WHERE source_type='note' AND source_ref=?", (note_id,))
            db.execute("""
                INSERT INTO embeddings (id, project_id, source_type, source_ref, chunk_text, embedding, content_hash, created_date)
                VALUES (?, ?, 'note', ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), project_id, note_id, content, _to_bytes(vec), h, datetime.now(timezone.utc).isoformat()))
        except Exception as e:
            print(f"[rag] embed_note failed for {note_id}: {e}")


def ensure_file_embeddings(project_id, files):
    """
    Check each file's content hash against stored embeddings.
    Re-index any file that is new or has changed.
    files: list of {'name': str, 'content': str}
    """
    if not files or not ollama_available():
        return
    with get_db() as db:
        rows = db.execute(
            "SELECT source_ref, content_hash FROM embeddings WHERE project_id=? AND source_type='file'",
            (project_id,)
        ).fetchall()
    stored = {r['source_ref']: r['content_hash'] for r in rows}

    for f in files:
        h = _hash(f['content'])
        if stored.get(f['name']) == h:
            continue
        _index_file(project_id, f['name'], f['content'], h)


def _index_file(project_id, filename, content, content_hash):
    chunks = _chunk_text(content)
    now    = datetime.now(timezone.utc).isoformat()
    with get_db() as db:
        db.execute(
            "DELETE FROM embeddings WHERE source_type='file' AND source_ref=? AND project_id=?",
            (filename, project_id)
        )
        for chunk in chunks:
            if not chunk.strip():
                continue
            try:
                vec = embed_text(chunk)
                db.execute("""
                    INSERT INTO embeddings (id, project_id, source_type, source_ref, chunk_text, embedding, content_hash, created_date)
                    VALUES (?, ?, 'file', ?, ?, ?, ?, ?)
                """, (str(uuid.uuid4()), project_id, filename, chunk, _to_bytes(vec), content_hash, now))
            except Exception as e:
                print(f"[rag] embed chunk of {filename} failed: {e}")


# ─── Retrieval ────────────────────────────────────────────────────────────────

def retrieve(project_id, query, top_k=TOP_K):
    """
    Find the most relevant chunks for a query.
    Returns list of dicts: {text, source_type, source_ref, score}
    Returns [] if Ollama is unavailable or no embeddings exist.
    """
    if not ollama_available():
        return []
    try:
        qvec = np.array(embed_text(query), dtype=np.float32)
    except Exception as e:
        print(f"[rag] query embed failed: {e}")
        return []

    with get_db() as db:
        rows = db.execute(
            "SELECT chunk_text, source_type, source_ref, embedding FROM embeddings WHERE project_id=?",
            (project_id,)
        ).fetchall()

    if not rows:
        return []

    scored = []
    qnorm  = np.linalg.norm(qvec)
    for row in rows:
        vec  = _from_bytes(row['embedding'])
        sim  = float(np.dot(qvec, vec) / (qnorm * np.linalg.norm(vec) + 1e-9))
        scored.append((sim, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {'text': r['chunk_text'], 'source_type': r['source_type'], 'source_ref': r['source_ref'], 'score': s}
        for s, r in scored[:top_k]
        if s > 0.3  # discard noise
    ]


def format_rag_context(chunks):
    """Format retrieved chunks for injection into the system prompt."""
    if not chunks:
        return None
    lines = ["Relevant context (retrieved by semantic similarity to your question):"]
    for c in chunks:
        label = f"[{c['source_type']}: {c['source_ref']}]" if c['source_ref'] else f"[{c['source_type']}]"
        lines.append(f"\n{label}\n{c['text']}")
    return '\n'.join(lines)


# ─── Chunking ─────────────────────────────────────────────────────────────────

def _chunk_text(text, max_chars=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks, preferring paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start  = 0
    while start < len(text):
        end = start + max_chars
        if end < len(text):
            for sep in ['\n\n', '\n', '. ', ' ']:
                idx = text.rfind(sep, start + max_chars // 2, end)
                if idx != -1:
                    end = idx + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks


# ─── Bulk indexer (for existing notes) ───────────────────────────────────────

def index_project_notes(project_id):
    """Index all unembedded notes for a project. Call from CLI or admin route."""
    if not ollama_available():
        print("[rag] Ollama not available")
        return 0
    with get_db() as db:
        notes = db.execute(
            "SELECT id, content FROM notes WHERE project_id=?", (project_id,)
        ).fetchall()
        indexed = db.execute(
            "SELECT source_ref FROM embeddings WHERE project_id=? AND source_type='note'",
            (project_id,)
        ).fetchall()
    already = {r['source_ref'] for r in indexed}
    count = 0
    for note in notes:
        if note['id'] not in already:
            embed_note(project_id, note['id'], note['content'])
            count += 1
    return count
