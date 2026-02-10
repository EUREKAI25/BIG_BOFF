# EURKAI_COCKPIT — Storage Documentation

**Version**: 1.0.0  
**Date**: 2025-01-12  
**Status**: STABLE

---

## Overview

The storage layer provides SQLite-based persistence for EURKAI_COCKPIT with:

- **CRUD operations** for all entities
- **Fernet encryption** for secrets
- **UUID identifiers** (generated Python-side)
- **JSON storage** for tags, variables, manifests
- **Idempotent initialization**
- **Cascade deletes** for referential integrity

---

## Quick Start

### 1. Environment Setup

```bash
# Generate encryption key (required for secrets)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set environment variable
export EURKAI_SECRET_KEY="your-generated-key-here"
```

### 2. Initialize Database

```python
from backend.storage import init_database, Storage

# Option 1: Using helper function
storage = init_database("data/eurkai.db")

# Option 2: Manual initialization
storage = Storage("data/eurkai.db")
storage.init_db()
```

### 3. Basic Usage

```python
# Create project
project = storage.create_project(
    name="My Project",
    description="Project description",
    tags=["ai", "automation"]
)

# Create brief
brief = storage.create_brief(
    project_id=project.id,
    title="Generate Report",
    user_prompt="Create a detailed report about...",
    goal="Produce a comprehensive analysis",
    tags=["report", "analysis"]
)

# Create run
run = storage.create_run(brief_id=brief.id, model="claude-3")

# Update run status
storage.update_run(
    run.id,
    status="success",
    result_json={"output": "Report generated"},
    duration_ms=1500
)
```

---

## Data Model

### Entity Relationship

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Project   │──1:N──│    Brief    │──1:N──│     Run     │
└─────────────┘       └─────────────┘       └─────────────┘
       │
       │ (optional)
       ▼
┌─────────────┐
│   Secret    │ (project-scoped or global)
└─────────────┘

┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Config    │       │   Module    │       │   Backup    │
│ (key/value) │       │ (registry)  │       │ (history)   │
└─────────────┘       └─────────────┘       └─────────────┘
```

### Tables

#### Projects

| Field | Type | Description |
|-------|------|-------------|
| id | TEXT (UUID) | Primary key |
| name | TEXT | Project name (required) |
| description | TEXT | Optional description |
| root_path | TEXT | Project root directory |
| tags | TEXT (JSON) | Array of tag strings |
| created_at | TEXT (ISO) | Creation timestamp |
| updated_at | TEXT (ISO) | Last update timestamp |

#### Briefs

| Field | Type | Description |
|-------|------|-------------|
| id | TEXT (UUID) | Primary key |
| project_id | TEXT (UUID) | FK to projects (required) |
| title | TEXT | Brief title (required) |
| goal | TEXT | What the brief should achieve |
| system_prompt | TEXT | System instructions |
| user_prompt | TEXT | User prompt (required) |
| variables_json | TEXT (JSON) | Template variables |
| expected_output | TEXT | Expected result description |
| tags | TEXT (JSON) | Array of tag strings |
| policy | TEXT (JSON) | Execution policy |
| created_at | TEXT (ISO) | Creation timestamp |
| updated_at | TEXT (ISO) | Last update timestamp |

#### Runs

| Field | Type | Description |
|-------|------|-------------|
| id | TEXT (UUID) | Primary key |
| run_id | TEXT | Unique run identifier |
| brief_id | TEXT (UUID) | FK to briefs (required) |
| status | TEXT | pending/running/success/failed |
| result_json | TEXT (JSON) | Execution result |
| logs_json | TEXT (JSON) | Execution logs array |
| error | TEXT | Error message if failed |
| model | TEXT | Model used |
| duration_ms | INTEGER | Execution duration |
| started_at | TEXT (ISO) | Start timestamp |
| finished_at | TEXT (ISO) | Completion timestamp |
| created_at | TEXT (ISO) | Creation timestamp |

#### Config

| Field | Type | Description |
|-------|------|-------------|
| id | TEXT (UUID) | Primary key |
| key | TEXT | Configuration key (unique) |
| value_json | TEXT (JSON) | Configuration value |
| updated_at | TEXT (ISO) | Last update timestamp |

#### Secrets

| Field | Type | Description |
|-------|------|-------------|
| id | TEXT (UUID) | Primary key |
| key | TEXT | Secret key name |
| encrypted_value | BLOB | Fernet-encrypted value |
| nonce | BLOB | Reserved for AES-GCM migration |
| scope | TEXT | "global" or "project" |
| project_id | TEXT (UUID) | FK to projects (if scoped) |
| created_at | TEXT (ISO) | Creation timestamp |
| updated_at | TEXT (ISO) | Last update timestamp |

#### Modules

| Field | Type | Description |
|-------|------|-------------|
| id | TEXT (UUID) | Primary key |
| name | TEXT | Module name (unique) |
| version | TEXT | SemVer version |
| description | TEXT | Module description |
| manifest_json | TEXT (JSON) | Full ModuleManifest |
| enabled | INTEGER | 1=enabled, 0=disabled |
| created_at | TEXT (ISO) | Registration timestamp |
| updated_at | TEXT (ISO) | Last update timestamp |

#### Backups

| Field | Type | Description |
|-------|------|-------------|
| id | TEXT (UUID) | Primary key |
| timestamp | TEXT (ISO) | Backup timestamp |
| commit_sha | TEXT | Git commit SHA (if applicable) |
| status | TEXT | success/failed/dry_run |
| notes | TEXT | Optional notes |
| created_at | TEXT (ISO) | Record creation timestamp |

---

## Module Manifest Schema

```json
{
  "name": "module-name",
  "version": "1.0.0",
  "description": "Module description",
  "inputs": [
    {
      "name": "input_name",
      "type": "string|number|boolean|object|array|file",
      "required": true
    }
  ],
  "outputs": [
    {
      "name": "output_name",
      "type": "string|number|boolean|object|array|file"
    }
  ],
  "constraints": {
    "hard": ["constraint1"],
    "soft": ["preference1"]
  },
  "tags": ["tag1", "tag2"],
  "enabled": true
}
```

---

## API Reference

### Storage Class

```python
class Storage:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH)
    def init_db(self) -> None
    
    # Projects
    def create_project(name, description=None, root_path=None, tags=None) -> Project
    def get_project(project_id) -> Optional[Project]
    def list_projects() -> list[Project]
    def update_project(project_id, **kwargs) -> Optional[Project]
    def delete_project(project_id) -> bool
    
    # Briefs
    def create_brief(project_id, title, user_prompt, **kwargs) -> Brief
    def get_brief(brief_id) -> Optional[Brief]
    def list_briefs(project_id=None) -> list[Brief]
    def update_brief(brief_id, **kwargs) -> Optional[Brief]
    def delete_brief(brief_id) -> bool
    
    # Runs
    def create_run(brief_id, run_id=None, **kwargs) -> Run
    def get_run(run_id) -> Optional[Run]
    def list_runs(brief_id=None) -> list[Run]
    def update_run(run_id, **kwargs) -> Optional[Run]
    def delete_run(run_id) -> bool
    
    # Config
    def set_config(key, value) -> Config
    def get_config(key) -> Optional[Config]
    def list_config() -> list[Config]
    def delete_config(key) -> bool
    
    # Secrets
    def create_secret(key, plaintext, scope="global", project_id=None) -> Secret
    def get_secret(secret_id) -> Optional[Secret]
    def get_secret_by_key(key, scope="global", project_id=None) -> Optional[Secret]
    def decrypt_secret(secret) -> str
    def list_secrets(scope=None, project_id=None) -> list[Secret]
    def update_secret(secret_id, plaintext) -> Optional[Secret]
    def delete_secret(secret_id) -> bool
    
    # Modules
    def create_module(manifest: ModuleManifest) -> Module
    def get_module(module_id) -> Optional[Module]
    def get_module_by_name(name) -> Optional[Module]
    def list_modules(enabled_only=False) -> list[Module]
    def update_module(module_id, **kwargs) -> Optional[Module]
    def delete_module(module_id) -> bool
    
    # Backups
    def create_backup(status, commit_sha=None, notes=None) -> Backup
    def list_backups(limit=50) -> list[Backup]
