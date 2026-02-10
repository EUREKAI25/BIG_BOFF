#!/usr/bin/env python3
"""
EURKAI — Module ménage-local : Catalogue automatique
Scanne le Dropbox, tague, détecte doublons et fichiers à jeter.
Produit une base SQLite + un rapport Markdown.
"""

import os
import sys
import sqlite3
import hashlib
import json
import signal
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Timeout")


# === CONFIGURATION ===

DROPBOX_ROOT = "/Users/nathalie/Dropbox"
DB_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db"
REPORT_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/rapport_catalogue.md"

# Dossiers à ignorer complètement
SKIP_DIRS = {
    ".dropbox", ".dropbox.cache", ".Spotlight-V100", ".fseventsd",
    ".Trashes", "__pycache__", "node_modules", ".git", ".svn",
    ".DS_Store", "@eaDir", ".vscode", ".idea",
    # Environnements Python / dépendances (parasites pour l'inventaire)
    "venv", ".venv", "env", ".env", "site-packages", "dist-packages",
    # Autres dépendances
    "bower_components", ".cache", ".npm", ".yarn",
}

# Fichiers système à ignorer
SKIP_FILES = {".DS_Store", "Thumbs.db", "desktop.ini", ".localized", "Icon\r"}

# === EXTENSIONS → TYPE ===

EXT_MAP = {
    # Code
    ".py": "code-python", ".js": "code-js", ".ts": "code-typescript",
    ".jsx": "code-jsx", ".tsx": "code-tsx", ".vue": "code-vue",
    ".html": "code-html", ".htm": "code-html", ".css": "code-css",
    ".scss": "code-scss", ".less": "code-less",
    ".php": "code-php", ".rb": "code-ruby", ".java": "code-java",
    ".sh": "script-shell", ".bash": "script-shell", ".zsh": "script-shell",
    ".bat": "script-batch", ".ps1": "script-powershell",
    ".sql": "code-sql", ".r": "code-r", ".swift": "code-swift",
    ".go": "code-go", ".rs": "code-rust", ".c": "code-c", ".cpp": "code-cpp",
    # Documents
    ".md": "doc-markdown", ".txt": "doc-texte", ".rtf": "doc-rtf",
    ".pdf": "doc-pdf", ".doc": "doc-word", ".docx": "doc-word",
    ".xls": "doc-excel", ".xlsx": "doc-excel",
    ".ppt": "doc-powerpoint", ".pptx": "doc-powerpoint",
    ".odt": "doc-libreoffice", ".ods": "doc-libreoffice",
    ".pages": "doc-pages", ".numbers": "doc-numbers", ".key": "doc-keynote",
    # Data
    ".json": "data-json", ".csv": "data-csv", ".xml": "data-xml",
    ".yaml": "data-yaml", ".yml": "data-yaml", ".toml": "data-toml",
    ".env": "config-env", ".ini": "config-ini", ".cfg": "config-ini",
    ".plist": "config-plist",
    # Media - Images
    ".jpg": "media-image", ".jpeg": "media-image", ".png": "media-image",
    ".gif": "media-image", ".svg": "media-image", ".webp": "media-image",
    ".bmp": "media-image", ".tiff": "media-image", ".ico": "media-image",
    ".psd": "media-image-psd", ".ai": "media-image-ai",
    ".sketch": "media-image-sketch", ".fig": "media-image-figma",
    # Media - Video
    ".mp4": "media-video", ".avi": "media-video", ".mov": "media-video",
    ".mkv": "media-video", ".flv": "media-video", ".wmv": "media-video",
    ".webm": "media-video", ".m4v": "media-video",
    ".prproj": "media-video-projet", ".aep": "media-video-projet",
    # Media - Audio
    ".mp3": "media-audio", ".wav": "media-audio", ".flac": "media-audio",
    ".aac": "media-audio", ".ogg": "media-audio", ".m4a": "media-audio",
    ".wma": "media-audio",
    # Archives
    ".zip": "archive-zip", ".rar": "archive-rar", ".7z": "archive-7z",
    ".tar": "archive-tar", ".gz": "archive-gz", ".bz2": "archive-bz2",
    ".dmg": "archive-dmg",
    # Config / Package
    ".lock": "config-lock",
    # Fonts
    ".ttf": "ressource-font", ".otf": "ressource-font", ".woff": "ressource-font",
    ".woff2": "ressource-font",
}

