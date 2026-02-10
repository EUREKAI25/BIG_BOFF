# EURKAI_COCKPIT — Secrets Module

**Version:** 1.0.0  
**Chantier:** C06  
**Status:** MVP Complete

## Overview

The Secrets module provides secure storage and retrieval of sensitive data (API keys, passwords, tokens) with:

- **AES-256-GCM** authenticated encryption
- **Argon2id** key derivation from master password
- **Copy-gating**: reveal/copy requires password verification
- **Comprehensive audit logging** to database

## Security Architecture

### Encryption Stack

```
┌─────────────────────────────────────────────────────────┐
│                    User Password                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Argon2id Key Derivation                                │
│  - Time cost: 3 iterations                              │
│  - Memory: 64 MB                                        │
│  - Salt: 128-bit (unique per secret)                    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  AES-256-GCM Encryption                                 │
│  - Key: 256-bit (derived)                               │
│  - Nonce: 96-bit (random per encryption)                │
│  - Tag: 128-bit authentication                          │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
CREATE SECRET:
  plaintext → [Argon2id(password)] → AES-256-GCM → encrypted_blob → SQLite

REVEAL SECRET:
  password → [verify hash] → [Argon2id(password, salt)] → AES-256-GCM decrypt → plaintext

LIST SECRETS:
  → metadata only (id, key, scope, timestamps)
  → NEVER returns encrypted_value or plaintext
```

## API Reference

### SecretsService

Main service class for secrets management.

```python
from backend.secrets import SecretsService

# Initialize with storage backend
service = SecretsService(storage)
```

#### `initialize_gate_password(password: str) -> tuple[bool, str]`

Set up the master gate password (one-time setup).

```python
success, message = service.initialize_gate_password("SecureP@ssw0rd!")
# Returns: (True, "Gate password initialized")
```

**Password Requirements:**
- Minimum 8 characters
- Maximum 128 characters
- Should contain: uppercase, lowercase, digits

#### `verify_gate_password(password: str) -> bool`

Verify if a password matches the stored gate password.

```python
is_valid = service.verify_gate_password("my-password")
```

#### `create_secret(...) -> tuple[SecretMetadata | None, str]`

Create a new encrypted secret.

```python
meta, msg = service.create_secret(
    key="API_KEY",              # Unique key name
    plaintext="sk-xxxxx",       # Value to encrypt
    gate_password="password",   # For encryption
    scope="global",             # "global" or "project"
    project_id=None,            # Required if scope="project"
    source="cli"                # "cli", "api", or "ui"
)
```

**Returns:**
- `SecretMetadata` on success (no plaintext)
- `None` on failure (with error message)

#### `list_secrets(...) -> list[SecretMetadata]`

List secrets metadata. **NEVER returns plaintext values.**

```python
secrets = service.list_secrets(
    scope="global",      # Optional filter
    project_id=None,     # Optional filter
    source="api"
)

for s in secrets:
    print(f"{s.key} ({s.scope})")
    # s.value does NOT exist
```

#### `reveal_secret(...) -> RevealResult`

Decrypt and reveal a secret value. **GATED: requires password.**

```python
result = service.reveal_secret(
    secret_id="uuid-xxx",
    gate_password="password",
    source="ui"
)

if result.success:
    print(result.value)  # Plaintext value
else:
    print(result.error)  # "Invalid gate password" etc.
```

#### `copy_secret(...) -> RevealResult`

Same as reveal, but logged as "copy" action.

```python
result = service.copy_secret(secret_id, gate_password)
```

#### `delete_secret(...) -> tuple[bool, str]`

Delete a secret.

```python
success, msg = service.delete_secret(secret_id, gate_password)
```

#### `get_logs(...) -> list[SecretLogEntry]`

Retrieve audit logs.

```python
logs = service.get_logs(
    secret_id=None,    # Filter by secret
    action=None,       # Filter by action type
    limit=100
)

for log in logs:
    print(f"{log.timestamp} | {log.action} | {log.result}")
```

## Data Types

### SecretMetadata

Safe representation of a secret (no plaintext).

