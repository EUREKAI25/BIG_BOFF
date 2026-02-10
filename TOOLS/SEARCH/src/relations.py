#!/usr/bin/env python3
"""
BIG_BOFF Search — Module Relations (standalone)
Liens entre éléments : contact ↔ event, lieu ↔ contact, photo ↔ contact, etc.

Module autonome : importable + CLI.

Usage CLI :
    python3 relations.py add --source contact:1 --target event:3 --label "organisateur"
    python3 relations.py list --type contact --id 1
    python3 relations.py delete --id 5

API importable :
    from relations import add_relation, delete_relation, get_relations
"""

import sys

from config import get_db


# ── Table ─────────────────────────────────────────────

def setup_relations_table(conn):
    """Crée la table relations si elle n'existe pas."""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            relation TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(source_type, source_id, target_type, target_id)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_rel_source ON relations(source_type, source_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rel_target ON relations(target_type, target_id)")
    conn.commit()


# ── Helpers ───────────────────────────────────────────

def _row_to_dict(row):
    """Convertit un tuple DB en dict relation."""
    if not row:
        return None
    return {
        "id": row[0],
        "source_type": row[1],
        "source_id": row[2],
        "target_type": row[3],
        "target_id": row[4],
        "relation": row[5],
        "created_at": row[6],
    }


# ── CRUD ──────────────────────────────────────────────

def add_relation(source_type, source_id, target_type, target_id,
                 relation="", db_path=None):
    """Crée un lien entre deux éléments.

    La relation est bidirectionnelle : on peut retrouver le lien
    en cherchant depuis l'un ou l'autre côté.

    Returns:
        dict: la relation créée
    Raises:
        ValueError si les paramètres sont invalides
    """
    valid_types = {"contact", "entreprise", "lieu", "event", "file", "email",
                   "note", "video", "vault"}
    if source_type not in valid_types:
        raise ValueError(f"Type source inconnu : {source_type}")
    if target_type not in valid_types:
        raise ValueError(f"Type target inconnu : {target_type}")

    conn = get_db(db_path)
    setup_relations_table(conn)
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO relations (source_type, source_id, target_type, target_id, relation)
            VALUES (?, ?, ?, ?, ?)
        """, (source_type, source_id, target_type, target_id, relation))
        rel_id = c.lastrowid
        conn.commit()
    except Exception:
        # UNIQUE constraint — la relation existe déjà
        conn.close()
        return None

    rel = get_relation_by_id(rel_id, _conn=conn)
    conn.close()
    return rel


def delete_relation(rel_id, db_path=None):
    """Supprime une relation par son ID.

    Returns:
        bool: True si supprimée, False si introuvable
    """
    conn = get_db(db_path)
    c = conn.cursor()
    c.execute("SELECT id FROM relations WHERE id = ?", (rel_id,))
    if not c.fetchone():
        conn.close()
        return False
    c.execute("DELETE FROM relations WHERE id = ?", (rel_id,))
    conn.commit()
    conn.close()
    return True


def get_relation_by_id(rel_id, db_path=None, _conn=None):
    """Retourne une relation par son ID."""
    conn = _conn or get_db(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM relations WHERE id = ?", (rel_id,))
    row = c.fetchone()
    if not _conn:
        conn.close()
    return _row_to_dict(row)


def get_relations(element_type, element_id, db_path=None):
    """Retourne toutes les relations liées à un élément (dans les 2 sens).

    Returns:
        list[dict]: relations (source ou target = l'élément demandé)
    """
    conn = get_db(db_path)
    setup_relations_table(conn)
    c = conn.cursor()

    c.execute("""
        SELECT * FROM relations
        WHERE (source_type = ? AND source_id = ?)
           OR (target_type = ? AND target_id = ?)
        ORDER BY created_at DESC
    """, (element_type, element_id, element_type, element_id))

    rows = c.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def delete_relations_for(element_type, element_id, db_path=None):
    """Supprime toutes les relations liées à un élément (nettoyage).

    Utilisé quand on supprime un contact, lieu, etc.
    """
    conn = get_db(db_path)
    c = conn.cursor()
    c.execute("""
        DELETE FROM relations
        WHERE (source_type = ? AND source_id = ?)
           OR (target_type = ? AND target_id = ?)
    """, (element_type, element_id, element_type, element_id))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted


# ── CLI ───────────────────────────────────────────────

def _cli_add(args):
    """CLI: relations.py add --source contact:1 --target event:3 [--label "..."]"""
    source = None
    target = None
    label = ""

    i = 0
    while i < len(args):
        if args[i] == "--source" and i + 1 < len(args):
            source = args[i + 1]
            i += 2
        elif args[i] == "--target" and i + 1 < len(args):
            target = args[i + 1]
            i += 2
        elif args[i] == "--label" and i + 1 < len(args):
            label = args[i + 1]
            i += 2
        else:
            i += 1

    if not source or not target:
        print("Usage : python3 relations.py add --source type:id --target type:id [--label \"...\"]")
        return

    try:
        s_type, s_id = source.split(":")
        t_type, t_id = target.split(":")
        rel = add_relation(s_type, int(s_id), t_type, int(t_id), relation=label)
        if rel:
            print(f"Relation créée (id={rel['id']}) : {source} → {target}")
            if label:
                print(f"  label: {label}")
        else:
            print("Relation déjà existante.")
    except ValueError as e:
        print(f"Erreur : {e}")


def _cli_list(args):
    """CLI: relations.py list --type contact --id 1"""
    elem_type = None
    elem_id = None

    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            elem_type = args[i + 1]
            i += 2
        elif args[i] == "--id" and i + 1 < len(args):
            elem_id = int(args[i + 1])
            i += 2
        else:
            i += 1

    if not elem_type or elem_id is None:
        print("Usage : python3 relations.py list --type <type> --id <id>")
        return

    rels = get_relations(elem_type, elem_id)
    if not rels:
        print("Aucune relation.")
        return
    print(f"{len(rels)} relation(s) :")
    for r in rels:
        arrow = f"{r['source_type']}:{r['source_id']} → {r['target_type']}:{r['target_id']}"
        label = f" ({r['relation']})" if r["relation"] else ""
        print(f"  [{r['id']}] {arrow}{label}")


def _cli_delete(args):
    """CLI: relations.py delete --id N"""
    rel_id = None
    for i, a in enumerate(args):
        if a == "--id" and i + 1 < len(args):
            rel_id = int(args[i + 1])
    if rel_id is None:
        print("Usage : python3 relations.py delete --id <rel_id>")
        return
    if delete_relation(rel_id):
        print(f"Relation {rel_id} supprimée.")
    else:
        print(f"Relation {rel_id} introuvable.")


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage :")
        print('  python3 relations.py add --source contact:1 --target event:3 [--label "..."]')
        print("  python3 relations.py list --type contact --id 1")
        print("  python3 relations.py delete --id <N>")
        return

    cmd = args[0]
    rest = args[1:]

    if cmd == "add":
        _cli_add(rest)
    elif cmd == "list":
        _cli_list(rest)
    elif cmd == "delete":
        _cli_delete(rest)
    else:
        print(f"Commande inconnue : {cmd}")
        print("Commandes : add, list, delete")


if __name__ == "__main__":
    main()