```

---

## Migrations

### CLI Commands

```bash
# Initialize database
python -m backend.storage.migrations init --db data/eurkai.db

# Run migrations (MVP: same as init)
python -m backend.storage.migrations migrate --db data/eurkai.db

# Check version
python -m backend.storage.migrations version --db data/eurkai.db

# Reset (DANGER: deletes all data)
python -m backend.storage.migrations reset --db data/eurkai.db
```

### Programmatic

```python
from backend.storage import init_database, migrate, reset_database

# Initialize (idempotent)
storage = init_database("data/eurkai.db")

# Run migrations
storage = migrate("data/eurkai.db")

# Reset (destructive!)
storage = reset_database("data/eurkai.db")
```

---

## Security

### Encryption

- **Algorithm**: Fernet (AES-128-CBC + HMAC)
- **Key storage**: Environment variable `EURKAI_SECRET_KEY`
- **Future**: Migration path to AES-256-GCM (nonce field reserved)

### Best Practices

1. Never commit encryption key to version control
2. Use environment variables or secure vault
3. Rotate keys periodically
4. Backup keys separately from database

### Key Generation

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Store this securely
```

---

## Testing

```bash
# Run all storage tests
python -m pytest tests/test_storage.py -v

# Run specific test class
python -m pytest tests/test_storage.py::TestSecrets -v

# Run with coverage
python -m pytest tests/test_storage.py --cov=backend.storage
```

---

## Constraints

### MVP Limitations

- No separate categories/tags table (tags as JSON arrays)
- No Run↔Module direct relationship (use tags)
- Single-user (no permissions)
- SQLite only (no PostgreSQL)

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| UUID over autoincrement | Git-friendly, mergeable, portable |
| Fernet over AES-GCM | Simpler API, built-in authentication |
| JSON arrays for tags | No need for join tables in MVP |
| Cascade deletes | Maintain referential integrity |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-12 | Initial storage layer |
