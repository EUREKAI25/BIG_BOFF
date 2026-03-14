#!/usr/bin/env python3
"""
BIG_BOFF Search — Micro-serveur local
API pour l'extension Chrome : autocomplete, search, co-occurrence.
Aucune dépendance externe (http.server + sqlite3).
"""

import base64
import email
import email.header
import email.utils
import hashlib
import http.server
import imaplib
import json
import os
import re
import socket
import sqlite3
import subprocess
import urllib.parse
from datetime import datetime
from pathlib import Path

from config import (
    normalize_tag, is_valid_tag,
    ID_OFFSET_EMAIL, ID_OFFSET_NOTE, ID_OFFSET_VAULT,
    ID_OFFSET_VIDEO, ID_OFFSET_EVENT, ID_OFFSET_CONTACT, ID_OFFSET_LIEU
)
from tasks import (
    task_create, task_get, task_list, task_update, task_done, task_undone,
    task_schedule, task_delete, attachment_add, attachment_delete,
    get_today_view, get_projects_view, conflict_list, conflict_resolve
)

try:
    from identity import (
        init_identity, get_identity, sign_data,
        verify_signature, load_private_keys, protect_identity
    )
    IDENTITY_AVAILABLE = True
except ImportError:
    IDENTITY_AVAILABLE = False
    print("⚠️  Module identity.py non disponible (Phase 1 P2P)")

DB_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db"
TASKS_DB_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/tasks.db"
DROPBOX_ROOT = "/Users/nathalie/Dropbox"
PORT = 7777
HOST = "0.0.0.0"  # Écoute sur toutes les interfaces pour accès réseau local
ACCOUNTS_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH/src/email_accounts.json"

# ── IP locale pour QR codes ─────────────────────────
def get_local_ip():
    """Obtient l'IP locale pour générer des URLs accessibles sur le réseau local."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

try:
    LOCAL_IP = get_local_ip()
    BASE_URL = f"http://{LOCAL_IP}:{PORT}"
    print(f"[DEBUG] IP réseau détectée: {LOCAL_IP}")
except Exception as e:
    print(f"[DEBUG] Erreur détection IP: {e}")
    LOCAL_IP = "127.0.0.1"
    BASE_URL = f"http://{LOCAL_IP}:{PORT}"

# ── Internationalisation (i18n) ─────────────────────
I18N_PATH = Path(__file__).parent / "i18n.json"
I18N_DATA = {}
try:
    with open(I18N_PATH, "r", encoding="utf-8") as f:
        I18N_DATA = json.load(f)
except Exception as e:
    print(f"[WARN] Impossible de charger i18n.json: {e}")

def t(key, lang="fr", **kwargs):
    """Traduit une clé avec interpolation des variables.

    Exemple: t("share.accept_page.title", from_alias="Alice")
    """
    keys = key.split(".")
    value = I18N_DATA.get(lang, {})
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, key)
        else:
            return key

    # Interpolation des variables
    if isinstance(value, str):
        for var, val in kwargs.items():
            value = value.replace(f"{{{var}}}", str(val))

    return value

# ── Miniatures ───────────────────────────────────────
THUMBNAIL_DIR = Path(__file__).parent.parent / ".thumbnails"
THUMBNAIL_DIR.mkdir(exist_ok=True)
SAVED_IMAGES_DIR = Path(__file__).parent.parent / ".saved_images"
SAVED_IMAGES_DIR.mkdir(exist_ok=True)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".ico"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv"}

# ── Coffre-fort ──────────────────────────────────────
_vault_master = None  # Mot de passe maître en mémoire (session uniquement)

# ── Identité P2P ─────────────────────────────────────
_identity_session = {
    "unlocked": False,
    "private_keys": None,
    "unlocked_at": None,
    "expires_at": None
}


def _vault_encrypt(plaintext, master_pwd):
    """Chiffre un texte avec AES-256-CBC via openssl."""
    env = os.environ.copy()
    env["VAULT_KEY"] = master_pwd
    r = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "100000",
         "-pass", "env:VAULT_KEY", "-base64", "-A"],
        input=plaintext.encode(), capture_output=True, env=env
    )
    return r.stdout.decode().strip()


def _vault_decrypt(ciphertext, master_pwd):
    """Déchiffre un texte AES-256-CBC via openssl."""
    env = os.environ.copy()
    env["VAULT_KEY"] = master_pwd
    r = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "100000",
         "-pass", "env:VAULT_KEY", "-base64", "-A"],
        input=ciphertext.encode(), capture_output=True, env=env
    )
    if r.returncode != 0:
        return None
    return r.stdout.decode()


def _vault_hash_master(master_pwd, salt=None):
    """Hash le mot de passe maître avec PBKDF2-SHA256."""
    if salt is None:
        salt = os.urandom(32)
    h = hashlib.pbkdf2_hmac("sha256", master_pwd.encode(), salt, 100000)
    return salt, h


def _vault_setup_tables(conn):
    """Crée les tables vault si elles n'existent pas."""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            login TEXT,
            password_enc TEXT,
            project TEXT,
            category TEXT DEFAULT 'password',
            url TEXT,
            notes TEXT,
            date_added TEXT,
            date_modified TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS vault_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_vault_service ON vault(service)")
    conn.commit()


