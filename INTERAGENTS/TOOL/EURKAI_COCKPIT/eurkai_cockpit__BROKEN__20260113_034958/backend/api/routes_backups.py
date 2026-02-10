"""
EURKAI_COCKPIT — Backups API Routes
Version: 1.0.0

Backup flow (C01 SPEC_V1):
- Export .db + .json
- Git commit if configured, else dry_run
"""

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, status

from ..models import BackupTrigger
from .deps import StorageDep, TokenDep, success_response, validation_error

router = APIRouter(prefix="/api/backups", tags=["backups"])


def get_backup_dir() -> Path:
    """Get backup directory."""
    base = os.environ.get("EURKAI_BACKUP_DIR")
    if base:
        return Path(base)
    return Path.home() / ".eurkai_cockpit" / "backups"


def is_git_configured() -> bool:
    """Check if git is available and repo is initialized."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            cwd=get_backup_dir().parent
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def export_database(storage: StorageDep, backup_dir: Path, timestamp: str) -> dict:
    """Export database to backup files."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Export .db copy
    db_path = storage.db_path
    db_backup = backup_dir / f"cockpit_{timestamp}.db"
    shutil.copy2(db_path, db_backup)
    
    # Export .json (all data)
    data = {
        "timestamp": timestamp,
        "projects": storage.list_projects(),
        "briefs": storage.list_briefs(),
        "config": storage.list_config(),
        "modules": storage.list_modules(),
        "tags": storage.list_tags(),
        # Note: secrets not exported in JSON (security)
        # Note: runs not exported (can be large)
    }
    
    json_backup = backup_dir / f"cockpit_{timestamp}.json"
    with open(json_backup, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return {
        "db_path": str(db_backup),
        "json_path": str(json_backup)
    }


def git_commit(backup_dir: Path, message: str) -> str | None:
    """Commit backup files to git."""
    try:
        cwd = backup_dir.parent
        
        # Add files
        subprocess.run(["git", "add", str(backup_dir)], cwd=cwd, check=True)
        
        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return None
        
        # Get commit SHA
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        return sha_result.stdout.strip() if sha_result.returncode == 0 else None
        
    except Exception:
        return None


@router.get("")
async def list_backups(storage: StorageDep, _: TokenDep):
    """GET /api/backups — Historique backups."""
    backups = storage.list_backups()
    return success_response(backups)


@router.post("/dry-run")
async def backup_dry_run(
    storage: StorageDep, 
    _: TokenDep,
    data: BackupTrigger | None = None
):
    """
    POST /api/backups/dry-run — Test sans commit.
    Creates local backup files only.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_dir = get_backup_dir()
    
    # Export files
    files = export_database(storage, backup_dir, timestamp)
    
    # Log backup
    backup = storage.create_backup(
        status="dry_run",
        notes=data.notes if data else None
    )
    
    return success_response({
        "id": backup["id"],
        "status": "dry_run",
        "files": files,
        "timestamp": backup["timestamp"]
    })


@router.post("")
async def trigger_backup(
    storage: StorageDep, 
    _: TokenDep,
    data: BackupTrigger | None = None
):
    """
    POST /api/backups — Déclencher backup.
    
    - If git configured: commit to backup/auto branch
    - If git not configured: dry_run (local dump only)
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_dir = get_backup_dir()
    
    # Export files
    files = export_database(storage, backup_dir, timestamp)
    
    # Try git commit
    commit_sha = None
    status_str = "dry_run"
    
    if is_git_configured():
        message = f"Backup {timestamp}"
        if data and data.notes:
            message += f": {data.notes}"
        
        commit_sha = git_commit(backup_dir, message)
        if commit_sha:
            status_str = "success"
        else:
            status_str = "failed"
    
    # Log backup
    backup = storage.create_backup(
        status=status_str,
        commit_sha=commit_sha,
        notes=data.notes if data else None
    )
    
    return success_response({
        "id": backup["id"],
        "status": status_str,
        "commit_sha": commit_sha,
        "files": files,
        "timestamp": backup["timestamp"]
    })
