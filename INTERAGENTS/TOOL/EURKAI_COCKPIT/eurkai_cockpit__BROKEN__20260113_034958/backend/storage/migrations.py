"""
EURKAI_COCKPIT — Database Migrations
Version: 1.0.0

MVP: init only (idempotent schema creation).
"""

import os
import sqlite3
from pathlib import Path

# Default paths
DEFAULT_DB_DIR = Path.home() / ".eurkai_cockpit"
DEFAULT_DB_NAME = "cockpit.db"


def get_db_path(db_path: str | None = None) -> Path:
    """
    Get database path from:
    1. Explicit parameter
    2. Environment variable EURKAI_DB_PATH
    3. Default ~/.eurkai_cockpit/cockpit.db
    """
    if db_path:
        return Path(db_path)
    
    env_path = os.environ.get("EURKAI_DB_PATH")
    if env_path:
        return Path(env_path)
    
    return DEFAULT_DB_DIR / DEFAULT_DB_NAME


def get_schema_sql() -> str:
    """Load schema.sql from package."""
    schema_path = Path(__file__).parent / "schema.sql"
    return schema_path.read_text(encoding="utf-8")


def init_db(db_path: str | None = None, force: bool = False) -> Path:
    """
    Initialize database with schema.
    
    Args:
        db_path: Optional explicit path to database
        force: If True, recreate database (WARNING: destroys data)
    
    Returns:
        Path to initialized database
    
    Notes:
        - Idempotent: safe to call multiple times
        - Creates parent directories if needed
        - Uses CREATE TABLE IF NOT EXISTS
    """
    path = get_db_path(db_path)
    
    # Create parent directory
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Force recreate if requested
    if force and path.exists():
        path.unlink()
    
    # Connect and execute schema
    conn = sqlite3.connect(str(path))
    try:
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Execute schema (idempotent due to IF NOT EXISTS)
        schema_sql = get_schema_sql()
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()
    
    return path


def check_db_initialized(db_path: str | None = None) -> bool:
    """Check if database exists and has required tables."""
    path = get_db_path(db_path)
    
    if not path.exists():
        return False
    
    required_tables = [
        "projects", "briefs", "runs", "secrets", 
        "config", "tags", "module_manifests", "backups"
    ]
    
    conn = sqlite3.connect(str(path))
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = {row[0] for row in cursor.fetchall()}
        return all(t in existing_tables for t in required_tables)
    finally:
        conn.close()


if __name__ == "__main__":
    # CLI: python -m backend.storage.migrations
    import sys
    
    force = "--force" in sys.argv
    db_path = None
    
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            db_path = arg
            break
    
    path = init_db(db_path, force=force)
    print(f"Database initialized: {path}")


def get_schema_version(db_path) -> int:
    """Return schema version for a given DB path (fallback to 1)."""
    import sqlite3
    try:
        con = sqlite3.connect(str(db_path))
        cur = con.cursor()
        # config table may or may not exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config'")
        if cur.fetchone():
            cur.execute("SELECT value FROM config WHERE key='schema_version' LIMIT 1")
            row = cur.fetchone()
            if row and row[0] is not None:
                try:
                    return int(row[0])
                except Exception:
                    pass
        return 1
    except Exception:
        return 1
    finally:
        try:
            con.close()
        except Exception:
            pass
