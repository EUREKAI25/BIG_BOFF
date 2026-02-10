"""
EURKAI_COCKPIT — Database Migrations
Version: 1.0.0

MVP: init_db only (idempotent schema creation).
Future: migration versioning with up/down scripts.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from .storage import Storage, DEFAULT_DB_PATH


# Migration version tracking
SCHEMA_VERSION = "1.0.0"


def get_schema_version(db_path: Path) -> Optional[str]:
    """Get current schema version from database."""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT value_json FROM config WHERE key = '_schema_version'"
        ).fetchone()
        conn.close()
        if row:
            import json
            return json.loads(row["value_json"])
        return None
    except sqlite3.OperationalError:
        return None


def set_schema_version(storage: Storage, version: str) -> None:
    """Set schema version in config."""
    storage.set_config("_schema_version", version)


def init_database(db_path: Path | str = DEFAULT_DB_PATH, force: bool = False) -> Storage:
    """Initialize database with schema (idempotent).
    
    Args:
        db_path: Path to SQLite database file
        force: If True, reinitialize even if already exists
        
    Returns:
        Storage instance ready for use
    """
    db_path = Path(db_path)
    
    # Check if already initialized
    current_version = get_schema_version(db_path)
    
    if current_version and not force:
        print(f"Database already initialized (v{current_version})")
        return Storage(db_path)
    
    # Initialize
    print(f"Initializing database at {db_path}...")
    storage = Storage(db_path)
    storage.init_db()
    
    # Set version
    set_schema_version(storage, SCHEMA_VERSION)
    print(f"Database initialized (v{SCHEMA_VERSION})")
    
    return storage


def migrate(db_path: Path | str = DEFAULT_DB_PATH) -> Storage:
    """Run pending migrations.
    
    MVP: Just ensures init_db is called.
    Future: Version-based migration scripts.
    """
    db_path = Path(db_path)
    current_version = get_schema_version(db_path)
    
    if not current_version:
        return init_database(db_path)
    
    # Future: check version and run migrations
    # For now, just return storage
    print(f"Database at v{current_version}, no migrations needed")
    return Storage(db_path)


def reset_database(db_path: Path | str = DEFAULT_DB_PATH) -> Storage:
    """Reset database (delete and recreate).
    
    WARNING: Destroys all data!
    """
    db_path = Path(db_path)
    
    if db_path.exists():
        print(f"Deleting existing database at {db_path}...")
        db_path.unlink()
    
    return init_database(db_path)


# CLI entrypoint
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EURKAI Database Migrations")
    parser.add_argument("command", choices=["init", "migrate", "reset", "version"])
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Database path")
    parser.add_argument("--force", action="store_true", help="Force reinit")
    
    args = parser.parse_args()
    db_path = Path(args.db)
    
    if args.command == "init":
        init_database(db_path, force=args.force)
    elif args.command == "migrate":
        migrate(db_path)
    elif args.command == "reset":
        confirm = input("WARNING: This will delete all data. Type 'yes' to confirm: ")
        if confirm.lower() == "yes":
            reset_database(db_path)
        else:
            print("Aborted")
    elif args.command == "version":
        version = get_schema_version(db_path)
        if version:
            print(f"Schema version: {version}")
        else:
            print("Database not initialized")

# ---- Compatibility shim for CLI/tests ----
def init_db(db_path: str) -> None:
    """Initialize DB schema (idempotent).

    This wrapper exists because the CLI/tests import init_db from
    backend.storage.migrations. It delegates to the best available
    migration entrypoint in this module.
    """
    return migrate(db_path)


def get_db_path(db_path: str | None = None) -> str:
    if db_path:
        return str(db_path)
    return str(DEFAULT_DB_PATH)
