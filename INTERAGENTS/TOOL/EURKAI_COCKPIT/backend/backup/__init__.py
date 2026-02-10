"""
EURKAI_COCKPIT — Backup Module (C07)
Version: 1.0.0

Database backup utilities:
- SQLite file copy
- JSON export per table
- Git commit/push to backup/auto branch
- Dry-run mode when Git is not configured
"""

from .backup import (
    BackupConfig,
    BackupResult,
    run_backup,
    export_json,
    copy_sqlite,
    git_commit_push,
    is_git_configured,
)

__all__ = [
    "BackupConfig",
    "BackupResult",
    "run_backup",
    "export_json",
    "copy_sqlite",
    "git_commit_push",
    "is_git_configured",
]
