# ProjectBaseX — Operations Reference

## Accessing the App

**URL:** http://localhost:5000

The server runs as a background service and starts automatically on boot.
Just open the link in your browser — no setup needed after initial install.

---

## Service Management

The app runs as a systemd user service. All commands use `--user` flag (no sudo needed).

```bash
# Check if running
systemctl --user status projectbasex

# Start / stop / restart
systemctl --user start projectbasex
systemctl --user stop projectbasex
systemctl --user restart projectbasex

# View live logs
journalctl --user -u projectbasex -f

# View last 50 log lines
journalctl --user -u projectbasex -n 50 --no-pager
```

The service is set to **auto-restart on failure** and **auto-start on boot**.
`loginctl linger` is enabled, so it runs even when no terminal is open.

---

## After Pulling Updates from Git

```bash
cd ~/Projects/Business_Projects/projectbasex
git pull
systemctl --user restart projectbasex
```

If you added new Python dependencies (`requirements.txt` changed):

```bash
venv/bin/pip install -r requirements.txt
systemctl --user restart projectbasex
```

---

## Ollama (Local Embeddings / RAG)

Ollama powers semantic search over your notes and project files.
The app works without it — RAG just degrades to "last 5 notes" fallback.

```bash
# Check if Ollama is running
curl -s http://localhost:11434 && echo "running" || echo "not running"

# Start Ollama (if not running)
ollama serve

# Pull the embedding model (one-time, 274 MB)
ollama pull nomic-embed-text

# Index all existing notes for a project (run after adding many notes manually)
cd ~/Projects/Business_Projects/projectbasex
venv/bin/python index_notes.py

# Index notes for a single project
venv/bin/python index_notes.py PRJ-005
```

New notes are indexed automatically when added through the UI.
File embeddings are indexed automatically on first AI chat in a project.

---

## Configuration

Settings live in `.env` in the project root (gitignored — never committed):

```bash
# Edit config
nano ~/Projects/Business_Projects/projectbasex/.env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Required. Get from console.anthropic.com |
| `AI_MODEL` | `claude-sonnet-4-6` | Claude model to use for chat |
| `PORT` | `5000` | Port the app listens on |
| `DEBUG` | `false` (via service) | Set true only for local dev |
| `DB_PATH` | `db/projectbasex.db` | Path to SQLite database |
| `PROJECTS_ROOT` | `~/Projects` | Root directory for project file browsing |

After editing `.env`, restart the service:

```bash
systemctl --user restart projectbasex
```

---

## Database

SQLite database is at `db/projectbasex.db`. Single file — easy to back up.

```bash
# Backup the database
cp ~/Projects/Business_Projects/projectbasex/db/projectbasex.db \
   ~/Projects/Business_Projects/projectbasex/db/projectbasex.db.bak

# Open database directly (for inspection)
sqlite3 ~/Projects/Business_Projects/projectbasex/db/projectbasex.db

# Useful queries
sqlite3 db/projectbasex.db "SELECT id, name, status FROM projects ORDER BY name;"
sqlite3 db/projectbasex.db "SELECT COUNT(*) FROM notes;"
sqlite3 db/projectbasex.db "SELECT COUNT(*) FROM embeddings;"
```

---

## Fresh Install (new machine or Docker migration)

```bash
git clone git@github.com:njb1966/projectbasex.git
cd projectbasex

# Python environment
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Config
cp .env.example .env
nano .env  # add ANTHROPIC_API_KEY

# Database
venv/bin/python -c "from database import init_db; init_db()"

# Optional: migrate from old ai-pm system
venv/bin/python migrate.py

# Install as service (Linux/systemd)
mkdir -p ~/.config/systemd/user
cp projectbasex.service ~/.config/systemd/user/   # if service file is committed
# or recreate it — see HOWTO.md service setup section

systemctl --user daemon-reload
systemctl --user enable projectbasex
systemctl --user start projectbasex
loginctl enable-linger $USER
```

---

## Rotating the Anthropic API Key

If your key is compromised or expired:

1. Go to https://console.anthropic.com → API Keys → create new key
2. Edit `.env`: replace the old `ANTHROPIC_API_KEY` value
3. `systemctl --user restart projectbasex`

---

## Git Workflow

```bash
cd ~/Projects/Business_Projects/projectbasex

git status          # what's changed
git diff            # see changes
git add <files>
git commit -m "..."
git push

git pull            # pull latest from GitHub
git log --oneline   # recent commits
```

Remote: `git@github.com:njb1966/projectbasex.git`

---

## Troubleshooting

**App not loading in browser**
```bash
systemctl --user status projectbasex
journalctl --user -u projectbasex -n 20 --no-pager
```

**Port 5000 already in use**
```bash
lsof -i :5000          # find what's using it
kill $(lsof -t -i:5000)
systemctl --user start projectbasex
```

**AI chat not working**
- Check `ANTHROPIC_API_KEY` is set in `.env`
- Check the key hasn't expired at console.anthropic.com
- `journalctl --user -u projectbasex -n 20` for error details

**RAG / semantic search not working**
- Ollama must be running: `curl http://localhost:11434`
- Model must be pulled: `ollama list` (should show `nomic-embed-text`)
- App falls back to last 5 notes automatically if Ollama is unavailable

**After a system update breaks something**
```bash
cd ~/Projects/Business_Projects/projectbasex
venv/bin/pip install -r requirements.txt --upgrade
systemctl --user restart projectbasex
```
