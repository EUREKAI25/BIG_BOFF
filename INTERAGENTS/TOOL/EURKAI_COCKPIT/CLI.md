# EURKAI_COCKPIT — CLI Documentation

## Overview

The CLI provides a command-line interface for orchestrating the cockpit workflow.
It operates directly on the SQLite database (C02 storage layer) and does **not** execute any AI models.

**Version**: 1.0.0

## Installation

```bash
# Dependencies
pip install click cryptography

# Set encryption key (required for secrets)
export EURKAI_SECRET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

## Commands

### `cockpit init`

Initialize database and default config. **Idempotent** — safe to run multiple times.

```bash
cockpit init [--db-path PATH]
```

**Options:**
- `--db-path PATH`: Override default database path (`data/eurkai.db`)

**Example:**
```bash
cockpit init
# ✓ Database created at data/eurkai.db
# ✓ Config version: 1.0.0

cockpit init  # Run again
# ✓ Database already initialized at data/eurkai.db
```

---

### `cockpit project add`

Add a new project.

```bash
cockpit project add NAME [OPTIONS]
```

**Arguments:**
- `NAME`: Project name (required)

**Options:**
- `-d, --desc TEXT`: Project description
- `-p, --path TEXT`: Root path of project
- `-t, --tags TEXT`: Comma-separated tags
- `--json`: Output as JSON (machine-readable)

**Example:**
```bash
cockpit project add "My Agent" --desc "AI agent project" --tags "ai,agent"
# ✓ Project created: My Agent (a1b2c3d4-...)

cockpit project add "API Project" --json
# {"id": "...", "name": "API Project", ...}
```

---

### `cockpit project list`

List all projects.

```bash
cockpit project list [--json]
```

**Options:**
- `--json`: Output as JSON array

**Example:**
```bash
cockpit project list
# ID       | Name       | Description    | Tags     | Created
# -------- | ---------- | -------------- | -------- | ----------
# a1b2c3d4 | My Agent   | AI agent proj  | ai,agent | 2025-01-12

cockpit project list --json
# [{"id": "...", "name": "My Agent", ...}]
```

---

### `cockpit brief add`

Add a brief to a project.

```bash
cockpit brief add PROJECT_ID TITLE [OPTIONS]
```

**Arguments:**
- `PROJECT_ID`: Target project ID (required)
- `TITLE`: Brief title (required)

**Options:**
- `-u, --user-prompt TEXT`: User prompt (required)
- `-g, --goal TEXT`: Brief goal
- `-s, --system-prompt TEXT`: System prompt
- `-e, --expected TEXT`: Expected output description
- `-t, --tags TEXT`: Comma-separated tags
- `--json`: Output as JSON

**Example:**
```bash
cockpit brief add a1b2c3d4 "Code Generator" \
  --user-prompt "Generate Python code" \
  --goal "Create working code" \
  --system-prompt "You are a code assistant"
# ✓ Brief created: Code Generator (b2c3d4e5-...)
```

---

### `cockpit brief list`

List briefs, optionally filtered by project.

```bash
cockpit brief list [OPTIONS]
```

**Options:**
- `-p, --project-id ID`: Filter by project
- `--json`: Output as JSON array

---

### `cockpit run start`

Create a new run for a brief. **Does not execute** — creates a `pending` run for future execution by a runner (C08+).

```bash
cockpit run start BRIEF_ID [--json]
```

**Arguments:**
- `BRIEF_ID`: Brief to run (required)

**Example:**
```bash
cockpit run start b2c3d4e5
# ✓ Run created: c3d4e5f6-...
#   Brief: Code Generator
#   Status: pending
#   Note: Run is pending. Use a runner (C08+) to execute.
```

---

### `cockpit run list`

List runs, optionally filtered by brief.

```bash
cockpit run list [OPTIONS]
```

**Options:**
- `-b, --brief-id ID`: Filter by brief
- `--json`: Output as JSON array

---

### `cockpit export`

Export full database (SQLite + JSON dump).

```bash
cockpit export [--output DIR] [--json]
```

**Options:**
- `-o, --output DIR`: Output directory (default: `export/`)
- `--json`: Output result as JSON

**Output files:**
- `eurkai_YYYYMMDD_HHMMSS.db`: SQLite database copy
- `eurkai_YYYYMMDD_HHMMSS.json`: JSON dump (all entities)

**JSON structure:**
```json
{
  "version": "1.0.0",
  "exported_at": "2025-01-12T15:30:00Z",
  "data": {
    "projects": [...],
    "briefs": [...],
    "runs": [...],
    "modules": [...],
    "config": [...],
    "secrets": [...]  // Encrypted (hex-encoded)
  }
}
```

**Example:**
```bash
cockpit export --output ./backup
# ✓ Export completed to ./backup/
#   Database: eurkai_20250112_153000.db
#   JSON: eurkai_20250112_153000.json
#   Projects: 3
#   Briefs: 5
#   Runs: 10
#   Secrets: 2 (encrypted)
```

---

### `cockpit import`

Import data from JSON export. Imports: **projects, briefs, modules, config**.
Does NOT import: **runs, secrets** (as per policy).

```bash
cockpit import FILE [--json]
```

**Arguments:**
- `FILE`: Path to JSON export file (required)

**Behavior:**
- Skips existing records (by ID)
- Validates project references for briefs
- Does not overwrite existing data

**Example:**
```bash
cockpit import ./backup/eurkai_20250112_153000.json
# ✓ Import completed from eurkai_20250112_153000.json
#   Projects: 2
#   Briefs: 4
#   Modules: 1
#   Config: 3
#   Skipped (existing): 1
#   Note: runs and secrets not imported
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EURKAI_DB_PATH` | Database path | `data/eurkai.db` |
| `EURKAI_SECRET_KEY` | Fernet encryption key | (required for secrets) |

---

## Machine-Readable Output

All commands support `--json` flag for machine-readable output:

```bash
# Pipeline example
cockpit project list --json | jq '.[0].id'
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid input, missing resource, etc.) |

---

## Integration Example

```bash
#!/bin/bash
# Automated workflow

# Initialize
cockpit init

# Create project
PROJECT_ID=$(cockpit project add "AutoProject" --json | jq -r '.id')

# Create brief
BRIEF_ID=$(cockpit brief add "$PROJECT_ID" "AutoBrief" \
  --user-prompt "Generate code" --json | jq -r '.id')

# Create run (pending)
RUN_ID=$(cockpit run start "$BRIEF_ID" --json | jq -r '.run_id')

echo "Created run: $RUN_ID"

# Export for backup
cockpit export --output ./backup
```

---

## Architecture Notes

The CLI is a **local orchestration tool**, not an execution engine.

```
┌─────────────┐
│   CLI C05   │  ← Commands
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Storage C02 │  ← SQLite CRUD
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Runner C08 │  ← Future: AI execution
└─────────────┘
```

The CLI:
- ✅ Creates/lists/exports data
- ✅ Creates pending runs
- ❌ Does NOT execute AI models
- ❌ Does NOT call external APIs

Execution is delegated to future runner modules (C08+).
