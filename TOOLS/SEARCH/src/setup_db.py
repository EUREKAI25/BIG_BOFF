#!/usr/bin/env python3
"""
BIG_BOFF Search — Database Setup
Initialise toutes les tables de la base de données.
"""

import sqlite3
import sys
from pathlib import Path

try:
    from config_loader import load_config, get_db_path, ensure_config_dir
except ImportError:
    print("❌ Erreur : config_loader.py manquant")
    sys.exit(1)


def setup_database(db_path: str = None):
    """Crée toutes les tables nécessaires.

    Args:
        db_path: Chemin vers la base de données (None = utilise config)
    """
    if db_path is None:
        db_path = get_db_path()

    # Créer le dossier parent si nécessaire
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"=== Setup BIG_BOFF Search Database ===")
    print(f"Base : {db_path}\n")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    tables_created = []

    # ────────────────────────────────────────────────────────────
    # Table items (fichiers du système)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            extension TEXT,
            chemin_relatif TEXT,
            chemin TEXT,
            taille INTEGER,
            date_modif TEXT,
            est_dossier INTEGER,
            UNIQUE(chemin)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_items_chemin ON items(chemin)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_items_ext ON items(extension)")
    tables_created.append("items")

    # ────────────────────────────────────────────────────────────
    # Table tags (tags atomiques)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            item_id INTEGER,
            tag TEXT,
            tag_display TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_tag ON tags(tag)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_tag_display ON tags(tag_display)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_tag_item ON tags(item_id)")
    tables_created.append("tags")

    # ────────────────────────────────────────────────────────────
    # Table notes (Apple Notes)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            folder TEXT,
            date_modif TEXT,
            body TEXT,
            UNIQUE(title, date_modif)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title)")
    tables_created.append("notes")

    # ────────────────────────────────────────────────────────────
    # Table emails (IMAP)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT,
            folder TEXT,
            uid TEXT,
            message_id TEXT,
            subject TEXT,
            from_addr TEXT,
            to_addr TEXT,
            date_sent TEXT,
            date_received TEXT,
            has_attachments INTEGER DEFAULT 0,
            size INTEGER DEFAULT 0,
            snippet TEXT DEFAULT '',
            UNIQUE(account, folder, uid)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_emails_account ON emails(account)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_emails_from ON emails(from_addr)")
    tables_created.append("emails")

    # ────────────────────────────────────────────────────────────
    # Table videos (URLs vidéo extraites)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            platform TEXT,
            title TEXT,
            source_note_id INTEGER,
            date_added TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_videos_url ON videos(url)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform)")
    tables_created.append("videos")

    # ────────────────────────────────────────────────────────────
    # Table vault (coffre-fort chiffré)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            username TEXT,
            password_encrypted TEXT,
            url TEXT,
            notes TEXT,
            category TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_vault_service ON vault(service)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_vault_category ON vault(category)")
    tables_created.append("vault")

    # ────────────────────────────────────────────────────────────
    # Table events (événements, récurrences)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT,
            description TEXT,
            recurrence TEXT DEFAULT 'none',
            tags_raw TEXT DEFAULT '',
            subtype TEXT DEFAULT 'generic',
            contact_id INTEGER,
            lieu_id INTEGER,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_subtype ON events(subtype)")
    tables_created.append("events")

    # ────────────────────────────────────────────────────────────
    # Table contacts (personnes / entreprises)
    # ────────────────────────────────────────────────────────────
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
            created_at TEXT,
            updated_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_contacts_nom ON contacts(nom)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(type)")
    tables_created.append("contacts")

    # ────────────────────────────────────────────────────────────
    # Table lieux (adresses, Google Maps)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS lieux (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            adresse TEXT DEFAULT '',
            description TEXT DEFAULT '',
            contact_id INTEGER,
            tags_raw TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_lieux_nom ON lieux(nom)")
    tables_created.append("lieux")

    # ────────────────────────────────────────────────────────────
    # Table relations (liens entre éléments)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            relation TEXT DEFAULT '',
            created_at TEXT,
            UNIQUE(source_type, source_id, target_type, target_id)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_type, source_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_type, target_id)")
    tables_created.append("relations")

    # ────────────────────────────────────────────────────────────
    # Table url_metadata_cache (cache fetch métadonnées)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS url_metadata_cache (
            url TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            keywords TEXT,
            fetched_at TEXT,
            fetch_success INTEGER DEFAULT 1
        )
    """)
    tables_created.append("url_metadata_cache")

    # ────────────────────────────────────────────────────────────
    # Table favorites (éléments favoris)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            item_id INTEGER PRIMARY KEY,
            favorited_at TEXT
        )
    """)
    tables_created.append("favorites")

    conn.commit()
    conn.close()

    print(f"✅ {len(tables_created)} tables créées/vérifiées :")
    for table in tables_created:
        print(f"   - {table}")

    print(f"\n✅ Base de données initialisée : {db_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Initialise la base de données BIG_BOFF Search")
    parser.add_argument('--db-path', help='Chemin custom de la base (optionnel)')
    args = parser.parse_args()

    # Initialiser config si nécessaire
    ensure_config_dir()

    # Setup database
    setup_database(args.db_path)


if __name__ == "__main__":
    main()
