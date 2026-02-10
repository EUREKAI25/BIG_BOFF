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
import sqlite3
import subprocess
import urllib.parse
from pathlib import Path

from config import normalize_tag, is_valid_tag

DB_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db"
DROPBOX_ROOT = "/Users/nathalie/Dropbox"
PORT = 7777
HOST = "127.0.0.1"
ACCOUNTS_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH/src/email_accounts.json"

# ── Miniatures ───────────────────────────────────────
THUMBNAIL_DIR = Path(__file__).parent.parent / ".thumbnails"
THUMBNAIL_DIR.mkdir(exist_ok=True)
SAVED_IMAGES_DIR = Path(__file__).parent.parent / ".saved_images"
SAVED_IMAGES_DIR.mkdir(exist_ok=True)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".ico"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv"}

# ── Coffre-fort ──────────────────────────────────────
_vault_master = None  # Mot de passe maître en mémoire (session uniquement)


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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
.container { max-width: 900px; margin: 0 auto; padding: 20px; }
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
.cooc-section { margin-bottom: 12px; }
.cooc-section:empty { display: none; }
.cooc-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.cooc-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.cooc-tag { padding: 3px 8px; border-radius: 4px; font-size: 12px; cursor: pointer; background: #e8ecf1; color: #444; border: 1px solid #d0d5dd; }
.cooc-tag:hover { background: #d4edda; border-color: #b1dfbb; }
.cooc-tag .cnt { font-size: 10px; opacity: 0.6; margin-left: 3px; }
.results-header { display: none; justify-content: space-between; padding: 8px 0; font-size: 12px; color: #888; border-bottom: 1px solid #eee; margin-bottom: 8px; }
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
.empty-state { padding: 60px 20px; text-align: center; color: #aaa; }
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
</style>
</head>
<body>
<header>
  <h1>BIG_BOFF Search</h1>
  <span class="stats" id="stats"></span>
</header>
<div class="error-banner" id="error-banner">Serveur non accessible.</div>
<div class="container">
  <div class="search-bar">
    <input type="text" id="search-input" placeholder="Rechercher un tag..." autofocus>
    <div class="autocomplete" id="autocomplete"></div>
  </div>
  <div class="type-filters" id="type-filters" style="display:none"></div>
  <div class="selected-tags" id="selected-tags"></div>
  <div class="cooc-section" id="cooc-section" style="display:none">
    <div class="cooc-label">Tags associes</div>
    <div class="cooc-tags" id="cooc-tags"></div>
  </div>
  <div class="results-header" id="results-header">
    <span id="results-count"></span>
    <span id="results-nav"></span>
  </div>
  <div class="results-list" id="results-list"></div>
  <div class="empty-state" id="empty-state">
    <div class="big"><i class="fa-solid fa-magnifying-glass"></i></div>
    <div>Tape un mot-clef pour chercher</div>
    <button class="add-btn" id="add-btn" title="Ajouter un \u00e9l\u00e9ment" style="margin:16px auto 0;width:40px;height:40px;font-size:22px">+</button>
    <div style="font-size:12px;margin-top:8px;color:#bbb">Ajouter un \u00e9l\u00e9ment</div>
  </div>
</div>
<script>
const API = window.location.origin + "/api";
const state = { includeTags: [], excludeTags: [], autocompleteIndex: -1, autocompleteItems: [], currentOffset: 0, pageSize: 50, totalResults: 0, activeTypes: [] };
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
const TYPE_BUTTONS = [{type:"all",label:"Tous",icon:""},{type:"file",label:"Fichiers",icon:'<i class="fa-solid fa-folder"></i>'},{type:"email",label:"Emails",icon:'<i class="fa-solid fa-envelope"></i>'},{type:"note",label:"Notes",icon:'<i class="fa-solid fa-note-sticky"></i>'},{type:"video",label:"Vid\u00e9os",icon:'<i class="fa-solid fa-video"></i>'},{type:"event",label:"\u00c9v\u00e9nements",icon:'<i class="fa-solid fa-calendar-days"></i>'},{type:"contact",label:"Contacts",icon:'<i class="fa-solid fa-user"></i>'},{type:"lieu",label:"Lieux",icon:'<i class="fa-solid fa-location-dot"></i>'},{type:"vault",label:"Vault",icon:'<i class="fa-solid fa-lock"></i>'},{type:"favori",label:"Favoris",icon:'<i class="fa-solid fa-heart"></i>'}];
function renderTypeFilters() {
  typeFiltersEl.innerHTML = TYPE_BUTTONS.map(function(b) {
    var isActive = b.type === "all" ? state.activeTypes.length === 0 : b.type === "favori" ? state.includeTags.indexOf("favori") >= 0 : state.activeTypes.indexOf(b.type) >= 0;
    return '<span class="type-btn' + (isActive ? ' active' : '') + '" data-type="' + b.type + '">' + (b.icon ? b.icon + ' ' : '') + b.label + '</span>';
  }).join("");
  typeFiltersEl.querySelectorAll(".type-btn").forEach(function(el) {
    el.addEventListener("click", function() {
      var t = el.dataset.type;
      if (t === "all") { state.activeTypes = []; }
      else if (t === "favori") { var fi = state.includeTags.indexOf("favori"); if (fi >= 0) state.includeTags.splice(fi, 1); else state.includeTags.push("favori"); }
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
    state.autocompleteItems = data.tags.filter(t => !selected.has(t.tag));
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
function renderCooccurrence(tags) {
  if (tags.length === 0) { coocSection.style.display = "none"; return; }
  coocSection.style.display = "block";
  coocTagsEl.innerHTML = tags.map(t => '<span class="cooc-tag" data-tag="' + esc(t.tag) + '">' + esc(t.tag) + ' <span class="cnt">' + t.count.toLocaleString() + '</span></span>').join("");
  coocTagsEl.querySelectorAll(".cooc-tag").forEach(el => {
    let lt, wl;
    el.addEventListener("mousedown", () => { wl = false; lt = setTimeout(() => { wl = true; addExcludeTag(el.dataset.tag); }, 500); });
    el.addEventListener("mouseup", () => { clearTimeout(lt); if (!wl) addIncludeTag(el.dataset.tag); });
    el.addEventListener("mouseleave", () => clearTimeout(lt));
    el.addEventListener("dblclick", e => { e.preventDefault(); removeTag(el.dataset.tag); addExcludeTag(el.dataset.tag); });
    el.addEventListener("contextmenu", e => e.preventDefault());
  });
}
async function fetchResults() {
  if (state.includeTags.length === 0 && state.activeTypes.length === 0) { resultsList.innerHTML = ""; resultsHeader.style.display = "none"; typeFiltersEl.style.display = "none"; coocSection.style.display = "none"; emptyState.style.display = "block"; return; }
  emptyState.style.display = "none"; typeFiltersEl.style.display = "";
  try {
    var sp = { include: state.includeTags, exclude: state.excludeTags, limit: state.pageSize, offset: state.currentOffset };
    if (state.activeTypes.length > 0) sp.types = state.activeTypes.join(",");
    const data = await apiFetch("search", sp);
    state.totalResults = data.total;
    renderResults(data.results);
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
      return '<div class="result-item result-email" data-id="' + r.id + '"><span class="result-icon icon-email"><i class="fa-solid fa-envelope"></i></span><div class="result-body"><div class="result-name">' + esc(r.nom) + fh(r.id) + '</div><div class="result-meta">' + esc(r.chemin) + '</div>' + sn + '<div class="result-meta">' + (r.date_modif || "?") + '</div></div></div>';
    }
    if (r.type === "note") {
      return '<div class="result-item result-note" data-id="' + r.id + '"><span class="result-icon icon-note"><i class="fa-solid fa-note-sticky"></i></span><div class="result-body"><div class="result-name">' + esc(r.nom) + fh(r.id) + '</div><div class="result-meta">' + esc(r.chemin) + '</div><div class="result-meta">' + (r.date_modif || "?") + '</div></div></div>';
    }
    if (r.type === "video") {
      var pIcon = {"youtube":'<i class="fa-brands fa-youtube"></i>',"facebook":'<i class="fa-brands fa-facebook"></i>',"vimeo":'<i class="fa-brands fa-vimeo-v"></i>',"dailymotion":'<i class="fa-solid fa-play"></i>',"instagram":'<i class="fa-brands fa-instagram"></i>',"tiktok":'<i class="fa-brands fa-tiktok"></i>'}[r.platform] || '<i class="fa-solid fa-play"></i>';
      return '<div class="result-item result-video" data-id="' + r.id + '" data-url="' + esc(r.url || r.chemin) + '"><span class="result-icon icon-video">' + pIcon + '</span><div class="result-body"><div class="result-name">' + esc(r.nom) + fh(r.id) + '</div><div class="result-meta">' + esc(r.platform || "") + ' \u00b7 ' + (r.date_modif || "?") + '</div><div class="result-meta" style="font-size:10px;color:#999;word-break:break-all">' + esc(r.url || r.chemin) + '</div></div></div>';
    }
    if (r.type === "event") {
      var recStr = r.recurrence && r.recurrence !== "none" ? ' \u00b7 <i class="fa-solid fa-rotate"></i> ' + ({"daily":"chaque jour","weekly":"chaque semaine","monthly":"chaque mois","yearly":"chaque ann\u00e9e"}[r.recurrence] || "") : "";
      var tagsStr = r.tags_raw ? '<div class="result-meta" style="margin-top:2px">' + esc(r.tags_raw) + '</div>' : '';
      return '<div class="result-item result-event" data-id="' + r.id + '"><span class="result-icon icon-event"><i class="fa-solid fa-calendar-days"></i></span><div class="result-body"><div class="result-name">' + esc(r.nom) + fh(r.id) + '</div><div class="result-meta">' + esc(r.date_fr || r.date_modif || "") + recStr + '</div>' + tagsStr + '</div></div>';
    }
    if (r.type === "contact") {
      var ctIcon = r.contact_type === "entreprise" ? '<i class="fa-solid fa-building"></i>' : '<i class="fa-solid fa-user"></i>';
      return '<div class="result-item result-contact" data-id="' + r.id + '"><span class="result-icon icon-contact">' + ctIcon + '</span><div class="result-body"><div class="result-name">' + esc(r.nom) + fh(r.id) + '</div><div class="result-meta">' + esc(r.chemin) + '</div></div></div>';
    }
    if (r.type === "lieu") {
      return '<div class="result-item result-lieu" data-id="' + r.id + '"><span class="result-icon icon-lieu"><i class="fa-solid fa-location-dot"></i></span><div class="result-body"><div class="result-name">' + esc(r.nom) + fh(r.id) + '</div><div class="result-meta">' + esc(r.chemin) + '</div></div></div>';
    }
    if (r.type === "vault") {
      return '<div class="result-item result-vault" data-id="' + r.id + '"><span class="result-icon icon-vault"><i class="fa-solid fa-lock"></i></span><div class="result-body"><div class="result-name">' + esc(r.nom) + fh(r.id) + '</div><div class="result-meta">' + esc(r.chemin) + (r.project ? ' \u00b7 ' + esc(r.project) : '') + '</div></div></div>';
    }
    var iconHtml = r.is_media ? '<img class="thumb" data-thumb-id="' + r.id + '" src="" alt="" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'inline\'" style="display:none"><span>' + (r.est_dossier ? '<i class="fa-solid fa-folder icon-file"></i>' : fileIcon(r.extension)) + '</span>' : '<span>' + (r.est_dossier ? '<i class="fa-solid fa-folder icon-file"></i>' : fileIcon(r.extension)) + '</span>';
    return '<div class="result-item" data-id="' + r.id + '"><span class="result-icon">' + iconHtml + '</span><div class="result-body"><div class="result-name">' + esc(r.nom) + fh(r.id) + '</div><div class="result-meta">' + formatSize(r.taille) + ' \u00b7 ' + (r.date_modif || "?") + '</div></div><div class="result-actions"><span class="action-btn open-btn" data-id="' + r.id + '" title="Ouvrir"><i class="fa-solid fa-arrow-up-right-from-square"></i></span><span class="action-btn reveal-btn" data-id="' + r.id + '" title="Finder"><i class="fa-solid fa-folder-open"></i></span></div></div>';
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
  resultsList.querySelectorAll(".result-item:not(.result-email):not(.result-note):not(.result-vault):not(.result-video):not(.result-event):not(.result-contact):not(.result-lieu)").forEach(el => {
    el.addEventListener("click", e => { if (e.target.classList.contains("action-btn")) return; openFile(el.dataset.id); });
  });
  resultsList.querySelectorAll(".result-email").forEach(el => {
    el.addEventListener("click", () => toggleEmailView(el));
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
    el.after(div);
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
    el.after(div);
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
    div.innerHTML = h; el.after(div);
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
    div.innerHTML = h; el.after(div);
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
    div.innerHTML = h; el.after(div);
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
    div.innerHTML = h; el.after(div);
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

checkServer(); checkVaultStatus(); input.focus();
</script>
</body>
</html>"""


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
        }

        if path == "/" or path == "":
            self._serve_fullpage()
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
        include = [normalize_tag(t.strip()) for t in params.get("include", []) if t.strip()]
        exclude = [normalize_tag(t.strip()) for t in params.get("exclude", []) if t.strip()]
        limit = int(params.get("limit", ["50"])[0])
        offset = int(params.get("offset", ["0"])[0])
        # Filtre par type : file, email, note, vault, video (comma-separated)
        types_raw = params.get("types", [""])[0].strip()
        active_types = set(t.strip() for t in types_raw.split(",") if t.strip()) if types_raw else set()

        if not include and not active_types:
            return {"results": [], "total": 0}

        conn = get_db()
        c = conn.cursor()

        if include:
            # Items qui ont TOUS les tags inclus
            placeholders_inc = ",".join("?" * len(include))
            query = f"""
                SELECT t.item_id
                FROM tags t
                WHERE t.tag IN ({placeholders_inc})
                GROUP BY t.item_id
                HAVING COUNT(DISTINCT t.tag) = ?
            """
            query_params = list(include) + [len(include)]

            # Exclure les items qui ont un tag exclu
            if exclude:
                placeholders_exc = ",".join("?" * len(exclude))
                query = f"""
                    SELECT item_id FROM ({query})
                    WHERE item_id NOT IN (
                        SELECT item_id FROM tags WHERE tag IN ({placeholders_exc})
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
            c.execute(f"""
                SELECT id, nom, extension, chemin_relatif, taille, est_dossier, date_modif
                FROM items WHERE id IN ({ph})
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

        # Trier par date desc et paginer
        results.sort(key=lambda r: r.get("date_modif", ""), reverse=True)
        page = results[offset:offset + limit]

        conn.close()
        return {"results": page, "total": total}

    def handle_cooccurrence(self, params):
        """Tags co-occurrents : les tags les plus fréquents parmi les items qui matchent."""
        include = [t.lower().strip() for t in params.get("include", []) if t.strip()]
        exclude = [t.lower().strip() for t in params.get("exclude", []) if t.strip()]
        types_raw = params.get("types", [""])[0].strip()
        active_types = set(t.strip() for t in types_raw.split(",") if t.strip()) if types_raw else set()

        if not include and not active_types:
            return {"tags": []}

        conn = get_db()
        c = conn.cursor()

        if include:
            # Items qui ont tous les tags inclus
            placeholders_inc = ",".join("?" * len(include))
            items_query = f"""
                SELECT t.item_id
                FROM tags t
                WHERE t.tag IN ({placeholders_inc})
                GROUP BY t.item_id
                HAVING COUNT(DISTINCT t.tag) = ?
            """
            items_params = list(include) + [len(include)]

            # Exclure
            if exclude:
                placeholders_exc = ",".join("?" * len(exclude))
                items_query = f"""
                    SELECT item_id FROM ({items_query})
                    WHERE item_id NOT IN (
                        SELECT item_id FROM tags WHERE tag IN ({placeholders_exc})
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
        all_selected = set(include) | set(exclude)
        if all_selected:
            all_placeholders = ",".join("?" * len(all_selected))
            cooc_query = f"""
                SELECT t2.tag, COUNT(*) as cnt
                FROM tags t2
                WHERE t2.item_id IN ({items_query})
                  AND t2.tag NOT IN ({all_placeholders})
                GROUP BY t2.tag
                ORDER BY cnt DESC
                LIMIT 15
            """
            c.execute(cooc_query, items_params + list(all_selected))
        else:
            cooc_query = f"""
                SELECT t2.tag, COUNT(*) as cnt
                FROM tags t2
                WHERE t2.item_id IN ({items_query})
                GROUP BY t2.tag
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

        # Vérifier que l'item existe
        c.execute("SELECT id FROM items WHERE id = ?", (item_id,))
        if not c.fetchone():
            conn.close()
            return {"error": "Item introuvable"}

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
            "/api/event": self.handle_event_delete,
            "/api/contact": self.handle_contact_delete,
            "/api/lieu": self.handle_lieu_delete,
            "/api/relation": self.handle_relation_delete,
            "/api/tags/delete": self.handle_tags_delete,
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
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM tags WHERE item_id = ? AND tag = 'favori'", (item_id,))
        exists = c.fetchone()[0] > 0
        if exists:
            c.execute("DELETE FROM tags WHERE item_id = ? AND tag = 'favori'", (item_id,))
        else:
            c.execute("INSERT INTO tags (item_id, tag) VALUES (?, 'favori')", (item_id,))
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
        conn = get_db()
        c = conn.cursor()
        ph = ",".join("?" * len(ids))
        c.execute(f"SELECT DISTINCT item_id FROM tags WHERE item_id IN ({ph}) AND tag = 'favori'", ids)
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

    def log_message(self, format, *args):
        """Log simplifié."""
        print(f"[SEARCH] {args[0]}")


def main():
    print(f"=== BIG_BOFF Search — Serveur ===")
    print(f"Base : {DB_PATH}")
    print(f"Port : {PORT}")
    print(f"URL  : http://{HOST}:{PORT}")
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
