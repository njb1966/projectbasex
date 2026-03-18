#!/usr/bin/env bash
# Start ProjectBaseX (local dev)
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    venv/bin/pip install -q -r requirements.txt
    echo "Dependencies installed."
fi

if [ ! -f "db/projectbasex.db" ]; then
    echo "No database found. Running migration from ai-pm..."
    venv/bin/python migrate.py
fi

echo "Starting ProjectBaseX on http://localhost:5000"
venv/bin/python app.py
