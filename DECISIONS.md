## Key Technical Decisions

### Decision Log Format

## 2025-01-[DATE] - Technology Stack Selection

**Context:** Need to choose the tech stack for ProjectBaseX. Must work on Linux, support AI integration, allow file system access, and fit my learning goals while being practical to build.

**Options Considered:**
1. Python + Flask + SQLite + Web UI (local)
2. Node.js + Express + SQLite + Web UI (local)
3. Electron app with React frontend
4. Terminal UI with Python Rich/Textual

**Decision:** Python + Flask + SQLite, local web app

**Reasoning:** Nick's stronger background is Python. Flask has minimal overhead. SQLite keeps everything in a single file — trivially portable to Docker/Mac Mini later. No ORM — raw sqlite3 for simplicity.

**Trade-offs:** Less frontend polish than Electron/Tauri, but browser UI is the right fit for a dashboard with AI chat.

**Next Steps:** Running. Migrate to Docker on Mac Mini when Phase 1 is stable daily use.

---

## 2025-01-XX - AI Integration

**Context:** Phase 2 — embedded AI chat per project.

**Decision:** Claude API (claude-sonnet-4-6), streaming via SSE, conversation history in SQLite.

**Reasoning:** Sonnet for quality analytical collaboration. Streaming makes it feel like a partner, not a query tool. Local DB for history keeps everything offline-capable.

---

## 2025-01-XX - RAG / Embeddings (Phase 3)

**Context:** Projects will accumulate large note sets and file bases (especially retro/BBS projects). "Last 5 notes" context is insufficient at scale.

**Decision:** Ollama local embeddings (nomic-embed-text) + sqlite-vec for vector storage. Build alongside file system reading in Phase 3.

**Reasoning:** Local-first is a core principle — no data leaves the machine. Ollama is already in the original spec as secondary AI. sqlite-vec keeps everything in one SQLite file. File reading and RAG are more valuable together than separately.

**Trade-offs:** More setup than an embeddings API, but zero ongoing cost and no privacy exposure.
