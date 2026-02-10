#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/LOCAL_RUNNER"
python3 -m venv .venv
source .venv/bin/activate
pip install flask flask-cors
python server.py
