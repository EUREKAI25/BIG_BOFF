#!/usr/bin/env python3
"""
Nettoie les tags de paramètres URL bruités (fbclid, mibextid, etc.)
"""

import sqlite3
from config import DB_PATH

# Paramètres URL à supprimer
URL_PARAMS = {
    "fbclid", "mibextid", "igshid", "igsh",
    "gclid", "gbraid", "wbraid", "msclkid",
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "utm", "ref", "source", "campaign", "medium",
}

def main():
    print("=== Nettoyage des tags de paramètres URL ===")
    print(f"Base : {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Compter les tags à supprimer
    placeholders = ','.join('?' * len(URL_PARAMS))
    c.execute(f"SELECT COUNT(*) FROM tags WHERE tag IN ({placeholders})", tuple(URL_PARAMS))
    total = c.fetchone()[0]

    if total == 0:
        print("✓ Aucun tag bruité trouvé !")
        conn.close()
        return

    print(f"Tags bruités à supprimer : {total}")

    # Lister les tags concernés
    c.execute(f"SELECT tag, COUNT(*) as cnt FROM tags WHERE tag IN ({placeholders}) GROUP BY tag ORDER BY cnt DESC", tuple(URL_PARAMS))
    for tag, cnt in c.fetchall():
        print(f"  - {tag}: {cnt}")

    # Supprimer
    c.execute(f"DELETE FROM tags WHERE tag IN ({placeholders})", tuple(URL_PARAMS))
    conn.commit()

    print(f"\n✓ {total} tags supprimés")
    conn.close()


if __name__ == "__main__":
    main()
