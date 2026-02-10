#!/usr/bin/env python3
"""
BIG_BOFF Search — Connecteur optionnel macOS Contacts.app
Lit directement la base SQLite du carnet d'adresses pour proposer
des suggestions lors de l'ajout d'un contact (pré-remplissage formulaire).

N'importe RIEN automatiquement — c'est juste de l'autocomplétion.
"""

import json
import os
import sqlite3
from pathlib import Path

# Bases SQLite de Contacts.app (macOS)
_AB_BASE = Path.home() / "Library" / "Application Support" / "AddressBook"
_AB_SOURCES = _AB_BASE / "Sources"


def _find_databases():
    """Trouve toutes les bases AddressBook sur ce Mac."""
    dbs = []
    if _AB_SOURCES.exists():
        for src in _AB_SOURCES.iterdir():
            db_path = src / "AddressBook-v22.abcddb"
            if db_path.exists():
                dbs.append(str(db_path))
    main_db = _AB_BASE / "AddressBook-v22.abcddb"
    if main_db.exists():
        dbs.append(str(main_db))
    return dbs


def search_system_contacts(query="", limit=30):
    """Cherche dans les contacts macOS (lecture seule, instantanée).

    Args:
        query: texte à chercher dans prénom/nom (vide = tous)
        limit: nombre max de résultats

    Returns:
        list[dict]: contacts avec prenom, nom, telephones, emails
    """
    dbs = _find_databases()
    if not dbs:
        return []

    query_lower = query.strip().lower()
    contacts = []

    for db_path in dbs:
        try:
            db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            db.row_factory = sqlite3.Row

            # Récupérer les contacts
            if query_lower:
                words = query_lower.split()
                where_parts = []
                params = []
                for w in words:
                    where_parts.append(
                        "(LOWER(COALESCE(ZFIRSTNAME,'')) LIKE ? OR LOWER(COALESCE(ZLASTNAME,'')) LIKE ? OR LOWER(COALESCE(ZORGANIZATION,'')) LIKE ?)"
                    )
                    params.extend([f"%{w}%", f"%{w}%", f"%{w}%"])
                where = " AND ".join(where_parts)
                rows = db.execute(
                    f"SELECT Z_PK, ZFIRSTNAME, ZLASTNAME, ZORGANIZATION FROM ZABCDRECORD WHERE {where} LIMIT ?",
                    params + [limit * 2],
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT Z_PK, ZFIRSTNAME, ZLASTNAME, ZORGANIZATION FROM ZABCDRECORD WHERE ZFIRSTNAME IS NOT NULL OR ZLASTNAME IS NOT NULL LIMIT ?",
                    [limit * 2],
                ).fetchall()

            for row in rows:
                pk = row["Z_PK"]
                prenom = row["ZFIRSTNAME"] or ""
                nom = row["ZLASTNAME"] or ""
                org = row["ZORGANIZATION"] or ""

                if not prenom and not nom and not org:
                    continue

                # Téléphones
                tels = [
                    r[0] for r in db.execute(
                        "SELECT ZFULLNUMBER FROM ZABCDPHONENUMBER WHERE ZOWNER=?", [pk]
                    ).fetchall() if r[0]
                ]

                # Emails
                emails = [
                    r[0] for r in db.execute(
                        "SELECT ZADDRESS FROM ZABCDEMAILADDRESS WHERE ZOWNER=?", [pk]
                    ).fetchall() if r[0]
                ]

                contacts.append({
                    "prenom": prenom,
                    "nom": nom or org,
                    "telephones": tels,
                    "emails": emails,
                })

            db.close()
        except Exception:
            continue

    # Dédoublonner par nom+prénom
    seen = set()
    unique = []
    for c in contacts:
        key = (c["prenom"].lower(), c["nom"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique[:limit]


def is_available():
    """Vérifie si le connecteur est utilisable (bases trouvées)."""
    return len(_find_databases()) > 0


if __name__ == "__main__":
    if not is_available():
        print("Pas de base Contacts macOS trouvée")
    else:
        q = " ".join(os.sys.argv[1:]) if len(os.sys.argv) > 1 else ""
        results = search_system_contacts(q, limit=20)
        print(f"{len(results)} contacts trouvés")
        for c in results:
            display = f"{c['prenom']} {c['nom']}".strip()
            tels = ", ".join(c["telephones"][:2])
            emails = ", ".join(c["emails"][:2])
            print(f"  {display} | {tels} | {emails}")
