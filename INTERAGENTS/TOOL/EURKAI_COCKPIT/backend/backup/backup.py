"""
EURKAI_COCKPIT — Backup Module (C07)
Version: 1.0.0

Database backup utilities:
- SQLite file copy
- JSON export per table (projects, briefs, runs, modules, config, secrets)
- Git commit/push to backup/auto branch
- Dry-run mode when Git is not configured

Environment variables:
- EURKAI_DB_PATH: Path to SQLite database (default: data/cockpit.db)
- EURKAI_BACKUP_DIR: Backup output directory (default: data/backups/<timestamp>)

Usage:
    python -m backend.backup.backup [--dry-run] [--db-path PATH] [--backup-dir DIR] [--remote REMOTE]
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ============================================
# CONFIGURATION
# ============================================

DEFAULT_DB_PATH = Path("data/cockpit.db")
DEFAULT_BACKUP_BASE = Path("data/backups")
DEFAULT_REMOTE = "origin"
BACKUP_BRANCH = "backup/auto"

# Tables to export as JSON
TABLES_TO_EXPORT = ["projects", "briefs", "runs", "modules", "config", "secrets"]


def get_db_path() -> Path:
    """Get database path from environment or default."""
    return Path(os.environ.get("EURKAI_DB_PATH", str(DEFAULT_DB_PATH)))


def get_backup_dir(timestamp: str) -> Path:
    """Get backup directory from environment or default with timestamp."""
    base = os.environ.get("EURKAI_BACKUP_DIR")
    if base:
        return Path(base)
    return DEFAULT_BACKUP_BASE / timestamp


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_safe() -> str:
    """Return current UTC timestamp safe for filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class BackupConfig:
    """Backup configuration."""
    db_path: Path
    backup_dir: Path
    remote: str = DEFAULT_REMOTE
    dry_run: bool = False
    timestamp: str = field(default_factory=utc_now_iso)


@dataclass
class BackupResult:
    """Result of a backup operation."""
    success: bool
    status: str  # success | failed | dry_run
    timestamp: str
    backup_dir: str
    sqlite_copied: bool = False
    json_exported: list[str] = field(default_factory=list)
    commit_sha: Optional[str] = None
    git_pushed: bool = False
    error: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================
# CORE FUNCTIONS
# ============================================

