#!/usr/bin/env python3
"""
BIG_BOFF Search — Indexation du contenu des fichiers
Lit les fichiers texte/code, extrait les identifiants significatifs,
les ajoute comme tags dans catalogue.db.
"""

import sqlite3
import re
import os
import signal
from pathlib import Path

from config import (
    DB_PATH, DROPBOX_ROOT, STOP_WORDS, EXCLUDED_EXTENSIONS,
    is_valid_tag, should_index_path, normalize_tag,
)

# Extensions à indexer et leurs extracteurs
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".php", ".rb", ".go",
    ".swift", ".java", ".c", ".cpp", ".rs", ".sh", ".bash",
    ".vue", ".sql",
}
MARKUP_EXTENSIONS = {".html", ".htm", ".css", ".scss", ".svg"}
TEXT_EXTENSIONS = {".md", ".txt", ".rtf"}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".xml", ".csv", ".env", ".ini"}

ALL_INDEXABLE = CODE_EXTENSIONS | MARKUP_EXTENSIONS | TEXT_EXTENSIONS | CONFIG_EXTENSIONS

# STOP_WORDS importé de config.py (centralisé)
CONTENT_STOP_WORDS = STOP_WORDS

# Taille max d'un fichier à indexer (500 Ko)
MAX_FILE_SIZE = 500_000

# Timeout lecture fichier (secondes)
READ_TIMEOUT = 3


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Lecture trop longue")


# ── Extracteurs par langage ──────────────────────────

def extract_python(content):
    """Extrait les identifiants Python : fonctions, classes, imports, décorateurs."""
    tags = set()

    # def function_name(
    for m in re.finditer(r'\bdef\s+(\w+)\s*\(', content):
        name = m.group(1)
        if not name.startswith('_') or name.startswith('__'):
            tags.add(name.lower())

    # class ClassName
    for m in re.finditer(r'\bclass\s+(\w+)', content):
        tags.add(m.group(1).lower())

    # import module / from module import
    for m in re.finditer(r'\bimport\s+([\w.]+)', content):
        parts = m.group(1).split('.')
        for p in parts:
            if len(p) >= 3:
                tags.add(p.lower())
    for m in re.finditer(r'\bfrom\s+([\w.]+)\s+import', content):
        parts = m.group(1).split('.')
        for p in parts:
            if len(p) >= 3:
                tags.add(p.lower())

    # @decorator
    for m in re.finditer(r'@(\w+)', content):
        tags.add(m.group(1).lower())

    return tags


def extract_javascript(content):
    """Extrait les identifiants JS/TS : fonctions, classes, imports, composants."""
    tags = set()

    # function name( / const name = ( / const name = async (
    for m in re.finditer(r'\bfunction\s+(\w+)', content):
        tags.add(m.group(1).lower())

    # const/let/var Name = / export const Name
    for m in re.finditer(r'\b(?:const|let|var|export)\s+(\w+)\s*=', content):
        name = m.group(1)
        if len(name) >= 3:
            tags.add(name.lower())

    # class ClassName
    for m in re.finditer(r'\bclass\s+(\w+)', content):
        tags.add(m.group(1).lower())

    # import ... from 'module'
    for m in re.finditer(r"""(?:from|require)\s*\(?\s*['"]([^'"]+)['"]""", content):
        mod = m.group(1).split('/')[-1]  # Dernier segment
        mod = mod.replace('.js', '').replace('.ts', '').replace('.jsx', '').replace('.tsx', '')
        if len(mod) >= 3 and not mod.startswith('.'):
            tags.add(mod.lower())

    # React components : <ComponentName
    for m in re.finditer(r'<([A-Z]\w+)', content):
        tags.add(m.group(1).lower())

    # export default
    for m in re.finditer(r'export\s+default\s+(?:class|function)?\s*(\w+)', content):
        tags.add(m.group(1).lower())

    return tags


