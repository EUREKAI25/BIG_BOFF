#!/usr/bin/env python3
"""
EURKAI — Module ménage-local : Hash SHA256 (second pass)
Lit la base catalogue.db existante, hashe les fichiers locaux (taille > 0, < 50 Mo),
met à jour la base, relance la détection de doublons exacts, et met à jour le rapport.
"""

import os
import sys
import sqlite3
import hashlib
import signal
from datetime import datetime

DB_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db"
DROPBOX_ROOT = "/Users/nathalie/Dropbox"
MAX_SIZE = 50 * 1024 * 1024  # 50 Mo max


class HashTimeout(Exception):
    pass

def timeout_handler(signum, frame):
    raise HashTimeout("Timeout")


def hash_file(path):
    """Hash SHA256 d'un fichier."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError, HashTimeout):
        return None


def main():
    print("=== EURKAI — Hash SHA256 (second pass) ===")
    print(f"Base : {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Compter les fichiers à hasher
    c.execute("""
        SELECT COUNT(*) FROM items
        WHERE est_dossier = 0
          AND taille > 0
          AND taille <= ?
          AND (hash_sha256 IS NULL OR hash_sha256 = '')
    """, (MAX_SIZE,))
    total = c.fetchone()[0]
    print(f"Fichiers à hasher : {total} (taille entre 1 o et {MAX_SIZE // (1024*1024)} Mo)")

    # Fichiers trop gros (info)
    c.execute("""
        SELECT COUNT(*), COALESCE(SUM(taille), 0) FROM items
        WHERE est_dossier = 0 AND taille > ?
    """, (MAX_SIZE,))
    big_count, big_size = c.fetchone()
    print(f"Fichiers > 50 Mo (exclus du hash) : {big_count} ({big_size / (1024*1024):.0f} Mo)")

    # Fichiers vides / cloud-only (info)
    c.execute("SELECT COUNT(*) FROM items WHERE est_dossier = 0 AND (taille = 0 OR taille IS NULL)")
    empty = c.fetchone()[0]
    print(f"Fichiers vides/cloud-only (exclus) : {empty}\n")

    # Récupérer la liste des fichiers à hasher
    c.execute("""
        SELECT id, chemin FROM items
        WHERE est_dossier = 0
          AND taille > 0
          AND taille <= ?
          AND (hash_sha256 IS NULL OR hash_sha256 = '')
        ORDER BY taille ASC
    """, (MAX_SIZE,))
    rows = c.fetchall()

    hashed = 0
    errors = 0
    for i, (item_id, path) in enumerate(rows):
        # Timeout de 5 secondes par fichier
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)

        try:
            file_hash = hash_file(path)
            signal.alarm(0)

            if file_hash:
                c.execute("UPDATE items SET hash_sha256 = ? WHERE id = ?", (file_hash, item_id))
                hashed += 1
            else:
                errors += 1
        except HashTimeout:
            signal.alarm(0)
            errors += 1
        except Exception:
            signal.alarm(0)
            errors += 1

        if (i + 1) % 1000 == 0:
            conn.commit()
            pct = (i + 1) / total * 100
            print(f"  ... {i + 1}/{total} ({pct:.0f}%) — {hashed} hashés, {errors} erreurs", flush=True)

    conn.commit()
    print(f"\n  Résultat : {hashed} hashés, {errors} erreurs sur {total} fichiers\n")

    # Détection de doublons exacts par hash
    print("Détection des doublons exacts (hash)...")
    c.execute("DELETE FROM doublons WHERE type_doublon = 'exact-hash'")

    c.execute("""
        SELECT hash_sha256, GROUP_CONCAT(chemin_relatif, '|||'), COUNT(*)
        FROM items
        WHERE hash_sha256 IS NOT NULL AND hash_sha256 <> ''
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

    conn.commit()
    print(f"  → {hash_dupes} paires de doublons exacts détectées\n")

    # Résumé
    c.execute("SELECT COUNT(*) FROM items WHERE hash_sha256 IS NOT NULL AND hash_sha256 <> ''")
    total_hashed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM doublons WHERE type_doublon = 'exact-hash'")
    total_dupes = c.fetchone()[0]

    print(f"=== RÉSUMÉ ===")
    print(f"Total fichiers hashés dans la base : {total_hashed}")
    print(f"Total doublons exacts : {total_dupes} paires")

    conn.close()
    print("\nTerminé !")


if __name__ == "__main__":
    main()
