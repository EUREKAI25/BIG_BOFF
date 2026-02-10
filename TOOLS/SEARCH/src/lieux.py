#!/usr/bin/env python3
"""
BIG_BOFF Search — Module Lieux (standalone)
Gestion des lieux avec tags automatiques et lien Google Maps.

Module autonome : importable + CLI.

Usage CLI :
    python3 lieux.py add --nom "Cabinet dentiste" --adresse "12 rue de la Paix, Paris" --tags "dentiste,sante"
    python3 lieux.py search "dentiste"
    python3 lieux.py get --id 1
    python3 lieux.py delete --id 1

API importable :
    from lieux import add_lieu, update_lieu, delete_lieu, get_lieu, search_lieux
"""

import sys
from urllib.parse import quote_plus

from config import (
    ID_OFFSET_LIEU,
    STOP_WORDS,
    extract_keywords,
    get_db,
)


# ── Table ─────────────────────────────────────────────

def setup_lieux_table(conn):
    """Crée la table lieux si elle n'existe pas."""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS lieux (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            adresse TEXT DEFAULT '',
            description TEXT DEFAULT '',
            contact_id INTEGER,
            tags_raw TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_lieux_nom ON lieux(nom)")
    conn.commit()


# ── Helpers ───────────────────────────────────────────

def _row_to_dict(row):
    """Convertit un tuple DB en dict lieu."""
    if not row:
        return None
    return {
        "id": row[0],
        "nom": row[1],
        "adresse": row[2],
        "description": row[3],
        "contact_id": row[4],
        "tags_raw": row[5],
        "created_at": row[6],
        "updated_at": row[7],
    }


def maps_url(adresse):
    """Génère un lien Google Maps pour une adresse."""
    if not adresse:
        return None
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(adresse)}"


def _lieu_tags(lieu_dict):
    """Génère les tags automatiques pour un lieu."""
    tags = {"lieu"}
    l = lieu_dict

    # Mots du nom
    if l.get("nom"):
        tags.update(extract_keywords(l["nom"], min_len=2))

    # Mots de l'adresse
    if l.get("adresse"):
        tags.update(extract_keywords(l["adresse"], min_len=3))

    # Tags manuels
    if l.get("tags_raw"):
        for t in l["tags_raw"].split(","):
            t = t.strip().lower()
            if t and t not in STOP_WORDS:
                tags.add(t)

    return tags


def _save_tags(conn, lieu_id, tags):
    """Insère les tags d'un lieu dans la table tags."""
    c = conn.cursor()
    item_id = -(lieu_id + ID_OFFSET_LIEU)
    for tag in tags:
        try:
            c.execute("INSERT INTO tags (item_id, tag) VALUES (?, ?)", (item_id, tag))
        except Exception:
            pass


def _delete_tags(conn, lieu_id):
    """Supprime tous les tags d'un lieu."""
    c = conn.cursor()
    item_id = -(lieu_id + ID_OFFSET_LIEU)
    c.execute("DELETE FROM tags WHERE item_id = ?", (item_id,))


# ── CRUD ──────────────────────────────────────────────

def add_lieu(nom, adresse="", description="", contact_id=None,
             tags_raw="", db_path=None):
    """Crée un lieu et ses tags.

    Validation :
        - nom obligatoire

    Returns:
        dict: le lieu créé (avec id)
    Raises:
        ValueError si nom vide
    """
    if not nom.strip():
        raise ValueError("Lieu : nom obligatoire")

    conn = get_db(db_path)
    setup_lieux_table(conn)
    c = conn.cursor()

    c.execute("""
        INSERT INTO lieux (nom, adresse, description, contact_id, tags_raw)
        VALUES (?, ?, ?, ?, ?)
    """, (nom, adresse, description, contact_id, tags_raw))

    lieu_id = c.lastrowid
    lieu = get_lieu(lieu_id, _conn=conn)
    tags = _lieu_tags(lieu)
    _save_tags(conn, lieu_id, tags)

    conn.commit()
    conn.close()
    return lieu