def extract_html(content):
    """Extrait les identifiants HTML : id, classes, balises personnalisées, meta."""
    tags = set()

    # id="xxx"
    for m in re.finditer(r'\bid=["\']([^"\']+)["\']', content):
        for word in re.split(r'[-_\s]+', m.group(1)):
            if len(word) >= 3:
                tags.add(word.lower())

    # class="xxx yyy"
    for m in re.finditer(r'\bclass=["\']([^"\']+)["\']', content):
        for cls in m.group(1).split():
            for word in re.split(r'[-_]+', cls):
                if len(word) >= 3:
                    tags.add(word.lower())

    # <title>...</title>
    for m in re.finditer(r'<title>([^<]+)</title>', content, re.IGNORECASE):
        for word in re.split(r'[\s\-_,.;:!?]+', m.group(1)):
            if len(word) >= 3:
                tags.add(word.lower())

    # Custom elements / components
    for m in re.finditer(r'<([a-z]+-[a-z-]+)', content):
        for word in m.group(1).split('-'):
            if len(word) >= 3:
                tags.add(word.lower())

    return tags


def extract_css(content):
    """Extrait les identifiants CSS : classes, ids, variables."""
    tags = set()

    # .class-name / #id-name
    for m in re.finditer(r'[.#]([\w-]+)', content):
        for word in re.split(r'[-_]+', m.group(1)):
            if len(word) >= 3:
                tags.add(word.lower())

    # --variable-name
    for m in re.finditer(r'--([\w-]+)', content):
        for word in re.split(r'[-_]+', m.group(1)):
            if len(word) >= 3:
                tags.add(word.lower())

    return tags


def extract_shell(content):
    """Extrait les identifiants Shell : fonctions, variables, commandes."""
    tags = set()

    # function name() or name()
    for m in re.finditer(r'(?:function\s+)?(\w+)\s*\(\)', content):
        tags.add(m.group(1).lower())

    # VARIABLE= ou variable=
    for m in re.finditer(r'\b([A-Z_][A-Z0-9_]{2,})\s*=', content):
        tags.add(m.group(1).lower())

    return tags


def extract_php(content):
    """Extrait les identifiants PHP : fonctions, classes, namespaces."""
    tags = set()

    for m in re.finditer(r'\bfunction\s+(\w+)', content):
        tags.add(m.group(1).lower())
    for m in re.finditer(r'\bclass\s+(\w+)', content):
        tags.add(m.group(1).lower())
    for m in re.finditer(r'\bnamespace\s+([\w\\]+)', content):
        for p in m.group(1).split('\\'):
            if len(p) >= 3:
                tags.add(p.lower())
    for m in re.finditer(r'\buse\s+([\w\\]+)', content):
        parts = m.group(1).split('\\')
        if len(parts[-1]) >= 3:
            tags.add(parts[-1].lower())

    return tags


def extract_sql(content):
    """Extrait les identifiants SQL : tables, colonnes."""
    tags = set()

    for m in re.finditer(r'\b(?:CREATE|ALTER|DROP)\s+TABLE\s+(?:IF\s+\w+\s+)?(\w+)', content, re.IGNORECASE):
        tags.add(m.group(1).lower())
    for m in re.finditer(r'\b(?:FROM|JOIN|INTO|UPDATE)\s+(\w+)', content, re.IGNORECASE):
        name = m.group(1).lower()
        if len(name) >= 3:
            tags.add(name)

    return tags


def extract_text_keywords(content, max_words=30):
    """Extrait les mots-clefs significatifs d'un fichier texte."""
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', content)
    freq = {}
    for w in words:
        w = w.lower()
        if is_valid_tag(w):
            freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: -x[1])
    tags = set()
    for word, count in sorted_words[:max_words]:
        if count >= 2:
            tags.add(word)
    return tags


# ── Dispatch ─────────────────────────────────────────

EXTRACTORS = {
    ".py": extract_python,
    ".js": extract_javascript,
    ".jsx": extract_javascript,
    ".ts": extract_javascript,
    ".tsx": extract_javascript,
    ".vue": extract_javascript,
    ".html": extract_html,
    ".htm": extract_html,
    ".css": extract_css,
    ".scss": extract_css,
    ".sh": extract_shell,
    ".bash": extract_shell,
    ".php": extract_php,
    ".sql": extract_sql,
}