```python
@dataclass
class SecretMetadata:
    id: str
    key: str
    scope: str               # "global" | "project"
    project_id: str | None
    created_at: str
    updated_at: str
    # NO value field!
```

### RevealResult

Result of reveal/copy operations.

```python
@dataclass
class RevealResult:
    success: bool
    value: str | None     # Only set if success=True
    error: str | None     # Only set if success=False
```

### SecretLogEntry

Audit log entry.

```python
@dataclass
class SecretLogEntry:
    id: str
    timestamp: str
    secret_id: str
    secret_key: str
    scope: str
    action: str      # create|list|reveal|copy|update|delete
    result: str      # success|fail
    source: str      # cli|api|ui
    reason: str | None
```

## Audit Logging

All secret operations are logged to the `secret_logs` table:

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 UTC |
| `secret_id` | Target secret UUID |
| `secret_key` | Secret key name |
| `scope` | global/project |
| `action` | create, list, reveal, copy, delete |
| `result` | success, fail |
| `source` | cli, api, ui |
| `reason` | Error reason (on failure) |

**CRITICAL:** Logs **NEVER** contain secret values, hashes, or fragments.

## Database Schema

### secrets table (existing from C02)

```sql
CREATE TABLE secrets (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL,
    encrypted_value BLOB NOT NULL,  -- AES-256-GCM ciphertext
    nonce BLOB NOT NULL,            -- 96-bit nonce
    scope TEXT NOT NULL DEFAULT 'global',
    project_id TEXT,
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(key, scope, project_id)
);
```

### secret_logs table (new in C06)

```sql
CREATE TABLE secret_logs (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    secret_id TEXT NOT NULL,
    secret_key TEXT NOT NULL,
    scope TEXT NOT NULL,
    action TEXT NOT NULL,
    result TEXT NOT NULL,
    source TEXT NOT NULL,
    reason TEXT,
    created_at TEXT
);
```

## CLI Usage (Example)

```bash
# Initialize gate password (first time)
eurkai secrets init --password "SecureP@ss123!"

# Create a secret
eurkai secrets create API_KEY "sk-xxxxx" --password "SecureP@ss123!"

# List secrets (no values shown)
eurkai secrets list
# Output:
#   API_KEY    global    2024-01-15T10:30:00Z

# Reveal a secret (prompts for password)
eurkai secrets reveal API_KEY
# Password: ********
# sk-xxxxx

# View audit logs
eurkai secrets logs --limit 10
```

## Security Checklist

- [x] AES-256-GCM authenticated encryption
- [x] Argon2id key derivation (memory-hard)
- [x] Unique salt per secret
- [x] Gate password verification before reveal
- [x] List endpoint never returns values
- [x] All access logged to database
- [x] Failed attempts logged with reason
- [x] No plaintext in logs

## Migration Notes

### From Fernet (C02) to AES-256-GCM (C06)

The C02 schema stored secrets encrypted with Fernet. C06 migrates to AES-256-GCM:

1. **New secrets** use AES-256-GCM with Argon2-derived keys
2. **Storage format** changed: `salt (16) + nonce (12) + ciphertext`
3. **Backward compatibility**: Old Fernet secrets need migration script

### Migration Script

```python
# migrate_secrets.py
from backend.secrets import SecretsService

def migrate_fernet_to_aes(storage, old_key, new_password):
    """Migrate Fernet-encrypted secrets to AES-256-GCM."""
    from cryptography.fernet import Fernet
    
    service = SecretsService(storage)
    f = Fernet(old_key)
    
    for secret in storage.list_secrets():
        # Decrypt with Fernet
        plaintext = f.decrypt(secret.encrypted_value)
        
        # Delete old
        storage.delete_secret(secret.id)
        
        # Re-create with AES-256-GCM
        service.create_secret(
            key=secret.key,
            plaintext=plaintext.decode(),
            gate_password=new_password,
            scope=secret.scope,
            project_id=secret.project_id
        )
```

## Version History

| Version | Changes |
|---------|---------|
| 1.0.0 | Initial release: AES-256-GCM, Argon2, copy-gating, audit logs |
