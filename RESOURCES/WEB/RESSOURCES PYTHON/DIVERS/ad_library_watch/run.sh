#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$DIR"
exec "$DIR/.venv/bin/streamlit" run "$DIR/ui/app.py"
