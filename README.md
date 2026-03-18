# ProjectBaseX

A local-first project management tool for solo developers who need clarity and AI collaboration — not team features.

Built for people who work in terminals, manage multiple creative and technical projects simultaneously, and need an analytical partner that challenges ideas rather than just executing commands.

---

## What it does

- **Kanban-style dashboard** — projects organized into lanes by status (Needs Attention, Active, Planning, Ideas, Idle Review, Paused, Completed, Archived)
- **AI collaboration per project** — streaming chat powered by Claude, with five purpose-built modes
- **Local RAG pipeline** — semantic search over notes and project files via Ollama (no data leaves your machine)
- **Recommendation engine** — "Today's Focus" scores projects by status priority and staleness, tells you what to work on and why
- **Activity reports** — weekly and monthly views of notes added, status changes, and portfolio health
- **Health checks** — one-click AI review that assesses a project against its original plan and recommends continue / pivot / pause / archive
- **Ideas capture** — quick capture with "sparked by" context, linkable to existing projects
- **File system integration** — reads README and markdown files from a project's directory and injects them as AI context
- **Timeline** — automatic log of status changes and project events

---

## AI Modes

| Mode | Purpose |
|------|---------|
| **General** | Open-ended analytical conversation |
| **Planning** | Build a spec before writing any code |
| **Stuck** | Diagnostic questioning — identify the actual blocker before burning tokens |
| **Review** | Honest assessment of current state vs. original plan |
| **Decision** | Tradeoff analysis — presents options, doesn't make the choice for you |

---

## Tech Stack

- **Backend:** Python 3.11 + Flask 3.0
- **Database:** SQLite (raw `sqlite3`, no ORM)
- **AI:** Anthropic Claude API (streaming via SSE)
- **Embeddings:** Ollama `nomic-embed-text` (local, no external API)
- **Vector search:** NumPy cosine similarity over float32 BLOBs in SQLite
- **Frontend:** Vanilla JS + Jinja2 templates — no build step

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) (for RAG — optional, degrades gracefully if not running)
- An Anthropic API key

---

## Setup

```bash
# Clone and create virtualenv
git clone git@github.com:njb1966/projectbasex.git
cd projectbasex
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run
venv/bin/python app.py
# Open http://localhost:5000
```

### Ollama setup (optional but recommended)

```bash
ollama pull nomic-embed-text   # 274 MB, one-time download
ollama serve                   # runs on localhost:11434

# Index existing notes for semantic search
venv/bin/python index_notes.py
```

---

## Project Status Model

```
idea → planning → active → needs-attention
                         ↓
                    idle-review → paused → archived
                         ↓
                      completed
```

| Status | Meaning |
|--------|---------|
| `idea` | Captured, not started |
| `planning` | Active specification phase |
| `active` | Currently building |
| `needs-attention` | Stuck, blocked, or needs a decision |
| `idle-review` | Untouched — evaluate whether to continue |
| `paused` | Deliberately on hold |
| `completed` | Original plan achieved |
| `archived` | Not pursuing |

---

## Migrating from an existing project database

If you have a `~/ai-pm/db/projects.json` from a prior system:

```bash
venv/bin/python migrate.py
```

---

## Design principles

- **Solo-first always** — no teams, no assignments, no collaboration features
- **AI as analytical partner** — challenge assumptions, identify risks, not a yes-man
- **Truth over motivation** — show reality, let the user decide next moves
- **Terminal-native** — file system integration, CLI workflows first-class
- **Local-first** — no data leaves the machine unless you choose otherwise

---

## Meta

This project is also a vehicle for mastering Claude Code and AI collaboration patterns. The real product is expertise.

**Platform:** Debian 12 (primary), portable to Docker / Mac Mini
**License:** Private