def extract_tags_from_content(content, ext):
    """Extrait les tags depuis le contenu d'un fichier.

    Retourne une liste de tuples (tag_display, tag_normalized).
    """
    tags_raw = set()

    # Extracteur spécialisé si dispo
    extractor = EXTRACTORS.get(ext)
    if extractor:
        tags_raw.update(extractor(content))

    # Pour tous les fichiers texte : mots-clefs fréquents
    if ext in TEXT_EXTENSIONS or ext in CONFIG_EXTENSIONS:
        tags_raw.update(extract_text_keywords(content))

    # Nettoyage + normalisation : garder original + normalisé
    tags = []
    seen = {}
    for t in tags_raw:
        if is_valid_tag(t):
            normalized = normalize_tag(t)
            if normalized not in seen:
                seen[normalized] = t
                tags.append((t, normalized))

    return tags


# ── Main ─────────────────────────────────────────────

def main():
    print("=== BIG_BOFF Search — Indexation du contenu ===")
    print(f"Base : {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Récupérer les fichiers indexables
    ext_list = tuple(ALL_INDEXABLE)
    placeholders = ",".join("?" * len(ext_list))
    c.execute(f"""
        SELECT id, chemin_relatif, extension, taille
        FROM items
        WHERE est_dossier = 0
          AND extension IN ({placeholders})
          AND taille > 0
          AND taille <= ?
    """, ext_list + (MAX_FILE_SIZE,))
    rows = c.fetchall()
    print(f"Fichiers à indexer : {len(rows)}")

    # Configurer timeout
    signal.signal(signal.SIGALRM, timeout_handler)

    indexed = 0
    errors = 0
    batch = []

    for i, (item_id, rel_path, ext, taille) in enumerate(rows):
        # Exclure les chemins parasites
        if not should_index_path(rel_path):
            continue
        full_path = Path(DROPBOX_ROOT) / rel_path
        if not full_path.exists():
            errors += 1
            continue

        try:
            signal.alarm(READ_TIMEOUT)
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            signal.alarm(0)
        except (TimeoutError, PermissionError, OSError):
            signal.alarm(0)
            errors += 1
            continue

        tags = extract_tags_from_content(content, ext.lower())
        if tags:
            for tag_display, tag_normalized in tags:
                batch.append((item_id, tag_normalized, tag_display))
            indexed += 1

        if (i + 1) % 2000 == 0:
            if batch:
                c.executemany("INSERT INTO tags (item_id, tag, tag_display) VALUES (?, ?, ?)", batch)
                conn.commit()
                batch = []
            print(f"  ... {i + 1}/{len(rows)} fichiers ({indexed} indexés, {errors} erreurs)")

    # Insérer le reste
    if batch:
        c.executemany("INSERT INTO tags (item_id, tag, tag_display) VALUES (?, ?, ?)", batch)
        conn.commit()

    # Stats
    c.execute("SELECT COUNT(*) FROM tags")
    total_tags = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT tag) FROM tags")
    unique_tags = c.fetchone()[0]

    print(f"\n=== RÉSULTAT ===")
    print(f"Fichiers indexés : {indexed}")
    print(f"Fichiers non lisibles : {errors}")
    print(f"Total entrées tags (avec contenu) : {total_tags}")
    print(f"Tags uniques (avec contenu) : {unique_tags}")

    # Top nouveaux tags (les plus fréquents parmi ceux ajoutés)
    c.execute("""
        SELECT tag, COUNT(*) as cnt FROM tags
        GROUP BY tag ORDER BY cnt DESC LIMIT 30
    """)
    print(f"\nTop 30 tags :")
    for tag, cnt in c.fetchall():
        print(f"  {tag:25s} {cnt}")

    conn.close()
    print("\nTerminé !")


if __name__ == "__main__":
    main()
