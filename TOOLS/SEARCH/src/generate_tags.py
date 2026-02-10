#!/usr/bin/env python3
"""
BIG_BOFF Search — Génération des tags atomiques
Lit catalogue.db, extrait les tags de chaque item, les insère dans la table tags.
Tags atomiques : 1 mot = 1 tag. Pas de tags composés.
"""

import sqlite3
import os
import re
from pathlib import Path

from config import (
    DB_PATH, STOP_WORDS, TAGS_3_WHITELIST, EXCLUDED_EXTENSIONS,
    is_valid_tag, should_index_path, normalize_tag,
)

# Extensions → tags de type et format
EXT_TAGS = {
    ".py": ["code", "script", "python"],
    ".js": ["code", "script", "javascript"],
    ".jsx": ["code", "script", "javascript", "react"],
    ".ts": ["code", "script", "typescript"],
    ".tsx": ["code", "script", "typescript", "react"],
    ".html": ["code", "web", "html"],
    ".htm": ["code", "web", "html"],
    ".css": ["code", "web", "css"],
    ".scss": ["code", "web", "css"],
    ".php": ["code", "script", "php"],
    ".sh": ["code", "script", "shell"],
    ".bash": ["code", "script", "shell"],
    ".sql": ["code", "script", "sql"],
    ".vue": ["code", "script", "vue"],
    ".swift": ["code", "swift"],
    ".go": ["code", "go"],
    ".rb": ["code", "ruby"],
    ".java": ["code", "java"],
    ".c": ["code", "c"],
    ".cpp": ["code", "c"],
    ".rs": ["code", "rust"],
    ".r": ["code", "r"],
    ".md": ["doc", "markdown"],
    ".txt": ["doc", "texte"],
    ".rtf": ["doc", "texte"],
    ".pdf": ["doc", "pdf"],
    ".doc": ["doc", "word"],
    ".docx": ["doc", "word"],
    ".xls": ["doc", "excel", "tableur"],
    ".xlsx": ["doc", "excel", "tableur"],
    ".ppt": ["doc", "presentation"],
    ".pptx": ["doc", "presentation"],
    ".pages": ["doc", "pages"],
    ".numbers": ["doc", "tableur"],
    ".key": ["doc", "presentation"],
    ".json": ["data", "json"],
    ".csv": ["data", "csv", "tableur"],
    ".xml": ["data", "xml"],
    ".yaml": ["data", "yaml", "config"],
    ".yml": ["data", "yaml", "config"],
    ".toml": ["data", "config"],
    ".env": ["config"],
    ".ini": ["config"],
    ".plist": ["config"],
    ".jpg": ["media", "image", "jpg"],
    ".jpeg": ["media", "image", "jpg"],
    ".png": ["media", "image", "png"],
    ".gif": ["media", "image", "gif"],
    ".svg": ["media", "image", "svg", "vecteur"],
    ".webp": ["media", "image", "webp"],
    ".bmp": ["media", "image"],
    ".tiff": ["media", "image"],
    ".ico": ["media", "image", "icone"],
    ".psd": ["media", "image", "photoshop"],
    ".ai": ["media", "image", "illustrator", "vecteur"],
    ".mp4": ["media", "video", "mp4"],
    ".avi": ["media", "video"],
    ".mov": ["media", "video", "mov"],
    ".mkv": ["media", "video"],
    ".webm": ["media", "video"],
    ".m4v": ["media", "video"],
    ".flv": ["media", "video"],
    ".prproj": ["media", "video", "premiere"],
    ".mp3": ["media", "audio", "mp3"],
    ".wav": ["media", "audio"],
    ".flac": ["media", "audio"],
    ".m4a": ["media", "audio"],
    ".ogg": ["media", "audio"],
    ".wma": ["media", "audio"],
    ".zip": ["archive", "zip"],
    ".rar": ["archive", "rar"],
    ".7z": ["archive"],
    ".tar": ["archive"],
    ".gz": ["archive"],
    ".dmg": ["archive", "dmg"],
    ".ttf": ["ressource", "font"],
    ".otf": ["ressource", "font"],
    ".woff": ["ressource", "font", "web"],
    ".woff2": ["ressource", "font", "web"],
    ".jsx": ["code", "script", "react"],
}


