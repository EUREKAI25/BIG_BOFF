#!/usr/bin/env python3
"""
Réindexation complète de TOUS les tags (notes, emails, vault, events, contacts, lieux).
À exécuter après avoir modifié la structure de la table tags.
"""

import sqlite3
from config import (
    DB_PATH, ID_OFFSET_EMAIL, ID_OFFSET_NOTE, ID_OFFSET_VAULT,
    ID_OFFSET_EVENT, ID_OFFSET_CONTACT, ID_OFFSET_LIEU,
    extract_keywords, normalize_tag, is_valid_tag
)

def main():
    print("=== Réindexation complète de tous les tags ===\n")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Supprimer tous les tags négatifs (notes, emails, etc.)
    c.execute("DELETE FROM tags WHERE item_id < 0")
    deleted = c.rowcount
    print(f"✓ {deleted} tags négatifs supprimés\n")

    batch = []

    # ── NOTES ────────────────────────────────────────────
    print("📝 Indexation des notes...")
    c.execute("SELECT id, title, body FROM notes")
    notes = c.fetchall()
    for note_id, title, body in notes:
        text = f"{title or ''} {body or ''}"
        tags = extract_keywords(text)
        item_id = -(note_id + ID_OFFSET_NOTE)
        for tag_display in tags:
            tag_normalized = normalize_tag(tag_display)
            batch.append((item_id, tag_normalized, tag_display))
    print(f"  → {len(notes)} notes, {len(batch)} tags")

    # ── EMAILS ───────────────────────────────────────────
    print("📧 Indexation des emails...")
    c.execute("SELECT id, subject, from_addr, to_addr FROM emails")
    emails = c.fetchall()
    email_count = 0
    for email_id, subject, from_addr, to_addr in emails:
        text = f"{subject or ''} {from_addr or ''} {to_addr or ''}"
        tags = extract_keywords(text)
        if tags:
            item_id = -(email_id + ID_OFFSET_EMAIL)
            for tag_display in tags:
                tag_normalized = normalize_tag(tag_display)
                batch.append((item_id, tag_normalized, tag_display))
            email_count += 1
    print(f"  → {len(emails)} emails, {email_count} avec tags")

    # ── VAULT ────────────────────────────────────────────
    print("🔒 Indexation du vault...")
    c.execute("SELECT id, service, login, project, category FROM vault")
    vaults = c.fetchall()
    for vault_id, service, login, project, category in vaults:
        text = f"{service or ''} {login or ''} {project or ''} {category or ''}"
        tags = extract_keywords(text)
        # Tags de catégorie
        if category:
            tags.add(category.lower())
        tags.add("vault")
        item_id = -(vault_id + ID_OFFSET_VAULT)
        for tag_display in tags:
            if is_valid_tag(tag_display):
                tag_normalized = normalize_tag(tag_display)
                batch.append((item_id, tag_normalized, tag_display))
    print(f"  → {len(vaults)} entrées vault")

    # ── EVENTS ───────────────────────────────────────────
    print("📅 Indexation des events...")
    try:
        c.execute("SELECT id, title, location, description, tags_raw FROM events")
        events = c.fetchall()
        for event_id, title, location, desc, tags_raw in events:
            text = f"{title or ''} {location or ''} {desc or ''}"
            tags = extract_keywords(text)
            # Tags utilisateur
            if tags_raw:
                for t in tags_raw.split(","):
                    t = t.strip()
                    if t and is_valid_tag(t):
                        tags.add(t)
            tags.add("event")
            item_id = -(event_id + ID_OFFSET_EVENT)
            for tag_display in tags:
                if is_valid_tag(tag_display):
                    tag_normalized = normalize_tag(tag_display)
                    batch.append((item_id, tag_normalized, tag_display))
        print(f"  → {len(events)} events")
    except sqlite3.OperationalError:
        print("  → Table events n'existe pas encore")

    # ── CONTACTS ─────────────────────────────────────────
    print("👤 Indexation des contacts...")
    try:
        c.execute("SELECT id, type, nom, prenom, tags_raw FROM contacts")
        contacts = c.fetchall()
        for contact_id, typ, nom, prenom, tags_raw in contacts:
            text = f"{nom or ''} {prenom or ''}"
            tags = extract_keywords(text)
            tags.add("contact")
            if typ:
                tags.add(typ.lower())
            # Tags utilisateur
            if tags_raw:
                for t in tags_raw.split(","):
                    t = t.strip()
                    if t and is_valid_tag(t):
                        tags.add(t)
            item_id = -(contact_id + ID_OFFSET_CONTACT)
            for tag_display in tags:
                if is_valid_tag(tag_display):
                    tag_normalized = normalize_tag(tag_display)
                    batch.append((item_id, tag_normalized, tag_display))
        print(f"  → {len(contacts)} contacts")
    except sqlite3.OperationalError:
        print("  → Table contacts n'existe pas encore")

    # ── LIEUX ────────────────────────────────────────────
    print("📍 Indexation des lieux...")
    try:
        c.execute("SELECT id, nom, adresse, tags_raw FROM lieux")
        lieux = c.fetchall()
        for lieu_id, nom, adresse, tags_raw in lieux:
            text = f"{nom or ''} {adresse or ''}"
            tags = extract_keywords(text)
            tags.add("lieu")
            # Tags utilisateur
            if tags_raw:
                for t in tags_raw.split(","):
                    t = t.strip()
                    if t and is_valid_tag(t):
                        tags.add(t)
            item_id = -(lieu_id + ID_OFFSET_LIEU)
            for tag_display in tags:
                if is_valid_tag(tag_display):
                    tag_normalized = normalize_tag(tag_display)
                    batch.append((item_id, tag_normalized, tag_display))
        print(f"  → {len(lieux)} lieux")
    except sqlite3.OperationalError:
        print("  → Table lieux n'existe pas encore")

    # ── INSERTION ────────────────────────────────────────
    print(f"\n💾 Insertion de {len(batch)} tags...")
    c.executemany("INSERT INTO tags (item_id, tag, tag_display) VALUES (?, ?, ?)", batch)
    conn.commit()

    # ── STATS ────────────────────────────────────────────
    c.execute("SELECT COUNT(*) FROM tags")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT tag) FROM tags")
    unique = c.fetchone()[0]

    print(f"\n✅ Terminé !")
    print(f"  Total tags : {total}")
    print(f"  Tags uniques : {unique}")

    conn.close()

if __name__ == "__main__":
    main()
