#!/usr/bin/env python3
"""
BIG_BOFF Pulse — Heartbeat système
Boucle infinie (1 tick/seconde), consulte le planning, déclenche les tâches échues.
Aucune dépendance externe, aucun appel IA.
"""

import json
import logging
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Chemins ──────────────────────────────────────────

BASE = Path("/Users/nathalie/Dropbox/____BIG_BOFF___")
SCHEDULE_FILE = BASE / "_PULSE.json"
ALERTS_FILE = BASE / "_ALERTS.json"
STATE_FILE = BASE / "TOOLS/.pulse_state.json"
LOG_FILE = BASE / "TOOLS/.pulse.log"
DB_PATH = BASE / "TOOLS/MAINTENANCE/catalogue.db"
DROPBOX_ROOT = Path("/Users/nathalie/Dropbox")
PIPELINE_DIR = BASE / "CLAUDE/PIPELINE"
SEARCH_SRC = BASE / "TOOLS/SEARCH/src"

# ── Logging ──────────────────────────────────────────

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("pulse")

# ── État persistant ──────────────────────────────────

_state = None


def load_state():
    global _state
    if _state is not None:
        return _state
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                _state = json.load(f)
        except Exception:
            _state = {}
    else:
        _state = {}
    _state.setdefault("last_runs", {})
    _state.setdefault("last_file_scan", 0)
    return _state


def save_state():
    if _state is not None:
        tmp = STATE_FILE.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(_state, f, indent=2)
        tmp.replace(STATE_FILE)


# ── Planning (cache avec mtime) ──────────────────────

_schedule_cache = None
_schedule_mtime = 0


def load_schedule():
    global _schedule_cache, _schedule_mtime
    try:
        mtime = os.path.getmtime(SCHEDULE_FILE)
        if mtime != _schedule_mtime or _schedule_cache is None:
            with open(SCHEDULE_FILE) as f:
                _schedule_cache = json.load(f)
            _schedule_mtime = mtime
            log.info("Planning rechargé")
    except Exception as e:
        if _schedule_cache is None:
            log.error(f"Planning introuvable: {e}")
            _schedule_cache = {"tasks": []}
    return _schedule_cache


# ── Alertes (cache avec mtime) ───────────────────────

_alerts_cache = None
_alerts_mtime = 0


def _load_alerts():
    global _alerts_cache, _alerts_mtime
    if not ALERTS_FILE.exists():
        _alerts_cache = {"alerts": []}
        return _alerts_cache
    try:
        mtime = os.path.getmtime(ALERTS_FILE)
        if mtime != _alerts_mtime or _alerts_cache is None:
            with open(ALERTS_FILE) as f:
                _alerts_cache = json.load(f)
            _alerts_mtime = mtime
    except Exception:
        if _alerts_cache is None:
            _alerts_cache = {"alerts": []}
    return _alerts_cache


def _save_alerts(data):
    global _alerts_mtime
    tmp = ALERTS_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(ALERTS_FILE)
    _alerts_mtime = os.path.getmtime(ALERTS_FILE)


# ══════════════════════════════════════════════════════
# HANDLERS
# ══════════════════════════════════════════════════════


def check_alerts():
    """Vérifie les alertes/rappels. Notification macOS si échue."""
    data = _load_alerts()
    alerts = data.get("alerts", [])
    if not alerts:
        return

    now = datetime.now()
    dirty = False

    for alert in alerts:
        if not alert.get("active", True):
            continue
        try:
            due = datetime.fromisoformat(alert["due"])
        except (KeyError, ValueError):
            continue

        if now >= due:
            title = alert.get("title", "Rappel BIG_BOFF")
            message = alert.get("message", "")
            try:
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}" sound name "Glass"'
                ], capture_output=True, timeout=5)
            except Exception:
                pass
            log.info(f"Alerte: {title}")
            alert["active"] = False
            alert["triggered_at"] = now.isoformat()
            dirty = True

    if dirty:
        _save_alerts(data)