def split_filename(name):
    """Découpe un nom de fichier en mots-clefs.

    Retourne une liste de tuples (tag_display, tag_normalized).
    """
    stem = Path(name).stem
    parts = re.split(r'[-_.\s()\[\]{}]+', stem)
    expanded = []
    for part in parts:
        words = re.sub(r'([a-z])([A-Z])', r'\1 \2', part).split()
        expanded.extend(words)
    tags = []
    for w in expanded:
        w_lower = w.lower().strip()
        if is_valid_tag(w_lower):
            tags.append((w_lower, normalize_tag(w_lower)))
    return tags


def extract_path_tags(rel_path):
    """Extrait les tags depuis chaque composant du chemin.

    Retourne une liste de tuples (tag_display, tag_normalized).
    """
    tags = []
    parts = Path(rel_path).parts
    for part in parts[:-1]:
        clean = part.strip("_").lower()
        for word in re.split(r'[-_.\s]+', clean):
            word = word.strip()
            if is_valid_tag(word):
                tags.append((word, normalize_tag(word)))
    return tags


def generate_tags_for_item(name, ext, rel_path, is_dir):
    """Génère tous les tags pour un item.

    Retourne une liste de tuples (tag_display, tag_normalized).
    """
    tags = []

    # 1. Tags depuis le chemin
    tags.extend(extract_path_tags(rel_path))

    # 2. Tags depuis le nom de fichier
    tags.extend(split_filename(name))

    # 3. Tags depuis l'extension (whitelistés, pas de normalisation)
    if ext and ext.lower() in EXT_TAGS:
        for t in EXT_TAGS[ext.lower()]:
            tags.append((t, t))  # display = normalized pour les tags whitelistés

    # Dédupliquer par tag normalisé (garder la première occurrence pour display)
    seen = {}
    unique_tags = []
    for display, normalized in tags:
        if normalized not in seen:
            seen[normalized] = display
            unique_tags.append((display, normalized))

    return unique_tags


def main():
    print("=== BIG_BOFF Search — Génération des tags ===")
    print(f"Base : {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Créer la table tags (drop si existe)
    c.execute("DROP TABLE IF EXISTS tags")
    c.execute("""
        CREATE TABLE tags (
            item_id INTEGER,
            tag TEXT,
            tag_display TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    c.execute("CREATE INDEX idx_tag ON tags(tag)")
    c.execute("CREATE INDEX idx_tag_display ON tags(tag_display)")
    c.execute("CREATE INDEX idx_tag_item ON tags(item_id)")

    # Lire tous les items
    c.execute("SELECT id, nom, extension, chemin_relatif, est_dossier FROM items")
    rows = c.fetchall()
    print(f"Items à tagger : {len(rows)}")

    batch = []
    skipped = 0
    for i, (item_id, name, ext, rel_path, is_dir) in enumerate(rows):
        # Exclure les chemins parasites et extensions inutiles
        rp = rel_path or ""
        ex = (ext or "").lower()
        if not should_index_path(rp) or ex in EXCLUDED_EXTENSIONS:
            skipped += 1
            continue
        tags = generate_tags_for_item(name, ext or "", rp, is_dir)
        for tag_display, tag_normalized in tags:
            batch.append((item_id, tag_normalized, tag_display))

        if (i + 1) % 5000 == 0:
            c.executemany("INSERT INTO tags (item_id, tag, tag_display) VALUES (?, ?, ?)", batch)
            conn.commit()
            batch = []
            print(f"  ... {i + 1}/{len(rows)} items taggés")

    # Insérer le reste
    if batch:
        c.executemany("INSERT INTO tags (item_id, tag, tag_display) VALUES (?, ?, ?)", batch)
        conn.commit()

    # Stats
    c.execute("SELECT COUNT(*) FROM tags")
    total_tags = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT tag) FROM tags")
    unique_tags = c.fetchone()[0]
    c.execute("SELECT tag, COUNT(*) as cnt FROM tags GROUP BY tag ORDER BY cnt DESC LIMIT 20")
    top_tags = c.fetchall()

    print(f"\n=== RÉSULTAT ===")
    print(f"Items exclus (cache/dist/vendor/map) : {skipped}")
    print(f"Total entrées tags : {total_tags}")
    print(f"Tags uniques : {unique_tags}")
    print(f"\nTop 20 tags :")
    for tag, cnt in top_tags:
        print(f"  {tag:20s} {cnt}")

    conn.close()
    print("\nTerminé !")


if __name__ == "__main__":
    main()
