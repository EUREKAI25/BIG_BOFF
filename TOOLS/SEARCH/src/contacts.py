#!/usr/bin/env python3
"""
BIG_BOFF Search — Module Contacts (standalone)
Gestion des contacts (personnes et entreprises) avec tags automatiques.

Module autonome : importable + CLI.

Usage CLI :
    python3 contacts.py add --type personne --nom "Dupont" --prenom "Marie" --tel "0612345678" --tags "dentiste,sante"
    python3 contacts.py add --type entreprise --nom "Cabinet Dupont" --adresse "12 rue de la Paix" --site "dupont.fr"
    python3 contacts.py search "dupont"
    python3 contacts.py get --id 1
    python3 contacts.py delete --id 1

API importable :
    from contacts import add_contact, update_contact, delete_contact, get_contact, search_contacts
"""

import sys
import json
from datetime import datetime

from config import (
    ID_OFFSET_CONTACT,
    STOP_WORDS,
    extract_keywords,
    get_db,
)


# ── Table ─────────────────────────────────────────────

def setup_contacts_table(conn):
    """Crée la table contacts si elle n'existe pas."""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL DEFAULT 'personne',
            nom TEXT NOT NULL DEFAULT '',
            prenom TEXT DEFAULT '',
            telephones TEXT DEFAULT '[]',
            emails TEXT DEFAULT '[]',
            date_naissance TEXT,
            heure_naissance TEXT,
            lieu_naissance TEXT,
            adresse TEXT DEFAULT '',
            site_web TEXT DEFAULT '',
            commentaire TEXT DEFAULT '',
            photo_path TEXT DEFAULT '',
            entreprise_id INTEGER,
            tags_raw TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(type)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_contacts_nom ON contacts(nom)")
    conn.commit()


# ── Helpers ───────────────────────────────────────────

def _row_to_dict(row):
    """Convertit un tuple DB en dict contact."""
    if not row:
        return None
    return {
        "id": row[0],
        "type": row[1],
        "nom": row[2],
        "prenom": row[3],
        "telephones": json.loads(row[4]) if row[4] else [],
        "emails": json.loads(row[5]) if row[5] else [],
        "date_naissance": row[6],
        "heure_naissance": row[7],
        "lieu_naissance": row[8],
        "adresse": row[9],
        "site_web": row[10],
        "commentaire": row[11],
        "photo_path": row[12],
        "entreprise_id": row[13],
        "tags_raw": row[14],
        "created_at": row[15],
        "updated_at": row[16],
    }


def _contact_tags(contact_dict):
    """Génère les tags automatiques pour un contact."""
    tags = {"contact"}
    c = contact_dict

    # Type
    tags.add(c["type"])  # personne ou entreprise

    # Mots du nom et prénom
    if c.get("nom"):
        tags.update(extract_keywords(c["nom"], min_len=2))
    if c.get("prenom"):
        tags.update(extract_keywords(c["prenom"], min_len=2))

    # Entreprise liée (nom)
    if c.get("entreprise_id"):
        tags.add("entreprise")

    # Adresse
    if c.get("adresse"):
        tags.update(extract_keywords(c["adresse"], min_len=3))

    # Site web
    if c.get("site_web"):
        parts = c["site_web"].replace("https://", "").replace("http://", "").replace("www.", "").split(".")
        for p in parts:
            p = p.strip().lower()
            if len(p) >= 3 and p not in STOP_WORDS:
                tags.add(p)

    # Tags manuels
    if c.get("tags_raw"):
        for t in c["tags_raw"].split(","):
            t = t.strip().lower()
            if t and t not in STOP_WORDS:
                tags.add(t)

    return tags


def _save_tags(conn, contact_id, tags):
    """Insère les tags d'un contact dans la table tags."""
    c = conn.cursor()
    item_id = -(contact_id + ID_OFFSET_CONTACT)
    for tag in tags:
        try:
            c.execute("INSERT INTO tags (item_id, tag) VALUES (?, ?)", (item_id, tag))
        except Exception:
            pass


def _delete_tags(conn, contact_id):
    """Supprime tous les tags d'un contact."""
    c = conn.cursor()
    item_id = -(contact_id + ID_OFFSET_CONTACT)
    c.execute("DELETE FROM tags WHERE item_id = ?", (item_id,))


# ── CRUD ──────────────────────────────────────────────

