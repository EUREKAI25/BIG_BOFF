#!/usr/bin/env python3
"""
Supprime tous les tags qui sont des adjectifs de la base de données.
À exécuter une seule fois pour nettoyer la base existante.
"""

import sqlite3
from config import DB_PATH, filter_adjectives

def main():
    print("=== Nettoyage des adjectifs dans la base ===\n")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Récupérer tous les tags uniques (tag_display)
    print("📊 Chargement des tags uniques...")
    c.execute("SELECT DISTINCT tag_display FROM tags WHERE tag_display IS NOT NULL")
    all_tags = [row[0] for row in c.fetchall()]
    print(f"  → {len(all_tags):,} tags uniques trouvés")

    # Filtrer les adjectifs (on garde les non-adjectifs)
    print("\n🔍 Détection des adjectifs via POS tagging...")
    non_adjectives = set(filter_adjectives(all_tags))
    adjectives = [tag for tag in all_tags if tag not in non_adjectives]

    print(f"  → {len(adjectives):,} adjectifs détectés")

    if adjectives:
        print("\n📝 Exemples d'adjectifs détectés (10 premiers) :")
        for adj in sorted(adjectives)[:10]:
            print(f"    • {adj}")

    # Supprimer les tags adjectifs
    if adjectives:
        print(f"\n🗑️  Suppression de {len(adjectives):,} adjectifs...")
        placeholders = ','.join('?' * len(adjectives))
        c.execute(f"DELETE FROM tags WHERE tag_display IN ({placeholders})", adjectives)
        deleted = c.rowcount
        conn.commit()
        print(f"  → {deleted:,} lignes supprimées")
    else:
        print("\n✨ Aucun adjectif à supprimer")

    # Stats finales
    c.execute("SELECT COUNT(*) FROM tags")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT tag) FROM tags")
    unique = c.fetchone()[0]

    print(f"\n✅ Terminé !")
    print(f"  Total tags restants : {total:,}")
    print(f"  Tags uniques restants : {unique:,}")

    conn.close()

if __name__ == "__main__":
    main()
