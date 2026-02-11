#!/usr/bin/env python3
"""
BIG_BOFF Search — Relay DB Setup
Initialise les tables du relay server (Phase 2 P2P).
"""

import sqlite3
from pathlib import Path

RELAY_DB_PATH = Path.home() / ".bigboff" / "relay.db"

def setup_relay_db():
    """Crée toutes les tables relay."""

    RELAY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== Setup Relay Database ===")
    print(f"Base : {RELAY_DB_PATH}\n")

    conn = sqlite3.connect(str(RELAY_DB_PATH))
    c = conn.cursor()

    tables_created = []

    # ────────────────────────────────────────────────────────────
    # Table users (registry identités)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            alias TEXT,
            public_key_rsa TEXT,
            public_key_ed25519 TEXT,
            registered_at TEXT,
            last_seen TEXT
        )
    """)
    tables_created.append("users")

    # ────────────────────────────────────────────────────────────
    # Table challenges (anti-replay)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS challenges (
            challenge_id TEXT PRIMARY KEY,
            user_id TEXT,
            challenge TEXT,
            created_at TEXT,
            expires_at TEXT,
            used INTEGER DEFAULT 0
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_challenges_expires ON challenges(expires_at)")
    tables_created.append("challenges")

    # ────────────────────────────────────────────────────────────
    # Table sync_log (changements différentiels)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            data TEXT,
            UNIQUE(user_id, entity_type, entity_id, timestamp)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_sync_user_ts ON sync_log(user_id, timestamp)")
    tables_created.append("sync_log")

    # ────────────────────────────────────────────────────────────
    # Migration Phase 5 : Ajouter expires_at à sync_log
    # ────────────────────────────────────────────────────────────
    try:
        c.execute("ALTER TABLE sync_log ADD COLUMN expires_at TEXT DEFAULT NULL")
        print("✅ Colonne expires_at ajoutée à sync_log")
    except sqlite3.OperationalError:
        # Colonne déjà existante
        pass

    # Index pour cleanup efficace
    c.execute("CREATE INDEX IF NOT EXISTS idx_sync_log_expires ON sync_log(expires_at)")

    # ────────────────────────────────────────────────────────────
    # Migration Phase 6 : Ajouter is_shared_copy à sync_log
    # ────────────────────────────────────────────────────────────
    try:
        c.execute("ALTER TABLE sync_log ADD COLUMN is_shared_copy INTEGER DEFAULT 0")
        print("✅ Colonne is_shared_copy ajoutée à sync_log")
    except sqlite3.OperationalError:
        # Colonne déjà existante
        pass

    # Index pour filtrage partage vs consultation
    c.execute("CREATE INDEX IF NOT EXISTS idx_sync_log_shared ON sync_log(is_shared_copy)")

    # ────────────────────────────────────────────────────────────
    # Table permissions (Phase 3 - ACL)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_user_id TEXT NOT NULL,
            target_user_id TEXT,
            target_group_id TEXT,
            scope_type TEXT NOT NULL,
            scope_value TEXT,
            mode TEXT DEFAULT 'consultation',
            permissions TEXT DEFAULT '["read"]',
            granted_at TEXT,
            revoked_at TEXT,
            UNIQUE(owner_user_id, target_user_id, scope_type, scope_value)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_permissions_owner ON permissions(owner_user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_permissions_target ON permissions(target_user_id)")
    tables_created.append("permissions")

    # ────────────────────────────────────────────────────────────
    # Tables groups (Phase 7 - Groupes 1-to-many)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner_user_id TEXT NOT NULL,
            created_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_groups_owner ON groups(owner_user_id)")
    tables_created.append("groups")

    c.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            group_id TEXT,
            user_id TEXT,
            role TEXT DEFAULT 'member',
            joined_at TEXT,
            UNIQUE(group_id, user_id)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_group_members_group ON group_members(group_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id)")
    tables_created.append("group_members")

    # ────────────────────────────────────────────────────────────
    # Table device_sessions (Phase 8 - Multi-device)
    # ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS device_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_name TEXT,
            created_at TEXT,
            expires_at TEXT,
            revoked_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_device_sessions_user ON device_sessions(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_device_sessions_expires ON device_sessions(expires_at)")
    tables_created.append("device_sessions")

    conn.commit()
    conn.close()

    print(f"✅ {len(tables_created)} tables créées/vérifiées :")
    for table in tables_created:
        print(f"   - {table}")

    print(f"\n✅ Relay database initialisée : {RELAY_DB_PATH}")


if __name__ == "__main__":
    setup_relay_db()