def scan_new_files():
    """Détecte les nouveaux fichiers Dropbox via Spotlight, les catalogue + tagge."""
    state = load_state()
    last_scan = state.get("last_file_scan", 0)
    now = time.time()

    # Temps écoulé depuis le dernier scan (max 5 min pour le premier run)
    since = min(int(now - last_scan), 300) if last_scan > 0 else 300

    try:
        result = subprocess.run(
            ["mdfind", "-onlyin", str(DROPBOX_ROOT),
             f"kMDItemFSCreationDate > $time.now(-{since})"],
            capture_output=True, text=True, timeout=30
        )
        new_files = [f for f in result.stdout.strip().split("\n") if f]
    except Exception as e:
        log.error(f"scan_new_files mdfind: {e}")
        return

    if not new_files:
        state["last_file_scan"] = now
        return

    # Import config Search (lazy)
    if str(SEARCH_SRC) not in sys.path:
        sys.path.insert(0, str(SEARCH_SRC))
    try:
        from config import should_index_path, EXCLUDED_EXTENSIONS, is_valid_tag
        from generate_tags import generate_tags_for_item
    except ImportError as e:
        log.error(f"scan_new_files import: {e}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # Chemins existants
    c.execute("SELECT chemin FROM items")
    existing = {row[0] for row in c.fetchall()}

    added = 0
    for filepath in new_files:
        p = Path(filepath)
        if not p.exists():
            continue

        full = str(p)
        if full in existing:
            continue

        try:
            rel = str(p.relative_to(DROPBOX_ROOT))
        except ValueError:
            continue

        ext = p.suffix.lower()
        if ext in EXCLUDED_EXTENSIONS:
            continue
        if not should_index_path(rel):
            continue

        is_dir = p.is_dir()
        try:
            size = p.stat().st_size if not is_dir else 0
        except OSError:
            continue

        c.execute(
            "INSERT INTO items (nom, extension, chemin, chemin_relatif, taille, est_dossier)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (p.name, p.suffix, full, rel, size, int(is_dir))
        )
        item_id = c.lastrowid

        tags = generate_tags_for_item(p.name, p.suffix or "", rel, is_dir)
        if tags:
            c.executemany(
                "INSERT INTO tags (item_id, tag) VALUES (?, ?)",
                [(item_id, t) for t in tags]
            )
        added += 1

    conn.commit()
    conn.close()

    state["last_file_scan"] = now
    if added > 0:
        log.info(f"scan_new_files: {added} éléments ajoutés")


def pipeline_check():
    """Délègue au dispatcher Pipeline existant (vérifie TODO, gates)."""
    dispatcher = PIPELINE_DIR / "dispatcher.py"
    if not dispatcher.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(dispatcher)],
            cwd=str(PIPELINE_DIR),
            timeout=300,
            capture_output=True
        )
    except Exception as e:
        log.error(f"pipeline_check: {e}")


def sync_emails():
    """Fetch les emails récents (incrémental via snippets)."""
    script = SEARCH_SRC / "index_emails.py"
    if not script.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(script), "--snippets"],
            cwd=str(SEARCH_SRC),
            timeout=600,
            capture_output=True
        )
        log.info("sync_emails: terminé")
    except Exception as e:
        log.error(f"sync_emails: {e}")


def content_index():
    """Indexation contenu des fichiers (mots-clés, identifiants)."""
    script = SEARCH_SRC / "index_content.py"
    if not script.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(script)],
            cwd=str(SEARCH_SRC),
            timeout=1800,
            capture_output=True
        )
        log.info("content_index: terminé")
    except Exception as e:
        log.error(f"content_index: {e}")


def check_stale_items():
    """Vérifie l'existence des fichiers par lots. Supprime les périmés."""
    state = load_state()
    offset = state.get("stale_check_offset", 0)
    batch_size = 500

    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute(
            "SELECT id, chemin FROM items WHERE est_dossier = 0 AND chemin IS NOT NULL"
            " LIMIT ? OFFSET ?",
            (batch_size, offset)
        )
        rows = c.fetchall()

        if not rows:
            state["stale_check_offset"] = 0
            conn.close()
            return

        stale_ids = []
        for item_id, chemin in rows:
            if not os.path.exists(chemin):
                stale_ids.append(item_id)

        if stale_ids:
            ph = ",".join("?" * len(stale_ids))
            c.execute(f"DELETE FROM tags WHERE item_id IN ({ph})", stale_ids)
            c.execute(f"DELETE FROM items WHERE id IN ({ph})", stale_ids)
            conn.commit()
            log.info(f"stale: {len(stale_ids)} items périmés supprimés (batch {offset})")

        conn.close()
        state["stale_check_offset"] = offset + batch_size
    except Exception as e:
        log.error(f"check_stale_items: {e}")