def update_lieu(lieu_id, db_path=None, **kwargs):
    """Modifie un lieu existant.

    Args:
        lieu_id: ID du lieu
        **kwargs: champs à modifier

    Returns:
        dict: le lieu mis à jour, ou None si introuvable
    """
    allowed = {"nom", "adresse", "description", "contact_id", "tags_raw"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return get_lieu(lieu_id, db_path=db_path)

    conn = get_db(db_path)
    c = conn.cursor()

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    set_clause += ", updated_at = datetime('now','localtime')"
    values = list(updates.values()) + [lieu_id]

    c.execute(f"UPDATE lieux SET {set_clause} WHERE id = ?", values)

    # Recréer les tags
    _delete_tags(conn, lieu_id)
    lieu = get_lieu(lieu_id, _conn=conn)
    if lieu:
        tags = _lieu_tags(lieu)
        _save_tags(conn, lieu_id, tags)

    conn.commit()
    conn.close()
    return lieu


def delete_lieu(lieu_id, db_path=None):
    """Supprime un lieu et ses tags.

    Returns:
        bool: True si supprimé, False si introuvable
    """
    conn = get_db(db_path)
    c = conn.cursor()

    c.execute("SELECT id FROM lieux WHERE id = ?", (lieu_id,))
    if not c.fetchone():
        conn.close()
        return False

    _delete_tags(conn, lieu_id)
    c.execute("DELETE FROM lieux WHERE id = ?", (lieu_id,))
    conn.commit()
    conn.close()
    return True


def get_lieu(lieu_id, db_path=None, _conn=None):
    """Retourne un lieu par son ID.

    Returns:
        dict ou None
    """
    conn = _conn or get_db(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM lieux WHERE id = ?", (lieu_id,))
    row = c.fetchone()
    if not _conn:
        conn.close()
    return _row_to_dict(row)


def search_lieux(query, db_path=None):
    """Recherche de lieux par nom/adresse (pour autocomplete).

    Returns:
        list[dict]: lieux correspondants (max 20)
    """
    conn = get_db(db_path)
    setup_lieux_table(conn)
    c = conn.cursor()
    q = f"%{query}%"
    c.execute("""
        SELECT * FROM lieux
        WHERE nom LIKE ? OR adresse LIKE ?
        ORDER BY nom
        LIMIT 20
    """, (q, q))
    rows = c.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ── CLI ───────────────────────────────────────────────

def _cli_add(args):
    """CLI: lieux.py add --nom "..." [options]"""
    nom = ""
    adresse = ""
    description = ""
    contact_id = None
    tags_raw = ""

    i = 0
    while i < len(args):
        if args[i] == "--nom" and i + 1 < len(args):
            nom = args[i + 1]
            i += 2
        elif args[i] == "--adresse" and i + 1 < len(args):
            adresse = args[i + 1]
            i += 2
        elif args[i] == "--desc" and i + 1 < len(args):
            description = args[i + 1]
            i += 2
        elif args[i] == "--contact" and i + 1 < len(args):
            contact_id = int(args[i + 1])
            i += 2
        elif args[i] == "--tags" and i + 1 < len(args):
            tags_raw = args[i + 1]
            i += 2
        else:
            i += 1

    try:
        lieu = add_lieu(nom=nom, adresse=adresse, description=description,
                        contact_id=contact_id, tags_raw=tags_raw)
        print(f"Lieu créé (id={lieu['id']}) : {lieu['nom']}")
        if adresse:
            print(f"  Maps : {maps_url(adresse)}")
    except ValueError as e:
        print(f"Erreur : {e}")


def _cli_search(args):
    """CLI: lieux.py search "query" """
    if not args:
        print("Usage : python3 lieux.py search \"query\"")
        return
    results = search_lieux(args[0])
    if not results:
        print("Aucun lieu trouvé.")
        return
    print(f"{len(results)} lieu(x) :")
    for l in results:
        print(f"  [{l['id']}] 📍 {l['nom']}")
        if l["adresse"]:
            print(f"       {l['adresse']}")


def _cli_get(args):
    """CLI: lieux.py get --id N"""
    lieu_id = None
    for i, a in enumerate(args):
        if a == "--id" and i + 1 < len(args):
            lieu_id = int(args[i + 1])
    if lieu_id is None:
        print("Usage : python3 lieux.py get --id <lieu_id>")
        return
    lieu = get_lieu(lieu_id)
    if not lieu:
        print(f"Lieu {lieu_id} introuvable.")
        return
    print(f"[{lieu['id']}] {lieu['nom']}")
    if lieu["adresse"]:
        print(f"  adresse: {lieu['adresse']}")
        print(f"  Maps: {maps_url(lieu['adresse'])}")
    if lieu["description"]:
        print(f"  description: {lieu['description']}")


def _cli_delete(args):
    """CLI: lieux.py delete --id N"""
    lieu_id = None
    for i, a in enumerate(args):
        if a == "--id" and i + 1 < len(args):
            lieu_id = int(args[i + 1])
    if lieu_id is None:
        print("Usage : python3 lieux.py delete --id <lieu_id>")
        return
    if delete_lieu(lieu_id):
        print(f"Lieu {lieu_id} supprimé.")
    else:
        print(f"Lieu {lieu_id} introuvable.")


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage :")
        print('  python3 lieux.py add --nom "Cabinet dentiste" --adresse "12 rue de la Paix, Paris"')
        print('  python3 lieux.py search "dentiste"')
        print("  python3 lieux.py get --id <N>")
        print("  python3 lieux.py delete --id <N>")
        return

    cmd = args[0]
    rest = args[1:]

    if cmd == "add":
        _cli_add(rest)
    elif cmd == "search":
        _cli_search(rest)
    elif cmd == "get":
        _cli_get(rest)
    elif cmd == "delete":
        _cli_delete(rest)
    else:
        print(f"Commande inconnue : {cmd}")
        print("Commandes : add, search, get, delete")


if __name__ == "__main__":
    main()
