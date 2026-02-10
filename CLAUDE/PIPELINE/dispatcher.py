"""Dispatcher — heartbeat toutes les minutes.

Vérifie rapidement s'il y a du travail (filesystem uniquement, aucun appel API).
Si oui, lance l'orchestrateur. Si non, sort silencieusement.
Inclut un verrou pour empêcher les exécutions concurrentes.
"""
import json
import os
import subprocess
import sys
import time

from config import TODO_DIR, STATE_FILE, PIPELINE_DIR, LOCK_FILE

LOCK_TIMEOUT = 600  # 10 minutes max avant de considérer le lock comme périmé


def is_locked():
    """Vérifie si une exécution est déjà en cours."""
    if not os.path.exists(LOCK_FILE):
        return False
    age = time.time() - os.path.getmtime(LOCK_FILE)
    if age > LOCK_TIMEOUT:
        os.remove(LOCK_FILE)
        return False
    return True


def lock():
    """Pose le verrou."""
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def unlock():
    """Retire le verrou."""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def has_work():
    """Vérifie s'il y a du travail. Aucun appel API — filesystem uniquement."""

    # Charger l'état
    processed = set()
    projects = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)
            processed = set(state.get("processed_files", []))
            projects = state.get("projects", {})

    # 1. Nouveaux fichiers dans TODO/ ?
    if os.path.exists(TODO_DIR):
        for fichier in os.listdir(TODO_DIR):
            if not fichier.startswith(".") and fichier not in processed:
                return True

    # 2. GATE validée dans un projet en attente ?
    gate_names = {
        "BRIEF":  "GATE_1_BRIEF.md",
        "CDC":    "GATE_2_CDC.md",
        "SPECS":  "GATE_3_SPECS.md",
        "BUILD":  "GATE_4_BUILD.md",
        "DEPLOY": "GATE_5_LAUNCH.md",
    }

    for nom, info in projects.items():
        if info.get("stage_status") != "GATE_PENDING":
            continue
        etape = info.get("stage")
        gate_file = os.path.join(
            info["path"], "VALIDATION", gate_names.get(etape, "")
        )
        if os.path.exists(gate_file):
            with open(gate_file, encoding="utf-8") as gf:
                content = gf.read()
            if "STATUT:" in content:
                # Vérifier qu'un vrai statut est écrit (pas juste le template)
                for keyword in ("GO", "AJUSTER", "KILL"):
                    if f"STATUT: {keyword}" in content or f"STATUT:{keyword}" in content:
                        return True

    return False


if __name__ == "__main__":
    if is_locked():
        sys.exit(0)

    if not has_work():
        sys.exit(0)

    lock()
    try:
        orchestrator = os.path.join(PIPELINE_DIR, "orchestrator.py")
        subprocess.run(
            [sys.executable, orchestrator],
            cwd=PIPELINE_DIR,
            timeout=300  # 5 minutes max
        )
    finally:
        unlock()
