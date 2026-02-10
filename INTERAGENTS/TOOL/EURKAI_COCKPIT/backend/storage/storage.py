"""
EURKAI_COCKPIT — Storage Layer (CRUD)
Version: 1.0.0

Provides CRUD operations for all entities:
- Projects, Briefs, Runs, Config, Secrets, Modules

Features:
- UUID generation (Python-side)
- Fernet symmetric encryption for secrets
- JSON validation
- Automatic timestamps
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, TypeVar, Generic, Optional

from cryptography.fernet import Fernet, InvalidToken

# ============================================
# CONFIGURATION
# ============================================

DEFAULT_DB_PATH = Path("data/eurkai.db")
ENCRYPTION_KEY_ENV = "EURKAI_SECRET_KEY"


def get_encryption_key() -> bytes:
    """Get Fernet key from environment or generate warning."""
    key = os.environ.get(ENCRYPTION_KEY_ENV)
    if not key:
        raise EnvironmentError(
            f"Missing {ENCRYPTION_KEY_ENV} environment variable. "
            f"Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return key.encode()


def generate_uuid() -> str:
    """Generate a new UUID v4."""
    return str(uuid.uuid4())


def utc_now() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ============================================
# ENCRYPTION
# ============================================

class SecretEncryption:
    """Fernet-based encryption for secrets."""
    
    def __init__(self, key: Optional[bytes] = None):
        self._key = key or get_encryption_key()
        self._fernet = Fernet(self._key)
    
    def encrypt(self, plaintext: str) -> tuple[bytes, bytes]:
        """Encrypt plaintext, return (encrypted_value, nonce).
        
        Note: Fernet includes its own nonce/IV internally.
        We store a separate nonce for future AES-GCM migration compatibility.
        """
        encrypted = self._fernet.encrypt(plaintext.encode())
        nonce = os.urandom(16)  # Placeholder for AES-GCM compatibility
        return encrypted, nonce
    
    def decrypt(self, encrypted_value: bytes, nonce: bytes) -> str:
        """Decrypt value. Nonce reserved for future AES-GCM."""
        try:
            return self._fernet.decrypt(encrypted_value).decode()
        except InvalidToken:
            raise ValueError("Failed to decrypt: invalid key or corrupted data")


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class Project:
    id: str
    name: str
    description: Optional[str] = None
    root_path: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class Brief:
    id: str
    project_id: str
    title: str
    user_prompt: str
    goal: Optional[str] = None
    system_prompt: Optional[str] = None
    variables_json: dict[str, Any] = field(default_factory=dict)
    expected_output: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    policy: dict[str, Any] = field(default_factory=lambda: {"passes_in_a_row": 2, "max_iters": 8})
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class Run:
    id: str
    run_id: str
    brief_id: str
    status: str = "pending"
    result_json: Optional[dict[str, Any]] = None
    logs_json: list[dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    model: Optional[str] = None
    duration_ms: Optional[int] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str = field(default_factory=utc_now)


@dataclass
class Config:
    id: str
    key: str
    value_json: Any
    updated_at: str = field(default_factory=utc_now)


@dataclass
class Secret:
    id: str
    key: str
    encrypted_value: bytes
    nonce: bytes
    scope: str = "global"
    project_id: Optional[str] = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class ModuleManifest:
    """Module manifest structure (v1)."""
    name: str
    version: str
    description: str = ""
    inputs: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    constraints: dict[str, list[str]] = field(default_factory=lambda: {"hard": [], "soft": []})
    tags: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class Module:
    id: str
    name: str
    version: str
    description: Optional[str] = None
    manifest_json: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass
class Backup:
    id: str
    timestamp: str
    status: str
    commit_sha: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = field(default_factory=utc_now)


# ============================================
# STORAGE CLASS
# ============================================

class Storage:
    """SQLite storage layer with CRUD operations."""
    
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH, encryption: Optional[SecretEncryption] = None):
        self.db_path = Path(db_path)
        self._encryption = encryption
        self._conn: Optional[sqlite3.Connection] = None
    
    @property
    def encryption(self) -> SecretEncryption:
        """Lazy-load encryption to avoid requiring key at init."""
        if self._encryption is None:
            self._encryption = SecretEncryption()
        return self._encryption
    
    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_db(self) -> None:
        """Initialize database schema (idempotent)."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        
        with self.connection() as conn:
            conn.executescript(schema_sql)
    
    # ----------------------------------------
    # PROJECTS
    # ----------------------------------------
    
    def create_project(self, name: str, description: Optional[str] = None, 
                       root_path: Optional[str] = None, tags: Optional[list[str]] = None) -> Project:
        """Create a new project."""
        project = Project(
            id=generate_uuid(),
            name=name,
            description=description,
            root_path=root_path,
            tags=tags or []
        )
        
        with self.connection() as conn:
            conn.execute(
                """INSERT INTO projects (id, name, description, root_path, tags, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (project.id, project.name, project.description, project.root_path,
                 json.dumps(project.tags), project.created_at, project.updated_at)
            )
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if row:
                return Project(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    root_path=row["root_path"],
                    tags=json.loads(row["tags"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
        return None
    
    def list_projects(self) -> list[Project]:
        """List all projects."""
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
            return [
                Project(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    root_path=row["root_path"],
                    tags=json.loads(row["tags"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
                for row in rows
            ]
    
    def update_project(self, project_id: str, **kwargs) -> Optional[Project]:
        """Update project fields."""
        allowed = {"name", "description", "root_path", "tags"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        
        if not updates:
            return self.get_project(project_id)
        
        if "tags" in updates:
            updates["tags"] = json.dumps(updates["tags"])
        
        updates["updated_at"] = utc_now()
        
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [project_id]
        
        with self.connection() as conn:
            conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
        
        return self.get_project(project_id)
    
    def delete_project(self, project_id: str) -> bool:
        """Delete project (cascade to briefs)."""
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cursor.rowcount > 0
    
    # ----------------------------------------
    # BRIEFS
    # ----------------------------------------
    
    def create_brief(self, project_id: str, title: str, user_prompt: str, **kwargs) -> Brief:
        """Create a new brief (project_id required)."""
        brief = Brief(
            id=generate_uuid(),
            project_id=project_id,
            title=title,
            user_prompt=user_prompt,
            goal=kwargs.get("goal"),
            system_prompt=kwargs.get("system_prompt"),
            variables_json=kwargs.get("variables_json", {}),
            expected_output=kwargs.get("expected_output"),
            tags=kwargs.get("tags", []),
            policy=kwargs.get("policy", {"passes_in_a_row": 2, "max_iters": 8})
        )
        
        with self.connection() as conn:
            conn.execute(
                """INSERT INTO briefs 
                   (id, project_id, title, goal, system_prompt, user_prompt, 
                    variables_json, expected_output, tags, policy, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (brief.id, brief.project_id, brief.title, brief.goal, brief.system_prompt,
                 brief.user_prompt, json.dumps(brief.variables_json), brief.expected_output,
                 json.dumps(brief.tags), json.dumps(brief.policy), brief.created_at, brief.updated_at)
            )
        return brief
    
    def get_brief(self, brief_id: str) -> Optional[Brief]:
        """Get brief by ID."""
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM briefs WHERE id = ?", (brief_id,)).fetchone()
            if row:
                return Brief(
                    id=row["id"],
                    project_id=row["project_id"],
                    title=row["title"],
                    goal=row["goal"],
                    system_prompt=row["system_prompt"],
                    user_prompt=row["user_prompt"],
                    variables_json=json.loads(row["variables_json"]),
                    expected_output=row["expected_output"],
                    tags=json.loads(row["tags"]),
                    policy=json.loads(row["policy"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
        return None
    
    def list_briefs(self, project_id: Optional[str] = None) -> list[Brief]:
        """List briefs, optionally filtered by project."""
        with self.connection() as conn:
            if project_id:
                rows = conn.execute(
                    "SELECT * FROM briefs WHERE project_id = ? ORDER BY created_at DESC",
                    (project_id,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM briefs ORDER BY created_at DESC").fetchall()
            
            return [
                Brief(
                    id=row["id"],
                    project_id=row["project_id"],
                    title=row["title"],
                    goal=row["goal"],
                    system_prompt=row["system_prompt"],
                    user_prompt=row["user_prompt"],
                    variables_json=json.loads(row["variables_json"]),
                    expected_output=row["expected_output"],
                    tags=json.loads(row["tags"]),
                    policy=json.loads(row["policy"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
                for row in rows
            ]
    
    def update_brief(self, brief_id: str, **kwargs) -> Optional[Brief]:
        """Update brief fields."""
        allowed = {"title", "goal", "system_prompt", "user_prompt", "variables_json",
                   "expected_output", "tags", "policy"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        
        if not updates:
            return self.get_brief(brief_id)
        
        for json_field in ["variables_json", "tags", "policy"]:
            if json_field in updates:
                updates[json_field] = json.dumps(updates[json_field])
        
        updates["updated_at"] = utc_now()
        
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [brief_id]
        
        with self.connection() as conn:
            conn.execute(f"UPDATE briefs SET {set_clause} WHERE id = ?", values)
        
        return self.get_brief(brief_id)
    
    def delete_brief(self, brief_id: str) -> bool:
        """Delete brief (cascade to runs)."""
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM briefs WHERE id = ?", (brief_id,))
            return cursor.rowcount > 0
    
    # ----------------------------------------
    # RUNS
    # ----------------------------------------
    
    def create_run(self, brief_id: str, run_id: Optional[str] = None, **kwargs) -> Run:
        """Create a new run."""
        run = Run(
            id=generate_uuid(),
            run_id=run_id or generate_uuid(),
            brief_id=brief_id,
            status=kwargs.get("status", "pending"),
            result_json=kwargs.get("result_json"),
            logs_json=kwargs.get("logs_json", []),
            error=kwargs.get("error"),
            model=kwargs.get("model"),
            started_at=kwargs.get("started_at")
        )
        
        with self.connection() as conn:
            conn.execute(
                """INSERT INTO runs 
                   (id, run_id, brief_id, status, result_json, logs_json, error, model, started_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (run.id, run.run_id, run.brief_id, run.status,
                 json.dumps(run.result_json) if run.result_json else None,
                 json.dumps(run.logs_json), run.error, run.model, run.started_at, run.created_at)
            )
        return run
    
    def get_run(self, run_id: str) -> Optional[Run]:
        """Get run by ID (primary key or run_id)."""
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE id = ? OR run_id = ?", 
                (run_id, run_id)
            ).fetchone()
            if row:
                return Run(
                    id=row["id"],
                    run_id=row["run_id"],
                    brief_id=row["brief_id"],
                    status=row["status"],
                    result_json=json.loads(row["result_json"]) if row["result_json"] else None,
                    logs_json=json.loads(row["logs_json"]) if row["logs_json"] else [],
                    error=row["error"],
                    model=row["model"],
                    duration_ms=row["duration_ms"],
                    started_at=row["started_at"],
                    finished_at=row["finished_at"],
                    created_at=row["created_at"]
                )
        return None
    
    def list_runs(self, brief_id: Optional[str] = None) -> list[Run]:
        """List runs, optionally filtered by brief."""
        with self.connection() as conn:
            if brief_id:
                rows = conn.execute(
                    "SELECT * FROM runs WHERE brief_id = ? ORDER BY created_at DESC",
                    (brief_id,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM runs ORDER BY created_at DESC").fetchall()
            
            return [
                Run(
                    id=row["id"],
                    run_id=row["run_id"],
                    brief_id=row["brief_id"],
                    status=row["status"],
                    result_json=json.loads(row["result_json"]) if row["result_json"] else None,
                    logs_json=json.loads(row["logs_json"]) if row["logs_json"] else [],
                    error=row["error"],
                    model=row["model"],
                    duration_ms=row["duration_ms"],
                    started_at=row["started_at"],
                    finished_at=row["finished_at"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]
    
    def update_run(self, run_id: str, **kwargs) -> Optional[Run]:
        """Update run fields."""
        allowed = {"status", "result_json", "logs_json", "error", "model", 
                   "duration_ms", "started_at", "finished_at"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        
        if not updates:
            return self.get_run(run_id)
        
        for json_field in ["result_json", "logs_json"]:
            if json_field in updates and updates[json_field] is not None:
                updates[json_field] = json.dumps(updates[json_field])
        
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [run_id, run_id]
        
        with self.connection() as conn:
            conn.execute(
                f"UPDATE runs SET {set_clause} WHERE id = ? OR run_id = ?", 
                values
            )
        
        return self.get_run(run_id)
    
    def delete_run(self, run_id: str) -> bool:
        """Delete run."""
        with self.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM runs WHERE id = ? OR run_id = ?", 
                (run_id, run_id)
            )
            return cursor.rowcount > 0
    
    # ----------------------------------------
    # CONFIG
    # ----------------------------------------
    
    def set_config(self, key: str, value: Any) -> Config:
        """Set config value (upsert)."""
        config = Config(
            id=generate_uuid(),
            key=key,
            value_json=value
        )
        
        with self.connection() as conn:
            conn.execute(
                """INSERT INTO config (id, key, value_json, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET 
                   value_json = excluded.value_json,
                   updated_at = excluded.updated_at""",
                (config.id, config.key, json.dumps(config.value_json), config.updated_at)
            )
        
        return self.get_config(key)  # type: ignore
    
    def get_config(self, key: str) -> Optional[Config]:
        """Get config by key."""
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM config WHERE key = ?", (key,)).fetchone()
            if row:
                return Config(
                    id=row["id"],
                    key=row["key"],
                    value_json=json.loads(row["value_json"]),
                    updated_at=row["updated_at"]
                )
        return None
    
    def list_config(self) -> list[Config]:
        """List all config entries."""
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM config ORDER BY key").fetchall()
            return [
                Config(
                    id=row["id"],
                    key=row["key"],
                    value_json=json.loads(row["value_json"]),
                    updated_at=row["updated_at"]
                )
                for row in rows
            ]
    
    def delete_config(self, key: str) -> bool:
        """Delete config entry."""
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM config WHERE key = ?", (key,))
            return cursor.rowcount > 0
    
    # ----------------------------------------
    # SECRETS
    # ----------------------------------------
    
    def create_secret(self, key: str, plaintext: str, scope: str = "global", 
                      project_id: Optional[str] = None) -> Secret:
        """Create encrypted secret."""
        encrypted_value, nonce = self.encryption.encrypt(plaintext)
        
        secret = Secret(
            id=generate_uuid(),
            key=key,
            encrypted_value=encrypted_value,
            nonce=nonce,
            scope=scope,
            project_id=project_id
        )
        
        with self.connection() as conn:
            conn.execute(
                """INSERT INTO secrets 
                   (id, key, encrypted_value, nonce, scope, project_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (secret.id, secret.key, secret.encrypted_value, secret.nonce,
                 secret.scope, secret.project_id, secret.created_at, secret.updated_at)
            )
        return secret
    
    def get_secret(self, secret_id: str) -> Optional[Secret]:
        """Get secret by ID (encrypted, not decrypted)."""
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM secrets WHERE id = ?", (secret_id,)).fetchone()
            if row:
                return Secret(
                    id=row["id"],
                    key=row["key"],
                    encrypted_value=row["encrypted_value"],
                    nonce=row["nonce"],
                    scope=row["scope"],
                    project_id=row["project_id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
        return None
    
    def get_secret_by_key(self, key: str, scope: str = "global", 
                          project_id: Optional[str] = None) -> Optional[Secret]:
        """Get secret by key and scope."""
        with self.connection() as conn:
            if scope == "project" and project_id:
                row = conn.execute(
                    "SELECT * FROM secrets WHERE key = ? AND scope = ? AND project_id = ?",
                    (key, scope, project_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM secrets WHERE key = ? AND scope = 'global'",
                    (key,)
                ).fetchone()
            
            if row:
                return Secret(
                    id=row["id"],
                    key=row["key"],
                    encrypted_value=row["encrypted_value"],
                    nonce=row["nonce"],
                    scope=row["scope"],
                    project_id=row["project_id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
        return None
    
    def decrypt_secret(self, secret: Secret) -> str:
        """Decrypt a secret value."""
        return self.encryption.decrypt(secret.encrypted_value, secret.nonce)
    
    def list_secrets(self, scope: Optional[str] = None, project_id: Optional[str] = None) -> list[Secret]:
        """List secrets (encrypted, keys only visible)."""
        with self.connection() as conn:
            if scope and project_id:
                rows = conn.execute(
                    "SELECT * FROM secrets WHERE scope = ? AND project_id = ? ORDER BY key",
                    (scope, project_id)
                ).fetchall()
            elif scope:
                rows = conn.execute(
                    "SELECT * FROM secrets WHERE scope = ? ORDER BY key",
                    (scope,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM secrets ORDER BY key").fetchall()
            
            return [
                Secret(
                    id=row["id"],
                    key=row["key"],
                    encrypted_value=row["encrypted_value"],
                    nonce=row["nonce"],
                    scope=row["scope"],
                    project_id=row["project_id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
                for row in rows
            ]
    
    def update_secret(self, secret_id: str, plaintext: str) -> Optional[Secret]:
        """Update secret value (re-encrypt)."""
        encrypted_value, nonce = self.encryption.encrypt(plaintext)
        
        with self.connection() as conn:
            conn.execute(
                """UPDATE secrets SET encrypted_value = ?, nonce = ?, updated_at = ?
                   WHERE id = ?""",
                (encrypted_value, nonce, utc_now(), secret_id)
            )
        
        return self.get_secret(secret_id)
    
    def delete_secret(self, secret_id: str) -> bool:
        """Delete secret."""
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM secrets WHERE id = ?", (secret_id,))
            return cursor.rowcount > 0
    
    # ----------------------------------------
    # MODULES
    # ----------------------------------------
    
    def create_module(self, manifest: ModuleManifest) -> Module:
        """Register a module manifest."""
        module = Module(
            id=generate_uuid(),
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            manifest_json=asdict(manifest),
            enabled=manifest.enabled
        )
        
        with self.connection() as conn:
            conn.execute(
                """INSERT INTO modules 
                   (id, name, version, description, manifest_json, enabled, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (module.id, module.name, module.version, module.description,
                 json.dumps(module.manifest_json), 1 if module.enabled else 0,
                 module.created_at, module.updated_at)
            )
        return module
    
    def get_module(self, module_id: str) -> Optional[Module]:
        """Get module by ID."""
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM modules WHERE id = ?", (module_id,)).fetchone()
            if row:
                return Module(
                    id=row["id"],
                    name=row["name"],
                    version=row["version"],
                    description=row["description"],
                    manifest_json=json.loads(row["manifest_json"]),
                    enabled=bool(row["enabled"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
        return None
    
    def get_module_by_name(self, name: str) -> Optional[Module]:
        """Get module by name."""
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM modules WHERE name = ?", (name,)).fetchone()
            if row:
                return Module(
                    id=row["id"],
                    name=row["name"],
                    version=row["version"],
                    description=row["description"],
                    manifest_json=json.loads(row["manifest_json"]),
                    enabled=bool(row["enabled"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
        return None
    
    def list_modules(self, enabled_only: bool = False) -> list[Module]:
        """List all modules."""
        with self.connection() as conn:
            if enabled_only:
                rows = conn.execute(
                    "SELECT * FROM modules WHERE enabled = 1 ORDER BY name"
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM modules ORDER BY name").fetchall()
            
            return [
                Module(
                    id=row["id"],
                    name=row["name"],
                    version=row["version"],
                    description=row["description"],
                    manifest_json=json.loads(row["manifest_json"]),
                    enabled=bool(row["enabled"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
                for row in rows
            ]
    
    def update_module(self, module_id: str, **kwargs) -> Optional[Module]:
        """Update module fields."""
        allowed = {"version", "description", "manifest_json", "enabled"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        
        if not updates:
            return self.get_module(module_id)
        
        if "manifest_json" in updates:
            updates["manifest_json"] = json.dumps(updates["manifest_json"])
        if "enabled" in updates:
            updates["enabled"] = 1 if updates["enabled"] else 0
        
        updates["updated_at"] = utc_now()
        
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [module_id]
        
        with self.connection() as conn:
            conn.execute(f"UPDATE modules SET {set_clause} WHERE id = ?", values)
        
        return self.get_module(module_id)
    
    def delete_module(self, module_id: str) -> bool:
        """Remove module from registry."""
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM modules WHERE id = ?", (module_id,))
            return cursor.rowcount > 0
    
    # ----------------------------------------
    # BACKUPS
    # ----------------------------------------
    
    def create_backup(self, status: str, commit_sha: Optional[str] = None, 
                      notes: Optional[str] = None) -> Backup:
        """Record a backup entry."""
        backup = Backup(
            id=generate_uuid(),
            timestamp=utc_now(),
            status=status,
            commit_sha=commit_sha,
            notes=notes
        )
        
        with self.connection() as conn:
            conn.execute(
                """INSERT INTO backups (id, timestamp, commit_sha, status, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (backup.id, backup.timestamp, backup.commit_sha, backup.status, 
                 backup.notes, backup.created_at)
            )
        return backup
    
    def list_backups(self, limit: int = 50) -> list[Backup]:
        """List backup history."""
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM backups ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            
            return [
                Backup(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    status=row["status"],
                    commit_sha=row["commit_sha"],
                    notes=row["notes"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]