# Noms de fichiers spéciaux
SPECIAL_FILES = {
    "package.json": "config-npm",
    "package-lock.json": "config-npm-lock",
    "tsconfig.json": "config-typescript",
    "webpack.config.js": "config-webpack",
    "vite.config.js": "config-vite", "vite.config.ts": "config-vite",
    ".gitignore": "config-git",
    ".eslintrc": "config-eslint", ".eslintrc.json": "config-eslint",
    ".prettierrc": "config-prettier",
    "Dockerfile": "config-docker", "docker-compose.yml": "config-docker",
    "Makefile": "config-make",
    "README.md": "doc-readme",
    "_SUIVI.md": "suivi-projet",
    "_HUB.md": "hub-central",
    "Claude.md": "contrat-claude",
}

# === DOMAINES (basés sur le chemin) ===

def detect_domaine(path_rel):
    """Détecte le domaine en fonction du chemin relatif."""
    p = path_rel.lower()
    tags = []
    if "projets/pro" in p:
        tags.append("pro")
    elif "projets/perso" in p:
        tags.append("perso")
    if "eurkai" in p or "eurekai" in p or "erk_" in p or "erk-" in p:
        tags.append("eurkai")
    if "sublym" in p:
        tags.append("sublym")
    if "lanostrai" in p or "lns" in p:
        tags.append("eurkai-ancien")
    if "aloha" in p:
        tags.append("eurkai-ancien")
    if "likidia" in p:
        tags.append("eurkai-ancien")
    if "genesia" in p:
        tags.append("eurkai-ancien")
    if "alchimie" in p:
        tags.append("eurkai-ancien")
    if "ex nihilo" in p or "exnihilo" in p:
        tags.append("eurkai-ancien")
    if "resources/" in p:
        tags.append("ressource")
    if "tools/" in p or "interagents/" in p:
        tags.append("infra")
    if "claude/" in p:
        tags.append("infra")
    if "chats/" in p or "conversations_chatgpt/" in p:
        tags.append("historique-ia")
    if "archive" in p:
        tags.append("archive")
    return tags


def detect_type_fichier(name, ext):
    """Détecte le type d'un fichier."""
    name_lower = name.lower()
    # Fichiers spéciaux d'abord
    if name in SPECIAL_FILES:
        return SPECIAL_FILES[name]
    # Par extension
    if ext.lower() in EXT_MAP:
        return EXT_MAP[ext.lower()]
    # Heuristiques
    if name_lower.startswith("tree-") and ext == ".md":
        return "doc-arborescence"
    if name_lower.startswith("readme"):
        return "doc-readme"
    return "inconnu"


def detect_flags(name, ext, size, path_rel, is_dir):
    """Détecte les flags d'alerte (à jeter, copie, etc.)."""
    flags = []
    name_lower = name.lower()

    # Copies manuelles
    if " copie" in name_lower or " copy" in name_lower:
        flags.append("copie-manuelle")
    if name_lower.endswith(" 2") or name_lower.endswith(" 3") or name_lower.endswith(" 4"):
        flags.append("copie-probable")

    # Archives qui doublent un dossier
    base_no_ext = Path(name).stem
    if ext.lower() in (".zip", ".rar", ".7z", ".tar", ".gz"):
        flags.append("archive-backup")

    # Fichiers (presque) vides
    if not is_dir and size is not None:
        if size == 0:
            flags.append("fichier-vide")
        elif size < 50:
            flags.append("fichier-quasi-vide")

    # Dossiers à noms suspects
    if is_dir:
        if name_lower in ("new", "restart", "test", "temp", "tmp", "old"):
            flags.append("nom-générique")

    # Noms avec numéros qui sentent la version
    for pattern in (" 2.zip", " 3.zip", " 2.rar"):
        if name_lower.endswith(pattern):
            flags.append("backup-numéroté")

    # Fichiers de build/cache
    if name_lower in ("package-lock.json", ".eslintcache"):
        flags.append("généré-auto")

    return flags


# === BASE DE DONNÉES ===