def add_contact(type="personne", nom="", prenom="", telephones=None,
                emails=None, date_naissance=None, heure_naissance=None,
                lieu_naissance=None, adresse="", site_web="",
                commentaire="", photo_path="", entreprise_id=None,
                tags_raw="", db_path=None):
    """Crée un contact et ses tags.

    Validation :
        - personne : nom OU prenom obligatoire (au moins un)
        - entreprise : nom obligatoire

    Returns:
        dict: le contact créé (avec id)
    Raises:
        ValueError si validation échoue
    """
    # Validation
    if type == "personne":
        if not nom.strip() and not (prenom or "").strip():
            raise ValueError("Contact personne : nom ou prénom obligatoire")
    elif type == "entreprise":
        if not nom.strip():
            raise ValueError("Contact entreprise : nom obligatoire")
    else:
        raise ValueError(f"Type de contact inconnu : {type}")

    telephones = telephones or []
    emails = emails or []

    conn = get_db(db_path)
    setup_contacts_table(conn)
    c = conn.cursor()

    c.execute("""
        INSERT INTO contacts (type, nom, prenom, telephones, emails,
                             date_naissance, heure_naissance, lieu_naissance,
                             adresse, site_web, commentaire, photo_path,
                             entreprise_id, tags_raw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (type, nom, prenom or "", json.dumps(telephones), json.dumps(emails),
          date_naissance, heure_naissance, lieu_naissance,
          adresse, site_web, commentaire, photo_path,
          entreprise_id, tags_raw))

    contact_id = c.lastrowid
    contact = get_contact(contact_id, _conn=conn)
    tags = _contact_tags(contact)
    _save_tags(conn, contact_id, tags)

    conn.commit()
    conn.close()
    return contact


def update_contact(contact_id, db_path=None, **kwargs):
    """Modifie un contact existant.

    Args:
        contact_id: ID du contact
        **kwargs: champs à modifier

    Returns:
        dict: le contact mis à jour, ou None si introuvable
    """
    allowed = {"type", "nom", "prenom", "telephones", "emails",
               "date_naissance", "heure_naissance", "lieu_naissance",
               "adresse", "site_web", "commentaire", "photo_path",
               "entreprise_id", "tags_raw"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return get_contact(contact_id, db_path=db_path)

    # Sérialiser les listes en JSON
    if "telephones" in updates and isinstance(updates["telephones"], list):
        updates["telephones"] = json.dumps(updates["telephones"])
    if "emails" in updates and isinstance(updates["emails"], list):
        updates["emails"] = json.dumps(updates["emails"])

    conn = get_db(db_path)
    c = conn.cursor()

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    set_clause += ", updated_at = datetime('now','localtime')"
    values = list(updates.values()) + [contact_id]

    c.execute(f"UPDATE contacts SET {set_clause} WHERE id = ?", values)

    # Recréer les tags
    _delete_tags(conn, contact_id)
    contact = get_contact(contact_id, _conn=conn)
    if contact:
        tags = _contact_tags(contact)
        _save_tags(conn, contact_id, tags)

    conn.commit()
    conn.close()
    return contact


def delete_contact(contact_id, db_path=None):
    """Supprime un contact et ses tags.

    Returns:
        bool: True si supprimé, False si introuvable
    """
    conn = get_db(db_path)
    c = conn.cursor()

    c.execute("SELECT id FROM contacts WHERE id = ?", (contact_id,))
    if not c.fetchone():
        conn.close()
        return False

    _delete_tags(conn, contact_id)
    c.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()
    conn.close()
    return True


def get_contact(contact_id, db_path=None, _conn=None):
    """Retourne un contact par son ID.

    Returns:
        dict ou None
    """
    conn = _conn or get_db(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
    row = c.fetchone()
    if not _conn:
        conn.close()
    return _row_to_dict(row)


def search_contacts(query, db_path=None):
    """Recherche de contacts par nom/prénom (pour autocomplete).

    Returns:
        list[dict]: contacts correspondants (max 20)
    """
    conn = get_db(db_path)
    setup_contacts_table(conn)
    c = conn.cursor()
    q = f"%{query}%"
    c.execute("""
        SELECT * FROM contacts
        WHERE nom LIKE ? OR prenom LIKE ?
        ORDER BY nom, prenom
        LIMIT 20
    """, (q, q))
    rows = c.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ── CLI ───────────────────────────────────────────────

def _cli_add(args):
    """CLI: contacts.py add --type personne --nom "..." [options]"""
    type_ = "personne"
    nom = ""
    prenom = ""
    telephones = []
    emails = []
    date_naissance = None
    heure_naissance = None
    lieu_naissance = None
    adresse = ""
    site_web = ""
    commentaire = ""
    tags_raw = ""
    entreprise_id = None

    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            type_ = args[i + 1]
            i += 2
        elif args[i] == "--nom" and i + 1 < len(args):
            nom = args[i + 1]
            i += 2
        elif args[i] == "--prenom" and i + 1 < len(args):
            prenom = args[i + 1]
            i += 2
        elif args[i] == "--tel" and i + 1 < len(args):
            telephones.append(args[i + 1])
            i += 2
        elif args[i] == "--email" and i + 1 < len(args):
            emails.append(args[i + 1])
            i += 2
        elif args[i] == "--naissance" and i + 1 < len(args):
            date_naissance = args[i + 1]
            i += 2
        elif args[i] == "--heure-naissance" and i + 1 < len(args):
            heure_naissance = args[i + 1]
            i += 2
        elif args[i] == "--lieu-naissance" and i + 1 < len(args):
            lieu_naissance = args[i + 1]
            i += 2
        elif args[i] == "--adresse" and i + 1 < len(args):
            adresse = args[i + 1]
            i += 2
        elif args[i] == "--site" and i + 1 < len(args):
            site_web = args[i + 1]
            i += 2
        elif args[i] == "--commentaire" and i + 1 < len(args):
            commentaire = args[i + 1]
            i += 2
        elif args[i] == "--tags" and i + 1 < len(args):
            tags_raw = args[i + 1]
            i += 2
        elif args[i] == "--entreprise" and i + 1 < len(args):
            entreprise_id = int(args[i + 1])
            i += 2
        else:
            i += 1

    try:
        contact = add_contact(
            type=type_, nom=nom, prenom=prenom,
            telephones=telephones, emails=emails,
            date_naissance=date_naissance,
            heure_naissance=heure_naissance,
            lieu_naissance=lieu_naissance,
            adresse=adresse, site_web=site_web,
            commentaire=commentaire,
            entreprise_id=entreprise_id,
            tags_raw=tags_raw,
        )
        display = contact["prenom"] + " " + contact["nom"] if contact["prenom"] else contact["nom"]
        print(f"Contact créé (id={contact['id']}) : {display.strip()} [{contact['type']}]")
    except ValueError as e:
        print(f"Erreur : {e}")


def _cli_search(args):
    """CLI: contacts.py search "query" """
    if not args:
        print("Usage : python3 contacts.py search \"query\"")
        return
    results = search_contacts(args[0])
    if not results:
        print("Aucun contact trouvé.")
        return
    print(f"{len(results)} contact(s) :")
    for c in results:
        display = c["prenom"] + " " + c["nom"] if c["prenom"] else c["nom"]
        type_label = "👤" if c["type"] == "personne" else "🏢"
        print(f"  [{c['id']}] {type_label} {display.strip()}")
        if c["telephones"]:
            print(f"       tél: {', '.join(c['telephones'])}")
        if c["emails"]:
            print(f"       email: {', '.join(c['emails'])}")


def _cli_get(args):
    """CLI: contacts.py get --id N"""
    contact_id = None
    for i, a in enumerate(args):
        if a == "--id" and i + 1 < len(args):
            contact_id = int(args[i + 1])
    if contact_id is None:
        print("Usage : python3 contacts.py get --id <contact_id>")
        return
    contact = get_contact(contact_id)
    if not contact:
        print(f"Contact {contact_id} introuvable.")
        return
    display = contact["prenom"] + " " + contact["nom"] if contact["prenom"] else contact["nom"]
    print(f"[{contact['id']}] {display.strip()} ({contact['type']})")
    for k in ("telephones", "emails", "adresse", "date_naissance", "commentaire", "site_web"):
        v = contact.get(k)
        if v and v != "[]":
            print(f"  {k}: {v}")


def _cli_delete(args):
    """CLI: contacts.py delete --id N"""
    contact_id = None
    for i, a in enumerate(args):
        if a == "--id" and i + 1 < len(args):
            contact_id = int(args[i + 1])
    if contact_id is None:
        print("Usage : python3 contacts.py delete --id <contact_id>")
        return
    if delete_contact(contact_id):
        print(f"Contact {contact_id} supprimé.")
    else:
        print(f"Contact {contact_id} introuvable.")


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage :")
        print('  python3 contacts.py add --type personne --nom "Dupont" --prenom "Marie" [options]')
        print('  python3 contacts.py add --type entreprise --nom "Cabinet Dupont" [options]')
        print('  python3 contacts.py search "dupont"')
        print("  python3 contacts.py get --id <N>")
        print("  python3 contacts.py delete --id <N>")
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
