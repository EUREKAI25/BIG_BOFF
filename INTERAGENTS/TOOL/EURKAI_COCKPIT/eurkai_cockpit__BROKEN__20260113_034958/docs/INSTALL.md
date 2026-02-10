# EURKAI_COCKPIT — Installation Guide

## Prerequisites

| Requirement | Version | Status |
|-------------|---------|--------|
| Python | >= 3.11 | **Required** |
| Git | Any | Optional (for backups) |
| npm/Node.js | >= 18 | Optional (for frontend) |
| SQLite | (stdlib) | Included with Python |

## Quick Install (One-Shot)

```bash
# From Downloads or wherever you extracted EURKAI_COCKPIT:
bash scripts/install_all.sh
```

This single command will:
1. ✅ Verify Python version
2. ✅ Create target directory (`~/.eurkai_cockpit/`)
3. ✅ Install Python dependencies
4. ✅ Build frontend (if present)
5. ✅ Initialize database
6. ✅ Run all tests
7. ✅ Generate validation report

## Installation Options

### Custom Target Directory

```bash
bash scripts/install_all.sh --target /opt/eurkai
```

### Skip Tests (Quick Install)

```bash
bash scripts/install_all.sh --skip-tests
```

### Dry Run (Preview)

```bash
bash scripts/install_all.sh --dry-run
```

### All Options

```
--target DIR       Installation directory (default: ~/.eurkai_cockpit)
--skip-tests       Skip test execution
--skip-frontend    Skip frontend even if present
--dry-run          Preview without making changes
--help             Show help message
```

## Manual Installation

If you prefer manual steps:

### 1. Create Directory Structure

```bash
mkdir -p ~/.eurkai_cockpit/{data,logs,backups}
cd ~/.eurkai_cockpit
```

### 2. Copy Files

```bash
cp -r /path/to/source/{backend,cli,tests,docs} .
cp /path/to/source/requirements.txt .
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
export EURKAI_DB_PATH="$HOME/.eurkai_cockpit/data/cockpit.db"
python -c "from backend.storage.migrations import init_db; init_db()"
```

### 5. Verify Installation

```bash
python -m pytest tests/ -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EURKAI_DB_PATH` | Database file path | `~/.eurkai_cockpit/data/cockpit.db` |
| `EURKAI_MASTER_PASSWORD` | Master password for secrets | None (required for secrets) |
| `EURKAI_TOKEN` | API authentication token | None (auth disabled) |
| `EURKAI_BACKUP_DIR` | Backup output directory | `~/.eurkai_cockpit/backups` |
| `EURKAI_AUDIT_LOG` | Audit log file path | Console only |

### Example .env Setup

```bash
# ~/.eurkai_cockpit/.env
export EURKAI_DB_PATH="$HOME/.eurkai_cockpit/data/cockpit.db"
export EURKAI_MASTER_PASSWORD="your-secure-password-here"
export EURKAI_BACKUP_DIR="$HOME/.eurkai_cockpit/backups"
```

## Post-Installation

### Start API Server

```bash
cd ~/.eurkai_cockpit
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

API will be available at:
- http://127.0.0.1:8000 — Root
- http://127.0.0.1:8000/docs — Swagger UI
- http://127.0.0.1:8000/health — Health check

### Use CLI

```bash
# Initialize (if not done)
python -m cli.cli init

# List projects
python -m cli.cli project list

# Create project
python -m cli.cli project create "My Project"

# Help
python -m cli.cli --help
```

### Run Backup

```bash
# Dry run (local files only)
python -m backend.backup.backup --dry-run

# Full backup (requires Git)
python -m backend.backup.backup
```

## Troubleshooting

### Python Version Error

```
Error: Python >= 3.11 required
```

**Solution:** Install Python 3.11+ from https://www.python.org/downloads/

### Dependency Installation Failed

```
Error: pip install failed
```

**Solutions:**
1. Try with `--user` flag: `pip install -r requirements.txt --user`
2. Use virtual environment: `python -m venv venv && source venv/bin/activate`
3. On Debian/Ubuntu with externally-managed Python: `pip install --break-system-packages`

### Database Not Found

```
Error: Database not found at ~/.eurkai_cockpit/data/cockpit.db
```

**Solution:** Run initialization:
```bash
python -m cli.cli init
```

### Tests Failing

Check the test output log:
```bash
cat ~/.eurkai_cockpit/logs/test_output.log
```

Common issues:
- Missing `EURKAI_MASTER_PASSWORD` for secrets tests
- Database locked by another process

## Uninstallation

```bash
# Remove installation directory
rm -rf ~/.eurkai_cockpit

# Remove from path (if added)
# Edit ~/.bashrc or ~/.zshrc
```

## Upgrading

The installer is **idempotent** — run it again to upgrade:

```bash
# Backup first
python -m backend.backup.backup

# Re-run installer
bash scripts/install_all.sh
```

Your data in `data/` will be preserved.

---

*Documentation generated for EURKAI_COCKPIT C08*