def init_db(db_path):
    """Crée la base SQLite."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS items")
    c.execute("DROP TABLE IF EXISTS doublons")
    c.execute("""
        CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chemin TEXT UNIQUE,
            chemin_relatif TEXT,
            nom TEXT,
            extension TEXT,
            est_dossier INTEGER,
            taille INTEGER,
            date_modif TEXT,
            type_fichier TEXT,
            domaines TEXT,
            flags TEXT,
            hash_sha256 TEXT,
            profondeur INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE doublons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            groupe TEXT,
            type_doublon TEXT,
            chemin1 TEXT,
            chemin2 TEXT,
            nom TEXT,
            taille INTEGER
        )
    """)
    c.execute("CREATE INDEX idx_nom ON items(nom)")
    c.execute("CREATE INDEX idx_type ON items(type_fichier)")
    c.execute("CREATE INDEX idx_taille ON items(taille)")
    c.execute("CREATE INDEX idx_hash ON items(hash_sha256)")
    conn.commit()
    return conn


# === SCAN ===

def hash_file(path, max_size=50 * 1024 * 1024):
    """Hash SHA256 d'un fichier (skip si > max_size ou inaccessible)."""
    try:
        size = os.path.getsize(path)
        if size > max_size or size == 0:
            return None
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def scan_dropbox(root, conn):
    """Scanne l'arborescence et remplit la base."""
    c = conn.cursor()
    count = 0
    errors = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Filtrer les dossiers à ignorer
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        rel_dir = os.path.relpath(dirpath, root)
        depth = rel_dir.count(os.sep) if rel_dir != "." else 0

        # Enregistrer le dossier lui-même (sauf la racine)
        if dirpath != root:
            dirname = os.path.basename(dirpath)
            domaines = detect_domaine(rel_dir)
            flags = detect_flags(dirname, "", None, rel_dir, True)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(dirpath)).strftime("%Y-%m-%d")
            except OSError:
                mtime = None

            try:
                c.execute("""
                    INSERT OR IGNORE INTO items
                    (chemin, chemin_relatif, nom, extension, est_dossier, taille,
                     date_modif, type_fichier, domaines, flags, profondeur)
                    VALUES (?, ?, ?, ?, 1, NULL, ?, 'dossier', ?, ?, ?)
                """, (
                    dirpath, rel_dir, dirname, "",
                    mtime,
                    ",".join(domaines) if domaines else "",
                    ",".join(flags) if flags else "",
                    depth
                ))
            except Exception as e:
                errors += 1

        # Enregistrer les fichiers
        for fname in filenames:
            if fname in SKIP_FILES:
                continue

            fpath = os.path.join(dirpath, fname)
            frel = os.path.relpath(fpath, root)
            ext = os.path.splitext(fname)[1]

            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(3)  # 3 secondes max par fichier
                stat = os.stat(fpath)
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                signal.alarm(0)
            except (OSError, TimeoutError):
                signal.alarm(0)
                size = None
                mtime = None

            ftype = detect_type_fichier(fname, ext)
            domaines = detect_domaine(frel)
            flags = detect_flags(fname, ext, size, frel, False)

            # Hash désactivé pour cette passe (trop lent avec les fichiers cloud)
            # Sera fait dans un second temps sur les fichiers locaux uniquement
            file_hash = None

            try:
                c.execute("""
                    INSERT OR IGNORE INTO items
                    (chemin, chemin_relatif, nom, extension, est_dossier, taille,
                     date_modif, type_fichier, domaines, flags, hash_sha256, profondeur)
                    VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fpath, frel, fname, ext,
                    size, mtime, ftype,
                    ",".join(domaines) if domaines else "",
                    ",".join(flags) if flags else "",
                    file_hash,
                    depth + 1
                ))
                count += 1
            except Exception as e:
                errors += 1

        if count % 500 == 0 and count > 0:
            conn.commit()
            print(f"  ... {count} fichiers scannés", flush=True)

    conn.commit()
    return count, errors


# === DÉTECTION DE DOUBLONS ===

def detect_doublons(conn):
    """Détecte les doublons exacts (hash) et probables (nom+taille)."""
    c = conn.cursor()

    # Doublons exacts par hash
    c.execute("""
        SELECT hash_sha256, GROUP_CONCAT(chemin_relatif, '|||'), COUNT(*)
        FROM items
        WHERE hash_sha256 IS NOT NULL AND hash_sha256 != ''
        GROUP BY hash_sha256
        HAVING COUNT(*) > 1
    """)
    hash_dupes = 0
    for row in c.fetchall():
        h, paths_str, cnt = row
        paths = paths_str.split("|||")
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                c.execute("""
                    INSERT INTO doublons (groupe, type_doublon, chemin1, chemin2, nom, taille)
                    SELECT ?, 'exact-hash',
                           a.chemin_relatif, b.chemin_relatif,
                           a.nom, a.taille
                    FROM items a, items b
                    WHERE a.chemin_relatif = ? AND b.chemin_relatif = ?
                """, (h[:12], paths[i], paths[j]))
                hash_dupes += 1

    # Doublons probables : même nom + même taille (fichiers uniquement)
    c.execute("""
        SELECT nom, taille, GROUP_CONCAT(chemin_relatif, '|||'), COUNT(*)
        FROM items
        WHERE est_dossier = 0 AND taille > 100
        GROUP BY nom, taille
        HAVING COUNT(*) > 1
    """)
    name_dupes = 0
    for row in c.fetchall():
        name, size, paths_str, cnt = row
        paths = paths_str.split("|||")
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                c.execute("""
                    INSERT INTO doublons (groupe, type_doublon, chemin1, chemin2, nom, taille)
                    VALUES (?, 'même-nom-taille', ?, ?, ?, ?)
                """, (f"nt-{name[:20]}", paths[i], paths[j], name, size))
                name_dupes += 1

    conn.commit()
    return hash_dupes, name_dupes


# === RAPPORT MARKDOWN ===

def generate_report(conn, report_path, scan_count, scan_errors, hash_dupes, name_dupes):
    """Génère le rapport Markdown."""
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# Rapport de catalogage — {now}\n",
        f"> Scan automatique du Dropbox. Base : `catalogue.db`\n",
        f"## Statistiques globales\n",
    ]

    # Stats globales
    c.execute("SELECT COUNT(*) FROM items WHERE est_dossier = 0")
    total_files = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM items WHERE est_dossier = 1")
    total_dirs = c.fetchone()[0]
    c.execute("SELECT SUM(taille) FROM items WHERE est_dossier = 0 AND taille IS NOT NULL")
    total_size = c.fetchone()[0] or 0

    lines.append(f"| Métrique | Valeur |")
    lines.append(f"|---|---|")
    lines.append(f"| Fichiers scannés | {total_files} |")
    lines.append(f"| Dossiers scannés | {total_dirs} |")
    lines.append(f"| Taille totale (fichiers locaux) | {total_size / (1024*1024):.1f} Mo |")
    lines.append(f"| Doublons exacts (hash) | {hash_dupes} paires |")
    lines.append(f"| Doublons probables (nom+taille) | {name_dupes} paires |")
    lines.append(f"| Erreurs de scan | {scan_errors} |\n")

    # Répartition par type
    lines.append(f"## Répartition par type\n")
    lines.append(f"| Type | Nombre | Taille |")
    lines.append(f"|---|---|---|")
    c.execute("""
        SELECT type_fichier, COUNT(*), COALESCE(SUM(taille), 0)
        FROM items WHERE est_dossier = 0
        GROUP BY type_fichier ORDER BY COUNT(*) DESC
    """)
    for row in c.fetchall():
        t, cnt, sz = row
        lines.append(f"| {t} | {cnt} | {sz / (1024*1024):.1f} Mo |")
    lines.append("")

    # Répartition par domaine
    lines.append(f"## Répartition par domaine\n")
    lines.append(f"| Domaine | Nombre éléments |")
    lines.append(f"|---|---|")
    domain_counts = defaultdict(int)
    c.execute("SELECT domaines FROM items WHERE domaines != ''")
    for row in c.fetchall():
        for d in row[0].split(","):
            if d:
                domain_counts[d] += 1
    for d, cnt in sorted(domain_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {d} | {cnt} |")
    lines.append("")

    # Fichiers flaggés
    lines.append(f"## Éléments flaggés\n")

    flag_types = [
        ("copie-manuelle", "Copies manuelles (mot 'copie' dans le nom)"),
        ("copie-probable", "Copies probables (suffixe numéroté)"),
        ("archive-backup", "Archives/backups (zip, rar...)"),
        ("backup-numéroté", "Backups numérotés (ex: 'truc 2.zip')"),
        ("fichier-vide", "Fichiers vides (0 octets)"),
        ("fichier-quasi-vide", "Fichiers quasi-vides (< 50 octets)"),
        ("nom-générique", "Dossiers à nom générique (new, temp...)"),
        ("généré-auto", "Fichiers générés automatiquement"),
    ]
    for flag, desc in flag_types:
        c.execute(
            "SELECT chemin_relatif, taille FROM items WHERE flags LIKE ? ORDER BY chemin_relatif",
            (f"%{flag}%",)
        )
        rows = c.fetchall()
        if rows:
            lines.append(f"### {desc} ({len(rows)})\n")
            for path, size in rows[:50]:  # max 50 par catégorie
                sz = f" ({size} o)" if size is not None else ""
                lines.append(f"- `{path}`{sz}")
            if len(rows) > 50:
                lines.append(f"- ... et {len(rows) - 50} autres")
            lines.append("")

    # Doublons exacts
    lines.append(f"## Doublons exacts (même hash SHA256)\n")
    c.execute("""
        SELECT chemin1, chemin2, nom, taille FROM doublons
        WHERE type_doublon = 'exact-hash'
        ORDER BY taille DESC
        LIMIT 100
    """)
    rows = c.fetchall()
    if rows:
        lines.append(f"| Fichier | Emplacement 1 | Emplacement 2 | Taille |")
        lines.append(f"|---|---|---|---|")
        for ch1, ch2, nom, taille in rows:
            sz = f"{taille / 1024:.0f} Ko" if taille else "?"
            lines.append(f"| {nom} | `{ch1}` | `{ch2}` | {sz} |")
    else:
        lines.append("Aucun doublon exact détecté (fichiers cloud-only exclus).\n")
    lines.append("")

    # Doublons probables (top 50 par taille)
    lines.append(f"## Doublons probables (même nom + même taille)\n")
    c.execute("""
        SELECT chemin1, chemin2, nom, taille FROM doublons
        WHERE type_doublon = 'même-nom-taille'
        ORDER BY taille DESC
        LIMIT 100
    """)
    rows = c.fetchall()
    if rows:
        lines.append(f"| Fichier | Emplacement 1 | Emplacement 2 | Taille |")
        lines.append(f"|---|---|---|---|")
        for ch1, ch2, nom, taille in rows:
            sz = f"{taille / 1024:.0f} Ko" if taille else "?"
            lines.append(f"| {nom} | `{ch1}` | `{ch2}` | {sz} |")
    else:
        lines.append("Aucun doublon probable détecté.\n")
    lines.append("")

    # Top 20 plus gros fichiers
    lines.append(f"## Top 20 plus gros fichiers\n")
    lines.append(f"| Fichier | Taille | Type | Emplacement |")
    lines.append(f"|---|---|---|---|")
    c.execute("""
        SELECT nom, taille, type_fichier, chemin_relatif FROM items
        WHERE est_dossier = 0 AND taille IS NOT NULL
        ORDER BY taille DESC LIMIT 20
    """)
    for nom, taille, ftype, path in c.fetchall():
        if taille > 1024 * 1024:
            sz = f"{taille / (1024*1024):.1f} Mo"
        else:
            sz = f"{taille / 1024:.0f} Ko"
        lines.append(f"| {nom} | {sz} | {ftype} | `{path}` |")
    lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# === MAIN ===

def main():
    print(f"=== EURKAI — Catalogue automatique ===")
    print(f"Racine : {DROPBOX_ROOT}")
    print(f"Base   : {DB_PATH}")
    print(f"Rapport: {REPORT_PATH}\n")

    print("[1/4] Initialisation de la base...")
    conn = init_db(DB_PATH)

    print("[2/4] Scan de l'arborescence...")
    count, errors = scan_dropbox(DROPBOX_ROOT, conn)
    print(f"  → {count} fichiers, {errors} erreurs\n")

    print("[3/4] Détection des doublons...")
    hash_dupes, name_dupes = detect_doublons(conn)
    print(f"  → {hash_dupes} doublons exacts, {name_dupes} doublons probables\n")

    print("[4/4] Génération du rapport...")
    generate_report(conn, REPORT_PATH, count, errors, hash_dupes, name_dupes)

    conn.close()
    print(f"\nTerminé ! Rapport : {REPORT_PATH}")


if __name__ == "__main__":
    main()
