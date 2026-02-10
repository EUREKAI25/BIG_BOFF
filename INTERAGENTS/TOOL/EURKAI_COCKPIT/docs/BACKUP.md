# EURKAI_COCKPIT — Backup Documentation (C07)

Version: 1.0.0

## Overview

The backup module provides database backup functionality for EURKAI_COCKPIT:

- **SQLite copy**: Creates a direct copy of the database file
- **JSON export**: Exports each table as a separate JSON file for readability and Git diff
- **Git integration**: Commits and pushes to `backup/auto` branch
- **Dry-run mode**: Always produces artifacts, even without Git

## Quick Start

### Basic dry-run (no Git required)

```bash
python -m backend.backup.backup --dry-run
```

### Full backup with Git push

```bash
python -m backend.backup.backup
```

### Custom paths

```bash
python -m backend.backup.backup \
  --db-path /path/to/eurkai.db \
  --backup-dir /path/to/backups/20260112 \
  --remote origin
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EURKAI_DB_PATH` | `data/cockpit.db` | Path to SQLite database |
| `EURKAI_BACKUP_DIR` | `data/backups/<timestamp>/` | Backup output directory |

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dry-run` | false | Create files but skip Git operations |
| `--db-path` | env or default | Path to SQLite database |
| `--backup-dir` | env or default | Backup output directory |
| `--remote` | `origin` | Git remote name |
| `--json` | true | Output result as JSON |

## Output Structure

A backup creates the following structure:

```
data/backups/20260112_183000/
├── cockpit.db          # SQLite file copy
├── projects.json       # Projects table
├── briefs.json         # Briefs table
├── runs.json           # Runs table
├── modules.json        # Modules table
├── config.json         # Config table
└── secrets.json        # Secrets (encrypted values as base64)
```

## Git Behavior

### Branch Strategy

- **Target branch**: `backup/auto`
- **Never commits to**: `main` or any other branch
- **Auto-creates**: Branch created if it doesn't exist

### Commit Format

```
backup(db): 2026-01-12T18:30:00Z
```

### Dry-run Conditions

The backup runs in dry-run mode when:

1. `--dry-run` flag is passed
2. Git is not installed
3. Not inside a Git repository
4. Remote doesn't exist

In all cases, backup files are **always created locally**.

## Programmatic Usage

```python
from backend.backup.backup import BackupConfig, run_backup
from pathlib import Path

config = BackupConfig(
    db_path=Path("data/cockpit.db"),
    backup_dir=Path("data/backups/20260112"),
    remote="origin",
    dry_run=False
)

result = run_backup(config)

if result.success:
    print(f"Backup complete: {result.status}")
    print(f"Commit: {result.commit_sha}")
else:
    print(f"Backup failed: {result.error}")
```

### BackupResult Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Overall success |
| `status` | str | `success`, `failed`, or `dry_run` |
| `timestamp` | str | ISO 8601 timestamp |
| `backup_dir` | str | Path to backup directory |
| `sqlite_copied` | bool | SQLite file copied |
| `json_exported` | list[str] | Tables exported as JSON |
| `commit_sha` | str? | Git commit SHA (12 chars) |
| `git_pushed` | bool | Push succeeded |
| `error` | str? | Error message if failed |
| `notes` | str | Additional notes |

## Cron Setup

### Daily backup at 2 AM

```cron
0 2 * * * cd /path/to/eurkai && python -m backend.backup.backup >> /var/log/eurkai-backup.log 2>&1
```

### With environment variables

```cron
0 2 * * * EURKAI_DB_PATH=/data/prod.db EURKAI_BACKUP_DIR=/backups cd /path/to/eurkai && python -m backend.backup.backup
```

### Verify cron is working

```bash
# List current crontab
crontab -l

# Edit crontab
crontab -e

# Check logs
tail -f /var/log/eurkai-backup.log
```

## Security Notes

### Secrets Handling

- Secrets are **always encrypted** in the database
- JSON export contains `encrypted_value` as **base64**
- Original encryption key is **never stored** in backups
- To restore secrets, you need the original `EURKAI_SECRET_KEY`

### Git Security

- Never push to `main` branch
- Use `backup/auto` branch for isolation
- Consider using a private repository
- GitHub Actions can auto-delete old backups

## Integration with Storage

The backup module integrates with C02 storage:

```python
# Backup automatically records to backups table
storage.create_backup(
    status="success",
    commit_sha="abc123def",
    notes="Backup to backup/auto"
)

# List backup history
backups = storage.list_backups(limit=10)
```

## Troubleshooting

### Git not configured

```
[backup] Git not configured (remote 'origin' not found). Files saved locally.
```

**Solution**: Initialize Git and add remote:

```bash
git init
git remote add origin git@github.com:user/repo.git
```

### Database not found

```
[backup] Error: Database not found: /path/to/db
```

**Solution**: Set correct path:

```bash
export EURKAI_DB_PATH=/correct/path/to/cockpit.db
```

### Push failed

```
[backup] Files saved locally but Git operations failed
```

**Solution**: Check Git permissions and network:

```bash
git push origin backup/auto
```

## API Reference

### Functions

#### `run_backup(config: BackupConfig) -> BackupResult`

Execute full backup operation.

#### `copy_sqlite(db_path: Path, backup_dir: Path) -> Path`

Copy SQLite file to backup directory.

#### `export_json(db_path: Path, backup_dir: Path, tables: list[str]) -> list[str]`

Export tables as JSON files.

#### `git_commit_push(backup_dir: Path, remote: str, timestamp: str) -> tuple[bool, str?]`

Commit and push to `backup/auto` branch.

#### `is_git_configured(remote: str) -> bool`

Check if Git repository and remote are configured.

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-12 | Initial release (C07) |
