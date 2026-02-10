#!/usr/bin/env python3
"""
Migration : applique le stemming français à tous les tags existants.
Fusionne les déclinaisons (chercher/cherche/cherché → cherch).
"""

import sqlite3
from config import DB_PATH, normalize_tag

def main():
    print("=== Migration stemming ===")
    print(f"Base : {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Stats avant
    c.execute("SELECT COUNT(DISTINCT tag) FROM tags")
    before_tags = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tags")
    before_assoc = c.fetchone()[0]

    print(f"Avant : {before_tags} tags distincts, {before_assoc} associations")

    # Charger tous les tags existants
    c.execute("SELECT DISTINCT tag FROM tags")
    all_tags = [row[0] for row in c.fetchall()]

    # Calculer les normalisations
    mappings = {}  # old_tag → new_tag
    for tag in all_tags:
        normalized = normalize_tag(tag)
        if normalized != tag:
            mappings[tag] = normalized

    if not mappings:
        print("Aucun tag à normaliser.")
        conn.close()
        return

    print(f"Tags à normaliser : {len(mappings)}")
    print("\nExemples :")
    for old, new in list(mappings.items())[:10]:
        print(f"  {old:20} → {new}")

    # Appliquer la migration par batch
    batch_size = 1000
    processed = 0

    for old_tag, new_tag in mappings.items():
        # Réassigner toutes les associations old_tag → new_tag
        # Éviter les doublons : INSERT uniquement si (item_id, new_tag) n'existe pas déjà
        c.execute("""
            INSERT INTO tags (item_id, tag)
            SELECT item_id, ? FROM tags
            WHERE tag = ?
            AND item_id NOT IN (SELECT item_id FROM tags WHERE tag = ?)
        """, (new_tag, old_tag, new_tag))

        # Supprimer l'ancien tag
        c.execute("DELETE FROM tags WHERE tag = ?", (old_tag,))

        processed += 1
        if processed % batch_size == 0:
            conn.commit()
            print(f"  ... {processed}/{len(mappings)} tags migrés")

    conn.commit()

    # Stats après
    c.execute("SELECT COUNT(DISTINCT tag) FROM tags")
    after_tags = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tags")
    after_assoc = c.fetchone()[0]

    print(f"\n=== RÉSULTAT ===")
    print(f"Avant : {before_tags} tags distincts, {before_assoc} associations")
    print(f"Après : {after_tags} tags distincts, {after_assoc} associations")
    print(f"Fusion : {before_tags - after_tags} tags ({100*(before_tags-after_tags)/before_tags:.1f}%)")
    print(f"Associations économisées : {before_assoc - after_assoc}")

    # VACUUM pour récupérer l'espace
    print("\nVACUUM...")
    conn.execute("VACUUM")
    conn.close()
    print("Terminé !")


if __name__ == "__main__":
    main()
