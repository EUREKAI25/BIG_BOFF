"""Configuration centralisée du pipeline agence."""
import os

# Chemins
BASE = "/Users/nathalie/Dropbox/____BIG_BOFF___"
ENV_FILE = os.path.join(BASE, "CLAUDE/env.txt")
TODO_DIR = os.path.join(BASE, "CLAUDE/TODO")
DROPBOX_DIR = os.path.join(BASE, "CLAUDE/DROPBOX")
PIPELINE_DIR = os.path.join(BASE, "CLAUDE/PIPELINE")
PROJETS_DIR = os.path.join(BASE, "PROJETS/PRO")
STATE_FILE = os.path.join(PIPELINE_DIR, "state.json")
LOG_FILE = os.path.join(PIPELINE_DIR, "pipeline.log")
TEMPLATES_DIR = os.path.join(PIPELINE_DIR, "templates")
LOCK_FILE = os.path.join(PIPELINE_DIR, ".lock")

# Fichiers de pilotage
HUB_FILE = os.path.join(BASE, "_HUB.md")
PROJETS_FILE = os.path.join(BASE, "CLAUDE/_PROJETS.md")
AUTOBRIEF_FILE = os.path.join(BASE, "CLAUDE/_AUTO_BRIEF.md")

# Charger les variables depuis env.txt
_env = {}
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                _env[key.strip()] = val.strip()

ANTHROPIC_API_KEY = _env.get("ANTHROPIC_API_KEY", "")
BREVO_API_KEY = _env.get("BREVO_API_KEY", "")

# Résoudre les références de variables (ex: ALERT_EMAILS=SULYM_ADMIN_EMAIL)
_alert_raw = _env.get("ALERT_EMAILS", "admin@sublym.org")
ALERT_EMAIL = _env.get(_alert_raw, _alert_raw)  # si c'est un nom de variable, résoudre
ALERT_PHONE = _env.get("ALERT_PHONE", "")

# Modèle Claude — sonnet pour la vitesse et le coût
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