def _generate_image_thumbnail(full_path, cache_path, size=(48, 48)):
    """Génère une miniature pour une image avec PIL."""
    try:
        from PIL import Image
        img = Image.open(full_path)
        img.thumbnail(size, Image.LANCZOS)
        if img.mode in ("RGBA", "P", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.save(str(cache_path), "JPEG", quality=75)
        return True
    except Exception:
        return False


def _generate_video_thumbnail(full_path, cache_path, size=(48, 48)):
    """Extrait une frame à 1s puis redimensionne avec PIL."""
    tmp_frame = str(cache_path) + ".tmp.jpg"
    try:
        r = subprocess.run(
            ["/usr/local/bin/ffmpeg", "-y", "-ss", "1", "-i", str(full_path),
             "-vframes", "1", "-q:v", "3", tmp_frame],
            capture_output=True, timeout=10
        )
        if r.returncode != 0 or not Path(tmp_frame).exists():
            subprocess.run(
                ["/usr/local/bin/ffmpeg", "-y", "-ss", "0", "-i", str(full_path),
                 "-vframes", "1", "-q:v", "3", tmp_frame],
                capture_output=True, timeout=10
            )
        if not Path(tmp_frame).exists():
            return False
        from PIL import Image
        img = Image.open(tmp_frame)
        img.thumbnail(size, Image.LANCZOS)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(str(cache_path), "JPEG", quality=75)
        return True
    except Exception:
        return False
    finally:
        try:
            Path(tmp_frame).unlink(missing_ok=True)
        except Exception:
            pass


def _extract_email(raw):
    """Extrait juste l'adresse email d'un header From/To."""
    if not raw:
        return ""
    match = re.search(r'<([^>]+)>', raw)
    if match:
        return match.group(1)
    match = re.search(r'[\w.-]+@[\w.-]+', raw)
    if match:
        return match.group(0)
    return raw


def _decode_header(raw):
    """Décode un header email encodé (base64/quoted-printable)."""
    if not raw:
        return ""
    parts = email.header.decode_header(raw)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="ignore"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def get_tasks_db():
    """DB séparée pour les tâches — évite les conflits avec pulse.py/VACUUM."""
    conn = sqlite3.connect(TASKS_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


FULLPAGE_HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>BIG_BOFF Search</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 14px; color: #1a1a1a; background: #f5f5f5; }
header { background: #1a1a1a; color: #fff; padding: 14px 24px; display: flex; align-items: center; gap: 12px; }
header h1 { font-size: 18px; font-weight: 600; letter-spacing: 0.5px; }
header .stats { margin-left: auto; font-size: 12px; opacity: 0.6; }
.container { max-width: 900px; margin: 0 auto; padding: 8px 20px 20px; }
.search-bar { position: relative; margin-bottom: 12px; display: flex; align-items: center; gap: 10px; }
.search-bar input { flex: 1; min-width: 0; padding: 12px 16px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; outline: none; transition: border-color 0.2s; background: #fff; }
.search-bar input:focus { border-color: #4a90d9; }
.autocomplete { position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 1px solid #ddd; border-radius: 0 0 8px 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 100; display: none; max-height: 250px; overflow-y: auto; }
.autocomplete .item { padding: 8px 16px; cursor: pointer; display: flex; justify-content: space-between; }
.autocomplete .item:hover, .autocomplete .item.selected { background: #f0f4ff; }
.autocomplete .item .count { font-size: 12px; color: #888; }
.type-filters { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 12px; }
.type-btn { padding: 4px 10px; border-radius: 5px; font-size: 12px; cursor: pointer; background: #f0f0f0; color: #666; border: 1px solid #ddd; transition: all 0.15s; }
.type-btn:hover { background: #e0e0e0; }
.type-btn.active { color: #fff; border-color: transparent; }
.type-btn.active[data-type="file"] { background: #3498db; }
.type-btn.active[data-type="projet"] { background: #2e7d32; }
.type-btn.active[data-type="email"] { background: #4a90d9; }
.type-btn.active[data-type="note"] { background: #f0ad4e; color: #333; }
.type-btn.active[data-type="video"] { background: #c00; }
.type-btn.active[data-type="vault"] { background: #9b59b6; }
.type-btn.active[data-type="contact"] { background: #e67e22; }
.type-btn.active[data-type="lieu"] { background: #1abc9c; }
.type-btn.active[data-type="favori"] { background: #e74c3c; }
.type-btn.active[data-type="all"] { background: #1a1a1a; }
.fav-btn { cursor: pointer; font-size: 16px; color: #ccc; transition: color 0.15s; flex-shrink: 0; margin-left: auto; padding: 0 4px; }
.fav-btn:hover { color: #e74c3c; }
.fav-btn.active { color: #e74c3c; }
.selected-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; min-height: 0; }
.selected-tags:empty { display: none; }
.tag { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 5px; font-size: 13px; font-weight: 500; cursor: pointer; }
.tag.include { background: #d4edda; color: #155724; border: 1px solid #b1dfbb; }
.tag.exclude { background: #f8d7da; color: #721c24; border: 1px solid #f1aeb5; }
.cooc-section { margin-bottom: 12px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.cooc-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; padding: 7px 10px; display: flex; align-items: center; cursor: pointer; user-select: none; background: #f9fafb; gap: 6px; }
.cooc-label:hover { background: #f3f4f6; }
.cooc-label .cooc-arrow { font-size: 10px; margin-left: 2px; transition: transform 0.2s; }
.cooc-label .cooc-sort-btn { margin-left: auto; font-size: 10px; padding: 1px 6px; border-radius: 4px; border: 1px solid #d0d5dd; background: #fff; color: #555; cursor: pointer; }
.cooc-label .cooc-sort-btn:hover { background: #e0e7ff; border-color: #6366f1; color: #4f46e5; }
.cooc-tags { display: flex; flex-wrap: wrap; gap: 5px; padding: 8px 10px; }
.cooc-tag { padding: 3px 8px; border-radius: 4px; font-size: 12px; cursor: pointer; background: #e8ecf1; color: #444; border: 1px solid #d0d5dd; }
.cooc-tag:hover { background: #d4edda; border-color: #b1dfbb; }
.cooc-tag .cnt { font-size: 10px; opacity: 0.6; margin-left: 3px; }
.results-header { display: none; justify-content: space-between; align-items: center; padding: 8px 0; font-size: 12px; color: #888; border-bottom: 1px solid #eee; margin-bottom: 8px; }
.sort-select { font-size: 11px; border: 1px solid #e5e7eb; border-radius: 5px; padding: 2px 6px; background: #fff; color: #555; cursor: pointer; }
.home-section { max-width: 900px; margin: 0 auto; padding: 8px 20px 60px; }
.home-today { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 16px; margin-bottom: 20px; }
.home-today-header { font-size: 13px; font-weight: 700; color: #374151; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
.home-today-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 13px; border-bottom: 1px solid #f3f4f6; color: #374151; cursor: pointer; }
.home-today-row:last-child { border-bottom: none; }
.home-today-row:hover { color: #4f46e5; }
.home-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 12px; }
.home-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px 12px 16px; text-align: center; cursor: pointer; transition: all 0.15s; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.home-card:hover { border-color: #6366f1; box-shadow: 0 4px 16px rgba(99,102,241,.12); transform: translateY(-2px); }
.home-card i { font-size: 26px; }
.home-card span { font-size: 12px; font-weight: 600; color: #374151; }
.results-list { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.result-item { padding: 10px 16px; border-bottom: 1px solid #f0f0f0; cursor: pointer; display: flex; align-items: flex-start; gap: 10px; }
.result-item:last-child { border-bottom: none; }
.result-item:hover { background: #f8f9ff; }
.result-email { border-left: 3px solid #4a90d9; }
.result-note { border-left: 3px solid #f0ad4e; }
.result-icon { font-size: 18px; flex-shrink: 0; margin-top: 2px; }
.result-icon .thumb { width: 60px; height: 60px; object-fit: cover; border-radius: 6px; background: #f0f0f0; display: block; }
.result-body { flex: 1; min-width: 0; }
.result-name { font-weight: 500; font-size: 14px; }
.icon-file{color:#3498db}.icon-email{color:#4a90d9}.icon-note{color:#f0ad4e}.icon-video{color:#c00}.icon-event{color:#27ae60}.icon-contact{color:#e67e22}.icon-lieu{color:#1abc9c}.icon-vault{color:#9b59b6}
.result-meta { font-size: 11px; color: #888; margin-top: 2px; }
.result-snippet { font-size: 11px; color: #777; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 800px; }
.result-actions { margin-left: auto; display: flex; gap: 6px; opacity: 0; }
.result-item:hover .result-actions { opacity: 1; }
.action-btn { font-size: 14px; padding: 3px 6px; border-radius: 4px; cursor: pointer; }
.action-btn:hover { background: #dde4f0; }
.empty-state { padding: 40px 20px; text-align: center; color: #aaa; }
.empty-state .big { font-size: 36px; margin-bottom: 10px; }
.error-banner { background: #fff3cd; color: #856404; padding: 10px 24px; font-size: 13px; display: none; }
a { color: #4a90d9; text-decoration: none; }
a:hover { text-decoration: underline; }
.email-content { padding: 12px 16px 12px 22px; background: #f8f9ff; border-left: 3px solid #4a90d9; border-bottom: 1px solid #e0e0e0; max-height: 500px; overflow-y: auto; }
.email-content .eml-hdr { margin-bottom: 5px; color: #555; font-size: 12px; }
.email-content .eml-hdr strong { color: #222; font-size: 15px; }
.email-content iframe { width: 100%; border: none; min-height: 200px; background: #fff; border-radius: 4px; }
.email-content pre { white-space: pre-wrap; word-wrap: break-word; font-family: inherit; font-size: 13px; line-height: 1.5; margin: 0; }
.email-loading { padding: 12px 22px; color: #888; font-size: 12px; border-left: 3px solid #4a90d9; border-bottom: 1px solid #e0e0e0; }
.note-content { padding: 12px 16px 12px 22px; background: #fef8f0; border-left: 3px solid #f0ad4e; border-bottom: 1px solid #e0e0e0; max-height: 500px; overflow-y: auto; }
.note-content .note-title { font-weight: 600; font-size: 15px; color: #222; margin-bottom: 4px; }
.note-content .note-date { font-size: 11px; color: #888; margin-bottom: 8px; }
.note-content .note-body { white-space: pre-wrap; word-wrap: break-word; font-family: inherit; font-size: 13px; line-height: 1.6; margin: 0; }
.note-content .note-body a { color: #4a90d9; text-decoration: underline; }
.note-content .note-body a.video-link { color: #c00; font-weight: 500; }
.note-loading { padding: 12px 22px; color: #888; font-size: 12px; border-left: 3px solid #f0ad4e; border-bottom: 1px solid #e0e0e0; }
.result-video { border-left: 3px solid #c00; }
.result-event { border-left: 3px solid #27ae60; }
.result-vault { border-left: 3px solid #9b59b6; }
.event-content { padding: 12px 16px 12px 22px; background: #f0faf0; border-left: 3px solid #27ae60; border-bottom: 1px solid #e0e0e0; max-height: 500px; overflow-y: auto; font-size: 13px; }
.event-content .ev-title { font-weight: 600; font-size: 15px; color: #222; margin-bottom: 4px; }
.event-content .ev-row { margin-bottom: 4px; color: #555; }
.event-content .ev-row .ev-label { color: #888; font-size: 12px; display: inline-block; min-width: 80px; }
.event-content .ev-tags { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
.event-content .ev-tag { padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #d4edda; color: #155724; }
.event-form-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 200; }
.event-form { background: #fff; border-radius: 10px; padding: 24px; width: 420px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
.event-form h3 { margin-bottom: 14px; font-size: 16px; color: #27ae60; }
.event-form label { display: block; font-size: 12px; color: #666; margin-bottom: 3px; margin-top: 10px; }
.event-form input, .event-form select, .event-form textarea { width: 100%; padding: 8px 10px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px; outline: none; }
.event-form input:focus, .event-form select:focus, .event-form textarea:focus { border-color: #27ae60; }
.event-form textarea { resize: vertical; min-height: 50px; }
.event-form .ef-row { display: flex; gap: 10px; }
.event-form .ef-row > div { flex: 1; }
.event-form .ef-btns { display: flex; gap: 8px; justify-content: flex-end; margin-top: 14px; }
.event-form .ef-btn { padding: 8px 16px; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
.event-form .ef-btn-ok { background: #27ae60; color: #fff; }
.event-form .ef-btn-cancel { background: #eee; color: #666; }
.event-form .ef-error { color: #c00; font-size: 12px; margin-top: 6px; display: none; }
.upcoming-section { margin-bottom: 16px; }
.upcoming-section .upcoming-header { font-size: 14px; font-weight: 600; color: #27ae60; padding: 8px 0; border-bottom: 1px solid #e0e0e0; margin-bottom: 4px; }
.type-btn.active[data-type="event"] { background: #27ae60; }
.vault-panel { padding: 12px 16px 12px 22px; background: #f5f0ff; border-left: 3px solid #9b59b6; border-bottom: 1px solid #e0e0e0; font-size: 13px; }
.vault-panel .vp-row { margin-bottom: 6px; display: flex; gap: 8px; align-items: center; }
.vault-panel .vp-label { color: #888; font-size: 12px; min-width: 55px; }
.vault-panel .vp-value { font-family: monospace; color: #333; word-break: break-all; }
.vault-panel .vp-pwd { font-family: monospace; background: #eee; padding: 3px 10px; border-radius: 4px; cursor: pointer; }
.vault-panel .vp-btn { padding: 4px 10px; border: 1px solid #9b59b6; border-radius: 4px; background: #fff; color: #9b59b6; font-size: 12px; cursor: pointer; }
.vault-panel .vp-btn:hover { background: #9b59b6; color: #fff; }
.vault-panel .vp-btn.copied { background: #27ae60; border-color: #27ae60; color: #fff; }
.vault-loading { padding: 12px 22px; color: #888; font-size: 12px; border-left: 3px solid #9b59b6; border-bottom: 1px solid #e0e0e0; }
.vault-modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 200; }
.vault-modal { background: #fff; border-radius: 10px; padding: 24px; width: 360px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
.vault-modal h3 { margin-bottom: 14px; font-size: 16px; color: #9b59b6; }
.vault-modal input { width: 100%; padding: 10px 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px; outline: none; margin-bottom: 12px; }
.vault-modal input:focus { border-color: #9b59b6; }
.vault-modal .vm-btns { display: flex; gap: 8px; justify-content: flex-end; }
.vault-modal .vm-btn { padding: 8px 16px; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
.vault-modal .vm-btn-ok { background: #9b59b6; color: #fff; }
.vault-modal .vm-btn-cancel { background: #eee; color: #666; }
.vault-modal .vm-error { color: #c00; font-size: 12px; margin-bottom: 10px; }
.result-contact { border-left: 3px solid #e67e22; }
.contact-content { padding: 12px 16px 12px 22px; background: #fef5ed; border-left: 3px solid #e67e22; border-bottom: 1px solid #e0e0e0; max-height: 350px; overflow-y: auto; font-size: 13px; }
.contact-content .ct-name { font-weight: 600; font-size: 14px; color: #222; margin-bottom: 4px; }
.contact-content .ct-row { margin-bottom: 4px; color: #555; }
.contact-content .ct-row .ct-label { color: #888; font-size: 12px; display: inline-block; min-width: 90px; }
.contact-content a { color: #4a90d9; text-decoration: underline; }
.result-lieu { border-left: 3px solid #1abc9c; }
.lieu-content { padding: 12px 16px 12px 22px; background: #edf9f6; border-left: 3px solid #1abc9c; border-bottom: 1px solid #e0e0e0; max-height: 350px; overflow-y: auto; font-size: 13px; }
.lieu-content .li-name { font-weight: 600; font-size: 14px; color: #222; margin-bottom: 4px; }
.lieu-content .li-row { margin-bottom: 4px; color: #555; }
.lieu-content .li-row .li-label { color: #888; font-size: 12px; display: inline-block; min-width: 90px; }
.lieu-content a { color: #4a90d9; text-decoration: underline; }
.lieu-content .maps-btn { display: inline-block; margin-top: 6px; padding: 5px 12px; background: #1abc9c; color: #fff; border-radius: 5px; font-size: 12px; text-decoration: none; }
.lieu-content .maps-btn:hover { background: #16a085; }
.add-btn { width: 32px; height: 32px; border-radius: 50%; border: 2px solid #27ae60; background: #fff; color: #27ae60; font-size: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.add-btn:hover { background: #27ae60; color: #fff; }
.add-form-body input[type="date"]::-webkit-calendar-picker-indicator { display: none; -webkit-appearance: none; }
.add-form-body input[type="date"] { cursor: pointer; }
.add-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); z-index: 300; display: flex; align-items: flex-start; justify-content: center; overflow-y: auto; padding: 40px 20px; }
.add-form { background: #fff; border-radius: 10px; width: 100%; max-width: 480px; box-shadow: 0 4px 24px rgba(0,0,0,0.2); overflow: hidden; }
.add-form-header { background: #27ae60; color: #fff; padding: 12px 16px; font-weight: 600; font-size: 14px; display: flex; align-items: center; justify-content: space-between; }
.add-form-header .close-btn { cursor: pointer; font-size: 20px; opacity: 0.8; }
.add-form-header .close-btn:hover { opacity: 1; }
.add-type-selector { display: flex; flex-wrap: wrap; gap: 5px; padding: 12px 16px; border-bottom: 1px solid #eee; }
.add-type-btn { padding: 5px 12px; border-radius: 5px; font-size: 12px; cursor: pointer; background: #f0f0f0; color: #666; border: 1px solid #ddd; }
.add-type-btn:hover { background: #e0e0e0; }
.add-type-btn.active { background: #27ae60; color: #fff; border-color: #27ae60; }
.add-form-body { padding: 12px 16px; max-height: 450px; overflow-y: auto; }
.add-form-body .form-group { margin-bottom: 10px; }
.add-form-body label { display: block; font-size: 11px; color: #888; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.3px; }
.add-form-body label .required { color: #c00; }
.add-form-body input, .add-form-body textarea, .add-form-body select { width: 100%; padding: 7px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 13px; font-family: inherit; outline: none; }
.add-form-body input:focus, .add-form-body textarea:focus { border-color: #27ae60; }
.add-form-body textarea { resize: vertical; min-height: 50px; }
.repeatable-row { display: flex; gap: 4px; margin-bottom: 4px; align-items: center; }
.repeatable-row input { flex: 1; }
.repeatable-add { width: 26px; height: 26px; border-radius: 50%; border: 1px solid #27ae60; background: #fff; color: #27ae60; font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.repeatable-add:hover { background: #27ae60; color: #fff; }
.repeatable-remove { width: 22px; height: 22px; border: none; background: none; color: #c00; font-size: 18px; cursor: pointer; flex-shrink: 0; }
.add-form-tags { display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 6px; }
.add-form-tags .af-tag { padding: 3px 8px; border-radius: 4px; font-size: 11px; background: #d4edda; color: #155724; display: flex; align-items: center; gap: 3px; }
.add-form-tags .af-tag .remove { cursor: pointer; font-size: 13px; opacity: 0.6; }
.add-form-tags .af-tag .remove:hover { opacity: 1; }
.add-form-tags .af-tag.auto { background: #e8ecf1; color: #444; }
.add-form-footer { padding: 12px 16px; border-top: 1px solid #eee; display: flex; gap: 8px; justify-content: flex-end; }
.add-form-footer .af-btn { padding: 8px 18px; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; font-weight: 500; }
.add-form-footer .af-btn-ok { background: #27ae60; color: #fff; }
.add-form-footer .af-btn-ok:hover { background: #219a52; }
.add-form-footer .af-btn-ok:disabled { background: #aaa; cursor: default; }
.add-form-footer .af-btn-cancel { background: #eee; color: #666; }
.add-form-footer .af-btn-cancel:hover { background: #ddd; }
.add-form .af-status { padding: 8px 16px; font-size: 12px; text-align: center; display: none; }
.add-form .af-status.success { display: block; background: #d4edda; color: #155724; }
.add-form .af-status.error { display: block; background: #f8d7da; color: #721c24; }
.form-autocomplete { position: relative; }
.form-ac-dropdown { position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 1px solid #ddd; border-radius: 0 0 6px 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 400; max-height: 150px; overflow-y: auto; display: none; }
.form-ac-dropdown .ac-item { padding: 6px 10px; cursor: pointer; font-size: 12px; }
.form-ac-dropdown .ac-item:hover { background: #f0f4ff; }
.form-ac-dropdown .ac-item.create { color: #27ae60; font-style: italic; }
/* Tags modifiables */
.tags-list { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.item-tag { display: inline-flex; align-items: center; gap: 4px; padding: 3px 6px 3px 8px; background: #e8f4f8; border: 1px solid #b8dce8; border-radius: 12px; font-size: 11px; color: #2c5f7a; }
.tag-remove-btn { background: none; border: none; color: #7a8e99; font-size: 16px; line-height: 1; cursor: pointer; padding: 0; width: 14px; height: 14px; display: flex; align-items: center; justify-content: center; border-radius: 50%; transition: all 0.15s ease; }
.tag-remove-btn:hover { background: #c0392b; color: #fff; transform: scale(1.1); }
/* Bouton suppression d'élément */
.delete-btn { background: none; border: none; color: #95a5a6; font-size: 14px; cursor: pointer; padding: 4px 8px; margin-left: 8px; border-radius: 4px; transition: all 0.2s; opacity: 0.6; }
.delete-btn:hover { background: #c0392b; color: #fff; opacity: 1; transform: scale(1.1); }

/* Modal de suppression */
.delete-modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 10000; align-items: center; justify-content: center; }
.delete-modal.active { display: flex; }
.delete-modal-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.6); }
.delete-modal-content { position: relative; background: #fff; border-radius: 8px; padding: 24px; max-width: 400px; width: 90%; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3); }
.delete-modal-title { font-size: 18px; font-weight: 600; color: #2c3e50; margin-bottom: 8px; }
.delete-modal-name { font-size: 14px; color: #7f8c8d; margin-bottom: 20px; word-break: break-word; }
.delete-modal-buttons { display: flex; gap: 12px; margin-bottom: 12px; }
.delete-modal-btn { flex: 1; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; background: #fff; cursor: pointer; text-align: center; transition: all 0.2s; }
.delete-modal-btn:hover { transform: translateY(-2px); box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); }
.delete-modal-btn.db-only { border-color: #3498db; color: #3498db; }
.delete-modal-btn.db-only:hover { background: #3498db; color: #fff; }
.delete-modal-btn.permanent { border-color: #e74c3c; color: #e74c3c; }
.delete-modal-btn.permanent:hover { background: #e74c3c; color: #fff; }
.delete-modal-desc { font-size: 11px; margin-top: 4px; opacity: 0.8; }
.delete-modal-cancel { width: 100%; padding: 10px; background: #ecf0f1; border: none; border-radius: 6px; cursor: pointer; color: #7f8c8d; font-weight: 500; }
.delete-modal-cancel:hover { background: #d5dbdb; }
/* ── Tabs nav ─────────────────────────────────────────────────────── */
.nav-tabs { display: flex; gap: 3px; margin-left: 20px; }
.nav-tab { background: rgba(255,255,255,.12); color: #fff; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; transition: background .15s; white-space: nowrap; }
.nav-tab:hover { background: rgba(255,255,255,.22); }
.nav-tab.active { background: #4f46e5; }
/* ── Tasks panel ──────────────────────────────────────────────────── */
#tasks-panel { max-width: 900px; margin: 0 auto; padding: 20px; }
.tasks-progress-card { background: #fff; border-radius: 10px; padding: 16px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); display: flex; align-items: center; gap: 16px; }
.tasks-progress-bar { flex: 1; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }
.tasks-progress-bar-fill { height: 100%; background: #16a34a; border-radius: 4px; transition: width .4s; }
.tasks-date { font-size: 13px; color: #6b7280; min-width: 120px; }
.tasks-progress-label { font-size: 13px; font-weight: 600; color: #111827; min-width: 60px; text-align: right; }
.all-done-banner { background: #dcfce7; border: 1px solid #86efac; border-radius: 10px; padding: 16px 20px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; }
.all-done-banner span { font-weight: 600; color: #16a34a; flex: 1; }
.all-done-banner button { background: #16a34a; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.t-section { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.t-section-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; color: #6b7280; margin-bottom: 12px; display: flex; align-items: center; gap: 6px; }
.t-dot { width: 8px; height: 8px; border-radius: 50%; }
.t-dot-red { background: #dc2626; }
.t-dot-blue { background: #4f46e5; }
.t-dot-green { background: #16a34a; }
.t-dot-gray { background: #9ca3af; }
.t-card { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; border-radius: 8px; margin-bottom: 6px; cursor: pointer; transition: background .12s; border: 1px solid #f3f4f6; }
.t-card:hover { background: #f9fafb; }
.t-card.overdue { border-left: 3px solid #dc2626; }
.t-card.done { opacity: .6; }
.t-card.tomorrow { opacity: .7; }
.t-card.blocked { border-left: 3px solid #d97706; }
.t-check { width: 20px; height: 20px; border: 2px solid #d1d5db; border-radius: 50%; flex-shrink: 0; margin-top: 2px; cursor: pointer; transition: all .15s; }
.t-check:hover { border-color: #4f46e5; }
.t-check.checked { background: #16a34a; border-color: #16a34a; display: flex; align-items: center; justify-content: center; }
.t-check.checked::after { content: "✓"; color: #fff; font-size: 11px; font-weight: 700; }
.t-body { flex: 1; min-width: 0; }
.t-title { font-size: 14px; font-weight: 500; color: #111827; }
.t-title.done-text { text-decoration: line-through; color: #9ca3af; }
.t-desc { font-size: 12px; color: #6b7280; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.t-meta { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 5px; align-items: center; }
.t-tag { background: #e0e7ff; color: #4338ca; padding: 1px 7px; border-radius: 4px; font-size: 11px; }
.t-badge { padding: 1px 7px; border-radius: 4px; font-size: 11px; }
.t-badge-orange { background: #fff7ed; color: #c2410c; }
.t-badge-gray { background: #f3f4f6; color: #6b7280; }
.t-actions { display: flex; gap: 4px; opacity: 0; transition: opacity .12s; }
.t-card:hover .t-actions { opacity: 1; }
.t-btn { background: none; border: 1px solid #e5e7eb; border-radius: 5px; padding: 4px 7px; cursor: pointer; font-size: 12px; color: #6b7280; }
.t-btn:hover { background: #f3f4f6; color: #111827; }
.t-btn.danger:hover { background: #fef2f2; border-color: #fca5a5; color: #dc2626; }
.t-add-btn { position: fixed; bottom: 24px; right: 24px; width: 52px; height: 52px; background: #4f46e5; color: #fff; border: none; border-radius: 50%; cursor: pointer; font-size: 22px; box-shadow: 0 4px 12px rgba(79,70,229,.4); display: none; transition: transform .15s; z-index: 50; }
.t-add-btn:hover { transform: scale(1.08); }
#tasks-panel .t-add-btn { display: flex; align-items: center; justify-content: center; }
.t-empty { padding: 40px 20px; text-align: center; color: #9ca3af; }
.t-empty i { font-size: 32px; margin-bottom: 10px; }
.conflict-badge { background: #fef3c7; color: #92400e; padding: 8px 16px; border-radius: 8px; margin-bottom: 12px; cursor: pointer; font-size: 13px; display: none; }
.conflict-badge.visible { display: flex; align-items: center; gap: 8px; }
/* Tasks modals */
.t-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 200; display: flex; align-items: center; justify-content: center; opacity: 0; pointer-events: none; transition: opacity .15s; }
.t-modal-overlay.open { opacity: 1; pointer-events: auto; }
.t-modal { background: #fff; border-radius: 12px; padding: 24px; width: min(520px, 92vw); max-height: 85vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,.3); }
.tag-chips { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 6px; min-height: 0; }
.tag-chip { display: flex; align-items: center; gap: 4px; background: #e0e7ff; color: #4338ca; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.tag-chip button { background: none; border: none; cursor: pointer; color: #6366f1; font-size: 13px; padding: 0; line-height: 1; }
.t-modal h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
.t-field { margin-bottom: 14px; }
.t-field label { display: block; font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 5px; }
.t-field input, .t-field textarea, .t-field select { width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 7px; font-size: 14px; font-family: inherit; outline: none; }
.t-field input:focus, .t-field textarea:focus, .t-field select:focus { border-color: #4f46e5; }
.t-field textarea { resize: vertical; min-height: 70px; }
.t-modal-btns { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.t-modal-btns button { padding: 9px 18px; border-radius: 7px; border: none; cursor: pointer; font-size: 14px; font-weight: 500; }
.t-btn-primary { background: #4f46e5; color: #fff; }
.t-btn-primary:hover { background: #4338ca; }
.t-btn-secondary { background: #f3f4f6; color: #374151; }
.t-btn-secondary:hover { background: #e5e7eb; }
/* Accordion projets */
.proj-row { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-radius: 8px; cursor: pointer; }
.proj-row:hover { background: #f9fafb; }
.proj-toggle { width: 18px; color: #9ca3af; font-size: 12px; flex-shrink: 0; }
.proj-children { padding-left: 24px; }
/* Détail projet pleine page */
#detail-panel { font-family: inherit; }
.dp-back { background: none; border: none; cursor: pointer; font-size: 15px; color: #4f46e5; padding: 6px 10px; border-radius: 6px; display: inline-flex; align-items: center; gap: 6px; font-weight: 500; transition: background .12s; }
.dp-back:hover { background: #eef2ff; }
.dp-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.dp-title { margin: 0; font-size: 22px; font-weight: 700; color: #1f2937; flex: 1; }
.dp-meta { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.dp-badge { padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
.dp-section { margin-bottom: 16px; }
.dp-section-label { font-size: 11px; font-weight: 700; color: #9ca3af; text-transform: uppercase; letter-spacing: .6px; margin-bottom: 4px; }
.dp-section-value { font-size: 14px; color: #374151; line-height: 1.6; }
.dp-section-value[contenteditable]:empty:before { content: attr(data-placeholder); color: #d1d5db; font-style: italic; pointer-events: none; }
.dp-block { border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; margin-bottom: 12px; }
.dp-block-header { padding: 10px 14px; background: #f9fafb; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #e5e7eb; cursor: pointer; user-select: none; }
.dp-ch-arrow { transition: transform 0.2s; color: #9ca3af; font-size: 11px; flex-shrink: 0; }
.dp-ch-arrow.open { transform: rotate(0deg); }
.dp-ch-arrow.closed { transform: rotate(-90deg); }
.dp-ch-body { overflow: hidden; transition: max-height 0.25s ease; }
.dp-ch-body.collapsed { max-height: 0 !important; }
.dp-block-header span { font-weight: 600; font-size: 14px; flex: 1; color: #1f2937; }
.dp-task-row { padding: 8px 14px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #f3f4f6; }
.dp-task-row:last-child { border-bottom: none; }
.dp-check { background: none; border: 2px solid #d1d5db; border-radius: 50%; width: 20px; height: 20px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: border-color .12s; }
.dp-check.done { border-color: #16a34a; background: #f0fdf4; }
.dp-task-title { flex: 1; font-size: 13px; color: #374151; }
.dp-task-title.done { text-decoration: line-through; color: #9ca3af; }
.dp-editable { cursor: text; min-width: 20px; transition: border-color .15s; }
.dp-editable:hover { border-bottom-color: #d1d5db !important; }
.dp-add-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.dp-quickadd-bar { display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap; }
.dp-qa-btn { padding: 5px 12px; border-radius: 6px; border: 1px solid #e5e7eb; background: #f9fafb; font-size: 12px; cursor: pointer; color: #374151; transition: all 0.12s; font-family: inherit; }
.dp-qa-btn:hover { background: #e0e7ff; border-color: #6366f1; color: #4f46e5; }
.dp-qa-btn.active { background: #e0e7ff; border-color: #6366f1; color: #4f46e5; }
.dp-quickadd-form { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; margin-bottom: 14px; display: flex; flex-direction: column; gap: 8px; }
.dp-qa-input { padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; font-family: inherit; box-sizing: border-box; width: 100%; }
.dp-qa-input:focus { outline: none; border-color: #4f46e5; }
.dp-tag-bar { display: flex; flex-wrap: wrap; gap: 4px; padding: 6px 0 10px; }
.dp-tag-chip { padding: 2px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; border: 1px solid #d1d5db; background: #f3f4f6; color: #555; transition: all 0.12s; }
.dp-tag-chip:hover { background: #e0e7ff; border-color: #6366f1; color: #4f46e5; }
.dp-tag-chip.active { background: #4f46e5; border-color: #4f46e5; color: #fff; }
.dp-sort-bar { display: flex; gap: 4px; align-items: center; flex-wrap: wrap; }
.dp-sort-opt { padding: 2px 8px; font-size: 11px; border: 1px solid #e5e7eb; border-radius: 4px; background: #fff; cursor: pointer; color: #6b7280; font-family: inherit; }
.dp-sort-opt.active { background: #4f46e5; border-color: #4f46e5; color: #fff; }
.dp-resources { margin-bottom: 14px; }
.dp-resource-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 13px; border-bottom: 1px solid #f3f4f6; }
/* ── Global Add Button + Modal ── */
.global-add-btn { width:40px;height:40px;border-radius:50%;background:#4f46e5;color:#fff;border:none;font-size:20px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s;box-shadow:0 2px 8px rgba(79,70,229,.35); }
.global-add-btn:hover { background:#4338ca; }
.ga-modal-overlay { position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:2000;display:flex;align-items:center;justify-content:center;padding:16px; }
.ga-modal-box { background:#1e1e2e;border-radius:20px;width:min(480px,100%);max-height:88vh;overflow-y:auto;display:flex;flex-direction:column;box-shadow:0 24px 80px rgba(0,0,0,.55); }
.ga-modal-head { padding:20px 20px 0;display:flex;align-items:center;justify-content:space-between; }
.ga-modal-head h2 { font-size:16px;font-weight:600;color:#e2e8f0;margin:0; }
.ga-close-btn { background:rgba(255,255,255,.08);border:none;font-size:16px;cursor:pointer;color:#94a3b8;padding:5px 8px;line-height:1;border-radius:8px; }
.ga-close-btn:hover { background:rgba(255,255,255,.15);color:#e2e8f0; }
.ga-modal-body { padding:16px 20px 20px;display:flex;flex-direction:column;gap:14px; }
.ga-type-pills { display:flex;gap:6px;flex-wrap:wrap; }
.ga-type-pill { padding:7px 16px;border-radius:20px;border:2px solid #e5e7eb;background:#fff;font-size:13px;font-weight:600;cursor:pointer;color:#6b7280;transition:all .15s;font-family:inherit; }
.ga-type-pill:hover { border-color:#c7d2fe; }
.ga-type-pill.active { border-color:#4f46e5;background:#eef2ff;color:#4f46e5; }
.ga-section-label { font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px; }
.ga-picker-list { display:flex;flex-direction:column;gap:2px;max-height:200px;overflow-y:auto;border:1.5px solid #e5e7eb;border-radius:10px;padding:4px; }
.ga-picker-item { display:flex;align-items:center;justify-content:space-between;padding:8px 10px;border-radius:7px;cursor:pointer;font-size:13px;transition:background .1s; }
.ga-picker-item:hover { background:#eef2ff; }
.ga-picker-item.selected { background:#4f46e5;color:#fff; }
.ga-picker-item .ga-pi-status { font-size:10px;padding:1px 6px;border-radius:4px;background:rgba(255,255,255,.25);opacity:.8; }
.ga-selected-badge { display:inline-flex;align-items:center;gap:6px;padding:5px 10px;background:#eef2ff;border:1.5px solid #c7d2fe;border-radius:8px;font-size:13px;font-weight:600;color:#4f46e5; }
.ga-selected-badge button { background:none;border:none;cursor:pointer;color:#6366f1;font-size:14px;padding:0;line-height:1; }
.ga-field { display:flex;flex-direction:column;gap:5px; }
.ga-field label { font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.6px; }
.ga-input { padding:9px 12px;border:1.5px solid rgba(255,255,255,.1);border-radius:9px;font-size:14px;font-family:inherit;outline:none;transition:border-color .15s;width:100%;box-sizing:border-box;background:rgba(255,255,255,.07);color:#e2e8f0; }
.ga-input::placeholder { color:#475569; }
.ga-input:focus { border-color:#6366f1; }
.ga-input option { background:#1e1e2e;color:#e2e8f0; }
.ga-footer { display:flex;justify-content:flex-end;gap:8px;padding:0 20px 20px; }
.ga-btn { padding:9px 22px;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;border:none;font-family:inherit; }
.ga-btn-cancel { background:rgba(255,255,255,.08);color:#94a3b8; }
.ga-btn-cancel:hover { background:rgba(255,255,255,.14); }
.ga-btn-save { background:#4f46e5;color:#fff; }
.ga-btn-save:hover { background:#4338ca; }
.ga-breadcrumb { display:flex;align-items:center;gap:6px;flex-wrap:wrap; }
.dp-resource-row a { color: #4f46e5; text-decoration: none; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dp-resource-row a:hover { text-decoration: underline; }
.dp-add-bar h3 { margin: 0; font-size: 16px; font-weight: 600; color: #1f2937; }
.dp-add-bar .dp-btns { display: flex; gap: 8px; }
.dp-empty { color: #9ca3af; font-size: 13px; padding: 16px; background: #f9fafb; border-radius: 8px; text-align: center; }
</style>
</head>
<body>
<!-- Modal de suppression -->
<div class="delete-modal" id="delete-modal">
  <div class="delete-modal-overlay"></div>
  <div class="delete-modal-content">
    <div class="delete-modal-title">Supprimer cet \u00e9l\u00e9ment ?</div>
    <div class="delete-modal-name" id="delete-modal-name"></div>
    <div class="delete-modal-buttons">
      <button class="delete-modal-btn db-only" id="delete-db-only">
        <div style="font-weight:600">Base seule</div>
        <div class="delete-modal-desc">Garder le fichier</div>
      </button>
      <button class="delete-modal-btn permanent" id="delete-permanent">
        <div style="font-weight:600">D\u00e9finitive</div>
        <div class="delete-modal-desc" id="delete-permanent-desc">Tout supprimer</div>
      </button>
    </div>
    <button class="delete-modal-cancel" id="delete-cancel">Annuler</button>
  </div>
</div>

<header>
  <h1>BIG_BOFF Search</h1>
  <span class="stats" id="stats"></span>
  <a href="#" id="share-btn" onclick="showShareQR(event)" title="Partager / QR code" style="color:#fff;font-size:16px;text-decoration:none;opacity:0.7;margin-left:10px"><i class="fa-solid fa-qrcode"></i></a>
</header>
<div class="error-banner" id="error-banner">Serveur non accessible.</div>
<div id="search-section" style="max-width:900px;margin:0 auto;padding:16px 20px 0">
  <div class="search-bar">
    <input type="text" id="search-input" placeholder="Rechercher un tag...">
    <div class="autocomplete" id="autocomplete"></div>
    <button class="global-add-btn" onclick="openGlobalAdd()" title="Ajouter..."><i class="fa-solid fa-plus"></i></button>
  </div>
  <div class="type-filters" id="type-filters"></div>
  <div class="selected-tags" id="selected-tags"></div>
</div>

<!-- Global Add Modal -->
<div id="ga-modal" class="ga-modal-overlay" style="display:none" onclick="if(event.target===this)closeGlobalAdd()">
  <div class="ga-modal-box">
    <div class="ga-modal-head">
      <h2>Ajouter</h2>
      <button class="ga-close-btn" onclick="closeGlobalAdd()">&times;</button>
    </div>
    <div class="ga-modal-body" id="ga-modal-body"></div>
    <div class="ga-footer">
      <button class="ga-btn ga-btn-save" id="ga-save-btn" onclick="saveGlobalAdd()" style="display:none"><i class="fa-solid fa-check"></i> Enregistrer</button>
    </div>
  </div>
</div>
<div class="container">
  <div class="cooc-section" id="cooc-section" style="display:none">
    <div class="cooc-label" onclick="toggleCooc()">
      <i class="fa-solid fa-tags"></i> Tags associ\u00e9s
      <i class="fa-solid fa-chevron-right cooc-arrow" id="cooc-arrow"></i>
      <button class="cooc-sort-btn" id="cooc-sort-btn" onclick="event.stopPropagation();toggleCoocSort()" title="Trier les tags">tri: \u00a0\ud83d\udd22</button>
    </div>
    <div class="cooc-tags" id="cooc-tags" style="display:none"></div>
  </div>
  <div class="results-header" id="results-header">
    <span id="results-count"></span>
    <div style="display:flex;align-items:center;gap:8px">
      <span id="results-nav"></span>
      <select class="sort-select" id="sort-select" onchange="setSortBy(this.value)" title="Trier les r\u00e9sultats">
        <option value="relevance">Pertinence</option>
        <option value="name_asc">Nom A\u2192Z</option>
        <option value="name_desc">Nom Z\u2192A</option>
        <option value="date_desc">Plus r\u00e9cent</option>
        <option value="date_asc">Plus ancien</option>
      </select>
    </div>
  </div>
  <div class="results-list" id="results-list"></div>
  <div class="empty-state" id="empty-state" style="display:none">
    <div class="big" style="font-size:24px;color:#e5e7eb"><i class="fa-solid fa-face-sad-tear"></i></div>
    <div>Aucun r\u00e9sultat</div>
  </div>
</div>

<!-- Home page -->
<div class="home-section" id="home-section">
  <div class="home-today" id="home-today-widget" style="display:none"></div>
  <div class="home-cards" id="home-type-cards"></div>
  <button class="add-btn" id="add-btn" title="Ajouter un \u00e9l\u00e9ment" style="position:fixed;bottom:24px;right:24px;width:48px;height:48px;font-size:24px;border-radius:50%;box-shadow:0 4px 16px rgba(0,0,0,.2);z-index:50">+</button>
</div>

<!-- ── Panel Aujourd'hui / Projets ───────────────────────────────── -->
<div id="tasks-panel" style="display:none">
  <div class="conflict-badge" id="tasks-conflict-badge" onclick="openTasksConflicts()">
    <i class="fa-solid fa-triangle-exclamation"></i>
    <span id="tasks-conflict-msg">Conflits de synchronisation en attente</span>
  </div>
  <div id="tasks-progress-card" class="tasks-progress-card" style="display:none">
    <div class="tasks-date" id="tasks-date"></div>
    <div class="tasks-progress-bar"><div class="tasks-progress-bar-fill" id="tasks-progress-fill" style="width:0%"></div></div>
    <div class="tasks-progress-label" id="tasks-progress-label">0 / 0</div>
  </div>
  <div id="tasks-all-done-banner" class="all-done-banner" style="display:none">
    <i class="fa-solid fa-party-horn" style="color:#16a34a;font-size:20px"></i>
    <span>Toutes les t\u00e2ches du jour sont faites !</span>
    <button onclick="openPlanTomorrow()"><i class="fa-solid fa-forward"></i> Planifier demain</button>
  </div>
  <div id="tasks-main-container"></div>
  <div id="projects-main-container" style="display:none"></div>
  <button class="t-add-btn" onclick="openAddTask()" title="Nouvelle t\u00e2che">+</button>
</div>

<!-- Panel détail projet (pleine page) -->
<div id="detail-panel" style="display:none;max-width:900px;margin:0 auto;padding:20px 20px 60px"></div>

<!-- Modal tâche -->
<div class="t-modal-overlay" id="t-modal-task">
  <div class="t-modal">
    <h3 id="t-modal-task-title">Nouvelle tâche</h3>
    <div class="t-field"><label>Titre *</label><input type="text" id="t-task-title" placeholder="Titre"></div>
    <div class="t-field"><label>Description</label><textarea id="t-task-desc" rows="2" placeholder="Description courte"></textarea></div>
    <div class="t-field"><label>Objectif (goal)</label><textarea id="t-task-goal" rows="2" placeholder="Quel est le résultat attendu ?"></textarea></div>
    <div class="t-field"><label>Mission</label><textarea id="t-task-mission" rows="2" placeholder="Comment y arriver ?"></textarea></div>
    <div class="t-field" id="t-type-field"><label>Type</label>
      <select id="t-task-type">
        <option value="task">Tâche</option>
        <option value="chantier">Chantier</option>
        <option value="projet">Projet</option>
      </select>
    </div>
    <div class="t-field"><label>Deadline</label><input type="date" id="t-task-deadline"></div>
    <div class="t-field" id="t-scheduled-field"><label>Planification</label>
      <select id="t-task-scheduled">
        <option value="today">Aujourd'hui</option>
        <option value="tomorrow">Demain</option>
        <option value="later">Plus tard</option>
      </select>
    </div>
    <div class="t-field"><label>Tags</label>
      <div class="tag-chips" id="t-tag-chips"></div>
      <input type="text" id="t-task-tags" placeholder="Ajouter un tag..." autocomplete="off">
    </div>
    <input type="hidden" id="t-task-edit-id">
    <input type="hidden" id="t-task-project-id">
    <input type="hidden" id="t-task-chantier-id">
    <div class="t-modal-btns">
      <button class="t-btn-secondary" onclick="closeTaskModal()">Annuler</button>
      <button class="t-btn-primary" onclick="saveTask()">Enregistrer</button>
    </div>
  </div>
</div>

<!-- Modal plan demain -->
<div class="t-modal-overlay" id="t-modal-tomorrow">
  <div class="t-modal">
    <h3>Planifier demain</h3>
    <p style="font-size:13px;color:#6b7280;margin-bottom:14px">Quelles t\u00e2ches veux-tu faire demain ?</p>
    <div id="t-tomorrow-list"></div>
    <div class="t-modal-btns">
      <button class="t-btn-secondary" onclick="closeTomorrowModal()">Fermer</button>
      <button class="t-btn-primary" onclick="confirmTomorrow()">Confirmer</button>
    </div>
  </div>
</div>

<!-- Modal d\u00e9tail t\u00e2che -->
<div class="t-modal-overlay" id="t-modal-detail">
  <div class="t-modal">
    <h3 id="t-detail-title"></h3>
    <div id="t-detail-body"></div>
    <div class="t-modal-btns">
      <button class="t-btn-secondary" onclick="closeDetailModal()">Fermer</button>
      <button class="t-btn-primary" onclick="openEditTask(currentDetailId)">Modifier</button>
    </div>
  </div>
</div>

<!-- Modal conflits -->
<div class="t-modal-overlay" id="t-modal-conflicts">
  <div class="t-modal" style="width:min(640px,92vw)">
    <h3>Conflits de synchronisation</h3>
    <div id="t-conflicts-body"></div>
    <div class="t-modal-btns"><button class="t-btn-secondary" onclick="closeConflictsModal()">Fermer</button></div>
  </div>
</div>

<script>
const API = window.location.origin + "/api";
const state = { includeTags: [], excludeTags: [], autocompleteIndex: -1, autocompleteItems: [], currentOffset: 0, pageSize: 50, totalResults: 0, activeTypes: [], sortBy: 'relevance' };
var _coocData = []; var _coocSortByCount = true; var _coocOpen = false;

// Restaurer l'état depuis les paramètres URL
(function initFromURL() {
  const params = new URLSearchParams(window.location.search);
  if (params.has("include")) {
    state.includeTags = params.get("include").split(",").filter(t => t.trim());
  }
  if (params.has("exclude")) {
    state.excludeTags = params.get("exclude").split(",").filter(t => t.trim());
  }
  if (params.has("types")) {
    state.activeTypes = params.get("types").split(",").filter(t => t.trim());
  }
})();

const input = document.getElementById("search-input");
const autocompleteEl = document.getElementById("autocomplete");
const selectedTagsEl = document.getElementById("selected-tags");
const coocSection = document.getElementById("cooc-section");
const coocTagsEl = document.getElementById("cooc-tags");
const resultsHeader = document.getElementById("results-header");
const resultsCount = document.getElementById("results-count");
const resultsNav = document.getElementById("results-nav");
const resultsList = document.getElementById("results-list");
const emptyState = document.getElementById("empty-state");
const errorBanner = document.getElementById("error-banner");
const statsEl = document.getElementById("stats");
const typeFiltersEl = document.getElementById("type-filters");
const TYPE_BUTTONS = [{type:"projet",label:"Projets",icon:'<i class="fa-solid fa-folder-tree"></i>'},{type:"file",label:"Fichiers",icon:'<i class="fa-solid fa-folder"></i>'},{type:"email",label:"Emails",icon:'<i class="fa-solid fa-envelope"></i>'},{type:"note",label:"Notes",icon:'<i class="fa-solid fa-note-sticky"></i>'},{type:"video",label:"Vid\u00e9os",icon:'<i class="fa-solid fa-video"></i>'},{type:"event",label:"\u00c9v\u00e9nements",icon:'<i class="fa-solid fa-calendar-days"></i>'},{type:"contact",label:"Contacts",icon:'<i class="fa-solid fa-user"></i>'},{type:"lieu",label:"Lieux",icon:'<i class="fa-solid fa-location-dot"></i>'},{type:"vault",label:"Vault",icon:'<i class="fa-solid fa-lock"></i>'},{type:"favori",label:"Favoris",icon:'<i class="fa-solid fa-heart"></i>'}];
function renderTypeFilters() {
  typeFiltersEl.innerHTML = TYPE_BUTTONS.map(function(b) {
    var isActive = b.type === "favori" ? state.includeTags.indexOf("favori") >= 0 : state.activeTypes.indexOf(b.type) >= 0;
    return '<span class="type-btn' + (isActive ? ' active' : '') + '" data-type="' + b.type + '">' + (b.icon ? b.icon + ' ' : '') + b.label + '</span>';
  }).join("");
  typeFiltersEl.querySelectorAll(".type-btn").forEach(function(el) {
    el.addEventListener("click", function() {
      var t = el.dataset.type;
      if (t === "favori") { var fi = state.includeTags.indexOf("favori"); if (fi >= 0) state.includeTags.splice(fi, 1); else state.includeTags.push("favori"); }
      else { if (state.activeTypes.indexOf(t) >= 0) state.activeTypes = []; else state.activeTypes = [t]; }
      refresh();
    });
  });
}
async function toggleFavorite(itemId, btnEl) {
  try {
    var resp = await fetch(API + "/favorite", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({id: parseInt(itemId)}) });
    var data = await resp.json();
    if (data.ok) { btnEl.innerHTML = data.favorited ? '<i class="fa-solid fa-heart"></i>' : '<i class="fa-regular fa-heart"></i>'; btnEl.classList.toggle("active", data.favorited); }
  } catch(e) {}
}
async function checkFavorites(ids) {
  if (!ids.length) return;
  try {
    var data = await apiFetch("favorite/check", { ids: ids.join(",") });
    var favSet = new Set(data.favorited || []);
    document.querySelectorAll(".fav-btn[data-fav-id]").forEach(function(btn) { if (favSet.has(parseInt(btn.dataset.favId))) { btn.innerHTML = '<i class="fa-solid fa-heart"></i>'; btn.classList.add("active"); } });
  } catch(e) {}
}

async function apiFetch(endpoint, params = {}) {
  const url = new URL(API + "/" + endpoint);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) v.forEach(val => url.searchParams.append(k, val));
    else url.searchParams.set(k, v);
  }
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("HTTP " + resp.status);
  return resp.json();
}
async function checkServer() {
  try {
    const data = await apiFetch("stats");
    statsEl.textContent = data.total_items.toLocaleString() + " fichiers \u00b7 " + data.unique_tags.toLocaleString() + " tags";
    errorBanner.style.display = "none";
  } catch { errorBanner.style.display = "block"; }
}
let debounceTimer;
function onInput() {
  clearTimeout(debounceTimer);
  const q = input.value.trim();
  if (q.length < 1) { hideAutocomplete(); return; }
  debounceTimer = setTimeout(() => fetchAutocomplete(q), 150);
}
async function fetchAutocomplete(q) {
  try {
    const data = await apiFetch("autocomplete", { q });
    const selected = new Set([...state.includeTags, ...state.excludeTags]);
    state.autocompleteItems = data.tags.filter(t => t.tag !== null && !selected.has(t.tag));
    state.autocompleteIndex = -1;
    renderAutocomplete();
  } catch { hideAutocomplete(); }
}
function renderAutocomplete() {
  if (state.autocompleteItems.length === 0) { hideAutocomplete(); return; }
  autocompleteEl.innerHTML = state.autocompleteItems.map((t, i) =>
    '<div class="item' + (i === state.autocompleteIndex ? ' selected' : '') + '" data-tag="' + esc(t.tag) + '"><span>' + highlight(t.tag, input.value.trim()) + '</span><span class="count">' + t.count.toLocaleString() + '</span></div>'
  ).join("");
  autocompleteEl.style.display = "block";
  autocompleteEl.querySelectorAll(".item").forEach(el => { el.addEventListener("click", () => addIncludeTag(el.dataset.tag)); });
}
function hideAutocomplete() { autocompleteEl.style.display = "none"; state.autocompleteItems = []; state.autocompleteIndex = -1; }
function highlight(text, query) {
  if (!text) return '';
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx < 0) return esc(text);
  return esc(text.slice(0, idx)) + "<strong>" + esc(text.slice(idx, idx + query.length)) + "</strong>" + esc(text.slice(idx + query.length));
}
function addIncludeTag(tag) { if (!state.includeTags.includes(tag) && !state.excludeTags.includes(tag)) state.includeTags.push(tag); input.value = ""; hideAutocomplete(); refresh(); input.focus(); }
function addExcludeTag(tag) { if (!state.excludeTags.includes(tag) && !state.includeTags.includes(tag)) state.excludeTags.push(tag); refresh(); }
function removeTag(tag) { state.includeTags = state.includeTags.filter(t => t !== tag); state.excludeTags = state.excludeTags.filter(t => t !== tag); refresh(); }
function toggleTagType(tag) {
  if (state.includeTags.includes(tag)) { state.includeTags = state.includeTags.filter(t => t !== tag); state.excludeTags.push(tag); }
  else if (state.excludeTags.includes(tag)) { state.excludeTags = state.excludeTags.filter(t => t !== tag); state.includeTags.push(tag); }
  refresh();
}
function renderSelectedTags() {
  let html = "";
  state.includeTags.forEach(tag => { html += '<span class="tag include" data-tag="' + esc(tag) + '">+' + esc(tag) + '</span>'; });
  state.excludeTags.forEach(tag => { html += '<span class="tag exclude" data-tag="' + esc(tag) + '">\u2212' + esc(tag) + '</span>'; });
  selectedTagsEl.innerHTML = html;
  selectedTagsEl.querySelectorAll(".tag").forEach(el => {
    let lt, wl;
    el.addEventListener("mousedown", () => { wl = false; lt = setTimeout(() => { wl = true; removeTag(el.dataset.tag); }, 500); });
    el.addEventListener("mouseup", () => { clearTimeout(lt); if (!wl) toggleTagType(el.dataset.tag); });
    el.addEventListener("mouseleave", () => clearTimeout(lt));
    el.addEventListener("dblclick", () => removeTag(el.dataset.tag));
    el.addEventListener("contextmenu", e => e.preventDefault());
  });
}
async function fetchCooccurrence() {
  if (state.includeTags.length === 0 && state.activeTypes.length === 0) { coocSection.style.display = "none"; return; }
  try {
    var cp = { include: state.includeTags, exclude: state.excludeTags };
    if (state.activeTypes.length > 0) cp.types = state.activeTypes.join(",");
    const data = await apiFetch("cooccurrence", cp);
    renderCooccurrence(data.tags);
  } catch { coocSection.style.display = "none"; }
}
function _renderCoocTags() {
  var sorted = _coocSortByCount ? [..._coocData] : [..._coocData].sort((a,b) => a.tag < b.tag ? -1 : 1);
  coocTagsEl.innerHTML = sorted.map(t => '<span class="cooc-tag" data-tag="' + esc(t.tag) + '">' + esc(t.tag) + ' <span class="cnt">' + t.count.toLocaleString() + '</span></span>').join("");
  coocTagsEl.querySelectorAll(".cooc-tag").forEach(el => {
    let lt, wl;
    el.addEventListener("mousedown", () => { wl = false; lt = setTimeout(() => { wl = true; addExcludeTag(el.dataset.tag); }, 500); });
    el.addEventListener("mouseup", () => { clearTimeout(lt); if (!wl) addIncludeTag(el.dataset.tag); });
    el.addEventListener("mouseleave", () => clearTimeout(lt));
    el.addEventListener("dblclick", e => { e.preventDefault(); removeTag(el.dataset.tag); addExcludeTag(el.dataset.tag); });
    el.addEventListener("contextmenu", e => e.preventDefault());
  });
}
function toggleCooc() {
  _coocOpen = !_coocOpen;
  coocTagsEl.style.display = _coocOpen ? '' : 'none';
  const arrow = document.getElementById('cooc-arrow');
  if (arrow) arrow.style.transform = _coocOpen ? 'rotate(90deg)' : '';
}
function toggleCoocSort() {
  _coocSortByCount = !_coocSortByCount;
  const btn = document.getElementById('cooc-sort-btn');
  if (btn) btn.textContent = 'tri: \u00a0' + (_coocSortByCount ? '\ud83d\udd22' : '\ud83d\udd24');
  _renderCoocTags();
}
function renderCooccurrence(tags) {
  if (!tags || tags.length === 0) { coocSection.style.display = "none"; return; }
  _coocData = tags;
  coocSection.style.display = "block";
  _renderCoocTags();
}
function _showHome() {
  document.getElementById('home-section').style.display = '';
  document.querySelector('.container').style.display = 'none';
  document.getElementById('type-filters').style.display = 'none';
  coocSection.style.display = 'none';
}
function _showResults() {
  document.getElementById('home-section').style.display = 'none';
  document.querySelector('.container').style.display = '';
  document.getElementById('type-filters').style.display = '';
}
function sortResults(results) {
  if (!state.sortBy || state.sortBy === 'relevance') return results;
  return [...results].sort((a, b) => {
    const na = (a.nom || a.title || '').toLowerCase(), nb = (b.nom || b.title || '').toLowerCase();
    const da = a.date_modif || a.date_sent || a.deadline_date || '', db = b.date_modif || b.date_sent || b.deadline_date || '';
    if (state.sortBy === 'name_asc') return na < nb ? -1 : 1;
    if (state.sortBy === 'name_desc') return na > nb ? -1 : 1;
    if (state.sortBy === 'date_desc') return da > db ? -1 : 1;
    if (state.sortBy === 'date_asc') return da < db ? -1 : 1;
    return 0;
  });
}
function setSortBy(val) { state.sortBy = val; state.currentOffset = 0; fetchResults(); }
async function fetchResults() {
  if (_currentDetailProjectId !== null) { _filterDetailPanel(); return; }
  if (state.includeTags.length === 0 && state.activeTypes.length === 0) { _showHome(); return; }
  _showResults(); emptyState.style.display = "none";
  try {
    var sp = { include: state.includeTags, exclude: state.excludeTags, limit: state.pageSize, offset: state.currentOffset };
    if (state.activeTypes.length > 0) sp.types = state.activeTypes.join(",");
    const data = await apiFetch("search", sp);
    state.totalResults = data.total;
    if (!data.results || !data.results.length) { emptyState.style.display = 'block'; resultsHeader.style.display = 'none'; return; }
    renderResults(sortResults(data.results));
  } catch { resultsList.innerHTML = '<div style="padding:20px;color:#aaa;text-align:center">Erreur de chargement</div>'; }
}
function renderResults(results) {
  resultsHeader.style.display = "flex";
  const start = state.currentOffset + 1;
  const end = Math.min(state.currentOffset + results.length, state.totalResults);
  resultsCount.textContent = start + "-" + end + " sur " + state.totalResults.toLocaleString();
  let nav = "";
  if (state.currentOffset > 0) nav += '<a href="#" id="prev-page">\u2190 Prec</a> ';
  if (state.currentOffset + state.pageSize < state.totalResults) nav += '<a href="#" id="next-page">Suiv \u2192</a>';
  resultsNav.innerHTML = nav;
  document.getElementById("prev-page")?.addEventListener("click", e => { e.preventDefault(); state.currentOffset = Math.max(0, state.currentOffset - state.pageSize); fetchResults(); });
  document.getElementById("next-page")?.addEventListener("click", e => { e.preventDefault(); state.currentOffset += state.pageSize; fetchResults(); });
  if (results.length === 0) { resultsList.innerHTML = '<div style="padding:20px;color:#aaa;text-align:center">Aucun resultat</div>'; return; }
  var fh = function(id) { return '<span class="fav-btn" data-fav-id="' + id + '" title="Favori"><i class="fa-regular fa-heart"></i></span>'; };
  resultsList.innerHTML = results.map(r => {
    if (r.type === "email") {
      var sn = r.snippet ? '<div class="result-snippet">' + esc(r.snippet) + '</div>' : '';
      var delBtn = '<button class="delete-btn" data-item-id="' + r.id + '" data-item-type="email" title="Supprimer cet email" style="margin-left:auto"><i class="fa-solid fa-trash"></i></button>';
      return '<div class="result-item result-email" data-id="' + r.id + '"><span class="result-icon icon-email"><i class="fa-solid fa-envelope"></i></span><div class="result-body"><div class="result-name" style="display:flex;align-items:center">' + esc(r.nom) + fh(r.id) + delBtn + '</div><div class="result-meta">' + esc(r.chemin) + '</div>' + sn + '<div class="result-meta">' + (r.date_modif || "?") + '</div></div></div>';
    }
    if (r.type === "note") {
      var delBtn = '<button class="delete-btn" data-item-id="' + r.id + '" data-item-type="note" title="Supprimer" style="margin-left:auto"><i class="fa-solid fa-trash"></i></button>';
      return '<div class="result-item result-note" data-id="' + r.id + '"><span class="result-icon icon-note"><i class="fa-solid fa-note-sticky"></i></span><div class="result-body"><div class="result-name" style="display:flex;align-items:center">' + esc(r.nom) + fh(r.id) + delBtn + '</div><div class="result-meta">' + esc(r.chemin) + '</div><div class="result-meta">' + (r.date_modif || "?") + '</div></div></div>';
    }
    if (r.type === "video") {
      var pIcon = {"youtube":'<i class="fa-brands fa-youtube"></i>',"facebook":'<i class="fa-brands fa-facebook"></i>',"vimeo":'<i class="fa-brands fa-vimeo-v"></i>',"dailymotion":'<i class="fa-solid fa-play"></i>',"instagram":'<i class="fa-brands fa-instagram"></i>',"tiktok":'<i class="fa-brands fa-tiktok"></i>'}[r.platform] || '<i class="fa-solid fa-play"></i>';
      var delBtn = '<button class="delete-btn" data-item-id="' + r.id + '" data-item-type="video" title="Supprimer" style="margin-left:auto"><i class="fa-solid fa-trash"></i></button>';
      return '<div class="result-item result-video" data-id="' + r.id + '" data-url="' + esc(r.url || r.chemin) + '"><span class="result-icon icon-video">' + pIcon + '</span><div class="result-body"><div class="result-name" style="display:flex;align-items:center">' + esc(r.nom) + fh(r.id) + delBtn + '</div><div class="result-meta">' + esc(r.platform || "") + ' \u00b7 ' + (r.date_modif || "?") + '</div><div class="result-meta" style="font-size:10px;color:#999;word-break:break-all">' + esc(r.url || r.chemin) + '</div></div></div>';
    }
    if (r.type === "event") {
      var recStr = r.recurrence && r.recurrence !== "none" ? ' \u00b7 <i class="fa-solid fa-rotate"></i> ' + ({"daily":"chaque jour","weekly":"chaque semaine","monthly":"chaque mois","yearly":"chaque ann\u00e9e"}[r.recurrence] || "") : "";
      var tagsStr = r.tags_raw ? '<div class="result-meta" style="margin-top:2px">' + esc(r.tags_raw) + '</div>' : '';
      var delBtn = '<button class="delete-btn" data-item-id="' + r.id + '" data-item-type="event" title="Supprimer" style="margin-left:auto"><i class="fa-solid fa-trash"></i></button>';
      return '<div class="result-item result-event" data-id="' + r.id + '"><span class="result-icon icon-event"><i class="fa-solid fa-calendar-days"></i></span><div class="result-body"><div class="result-name" style="display:flex;align-items:center">' + esc(r.nom) + fh(r.id) + delBtn + '</div><div class="result-meta">' + esc(r.date_fr || r.date_modif || "") + recStr + '</div>' + tagsStr + '</div></div>';
    }
    if (r.type === "contact") {
      var ctIcon = r.contact_type === "entreprise" ? '<i class="fa-solid fa-building"></i>' : '<i class="fa-solid fa-user"></i>';
      var delBtn = '<button class="delete-btn" data-item-id="' + r.id + '" data-item-type="contact" title="Supprimer" style="margin-left:auto"><i class="fa-solid fa-trash"></i></button>';
      return '<div class="result-item result-contact" data-id="' + r.id + '"><span class="result-icon icon-contact">' + ctIcon + '</span><div class="result-body"><div class="result-name" style="display:flex;align-items:center">' + esc(r.nom) + fh(r.id) + delBtn + '</div><div class="result-meta">' + esc(r.chemin) + '</div></div></div>';
    }
    if (r.type === "lieu") {
      var delBtn = '<button class="delete-btn" data-item-id="' + r.id + '" data-item-type="lieu" title="Supprimer" style="margin-left:auto"><i class="fa-solid fa-trash"></i></button>';
      return '<div class="result-item result-lieu" data-id="' + r.id + '"><span class="result-icon icon-lieu"><i class="fa-solid fa-location-dot"></i></span><div class="result-body"><div class="result-name" style="display:flex;align-items:center">' + esc(r.nom) + fh(r.id) + delBtn + '</div><div class="result-meta">' + esc(r.chemin) + '</div></div></div>';
    }
    if (r.type === "vault") {
      var delBtn = '<button class="delete-btn" data-item-id="' + r.id + '" data-item-type="vault" title="Supprimer" style="margin-left:auto"><i class="fa-solid fa-trash"></i></button>';
      return '<div class="result-item result-vault" data-id="' + r.id + '"><span class="result-icon icon-vault"><i class="fa-solid fa-lock"></i></span><div class="result-body"><div class="result-name" style="display:flex;align-items:center">' + esc(r.nom) + fh(r.id) + delBtn + '</div><div class="result-meta">' + esc(r.chemin) + (r.project ? ' \u00b7 ' + esc(r.project) : '') + '</div></div></div>';
    }
    if (r.type === "projet") {
      var cat = r.category ? '<span style="font-size:10px;padding:1px 6px;border-radius:10px;background:#e8f0fe;color:#1a73e8;margin-left:6px">' + esc(r.category) + '</span>' : '';
      var status = r.status ? '<span style="font-size:10px;padding:1px 6px;border-radius:10px;background:#f0f0f0;color:#666;margin-left:4px">' + esc(r.status) + '</span>' : '';
      var tags = r.tags_raw ? '<div class="result-meta" style="margin-top:2px">' + r.tags_raw.split(',').filter(t=>t.trim()).map(t=>'<span style="font-size:10px;background:#f0f0f0;padding:1px 5px;border-radius:8px;margin-right:3px">' + esc(t.trim()) + '</span>').join('') + '</div>' : '';
      var desc = r.description ? '<div class="result-snippet">' + esc(r.description.slice(0,120)) + '</div>' : '';
      var counts = '';
      if (r.nb_chantiers > 0 || r.nb_tasks > 0) {
        counts = '<div class="result-meta" style="margin-top:3px;display:flex;gap:10px">';
        if (r.nb_chantiers > 0) counts += '<span style="font-size:11px;color:#6366f1"><i class="fa-solid fa-layer-group" style="margin-right:3px"></i>' + r.nb_chantiers + ' chantier' + (r.nb_chantiers > 1 ? 's' : '') + '</span>';
        if (r.nb_tasks > 0) counts += '<span style="font-size:11px;color:#6b7280"><i class="fa-solid fa-circle-dot" style="margin-right:3px"></i>' + r.nb_tasks + ' t\u00e2che' + (r.nb_tasks > 1 ? 's' : '') + '</span>';
        counts += '</div>';
      }
      return '<div class="result-item result-projet" data-id="' + r.id + '"><span class="result-icon" style="color:#2e7d32"><i class="fa-solid fa-folder-tree"></i></span><div class="result-body"><div class="result-name" style="display:flex;align-items:center">' + esc(r.nom) + cat + status + '</div>' + desc + counts + tags + '</div></div>';
    }
    var iconHtml = r.is_media ? '<img class="thumb" data-thumb-id="' + r.id + '" src="" alt="" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'inline\'" style="display:none"><span>' + (r.est_dossier ? '<i class="fa-solid fa-folder icon-file"></i>' : fileIcon(r.extension)) + '</span>' : '<span>' + (r.est_dossier ? '<i class="fa-solid fa-folder icon-file"></i>' : fileIcon(r.extension)) + '</span>';
    var delBtn = '<button class="delete-btn" data-item-id="' + r.id + '" data-item-type="file" title="Supprimer" style="margin-left:auto"><i class="fa-solid fa-trash"></i></button>';
    return '<div class="result-item" data-id="' + r.id + '"><span class="result-icon">' + iconHtml + '</span><div class="result-body"><div class="result-name" style="display:flex;align-items:center">' + esc(r.nom) + fh(r.id) + delBtn + '</div><div class="result-meta">' + formatSize(r.taille) + ' \u00b7 ' + (r.date_modif || "?") + '</div></div><div class="result-actions"><span class="action-btn open-btn" data-id="' + r.id + '" title="Ouvrir"><i class="fa-solid fa-arrow-up-right-from-square"></i></span><span class="action-btn reveal-btn" data-id="' + r.id + '" title="Finder"><i class="fa-solid fa-folder-open"></i></span></div></div>';
  }).join("");
  // Charger les miniatures en lazy
  resultsList.querySelectorAll("img.thumb[data-thumb-id]").forEach(function(img) {
    apiFetch("thumbnail", { id: img.dataset.thumbId, size: "80" }).then(function(d) {
      if (d.data) { img.src = d.data; img.style.display = "block"; img.nextElementSibling.style.display = "none"; }
    }).catch(function() {});
  });
  resultsList.querySelectorAll(".result-event").forEach(el => {
    el.addEventListener("click", () => toggleEventView(el));
  });
  resultsList.querySelectorAll(".result-contact").forEach(el => {
    el.addEventListener("click", () => toggleContactView(el));
  });
  resultsList.querySelectorAll(".result-lieu").forEach(el => {
    el.addEventListener("click", () => toggleLieuView(el));
  });
  resultsList.querySelectorAll(".result-item:not(.result-email):not(.result-note):not(.result-vault):not(.result-video):not(.result-event):not(.result-contact):not(.result-lieu):not(.result-projet)").forEach(el => {
    el.addEventListener("click", e => { if (e.target.classList.contains("action-btn")) return; openFile(el.dataset.id); });
  });
  resultsList.querySelectorAll(".result-projet").forEach(el => {
    el.addEventListener("click", e => { e.stopPropagation(); showProjectDetail(parseInt(el.dataset.id)); });
  });
  resultsList.querySelectorAll(".result-email").forEach(el => {
    el.addEventListener("click", () => toggleEmailView(el));
  });
  // Fonction d'affichage du modal de suppression
  function showDeleteModal(itemId, itemType, itemName) {
    return new Promise((resolve) => {
      var modal = document.getElementById("delete-modal");
      var nameEl = document.getElementById("delete-modal-name");
      var dbOnlyBtn = document.getElementById("delete-db-only");
      var permanentBtn = document.getElementById("delete-permanent");
      var permanentDesc = document.getElementById("delete-permanent-desc");
      var cancelBtn = document.getElementById("delete-cancel");

      var descriptions = {
        email: "Supprimer du serveur IMAP",
        file: "Mettre \u00e0 la corbeille",
        note: "Tout supprimer",
        vault: "Tout supprimer",
        video: "Tout supprimer",
        event: "Tout supprimer",
        contact: "Tout supprimer",
        lieu: "Tout supprimer"
      };

      nameEl.textContent = itemName;
      permanentDesc.textContent = descriptions[itemType] || "Tout supprimer";
      modal.classList.add("active");

      var cleanup = () => {
        modal.classList.remove("active");
        dbOnlyBtn.removeEventListener("click", handleDbOnly);
        permanentBtn.removeEventListener("click", handlePermanent);
        cancelBtn.removeEventListener("click", handleCancel);
      };

      var handleDbOnly = () => { cleanup(); resolve("db_only"); };
      var handlePermanent = () => { cleanup(); resolve("permanent"); };
      var handleCancel = () => { cleanup(); resolve(null); };

      dbOnlyBtn.addEventListener("click", handleDbOnly);
      permanentBtn.addEventListener("click", handlePermanent);
      cancelBtn.addEventListener("click", handleCancel);
    });
  }

  resultsList.querySelectorAll(".delete-btn").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      var itemId = btn.dataset.itemId;
      var itemType = btn.dataset.itemType;
      var itemName = btn.closest(".result-item").querySelector(".result-name").textContent.trim();

      var mode = await showDeleteModal(itemId, itemType, itemName);
      if (!mode) return;

      try {
        var resp = await fetch(API + "/" + itemType, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ item_id: parseInt(itemId), mode: mode })
        });
        var result = await resp.json();
        if (result.success) {
          btn.closest(".result-item").remove();
          state.totalResults--;
          renderResultsCount();
        } else {
          alert("Erreur : " + (result.error || "Suppression \u00e9chou\u00e9e"));
        }
      } catch (err) {
        alert("Erreur r\u00e9seau : " + err.message);
      }
    });
  });
  resultsList.querySelectorAll(".result-vault").forEach(el => {
    el.addEventListener("click", () => toggleVaultView(el));
  });
  resultsList.querySelectorAll(".result-note").forEach(el => {
    el.addEventListener("click", () => toggleNoteView(el));
  });
  resultsList.querySelectorAll(".result-video").forEach(el => {
    el.addEventListener("click", () => { window.open(el.dataset.url, "_blank"); });
  });
  resultsList.querySelectorAll(".open-btn").forEach(el => { el.addEventListener("click", () => openFile(el.dataset.id)); });
  resultsList.querySelectorAll(".reveal-btn").forEach(el => { el.addEventListener("click", () => revealFile(el.dataset.id)); });
  resultsList.querySelectorAll(".fav-btn").forEach(function(btn) { btn.addEventListener("click", function(e) { e.stopPropagation(); toggleFavorite(btn.dataset.favId, btn); }); });
  var allIds = results.map(function(r) { return r.id; });
  checkFavorites(allIds);
}
async function openFile(id) { try { await apiFetch("open", { id }); } catch {} }
async function revealFile(id) { try { await apiFetch("reveal", { id }); } catch {} }
function linkifyBody(text) {
  var escaped = esc(text);
  return escaped.replace(/(https?:\/\/[^\s<]+)/g, function(url) {
    var isVideo = /youtube\.com|youtu\.be|vimeo\.com|dailymotion\.com|facebook\.com\/.*\/videos/i.test(url);
    var cls = isVideo ? 'video-link' : '';
    var icon = isVideo ? '<i class="fa-solid fa-play"></i> ' : '';
    return '<a href="' + url + '" target="_blank" class="' + cls + '" onclick="event.stopPropagation()">' + icon + url + '</a>';
  });
}

async function renderItemTags(itemId, container) {
  try {
    const resp = await fetch(API + '/tags/get?item_id=' + itemId);
    const data = await resp.json();

    let html = '<div class="add-tag-section" style="display:flex;gap:4px;margin:12px 0 8px 0;">';
    html += '<input type="text" class="add-tag-input" placeholder="Ajouter un tag..." style="flex:1;padding:4px 8px;border:1px solid #ccc;border-radius:4px;font-size:11px;">';
    html += '<button class="add-tag-btn" title="Ajouter ce tag" style="width:24px;height:24px;border-radius:50%;border:2px solid #27ae60;background:#fff;color:#27ae60;font-size:16px;cursor:pointer;line-height:1;">+</button>';
    html += '<div class="add-tag-dropdown" style="display:none;position:absolute;background:#fff;border:1px solid #ccc;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.1);z-index:1000;max-height:200px;overflow-y:auto;"></div>';
    html += '</div><div class="tags-list" style="margin-top:8px;">';

    if (!data.tags || data.tags.length === 0) {
      html += '<div style="color:#999;font-size:11px;font-style:italic">Aucun tag</div>';
    } else {
      html += data.tags.map(tag => '<span class="item-tag" data-tag="' + esc(tag) + '">' + esc(tag) + ' <button class="tag-remove-btn" title="Supprimer ce tag">×</button></span>').join('');
    }
    html += '</div>';
    container.innerHTML = html;

    const inputEl = container.querySelector('.add-tag-input');
    const btnEl = container.querySelector('.add-tag-btn');
    const dropdownEl = container.querySelector('.add-tag-dropdown');
    let debounceTimer;

    inputEl.addEventListener('input', async (e) => {
      const q = e.target.value.trim();
      clearTimeout(debounceTimer);
      if (q.length < 2) { dropdownEl.style.display = 'none'; return; }

      debounceTimer = setTimeout(async () => {
        try {
          const acData = await apiFetch('autocomplete', { q });
          const existing = new Set(data.tags || []);
          const filtered = (acData.tags || []).filter(t => !existing.has(t.tag)).slice(0, 8);
          let dropHtml = filtered.map(t => '<div class="ac-item" data-tag="' + esc(t.tag) + '" style="padding:6px 8px;cursor:pointer;font-size:11px;">' + esc(t.tag) + ' <span style="color:#888;font-size:10px">(' + t.count + ')</span></div>').join('');
          if (!filtered.some(t => t.tag === q.toLowerCase())) {
            dropHtml += '<div class="ac-item create" data-tag="' + esc(q.toLowerCase()) + '" style="padding:6px 8px;cursor:pointer;font-size:11px;border-top:1px solid #eee;">Créer "' + esc(q) + '"</div>';
          }
          dropdownEl.innerHTML = dropHtml;
          dropdownEl.style.display = dropHtml ? 'block' : 'none';
          const rect = inputEl.getBoundingClientRect();
          dropdownEl.style.position = 'absolute';
          dropdownEl.style.top = (rect.bottom + 2) + 'px';
          dropdownEl.style.left = rect.left + 'px';
          dropdownEl.style.width = rect.width + 'px';
          dropdownEl.querySelectorAll('.ac-item').forEach(el => {
            el.addEventListener('click', () => { inputEl.value = el.dataset.tag; dropdownEl.style.display = 'none'; });
          });
        } catch (err) { console.error('Autocomplete error:', err); }
      }, 300);
    });

    document.addEventListener('click', (e) => { if (!container.contains(e.target)) { dropdownEl.style.display = 'none'; } });

    btnEl.addEventListener('click', async (e) => {
      e.stopPropagation();
      const tagToAdd = inputEl.value.trim().toLowerCase();
      if (!tagToAdd) { alert('Entrez un tag à ajouter'); return; }
      try {
        const addResp = await fetch(API + '/tags/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ item_id: itemId, tag: tagToAdd })
        });
        const addResult = await addResp.json();
        if (addResult.success) {
          inputEl.value = '';
          dropdownEl.style.display = 'none';
          renderItemTags(itemId, container);
        } else {
          alert('Erreur : ' + (addResult.error || 'Ajout échoué'));
        }
      } catch (err) { alert('Erreur réseau : ' + err.message); }
    });

    inputEl.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); btnEl.click(); } });

    container.querySelectorAll('.tag-remove-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const tagEl = e.target.parentElement;
        const tag = tagEl.dataset.tag;
        if (!confirm('Supprimer le tag "' + tag + '" ?')) return;
        try {
          const resp = await fetch(API + '/tags/delete', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId, tag })
          });
          const result = await resp.json();
          if (result.success) {
            renderItemTags(itemId, container);
          } else {
            alert('Erreur : ' + (result.error || 'Suppression échouée'));
          }
        } catch (err) { alert('Erreur réseau : ' + err.message); }
      });
    });
  } catch (err) {
    container.innerHTML = '<div style="color:#c0392b;font-size:11px">Erreur chargement tags</div>';
  }
}

async function toggleNoteView(el) {
  var id = el.dataset.id;
  var ex = el.nextElementSibling;
  if (ex && ex.classList.contains("note-content")) { ex.remove(); return; }
  document.querySelectorAll(".note-content, .note-loading").forEach(function(e) { e.remove(); });
  var ld = document.createElement("div"); ld.className = "note-loading"; ld.textContent = "Chargement\u2026";
  el.after(ld);
  try {
    var data = await apiFetch("note", { id: id });
    ld.remove();
    if (data.error) { var err = document.createElement("div"); err.className = "note-content"; err.innerHTML = '<div style="color:#c00">' + esc(data.error) + '</div>'; el.after(err); return; }
    var div = document.createElement("div"); div.className = "note-content";
    var ttl = document.createElement("div"); ttl.className = "note-title"; ttl.textContent = data.title || "(sans titre)"; div.appendChild(ttl);
    var dt = document.createElement("div"); dt.className = "note-date"; dt.textContent = data.date || ""; div.appendChild(dt);
    var hr = document.createElement("hr"); hr.style.cssText = "border:none;border-top:1px solid #e0d5c0;margin:6px 0"; div.appendChild(hr);
    var body = document.createElement("div"); body.className = "note-body"; body.innerHTML = linkifyBody(data.body || "(vide)"); div.appendChild(body);
    var tagsSection = document.createElement("div"); tagsSection.innerHTML = '<div style="margin-top:12px;font-weight:600;font-size:11px;color:#666;text-transform:uppercase;">Tags</div><div class="tags-container"></div>'; div.appendChild(tagsSection);
    el.after(div);
    renderItemTags(id, div.querySelector('.tags-container'));
  } catch { ld.remove(); }
}
let expandedEmailId = null;
async function toggleEmailView(el) {
  const id = el.dataset.id;
  const existing = el.nextElementSibling;
  if (existing && existing.classList.contains("email-content")) { existing.remove(); expandedEmailId = null; return; }
  document.querySelectorAll(".email-content, .email-loading").forEach(e => e.remove());
  const loading = document.createElement("div"); loading.className = "email-loading"; loading.textContent = "Chargement\u2026";
  el.after(loading); expandedEmailId = id;
  try {
    const data = await apiFetch("email", { id });
    loading.remove();
    if (expandedEmailId !== id) return;
    if (data.error) { const err = document.createElement("div"); err.className = "email-content"; err.innerHTML = '<div style="color:#c00">Erreur : ' + esc(data.error) + '</div>'; el.after(err); return; }
    const div = document.createElement("div"); div.className = "email-content";
    const subj = document.createElement("div"); subj.className = "eml-hdr"; subj.innerHTML = "<strong>" + esc(data.subject || "(sans sujet)") + "</strong>"; div.appendChild(subj);
    const ft = document.createElement("div"); ft.className = "eml-hdr"; ft.textContent = "De : " + (data.from || "?") + "  \u2192  " + (data.to || "?"); div.appendChild(ft);
    const dt = document.createElement("div"); dt.className = "eml-hdr"; dt.textContent = data.date || ""; div.appendChild(dt);
    const hr = document.createElement("hr"); hr.style.cssText = "border:none;border-top:1px solid #ddd;margin:8px 0"; div.appendChild(hr);
    if (data.body_html) {
      const iframe = document.createElement("iframe"); iframe.sandbox = "allow-same-origin"; iframe.style.cssText = "width:100%;border:none;min-height:200px;background:#fff;border-radius:4px;"; iframe.srcdoc = data.body_html; div.appendChild(iframe);
      iframe.addEventListener("load", () => { try { const h = iframe.contentDocument.body.scrollHeight; iframe.style.height = Math.min(h + 20, 500) + "px"; } catch {} });
    } else if (data.body_text) { const pre = document.createElement("pre"); pre.textContent = data.body_text; div.appendChild(pre); }
    else { const em = document.createElement("div"); em.style.color = "#aaa"; em.textContent = "(contenu vide)"; div.appendChild(em); }
    const tagsSection = document.createElement("div"); tagsSection.innerHTML = '<div style="margin-top:12px;font-weight:600;font-size:11px;color:#666;text-transform:uppercase;">Tags</div><div class="tags-container"></div>'; div.appendChild(tagsSection);
    el.after(div);
    renderItemTags(id, div.querySelector('.tags-container'));
  } catch { loading.remove(); const err = document.createElement("div"); err.className = "email-content"; err.innerHTML = '<div style="color:#c00">Impossible de charger</div>'; el.after(err); }
}
function refresh() { state.currentOffset = 0; renderTypeFilters(); renderSelectedTags(); fetchResults(); fetchCooccurrence(); }
input.addEventListener("input", onInput);
input.addEventListener("keydown", e => {
  const items = state.autocompleteItems;
  if (e.key === "ArrowDown") { e.preventDefault(); state.autocompleteIndex = Math.min(state.autocompleteIndex + 1, items.length - 1); renderAutocomplete(); }
  else if (e.key === "ArrowUp") { e.preventDefault(); state.autocompleteIndex = Math.max(state.autocompleteIndex - 1, -1); renderAutocomplete(); }
  else if (e.key === "Enter") { e.preventDefault(); if (state.autocompleteIndex >= 0 && items[state.autocompleteIndex]) addIncludeTag(items[state.autocompleteIndex].tag); else if (items.length > 0) addIncludeTag(items[0].tag); }
  else if (e.key === "Escape") hideAutocomplete();
  else if (e.key === "Backspace" && input.value === "" && state.includeTags.length > 0) { state.includeTags.pop(); refresh(); }
});
function esc(str) { const d = document.createElement("div"); d.textContent = str; return d.innerHTML; }
function formatSize(bytes) { if (!bytes || bytes === 0) return "\u2014"; if (bytes < 1024) return bytes + " o"; if (bytes < 1048576) return (bytes / 1024).toFixed(0) + " Ko"; if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + " Mo"; return (bytes / 1073741824).toFixed(2) + " Go"; }
function fileIcon(ext) {
  if (!ext) return '<i class="fa-solid fa-file"></i>';
  ext = ext.toLowerCase();
  const icons = { ".py":'<i class="fa-brands fa-python"></i>',".js":'<i class="fa-brands fa-js"></i>',".ts":'<i class="fa-brands fa-js"></i>',".html":'<i class="fa-brands fa-html5"></i>',".css":'<i class="fa-brands fa-css3-alt"></i>',".md":'<i class="fa-solid fa-file-lines"></i>',".txt":'<i class="fa-solid fa-file-lines"></i>',".pdf":'<i class="fa-solid fa-file-pdf" style="color:#c00"></i>',".jpg":'<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',".jpeg":'<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',".png":'<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',".gif":'<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',".svg":'<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',".mp4":'<i class="fa-solid fa-file-video"></i>',".mov":'<i class="fa-solid fa-file-video"></i>',".mp3":'<i class="fa-solid fa-file-audio" style="color:#9b59b6"></i>',".wav":'<i class="fa-solid fa-file-audio" style="color:#9b59b6"></i>',".zip":'<i class="fa-solid fa-file-zipper" style="color:#7f8c8d"></i>',".json":'<i class="fa-solid fa-file-code"></i>',".xml":'<i class="fa-solid fa-file-code"></i>',".csv":'<i class="fa-solid fa-file-csv"></i>' };
  return icons[ext] || '<i class="fa-solid fa-file"></i>';
}
let vaultUnlocked = false;
async function checkVaultStatus() { try { const d = await apiFetch("vault/status"); vaultUnlocked = d.unlocked; } catch { vaultUnlocked = false; } }
async function toggleVaultView(el) {
  const id = el.dataset.id;
  const ex = el.nextElementSibling;
  if (ex && ex.classList.contains("vault-panel")) { ex.remove(); return; }
  document.querySelectorAll(".vault-panel, .vault-loading").forEach(e => e.remove());
  await checkVaultStatus();
  if (!vaultUnlocked) { showVaultModal(el); return; }
  loadVaultEntry(el, id);
}
function showVaultModal(afterEl) {
  const ov = document.createElement("div"); ov.className = "vault-modal-overlay";
  ov.innerHTML = '<div class="vault-modal"><h3><i class="fa-solid fa-lock"></i> Mot de passe maitre</h3><div class="vm-error" style="display:none"></div><input type="password" placeholder="Entrer le mot de passe maitre..." autofocus><div class="vm-btns"><button class="vm-btn vm-btn-cancel">Annuler</button><button class="vm-btn vm-btn-ok">OK</button></div></div>';
  document.body.appendChild(ov);
  const inp = ov.querySelector("input"), err = ov.querySelector(".vm-error");
  ov.querySelector(".vm-btn-cancel").addEventListener("click", () => ov.remove());
  ov.addEventListener("click", e => { if (e.target === ov) ov.remove(); });
  async function doUnlock() {
    const m = inp.value; if (!m) return;
    try {
      const r = await fetch(API + "/vault/unlock", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({master: m}) });
      const d = await r.json();
      if (d.ok) { vaultUnlocked = true; ov.remove(); if (afterEl) loadVaultEntry(afterEl, afterEl.dataset.id); }
      else { err.textContent = d.error || "Erreur"; err.style.display = "block"; inp.value = ""; inp.focus(); }
    } catch { err.textContent = "Erreur de connexion"; err.style.display = "block"; }
  }
  ov.querySelector(".vm-btn-ok").addEventListener("click", doUnlock);
  inp.addEventListener("keydown", e => { if (e.key === "Enter") doUnlock(); if (e.key === "Escape") ov.remove(); });
  inp.focus();
}
async function loadVaultEntry(el, id) {
  const ld = document.createElement("div"); ld.className = "vault-loading"; ld.textContent = "D\u00e9chiffrement\u2026";
  el.after(ld);
  try {
    const d = await apiFetch("vault/get", { id }); ld.remove();
    if (d.error) { const e = document.createElement("div"); e.className = "vault-panel"; e.innerHTML = '<div style="color:#c00">' + esc(d.error) + '</div>'; el.after(e); return; }
    const div = document.createElement("div"); div.className = "vault-panel";
    let h = '<div class="vp-row"><span class="vp-label">Service</span><span class="vp-value">' + esc(d.service) + '</span></div>';
    if (d.login) h += '<div class="vp-row"><span class="vp-label">Login</span><span class="vp-value">' + esc(d.login) + '</span></div>';
    if (d.password) {
      h += '<div class="vp-row"><span class="vp-label">Mdp</span><span class="vp-pwd" id="vp-pwd">\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF</span>';
      h += ' <button class="vp-btn" id="vp-show">Voir</button> <button class="vp-btn" id="vp-copy">Copier</button></div>';
    }
    if (d.url) h += '<div class="vp-row"><span class="vp-label">URL</span><span class="vp-value" style="font-size:11px">' + esc(d.url) + '</span></div>';
    if (d.notes) h += '<div class="vp-row"><span class="vp-label">Notes</span><span class="vp-value" style="font-size:11px">' + esc(d.notes) + '</span></div>';
    h += '<div style="margin-top:12px;font-weight:600;font-size:11px;color:#666;text-transform:uppercase;">Tags</div><div class="tags-container"></div>';
    div.innerHTML = h; el.after(div);
    renderItemTags(id, div.querySelector('.tags-container'));
    const showB = div.querySelector("#vp-show"), pwdD = div.querySelector("#vp-pwd");
    if (showB && pwdD) { let vis = false; showB.addEventListener("click", () => { vis = !vis; pwdD.textContent = vis ? d.password : "\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF"; showB.textContent = vis ? "Masquer" : "Voir"; }); }
    const copyB = div.querySelector("#vp-copy");
    if (copyB) { copyB.addEventListener("click", async () => { try { await apiFetch("vault/copy", { id }); copyB.textContent = "Copi\u00e9 !"; copyB.classList.add("copied"); setTimeout(() => { copyB.textContent = "Copier"; copyB.classList.remove("copied"); }, 2000); } catch { copyB.textContent = "Erreur"; } }); }
  } catch { ld.remove(); }
}
async function toggleEventView(el) {
  var id = el.dataset.id;
  var ex = el.nextElementSibling;
  if (ex && ex.classList.contains("event-content")) { ex.remove(); return; }
  document.querySelectorAll(".event-content").forEach(function(e) { e.remove(); });
  try {
    var data = await apiFetch("event", { id: id });
    if (data.error) return;
    var div = document.createElement("div"); div.className = "event-content";
    var h = '<div class="ev-title">' + esc(data.title) + '</div>';
    h += '<div class="ev-row"><span class="ev-label">Date</span>' + esc(data.date_fr || data.date_start) + '</div>';
    if (data.date_end) h += '<div class="ev-row"><span class="ev-label">Fin</span>' + esc(data.date_end) + '</div>';
    if (data.location) h += '<div class="ev-row"><span class="ev-label">Lieu</span>' + esc(data.location) + '</div>';
    if (data.description) h += '<div class="ev-row"><span class="ev-label">D\u00e9tail</span>' + esc(data.description) + '</div>';
    if (data.recurrence && data.recurrence !== "none") {
      var rl = {"daily":"chaque jour","weekly":"chaque semaine","monthly":"chaque mois","yearly":"chaque ann\u00e9e"}[data.recurrence] || data.recurrence;
      if (data.recurrence_interval > 1) rl = "tous les " + data.recurrence_interval + " " + ({"daily":"jours","weekly":"semaines","monthly":"mois","yearly":"ans"}[data.recurrence] || "");
      h += '<div class="ev-row"><span class="ev-label">R\u00e9currence</span><i class="fa-solid fa-rotate"></i> ' + rl + '</div>';
    }
    if (data.tags_raw) {
      h += '<div class="ev-tags">';
      data.tags_raw.split(",").forEach(function(t) { t = t.trim(); if (t) h += '<span class="ev-tag">' + esc(t) + '</span>'; });
      h += '</div>';
    }
    h += '<div style="margin-top:12px;font-weight:600;font-size:11px;color:#666;text-transform:uppercase;">Tags</div><div class="tags-container"></div>';
    div.innerHTML = h; el.after(div);
    renderItemTags(id, div.querySelector('.tags-container'));
  } catch(e) {}
}
function showEventForm() {
  var ov = document.createElement("div"); ov.className = "event-form-overlay";
  ov.innerHTML = '<div class="event-form"><h3><i class="fa-solid fa-calendar-days"></i> Nouvel \u00e9v\u00e9nement</h3>' +
    '<label>Titre *</label><input type="text" id="ef-title" placeholder="Ex: Anniversaire Maman">' +
    '<div class="ef-row"><div><label>Date d\u00e9but *</label><input type="date" id="ef-date"></div><div><label>Heure</label><input type="time" id="ef-time"></div></div>' +
    '<div class="ef-row"><div><label>Date fin</label><input type="date" id="ef-date-end"></div><div><label>Heure fin</label><input type="time" id="ef-time-end"></div></div>' +
    '<label>Lieu</label><input type="text" id="ef-loc" placeholder="Optionnel">' +
    '<label>Description</label><textarea id="ef-desc" placeholder="Optionnel"></textarea>' +
    '<label>Tags (s\u00e9par\u00e9s par virgule)</label><input type="text" id="ef-tags" placeholder="famille, anniversaire">' +
    '<div class="ef-row"><div><label>R\u00e9currence</label><select id="ef-rec"><option value="none">Aucune</option><option value="daily">Quotidienne</option><option value="weekly">Hebdomadaire</option><option value="monthly">Mensuelle</option><option value="yearly">Annuelle</option></select></div>' +
    '<div><label>Intervalle</label><input type="number" id="ef-interval" value="1" min="1"></div></div>' +
    '<div class="ef-row"><div><label>Nb occurrences</label><input type="number" id="ef-count" placeholder="Illimit\u00e9" min="1"></div>' +
    '<div><label>Fin r\u00e9currence</label><input type="date" id="ef-rec-end"></div></div>' +
    '<div class="ef-error" id="ef-error"></div>' +
    '<div class="ef-btns"><button class="ef-btn ef-btn-cancel">Annuler</button><button class="ef-btn ef-btn-ok">Cr\u00e9er</button></div></div>';
  document.body.appendChild(ov);
  ov.querySelector(".ef-btn-cancel").addEventListener("click", function() { ov.remove(); });
  ov.addEventListener("click", function(e) { if (e.target === ov) ov.remove(); });
  ov.querySelector(".ef-btn-ok").addEventListener("click", async function() {
    var title = ov.querySelector("#ef-title").value.trim();
    var date = ov.querySelector("#ef-date").value;
    var time = ov.querySelector("#ef-time").value;
    if (!title || !date) { var err = ov.querySelector("#ef-error"); err.textContent = "Titre et date requis"; err.style.display = "block"; return; }
    var dateStart = date + (time ? " " + time : "");
    var dateEndVal = ov.querySelector("#ef-date-end").value;
    var timeEnd = ov.querySelector("#ef-time-end").value;
    var dateEnd = dateEndVal ? dateEndVal + (timeEnd ? " " + timeEnd : "") : "";
    var body = {
      title: title,
      date_start: dateStart,
      date_end: dateEnd || null,
      description: ov.querySelector("#ef-desc").value.trim(),
      location: ov.querySelector("#ef-loc").value.trim(),
      tags_raw: ov.querySelector("#ef-tags").value.trim(),
      recurrence: ov.querySelector("#ef-rec").value,
      recurrence_interval: parseInt(ov.querySelector("#ef-interval").value) || 1,
      recurrence_count: parseInt(ov.querySelector("#ef-count").value) || null,
      recurrence_end: ov.querySelector("#ef-rec-end").value || null
    };
    try {
      var resp = await fetch(API + "/event", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body) });
      var data = await resp.json();
      if (data.error) { var err = ov.querySelector("#ef-error"); err.textContent = data.error; err.style.display = "block"; return; }
      ov.remove(); refresh();
    } catch(e) { var err = ov.querySelector("#ef-error"); err.textContent = "Erreur de connexion"; err.style.display = "block"; }
  });
  ov.querySelector("#ef-title").focus();
}
async function fetchUpcomingEvents(mode) {
  try {
    var data = await apiFetch("events/upcoming", { mode: mode || "day" });
    if (!data.groups) return;
    emptyState.style.display = "none";
    resultsHeader.style.display = "none";
    var html = '<div style="padding:8px 16px 4px;display:flex;justify-content:space-between;align-items:center"><span style="font-size:13px;color:#888">Vue temporelle</span><button onclick="showEventForm()" style="padding:4px 12px;border:1px solid #27ae60;border-radius:5px;background:#fff;color:#27ae60;font-size:12px;cursor:pointer"><i class="fa-solid fa-plus"></i> Ajouter</button></div>';
    var keys = data.keys, labels = data.labels, groups = data.groups;
    var total = 0;
    for (var ki = 0; ki < keys.length; ki++) { total += (groups[keys[ki]] || []).length; }
    if (total === 0) { html += '<div style="padding:20px;text-align:center;color:#aaa">Aucun \u00e9v\u00e9nement \u00e0 venir</div>'; }
    else {
      for (var ki = 0; ki < keys.length; ki++) {
        var evts = groups[keys[ki]] || [];
        if (evts.length === 0) continue;
        html += '<div class="upcoming-section"><div class="upcoming-header">' + esc(labels[ki]) + ' (' + evts.length + ')</div>';
        for (var ei = 0; ei < evts.length; ei++) {
          var ev = evts[ei];
          var recStr = ev.recurrence && ev.recurrence !== "none" ? ' \u00b7 <i class="fa-solid fa-rotate"></i> ' + ({"daily":"chaque jour","weekly":"chaque semaine","monthly":"chaque mois","yearly":"chaque ann\u00e9e"}[ev.recurrence] || "") : "";
          var tagsStr = ev.tags_raw ? '<div class="result-meta" style="margin-top:2px">' + esc(ev.tags_raw) + '</div>' : '';
          html += '<div class="result-item result-event" data-id="' + ev.id + '"><span class="result-icon icon-event"><i class="fa-solid fa-calendar-days"></i></span><div class="result-body"><div class="result-name">' + esc(ev.title) + '</div><div class="result-meta">' + esc(ev.occurrence_date_fr || ev.date_start || "") + recStr + '</div>' + tagsStr + '</div></div>';
        }
        html += '</div>';
      }
    }
    resultsList.innerHTML = html;
    resultsList.querySelectorAll(".result-event").forEach(function(el) { el.addEventListener("click", function() { toggleEventView(el); }); });
  } catch(e) { resultsList.innerHTML = '<div style="padding:20px;color:#aaa;text-align:center">Erreur de chargement</div>'; }
}
var _origRefresh = refresh;
refresh = function() {
  if (state.activeTypes.length === 1 && state.activeTypes[0] === "event" && state.includeTags.length === 0) {
    state.currentOffset = 0; typeFiltersEl.style.display = ""; renderTypeFilters(); renderSelectedTags();
    coocSection.style.display = "none";
    fetchUpcomingEvents("day");
    return;
  }
  _origRefresh();
};
// Contact/Lieu detail toggle
async function toggleContactView(el) {
  var id = el.dataset.id;
  var ex = el.nextElementSibling;
  if (ex && ex.classList.contains("contact-content")) { ex.remove(); return; }
  document.querySelectorAll(".contact-content").forEach(function(e) { e.remove(); });
  try {
    var data = await apiFetch("contact", { id: id });
    if (data.error) return;
    var div = document.createElement("div"); div.className = "contact-content";
    var display = ((data.prenom || "") + " " + (data.nom || "")).trim();
    var ctIcon = data.type === "entreprise" ? '<i class="fa-solid fa-building icon-contact"></i>' : '<i class="fa-solid fa-user icon-contact"></i>';
    var h = '<div class="ct-name">' + ctIcon + ' ' + esc(display) + '</div>';
    if (data.type) h += '<div class="ct-row"><span class="ct-label">Type</span>' + esc(data.type) + '</div>';
    var tels = data.telephones || [];
    if (tels.length) h += '<div class="ct-row"><span class="ct-label">T\u00e9l\u00e9phone</span>' + tels.map(esc).join(", ") + '</div>';
    var emls = data.emails || [];
    if (emls.length) h += '<div class="ct-row"><span class="ct-label">Email</span>' + emls.map(function(e) { return '<a href="mailto:' + esc(e) + '">' + esc(e) + '</a>'; }).join(", ") + '</div>';
    if (data.adresse) h += '<div class="ct-row"><span class="ct-label">Adresse</span>' + esc(data.adresse) + '</div>';
    if (data.date_naissance) {
      var birth = esc(data.date_naissance);
      if (data.heure_naissance) birth += ' \u00e0 ' + esc(data.heure_naissance);
      if (data.lieu_naissance) birth += ' (' + esc(data.lieu_naissance) + ')';
      h += '<div class="ct-row"><span class="ct-label">Naissance</span>' + birth + '</div>';
    }
    if (data.site_web) h += '<div class="ct-row"><span class="ct-label">Site web</span><a href="' + esc(data.site_web) + '" target="_blank">' + esc(data.site_web) + '</a></div>';
    if (data.commentaire) h += '<div class="ct-row"><span class="ct-label">Note</span>' + esc(data.commentaire) + '</div>';
    h += '<div style="margin-top:12px;font-weight:600;font-size:11px;color:#666;text-transform:uppercase;">Tags</div><div class="tags-container"></div>';
    div.innerHTML = h; el.after(div);
    renderItemTags(id, div.querySelector('.tags-container'));
  } catch(e) {}
}
async function toggleLieuView(el) {
  var id = el.dataset.id;
  var ex = el.nextElementSibling;
  if (ex && ex.classList.contains("lieu-content")) { ex.remove(); return; }
  document.querySelectorAll(".lieu-content").forEach(function(e) { e.remove(); });
  try {
    var data = await apiFetch("lieu", { id: id });
    if (data.error) return;
    var div = document.createElement("div"); div.className = "lieu-content";
    var h = '<div class="li-name"><i class="fa-solid fa-location-dot icon-lieu"></i> ' + esc(data.nom) + '</div>';
    if (data.adresse) {
      h += '<div class="li-row"><span class="li-label">Adresse</span>' + esc(data.adresse) + '</div>';
      if (data.maps_url) h += '<a class="maps-btn" href="' + esc(data.maps_url) + '" target="_blank"><i class="fa-solid fa-map-location-dot"></i> Google Maps</a>';
    }
    if (data.description) h += '<div class="li-row" style="margin-top:6px"><span class="li-label">Description</span>' + esc(data.description) + '</div>';
    h += '<div style="margin-top:12px;font-weight:600;font-size:11px;color:#666;text-transform:uppercase;">Tags</div><div class="tags-container"></div>';
    div.innerHTML = h; el.after(div);
    renderItemTags(id, div.querySelector('.tags-container'));
  } catch(e) {}
}

// Bouton + et formulaire d'ajout
var ADD_TYPES = [
  {key:"contact",label:"Contact",icon:'<i class="fa-solid fa-user"></i>'},
  {key:"entreprise",label:"Entreprise",icon:'<i class="fa-solid fa-building"></i>'},
  {key:"lieu",label:"Lieu",icon:'<i class="fa-solid fa-location-dot"></i>'},
  {key:"event",label:"\u00c9v\u00e9nement",icon:'<i class="fa-solid fa-calendar-days"></i>'},
  {key:"anniversaire",label:"Anniversaire",icon:'<i class="fa-solid fa-cake-candles"></i>'},
  {key:"rdv",label:"RDV",icon:'<i class="fa-solid fa-clock"></i>'}
];
function showAddForm() {
  document.querySelector(".add-overlay")?.remove();
  var overlay = document.createElement("div"); overlay.className = "add-overlay";
  var inheritedTags = state.includeTags.filter(function(t) { return t !== "favori"; });
  var currentType = "contact";
  var formTags = inheritedTags.map(function(t) { return {value:t,auto:true}; });
  function buildFields() {
    var t = currentType;
    var isContact = t==="contact", isEntreprise = t==="entreprise", isLieu = t==="lieu";
    var isEvent = t==="event", isAnniv = t==="anniversaire", isRdv = t==="rdv";
    var isEvt = isEvent||isAnniv||isRdv;
    var f = "";
    if (isContact) f += '<div id="af-sys-contacts" style="margin-bottom:8px;display:none"><div style="margin-bottom:4px"><span style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.3px">Remplir depuis mes contacts</span></div><input type="text" id="af-sys-search" placeholder="Chercher un contact existant..." style="width:100%;padding:5px 8px;border:1px solid #ddd;border-radius:4px;font-size:12px;margin-bottom:4px"><div id="af-sys-results" style="max-height:120px;overflow-y:auto;font-size:11px"></div></div>';
    if (isContact) f += '<div class="form-group"><label>Pr\u00e9nom</label><input type="text" id="af-prenom" placeholder="Pr\u00e9nom"></div><div class="form-group"><label>Nom</label><input type="text" id="af-nom" placeholder="Nom"></div>';
    if (isEntreprise||isLieu) f += '<div class="form-group"><label>Nom <span class="required">*</span></label><input type="text" id="af-nom" placeholder="Nom" required></div>';
    if (isEvt) f += '<div class="form-group"><label>Titre <span class="required">*</span></label><input type="text" id="af-titre" placeholder="Titre"></div><div class="form-group"><label>Date <span class="required">*</span></label><input type="date" id="af-date"></div>';
    if (isContact||isEntreprise) f += '<div class="form-group"><label>T\u00e9l\u00e9phone</label><div id="af-tels"><div class="repeatable-row"><input type="tel" placeholder="T\u00e9l\u00e9phone"><button type="button" class="repeatable-add" data-target="af-tels">+</button></div></div></div>';
    if (isContact||isEntreprise) f += '<div class="form-group"><label>Email</label><div id="af-emails"><div class="repeatable-row"><input type="email" placeholder="Email"><button type="button" class="repeatable-add" data-target="af-emails">+</button></div></div></div>';
    if (isContact) f += '<div class="form-group"><label>Date de naissance</label><input type="date" id="af-naissance"></div><div style="display:flex;gap:8px"><div class="form-group" style="flex:1"><label>Heure naissance</label><input type="time" id="af-heure-naissance"></div><div class="form-group" style="flex:1"><label>Lieu naissance</label><input type="text" id="af-lieu-naissance" placeholder="Ville"></div></div>';
    if (isContact||isEntreprise||isLieu) f += '<div class="form-group"><label>Adresse</label><input type="text" id="af-adresse" placeholder="Adresse"></div>';
    if (isEntreprise) f += '<div class="form-group"><label>Site web</label><input type="url" id="af-site" placeholder="https://"></div>';
    if (isLieu||isEvt) f += '<div class="form-group form-autocomplete"><label>Contact' + ((isAnniv||isRdv) ? ' <span class="required">*</span>' : '') + '</label><input type="text" id="af-contact-search" placeholder="Chercher un contact..." autocomplete="off"><input type="hidden" id="af-contact-id"><div class="form-ac-dropdown" id="af-contact-dropdown"></div></div>';
    if (isRdv) f += '<div class="form-group form-autocomplete"><label>Lieu <span class="required">*</span></label><input type="text" id="af-lieu-search" placeholder="Chercher un lieu..." autocomplete="off"><input type="hidden" id="af-lieu-id"><div class="form-ac-dropdown" id="af-lieu-dropdown"></div></div>';
    if (isEvent||isAnniv) f += '<div class="form-group"><label>Lieu</label><input type="text" id="af-location" placeholder="Lieu"></div>';
    if (isLieu||isEvt) f += '<div class="form-group"><label>Description</label><textarea id="af-desc" rows="2" placeholder="Description"></textarea></div>';
    if (isContact||isEntreprise) f += '<div class="form-group"><label>Commentaire</label><textarea id="af-commentaire" rows="2" placeholder="Commentaire"></textarea></div>';
    if (isEvt) { var dr = isAnniv ? "yearly" : "none"; f += '<div class="form-group"><label>R\u00e9currence</label><select id="af-recurrence"><option value="none"' + (dr==="none"?" selected":"") + '>Aucune</option><option value="daily">Chaque jour</option><option value="weekly">Chaque semaine</option><option value="monthly">Chaque mois</option><option value="yearly"' + (dr==="yearly"?" selected":"") + '>Chaque ann\u00e9e</option></select></div>'; }
    var tagsH = formTags.map(function(tg,i) { return '<span class="af-tag' + (tg.auto?" auto":"") + '">' + esc(tg.value) + (tg.auto ? "" : '<span class="remove" data-tag-idx="' + i + '">\u00d7</span>') + '</span>'; }).join("");
    f += '<div class="form-group"><label>Tags</label><div class="add-form-tags" id="af-tags-list">' + tagsH + '</div><div class="form-autocomplete"><input type="text" id="af-tag-input" placeholder="Ajouter un tag..."><div class="form-ac-dropdown" id="af-tag-dropdown"></div></div></div>';
    return f;
  }
  function renderForm() {
    overlay.innerHTML = '<div class="add-form"><div class="add-form-header"><span>Ajouter un \u00e9l\u00e9ment</span><span class="close-btn" id="af-close">\u00d7</span></div><div class="add-type-selector">' + ADD_TYPES.map(function(t) { return '<span class="add-type-btn' + (t.key===currentType?" active":"") + '" data-add-type="' + t.key + '">' + t.icon + ' ' + t.label + '</span>'; }).join("") + '</div><div class="add-form-body">' + buildFields() + '</div><div class="af-status" id="af-status"></div><div class="add-form-footer"><button class="af-btn af-btn-cancel" id="af-cancel">Annuler</button><button class="af-btn af-btn-ok" id="af-submit">Enregistrer</button></div></div>';
    overlay.querySelector("#af-close").addEventListener("click", function() { overlay.remove(); });
    overlay.querySelector("#af-cancel").addEventListener("click", function() { overlay.remove(); });
    overlay.addEventListener("click", function(e) { if (e.target===overlay) overlay.remove(); });
    overlay.querySelectorAll(".add-type-btn").forEach(function(btn) { btn.addEventListener("click", function() { currentType=btn.dataset.addType; renderForm(); }); });
    overlay.querySelectorAll(".af-tag .remove").forEach(function(el) { el.addEventListener("click", function() { formTags.splice(parseInt(el.dataset.tagIdx),1); renderForm(); }); });
    overlay.querySelectorAll(".repeatable-add").forEach(function(btn) { btn.addEventListener("click", function() { var c=overlay.querySelector("#"+btn.dataset.target); var row=document.createElement("div"); row.className="repeatable-row"; var inp=c.querySelector("input").cloneNode(true); inp.value=""; var rb=document.createElement("button"); rb.type="button"; rb.className="repeatable-remove"; rb.textContent="\u00d7"; rb.addEventListener("click",function(){row.remove();}); row.appendChild(inp); row.appendChild(rb); c.appendChild(row); }); });
    // Tag autocomplete
    var tagInput = overlay.querySelector("#af-tag-input");
    var tagDrop = overlay.querySelector("#af-tag-dropdown");
    if (tagInput&&tagDrop) { var dt; tagInput.addEventListener("input",function(){ clearTimeout(dt); var q=tagInput.value.trim(); if(q.length<1){tagDrop.style.display="none";return;} dt=setTimeout(async function(){ try{var d=await apiFetch("autocomplete",{q:q}); var ex=new Set(formTags.map(function(t){return t.value;})); var fi=(d.tags||[]).filter(function(t){return !ex.has(t.tag);}).slice(0,8); var h=fi.map(function(t){return '<div class="ac-item" data-tag="'+esc(t.tag)+'">'+esc(t.tag)+' <span style="color:#888;font-size:10px">('+t.count+')</span></div>';}).join(""); if(!fi.some(function(t){return t.tag===q.toLowerCase();})) h+='<div class="ac-item create" data-tag="'+esc(q.toLowerCase())+'">Cr\u00e9er "'+esc(q)+'"</div>'; tagDrop.innerHTML=h; tagDrop.style.display=h?"block":"none"; tagDrop.querySelectorAll(".ac-item").forEach(function(it){it.addEventListener("click",function(){formTags.push({value:it.dataset.tag,auto:false}); tagInput.value=""; tagDrop.style.display="none"; renderForm();});}); }catch(e){tagDrop.style.display="none";} },150); }); tagInput.addEventListener("keydown",function(e){if(e.key==="Enter"){e.preventDefault();var q=tagInput.value.trim();if(q){formTags.push({value:q.toLowerCase(),auto:false});tagInput.value="";tagDrop.style.display="none";renderForm();}}}); }
    // Contact search
    var cInput=overlay.querySelector("#af-contact-search"),cDrop=overlay.querySelector("#af-contact-dropdown"),cHid=overlay.querySelector("#af-contact-id");
    if(cInput&&cDrop){var dc;cInput.addEventListener("input",function(){clearTimeout(dc);if(cHid)cHid.value="";var q=cInput.value.trim();if(q.length<1){cDrop.style.display="none";return;}dc=setTimeout(async function(){try{var d=await apiFetch("contacts/search",{q:q});var rs=d.results||[];var h=rs.map(function(c){var dn=((c.prenom||"")+" "+(c.nom||"")).trim();var ic=c.type==="entreprise"?'<i class="fa-solid fa-building icon-contact"></i>':'<i class="fa-solid fa-user icon-contact"></i>';return '<div class="ac-item" data-cid="'+c.id+'">'+ic+' '+esc(dn)+'</div>';}).join("");h+='<div class="ac-item create" data-cnew="1"><i class="fa-solid fa-plus"></i> Cr\u00e9er un nouveau contact...</div>';cDrop.innerHTML=h;cDrop.style.display="block";cDrop.querySelectorAll("[data-cid]").forEach(function(it){it.addEventListener("click",function(){var c=rs.find(function(x){return x.id===parseInt(it.dataset.cid);});if(c){cInput.value=((c.prenom||"")+" "+(c.nom||"")).trim();cHid.value=c.id;cDrop.style.display="none";}});});cDrop.querySelector("[data-cnew]")?.addEventListener("click",function(){cDrop.style.display="none";currentType="contact";renderForm();});}catch(e){cDrop.style.display="none";}},200);});}
    // Lieu search
    var lInput=overlay.querySelector("#af-lieu-search"),lDrop=overlay.querySelector("#af-lieu-dropdown"),lHid=overlay.querySelector("#af-lieu-id");
    if(lInput&&lDrop){var dl;lInput.addEventListener("input",function(){clearTimeout(dl);if(lHid)lHid.value="";var q=lInput.value.trim();if(q.length<1){lDrop.style.display="none";return;}dl=setTimeout(async function(){try{var d=await apiFetch("lieux/search",{q:q});var rs=d.results||[];var h=rs.map(function(l){return '<div class="ac-item" data-lid="'+l.id+'"><i class="fa-solid fa-location-dot icon-lieu"></i> '+esc(l.nom)+(l.adresse?' \u2014 '+esc(l.adresse):'')+'</div>';}).join("");h+='<div class="ac-item create" data-lnew="1"><i class="fa-solid fa-plus"></i> Cr\u00e9er un nouveau lieu...</div>';lDrop.innerHTML=h;lDrop.style.display="block";lDrop.querySelectorAll("[data-lid]").forEach(function(it){it.addEventListener("click",function(){var l=rs.find(function(x){return x.id===parseInt(it.dataset.lid);});if(l){lInput.value=l.nom;lHid.value=l.id;lDrop.style.display="none";}});});lDrop.querySelector("[data-lnew]")?.addEventListener("click",function(){lDrop.style.display="none";currentType="lieu";renderForm();});}catch(e){lDrop.style.display="none";}},200);});}
    // Contacts système
    var sysCt=overlay.querySelector("#af-sys-contacts"), sysData=[];
    async function loadSysContacts(q){try{var p=q?{q:q}:{};var d=await apiFetch("system-contacts/list",p);if(!d.available){sysCt.style.display="none";return;}sysCt.style.display="block";renderSysContacts(d.contacts||[],d.total||0);}catch(e){sysCt.style.display="none";}}
    if(sysCt){loadSysContacts("");var sysSearch=sysCt.querySelector("#af-sys-search");if(sysSearch){var dst;sysSearch.addEventListener("input",function(){clearTimeout(dst);dst=setTimeout(function(){loadSysContacts(sysSearch.value.trim());},200);});}}
    function renderSysContacts(contacts,total){sysData=contacts;var el=overlay.querySelector("#af-sys-results");if(!el)return;if(!contacts.length){el.innerHTML='<div style="color:#aaa;padding:4px">Aucun contact trouv\u00e9</div>';return;}el.innerHTML=contacts.slice(0,20).map(function(c,idx){var dn=((c.prenom||"")+" "+(c.nom||"")).trim();var info=[].concat((c.telephones||[]).slice(0,1),(c.emails||[]).slice(0,1)).join(" \\u00b7 ");return '<div style="padding:4px 6px;cursor:pointer;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center" data-sys-idx="'+idx+'"><i class="fa-solid fa-user icon-contact"></i> '+esc(dn)+'<span style="color:#aaa;font-size:10px">'+esc(info)+'</span></div>';}).join("")+(total>20?'<div style="color:#888;padding:4px;text-align:center;font-size:10px">'+total+' contacts au total</div>':"");el.querySelectorAll("[data-sys-idx]").forEach(function(it){it.addEventListener("click",function(){var c=sysData[parseInt(it.dataset.sysIdx)];if(!c)return;var pe=overlay.querySelector("#af-prenom"),ne=overlay.querySelector("#af-nom");if(pe)pe.value=c.prenom||"";if(ne)ne.value=c.nom||"";var tc=overlay.querySelector("#af-tels");if(tc&&c.telephones&&c.telephones.length){var fi=tc.querySelector("input");if(fi)fi.value=c.telephones[0];for(var i=1;i<c.telephones.length;i++){var row=document.createElement("div");row.className="repeatable-row";var inp=document.createElement("input");inp.type="tel";inp.placeholder="T\\u00e9l\\u00e9phone";inp.value=c.telephones[i];var rb=document.createElement("button");rb.type="button";rb.className="repeatable-remove";rb.textContent="\\u00d7";rb.addEventListener("click",(function(r){return function(){r.remove();};})(row));row.appendChild(inp);row.appendChild(rb);tc.appendChild(row);}}var ec=overlay.querySelector("#af-emails");if(ec&&c.emails&&c.emails.length){var fi=ec.querySelector("input");if(fi)fi.value=c.emails[0];for(var i=1;i<c.emails.length;i++){var row=document.createElement("div");row.className="repeatable-row";var inp=document.createElement("input");inp.type="email";inp.placeholder="Email";inp.value=c.emails[i];var rb=document.createElement("button");rb.type="button";rb.className="repeatable-remove";rb.textContent="\\u00d7";rb.addEventListener("click",(function(r){return function(){r.remove();};})(row));row.appendChild(inp);row.appendChild(rb);ec.appendChild(row);}}sysCt.style.display="none";});it.addEventListener("mouseenter",function(){it.style.background="#fef5ed";});it.addEventListener("mouseleave",function(){it.style.background="";});});}
    // Date inputs : calendrier on focus
    overlay.querySelectorAll('input[type="date"]').forEach(function(di) { di.addEventListener("focus", function() { try { di.showPicker(); } catch(e) {} }); });
    // Submit
    overlay.querySelector("#af-submit").addEventListener("click", async function() {
      var st=overlay.querySelector("#af-status"),sb=overlay.querySelector("#af-submit");
      st.className="af-status";st.style.display="none";sb.disabled=true;
      var tagsStr=formTags.map(function(t){return t.value;}).join(",");
      try {
        var result, t=currentType;
        if(t==="contact"||t==="entreprise"){var nom=(overlay.querySelector("#af-nom")||{}).value||"";var prenom=(overlay.querySelector("#af-prenom")||{}).value||"";if(t==="contact"&&!nom.trim()&&!prenom.trim())throw new Error("Nom ou pr\u00e9nom requis");if(t==="entreprise"&&!nom.trim())throw new Error("Nom requis");var tels=[];overlay.querySelectorAll("#af-tels input").forEach(function(i){if(i.value.trim())tels.push(i.value.trim());});var emails=[];overlay.querySelectorAll("#af-emails input").forEach(function(i){if(i.value.trim())emails.push(i.value.trim());});result=await fetch(API+"/contact",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({type:t==="entreprise"?"entreprise":"personne",nom:nom.trim(),prenom:(prenom||"").trim(),telephones:tels,emails:emails,date_naissance:(overlay.querySelector("#af-naissance")||{}).value||null,heure_naissance:(overlay.querySelector("#af-heure-naissance")||{}).value||null,lieu_naissance:(overlay.querySelector("#af-lieu-naissance")||{}).value||null,adresse:(overlay.querySelector("#af-adresse")||{}).value||"",site_web:(overlay.querySelector("#af-site")||{}).value||"",commentaire:(overlay.querySelector("#af-commentaire")||{}).value||"",tags_raw:tagsStr})}).then(function(r){return r.json();});}
        else if(t==="lieu"){var nom=(overlay.querySelector("#af-nom")||{}).value||"";if(!nom.trim())throw new Error("Nom requis");result=await fetch(API+"/lieu",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({nom:nom.trim(),adresse:(overlay.querySelector("#af-adresse")||{}).value||"",description:(overlay.querySelector("#af-desc")||{}).value||"",contact_id:(overlay.querySelector("#af-contact-id")||{}).value?parseInt(overlay.querySelector("#af-contact-id").value):null,tags_raw:tagsStr})}).then(function(r){return r.json();});}
        else if(t==="event"||t==="anniversaire"||t==="rdv"){var titre=(overlay.querySelector("#af-titre")||{}).value||"";var date=(overlay.querySelector("#af-date")||{}).value||"";if(!titre.trim()||!date)throw new Error("Titre et date requis");var cId=(overlay.querySelector("#af-contact-id")||{}).value?parseInt(overlay.querySelector("#af-contact-id").value):null;var lId=(overlay.querySelector("#af-lieu-id")||{}).value?parseInt(overlay.querySelector("#af-lieu-id").value):null;if(t==="anniversaire"&&!cId)throw new Error("Contact obligatoire pour un anniversaire");if(t==="rdv"&&(!cId||!lId))throw new Error("Contact et lieu obligatoires pour un RDV");var sub=t==="anniversaire"?"anniversaire":t==="rdv"?"rendez_vous":"generic";result=await fetch(API+"/event",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title:titre.trim(),date_start:date,description:(overlay.querySelector("#af-desc")||{}).value||"",location:(overlay.querySelector("#af-location")||{}).value||"",tags_raw:tagsStr,recurrence:(overlay.querySelector("#af-recurrence")||{}).value||"none",subtype:sub,contact_id:cId,lieu_id:lId})}).then(function(r){return r.json();});}
        if(result&&result.error)throw new Error(result.error);
        st.className="af-status success";st.innerHTML='<i class="fa-solid fa-check"></i> Enregistr\u00e9 !';st.style.display="block";
        setTimeout(function(){overlay.remove();refresh();},1500);
      } catch(e) { st.className="af-status error";st.textContent=e.message||"Erreur";st.style.display="block";sb.disabled=false; }
    });
  }
  renderForm();
  document.body.appendChild(overlay);
}
document.getElementById("add-btn").addEventListener("click", showAddForm);

// ── Home page ──────────────────────────────────────────────────────
const HOME_TYPE_CARDS = [
  {type:"projet", label:"Projets", icon:'<i class="fa-solid fa-folder-tree" style="color:#2e7d32"></i>'},
  {type:"file", label:"Fichiers", icon:'<i class="fa-solid fa-folder" style="color:#3498db"></i>'},
  {type:"email", label:"Emails", icon:'<i class="fa-solid fa-envelope" style="color:#4a90d9"></i>'},
  {type:"note", label:"Notes", icon:'<i class="fa-solid fa-note-sticky" style="color:#f0ad4e"></i>'},
  {type:"event", label:"\u00c9v\u00e9nements", icon:'<i class="fa-solid fa-calendar-days" style="color:#27ae60"></i>'},
  {type:"contact", label:"Contacts", icon:'<i class="fa-solid fa-user" style="color:#e67e22"></i>'},
  {type:"lieu", label:"Lieux", icon:'<i class="fa-solid fa-location-dot" style="color:#1abc9c"></i>'},
  {type:"video", label:"Vid\u00e9os", icon:'<i class="fa-solid fa-video" style="color:#c00"></i>'},
  {type:"vault", label:"Vault", icon:'<i class="fa-solid fa-lock" style="color:#9b59b6"></i>'},
  {type:"favori", label:"Favoris", icon:'<i class="fa-solid fa-heart" style="color:#e74c3c"></i>'}
];
function activateType(type) {
  if (type === 'favori') { state.includeTags = ['favori']; state.activeTypes = []; }
  else { state.activeTypes = [type]; state.includeTags = []; }
  state.currentOffset = 0;
  renderTypeFilters(); renderSelectedTags(); fetchResults(); fetchCooccurrence();
}
async function loadHomePage() {
  // Type cards
  const cardsEl = document.getElementById('home-type-cards');
  if (cardsEl) cardsEl.innerHTML = HOME_TYPE_CARDS.map(c =>
    '<div class="home-card" onclick="activateType(\'' + c.type + '\')">' + c.icon + '<span>' + c.label + '</span></div>'
  ).join('');
  // Today tasks widget
  try {
    const data = await apiFetch('tasks', { scheduled: 'today', status: 'todo' });
    const tasks = data.tasks || [];
    const widget = document.getElementById('home-today-widget');
    if (widget && tasks.length > 0) {
      let h = '<div class="home-today-header"><i class="fa-solid fa-calendar-day" style="color:#6366f1"></i> Aujourd\'hui <span style="margin-left:auto;font-size:11px;color:#9ca3af">' + tasks.length + ' t\u00e2che' + (tasks.length > 1 ? 's' : '') + '</span></div>';
      tasks.slice(0, 6).forEach(t => {
        h += '<div class="home-today-row" onclick="showProjectDetail(' + (t.project_id || t.id) + ')"><i class="fa-regular fa-circle" style="color:#9ca3af;font-size:11px;flex-shrink:0"></i><span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + escHtml(t.title) + '</span></div>';
      });
      if (tasks.length > 6) h += '<div style="font-size:11px;color:#9ca3af;padding:4px 0">+' + (tasks.length - 6) + ' autres</div>';
      widget.innerHTML = h; widget.style.display = '';
    }
  } catch(e) {}
}

// Init
(function initUI() {
  document.getElementById('tasks-panel').style.display = 'none';
  document.getElementById('detail-panel').style.display = 'none';
  document.getElementById('type-filters').style.display = 'none';
})();
checkServer(); checkVaultStatus();
setTimeout(() => { try { input.focus(); } catch(e){} }, 50);

// Listener tag chips dans la modale tâche
document.getElementById('t-task-tags').addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); _addTagFromInput(); }
});

// Afficher home ou résultats selon état initial
renderTypeFilters();
if (state.includeTags.length > 0 || state.excludeTags.length > 0 || state.activeTypes.length > 0) {
  _showResults();
  renderSelectedTags(); fetchResults(); fetchCooccurrence();
} else {
  _showHome();
  loadHomePage();
}

// ═══════════════════════════════════════════════════════════════════
// ── ONGLETS : Aujourd'hui / Projets ────────────────────────────────
// ═══════════════════════════════════════════════════════════════════

let currentTab = 'search';
let todayData = null;
let projectsData = [];
let currentDetailId = null;
let tomorrowSelected = new Set();
let _currentDetailProjectId = null;
let _detailPrevTab = 'search';

function switchTab(tab) {
  currentTab = tab;
  const isSearch = tab === 'search';
  document.querySelector('.container').style.display = isSearch ? '' : 'none';
  document.getElementById('home-section').style.display = isSearch ? '' : 'none';
  document.getElementById('tasks-panel').style.display = isSearch ? 'none' : 'flex';
  document.getElementById('tasks-panel').style.flexDirection = 'column';
  document.getElementById('tasks-main-container').style.display = tab === 'today' ? '' : 'none';
  document.getElementById('projects-main-container').style.display = tab === 'projects' ? '' : 'none';
  if (isSearch && state.includeTags.length === 0 && state.activeTypes.length === 0) {
    document.querySelector('.container').style.display = 'none';
    loadHomePage();
  }
  if (tab === 'today') loadTodayView();
  if (tab === 'projects') loadProjectsView();
}

// ── Détail projet (pleine page) ──────────────────────────────────────
var _detailProjectData = null;
var _chOpenState = {};
var _detailSortBy = 'deadline';
var _detailActiveTags = [];

function _sortByDeadline(arr) {
  return arr.slice().sort((a,b) => {
    const da = a.deadline_date || '9999'; const db = b.deadline_date || '9999';
    return da < db ? -1 : da > db ? 1 : 0;
  });
}

function _taskRow(t, pid) {
  const isDone = t.status === 'done';
  let h = '<div class="dp-task-row">';
  h += '<button class="dp-check' + (isDone?' done':'') + '" onclick="toggleTask(' + t.id + ',\'' + (isDone?'todo':'done') + '\')">' + (isDone?'<i class="fa-solid fa-check" style="color:#16a34a;font-size:10px"></i>':'') + '</button>';
  h += '<span contenteditable="true" data-id="' + t.id + '" data-kind="task" class="dp-editable dp-task-title' + (isDone?' done':'') + '" style="outline:none;border-bottom:1px dashed transparent" onfocus="this.style.borderColor=\'#4f46e5\'" onblur="this.style.borderColor=\'transparent\';_autoSaveTitle(this)" onkeydown="if(event.key===\'Enter\'){event.preventDefault();this.blur()}">' + escHtml(t.title) + '</span>';
  if (t.deadline_date) h += '<span style="font-size:10px;color:#c2410c;flex-shrink:0"><i class="fa-regular fa-calendar"></i> ' + escHtml(t.deadline_date) + '</span>';
  h += '<button class="t-btn" onclick="openEditTask(' + t.id + ')"><i class="fa-solid fa-pen"></i></button>';
  h += '<button class="t-btn" style="color:#ef4444" onclick="deleteTask(' + t.id + ',' + JSON.stringify(t.title) + ')"><i class="fa-solid fa-trash"></i></button>';
  h += '</div>';
  return h;
}

async function deleteTask(id, title) {
  if (!confirm('Supprimer \u00ab ' + title + ' \u00bb\u00a0?')) return;
  await tApi('/api/tasks', 'DELETE', {id});
  const res = await tApi('/api/tasks/steps?project_id=' + _currentDetailProjectId);
  if (res.project) { _detailProjectData = res.project; _renderDetailContent([..._detailActiveTags]); }
}

function _dpSort(arr) {
  return arr.slice().sort((a, b) => {
    if (_detailSortBy === 'name') {
      return (a.title||'').toLowerCase() < (b.title||'').toLowerCase() ? -1 : 1;
    }
    if (_detailSortBy === 'status') {
      const sa = a.status === 'done' ? 1 : 0, sb = b.status === 'done' ? 1 : 0;
      return sa - sb;
    }
    // deadline (default)
    const da = a.deadline_date || '9999', db = b.deadline_date || '9999';
    return da < db ? -1 : da > db ? 1 : 0;
  });
}
function dpSetSort(by) {
  _detailSortBy = by;
  document.querySelectorAll('.dp-sort-opt').forEach(b => b.classList.toggle('active', b.dataset.sort === by));
  _renderDetailContent(_detailActiveTags);
}
function dpToggleTag(tag) {
  const idx = _detailActiveTags.indexOf(tag);
  if (idx >= 0) _detailActiveTags.splice(idx, 1); else _detailActiveTags.push(tag);
  document.querySelectorAll('.dp-tag-chip').forEach(c => c.classList.toggle('active', _detailActiveTags.includes(c.dataset.tag)));
  _renderDetailContent(_detailActiveTags);
}
function _renderDetailContent(filterTags) {
  const container = document.getElementById('dp-tasks-container');
  if (!container || !_detailProjectData) return;
  const p = _detailProjectData;
  const pid = p.id;
  const ft = (filterTags || []).map(t => t.toLowerCase());

  // Collect all unique tags across all tasks
  const allTags = new Set();
  (p.chantiers || []).forEach(ch => {
    (ch.tags || []).forEach(t => t && allTags.add(t));
    (ch.subtasks || []).forEach(t => (t.tags || []).forEach(tg => tg && allTags.add(tg)));
  });
  (p.subtasks || []).forEach(t => (t.tags || []).forEach(tg => tg && allTags.add(tg)));

  let html = '';

  // Tag bar
  if (allTags.size > 0) {
    html += '<div class="dp-tag-bar">';
    [...allTags].sort().forEach(tag => {
      const active = _detailActiveTags.includes(tag);
      html += '<span class="dp-tag-chip' + (active?' active':'') + '" data-tag="' + escHtml(tag) + '" onclick="dpToggleTag(\'' + escHtml(tag) + '\')">' + escHtml(tag) + '</span>';
    });
    html += '</div>';
  }

  // Sort bar + resources header
  html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:6px">';
  html += '<div class="dp-sort-bar"><span style="font-size:11px;color:#9ca3af;margin-right:2px">Tri&nbsp;:</span>';
  [['deadline','Deadline'],['name','Nom'],['status','Statut']].forEach(([val,lbl]) => {
    html += '<button class="dp-sort-opt' + (_detailSortBy===val?' active':'') + '" data-sort="' + val + '" onclick="dpSetSort(\'' + val + '\')">' + lbl + '</button>';
  });
  html += '</div></div>';

  // Attachments (links/docs)
  const attachments = (p.attachments || []).filter(a => a.type === 'url' || a.type === 'file');
  const notes = (p.attachments || []).filter(a => a.type === 'note');
  if (attachments.length || notes.length) {
    html += '<div class="dp-resources">';
    html += '<div style="font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px">Ressources</div>';
    attachments.forEach(a => {
      const icon = a.type === 'url' ? '\ud83d\udd17' : '\ud83d\udcc4';
      html += '<div class="dp-resource-row">' + icon + ' ';
      if (a.url) html += '<a href="' + escHtml(a.url) + '" target="_blank">' + escHtml(a.name) + '</a>';
      else html += '<span>' + escHtml(a.name) + (a.file_path ? ' <span style="color:#9ca3af;font-size:11px">— ' + escHtml(a.file_path) + '</span>' : '') + '</span>';
      html += '<button class="t-btn" style="color:#ef4444" onclick="dpDeleteAttachment(' + a.id + ')"><i class="fa-solid fa-xmark"></i></button></div>';
    });
    html += '</div>';
  }

  // Notes
  (p.subtasks || []).filter(t => (t.tags||[]).includes('note')).forEach(n => {
    html += '<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:10px 12px;margin-bottom:8px;font-size:13px;color:#374151">';
    html += '<div style="display:flex;align-items:flex-start;gap:8px"><i class="fa-solid fa-note-sticky" style="color:#f59e0b;margin-top:2px"></i><div style="flex:1">' + escHtml(n.title) + '</div>';
    html += '<button class="t-btn" onclick="openEditTask(' + n.id + ')"><i class="fa-solid fa-pen"></i></button></div></div>';
  });

  let hasContent = false;

  _dpSort(p.chantiers || []).forEach(ch => {
    let tasks = _sortByDeadline(ch.subtasks || []);
    if (ft.length) {
      tasks = tasks.filter(t => {
        const tStr = (t.title + ' ' + (t.tags || []).join(' ')).toLowerCase();
        return ft.every(f => tStr.includes(f));
      });
      if (!tasks.length) return;
    }
    hasContent = true;
    if (_chOpenState[ch.id] === undefined) _chOpenState[ch.id] = true;
    const isOpen = _chOpenState[ch.id];
    const chStatusColor = STATUS_COLORS[ch.status] || '#9ca3af';
    html += '<div class="dp-block">';
    html += '<div class="dp-block-header" onclick="dpToggleCh(' + ch.id + ')">';
    html += '<i class="fa-solid fa-chevron-down dp-ch-arrow ' + (isOpen?'open':'closed') + '" id="ch-arrow-' + ch.id + '"></i>';
    html += '<span contenteditable="true" data-id="' + ch.id + '" data-kind="task" class="dp-editable" style="font-weight:600;font-size:14px;flex:1;outline:none;border-bottom:1px dashed transparent" onclick="event.stopPropagation()" onfocus="event.stopPropagation();this.style.borderColor=\'#4f46e5\'" onblur="this.style.borderColor=\'transparent\';_autoSaveTitle(this)" onkeydown="if(event.key===\'Enter\'){event.preventDefault();this.blur()}">' + escHtml(ch.title) + '</span>';
    if (ch.deadline_date) html += '<span style="font-size:10px;color:#c2410c;flex-shrink:0"><i class="fa-regular fa-calendar"></i> ' + escHtml(ch.deadline_date) + '</span>';
    if (ch.status && ch.status !== 'todo') html += '<span style="font-size:10px;padding:1px 6px;border-radius:4px;background:' + chStatusColor + '22;color:' + chStatusColor + ';font-weight:600;flex-shrink:0">' + escHtml(ch.status) + '</span>';
    html += '<button class="t-btn" onclick="event.stopPropagation();openAddTask(\'task\',' + pid + ',' + ch.id + ')"><i class="fa-solid fa-plus"></i></button>';
    html += '<button class="t-btn" onclick="event.stopPropagation();openEditTask(' + ch.id + ')"><i class="fa-solid fa-pen"></i></button>';
    html += '</div>';
    html += '<div class="dp-ch-body' + (isOpen?'':' collapsed') + '" id="ch-body-' + ch.id + '" style="max-height:' + (isOpen?'2000px':'0') + '">';
    if (tasks.length) tasks.forEach(t => { html += _taskRow(t, pid); });
    else html += '<div style="padding:8px 14px;font-size:12px;color:#9ca3af">Aucune t\u00e2che</div>';
    html += '</div></div>';
  });

  const directTasks = ft.length
    ? _sortByDeadline(p.subtasks || []).filter(t => {
        const tStr = (t.title + ' ' + (t.tags || []).join(' ')).toLowerCase();
        return ft.every(f => tStr.includes(f));
      })
    : _sortByDeadline(p.subtasks || []);
  if (directTasks.length) {
    hasContent = true;
    directTasks.forEach(t => { html += _taskRow(t, pid); });
  }

  if (!hasContent) html = '<div class="dp-empty">' + (ft.length ? 'Aucun r\u00e9sultat pour ce filtre.' : 'Aucun chantier ni t\u00e2che pour ce projet.') + '</div>';
  container.innerHTML = html;
}

function dpToggleCh(chId) {
  _chOpenState[chId] = !_chOpenState[chId];
  const body = document.getElementById('ch-body-' + chId);
  const arrow = document.getElementById('ch-arrow-' + chId);
  if (body) { body.classList.toggle('collapsed', !_chOpenState[chId]); body.style.maxHeight = _chOpenState[chId] ? '2000px' : '0'; }
  if (arrow) { arrow.classList.toggle('closed', !_chOpenState[chId]); arrow.classList.toggle('open', !!_chOpenState[chId]); }
}

function _filterDetailPanel() {
  const combined = [...new Set([..._detailActiveTags, ...state.includeTags.map(t => t.toLowerCase())])];
  _renderDetailContent(combined);
}

async function showProjectDetail(id) {
  const res = await tApi('/api/tasks/steps?project_id=' + id);
  const p = res.project || null;
  if (!p) return;
  _currentDetailProjectId = id;
  _detailProjectData = p;
  _detailPrevTab = currentTab;
  document.querySelector('.container').style.display = 'none';
  document.getElementById('tasks-panel').style.display = 'none';
  const panel = document.getElementById('detail-panel');
  panel.style.display = '';
  const statusColor = STATUS_COLORS[p.status] || '#9ca3af';
  let html = '<div class="dp-header">';
  html += '<button class="dp-back" onclick="closeDetailPanel()"><i class="fa-solid fa-arrow-left"></i> Retour</button>';
  html += '<h1 class="dp-title">' + escHtml(p.title) + '</h1>';
  html += '<button class="t-btn" onclick="openEditTask(' + id + ')"><i class="fa-solid fa-pen"></i> Modifier</button>';
  html += '</div>';
  html += '<div class="dp-meta">';
  html += '<span class="dp-badge" style="background:' + statusColor + '22;color:' + statusColor + '">' + escHtml(p.status || 'todo') + '</span>';
  if (p.category) html += '<span class="dp-badge" style="background:#e0e7ff;color:#4f46e5">' + escHtml(p.category) + '</span>';
  html += '</div>';
  function metaField(label, field, val, placeholder) {
    return '<div class="dp-section"><div class="dp-section-label">' + label + '</div>'
      + '<div class="dp-section-value dp-editable" contenteditable="true" data-id="' + id + '" data-field="' + field + '" data-kind="projet_meta"'
      + ' style="outline:none;min-height:1.2em;border-bottom:1px dashed transparent"'
      + ' onfocus="this.style.borderColor=\'#4f46e5\'"'
      + ' onblur="this.style.borderColor=\'transparent\';_autoSaveProjectMeta(this)"'
      + ' onkeydown="if(event.key===\'Enter\'){event.preventDefault();this.blur()}"'
      + ' data-placeholder="' + placeholder + '">'
      + escHtml(val || '') + '</div></div>';
  }
  html += metaField('Description', 'description', p.description, 'Ajouter une description\u2026');
  html += metaField('Objectif', 'goal', p.goal, 'Ajouter un objectif\u2026');
  html += metaField('Mission', 'mission', p.mission, 'Ajouter une mission\u2026');
  html += metaField('Deadline', 'deadline_date', p.deadline_date, 'YYYY-MM-DD');
  const tags = (p.tags || []).filter(tg => !['pro','perso'].includes(tg));
  if (tags.length) html += '<div class="dp-section">' + tags.map(tg => '<span class="t-tag" style="font-size:12px">' + escHtml(tg) + '</span>').join(' ') + '</div>';
  // Quick-add bar
  html += '<div class="dp-quickadd-bar" id="dp-qa-bar">';
  html += '<button class="dp-qa-btn" id="dp-qa-btn-task" onclick="dpQuickAdd(\'task\')"><i class="fa-solid fa-plus"></i> T\u00e2che</button>';
  html += '<button class="dp-qa-btn" id="dp-qa-btn-note" onclick="dpQuickAdd(\'note\')"><i class="fa-solid fa-note-sticky"></i> Note</button>';
  html += '<button class="dp-qa-btn" id="dp-qa-btn-lien" onclick="dpQuickAdd(\'lien\')"><i class="fa-solid fa-link"></i> Lien</button>';
  html += '<button class="dp-qa-btn" id="dp-qa-btn-doc" onclick="dpQuickAdd(\'doc\')"><i class="fa-solid fa-file"></i> Doc</button>';
  html += '</div>';
  html += '<div id="dp-quickadd-form" style="display:none"></div>';
  html += '<div class="dp-add-bar" style="margin-bottom:10px"><h3 style="margin:0">Chantiers &amp; T\u00e2ches</h3></div>';
  html += '<div id="dp-tasks-container"></div>';
  panel.innerHTML = html;
  _detailActiveTags = [];
  _detailSortBy = 'deadline';
  _renderDetailContent([]);
}

async function toggleTask(taskId, newStatus) {
  if (newStatus === 'done') await tApi('/api/tasks/done', 'POST', { id: taskId });
  else await tApi('/api/tasks/undone', 'POST', { id: taskId });
  if (_currentDetailProjectId) {
    const res = await tApi('/api/tasks/steps?project_id=' + _currentDetailProjectId);
    if (res.project) { _detailProjectData = res.project; _renderDetailContent(state.includeTags.map(t => t.toLowerCase())); }
  }
}

function closeDetailPanel() {
  document.getElementById('detail-panel').style.display = 'none';
  _currentDetailProjectId = null;
  _detailProjectData = null;
  if (_detailPrevTab === 'search') {
    document.querySelector('.container').style.display = '';
  } else {
    switchTab(_detailPrevTab);
  }
}

async function _autoSaveTitle(el) {
  const id = parseInt(el.dataset.id);
  const newTitle = el.textContent.trim();
  if (!id || !newTitle) return;
  await tApi('/api/tasks', 'PUT', { id, title: newTitle });
  if (_currentDetailProjectId) {
    await tApi('/api/tasks/steps_rewrite', 'POST', { project_id: _currentDetailProjectId });
  }
}
async function _autoSaveProjectMeta(el) {
  const id = parseInt(el.dataset.id);
  const field = el.dataset.field;
  const val = el.textContent.trim();
  if (!id || !field) return;
  await tApi('/api/tasks', 'PUT', { id, [field]: val });
  await tApi('/api/tasks/steps_rewrite', 'POST', { project_id: id });
}

// ── Global Add Modal ─────────────────────────────────────────────────
let _gaType = null;
let _gaProjects = null;

let _gaAllTags = null;
let _gaChips = [];

async function openGlobalAdd() {
  _gaType = null;
  _gaChips = [];
  const [pr, tr] = await Promise.all([
    _gaProjects ? Promise.resolve({tasks:_gaProjects}) : tApi('/api/tasks?kind=projet&parent_id=null'),
    _gaAllTags  ? Promise.resolve({tags:_gaAllTags})   : tApi('/api/tasks/tags'),
  ]);
  _gaProjects = (pr.tasks || []).sort((a,b) => a.title.localeCompare(b.title));
  _gaAllTags  = tr.tags || [];
  _gaRender();
  document.getElementById('ga-modal').style.display = 'flex';
}

function closeGlobalAdd() {
  document.getElementById('ga-modal').style.display = 'none';
  _gaType = null;
}

function _gaPickType(t) {
  _gaType = t;
  _gaChips = [];
  _gaRender();
  setTimeout(() => {
    const f = document.querySelector('#ga-modal .ga-input:not(select):not([type=file])');
    if (f) f.focus();
  }, 40);
}

function _gaAddChip(val) {
  const v = val.trim().toLowerCase().replace(/,/g,'');
  if (v && !_gaChips.includes(v)) { _gaChips.push(v); }
  const inp = document.getElementById('ga-tag-inp');
  if (inp) inp.value = '';
  _gaRenderChips();
}
function _gaRemoveChip(t) {
  _gaChips = _gaChips.filter(c => c !== t);
  _gaRenderChips();
}
function _gaRenderChips() {
  const bar = document.getElementById('ga-chips');
  if (!bar) return;
  bar.innerHTML = _gaChips.map(c =>
    '<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;background:#6366f1;color:#fff;border-radius:5px;font-size:12px">'
    + escHtml(c)
    + '<button onclick="_gaRemoveChip(\'' + escHtml(c) + '\')" style="background:none;border:none;color:#fff;cursor:pointer;padding:0;font-size:12px;line-height:1">&times;</button></span>'
  ).join('');
}
function _gaTagKeydown(e) {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault();
    _gaAddChip(e.target.value);
  }
}

function _gaRender() {
  const body = document.getElementById('ga-modal-body');
  const saveBtn = document.getElementById('ga-save-btn');
  const defs = [
    {id:'todo', label:'Todo', icon:'fa-circle-check', bg:'#4f46e5', badge:'rgba(255,255,255,.18)'},
    {id:'note', label:'Note', icon:'fa-note-sticky',  bg:'#f59e0b', badge:'rgba(255,255,255,.18)'},
    {id:'url',  label:'URL',  icon:'fa-link',         bg:'#0ea5e9', badge:'rgba(255,255,255,.18)'},
    {id:'doc',  label:'Doc',  icon:'fa-file',         bg:'#10b981', badge:'rgba(255,255,255,.18)'},
  ];
  let html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">';
  defs.forEach(({id, label, icon, bg, badge}) => {
    const active = _gaType === id;
    const cardBg = active ? bg : '#2d2d3a';
    const opacity = active ? '1' : '0.72';
    html += '<button onclick="_gaPickType(\'' + id + '\')" style="padding:24px 16px 20px;border-radius:16px;border:none;background:' + cardBg + ';cursor:pointer;font-family:inherit;display:flex;flex-direction:column;align-items:center;gap:12px;opacity:' + opacity + ';transition:all .18s;box-shadow:' + (active?'0 4px 18px '+bg+'55':'none') + '">';
    html += '<div style="width:54px;height:54px;border-radius:14px;background:' + badge + ';display:flex;align-items:center;justify-content:center">';
    html += '<i class="fa-solid ' + icon + '" style="font-size:24px;color:#fff"></i></div>';
    html += '<span style="font-size:14px;font-weight:600;color:#fff">' + label + '</span>';
    html += '</button>';
  });
  html += '</div>';

  if (_gaType) {
    // Project selector
    const projects = _gaProjects || [];
    const preId = _currentDetailProjectId || '';
    html += '<div class="ga-field"><label>Projet <span style="color:#ef4444">*</span></label>';
    html += '<select id="ga-project" class="ga-input">';
    html += '<option value="">— Choisir un projet —</option>';
    projects.forEach(p => {
      html += '<option value="' + p.id + '"' + (p.id == preId ? ' selected' : '') + '>' + escHtml(p.title) + (p.category ? ' (' + escHtml(p.category) + ')' : '') + '</option>';
    });
    html += '</select></div>';

    // Champs communs + spécifiques
    const tagDatalist = '<datalist id="ga-tag-list">' + (_gaAllTags||[]).map(t => '<option value="' + escHtml(t) + '">').join('') + '</datalist>';
    const tagsBlock = tagDatalist
      + '<div class="ga-field"><label>Tags</label>'
      + '<div id="ga-chips" style="display:flex;flex-wrap:wrap;gap:4px;min-height:0;margin-bottom:4px"></div>'
      + '<input id="ga-tag-inp" class="ga-input" type="text" list="ga-tag-list" placeholder="Ajouter un tag…" onkeydown="_gaTagKeydown(event)" onchange="_gaAddChip(this.value)" style="margin-top:0" />'
      + '</div>';

    if (_gaType === 'todo') {
      html += '<div class="ga-field"><label>Titre <span style="color:#ef4444">*</span></label><input id="ga-title" class="ga-input" type="text" placeholder="Titre de la tâche…" /></div>';
      html += '<div class="ga-field"><label>Description</label><textarea id="ga-desc" class="ga-input" rows="2" placeholder="Description…" style="resize:vertical"></textarea></div>';
      html += '<div class="ga-field"><label>Deadline</label><input id="ga-deadline" class="ga-input" type="date" /></div>';
      html += tagsBlock;
    } else if (_gaType === 'note') {
      html += '<div class="ga-field"><label>Contenu <span style="color:#ef4444">*</span></label><textarea id="ga-content" class="ga-input" rows="4" placeholder="Contenu de la note…" style="resize:vertical;min-height:90px"></textarea></div>';
      html += tagsBlock;
    } else if (_gaType === 'url') {
      html += '<div class="ga-field"><label>URL <span style="color:#ef4444">*</span></label><input id="ga-url" class="ga-input" type="url" placeholder="https://…" /></div>';
      html += '<div class="ga-field"><label>Nom</label><input id="ga-name" class="ga-input" type="text" placeholder="Nom affiché (optionnel)" /></div>';
      html += '<div class="ga-field"><label>Description</label><textarea id="ga-desc" class="ga-input" rows="2" placeholder="Description…" style="resize:vertical"></textarea></div>';
      html += tagsBlock;
    } else if (_gaType === 'doc') {
      html += '<div class="ga-field"><label>Fichier <span style="color:#ef4444">*</span></label>';
      html += '<div style="display:flex;gap:8px;align-items:center">';
      html += '<span id="ga-file-label" style="flex:1;font-size:13px;color:#64748b;font-style:italic">Aucun fichier sélectionné</span>';
      html += '<button type="button" onclick="document.getElementById(\'ga-file-inp\').click()" style="padding:7px 14px;border-radius:8px;border:1.5px solid rgba(255,255,255,.15);background:rgba(255,255,255,.08);color:#e2e8f0;cursor:pointer;font-size:13px;font-family:inherit;white-space:nowrap"><i class="fa-solid fa-folder-open"></i> Parcourir</button>';
      html += '<input type="file" id="ga-file-inp" style="display:none" onchange="document.getElementById(\'ga-file-label\').textContent=this.files[0]?.name||\'\';">';
      html += '</div></div>';
      html += '<div class="ga-field"><label>Nom</label><input id="ga-name" class="ga-input" type="text" placeholder="Nom affiché (optionnel)" /></div>';
      html += '<div class="ga-field"><label>Description</label><textarea id="ga-desc" class="ga-input" rows="2" placeholder="Description…" style="resize:vertical"></textarea></div>';
      html += tagsBlock;
    }
    saveBtn.style.display = '';
  } else {
    saveBtn.style.display = 'none';
  }
  body.innerHTML = html;
  // Restore chips
  if (_gaChips.length) _gaRenderChips();
}

async function saveGlobalAdd() {
  const pid = parseInt(document.getElementById('ga-project')?.value);
  if (!pid) { document.getElementById('ga-project')?.focus(); return; }

  const desc = document.getElementById('ga-desc')?.value.trim() || '';
  const tags = [..._gaChips];
  if (_gaType === 'todo') {
    const title = document.getElementById('ga-title')?.value.trim();
    if (!title) { document.getElementById('ga-title').focus(); return; }
    const deadline_date = document.getElementById('ga-deadline')?.value || null;
    await tApi('/api/tasks', 'POST', {title, description:desc, kind:'task', project_id:pid, deadline_date, tags});
  } else if (_gaType === 'note') {
    const content = document.getElementById('ga-content')?.value.trim();
    if (!content) { document.getElementById('ga-content').focus(); return; }
    const noteTags = tags.includes('note') ? tags : ['note', ...tags];
    await tApi('/api/tasks', 'POST', {title:content, description:desc, kind:'task', project_id:pid, tags:noteTags});
  } else if (_gaType === 'url') {
    const url = document.getElementById('ga-url')?.value.trim();
    if (!url) { document.getElementById('ga-url').focus(); return; }
    const name = document.getElementById('ga-name')?.value.trim() || url;
    await tApi('/api/tasks/attachments', 'POST', {task_id:pid, type:'url', name, url, comment:desc});
  } else if (_gaType === 'doc') {
    const fileInp = document.getElementById('ga-file-inp');
    const fileName = fileInp?.files?.[0]?.name || '';
    if (!fileName) { document.getElementById('ga-file-inp').click(); return; }
    const name = document.getElementById('ga-name')?.value.trim() || fileName;
    await tApi('/api/tasks/attachments', 'POST', {task_id:pid, type:'file', name, file_path:fileName, comment:desc});
  }

  _gaProjects = null;
  closeGlobalAdd();
  if (_currentDetailProjectId && _currentDetailProjectId == pid) {
    const res = await tApi('/api/tasks/steps?project_id=' + pid);
    if (res.project) { _detailProjectData = res.project; _renderDetailContent([..._detailActiveTags]); }
  }
}

// ── Quick-add (tâche / note / lien / doc) ────────────────────────────
function dpQuickAdd(type) {
  const formDiv = document.getElementById('dp-quickadd-form');
  if (!formDiv) return;
  // Toggle: click same button again → close
  if (formDiv.dataset.activeType === type && formDiv.style.display !== 'none') {
    formDiv.style.display = 'none';
    formDiv.dataset.activeType = '';
    return;
  }
  formDiv.dataset.activeType = type;
  formDiv.style.display = 'block';
  const pid = _currentDetailProjectId;
  const chantiers = (_detailProjectData && _detailProjectData.chantiers) || [];
  let html = '<div class="dp-quickadd-form">';
  if (type === 'task') {
    html += '<input id="dp-qa-title" class="dp-qa-input" type="text" placeholder="Titre de la tâche…" autofocus />';
    if (chantiers.length) {
      html += '<select id="dp-qa-ch" class="dp-qa-input" style="font-size:13px">';
      html += '<option value="">— Sans chantier —</option>';
      chantiers.forEach(ch => { html += '<option value="' + ch.id + '">' + escHtml(ch.title) + '</option>'; });
      html += '</select>';
    }
    html += '<input id="dp-qa-deadline" class="dp-qa-input" type="date" placeholder="Deadline (optionnel)" />';
    html += '<input id="dp-qa-tags" class="dp-qa-input" type="text" placeholder="Tags (virgule)" />';
  } else if (type === 'note') {
    html += '<textarea id="dp-qa-title" class="dp-qa-input" rows="3" placeholder="Contenu de la note…" style="resize:vertical"></textarea>';
  } else if (type === 'lien') {
    html += '<input id="dp-qa-name" class="dp-qa-input" type="text" placeholder="Nom du lien" />';
    html += '<input id="dp-qa-url" class="dp-qa-input" type="url" placeholder="https://…" autofocus />';
  } else if (type === 'doc') {
    html += '<input id="dp-qa-name" class="dp-qa-input" type="text" placeholder="Nom du document" />';
    html += '<input id="dp-qa-path" class="dp-qa-input" type="text" placeholder="Chemin fichier…" autofocus />';
  }
  html += '<div style="display:flex;gap:6px;justify-content:flex-end">';
  html += '<button class="dp-qa-btn" style="background:#e5e7eb;color:#374151" onclick="document.getElementById(\'dp-quickadd-form\').style.display=\'none\'">Annuler</button>';
  html += '<button class="dp-qa-btn" onclick="dpSaveQuickAdd(\'' + type + '\',' + pid + ')"><i class="fa-solid fa-check"></i> Enregistrer</button>';
  html += '</div></div>';
  formDiv.innerHTML = html;
  const first = formDiv.querySelector('input,textarea');
  if (first) setTimeout(() => first.focus(), 50);
}

async function dpSaveQuickAdd(type, pid) {
  if (type === 'task') {
    const title = (document.getElementById('dp-qa-title') || {}).value.trim();
    if (!title) return;
    const chEl = document.getElementById('dp-qa-ch');
    const chantier_id = chEl && chEl.value ? parseInt(chEl.value) : null;
    const deadlineEl = document.getElementById('dp-qa-deadline');
    const deadline_date = deadlineEl && deadlineEl.value ? deadlineEl.value : null;
    const tagsEl = document.getElementById('dp-qa-tags');
    const tags = tagsEl && tagsEl.value ? tagsEl.value.split(',').map(t => t.trim()).filter(Boolean) : [];
    await tApi('/api/tasks', 'POST', { title, kind: 'task', project_id: pid, chantier_id, deadline_date, tags });
  } else if (type === 'note') {
    const body = (document.getElementById('dp-qa-title') || {}).value.trim();
    if (!body) return;
    await tApi('/api/tasks', 'POST', { title: body, kind: 'task', project_id: pid, tags: ['note'] });
  } else if (type === 'lien') {
    const name = (document.getElementById('dp-qa-name') || {}).value.trim();
    const url = (document.getElementById('dp-qa-url') || {}).value.trim();
    if (!url) return;
    await tApi('/api/tasks/attachments', 'POST', { task_id: pid, type: 'url', name: name || url, url });
  } else if (type === 'doc') {
    const name = (document.getElementById('dp-qa-name') || {}).value.trim();
    const file_path = (document.getElementById('dp-qa-path') || {}).value.trim();
    if (!file_path) return;
    await tApi('/api/tasks/attachments', 'POST', { task_id: pid, type: 'file', name: name || file_path, file_path });
  }
  // Close form and refresh
  const formDiv = document.getElementById('dp-quickadd-form');
  if (formDiv) { formDiv.style.display = 'none'; formDiv.dataset.activeType = ''; }
  const res = await tApi('/api/tasks/steps?project_id=' + pid);
  if (res.project) { _detailProjectData = res.project; _renderDetailContent([..._detailActiveTags]); }
}

async function dpDeleteAttachment(id) {
  await tApi('/api/tasks/attachments', 'DELETE', { id });
  const pid = _currentDetailProjectId;
  const res = await tApi('/api/tasks/steps?project_id=' + pid);
  if (res.project) { _detailProjectData = res.project; _renderDetailContent([..._detailActiveTags]); }
}

// ── API helper ──────────────────────────────────────────────────────
async function tApi(path, method, body) {
  const opts = { method: method || 'GET', headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(window.location.origin + path, opts);
  return r.json();
}

function escHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Vue Aujourd'hui ────────────────────────────────────────────────
async function loadTodayView() {
  const data = await tApi('/api/tasks/today');
  todayData = data;
  renderTodayView(data);
}

function renderTodayView(data) {
  // Conflict badge
  const cb = document.getElementById('tasks-conflict-badge');
  if (data.conflict_count > 0) {
    cb.classList.add('visible');
    document.getElementById('tasks-conflict-msg').textContent = data.conflict_count + ' conflit(s) de synchronisation';
  } else { cb.classList.remove('visible'); }

  // Progress card (only if there are today tasks)
  const total = data.progress.total || 0;
  const done = data.progress.done || 0;
  const pct = total ? Math.round(done / total * 100) : 0;
  const pc = document.getElementById('tasks-progress-card');
  pc.style.display = total ? '' : 'none';
  const dateStr = new Date().toLocaleDateString('fr-FR', {weekday:'long',day:'numeric',month:'long'});
  document.getElementById('tasks-date').textContent = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
  document.getElementById('tasks-progress-fill').style.width = pct + '%';
  document.getElementById('tasks-progress-label').textContent = done + ' / ' + total;

  // All done banner
  const adb = document.getElementById('tasks-all-done-banner');
  adb.style.display = data.all_done && total > 0 ? '' : 'none';

  let html = '';

  if (data.overdue && data.overdue.length > 0) {
    html += '<div class="t-section"><div class="t-section-title"><span class="t-dot t-dot-red"></span> En retard (' + data.overdue.length + ')</div>';
    html += data.overdue.map(t => tCard(t, 'overdue')).join('');
    html += '</div>';
  }

  html += '<div class="t-section"><div class="t-section-title"><span class="t-dot t-dot-blue"></span> Aujourd\'hui (' + data.today.length + ')</div>';
  if (data.today.length) {
    html += data.today.map(t => tCard(t, 'today')).join('');
  } else {
    html += '<div class="t-empty"><i class="fa-regular fa-circle-check"></i><p>Aucune t\u00e2che pour aujourd\'hui.<br>Clique sur + pour en ajouter.</p></div>';
  }
  html += '</div>';

  if (data.done_today && data.done_today.length > 0) {
    html += '<div class="t-section"><div class="t-section-title"><span class="t-dot t-dot-green"></span> Faites (' + data.done_today.length + ')</div>';
    html += data.done_today.map(t => tCard(t, 'done')).join('');
    html += '</div>';
  }

  if (data.tomorrow && data.tomorrow.length > 0) {
    html += '<div class="t-section"><div class="t-section-title"><span class="t-dot t-dot-gray"></span> Demain (' + data.tomorrow.length + ')</div>';
    html += data.tomorrow.map(t => tCard(t, 'tomorrow')).join('');
    html += '</div>';
  }

  document.getElementById('tasks-main-container').innerHTML = html;
}

function tCard(t, type) {
  const isDone = t.status === 'done';
  const isBlocked = t.blocked_by_id;
  const tags = (t.tags || []).filter(tg => !['today','later','tomorrow','projet','chantier','task'].includes(tg));
  const attachCount = (t.attachments || []).length;
  const subCount = (t.subtasks || []).length;
  const tagsHtml = tags.map(tg => '<span class="t-tag">' + escHtml(tg) + '</span>').join('');
  const blockedHtml = isBlocked ? '<span class="t-badge t-badge-orange"><i class="fa-solid fa-clock"></i> Bloqu\u00e9</span>' : '';
  const attachHtml = attachCount ? '<span class="t-badge t-badge-gray"><i class="fa-solid fa-paperclip"></i> ' + attachCount + '</span>' : '';
  const subHtml = subCount ? '<span class="t-badge t-badge-gray"><i class="fa-solid fa-list"></i> ' + subCount + '</span>' : '';
  const schedBtn = type !== 'done' && type !== 'tomorrow'
    ? '<button class="t-btn" onclick="event.stopPropagation();rescheduleTask(' + t.id + ',\'' + (type==='today'?'later':'today') + '\')" title="' + (type==='today'?'Reporter':'Planifier aujourd\'hui') + '"><i class="fa-solid fa-' + (type==='today'?'forward':'calendar-day') + '"></i></button>'
    : '';
  return '<div class="t-card ' + type + (isDone?' done':'') + (isBlocked?' blocked':'') + '" onclick="openTaskDetail(' + t.id + ')">'
    + '<div class="t-check ' + (isDone?'checked':'') + '" onclick="event.stopPropagation();toggleDone(' + t.id + ',' + isDone + ')" title="' + (isDone?'D\u00e9cocher':'Marquer fait') + '"></div>'
    + '<div class="t-body">'
    + '<div class="t-title' + (isDone?' done-text':'') + '">' + escHtml(t.title) + '</div>'
    + (t.description ? '<div class="t-desc">' + escHtml(t.description) + '</div>' : '')
    + '<div class="t-meta">' + tagsHtml + blockedHtml + attachHtml + subHtml + '</div>'
    + '</div>'
    + '<div class="t-actions">'
    + schedBtn
    + '<button class="t-btn" onclick="event.stopPropagation();openEditTask(' + t.id + ')" title="Modifier"><i class="fa-solid fa-pen"></i></button>'
    + '<button class="t-btn danger" onclick="event.stopPropagation();deleteTask(' + t.id + ')" title="Supprimer"><i class="fa-solid fa-trash"></i></button>'
    + '</div>'
    + '</div>';
}

async function toggleDone(id, isDone) {
  const endpoint = isDone ? '/api/tasks/undone' : '/api/tasks/done';
  const res = await tApi(endpoint, 'POST', { id });
  if (res.success) loadTodayView();
}

async function rescheduleTask(id, scheduled) {
  await tApi('/api/tasks/schedule', 'POST', { id, scheduled });
  loadTodayView();
}

async function deleteTask(id) {
  if (!confirm('Supprimer cette t\u00e2che ?')) return;
  await tApi('/api/tasks', 'DELETE', { id });
  if (currentTab === 'today') loadTodayView();
  else loadProjectsView();
}

// ── Labels par kind ─────────────────────────────────────────────────
const KIND_LABEL = { projet: 'Projet', chantier: 'Chantier', task: 'Tâche' };

// ── Gestion chips tags ───────────────────────────────────────────────
let _modalTags = [];

function _renderTagChips() {
  const container = document.getElementById('t-tag-chips');
  container.innerHTML = _modalTags.map((t, i) =>
    '<span class="tag-chip">' + escHtml(t) +
    '<button onclick="_removeTag(' + i + ')" title="Supprimer">&times;</button></span>'
  ).join('');
}

function _removeTag(i) {
  _modalTags.splice(i, 1);
  _renderTagChips();
}

function _addTagFromInput() {
  const input = document.getElementById('t-task-tags');
  const val = input.value.trim().toLowerCase();
  if (val && !_modalTags.includes(val)) {
    _modalTags.push(val);
    _renderTagChips();
  }
  input.value = '';
}

function _resetModal() {
  ['t-task-title','t-task-desc','t-task-goal','t-task-mission','t-task-tags'].forEach(id => {
    document.getElementById(id).value = '';
  });
  document.getElementById('t-task-deadline').value = '';
  document.getElementById('t-task-edit-id').value = '';
  document.getElementById('t-task-project-id').value = '';
  document.getElementById('t-task-chantier-id').value = '';
  _modalTags = [];
  _renderTagChips();
}

// openAddTask(kind, projectId, chantierId)
async function openAddTask(kind, projectId, chantierId) {
  _resetModal();
  kind = kind || (currentTab === 'today' ? 'task' : 'projet');
  document.getElementById('t-modal-task-title').textContent = 'Nouveau ' + KIND_LABEL[kind];
  document.getElementById('t-task-type').value = kind;
  document.getElementById('t-type-field').style.display = kind === 'task' ? 'none' : '';  // masquer si imposé
  document.getElementById('t-task-scheduled').value = currentTab === 'today' ? 'today' : 'later';
  if (projectId)  document.getElementById('t-task-project-id').value  = projectId;
  if (chantierId) document.getElementById('t-task-chantier-id').value = chantierId;
  // Masquer planification pour projet/chantier
  document.getElementById('t-scheduled-field').style.display = kind === 'task' ? '' : 'none';
  document.getElementById('t-modal-task').classList.add('open');
  setTimeout(() => document.getElementById('t-task-title').focus(), 100);
}

async function openEditTask(id) {
  const res = await tApi('/api/tasks?id=' + id);
  const t = res.tasks ? res.tasks[0] : null;
  if (!t) return;
  const kind = t.kind || 'task';
  document.getElementById('t-modal-task-title').textContent = 'Modifier — ' + KIND_LABEL[kind];
  document.getElementById('t-task-title').value    = t.title;
  document.getElementById('t-task-desc').value     = t.description || '';
  document.getElementById('t-task-goal').value     = t.goal || '';
  document.getElementById('t-task-mission').value  = t.mission || '';
  document.getElementById('t-task-deadline').value = t.deadline_date || '';
  document.getElementById('t-task-type').value     = kind;
  document.getElementById('t-task-scheduled').value = t.scheduled || 'later';
  document.getElementById('t-task-edit-id').value  = id;
  document.getElementById('t-task-project-id').value  = t.project_id || '';
  document.getElementById('t-task-chantier-id').value = t.chantier_id || '';
  _modalTags = (t.tags || []).filter(tg => !['pro','perso'].includes(tg));
  document.getElementById('t-task-tags').value = '';
  _renderTagChips();
  // Affichage champs selon kind
  document.getElementById('t-type-field').style.display = '';
  document.getElementById('t-scheduled-field').style.display = kind === 'task' ? '' : 'none';
  closeDetailModal();
  document.getElementById('t-modal-task').classList.add('open');
}

function closeTaskModal() {
  document.getElementById('t-modal-task').classList.remove('open');
}

// ── Partage / QR Code ────────────────────────────────────────────────
function showShareQR(e) {
  if (e) e.preventDefault();
  const params = new URLSearchParams();
  if (state.includeTags.length > 0) params.set('include', state.includeTags.join(','));
  if (state.excludeTags.length > 0) params.set('exclude', state.excludeTags.join(','));
  if (state.activeTypes.length > 0) params.set('types', state.activeTypes.join(','));
  const shareUrl = window.location.origin + '/' + (params.toString() ? '?' + params.toString() : '');

  const ov = document.createElement('div');
  ov.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:9999';
  ov.innerHTML = '<div style="background:#fff;border-radius:12px;padding:24px;width:340px;text-align:center;box-shadow:0 4px 24px rgba(0,0,0,0.25)">'
    + '<h3 style="margin:0 0 16px;color:#333"><i class="fa-solid fa-qrcode"></i> Partager</h3>'
    + '<div id="_share-qr" style="margin:0 auto 16px;width:200px;height:200px"></div>'
    + '<input type="text" value="' + shareUrl.replace(/"/g,'&quot;') + '" readonly style="width:100%;padding:6px 8px;border:1px solid #ddd;border-radius:6px;font-size:12px;background:#f8f8f8" onclick="this.select()">'
    + '<div style="margin-top:12px;display:flex;gap:8px;justify-content:center">'
    + '<button onclick="navigator.clipboard.writeText(\'' + shareUrl.replace(/'/g,"\\'") + '\').then(()=>this.textContent=\'Copié !\')" style="padding:6px 14px;background:#4a90d9;color:#fff;border:none;border-radius:6px;cursor:pointer">Copier le lien</button>'
    + '<button onclick="this.closest(\'div[style*=fixed]\').remove()" style="padding:6px 14px;background:#f0f0f0;color:#555;border:none;border-radius:6px;cursor:pointer">Fermer</button>'
    + '</div></div>';
  document.body.appendChild(ov);
  ov.addEventListener('click', function(e) { if (e.target === ov) ov.remove(); });
  if (typeof QRCode !== 'undefined') {
    new QRCode(document.getElementById('_share-qr'), { text: shareUrl, width: 200, height: 200, correctLevel: QRCode.CorrectLevel.M });
  } else {
    document.getElementById('_share-qr').innerHTML = '<div style="color:#999;font-size:12px;line-height:200px">QR code non disponible</div>';
  }
}


async function saveTask() {
  const title = document.getElementById('t-task-title').value.trim();
  if (!title) { alert('Le titre est obligatoire'); return; }
  const kind        = document.getElementById('t-task-type').value;
  const scheduled   = document.getElementById('t-task-scheduled').value;
  const editId      = document.getElementById('t-task-edit-id').value;
  const projectId   = document.getElementById('t-task-project-id').value;
  const chantierId  = document.getElementById('t-task-chantier-id').value;
  const description = document.getElementById('t-task-desc').value.trim();
  const goal        = document.getElementById('t-task-goal').value.trim();
  const mission     = document.getElementById('t-task-mission').value.trim();
  const deadline    = document.getElementById('t-task-deadline').value || null;
  // Flush any pending tag from input before saving
  _addTagFromInput();

  const payload = { title, description, goal, mission, kind, scheduled,
                    deadline_date: deadline, tags: _modalTags,
                    project_id:  projectId  ? parseInt(projectId)  : null,
                    chantier_id: chantierId ? parseInt(chantierId) : null };

  if (editId) {
    await tApi('/api/tasks', 'PUT', { id: parseInt(editId), ...payload });
  } else {
    await tApi('/api/tasks', 'POST', payload);
  }
  closeTaskModal();
  if (_currentDetailProjectId !== null) { showProjectDetail(_currentDetailProjectId); }
  else if (currentTab === 'today') loadTodayView();
  else loadProjectsView();
}

// ── Task detail ─────────────────────────────────────────────────────
async function openTaskDetail(id) {
  currentDetailId = id;
  const res = await tApi('/api/tasks?id=' + id);
  const t = res.tasks ? res.tasks[0] : null;
  if (!t) return;
  document.getElementById('t-detail-title').textContent = t.title;

  let html = '';
  if (t.description) html += '<p style="color:#6b7280;font-size:13px;margin-bottom:12px">' + escHtml(t.description) + '</p>';

  const tags = (t.tags || []).filter(tg => !['today','later','tomorrow','projet','chantier','task'].includes(tg));
  if (tags.length) html += '<div style="margin-bottom:12px">' + tags.map(tg => '<span class="t-tag" style="font-size:12px">' + escHtml(tg) + '</span>').join(' ') + '</div>';

  // Sous-t\u00e2ches
  if (t.subtasks && t.subtasks.length) {
    html += '<div style="margin-bottom:12px"><strong style="font-size:12px">Sous-t\u00e2ches (' + t.subtasks.length + ')</strong>';
    t.subtasks.forEach(st => {
      html += '<div style="padding:6px 0;border-bottom:1px solid #f3f4f6;font-size:13px;display:flex;gap:8px;align-items:center">';
      html += '<span style="color:' + (st.status==='done'?'#16a34a':'#9ca3af') + '">' + (st.status==='done'?'✓':'○') + '</span>';
      html += escHtml(st.title) + '</div>';
    });
    html += '</div>';
  }

  // Pi\u00e8ces jointes
  html += '<div id="t-detail-attachments"><strong style="font-size:12px">Pi\u00e8ces jointes</strong>';
  if (t.attachments && t.attachments.length) {
    t.attachments.forEach(a => {
      html += '<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #f3f4f6">';
      html += '<i class="fa-solid fa-' + (a.type==='url'?'link':'file') + '" style="color:#9ca3af"></i>';
      html += '<span style="flex:1;font-size:13px">' + escHtml(a.name) + '</span>';
      if (a.url) html += '<a href="' + escHtml(a.url) + '" target="_blank" style="font-size:12px">Ouvrir</a>';
      html += '<button class="t-btn danger" onclick="deleteAttachment(' + a.id + ')" style="padding:2px 6px"><i class="fa-solid fa-times"></i></button>';
      html += '</div>';
    });
  } else {
    html += '<div style="font-size:12px;color:#9ca3af;padding:8px 0">Aucune pi\u00e8ce jointe</div>';
  }
  html += '<div style="margin-top:8px;display:flex;gap:6px">'
    + '<input type="text" id="t-att-name" placeholder="Nom *" style="flex:1;padding:6px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:12px">'
    + '<input type="text" id="t-att-url" placeholder="URL" style="flex:2;padding:6px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:12px">'
    + '<button class="t-btn" onclick="addAttachment(' + id + ')" style="padding:6px 10px"><i class="fa-solid fa-plus"></i></button>'
    + '</div>';
  html += '</div>';

  document.getElementById('t-detail-body').innerHTML = html;
  document.getElementById('t-modal-detail').classList.add('open');
}

function closeDetailModal() {
  document.getElementById('t-modal-detail').classList.remove('open');
  currentDetailId = null;
}

async function addAttachment(taskId) {
  const name = document.getElementById('t-att-name').value.trim();
  const url = document.getElementById('t-att-url').value.trim();
  if (!name) { alert('Le nom est obligatoire'); return; }
  await tApi('/api/tasks/attachments', 'POST', { task_id: taskId, type: url ? 'url' : 'file', name, url });
  openTaskDetail(taskId);
}

async function deleteAttachment(id) {
  await tApi('/api/tasks/attachments', 'DELETE', { id });
  if (currentDetailId) openTaskDetail(currentDetailId);
}

// ── Vue Projets ─────────────────────────────────────────────────────
async function loadProjectsView() {
  const data = await tApi('/api/tasks/projects');
  projectsData = data.projects || [];
  renderProjectsView();
}

const STATUS_COLORS = { actif:'#16a34a', pause:'#d97706', archive:'#9ca3af', idee:'#6366f1', stable:'#0ea5e9', bloque:'#dc2626', todo:'#6b7280', done:'#16a34a' };
const KIND_ICON = { projet:'fa-folder-open', chantier:'fa-layer-group', task:'fa-circle-dot' };

function renderProjectsView() {
  const el = document.getElementById('projects-main-container');
  if (!projectsData.length) {
    el.innerHTML = '<div class="t-empty"><i class="fa-solid fa-folder-open"></i><p>Aucun projet.</p></div>';
    return;
  }
  el.innerHTML = '<div class="t-section">' + projectsData.map(p => projAccordion(p, 0)).join('') + '</div>';
}

function projAccordion(p, depth) {
  const kind     = p.kind || 'task';
  const chantiers = p.chantiers || [];
  const subtasks  = p.subtasks  || [];
  const children  = kind === 'projet' ? chantiers : subtasks;
  const hasChildren = children.length > 0;
  const toggleId = 'proj-' + p.id;
  const indent   = depth * 18;
  const statusColor = STATUS_COLORS[p.status] || '#9ca3af';
  const icon = KIND_ICON[kind] || 'fa-circle-dot';
  const fw = depth === 0 ? 700 : depth === 1 ? 600 : 400;
  const fs = depth === 0 ? 15 : depth === 1 ? 14 : 13;

  const rowClick = kind === 'projet' ? 'showProjectDetail(' + p.id + ')' : 'toggleProj(\'' + toggleId + '\')';
  let html = '<div class="proj-row" style="padding-left:' + (10 + indent) + 'px" onclick="' + rowClick + '">';
  html += '<span class="proj-toggle" id="' + toggleId + '-icon" style="color:#9ca3af;font-size:10px;width:14px"' + (kind !== 'projet' ? '' : ' onclick="event.stopPropagation();toggleProj(\'' + toggleId + '\')"') + '>' + (hasChildren ? '&#9658;' : '&nbsp;') + '</span>';
  html += '<i class="fa-solid ' + icon + '" style="color:' + statusColor + ';font-size:12px;flex-shrink:0"></i>';
  html += '<span style="flex:1;font-size:' + fs + 'px;font-weight:' + fw + ';margin-left:6px">' + escHtml(p.title) + '</span>';
  // Badges status / deadline
  if (p.status && p.status !== 'todo') html += '<span style="font-size:10px;padding:1px 6px;border-radius:4px;background:' + statusColor + '22;color:' + statusColor + ';font-weight:600">' + escHtml(p.status) + '</span>';
  if (p.deadline_date) html += '<span style="font-size:10px;color:#d97706;margin-left:4px"><i class="fa-regular fa-calendar"></i> ' + escHtml(p.deadline_date) + '</span>';
  // Boutons actions
  html += '<div class="t-actions" onclick="event.stopPropagation()">';
  if (kind === 'projet') {
    html += '<button class="t-btn" onclick="openAddTask(\'chantier\',' + p.id + ',null)" title="Ajouter un chantier"><i class="fa-solid fa-layer-group"></i></button>';
    html += '<button class="t-btn" onclick="openAddTask(\'task\',' + p.id + ',null)" title="Ajouter une tâche"><i class="fa-solid fa-plus"></i></button>';
  } else if (kind === 'chantier') {
    html += '<button class="t-btn" onclick="openAddTask(\'task\',' + (p.project_id||'null') + ',' + p.id + ')" title="Ajouter une tâche"><i class="fa-solid fa-plus"></i></button>';
  }
  html += '<button class="t-btn" onclick="openEditTask(' + p.id + ')" title="Modifier"><i class="fa-solid fa-pen"></i></button>';
  html += '</div>';
  html += '</div>';

  if (hasChildren) {
    html += '<div class="proj-children" id="' + toggleId + '" style="display:none">';
    if (kind === 'projet') {
      // Chantiers d'abord
      html += chantiers.map(ch => projAccordion(ch, depth + 1)).join('');
      // Puis tâches directes
      if (subtasks.length) {
        html += '<div style="padding-left:' + (10 + indent + 18) + 'px;padding-top:2px">';
        html += subtasks.map(t => projAccordion(t, depth + 2)).join('');
        html += '</div>';
      }
    } else {
      html += subtasks.map(t => projAccordion(t, depth + 1)).join('');
    }
    html += '</div>';
  }
  return html;
}

function toggleProj(id) {
  const el = document.getElementById(id);
  const icon = document.getElementById(id + '-icon');
  if (!el) return;
  const open = el.style.display !== 'none';
  el.style.display = open ? 'none' : '';
  icon.textContent = open ? '\u25b6' : '\u25bc';
}

// ── Plan demain ─────────────────────────────────────────────────────
async function openPlanTomorrow() {
  tomorrowSelected.clear();
  const data = await tApi('/api/tasks?scheduled=later&status=todo');
  const tasks = data.tasks || [];
  let html = '';
  if (!tasks.length) {
    html = '<div style="color:#9ca3af;font-size:13px;padding:12px 0">Aucune t\u00e2che disponible (toutes planifi\u00e9es ou faites).</div>';
  } else {
    tasks.forEach(t => {
      html += '<label style="display:flex;align-items:center;gap:10px;padding:8px 0;cursor:pointer;border-bottom:1px solid #f3f4f6">'
        + '<input type="checkbox" value="' + t.id + '" onchange="tomorrowSelected[this.checked?\'add\':\'delete\'](' + t.id + ')">'
        + '<span style="font-size:14px">' + escHtml(t.title) + '</span>'
        + '</label>';
    });
  }
  document.getElementById('t-tomorrow-list').innerHTML = html;
  document.getElementById('t-modal-tomorrow').classList.add('open');
}

function closeTomorrowModal() {
  document.getElementById('t-modal-tomorrow').classList.remove('open');
}

async function confirmTomorrow() {
  for (const id of tomorrowSelected) {
    await tApi('/api/tasks/schedule', 'POST', { id, scheduled: 'tomorrow' });
  }
  closeTomorrowModal();
  loadTodayView();
}

// ── Conflits ────────────────────────────────────────────────────────
async function openTasksConflicts() {
  const data = await tApi('/api/tasks/conflicts');
  const conflicts = data.conflicts || [];
  let html = '';
  conflicts.forEach(c => {
    html += '<div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:12px">';
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:10px">';
    html += '<div><div style="font-size:11px;font-weight:600;margin-bottom:6px;color:#6b7280">ORIGINAL</div><div style="font-size:14px">' + escHtml(c.original_title || c.title) + '</div></div>';
    html += '<div><div style="font-size:11px;font-weight:600;margin-bottom:6px;color:#6b7280">CONFLIT</div><div style="font-size:14px">' + escHtml(c.title) + '</div></div>';
    html += '</div>';
    html += '<div style="display:flex;gap:6px">';
    html += '<button class="t-btn" onclick="resolveConflict(' + c.id + ',\'original\')">Garder original</button>';
    html += '<button class="t-btn" onclick="resolveConflict(' + c.id + ',\'conflict\')">Garder conflit</button>';
    html += '<button class="t-btn" onclick="resolveConflict(' + c.id + ',\'both\')">Garder les deux</button>';
    html += '</div></div>';
  });
  if (!html) html = '<div style="color:#9ca3af;font-size:13px;padding:12px 0">Aucun conflit.</div>';
  document.getElementById('t-conflicts-body').innerHTML = html;
  document.getElementById('t-modal-conflicts').classList.add('open');
}

async function resolveConflict(id, keep) {
  await tApi('/api/tasks/conflicts/resolve', 'POST', { conflict_id: id, keep });
  openTasksConflicts();
  loadTodayView();
}

function closeConflictsModal() {
  document.getElementById('t-modal-conflicts').classList.remove('open');
}
</script>
<script src="/qrcode.min.js" defer></script>
</body>
</html>"""


# ────────────────────────────────────────────────────────────
# Identity P2P — Helpers session
# ────────────────────────────────────────────────────────────

def _unlock_identity(password: str = None) -> bool:
    """Charge private keys en mémoire et démarre la session.

    Args:
        password: Mot de passe si l'identité est protégée

    Returns:
        True si déverrouillage réussi, False sinon
    """
    if not IDENTITY_AVAILABLE:
        return False
    try:
        rsa_key, ed25519_key = load_private_keys(password)
        _identity_session["unlocked"] = True
        _identity_session["private_keys"] = (rsa_key, ed25519_key)
        _identity_session["unlocked_at"] = datetime.now()
        _identity_session["expires_at"] = datetime.now() + timedelta(hours=1)
        return True
    except Exception as e:
        print(f"❌ Erreur déverrouillage identité : {e}")
        return False


def _lock_identity():
    """Efface private keys de la mémoire et verrouille la session."""
    _identity_session["unlocked"] = False
    _identity_session["private_keys"] = None
    _identity_session["unlocked_at"] = None
    _identity_session["expires_at"] = None


def _is_session_valid() -> bool:
    """Vérifie que la session identity est active et non expirée.

    Returns:
        True si session valide, False sinon
    """
    if not _identity_session["unlocked"]:
        return False
    if _identity_session["expires_at"] is None:
        return False
    if datetime.now() > _identity_session["expires_at"]:
        _lock_identity()
        return False
    return True


# ────────────────────────────────────────────────────────────
# Identity P2P — Route handlers
# ────────────────────────────────────────────────────────────

def handle_identity_status(handler):
    """GET /api/identity/status — Retourne le statut de l'identité.

    Returns:
        {
            "initialized": bool,
            "user_id": str (si initialisé),
            "alias": str (si initialisé),
            "protected": bool (si initialisé),
            "created_at": str (si initialisé)
        }
    """
    if not IDENTITY_AVAILABLE:
        return {"error": "identity_module_unavailable"}

    identity = get_identity()
    if identity:
        return {
            "initialized": True,
            "user_id": identity["user_id"],
            "alias": identity["alias"],
            "protected": identity["protection"]["enabled"],
            "created_at": identity["created_at"]
        }
    return {"initialized": False}


def handle_identity_init(handler, data):
    """POST /api/identity/init — Initialise nouvelle identité.

    Args:
        data: {"alias": str (optionnel), "password": str (optionnel)}

    Returns:
        {
            "success": bool,
            "user_id": str,
            "public_key_rsa": str,
            "public_key_ed25519": str
        }
    """
    if not IDENTITY_AVAILABLE:
        return {"error": "identity_module_unavailable"}

    # Vérifier qu'aucune identité n'existe déjà
    if get_identity():
        return {"error": "identity_already_exists"}

    alias = data.get("alias", "User")
    password = data.get("password")

    try:
        identity = init_identity(alias, password)

        # Déverrouiller session automatiquement
        _unlock_identity(password)

        return {
            "success": True,
            "user_id": identity["user_id"],
            "public_key_rsa": identity["keys"]["rsa"]["public_key"],
            "public_key_ed25519": identity["keys"]["ed25519"]["public_key"]
        }
    except Exception as e:
        print(f"❌ Erreur init identity : {e}")
        return {"error": str(e)}


def handle_identity_public_key(handler):
    """GET /api/identity/public_key — Retourne les clés publiques.

    Returns:
        {
            "user_id": str,
            "public_key_rsa": str,
            "public_key_ed25519": str
        }
    """
    if not IDENTITY_AVAILABLE:
        return {"error": "identity_module_unavailable"}

    identity = get_identity()
    if not identity:
        return {"error": "identity_not_initialized"}

    return {
        "user_id": identity["user_id"],
        "public_key_rsa": identity["keys"]["rsa"]["public_key"],
        "public_key_ed25519": identity["keys"]["ed25519"]["public_key"]
    }


def handle_identity_sign(handler, data):
    """POST /api/identity/sign — Signe des données (auth challenge).

    Args:
        data: {"data": str, "key_type": str (optionnel, défaut "ed25519")}

    Returns:
        {
            "signature": str,
            "algorithm": str
        }
    """
    if not IDENTITY_AVAILABLE:
        return {"error": "identity_module_unavailable"}

    if not _is_session_valid():
        return {"error": "session_locked"}

    data_to_sign = data.get("data")
    if not data_to_sign:
        return {"error": "missing_data"}

    key_type = data.get("key_type", "ed25519")

    try:
        signature = sign_data(data_to_sign, key_type)

        return {
            "signature": signature,
            "algorithm": key_type
        }
    except Exception as e:
        print(f"❌ Erreur signature : {e}")
        return {"error": str(e)}


def handle_identity_verify(handler, data):
    """POST /api/identity/verify — Vérifie une signature.

    Args:
        data: {
            "data": str,
            "signature": str,
            "public_key": str,
            "key_type": str (optionnel, défaut "ed25519")
        }

    Returns:
        {"valid": bool}
    """
    if not IDENTITY_AVAILABLE:
        return {"error": "identity_module_unavailable"}

    data_str = data.get("data")
    signature = data.get("signature")
    public_key = data.get("public_key")

    if not all([data_str, signature, public_key]):
        return {"error": "missing_parameters"}

    key_type = data.get("key_type", "ed25519")

    try:
        valid = verify_signature(data_str, signature, public_key, key_type)
        return {"valid": valid}
    except Exception as e:
        print(f"❌ Erreur vérification signature : {e}")
        return {"error": str(e), "valid": False}


def handle_identity_protect(handler, data):
    """POST /api/identity/protect — Protège l'identité avec un mot de passe.

    Args:
        data: {"password": str}

    Returns:
        {"success": bool, "message": str}
    """
    if not IDENTITY_AVAILABLE:
        return {"error": "identity_module_unavailable"}

    password = data.get("password")
    if not password:
        return {"error": "missing_password"}

    try:
        success = protect_identity(password)

        if success:
            _lock_identity()
            return {"success": True, "message": "Identité protégée"}
        return {"error": "protection_failed"}
    except Exception as e:
        print(f"❌ Erreur protection identity : {e}")
        return {"error": str(e)}


def handle_identity_unlock(handler, data):
    """POST /api/identity/unlock — Déverrouille la session.

    Args:
        data: {"password": str (optionnel si non protégée)}

    Returns:
        {"success": bool}
    """
    if not IDENTITY_AVAILABLE:
        return {"error": "identity_module_unavailable"}

    password = data.get("password")

    if _unlock_identity(password):
        return {"success": True}
    return {"error": "incorrect_password"}


class SearchHandler(http.server.BaseHTTPRequestHandler):
    """Gère les requêtes de l'extension Chrome."""

    def do_OPTIONS(self):
        """CORS preflight."""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        routes = {
            "/api/autocomplete": self.handle_autocomplete,
            "/api/search": self.handle_search,
            "/api/cooccurrence": self.handle_cooccurrence,
            "/api/stats": self.handle_stats,
            "/api/open": self.handle_open,
            "/api/reveal": self.handle_reveal,
            "/api/email": self.handle_email,
            "/api/vault/get": self.handle_vault_get,
            "/api/vault/copy": self.handle_vault_copy,
            "/api/vault/lock": self.handle_vault_lock,
            "/api/vault/status": self.handle_vault_status,
            "/api/thumbnail": self.handle_thumbnail,
            "/api/note": self.handle_note,
            "/api/favorite/check": self.handle_favorite_check,
            "/api/event": self.handle_event_get,
            "/api/events/upcoming": self.handle_events_upcoming,
            "/api/contact": self.handle_contact_get,
            "/api/contacts/search": self.handle_contacts_search,
            "/api/lieu": self.handle_lieu_get,
            "/api/lieux/search": self.handle_lieux_search,
            "/api/relations": self.handle_relations_get,
            "/api/system-contacts/list": self.handle_system_contacts_list,
            "/api/tags/get": self.handle_tags_get,
            "/api/identity/status": self.handle_identity_status_get,
            "/api/identity/public_key": self.handle_identity_public_key_get,
            "/api/consult/list": self.handle_consult_list,  # Phase 5
            "/api/i18n": self.handle_i18n,  # Internationalization
            "/api/share/notifications": self.handle_share_notifications,  # Notifications d'acceptation
            # ── Tasks / Dashboard ──────────────────────────────────────────────
            "/api/tasks": self.handle_tasks_list,
            "/api/tasks/today": self.handle_tasks_today,
            "/api/tasks/tags": self.handle_tasks_tags,
            "/api/tasks/projects": self.handle_tasks_projects,
            "/api/tasks/conflicts": self.handle_tasks_conflicts,
            "/api/tasks/steps": self.handle_tasks_steps,
        }

        if path == "/" or path == "":
            self._serve_fullpage()
            return

        if path == "/today":
            self.send_response(301)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if path == "/qrcode.min.js":
            qr_path = os.path.join(os.path.dirname(__file__), "..", "extension", "qrcode.min.js")
            try:
                with open(os.path.abspath(qr_path), "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript")
                self.send_header("Cache-Control", "max-age=3600")
                self.end_headers()
                self.wfile.write(data)
            except Exception:
                self._json_response(404, {"error": "qrcode.min.js not found"})
            return

        if path == "/accept":
            self._serve_accept_page(params)
            return

        handler = routes.get(path)
        if handler:
            try:
                result = handler(params)
                self._json_response(200, result)
            except Exception as e:
                self._json_response(500, {"error": str(e)})
        else:
            self._json_response(404, {"error": "Route inconnue"})

    def handle_autocomplete(self, params):
        """Autocomplétion : retourne les tags commençant par le préfixe.

        Scoring de pertinence :
        - 100 : match exact sur tag_display (forme originale)
        - 50 : match sur tag (racine normalisée)
        """
        q = params.get("q", [""])[0].lower().strip()
        if len(q) < 1:
            return {"tags": []}

        q_normalized = normalize_tag(q)

        conn = get_db()
        c = conn.cursor()

        # Chercher à la fois dans tag_display ET tag, grouper par tag
        # Prendre le tag_display le plus fréquent (et le plus long en cas d'égalité)
        c.execute("""
            WITH tag_groups AS (
                SELECT tag, tag_display, COUNT(*) as freq
                FROM tags
                WHERE tag_display LIKE ? || '%' OR tag LIKE ? || '%'
                GROUP BY tag, tag_display
            ),
            best_display AS (
                SELECT tag,
                       (SELECT tag_display FROM tag_groups tg2
                        WHERE tg2.tag = tg1.tag
                        ORDER BY freq DESC, LENGTH(tag_display) DESC
                        LIMIT 1) as display,
                       SUM(freq) as total_freq
                FROM tag_groups tg1
                GROUP BY tag
            )
            SELECT display,
                   CASE
                       WHEN display LIKE ? || '%' THEN 100
                       WHEN tag LIKE ? || '%' THEN 50
                       ELSE 0
                   END as score,
                   total_freq
            FROM best_display
            ORDER BY score DESC, total_freq DESC
            LIMIT 20
        """, (q, q_normalized, q, q_normalized))

        tags = [{"tag": row[0], "count": row[2], "score": row[1]} for row in c.fetchall()]
        conn.close()
        return {"tags": tags}

    def handle_search(self, params):
        """Recherche par tags (inclusion + exclusion), filtre optionnel par type.

        Les tags sont normalisés (stemming français) pour trouver toutes les variantes :
        'rechercher', 'recherche', 'recherché' → même racine → mêmes résultats.
        """
        include = [t.strip() for t in params.get("include", []) if t.strip()]
        exclude = [t.strip() for t in params.get("exclude", []) if t.strip()]
        limit = int(params.get("limit", ["50"])[0])
        offset = int(params.get("offset", ["0"])[0])
        # Filtre par type : file, email, note, vault, video (comma-separated)
        types_raw = params.get("types", [""])[0].strip()
        active_types = set(t.strip() for t in types_raw.split(",") if t.strip()) if types_raw else set()
        # Filtre par source : local (défaut), consulted, all (Phase 5)
        source_filter = params.get("source", ["local"])[0].strip()

        if not include and not active_types:
            return {"results": [], "total": 0}

        # Type projet = uniquement tasks.db, bypass catalogue.db
        if active_types == {"projet"}:
            return self._search_projets_only(include, exclude, limit, offset)

        conn = get_db()
        c = conn.cursor()

        if include:
            # Items qui ont TOUS les tags inclus (chercher dans tag_display)
            placeholders_inc = ",".join("?" * len(include))
            query = f"""
                SELECT t.item_id
                FROM tags t
                WHERE t.tag_display IN ({placeholders_inc})
                GROUP BY t.item_id
                HAVING COUNT(DISTINCT t.tag_display) = ?
            """
            query_params = list(include) + [len(include)]

            # Exclure les items qui ont un tag exclu
            if exclude:
                placeholders_exc = ",".join("?" * len(exclude))
                query = f"""
                    SELECT item_id FROM ({query})
                    WHERE item_id NOT IN (
                        SELECT item_id FROM tags WHERE tag_display IN ({placeholders_exc})
                    )
                """
                query_params += list(exclude)

            c.execute(f"SELECT item_id FROM ({query})", query_params)
            all_ids = [row[0] for row in c.fetchall()]
        else:
            # Pas de tags mais filtre type actif → tous les items distincts
            c.execute("SELECT DISTINCT item_id FROM tags")
            all_ids = [row[0] for row in c.fetchall()]

        # Filtrer par type si demandé
        if active_types:
            def _type_match(i):
                if i > 0:
                    return "file" in active_types
                if -200000 <= i < -100000:
                    return "email" in active_types
                if -300000 <= i < -200000:
                    return "note" in active_types
                if -400000 <= i < -300000:
                    return "vault" in active_types
                if -500000 <= i < -400000:
                    return "video" in active_types
                if -600000 <= i < -500000:
                    return "event" in active_types
                if -700000 <= i < -600000:
                    return "contact" in active_types
                if i < -700000:
                    return "lieu" in active_types
                return False
            all_ids = [i for i in all_ids if _type_match(i)]

        file_ids = [i for i in all_ids if i > 0]
        lieu_ids = [-(i + 700000) for i in all_ids if i < -700000]
        contact_ids = [-(i + 600000) for i in all_ids if -700000 <= i < -600000]
        event_ids = [-(i + 500000) for i in all_ids if -600000 <= i < -500000]
        video_ids = [-(i + 400000) for i in all_ids if -500000 <= i < -400000]
        vault_ids = [-(i + 300000) for i in all_ids if -400000 <= i < -300000]
        note_ids = [-(i + 200000) for i in all_ids if -300000 <= i < -200000]
        email_ids = [-(i + 100000) for i in all_ids if -200000 <= i < -100000]

        total = len(all_ids)

        # Récupérer les fichiers
        results = []
        if file_ids:
            ph = ",".join("?" * len(file_ids))
            # Filtre source_user_id (Phase 5)
            source_condition = ""
            if source_filter == "local":
                source_condition = " AND source_user_id IS NULL"
            elif source_filter == "consulted":
                source_condition = " AND source_user_id IS NOT NULL"
            # source_filter == "all" : pas de condition

            c.execute(f"""
                SELECT id, nom, extension, chemin_relatif, taille, est_dossier, date_modif, source_user_id, is_shared_copy
                FROM items WHERE id IN ({ph}){source_condition}
                ORDER BY date_modif DESC
            """, file_ids)
            for row in c.fetchall():
                ext_lower = (row[2] or "").lower()
                results.append({
                    "id": row[0],
                    "type": "file",
                    "nom": row[1],
                    "extension": row[2] or "",
                    "chemin": row[3] or "",
                    "taille": row[4] or 0,
                    "est_dossier": bool(row[5]),
                    "date_modif": row[6] or "",
                    "source_user_id": row[7] or None,  # Phase 5
                    "is_shared_copy": bool(row[8]) if row[8] is not None else False,  # Phase 6
                    "is_media": ext_lower in IMAGE_EXTENSIONS or ext_lower in VIDEO_EXTENSIONS,
                })

        # Récupérer les emails
        if email_ids:
            ph = ",".join("?" * len(email_ids))
            c.execute(f"""
                SELECT id, subject, from_addr, account, folder, date_sent, size, to_addr, snippet
                FROM emails WHERE id IN ({ph})
                ORDER BY date_sent DESC
            """, email_ids)
            for row in c.fetchall():
                from_raw = row[2] or ""
                to_raw = row[7] or ""
                # Extraire juste l'email (pas le nom long)
                from_email = _extract_email(from_raw)
                to_email = _extract_email(to_raw)
                results.append({
                    "id": -(row[0] + 100000),
                    "type": "email",
                    "nom": row[1] or "(sans sujet)",
                    "extension": "",
                    "chemin": f"{from_email} -> {to_email}",
                    "from": from_email,
                    "account": row[3] or "",
                    "folder": row[4] or "",
                    "taille": row[6] or 0,
                    "est_dossier": False,
                    "date_modif": row[5] or "",
                    "snippet": row[8] or "",
                })

        # Récupérer les notes
        if note_ids:
            ph = ",".join("?" * len(note_ids))
            c.execute(f"""
                SELECT id, title, date_modif, body
                FROM notes WHERE id IN ({ph})
                ORDER BY date_modif DESC
            """, note_ids)
            for row in c.fetchall():
                body_preview = (row[3] or "")[:150].replace('\n', ' ')
                results.append({
                    "id": -(row[0] + 200000),
                    "type": "note",
                    "nom": row[1] or "(sans titre)",
                    "extension": "",
                    "chemin": body_preview,
                    "taille": 0,
                    "est_dossier": False,
                    "date_modif": row[2] or "",
                })

        # Récupérer les entrées vault
        if vault_ids:
            ph = ",".join("?" * len(vault_ids))
            c.execute(f"""
                SELECT id, service, login, project, category, url, notes, date_modified
                FROM vault WHERE id IN ({ph})
                ORDER BY service
            """, vault_ids)
            for row in c.fetchall():
                results.append({
                    "id": -(row[0] + 300000),
                    "type": "vault",
                    "nom": row[1] or "?",
                    "extension": "",
                    "chemin": row[2] or "",
                    "project": row[3] or "",
                    "category": row[4] or "password",
                    "url": row[5] or "",
                    "notes": row[6] or "",
                    "taille": 0,
                    "est_dossier": False,
                    "date_modif": row[7] or "",
                })

        # Récupérer les vidéos
        if video_ids:
            ph = ",".join("?" * len(video_ids))
            c.execute(f"""
                SELECT id, url, platform, title, source_note_id, date_added
                FROM videos WHERE id IN ({ph})
                ORDER BY date_added DESC
            """, video_ids)
            for row in c.fetchall():
                results.append({
                    "id": -(row[0] + 400000),
                    "type": "video",
                    "nom": row[3] or row[1] or "?",
                    "extension": "",
                    "chemin": row[1] or "",
                    "url": row[1] or "",
                    "platform": row[2] or "",
                    "taille": 0,
                    "est_dossier": False,
                    "date_modif": row[5] or "",
                })

        # Récupérer les événements
        if event_ids:
            from events import get_event, _format_date_fr, _parse_dt, RECURRENCE_LABELS
            for eid in event_ids:
                ev = get_event(eid, _conn=conn)
                if ev:
                    dt = _parse_dt(ev["date_start"])
                    results.append({
                        "id": -(eid + 500000),
                        "type": "event",
                        "nom": ev["title"],
                        "extension": "",
                        "chemin": "",
                        "taille": 0,
                        "est_dossier": False,
                        "date_modif": ev["date_start"] or "",
                        "date_fr": _format_date_fr(dt) if dt else "",
                        "recurrence": ev.get("recurrence", "none"),
                        "tags_raw": ev.get("tags_raw", ""),
                        "location": ev.get("location", ""),
                        "description": ev.get("description", ""),
                    })

        # Récupérer les contacts
        if contact_ids:
            from contacts import get_contact
            for cid in contact_ids:
                ct = get_contact(cid, _conn=conn)
                if ct:
                    display = (ct.get("prenom", "") + " " + ct.get("nom", "")).strip()
                    meta_parts = [ct["type"]]
                    tels = ct.get("telephones", [])
                    if tels:
                        meta_parts.append(tels[0])
                    emls = ct.get("emails", [])
                    if emls:
                        meta_parts.append(emls[0])
                    results.append({
                        "id": -(cid + 600000),
                        "type": "contact",
                        "nom": display or "(sans nom)",
                        "extension": "",
                        "chemin": " | ".join(meta_parts),
                        "taille": 0,
                        "est_dossier": False,
                        "date_modif": ct.get("created_at", ""),
                        "contact_type": ct["type"],
                    })

        # Récupérer les lieux
        if lieu_ids:
            from lieux import get_lieu
            for lid in lieu_ids:
                l = get_lieu(lid, _conn=conn)
                if l:
                    results.append({
                        "id": -(lid + 700000),
                        "type": "lieu",
                        "nom": l["nom"],
                        "extension": "",
                        "chemin": l.get("adresse", ""),
                        "taille": 0,
                        "est_dossier": False,
                        "date_modif": l.get("created_at", ""),
                    })

        # ── Projets depuis tasks.db (si filtre type=projet actif ou parmi les types) ──
        if "projet" in active_types or not active_types:
            tconn = get_tasks_db()
            tc = tconn.cursor()
            if include:
                # Chercher projets dont tags_raw contient tous les tags inclus
                proj_query = "SELECT id, title, description, status, tags_raw, created_at, fs_path, category FROM tasks WHERE kind='projet' AND conflict_of_id IS NULL"
                proj_rows = tc.execute(proj_query).fetchall()
                def _proj_matches(row):
                    raw = (row[4] or "").lower()
                    tags = {t.strip() for t in raw.split(",") if t.strip()}
                    return all(t.lower() in tags for t in include)
                proj_rows = [r for r in proj_rows if _proj_matches(r)]
                if exclude:
                    def _proj_not_excluded(row):
                        raw = (row[4] or "").lower()
                        tags = {t.strip() for t in raw.split(",") if t.strip()}
                        return not any(t.lower() in tags for t in exclude)
                    proj_rows = [r for r in proj_rows if _proj_not_excluded(r)]
            else:
                proj_rows = tc.execute(
                    "SELECT id, title, description, status, tags_raw, created_at, fs_path, category FROM tasks WHERE kind='projet' AND conflict_of_id IS NULL"
                ).fetchall()
            tconn.close()
            if "projet" in active_types:
                # Mode filtre Projets : remplacer les résultats par les projets uniquement
                results = []
                total = len(proj_rows)
            for r in proj_rows:
                results.append({
                    "id": r[0],
                    "type": "projet",
                    "nom": r[1],
                    "description": r[2] or "",
                    "status": r[3] or "todo",
                    "tags_raw": r[4] or "",
                    "extension": "",
                    "chemin": r[6] or "",
                    "taille": 0,
                    "est_dossier": True,
                    "date_modif": r[5] or "",
                    "category": r[7] or "",
                })
            if "projet" not in active_types:
                total += len(proj_rows)

        # Trier par date desc et paginer
        results.sort(key=lambda r: r.get("date_modif", ""), reverse=True)
        page = results[offset:offset + limit]

        conn.close()
        return {"results": page, "total": total}

    def _search_projets_only(self, include, exclude, limit, offset):
        """Recherche projets (tasks.db) uniquement — pour le filtre type=projet."""
        conn = get_tasks_db()
        rows = conn.execute(
            "SELECT id, title, description, status, tags_raw, created_at, fs_path, category "
            "FROM tasks WHERE kind='projet' AND conflict_of_id IS NULL"
        ).fetchall()
        def _matches(row):
            raw = (row[4] or "").lower()
            tags = {t.strip() for t in raw.split(",") if t.strip()}
            title_lower = (row[1] or "").lower()
            desc_lower = (row[2] or "").lower()
            if include:
                for t in include:
                    tl = t.lower()
                    if tl not in tags and tl not in title_lower and tl not in desc_lower:
                        return False
            if exclude and any(t.lower() in tags for t in exclude):
                return False
            return True
        rows = [r for r in rows if _matches(r)]
        total = len(rows)
        rows.sort(key=lambda r: r[5] or "", reverse=True)
        page = rows[offset:offset + limit]
        # Compter chantiers et tâches pour chaque projet
        results = []
        for r in page:
            proj_id = r[0]
            nb_chantiers = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE kind='chantier' AND project_id=? AND conflict_of_id IS NULL",
                (proj_id,)
            ).fetchone()[0]
            nb_tasks = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE kind='task' AND project_id=? AND conflict_of_id IS NULL",
                (proj_id,)
            ).fetchone()[0]
            results.append({
                "id": proj_id, "type": "projet", "nom": r[1],
                "description": r[2] or "", "status": r[3] or "todo",
                "tags_raw": r[4] or "", "extension": "",
                "chemin": r[6] or "", "taille": 0, "est_dossier": True,
                "date_modif": r[5] or "", "category": r[7] or "",
                "nb_chantiers": nb_chantiers, "nb_tasks": nb_tasks,
            })
        conn.close()
        return {"results": results, "total": total}

    def handle_cooccurrence(self, params):
        """Tags co-occurrents : les tags les plus fréquents parmi les items qui matchent."""
        include = [t.strip() for t in params.get("include", []) if t.strip()]
        exclude = [t.strip() for t in params.get("exclude", []) if t.strip()]
        types_raw = params.get("types", [""])[0].strip()
        active_types = set(t.strip() for t in types_raw.split(",") if t.strip()) if types_raw else set()

        if not include and not active_types:
            return {"tags": []}

        conn = get_db()
        c = conn.cursor()

        if include:
            # Items qui ont tous les tags inclus (chercher dans tag_display)
            placeholders_inc = ",".join("?" * len(include))
            items_query = f"""
                SELECT t.item_id
                FROM tags t
                WHERE t.tag_display IN ({placeholders_inc})
                GROUP BY t.item_id
                HAVING COUNT(DISTINCT t.tag_display) = ?
            """
            items_params = list(include) + [len(include)]

            # Exclure
            if exclude:
                placeholders_exc = ",".join("?" * len(exclude))
                items_query = f"""
                    SELECT item_id FROM ({items_query})
                    WHERE item_id NOT IN (
                        SELECT item_id FROM tags WHERE tag_display IN ({placeholders_exc})
                    )
                """
                items_params += list(exclude)
        else:
            # Pas de tags → tous les items distincts (sera filtré par type ensuite)
            items_query = "SELECT DISTINCT item_id FROM tags"
            items_params = []

        # Filtrer par type si demandé
        if active_types:
            def _type_match(i):
                if i > 0: return "file" in active_types
                if -200000 <= i < -100000: return "email" in active_types
                if -300000 <= i < -200000: return "note" in active_types
                if -400000 <= i < -300000: return "vault" in active_types
                if -500000 <= i < -400000: return "video" in active_types
                if -600000 <= i < -500000: return "event" in active_types
                if -700000 <= i < -600000: return "contact" in active_types
                if i < -700000: return "lieu" in active_types
                return False
            c.execute(f"SELECT item_id FROM ({items_query})", items_params)
            filtered_ids = [row[0] for row in c.fetchall() if _type_match(row[0])]
            if not filtered_ids:
                conn.close()
                return {"tags": []}
            ph = ",".join("?" * len(filtered_ids))
            items_query = f"SELECT item_id FROM tags WHERE item_id IN ({ph}) GROUP BY item_id"
            items_params = filtered_ids

        # Tags co-occurrents (exclure ceux déjà sélectionnés)
        # Utiliser tag_display pour afficher les formes originales
        all_selected = set(include) | set(exclude)
        if all_selected:
            all_placeholders = ",".join("?" * len(all_selected))
            # Grouper par tag_display
            cooc_query = f"""
                SELECT tag_display, COUNT(*) as cnt
                FROM tags
                WHERE item_id IN ({items_query})
                  AND tag_display NOT IN ({all_placeholders})
                GROUP BY tag_display
                ORDER BY cnt DESC
                LIMIT 15
            """
            c.execute(cooc_query, items_params + list(all_selected))
        else:
            cooc_query = f"""
                SELECT tag_display, COUNT(*) as cnt
                FROM tags
                WHERE item_id IN ({items_query})
                GROUP BY tag_display
                ORDER BY cnt DESC
                LIMIT 15
            """
            c.execute(cooc_query, items_params)
        tags = [{"tag": row[0], "count": row[1]} for row in c.fetchall()]

        conn.close()
        return {"tags": tags}

    def handle_tags_add(self, data):
        """Ajoute un tag à un item.

        POST /api/tags/add
        Body: {"item_id": 123, "tag": "nouveau-tag"}
        """
        item_id = data.get("item_id")
        tag_display = data.get("tag", "").strip()

        if not item_id or not tag_display:
            return {"error": "item_id et tag requis"}

        # Normaliser le tag
        tag_normalized = normalize_tag(tag_display)

        # Vérifier que le tag est valide
        if not is_valid_tag(tag_display):
            return {"error": "Tag invalide (longueur min 3, alphanumérique uniquement)"}

        conn = get_db()
        c = conn.cursor()

        # Vérifier si le tag existe déjà pour cet item
        c.execute("SELECT 1 FROM tags WHERE item_id = ? AND tag = ?", (item_id, tag_normalized))
        if c.fetchone():
            conn.close()
            return {"error": "Tag déjà présent"}

        # Insérer le tag
        c.execute("INSERT INTO tags (item_id, tag, tag_display) VALUES (?, ?, ?)",
                  (item_id, tag_normalized, tag_display))
        conn.commit()
        conn.close()

        return {"success": True, "tag": tag_display, "tag_normalized": tag_normalized}

    def handle_tags_delete(self, data):
        """Supprime un tag d'un item.

        DELETE /api/tags/delete
        Body: {"item_id": 123, "tag": "tag-a-supprimer"}
        """
        item_id = data.get("item_id")
        tag = data.get("tag", "").strip()

        if not item_id or not tag:
            return {"error": "item_id et tag requis"}

        # Normaliser le tag pour trouver la bonne ligne
        tag_normalized = normalize_tag(tag)

        conn = get_db()
        c = conn.cursor()

        # Supprimer l'association (tag peut être normalisé ou display)
        c.execute("DELETE FROM tags WHERE item_id = ? AND (tag = ? OR tag_display = ?)",
                  (item_id, tag_normalized, tag))
        deleted = c.rowcount
        conn.commit()
        conn.close()

        if deleted == 0:
            return {"error": "Association introuvable"}

        return {"success": True, "deleted": deleted}

    def handle_tags_get(self, params):
        """Récupère tous les tags d'un item.

        GET /api/tags/get?item_id=123
        """
        item_id = params.get("item_id", [""])[0]
        if not item_id:
            return {"error": "item_id requis"}

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT tag_display FROM tags WHERE item_id = ? ORDER BY tag_display", (item_id,))
        tags = [row[0] for row in c.fetchall()]
        conn.close()

        return {"tags": tags}

    def handle_open(self, params):
        """Ouvre un fichier avec l'application par défaut du Mac."""
        item_id = params.get("id", [""])[0]
        if not item_id:
            return {"error": "id manquant"}

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT chemin_relatif FROM items WHERE id = ?", (item_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return {"error": "item introuvable"}

        full_path = Path(DROPBOX_ROOT) / row[0]
        if not full_path.exists():
            return {"error": "fichier introuvable sur le disque"}

        subprocess.Popen(["open", str(full_path)])
        return {"ok": True, "path": str(full_path)}

    def handle_reveal(self, params):
        """Montre le fichier dans le Finder."""
        item_id = params.get("id", [""])[0]
        if not item_id:
            return {"error": "id manquant"}

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT chemin_relatif FROM items WHERE id = ?", (item_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return {"error": "item introuvable"}

        full_path = Path(DROPBOX_ROOT) / row[0]
        if not full_path.exists():
            return {"error": "fichier introuvable sur le disque"}

        subprocess.Popen(["open", "-R", str(full_path)])
        return {"ok": True, "path": str(full_path)}

    def delete_email_from_imap(self, account_email, folder, uid):
        """Supprime un email sur le serveur IMAP."""
        try:
            # Charger les credentials
            with open(ACCOUNTS_PATH) as f:
                accounts = json.load(f)

            account = None
            for a in accounts:
                if a["email"] == account_email:
                    account = a
                    break

            if not account:
                return {"success": False, "error": f"Compte {account_email} non configuré"}

            # Connexion IMAP
            imap = imaplib.IMAP4_SSL(account["imap_server"], account.get("imap_port", 993))
            imap.login(account["email"], account["password"])

            # Sélectionner le dossier en mode écriture
            status, _ = imap.select(f'"{folder}"', readonly=False)
            if status != "OK":
                imap.logout()
                return {"success": False, "error": f"Impossible de sélectionner le dossier {folder}"}

            # Marquer l'email comme supprimé
            status, _ = imap.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
            if status != "OK":
                imap.logout()
                return {"success": False, "error": "Impossible de marquer l'email comme supprimé"}

            # Expunge pour supprimer définitivement
            imap.expunge()
            imap.logout()

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def handle_email_delete(self, data):
        """Supprime un email (serveur IMAP + base locale + tags).

        DELETE /api/email
        Body: {"item_id": -100123, "mode": "db_only" | "permanent"}
        """
        item_id = data.get("item_id")
        mode = data.get("mode", "permanent")
        if not item_id:
            return {"error": "item_id requis"}

        # Convention : item_id = -(email_db_id + 100000)
        email_db_id = -(item_id + 100000)

        conn = get_db()
        c = conn.cursor()

        # Récupérer les infos de l'email
        c.execute("SELECT account, folder, uid, subject FROM emails WHERE id = ?", (email_db_id,))
        row = c.fetchone()

        if not row:
            conn.close()
            return {"error": "Email introuvable en base"}

        account_email, folder, uid, subject = row

        # 1. Supprimer sur le serveur IMAP (si mode permanent)
        if mode == "permanent":
            result = self.delete_email_from_imap(account_email, folder, uid)
            if not result["success"]:
                conn.close()
                return {"error": f"Échec suppression IMAP : {result['error']}"}

        # 2. Supprimer les tags
        c.execute("DELETE FROM tags WHERE item_id = ?", (item_id,))

        # 3. Supprimer de la base
        c.execute("DELETE FROM emails WHERE id = ?", (email_db_id,))

        conn.commit()
        conn.close()

        return {"success": True, "message": f"Email '{subject}' supprimé"}

    def handle_note_delete(self, data):
        """Supprime une note (base + tags uniquement)."""
        item_id = data.get("item_id")
        if not item_id:
            return {"error": "item_id requis"}

        note_db_id = -(item_id + ID_OFFSET_NOTE)
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT title FROM notes WHERE id = ?", (note_db_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return {"error": "Note introuvable"}

        c.execute("DELETE FROM tags WHERE item_id = ?", (item_id,))
        c.execute("DELETE FROM notes WHERE id = ?", (note_db_id,))
        conn.commit()
        conn.close()
        return {"success": True}

    def handle_vault_delete(self, data):
        """Supprime une entrée vault (base + tags uniquement)."""
        item_id = data.get("item_id")
        if not item_id:
            return {"error": "item_id requis"}

        vault_db_id = -(item_id + ID_OFFSET_VAULT)
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM tags WHERE item_id = ?", (item_id,))
        c.execute("DELETE FROM vault WHERE id = ?", (vault_db_id,))
        conn.commit()
        conn.close()
        return {"success": True}

    def handle_video_delete(self, data):
        """Supprime une vidéo (base + tags uniquement)."""
        item_id = data.get("item_id")
        if not item_id:
            return {"error": "item_id requis"}

        video_db_id = -(item_id + ID_OFFSET_VIDEO)
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM tags WHERE item_id = ?", (item_id,))
        c.execute("DELETE FROM videos WHERE id = ?", (video_db_id,))
        conn.commit()
        conn.close()
        return {"success": True}

    def handle_file_delete(self, data):
        """Supprime un fichier (mode: db_only ou permanent=corbeille)."""
        item_id = data.get("item_id")
        mode = data.get("mode", "permanent")
        if not item_id or item_id < 0:
            return {"error": "item_id fichier requis"}

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT chemin FROM items WHERE id = ?", (item_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return {"error": "Fichier introuvable"}

        file_path = Path(DROPBOX_ROOT) / row[0]

        # Mode permanent : mettre à la corbeille
        if mode == "permanent" and file_path.exists():
            try:
                import subprocess
                subprocess.run(["osascript", "-e", f'tell application "Finder" to delete POSIX file "{file_path}"'], check=True)
            except Exception as e:
                conn.close()
                return {"error": f"Échec mise à la corbeille : {str(e)}"}

        # Supprimer de la base
        c.execute("DELETE FROM tags WHERE item_id = ?", (item_id,))
        c.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return {"success": True}

    def handle_email(self, params):
        """Récupère le contenu complet d'un email via IMAP."""
        raw_id = params.get("id", [""])[0]
        if not raw_id:
            return {"error": "id manquant"}

        tag_id = int(raw_id)
        # Convention : tag_id = -(email_db_id + 100000)
        email_db_id = -(tag_id + 100000)

        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT account, folder, uid, subject, from_addr, to_addr, date_sent
                      FROM emails WHERE id = ?""", (email_db_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return {"error": "email introuvable en base"}

        account_email = row["account"]
        folder = row["folder"]
        uid = row["uid"]

        # Charger les comptes
        with open(ACCOUNTS_PATH) as f:
            accounts = json.load(f)

        account = None
        for a in accounts:
            if a["email"] == account_email:
                account = a
                break

        if not account:
            return {"error": f"compte {account_email} non configuré"}

        # Connexion IMAP pour récupérer le body complet
        try:
            imap = imaplib.IMAP4_SSL(account["imap_server"], account.get("imap_port", 993))
            imap.login(account["email"], account["password"])
            status, _ = imap.select(f'"{folder}"', readonly=True)
            if status != "OK":
                imap.logout()
                return {"error": f"dossier {folder} inaccessible"}

            uid_bytes = uid.encode() if isinstance(uid, str) else uid
            status, msg_data = imap.uid('fetch', uid_bytes, '(RFC822)')
            imap.logout()

            if status != "OK" or not msg_data or not msg_data[0]:
                return {"error": "email introuvable sur le serveur"}

            raw_bytes = None
            for part in msg_data:
                if isinstance(part, tuple):
                    raw_bytes = part[1]
                    break

            if not raw_bytes:
                return {"error": "contenu vide"}

            msg = email.message_from_bytes(raw_bytes)

            body_html = ""
            body_text = ""

            if msg.is_multipart():
                for part in msg.walk():
                    ct = part.get_content_type()
                    cd = str(part.get("Content-Disposition", ""))
                    if "attachment" in cd:
                        continue
                    if ct == "text/html" and not body_html:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body_html = payload.decode(charset, errors="ignore")
                    elif ct == "text/plain" and not body_text:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body_text = payload.decode(charset, errors="ignore")
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    decoded = payload.decode(charset, errors="ignore")
                    if msg.get_content_type() == "text/html":
                        body_html = decoded
                    else:
                        body_text = decoded

            subject = _decode_header(msg.get("Subject", ""))
            from_addr = _decode_header(msg.get("From", ""))
            to_addr = _decode_header(msg.get("To", ""))

            return {
                "subject": subject,
                "from": _extract_email(from_addr),
                "from_full": from_addr,
                "to": _extract_email(to_addr),
                "to_full": to_addr,
                "date": row["date_sent"] or "",
                "body_html": body_html,
                "body_text": body_text,
            }

        except Exception as e:
            return {"error": str(e)}

    # ── Event endpoints ─────────────────────────────────

    def handle_event_get(self, params):
        """GET /api/event?id= — Détail d'un événement."""
        raw_id = params.get("id", [""])[0]
        if not raw_id:
            return {"error": "id manquant"}
        from events import get_event, _parse_dt, _format_date_fr
        tag_id = int(raw_id)
        event_id = -(tag_id + 500000)
        ev = get_event(event_id)
        if not ev:
            return {"error": "événement introuvable"}
        dt = _parse_dt(ev["date_start"])
        ev["date_fr"] = _format_date_fr(dt) if dt else ""
        return ev

    def handle_events_upcoming(self, params):
        """GET /api/events/upcoming?mode=day — Vue temporelle."""
        mode = params.get("mode", ["day"])[0]
        from events import get_upcoming
        return get_upcoming(mode=mode)

    def handle_event_post(self, data):
        """POST /api/event — Créer un événement."""
        title = data.get("title", "").strip()
        date_start = data.get("date_start", "").strip()
        if not title or not date_start:
            return {"error": "titre et date_start requis"}
        from events import add_event
        ev = add_event(
            title=title,
            date_start=date_start,
            date_end=data.get("date_end"),
            description=data.get("description", ""),
            location=data.get("location", ""),
            tags_raw=data.get("tags_raw", ""),
            recurrence=data.get("recurrence", "none"),
            recurrence_interval=data.get("recurrence_interval", 1),
            recurrence_count=data.get("recurrence_count"),
            recurrence_end=data.get("recurrence_end"),
            subtype=data.get("subtype", "generic"),
            contact_id=data.get("contact_id"),
            lieu_id=data.get("lieu_id"),
        )
        return {"ok": True, "event": ev}

    def handle_event_put(self, data):
        """PUT /api/event — Modifier un événement."""
        event_id = data.get("id")
        if not event_id:
            return {"error": "id requis"}
        from events import update_event
        kwargs = {k: v for k, v in data.items() if k != "id"}
        ev = update_event(event_id, **kwargs)
        if not ev:
            return {"error": "événement introuvable"}
        return {"ok": True, "event": ev}

    def handle_event_delete(self, data):
        """DELETE /api/event — Supprimer un événement."""
        event_id = data.get("id")
        if not event_id:
            return {"error": "id requis"}
        from events import delete_event
        ok = delete_event(event_id)
        return {"ok": ok}

    # ── Contact endpoints ──────────────────────────────

    def handle_contact_get(self, params):
        """GET /api/contact?id= — Détail d'un contact."""
        raw_id = params.get("id", [""])[0]
        if not raw_id:
            return {"error": "id manquant"}
        from contacts import get_contact
        contact_id = -(int(raw_id) + 600000)
        c = get_contact(contact_id)
        if not c:
            return {"error": "contact introuvable"}
        return c

    def handle_contacts_search(self, params):
        """GET /api/contacts/search?q= — Recherche contacts (autocomplete)."""
        q = params.get("q", [""])[0]
        if not q:
            return {"results": []}
        from contacts import search_contacts
        results = search_contacts(q)
        return {"results": results}

    def handle_system_contacts_list(self, params):
        """GET /api/system-contacts/list — Suggestions contacts du système (lecture seule)."""
        q = params.get("q", [""])[0]
        try:
            from import_system_contacts import search_system_contacts, is_available
            if not is_available():
                return {"available": False, "contacts": [], "total": 0}
            contacts = search_system_contacts(q, limit=30)
            return {"available": True, "contacts": contacts, "total": len(contacts)}
        except ImportError:
            return {"available": False, "contacts": [], "total": 0}
        except Exception as e:
            return {"available": False, "contacts": [], "total": 0, "error": str(e)}

    def handle_contact_post(self, data):
        """POST /api/contact — Créer un contact."""
        from contacts import add_contact
        try:
            c = add_contact(
                type=data.get("type", "personne"),
                nom=data.get("nom", ""),
                prenom=data.get("prenom", ""),
                telephones=data.get("telephones", []),
                emails=data.get("emails", []),
                date_naissance=data.get("date_naissance"),
                heure_naissance=data.get("heure_naissance"),
                lieu_naissance=data.get("lieu_naissance"),
                adresse=data.get("adresse", ""),
                site_web=data.get("site_web", ""),
                commentaire=data.get("commentaire", ""),
                photo_path=data.get("photo_path", ""),
                entreprise_id=data.get("entreprise_id"),
                tags_raw=data.get("tags_raw", ""),
            )
            return {"ok": True, "contact": c}
        except ValueError as e:
            return {"error": str(e)}

    def handle_contact_put(self, data):
        """PUT /api/contact — Modifier un contact."""
        contact_id = data.get("id")
        if not contact_id:
            return {"error": "id requis"}
        from contacts import update_contact
        kwargs = {k: v for k, v in data.items() if k != "id"}
        c = update_contact(contact_id, **kwargs)
        if not c:
            return {"error": "contact introuvable"}
        return {"ok": True, "contact": c}

    def handle_contact_delete(self, data):
        """DELETE /api/contact — Supprimer un contact."""
        contact_id = data.get("id")
        if not contact_id:
            return {"error": "id requis"}
        from contacts import delete_contact
        from relations import delete_relations_for
        delete_relations_for("contact", contact_id)
        ok = delete_contact(contact_id)
        return {"ok": ok}

    # ── Lieu endpoints ────────────────────────────────

    def handle_lieu_get(self, params):
        """GET /api/lieu?id= — Détail d'un lieu."""
        raw_id = params.get("id", [""])[0]
        if not raw_id:
            return {"error": "id manquant"}
        from lieux import get_lieu, maps_url
        lieu_id = -(int(raw_id) + 700000)
        l = get_lieu(lieu_id)
        if not l:
            return {"error": "lieu introuvable"}
        if l.get("adresse"):
            l["maps_url"] = maps_url(l["adresse"])
        return l

    def handle_lieux_search(self, params):
        """GET /api/lieux/search?q= — Recherche lieux (autocomplete)."""
        q = params.get("q", [""])[0]
        if not q:
            return {"results": []}
        from lieux import search_lieux
        results = search_lieux(q)
        return {"results": results}

    def handle_lieu_post(self, data):
        """POST /api/lieu — Créer un lieu."""
        from lieux import add_lieu
        try:
            l = add_lieu(
                nom=data.get("nom", ""),
                adresse=data.get("adresse", ""),
                description=data.get("description", ""),
                contact_id=data.get("contact_id"),
                tags_raw=data.get("tags_raw", ""),
            )
            return {"ok": True, "lieu": l}
        except ValueError as e:
            return {"error": str(e)}

    def handle_lieu_put(self, data):
        """PUT /api/lieu — Modifier un lieu."""
        lieu_id = data.get("id")
        if not lieu_id:
            return {"error": "id requis"}
        from lieux import update_lieu
        kwargs = {k: v for k, v in data.items() if k != "id"}
        l = update_lieu(lieu_id, **kwargs)
        if not l:
            return {"error": "lieu introuvable"}
        return {"ok": True, "lieu": l}

    def handle_lieu_delete(self, data):
        """DELETE /api/lieu — Supprimer un lieu."""
        lieu_id = data.get("id")
        if not lieu_id:
            return {"error": "id requis"}
        from lieux import delete_lieu
        from relations import delete_relations_for
        delete_relations_for("lieu", lieu_id)
        ok = delete_lieu(lieu_id)
        return {"ok": ok}

    # ── Relation endpoints ────────────────────────────

    def handle_relations_get(self, params):
        """GET /api/relations?type=&id= — Relations d'un élément."""
        elem_type = params.get("type", [""])[0]
        raw_id = params.get("id", [""])[0]
        if not elem_type or not raw_id:
            return {"error": "type et id requis"}
        from relations import get_relations
        return {"relations": get_relations(elem_type, int(raw_id))}

    def handle_relation_post(self, data):
        """POST /api/relation — Créer un lien."""
        from relations import add_relation
        try:
            rel = add_relation(
                source_type=data.get("source_type", ""),
                source_id=data.get("source_id"),
                target_type=data.get("target_type", ""),
                target_id=data.get("target_id"),
                relation=data.get("relation", ""),
            )
            if rel:
                return {"ok": True, "relation": rel}
            return {"error": "relation déjà existante"}
        except ValueError as e:
            return {"error": str(e)}

    def handle_relation_delete(self, data):
        """DELETE /api/relation — Supprimer un lien."""
        rel_id = data.get("id")
        if not rel_id:
            return {"error": "id requis"}
        from relations import delete_relation
        ok = delete_relation(rel_id)
        return {"ok": ok}

    # ── Validation endpoints ───────────────────────────

    def handle_validation_submit(self, data):
        """POST /api/validation/submit — Reçoit validation formulaire HTML.

        Body: {"type": "brief|cdc|specs|build", "project": "NOM", "responses": {...}}
        Écrit dans /tmp/claude_validation_<project>.json pour que Claude puisse lire.
        """
        validation_type = data.get("type", "unknown")
        project = data.get("project", "unknown")
        responses = data.get("responses", {})

        validation_file = f"/tmp/claude_validation_{project}.json"
        validation_data = {
            "type": validation_type,
            "project": project,
            "responses": responses,
            "timestamp": subprocess.run(
                ["date", "+%Y-%m-%d %H:%M:%S"],
                capture_output=True,
                text=True
            ).stdout.strip()
        }

        try:
            with open(validation_file, "w", encoding="utf-8") as f:
                json.dump(validation_data, f, indent=2, ensure_ascii=False)
            return {"success": True, "message": "Validation enregistrée ✓"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Vault endpoints ────────────────────────────────

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Lire le body JSON
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._json_response(400, {"error": "JSON invalide"})
            return

        post_routes = {
            "/api/vault/unlock": self.handle_vault_unlock,
            "/api/vault/add": self.handle_vault_add,
            "/api/favorite": self.handle_favorite_toggle,
            "/api/event": self.handle_event_post,
            "/api/video/add": self.handle_video_add,
            "/api/image/save": self.handle_image_save,
            "/api/contact": self.handle_contact_post,
            "/api/lieu": self.handle_lieu_post,
            "/api/relation": self.handle_relation_post,
            "/api/tags/add": self.handle_tags_add,
            "/api/identity/init": self.handle_identity_init_post,
            "/api/identity/sign": self.handle_identity_sign_post,
            "/api/identity/verify": self.handle_identity_verify_post,
            "/api/identity/protect": self.handle_identity_protect_post,
            "/api/identity/unlock": self.handle_identity_unlock_post,
            "/api/share/accept": self.handle_share_accept,  # Phase 4 P2P
            "/api/qr/generate": self.handle_qr_generate,  # Phase 6 P2P
            "/api/validation/submit": self.handle_validation_submit,  # Validations formulaires
            # ── Tasks ─────────────────────────────────────────────────────────
            "/api/tasks": self.handle_tasks_post,
            "/api/tasks/schedule": self.handle_tasks_schedule,
            "/api/tasks/done": self.handle_tasks_done,
            "/api/tasks/undone": self.handle_tasks_undone,
            "/api/tasks/attachments": self.handle_tasks_attachment_add,
            "/api/tasks/conflicts/resolve": self.handle_tasks_conflict_resolve,
            "/api/tasks/steps_rewrite": self.handle_tasks_steps_rewrite,
        }

        handler = post_routes.get(path)
        if handler:
            try:
                result = handler(data)
                self._json_response(200, result)
            except Exception as e:
                self._json_response(500, {"error": str(e)})
        else:
            self._json_response(404, {"error": "Route inconnue"})

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._json_response(400, {"error": "JSON invalide"})
            return
        put_routes = {
            "/api/event": self.handle_event_put,
            "/api/contact": self.handle_contact_put,
            "/api/lieu": self.handle_lieu_put,
            "/api/tasks": self.handle_tasks_put,
        }
        handler = put_routes.get(path)
        if handler:
            try:
                result = handler(data)
                self._json_response(200, result)
            except Exception as e:
                self._json_response(500, {"error": str(e)})
        else:
            self._json_response(404, {"error": "Route inconnue"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._json_response(400, {"error": "JSON invalide"})
            return
        delete_routes = {
            "/api/email": self.handle_email_delete,
            "/api/note": self.handle_note_delete,
            "/api/vault": self.handle_vault_delete,
            "/api/video": self.handle_video_delete,
            "/api/file": self.handle_file_delete,
            "/api/event": self.handle_event_delete,
            "/api/contact": self.handle_contact_delete,
            "/api/lieu": self.handle_lieu_delete,
            "/api/relation": self.handle_relation_delete,
            "/api/tags/delete": self.handle_tags_delete,
            "/api/tasks": self.handle_tasks_delete,
            "/api/tasks/attachments": self.handle_tasks_attachment_delete,
        }
        handler = delete_routes.get(path)
        if handler:
            try:
                result = handler(data)
                self._json_response(200, result)
            except Exception as e:
                self._json_response(500, {"error": str(e)})
        else:
            self._json_response(404, {"error": "Route inconnue"})

    def handle_vault_status(self, params):
        """Retourne si le coffre est déverrouillé."""
        global _vault_master
        return {"unlocked": _vault_master is not None}

    def handle_vault_unlock(self, data):
        """Déverrouille le coffre avec le mot de passe maître."""
        global _vault_master
        master = data.get("master", "")
        if not master:
            return {"error": "mot de passe manquant"}

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT value FROM vault_config WHERE key = 'master_hash'")
        hash_row = c.fetchone()
        c.execute("SELECT value FROM vault_config WHERE key = 'master_salt'")
        salt_row = c.fetchone()
        conn.close()

        if not hash_row or not salt_row:
            return {"error": "coffre non initialisé"}

        salt = bytes.fromhex(salt_row["value"])
        _, h = _vault_hash_master(master, salt)
        if h.hex() != hash_row["value"]:
            return {"error": "mot de passe incorrect"}

        _vault_master = master
        return {"ok": True}

    def handle_vault_lock(self, params):
        """Verrouille le coffre."""
        global _vault_master
        _vault_master = None
        return {"ok": True}

    def handle_vault_get(self, params):
        """Retourne une entrée du coffre (mot de passe déchiffré si déverrouillé)."""
        global _vault_master
        raw_id = params.get("id", [""])[0]
        if not raw_id:
            return {"error": "id manquant"}

        tag_id = int(raw_id)
        vault_id = -(tag_id + 300000)

        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT id, service, login, password_enc, project, category, url, notes
                      FROM vault WHERE id = ?""", (vault_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return {"error": "entrée introuvable"}

        result = {
            "id": tag_id,
            "service": row["service"],
            "login": row["login"],
            "project": row["project"] or "",
            "category": row["category"] or "",
            "url": row["url"] or "",
            "notes": row["notes"] or "",
        }

        # Déchiffrer le mot de passe si déverrouillé
        if _vault_master and row["password_enc"]:
            decrypted = _vault_decrypt(row["password_enc"], _vault_master)
            result["password"] = decrypted if decrypted else "(erreur déchiffrement)"
        else:
            result["password"] = None  # verrouillé

        return result

    def handle_vault_copy(self, params):
        """Copie le mot de passe dans le presse-papiers."""
        global _vault_master
        if not _vault_master:
            return {"error": "coffre verrouillé"}

        raw_id = params.get("id", [""])[0]
        if not raw_id:
            return {"error": "id manquant"}

        tag_id = int(raw_id)
        vault_id = -(tag_id + 300000)

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT password_enc FROM vault WHERE id = ?", (vault_id,))
        row = c.fetchone()
        conn.close()

        if not row or not row["password_enc"]:
            return {"error": "pas de mot de passe"}

        decrypted = _vault_decrypt(row["password_enc"], _vault_master)
        if not decrypted:
            return {"error": "erreur déchiffrement"}

        # Copier dans le presse-papiers (macOS)
        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        proc.communicate(decrypted.encode())
        return {"ok": True, "copied": True}

    def handle_vault_add(self, data):
        """Ajoute une entrée au coffre."""
        global _vault_master
        if not _vault_master:
            return {"error": "coffre verrouillé"}

        service = data.get("service", "").strip()
        login = data.get("login", "").strip()
        password = data.get("password", "").strip()
        project = data.get("project", "").strip()
        category = data.get("category", "password").strip()
        url = data.get("url", "").strip()
        notes = data.get("notes", "").strip()

        if not service:
            return {"error": "service requis"}

        pwd_enc = _vault_encrypt(password, _vault_master) if password else ""
        now = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO vault (service, login, password_enc, project, category, url, notes,
                               date_added, date_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (service, login, pwd_enc, project, category, url, notes, now, now))

        vault_id = c.lastrowid
        tag_id = -(vault_id + 300000)

        # Tags
        tags = {"pwd", "coffre"}
        for word in re.split(r'[\s\-_.,;:!?()\[\]{}"/\'@]+', service):
            w = word.lower().strip()
            if len(w) >= 3 and w.isalpha():
                tags.add(w)
        if project:
            for word in re.split(r'[\s\-_.,;:!?()\[\]{}"/\'@]+', project):
                w = word.lower().strip()
                if len(w) >= 3 and w.isalpha():
                    tags.add(w)
        if category and len(category) >= 3:
            tags.add(category)

        for tag in tags:
            c.execute("INSERT INTO tags (item_id, tag) VALUES (?, ?)", (tag_id, tag))

        conn.commit()
        conn.close()
        return {"ok": True, "id": tag_id}

    # ── Video/Image add endpoints ─────────────────────

    def handle_video_add(self, data):
        """POST /api/video/add — Ajouter une vidéo depuis le menu contextuel."""
        url = data.get("url", "").strip()
        if not url:
            return {"error": "url requise"}

        platform = data.get("platform", "").strip()
        title = data.get("title", "").strip()
        user_tags = [t.strip().lower() for t in data.get("tags", []) if t.strip()]

        # Détection plateforme si non fournie
        if not platform:
            from index_notes import VIDEO_PATTERNS
            for pat, plat in VIDEO_PATTERNS:
                if re.search(pat, url, re.IGNORECASE):
                    platform = plat
                    break

        # Titre YouTube via oEmbed si pas fourni
        if not title and platform == "youtube":
            try:
                import urllib.request
                oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url, safe='')}&format=json"
                req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    oembed = json.loads(resp.read().decode("utf-8"))
                    title = oembed.get("title", "")
            except Exception:
                pass

        conn = get_db()
        c = conn.cursor()

        # Vérifier si URL déjà en base
        c.execute("SELECT id FROM videos WHERE url = ?", (url,))
        existing = c.fetchone()

        if existing:
            video_id = existing[0]
            tag_id = -(video_id + 400000)
            # Ajouter les nouveaux tags manquants
            c.execute("SELECT tag FROM tags WHERE item_id = ?", (tag_id,))
            existing_tags = {row[0] for row in c.fetchall()}
            new_tags = set()
            for t in user_tags:
                if t and t not in existing_tags:
                    new_tags.add(t)
            for tag in new_tags:
                c.execute("INSERT INTO tags (item_id, tag) VALUES (?, ?)", (tag_id, tag))
            conn.commit()
            conn.close()
            return {"ok": True, "already_exists": True, "id": tag_id, "tags_added": len(new_tags)}

        # INSERT nouvelle vidéo
        now = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
        c.execute("""
            INSERT INTO videos (url, platform, title, date_added)
            VALUES (?, ?, ?, ?)
        """, (url, platform or "unknown", title or url, now))
        video_id = c.lastrowid
        tag_id = -(video_id + 400000)

        # Tags : video + plateforme + mots du titre + tags utilisateur
        tags = {"video"}
        if platform:
            tags.add(platform)
        if title:
            for w in re.split(r'[\s\-_.,;:!?()\[\]{}"\'/\\@#&+=<>|~`]+', title.lower()):
                if len(w) >= 3 and w.isalpha() and w not in {"the", "and", "for", "les", "des", "une"}:
                    tags.add(w)
        for t in user_tags:
            if t:
                tags.add(t)

        for tag in tags:
            c.execute("INSERT INTO tags (item_id, tag) VALUES (?, ?)", (tag_id, tag))

        conn.commit()
        conn.close()
        return {"ok": True, "id": tag_id, "title": title, "platform": platform}

    def handle_image_save(self, data):
        """POST /api/image/save — Sauvegarder et tagger une image."""
        image_data = data.get("image_data", "")  # base64
        source_url = data.get("source_url", "").strip()
        filename = data.get("filename", "").strip()
        user_tags = [t.strip().lower() for t in data.get("tags", []) if t.strip()]

        if not image_data:
            return {"error": "image_data requise (base64)"}

        # Décoder le base64
        # Supprimer le préfixe data:image/...;base64, si présent
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        try:
            raw = base64.b64decode(image_data)
        except Exception:
            return {"error": "base64 invalide"}

        # Déterminer l'extension
        ext = ".jpg"
        if filename:
            p = Path(filename)
            if p.suffix.lower() in IMAGE_EXTENSIONS:
                ext = p.suffix.lower()
        elif raw[:4] == b'\x89PNG':
            ext = ".png"
        elif raw[:3] == b'GIF':
            ext = ".gif"
        elif raw[:4] == b'RIFF' and raw[8:12] == b'WEBP':
            ext = ".webp"

        # Nommer : SHA256[:16] + extension
        h = hashlib.sha256(raw).hexdigest()[:16]
        save_name = h + ext
        save_path = SAVED_IMAGES_DIR / save_name

        # Vérifier si déjà sauvegardée
        if save_path.exists():
            # Retrouver l'item existant
            conn = get_db()
            c = conn.cursor()
            rel_path = str(save_path.relative_to(Path(DROPBOX_ROOT)))
            c.execute("SELECT id FROM items WHERE chemin_relatif = ?", (rel_path,))
            row = c.fetchone()
            if row:
                item_id = row[0]
                # Ajouter les nouveaux tags
                c.execute("SELECT tag FROM tags WHERE item_id = ?", (item_id,))
                existing_tags = {r[0] for r in c.fetchall()}
                added = 0
                for t in user_tags:
                    if t and t not in existing_tags:
                        c.execute("INSERT INTO tags (item_id, tag) VALUES (?, ?)", (item_id, t))
                        added += 1
                conn.commit()
                conn.close()
                return {"ok": True, "already_exists": True, "id": item_id, "path": str(save_path), "tags_added": added}
            conn.close()

        # Sauvegarder l'image
        with open(save_path, "wb") as f:
            f.write(raw)

        # Insérer dans items
        rel_path = str(save_path.relative_to(Path(DROPBOX_ROOT)))
        now = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO items (nom, extension, chemin_relatif, taille, est_dossier, date_modif)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (save_name, ext, rel_path, len(raw), now))
        item_id = c.lastrowid

        # Tags : image + domaine source + tags utilisateur
        tags = {"image"}
        if source_url:
            try:
                domain = urllib.parse.urlparse(source_url).hostname or ""
                # Extraire le nom de domaine principal
                parts = domain.split(".")
                for p in parts:
                    if len(p) >= 3 and p not in {"www", "com", "org", "net", "fr"}:
                        tags.add(p)
            except Exception:
                pass
        for t in user_tags:
            if t:
                tags.add(t)

        for tag in tags:
            c.execute("INSERT INTO tags (item_id, tag) VALUES (?, ?)", (item_id, tag))

        conn.commit()
        conn.close()
        return {"ok": True, "id": item_id, "path": str(save_path)}

    # ── Favoris endpoints ──────────────────────────────

    def handle_favorite_toggle(self, data):
        """Toggle le tag 'favori' sur un item."""
        item_id = data.get("id")
        if item_id is None:
            return {"error": "id manquant"}
        item_id = int(item_id)

        tag_normalized = normalize_tag("favori")  # "favor"

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM tags WHERE item_id = ? AND tag = ?", (item_id, tag_normalized))
        exists = c.fetchone()[0] > 0
        if exists:
            c.execute("DELETE FROM tags WHERE item_id = ? AND tag = ?", (item_id, tag_normalized))
        else:
            c.execute("INSERT INTO tags (item_id, tag, tag_display) VALUES (?, ?, 'favori')", (item_id, tag_normalized))
        conn.commit()
        conn.close()
        return {"ok": True, "favorited": not exists}

    def handle_favorite_check(self, params):
        """Vérifie quels IDs sont favoris."""
        ids_raw = params.get("ids", [""])[0]
        if not ids_raw:
            return {"favorited": []}
        try:
            ids = [int(x.strip()) for x in ids_raw.split(",") if x.strip()]
        except ValueError:
            return {"favorited": []}
        if not ids:
            return {"favorited": []}

        tag_normalized = normalize_tag("favori")  # "favor"

        conn = get_db()
        c = conn.cursor()
        ph = ",".join("?" * len(ids))
        c.execute(f"SELECT DISTINCT item_id FROM tags WHERE item_id IN ({ph}) AND tag = ?", ids + [tag_normalized])
        fav_ids = [row[0] for row in c.fetchall()]
        conn.close()
        return {"favorited": fav_ids}

    def handle_stats(self, params):
        """Statistiques générales."""
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM items")
        total_items = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tags")
        total_tags = c.fetchone()[0]
        c.execute("SELECT COUNT(DISTINCT tag) FROM tags")
        unique_tags = c.fetchone()[0]
        conn.close()
        return {
            "total_items": total_items,
            "total_tags": total_tags,
            "unique_tags": unique_tags,
        }

    def handle_i18n(self, params):
        """GET /api/i18n — Retourne les traductions i18n."""
        return I18N_DATA

    def handle_share_notifications(self, params):
        """GET /api/share/notifications?since=timestamp — Retourne les notifications d'acceptation."""
        since = params.get("since", [""])[0]
        notif_file = "/tmp/bigboff_share_notifications.json"

        try:
            if not os.path.exists(notif_file):
                return {"notifications": []}

            with open(notif_file, "r") as f:
                notifications = json.load(f)

            # Filtrer par timestamp si fourni
            if since:
                notifications = [n for n in notifications if n.get("timestamp", "") > since]

            return {"notifications": notifications}
        except Exception as e:
            return {"error": str(e), "notifications": []}

    def handle_note(self, params):
        """Retourne le contenu complet d'une note Apple."""
        tag_id = int(params.get("id", ["0"])[0])
        note_id = -(tag_id + 200000)
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT title, body, date_modif FROM notes WHERE id = ?", (note_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {"error": "Note introuvable"}
        return {
            "title": row["title"] or "",
            "body": row["body"] or "",
            "date": row["date_modif"] or "",
        }

    def handle_thumbnail(self, params):
        """Retourne la miniature d'un fichier image/vidéo en base64."""
        item_id = params.get("id", [""])[0]
        size_param = params.get("size", ["48"])[0]
        if not item_id:
            return {"error": "id manquant"}
        size = (80, 80) if size_param == "80" else (48, 48)

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT chemin_relatif, extension FROM items WHERE id = ?", (item_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return {"error": "item introuvable"}

        ext = (row["extension"] or "").lower()
        if ext not in IMAGE_EXTENSIONS and ext not in VIDEO_EXTENSIONS:
            return {"error": "pas un media"}

        cache_name = f"{size[0]}_{item_id}.jpg"
        cache_path = THUMBNAIL_DIR / cache_name
        if not cache_path.exists():
            full_path = Path(DROPBOX_ROOT) / row["chemin_relatif"]
            if not full_path.exists():
                return {"error": "fichier introuvable"}
            if ext in IMAGE_EXTENSIONS:
                ok = _generate_image_thumbnail(full_path, cache_path, size)
            else:
                ok = _generate_video_thumbnail(full_path, cache_path, size)
            if not ok:
                return {"error": "generation echouee"}

        with open(cache_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("ascii")
        return {"data": f"data:image/jpeg;base64,{b64}"}

    def _serve_fullpage(self):
        """Sert la page de recherche plein écran."""
        html = FULLPAGE_HTML
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _serve_accept_page(self, params):
        """Sert la page de prévisualisation d'un partage P2P (avec i18n)."""
        import base64
        import datetime

        lang = params.get("lang", ["fr"])[0]  # TODO: détecter depuis Accept-Language
        token = params.get("token", [""])[0]

        if not token:
            error_msg = t("share.accept_page.error_missing_token", lang=lang)
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h1>{error_msg}</h1>".encode("utf-8"))
            return

        try:
            # Décoder le token base64
            qr_json = base64.b64decode(token).decode("utf-8")
            qr_data = json.loads(qr_json)

            from_alias = qr_data.get("from_alias", "Inconnu")
            share_name = qr_data.get("share_name", "Sans nom")
            mode = qr_data.get("mode", "consultation")
            count = qr_data.get("count", 0)
            expires_at = qr_data.get("expires_at", "")

            # Formatter la date d'expiration
            if expires_at:
                try:
                    exp_dt = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    expires_display = exp_dt.strftime("%d/%m/%Y %H:%M")
                except:
                    expires_display = expires_at
            else:
                expires_display = t("share.accept_page.info_expires", lang=lang, date="?")

            # Textes i18n
            title = t("share.accept_page.title", lang=lang, from_alias=from_alias)
            subtitle = t("share.accept_page.subtitle", lang=lang)
            count_text = t("share.accept_page.info_items", lang=lang, count=count)
            list_text = t("share.accept_page.info_list", lang=lang, share_name=share_name)
            mode_text = t(f"share.accept_page.info_mode_{mode}", lang=lang)
            mode_icon = "👁️" if mode == "consultation" else "🔄"
            expires_text = t("share.accept_page.info_expires", lang=lang, date=expires_display)
            btn_accept = t("share.accept_page.btn_accept", lang=lang)
            btn_refuse = t("share.accept_page.btn_refuse", lang=lang)
            loading_text = t("share.accept_page.loading", lang=lang)

            # Charger template HTML
            from string import Template
            template_path = Path(__file__).parent / "accept_page_template.html"
            with open(template_path, "r", encoding="utf-8") as f:
                html_template = Template(f.read())

            # Préparer les strings JSON pour le JavaScript
            strings_for_js = {
                "success_title": t("share.accept_page.success_title", lang=lang),
                "success_has_account": t("share.accept_page.success_has_account", lang=lang),
                "success_no_account": t("share.accept_page.success_no_account", lang=lang),
                "btn_install": t("share.accept_page.btn_install", lang=lang),
                "btn_open_bigboff": t("share.accept_page.btn_open_bigboff", lang=lang),
                "error_invalid_token": t("share.accept_page.error_invalid_token", lang=lang),
                "error_network": t("share.accept_page.error_network", lang=lang)
            }

            # Remplacer les placeholders
            html = html_template.substitute(
                lang=lang,
                page_title=title,
                title=title,
                subtitle=subtitle,
                count_text=count_text,
                list_text=list_text,
                mode_icon=mode_icon,
                mode_text=mode_text,
                expires_text=expires_text,
                btn_accept=btn_accept,
                btn_refuse=btn_refuse,
                loading_text=loading_text,
                token=token,
                strings_json=json.dumps(strings_for_js, ensure_ascii=False)
            )

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            error_html = f"<h1>Erreur</h1><p>Impossible de décoder le token : {str(e)}</p>"
            self.wfile.write(error_html.encode("utf-8"))

    def _json_response(self, code, data):
        self.send_response(code)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # ── Identity P2P — Méthodes wrapper ─────────────────

    def handle_identity_status_get(self, params):
        """GET /api/identity/status"""
        return handle_identity_status(self)

    def handle_identity_public_key_get(self, params):
        """GET /api/identity/public_key"""
        return handle_identity_public_key(self)

    def handle_identity_init_post(self, data):
        """POST /api/identity/init"""
        return handle_identity_init(self, data)

    def handle_identity_sign_post(self, data):
        """POST /api/identity/sign"""
        return handle_identity_sign(self, data)

    def handle_identity_verify_post(self, data):
        """POST /api/identity/verify"""
        return handle_identity_verify(self, data)

    def handle_identity_protect_post(self, data):
        """POST /api/identity/protect"""
        return handle_identity_protect(self, data)

    def handle_identity_unlock_post(self, data):
        """POST /api/identity/unlock"""
        return handle_identity_unlock(self, data)

    def handle_share_accept(self, data):
        """POST /api/share/accept - Accepte un partage QR (Phase 4 P2P)

        Accepte soit :
        - {token: "base64..."} depuis la page /accept mobile
        - {from_user_id, permission, ...} format direct (legacy)
        """
        import base64

        # Nouveau format : token base64
        token = data.get("token")
        if token:
            try:
                # Décoder le token
                qr_json = base64.b64decode(token).decode("utf-8")
                qr_data = json.loads(qr_json)

                from_user_id = qr_data.get("from_user_id")
                from_alias = qr_data.get("from_alias", "Inconnu")
                permission = qr_data.get("permission", {})
                share_name = qr_data.get("share_name", "Partage sans nom")
                count = qr_data.get("count", 0)

                # TODO Phase 4+ : Vérifier signature et expiration
                # TODO Phase 5+ : Créer la permission via relay/permissions.py
                # Pour l'instant, on retourne juste un succès

                # Enregistrer l'acceptation pour notification
                import datetime
                acceptation = {
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                    "from_user_id": from_user_id,
                    "from_alias": from_alias,
                    "share_name": share_name,
                    "count": count,
                    "mode": permission.get("mode"),
                    "recipient": "unknown"  # TODO: récupérer l'identité du receveur
                }

                # Stocker dans un fichier temporaire (notifications des dernières 24h)
                notif_file = "/tmp/bigboff_share_notifications.json"
                notifications = []
                try:
                    if os.path.exists(notif_file):
                        with open(notif_file, "r") as f:
                            notifications = json.load(f)
                    notifications.append(acceptation)
                    # Garder seulement les 50 dernières
                    notifications = notifications[-50:]
                    with open(notif_file, "w") as f:
                        json.dump(notifications, f, indent=2)
                except Exception as e:
                    print(f"[WARN] Erreur sauvegarde notification: {e}")

                # Log l'acceptation
                print(f"[ACCEPT] {from_alias} ({from_user_id}) partage '{share_name}' ({count} éléments)")
                print(f"[ACCEPT] Mode: {permission.get('mode')}, Scope: {permission.get('scope_type')}")

                return {
                    "success": True,
                    "message": f"Partage '{share_name}' accepté !",
                    "from_alias": from_alias,
                    "count": count,
                    "mode": permission.get("mode")
                }

            except Exception as e:
                import traceback
                traceback.print_exc()
                return {"success": False, "error": f"Erreur décodage token: {str(e)}"}

        # Ancien format (legacy)
        from_user_id = data.get("from_user_id")
        permission = data.get("permission", {})
        signature = data.get("signature")

        if not from_user_id or not permission:
            return {"success": False, "error": "Données manquantes"}

        # TODO Phase 4 : Vérifier signature QR

        # Appeler permissions.py pour créer la permission via relay
        try:
            from permissions import grant_permission

            result = grant_permission(
                from_user_id,  # target = celui qui partage (inversé ici)
                permission.get("scope_type"),
                permission.get("scope_value"),
                permission.get("mode", "consultation"),
                permission.get("permissions", ["read"])
            )

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def handle_qr_generate(self, data):
        """POST /api/qr/generate - Génère données QR pour partage (Phase 6 P2P)

        Request:
        {
            "scope_type": "tag",
            "scope_value": "recettes",
            "mode": "consultation" ou "partage",
            "permissions": ["read"]  (optionnel)
        }

        Response:
        {
            "success": true,
            "qr_data": {
                "version": "1.0",
                "type": "share_permission",
                "from_user_id": "bigboff_...",
                "from_alias": "Alice",
                "permission": {
                    "scope_type": "tag",
                    "scope_value": "recettes",
                    "mode": "consultation",
                    "permissions": ["read"]
                },
                "signature": "...",
                "expires_at": "2026-02-11T10:00:00Z"
            },
            "qr_base64": "eyJ2ZXJ...",  # JSON base64-encodé pour QR
            "count": 42  # Nombre d'éléments qui seront partagés
        }
        """
        scope_type = data.get("scope_type")
        mode = data.get("mode", "consultation")
        permissions = data.get("permissions", ["read"])

        if not scope_type:
            return {"success": False, "error": "scope_type requis"}

        if mode not in ["consultation", "partage"]:
            return {"success": False, "error": "mode doit être 'consultation' ou 'partage'"}

        try:
            # 1. Récupérer identité locale
            from identity import get_identity
            identity = get_identity()

            if not identity:
                return {"success": False, "error": "Identité non initialisée"}

            user_id = identity.get("user_id")
            alias = identity.get("alias", "")

            # 2. Compter éléments qui seront partagés
            conn = get_db()
            c = conn.cursor()

            count = 0
            search_criteria = None

            if scope_type == "search":
                # Nouveau : Partager les résultats d'une recherche
                include_tags = data.get("include_tags", [])
                exclude_tags = data.get("exclude_tags", [])
                types = data.get("types", [])
                share_name = data.get("share_name", " ".join(include_tags))

                # Requête identique à /api/search
                query = "SELECT DISTINCT i.id FROM items i"
                conditions = []
                params = []

                if include_tags:
                    placeholders = ','.join('?' * len(include_tags))
                    query += f"""
                        JOIN (
                            SELECT item_id, COUNT(DISTINCT tag) as tag_count
                            FROM tags
                            WHERE tag_display IN ({placeholders})
                            GROUP BY item_id
                            HAVING tag_count = ?
                        ) t ON i.id = t.item_id
                    """
                    params.extend(include_tags)
                    params.append(len(include_tags))

                if exclude_tags:
                    placeholders_ex = ','.join('?' * len(exclude_tags))
                    conditions.append(f"""i.id NOT IN (
                        SELECT item_id FROM tags WHERE tag_display IN ({placeholders_ex})
                    )""")
                    params.extend(exclude_tags)

                if types:
                    type_conditions = []
                    for t in types:
                        if t == "file":
                            type_conditions.append("i.type = 'file'")
                        elif t in ["email", "note", "event", "contact", "lieu", "vault", "video"]:
                            type_conditions.append(f"i.type = '{t}'")
                        elif t == "favori":
                            conditions.append("i.id IN (SELECT item_id FROM favorites)")
                    if type_conditions:
                        conditions.append("(" + " OR ".join(type_conditions) + ")")

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                c.execute(query, params)
                count = len(c.fetchall())

                search_criteria = {
                    "include_tags": include_tags,
                    "exclude_tags": exclude_tags,
                    "types": types,
                    "share_name": share_name
                }

            elif scope_type == "tag":
                scope_value = data.get("scope_value")
                c.execute("""
                    SELECT COUNT(DISTINCT item_id)
                    FROM tags
                    WHERE tag = ?
                """, (scope_value,))
                count = c.fetchone()[0]
                search_criteria = scope_value

            elif scope_type == "all":
                c.execute("SELECT COUNT(*) FROM items")
                count = c.fetchone()[0]
                search_criteria = "all"

            # 3. Créer payload QR
            import datetime
            expires_at = (datetime.datetime.utcnow() + datetime.timedelta(hours=24)).isoformat() + "Z"

            # Extraire share_name depuis search_criteria si disponible
            if isinstance(search_criteria, dict):
                share_name = search_criteria.get("share_name", "Partage sans nom")
            else:
                share_name = str(search_criteria) if search_criteria else "Partage sans nom"

            qr_data = {
                "version": "1.0",
                "type": "share_permission",
                "from_user_id": user_id,
                "from_alias": alias,
                "permission": {
                    "scope_type": scope_type,
                    "scope_criteria": search_criteria,
                    "mode": mode,
                    "permissions": permissions
                },
                "share_name": share_name,  # Pour l'affichage dans la page /accept
                "count": count,  # Pour l'affichage dans la page /accept
                "expires_at": expires_at,
                "signature": ""  # TODO Phase 4+ : Signer avec Ed25519
            }

            # 4. Encoder en base64 pour QR
            import json
            import base64
            qr_json = json.dumps(qr_data)
            qr_base64 = base64.b64encode(qr_json.encode()).decode()

            # Générer URL complète pour scan mobile
            qr_url = f"{BASE_URL}/accept?token={qr_base64}"

            return {
                "success": True,
                "qr_data": qr_data,
                "qr_base64": qr_base64,  # Garder pour compatibilité extension
                "qr_url": qr_url,  # URL complète pour mobile
                "count": count
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def handle_consult_list(self, params):
        """GET /api/consult/list

        Lister tous les éléments consultés (source_user_id NOT NULL).

        Response:
        {
          "success": true,
          "consulted": [
            {
              "source_user_id": "bigboff_abc123",
              "source_alias": "Alice",
              "count_items": 42,
              "count_contacts": 5,
              "count_lieux": 2,
              "count_events": 8
            }
          ]
        }
        """
        conn = get_db()
        c = conn.cursor()

        # Grouper par source_user_id pour chaque type
        stats = {}

        # Items (fichiers)
        c.execute("""
            SELECT source_user_id, COUNT(*) as count
            FROM items
            WHERE source_user_id IS NOT NULL
            GROUP BY source_user_id
        """)
        for row in c.fetchall():
            user_id = row[0]
            if user_id not in stats:
                stats[user_id] = {"source_user_id": user_id}
            stats[user_id]["count_items"] = row[1]

        # Contacts
        c.execute("""
            SELECT source_user_id, COUNT(*) as count
            FROM contacts
            WHERE source_user_id IS NOT NULL
            GROUP BY source_user_id
        """)
        for row in c.fetchall():
            user_id = row[0]
            if user_id not in stats:
                stats[user_id] = {"source_user_id": user_id}
            stats[user_id]["count_contacts"] = row[1]

        # Lieux
        c.execute("""
            SELECT source_user_id, COUNT(*) as count
            FROM lieux
            WHERE source_user_id IS NOT NULL
            GROUP BY source_user_id
        """)
        for row in c.fetchall():
            user_id = row[0]
            if user_id not in stats:
                stats[user_id] = {"source_user_id": user_id}
            stats[user_id]["count_lieux"] = row[1]

        # Events
        c.execute("""
            SELECT source_user_id, COUNT(*) as count
            FROM events
            WHERE source_user_id IS NOT NULL
            GROUP BY source_user_id
        """)
        for row in c.fetchall():
            user_id = row[0]
            if user_id not in stats:
                stats[user_id] = {"source_user_id": user_id}
            stats[user_id]["count_events"] = row[1]

        conn.close()

        # Construire résultat
        consulted = []
        for user_id, data in stats.items():
            consulted.append({
                "source_user_id": user_id,
                "source_alias": user_id[:20] + "...",  # Tronquer pour affichage
                "count_items": data.get("count_items", 0),
                "count_contacts": data.get("count_contacts", 0),
                "count_lieux": data.get("count_lieux", 0),
                "count_events": data.get("count_events", 0)
            })

        return {
            "success": True,
            "consulted": consulted,
            "count": len(consulted)
        }

    # ── Tasks handlers ────────────────────────────────────────────────────────

    def handle_tasks_tags(self, params):
        """GET /api/tasks/tags → Tags uniques de toutes les tâches."""
        conn = get_tasks_db()
        try:
            rows = conn.execute("SELECT DISTINCT tags_raw FROM tasks WHERE tags_raw != '' AND conflict_of_id IS NULL").fetchall()
            tags = set()
            for (raw,) in rows:
                for t in raw.split(","):
                    t = t.strip()
                    if t:
                        tags.add(t)
            return {"tags": sorted(tags)}
        finally:
            conn.close()

    def handle_tasks_today(self, params):
        """GET /api/tasks/today → Vue Aujourd'hui complète."""
        conn = get_tasks_db()
        try:
            return get_today_view(conn)
        finally:
            conn.close()

    def handle_tasks_projects(self, params):
        """GET /api/tasks/projects → Tous les projets avec hiérarchie."""
        conn = get_tasks_db()
        try:
            return {"projects": get_projects_view(conn)}
        finally:
            conn.close()

    def handle_tasks_list(self, params):
        """GET /api/tasks → Liste de tâches avec filtres, ou GET /api/tasks?id=N → tâche unique."""
        conn = get_tasks_db()
        try:
            # Si ?id=N → retourner une tâche précise
            task_id_raw = params.get("id", [None])[0]
            if task_id_raw:
                t = task_get(conn, int(task_id_raw))
                return {"tasks": [t] if t else [], "count": 1 if t else 0}

            kind_raw = params.get("kind", [None])[0]
            scheduled = params.get("scheduled", [None])[0]
            status = params.get("status", [None])[0]
            parent_id = params.get("parent_id", ["__root__"])[0]
            if parent_id == "null":
                parent_id = None
            elif parent_id != "__root__":
                parent_id = int(parent_id)
            tags_raw = params.get("tags", [""])[0]
            tags_include = [t for t in tags_raw.split(",") if t] if tags_raw else None
            tasks = task_list(conn, kind=kind_raw, scheduled=scheduled, status=status,
                              parent_id=parent_id, tags_include=tags_include,
                              with_subtasks=True)
            return {"tasks": tasks, "count": len(tasks)}
        finally:
            conn.close()

    def handle_tasks_conflicts(self, params):
        """GET /api/tasks/conflicts → Conflits de sync en attente."""
        conn = get_tasks_db()
        try:
            return {"conflicts": conflict_list(conn)}
        finally:
            conn.close()

    def handle_tasks_steps(self, params):
        """GET /api/tasks/steps?project_id=N → sync from file, return project data with chantiers."""
        project_id_raw = params.get("project_id", [None])[0]
        if not project_id_raw:
            return {"error": "project_id obligatoire"}
        project_id = int(project_id_raw)
        conn = get_tasks_db()
        try:
            proj = task_get(conn, project_id)
            if not proj:
                return {"error": "projet introuvable"}
            fs_path = proj.get("fs_path")
            if fs_path:
                sync_steps_from_file(conn, project_id, fs_path)
            # Rebuild full project with chantiers + their tasks + direct tasks
            proj = task_get(conn, project_id)
            c = conn.cursor()
            # Chantiers — triés par deadline ASC NULLS LAST
            c.execute(
                "SELECT id,title,status,deadline_date,tags_raw FROM tasks WHERE kind='chantier' AND project_id=? AND conflict_of_id IS NULL ORDER BY CASE WHEN deadline_date IS NULL OR deadline_date='' THEN 1 ELSE 0 END, deadline_date, sort_order",
                (project_id,)
            )
            chantiers = []
            for ch_id, ch_title, ch_status, ch_dl, ch_tags in c.fetchall():
                c2 = conn.cursor()
                c2.execute(
                    "SELECT id,title,status,deadline_date,tags_raw FROM tasks WHERE kind='task' AND chantier_id=? AND conflict_of_id IS NULL ORDER BY CASE WHEN deadline_date IS NULL OR deadline_date='' THEN 1 ELSE 0 END, deadline_date, sort_order",
                    (ch_id,)
                )
                subtasks = [{"id": r[0], "title": r[1], "status": r[2], "deadline_date": r[3],
                             "tags": [t.strip() for t in (r[4] or "").split(",") if t.strip()]} for r in c2.fetchall()]
                chantiers.append({"id": ch_id, "title": ch_title, "status": ch_status, "deadline_date": ch_dl,
                                  "tags": [t.strip() for t in (ch_tags or "").split(",") if t.strip()],
                                  "subtasks": subtasks})
            proj["chantiers"] = chantiers
            # Direct tasks — triées par deadline ASC NULLS LAST
            c.execute(
                "SELECT id,title,status,deadline_date,tags_raw FROM tasks WHERE kind='task' AND project_id=? AND chantier_id IS NULL AND conflict_of_id IS NULL ORDER BY CASE WHEN deadline_date IS NULL OR deadline_date='' THEN 1 ELSE 0 END, deadline_date, sort_order",
                (project_id,)
            )
            proj["subtasks"] = [{"id": r[0], "title": r[1], "status": r[2], "deadline_date": r[3],
                                  "tags": [t.strip() for t in (r[4] or "").split(",") if t.strip()]} for r in c.fetchall()]
            return {"success": True, "project": proj}
        finally:
            conn.close()

    def handle_tasks_steps_rewrite(self, data):
        """POST /api/tasks/steps_rewrite → rewrite _STEPS.md from DB."""
        project_id = data.get("project_id")
        if not project_id:
            return {"error": "project_id obligatoire"}
        conn = get_tasks_db()
        try:
            sync_steps_to_file(conn, int(project_id))
            return {"success": True}
        finally:
            conn.close()

    def handle_tasks_post(self, data):
        """POST /api/tasks → Créer une tâche/chantier/projet."""
        title = data.get("title", "").strip()
        if not title:
            return {"error": "title obligatoire"}
        kind = data.get("kind", "task")
        if kind not in ("projet", "chantier", "task"):
            kind = "task"
        category = data.get("category", "PRO").upper()
        conn = get_tasks_db()
        try:
            task = task_create(
                conn,
                title=title,
                description=data.get("description", ""),
                kind=kind,
                project_id=data.get("project_id"),
                chantier_id=data.get("chantier_id"),
                parent_id=data.get("parent_id"),
                scheduled=data.get("scheduled", "later"),
                deadline_date=data.get("deadline_date"),
                tags=data.get("tags", []),
                sort_order=data.get("sort_order", 0)
            )
            # Hook projet : créer dossier + _SUIVI.md + MAJ _PROJETS.md
            if kind == "projet":
                fs_info = _create_project_files(title, category, data.get("description", ""))
                if fs_info.get("fs_path"):
                    conn.execute("UPDATE tasks SET fs_path=?, category=? WHERE id=?",
                                 (fs_info["fs_path"], category, task["id"]))
                    conn.commit()
                    task["fs_path"] = fs_info["fs_path"]
            # Auto-promotion : si une tâche reçoit un chantier_id ou project_id parent
            # et qu'un autre task a déjà ce chantier_id → le parent task devient chantier
            if kind == "task" and data.get("chantier_id"):
                parent_row = conn.execute(
                    "SELECT id, kind FROM tasks WHERE id=?", (data["chantier_id"],)
                ).fetchone()
                if parent_row and parent_row[1] == "task":
                    conn.execute("UPDATE tasks SET kind='chantier' WHERE id=?", (parent_row[0],))
                    conn.commit()
            # Sync _STEPS.md
            pid = task.get("project_id") or (task["id"] if task.get("kind") == "projet" else None)
            if pid:
                sync_steps_to_file(conn, pid)
            return {"success": True, "task": task}
        finally:
            conn.close()

    def handle_tasks_put(self, data):
        """PUT /api/tasks → Mettre à jour une tâche."""
        task_id = data.get("id")
        if not task_id:
            return {"error": "id obligatoire"}
        conn = get_tasks_db()
        try:
            fields = {k: v for k, v in data.items() if k != "id"}
            if "tags" in fields:
                fields["tags_raw"] = ",".join(fields.pop("tags"))
            if "kind" in fields and fields["kind"] not in ("projet", "chantier", "task"):
                del fields["kind"]
            task = task_update(conn, task_id, **fields)
            pid = task.get("project_id") or (task["id"] if task.get("kind") == "projet" else None)
            if pid:
                sync_steps_to_file(conn, pid)
            return {"success": True, "task": task}
        finally:
            conn.close()

    def handle_tasks_delete(self, data):
        """DELETE /api/tasks → Supprimer une tâche."""
        task_id = data.get("id")
        if not task_id:
            return {"error": "id obligatoire"}
        conn = get_tasks_db()
        try:
            row = conn.execute("SELECT project_id, kind FROM tasks WHERE id=?", (task_id,)).fetchone()
            project_id = row[0] if row else None
            result = task_delete(conn, task_id)
            if project_id:
                sync_steps_to_file(conn, project_id)
            return {"success": True, **result}
        finally:
            conn.close()

    def handle_tasks_done(self, data):
        """POST /api/tasks/done → Marquer une tâche comme faite."""
        task_id = data.get("id")
        if not task_id:
            return {"error": "id obligatoire"}
        conn = get_tasks_db()
        try:
            task = task_done(conn, task_id)
            pid = task.get("project_id") or (task["id"] if task.get("kind") == "projet" else None)
            if pid:
                sync_steps_to_file(conn, pid)
            view = get_today_view(conn)
            return {"success": True, "task": task, "all_done": view["all_done"],
                    "progress": view["progress"]}
        finally:
            conn.close()

    def handle_tasks_undone(self, data):
        """POST /api/tasks/undone → Décocher une tâche."""
        task_id = data.get("id")
        if not task_id:
            return {"error": "id obligatoire"}
        conn = get_tasks_db()
        try:
            task = task_undone(conn, task_id)
            pid = task.get("project_id") or (task["id"] if task.get("kind") == "projet" else None)
            if pid:
                sync_steps_to_file(conn, pid)
            return {"success": True, "task": task}
        finally:
            conn.close()

    def handle_tasks_schedule(self, data):
        """POST /api/tasks/schedule → Changer le planning d'une tâche."""
        task_id = data.get("id")
        scheduled = data.get("scheduled")
        if not task_id or not scheduled:
            return {"error": "id et scheduled obligatoires"}
        conn = get_tasks_db()
        try:
            task = task_schedule(conn, task_id, scheduled)
            return {"success": True, "task": task}
        finally:
            conn.close()

    def handle_tasks_attachment_add(self, data):
        """POST /api/tasks/attachments → Ajouter une pièce jointe."""
        task_id = data.get("task_id")
        type_ = data.get("type")
        name = data.get("name", "").strip()
        if not task_id or not type_ or not name:
            return {"error": "task_id, type et name obligatoires"}
        conn = get_tasks_db()
        try:
            att = attachment_add(conn, task_id, type_, name,
                                 url=data.get("url"),
                                 file_path=data.get("file_path"),
                                 comment=data.get("comment", ""))
            # Sync _STEPS.md : task_id peut être le projet lui-même ou une tâche
            row = conn.execute("SELECT project_id, kind FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row:
                pid = row[0] if row[1] != "projet" else task_id
                if pid:
                    sync_steps_to_file(conn, pid)
            return {"success": True, "attachment": att}
        finally:
            conn.close()

    def handle_tasks_attachment_delete(self, data):
        """DELETE /api/tasks/attachments → Supprimer une pièce jointe."""
        att_id = data.get("id")
        if not att_id:
            return {"error": "id obligatoire"}
        conn = get_tasks_db()
        try:
            return {"success": True, **attachment_delete(conn, att_id)}
        finally:
            conn.close()

    def handle_tasks_conflict_resolve(self, data):
        """POST /api/tasks/conflicts/resolve → Résoudre un conflit de sync."""
        conflict_id = data.get("conflict_id")
        keep = data.get("keep", "original")
        if not conflict_id:
            return {"error": "conflict_id obligatoire"}
        conn = get_tasks_db()
        try:
            return conflict_resolve(conn, conflict_id, keep=keep)
        finally:
            conn.close()

    def log_message(self, format, *args):
        """Log simplifié."""
        print(f"[SEARCH] {args[0]}")


def _steps_md_path(fs_path):
    """Returns path to _STEPS.md for a project directory."""
    return os.path.join(fs_path, "_STEPS.md")


def parse_steps_md(content):
    """
    Parse _STEPS.md content into structured data.
    Supports optional YAML front matter (---) for project meta fields.
    Flexible format:
      - Front matter: ---\ndescription: ...\ngoal: ...\nmission: ...\n---
      - Chantier: "# CHANTIER: title"  OR any "# title" (except # TASK:)
      - Task under chantier: "## TASK: [x] title"  OR  "## [x] title"  OR  "## title"
      - Direct task: "# TASK: [x] title"
    Returns: {"meta": {"description": ..., "goal": ..., "mission": ...},
              "chantiers": [{"title": str, "tasks": [{"title": str, "done": bool}]}],
              "direct_tasks": [{"title": str, "done": bool}]}
    """
    chantiers = []
    direct_tasks = []
    current_chantier = None
    meta = {}

    all_lines = content.splitlines()
    i = 0

    # Parse YAML front matter
    if all_lines and all_lines[0].strip() == '---':
        i = 1
        while i < len(all_lines) and all_lines[i].strip() != '---':
            m = re.match(r'^(\w+):\s*(.*)$', all_lines[i])
            if m:
                meta[m.group(1)] = m.group(2).strip()
            i += 1
        i += 1  # skip closing ---

    for line in all_lines[i:]:
        line = line.rstrip()

        # Direct task (canonical): # TASK: [x] title  — must check BEFORE generic H1
        m_t1 = re.match(r'^#\s+TASK:\s+\[(.)\]\s+(.+)', line)
        if m_t1:
            done = m_t1.group(1).lower() == 'x'
            direct_tasks.append({"title": m_t1.group(2).strip(), "done": done})
            current_chantier = None
            continue

        # Chantier (canonical): # CHANTIER: title
        m_ch = re.match(r'^#\s+CHANTIER:\s+(.+)', line)
        if m_ch:
            current_chantier = {"title": m_ch.group(1).strip(), "tasks": []}
            chantiers.append(current_chantier)
            continue

        # Any H1 not matching above → chantier (flexible format)
        m_h1 = re.match(r'^#\s+(.+)', line)
        if m_h1:
            current_chantier = {"title": m_h1.group(1).strip(), "tasks": []}
            chantiers.append(current_chantier)
            continue

        # Tasks under chantier
        if current_chantier is not None:
            # Canonical: ## TASK: [x] title
            m_t2 = re.match(r'^##\s+TASK:\s+\[(.)\]\s+(.+)', line)
            if m_t2:
                done = m_t2.group(1).lower() == 'x'
                current_chantier["tasks"].append({"title": m_t2.group(2).strip(), "done": done})
                continue
            # Flexible: ## [x] title
            m_t2b = re.match(r'^##\s+\[(.)\]\s+(.+)', line)
            if m_t2b:
                done = m_t2b.group(1).lower() == 'x'
                current_chantier["tasks"].append({"title": m_t2b.group(2).strip(), "done": done})
                continue
            # Flexible: ## title (no status → todo)
            m_t2c = re.match(r'^##\s+(.+)', line)
            if m_t2c:
                current_chantier["tasks"].append({"title": m_t2c.group(1).strip(), "done": False})
                continue

    return {"meta": meta, "chantiers": chantiers, "direct_tasks": direct_tasks}


def render_steps_md(conn, project_id):
    """
    Render _STEPS.md content from the database for a given project.
    Includes YAML front matter with description/goal/mission if set.
    Returns the markdown string.
    """
    c = conn.cursor()

    # Get project meta fields
    row = c.execute(
        "SELECT description, goal, mission, deadline_date FROM tasks WHERE id=? AND kind='projet'",
        (project_id,)
    ).fetchone()
    description = (row[0] or "").strip() if row else ""
    goal = (row[1] or "").strip() if row else ""
    mission = (row[2] or "").strip() if row else ""
    deadline = (row[3] or "").strip() if row else ""

    lines = []

    # Front matter — toujours présent avec tous les champs
    lines.append("---")
    lines.append(f"description: {description}")
    lines.append(f"goal: {goal}")
    lines.append(f"mission: {mission}")
    lines.append(f"deadline: {deadline}")
    lines.append("---")
    lines.append("")

    # Get chantiers of this project
    c.execute(
        "SELECT id, title, status FROM tasks WHERE kind='chantier' AND project_id=? AND conflict_of_id IS NULL ORDER BY sort_order, created_at",
        (project_id,)
    )
    chantiers = c.fetchall()

    for ch_id, ch_title, ch_status in chantiers:
        lines.append(f"# CHANTIER: {ch_title}")
        c.execute(
            "SELECT title, status FROM tasks WHERE kind='task' AND chantier_id=? AND conflict_of_id IS NULL ORDER BY sort_order, created_at",
            (ch_id,)
        )
        for t_title, t_status in c.fetchall():
            check = "x" if t_status == "done" else " "
            lines.append(f"## TASK: [{check}] {t_title}")
        lines.append("")

    # Direct tasks (no chantier)
    c.execute(
        "SELECT title, status FROM tasks WHERE kind='task' AND project_id=? AND chantier_id IS NULL AND conflict_of_id IS NULL ORDER BY sort_order, created_at",
        (project_id,)
    )
    direct = c.fetchall()
    if direct:
        for t_title, t_status in direct:
            check = "x" if t_status == "done" else " "
            lines.append(f"# TASK: [{check}] {t_title}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def sync_steps_to_file(conn, project_id):
    """Write _STEPS.md from DB state. Silently fails if no fs_path."""
    try:
        row = conn.execute("SELECT fs_path FROM tasks WHERE id=? AND kind='projet'", (project_id,)).fetchone()
        if not row or not row[0]:
            return
        fs_path = row[0]
        if not os.path.isdir(fs_path):
            return
        content = render_steps_md(conn, project_id)
        path = _steps_md_path(fs_path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"[WARN] sync_steps_to_file({project_id}): {e}")


def sync_steps_from_file(conn, project_id, fs_path):
    """
    Read _STEPS.md and reconcile with DB.
    - Front matter (description/goal/mission) → updates project meta
    - Chantiers/tasks in file but not in DB → create
    - Chantiers/tasks in DB: status updated from file if title matches
    Does NOT delete DB items missing from file.
    """
    try:
        path = _steps_md_path(fs_path)
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        parsed = parse_steps_md(content)
        now = datetime.now().isoformat(timespec="seconds")

        # Update project meta from front matter if present
        meta = parsed.get("meta", {})
        field_map = {"description": "description", "goal": "goal", "mission": "mission", "deadline": "deadline_date"}
        meta_updates = {field_map[k]: meta[k] for k in field_map if k in meta}
        if meta_updates:
            set_clause = ", ".join(f"{k}=?" for k in meta_updates)
            conn.execute(
                f"UPDATE tasks SET {set_clause}, updated_at=? WHERE id=? AND kind='projet'",
                list(meta_updates.values()) + [now, project_id]
            )

        # Process chantiers
        for ch_data in parsed["chantiers"]:
            # Find existing chantier by title
            row = conn.execute(
                "SELECT id FROM tasks WHERE kind='chantier' AND project_id=? AND title=? AND conflict_of_id IS NULL",
                (project_id, ch_data["title"])
            ).fetchone()
            if row:
                ch_id = row[0]
            else:
                conn.execute(
                    "INSERT INTO tasks (title, kind, project_id, status, scheduled, tags_raw, sort_order, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (ch_data["title"], "chantier", project_id, "todo", "later", "", 0, now, now)
                )
                conn.commit()
                ch_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            # Process tasks of this chantier
            for t_data in ch_data["tasks"]:
                t_status = "done" if t_data["done"] else "todo"
                t_row = conn.execute(
                    "SELECT id, status FROM tasks WHERE kind='task' AND chantier_id=? AND title=? AND conflict_of_id IS NULL",
                    (ch_id, t_data["title"])
                ).fetchone()
                if t_row:
                    if t_row[1] != t_status:
                        done_at = now if t_status == "done" else None
                        conn.execute("UPDATE tasks SET status=?, done_at=?, updated_at=? WHERE id=?",
                                     (t_status, done_at, now, t_row[0]))
                else:
                    done_at = now if t_status == "done" else None
                    conn.execute(
                        "INSERT INTO tasks (title, kind, project_id, chantier_id, status, scheduled, tags_raw, sort_order, done_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (t_data["title"], "task", project_id, ch_id, t_status, "later", "", 0, done_at, now, now)
                    )

        # Process direct tasks
        for t_data in parsed["direct_tasks"]:
            t_status = "done" if t_data["done"] else "todo"
            t_row = conn.execute(
                "SELECT id, status FROM tasks WHERE kind='task' AND project_id=? AND chantier_id IS NULL AND title=? AND conflict_of_id IS NULL",
                (project_id, t_data["title"])
            ).fetchone()
            if t_row:
                if t_row[1] != t_status:
                    done_at = now if t_status == "done" else None
                    conn.execute("UPDATE tasks SET status=?, done_at=?, updated_at=? WHERE id=?",
                                 (t_status, done_at, now, t_row[0]))
            else:
                done_at = now if t_status == "done" else None
                conn.execute(
                    "INSERT INTO tasks (title, kind, project_id, chantier_id, status, scheduled, tags_raw, sort_order, done_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (t_data["title"], "task", project_id, None, t_status, "later", "", 0, done_at, now, now)
                )

        conn.commit()
    except Exception as e:
        print(f"[WARN] sync_steps_from_file({project_id}): {e}")


def _create_project_files(title, category="PRO", description=""):
    """
    Crée le dossier projet + _SUIVI.md et met à jour _PROJETS.md.
    Retourne {"fs_path": ..., "created": True/False}
    """
    import os, re
    from datetime import date

    PROJETS_ROOT = "/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS"
    PROJETS_MD   = "/Users/nathalie/Dropbox/____BIG_BOFF___/CLAUDE/_PROJETS.md"

    fs_path = os.path.join(PROJETS_ROOT, category, title)

    # Créer le dossier si inexistant
    created = False
    if not os.path.isdir(fs_path):
        os.makedirs(fs_path, exist_ok=True)
        created = True

    # Créer _SUIVI.md si inexistant
    suivi = os.path.join(fs_path, "_SUIVI.md")
    if not os.path.exists(suivi):
        today = date.today().isoformat()
        with open(suivi, "w", encoding="utf-8") as f:
            f.write(f"# {title} — Suivi\n\n")
            if description:
                f.write(f"> {description}\n\n")
            f.write(f"**Statut** : 🟢 actif\n")
            f.write(f"**Créé** : {today}\n")
            f.write(f"**Dernière MAJ** : {today}\n\n---\n\n")
            f.write("## Objectif\n\n\n## À faire\n\n- [ ] \n\n## Historique\n\n")
            f.write(f"| Date | Action |\n|---|---|\n| {today} | Création du projet |\n")

    # Mettre à jour _PROJETS.md : ajouter la ligne dans "Projets actifs"
    if os.path.exists(PROJETS_MD):
        with open(PROJETS_MD, "r", encoding="utf-8") as f:
            content = f.read()
        rel_path = os.path.relpath(fs_path, "/Users/nathalie/Dropbox/____BIG_BOFF___")
        new_line = f"| **{title}** | `{rel_path}/` | {description} | 🟢 actif |\n"
        # Insérer après l'en-tête du tableau "Projets actifs" si pas déjà présent
        if f"**{title}**" not in content:
            # Trouver la fin du tableau actifs (première ligne | après "## Projets actifs")
            content = re.sub(
                r'(\| Projet \| Path \| Description \| Statut \|\n\|[^\n]+\|\n)',
                r'\1' + new_line,
                content
            )
            with open(PROJETS_MD, "w", encoding="utf-8") as f:
                f.write(content)

    return {"fs_path": fs_path, "created": created}




def main():
    print(f"=== BIG_BOFF Search — Serveur ===")
    print(f"Base : {DB_PATH}")
    print(f"Port : {PORT}")
    print(f"URL locale    : http://{HOST}:{PORT}")
    print(f"URL réseau    : {BASE_URL}")
    print(f"IP détectée   : {LOCAL_IP}")
    print()
    print("Endpoints :")
    print("  GET /api/autocomplete?q=py")
    print("  GET /api/search?include=code&include=python&exclude=test")
    print("  GET /api/cooccurrence?include=code&include=python")
    print("  GET /api/stats")
    print()

    server = http.server.HTTPServer((HOST, PORT), SearchHandler)
    try:
        print("Serveur démarré. Ctrl+C pour arrêter.\n")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
        server.server_close()


if __name__ == "__main__":
    main()