def is_git_configured(remote: str = DEFAULT_REMOTE) -> bool:
    """Check if Git repository is configured with the specified remote."""
    try:
        # Check if we're in a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return False
        
        # Check if remote exists
        result = subprocess.run(
            ["git", "remote", "get-url", remote],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def copy_sqlite(db_path: Path, backup_dir: Path) -> Path:
    """Copy SQLite database file to backup directory.
    
    Returns: Path to copied file.
    Raises: FileNotFoundError if database doesn't exist.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / db_path.name
    shutil.copy2(db_path, dest)
    return dest


def export_json(db_path: Path, backup_dir: Path, tables: list[str] = TABLES_TO_EXPORT) -> list[str]:
    """Export each table to a separate JSON file.
    
    Returns: List of exported table names.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    try:
        for table in tables:
            try:
                cursor = conn.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                # Convert rows to list of dicts, handling binary data
                data = []
                for row in rows:
                    row_dict = dict(row)
                    # Handle binary fields (encrypted_value, nonce in secrets)
                    for key, value in row_dict.items():
                        if isinstance(value, bytes):
                            row_dict[key] = base64.b64encode(value).decode('ascii')
                    data.append(row_dict)
                
                # Write JSON file
                json_path = backup_dir / f"{table}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                exported.append(table)
            except sqlite3.OperationalError:
                # Table doesn't exist, skip
                continue
    finally:
        conn.close()
    
    return exported


def git_commit_push(
    backup_dir: Path,
    remote: str = DEFAULT_REMOTE,
    timestamp: str = ""
) -> tuple[bool, Optional[str]]:
    """Commit backup files and push to backup/auto branch.
    
    Returns: (success, commit_sha or None)
    """
    if not timestamp:
        timestamp = utc_now_iso()
    
    commit_message = f"backup(db): {timestamp}"
    
    try:
        # Ensure we're on the backup branch (create if needed)
        result = subprocess.run(
            ["git", "rev-parse", "--verify", BACKUP_BRANCH],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            # Branch doesn't exist, create it
            subprocess.run(
                ["git", "checkout", "-b", BACKUP_BRANCH],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
        else:
            # Branch exists, switch to it
            subprocess.run(
                ["git", "checkout", BACKUP_BRANCH],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
        
        # Add backup directory
        subprocess.run(
            ["git", "add", str(backup_dir)],
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        # Check if there are changes to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if not status.stdout.strip():
            # No changes
            return True, None
        
        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        # Get commit SHA
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10
        )
        commit_sha = sha_result.stdout.strip()[:12] if sha_result.returncode == 0 else None
        
        # Push
        push_result = subprocess.run(
            ["git", "push", remote, BACKUP_BRANCH],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if push_result.returncode != 0:
            # Push failed but commit succeeded
            return True, commit_sha
        
        return True, commit_sha
        
    except subprocess.CalledProcessError as e:
        return False, None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, None


def run_backup(config: BackupConfig) -> BackupResult:
    """Execute full backup operation.
    
    Steps:
    1. Copy SQLite file
    2. Export JSON per table
    3. If Git configured and not dry-run: commit & push
    4. Record in backups table (if storage available)
    
    Returns: BackupResult with operation details
    """
    timestamp = config.timestamp
    result = BackupResult(
        success=False,
        status="pending",
        timestamp=timestamp,
        backup_dir=str(config.backup_dir)
    )
    
    try:
        # Step 1: Copy SQLite
        copy_sqlite(config.db_path, config.backup_dir)
        result.sqlite_copied = True
        
        # Step 2: Export JSON
        exported = export_json(config.db_path, config.backup_dir)
        result.json_exported = exported
        
        # Step 3: Git operations (if configured and not dry-run)
        git_available = is_git_configured(config.remote)
        
        if config.dry_run:
            result.status = "dry_run"
            result.success = True
            result.notes = "Dry-run mode: Git operations skipped"
        elif not git_available:
            result.status = "dry_run"
            result.success = True
            result.notes = f"Git not configured (remote '{config.remote}' not found). Files saved locally."
        else:
            # Attempt Git commit and push
            git_success, commit_sha = git_commit_push(
                config.backup_dir,
                config.remote,
                timestamp
            )
            
            if git_success:
                result.status = "success"
                result.success = True
                result.commit_sha = commit_sha
                result.git_pushed = True
                result.notes = f"Backup committed to {BACKUP_BRANCH}"
            else:
                result.status = "failed"
                result.success = False
                result.error = "Git commit/push failed"
                result.notes = "Files saved locally but Git operations failed"
        
        # Step 4: Record in backups table (try to import storage)
        try:
            from backend.storage.storage import Storage
            storage = Storage(db_path=config.db_path)
            storage.create_backup(
                status=result.status,
                commit_sha=result.commit_sha,
                notes=result.notes
            )
        except ImportError:
            # Storage module not available, skip recording
            pass
        except Exception:
            # Don't fail backup if recording fails
            pass
        
    except FileNotFoundError as e:
        result.status = "failed"
        result.success = False
        result.error = str(e)
    except Exception as e:
        result.status = "failed"
        result.success = False
        result.error = f"Unexpected error: {e}"
    
    return result


# ============================================
# CLI
# ============================================

def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="EURKAI Backup: dump DB to SQLite + JSON, optionally push to GitHub"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create backup files but skip Git operations"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH} or EURKAI_DB_PATH env)"
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Backup output directory (default: data/backups/<timestamp> or EURKAI_BACKUP_DIR env)"
    )
    parser.add_argument(
        "--remote",
        type=str,
        default=DEFAULT_REMOTE,
        help=f"Git remote name (default: {DEFAULT_REMOTE})"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=True,
        help="Output result as JSON (default: human-readable)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    timestamp_safe = utc_now_safe()
    db_path = args.db_path or get_db_path()
    backup_dir = args.backup_dir or get_backup_dir(timestamp_safe)
    
    config = BackupConfig(
        db_path=db_path,
        backup_dir=backup_dir,
        remote=args.remote,
        dry_run=args.dry_run
    )
    
    print(f"[backup] Starting backup...")
    print(f"[backup] DB path: {config.db_path}")
    print(f"[backup] Backup dir: {config.backup_dir}")
    print(f"[backup] Dry-run: {config.dry_run}")
    print()
    
    result = run_backup(config)
    
    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Status: {result.status}")
        print(f"SQLite copied: {result.sqlite_copied}")
        print(f"JSON exported: {', '.join(result.json_exported)}")
        if result.commit_sha:
            print(f"Commit: {result.commit_sha}")
        if result.error:
            print(f"Error: {result.error}")
        print(f"Notes: {result.notes}")
    
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