def index_pdfs():
    """Extrait le texte des PDF via pdftotext et génère des tags."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        # PDFs pas encore indexés (marqueur _pdf_indexed absent)
        c.execute("""
            SELECT i.id, i.chemin FROM items i
            WHERE i.extension IN ('.pdf', '.PDF')
            AND i.est_dossier = 0
            AND i.id NOT IN (SELECT item_id FROM tags WHERE tag = '_pdf_indexed')
            LIMIT 10
        """)
        rows = c.fetchall()

        if not rows:
            conn.close()
            return

        # Import lazy
        if str(SEARCH_SRC) not in sys.path:
            sys.path.insert(0, str(SEARCH_SRC))
        from config import is_valid_tag

        indexed = 0
        for item_id, chemin in rows:
            if not chemin or not os.path.exists(chemin):
                c.execute("INSERT INTO tags (item_id, tag) VALUES (?, '_pdf_indexed')", (item_id,))
                continue

            try:
                result = subprocess.run(
                    ["pdftotext", chemin, "-"],
                    capture_output=True, text=True, timeout=30
                )
                text = result.stdout
            except Exception:
                c.execute("INSERT INTO tags (item_id, tag) VALUES (?, '_pdf_indexed')", (item_id,))
                continue

            if not text or len(text.strip()) < 20:
                c.execute("INSERT INTO tags (item_id, tag) VALUES (?, '_pdf_indexed')", (item_id,))
                continue

            # Extraire les mots fréquents
            import re
            words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', text)
            freq = {}
            for w in words:
                w = w.lower()
                if is_valid_tag(w):
                    freq[w] = freq.get(w, 0) + 1

            top_words = sorted(freq.items(), key=lambda x: -x[1])[:30]
            tags = [w for w, cnt in top_words if cnt >= 2]

            if tags:
                c.execute("SELECT tag FROM tags WHERE item_id = ?", (item_id,))
                existing = {row[0] for row in c.fetchall()}
                new_tags = [(item_id, t) for t in tags if t not in existing]
                if new_tags:
                    c.executemany("INSERT INTO tags (item_id, tag) VALUES (?, ?)", new_tags)

            c.execute("INSERT INTO tags (item_id, tag) VALUES (?, '_pdf_indexed')", (item_id,))
            indexed += 1

        conn.commit()
        conn.close()
        if indexed > 0:
            log.info(f"index_pdfs: {indexed} PDFs indexés")
    except Exception as e:
        log.error(f"index_pdfs: {e}")


def maintenance_cleanup():
    """Tags orphelins, VACUUM."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("DELETE FROM tags WHERE item_id NOT IN (SELECT id FROM items)")
        orphans = c.rowcount
        conn.commit()
        if orphans > 0:
            log.info(f"cleanup: {orphans} tags orphelins supprimés")
        conn.execute("VACUUM")
        conn.close()
        log.info("cleanup: VACUUM terminé")
    except Exception as e:
        log.error(f"cleanup: {e}")


# ── Registry ─────────────────────────────────────────

HANDLERS = {
    "check_alerts": check_alerts,
    "scan_new_files": scan_new_files,
    "pipeline_check": pipeline_check,
    "sync_emails": sync_emails,
    "content_index": content_index,
    "check_stale_items": check_stale_items,
    "index_pdfs": index_pdfs,
    "maintenance_cleanup": maintenance_cleanup,
}


# ══════════════════════════════════════════════════════
# BOUCLE PRINCIPALE
# ══════════════════════════════════════════════════════

def main():
    log.info("Pulse démarré (PID %d)", os.getpid())
    state = load_state()
    last_save = time.time()

    while True:
        try:
            schedule = load_schedule()
            now = time.time()

            for task in schedule.get("tasks", []):
                if not task.get("enabled", True):
                    continue

                task_id = task["id"]
                interval = task["interval"]
                action = task["action"]

                last_run = state["last_runs"].get(task_id, 0)

                if now - last_run >= interval:
                    handler = HANDLERS.get(action)
                    if handler:
                        try:
                            handler()
                        except Exception as e:
                            log.error(f"Tâche {task_id}: {e}")
                    state["last_runs"][task_id] = now

            # Persister l'état toutes les 60 secondes
            if now - last_save > 60:
                save_state()
                last_save = now

        except KeyboardInterrupt:
            log.info("Pulse arrêté (SIGINT)")
            save_state()
            break
        except Exception as e:
            log.error(f"Pulse erreur: {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()
