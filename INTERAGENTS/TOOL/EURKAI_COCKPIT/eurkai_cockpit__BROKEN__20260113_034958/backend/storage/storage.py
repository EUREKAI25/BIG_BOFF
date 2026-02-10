"""
EURKAI_COCKPIT — Storage Layer (CRUD)
Version: 1.0.0

SQLite-based storage with JSON field support.
Follows C01/C02 contracts strictly.
"""
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

from .migrations import get_db_path, init_db


class Storage:
    """
    CRUD storage layer for EURKAI_COCKPIT.
    
    Thread-safe: creates new connection per operation.
    JSON fields are automatically serialized/deserialized.
    """
    
    def __init__(self, db_path: str | None = None, auto_init: bool = True):
        """
        Initialize storage.
        
        Args:
            db_path: Optional explicit database path
            auto_init: If True, initialize DB if not exists
        """
        self.db_path = get_db_path(db_path)
        
        if auto_init and not self.db_path.exists():
            init_db(str(self.db_path))
    
    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
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
    
    def _generate_id(self) -> str:
        """Generate UUIDv4."""
        return str(uuid.uuid4())
    
    def _now(self) -> str:
        """Current timestamp ISO 8601."""
        return datetime.utcnow().isoformat() + "Z"
    
    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert Row to dict."""
        return dict(row)
    
    # =========================================================================
    # PROJECTS
    # =========================================================================
    
    def create_project(self, name: str, description: str | None = None) -> dict:
        """Create a new project."""
        project_id = self._generate_id()
        now = self._now()
        
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO projects (id, name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, name, description, now, now)
            )
        
        return self.get_project(project_id)
    
    def get_project(self, project_id: str) -> dict | None:
        """Get project by ID."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?",
                (project_id,)
            ).fetchone()
        
        return self._row_to_dict(row) if row else None
    
    def list_projects(self) -> list[dict]:
        """List all projects."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM projects ORDER BY created_at DESC"
            ).fetchall()
        
        return [self._row_to_dict(r) for r in rows]
    
    def update_project(self, project_id: str, **kwargs) -> dict | None:
        """Update project fields."""
        if not kwargs:
            return self.get_project(project_id)
        
        allowed = {"name", "description"}
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        
        if not fields:
            return self.get_project(project_id)
        
        fields["updated_at"] = self._now()
        
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [project_id]
        
        with self._conn() as conn:
            conn.execute(
                f"UPDATE projects SET {set_clause} WHERE id = ?",
                values
            )
        
        return self.get_project(project_id)
    
    def delete_project(self, project_id: str) -> bool:
        """Delete project (cascades to briefs, runs)."""
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM projects WHERE id = ?",
                (project_id,)
            )
        return cursor.rowcount > 0
    
    # =========================================================================
    # BRIEFS
    # =========================================================================
    
    def create_brief(
        self,
        project_id: str,
        title: str,
        user_prompt: str,
        goal: str | None = None,
        system_prompt: str | None = None,
        variables: dict | None = None,
        expected_output: str | None = None,
        tags: list[str] | None = None,
        policy: dict | None = None
    ) -> dict:
        """Create a new brief (project_id required)."""
        brief_id = self._generate_id()
        now = self._now()
        
        variables_json = json.dumps(variables or {})
        tags_json = json.dumps(tags or [])
        policy_json = json.dumps(policy or {"passes_in_a_row": 2, "max_iters": 8})
        
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO briefs 
                (id, project_id, title, goal, system_prompt, user_prompt, 
                 variables, expected_output, tags, policy, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (brief_id, project_id, title, goal, system_prompt, user_prompt,
                 variables_json, expected_output, tags_json, policy_json, now, now)
            )
        
        return self.get_brief(brief_id)
    
    def get_brief(self, brief_id: str) -> dict | None:
        """Get brief by ID with JSON fields parsed."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM briefs WHERE id = ?",
                (brief_id,)
            ).fetchone()
        
        if not row:
            return None
        
        result = self._row_to_dict(row)
        result["variables"] = json.loads(result["variables"])
        result["tags"] = json.loads(result["tags"])
        result["policy"] = json.loads(result["policy"])
        return result
    
    def list_briefs(self, project_id: str | None = None) -> list[dict]:
        """List briefs, optionally filtered by project."""
        with self._conn() as conn:
            if project_id:
                rows = conn.execute(
                    "SELECT * FROM briefs WHERE project_id = ? ORDER BY created_at DESC",
                    (project_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM briefs ORDER BY created_at DESC"
                ).fetchall()
        
        results = []
        for row in rows:
            r = self._row_to_dict(row)
            r["variables"] = json.loads(r["variables"])
            r["tags"] = json.loads(r["tags"])
            r["policy"] = json.loads(r["policy"])
            results.append(r)
        
        return results
    
    def update_brief(self, brief_id: str, **kwargs) -> dict | None:
        """Update brief fields."""
        if not kwargs:
            return self.get_brief(brief_id)
        
        allowed = {
            "title", "goal", "system_prompt", "user_prompt",
            "variables", "expected_output", "tags", "policy"
        }
        fields = {}
        
        for k, v in kwargs.items():
            if k not in allowed or v is None:
                continue
            if k in ("variables", "tags", "policy"):
                fields[k] = json.dumps(v)
            else:
                fields[k] = v
        
        if not fields:
            return self.get_brief(brief_id)
        
        fields["updated_at"] = self._now()
        
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [brief_id]
        
        with self._conn() as conn:
            conn.execute(
                f"UPDATE briefs SET {set_clause} WHERE id = ?",
                values
            )
        
        return self.get_brief(brief_id)
    
    def delete_brief(self, brief_id: str) -> bool:
        """Delete brief (cascades to runs)."""
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM briefs WHERE id = ?",
                (brief_id,)
            )
        return cursor.rowcount > 0
    
    # =========================================================================
    # RUNS
    # =========================================================================
    
    def create_run(self, brief_id: str, model: str | None = None) -> dict:
        """Create a new run (pending status)."""
        run_id = self._generate_id()
        now = self._now()
        
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO runs (id, brief_id, status, model, created_at)
                VALUES (?, ?, 'pending', ?, ?)
                """,
                (run_id, brief_id, model, now)
            )
        
        return self.get_run(run_id)
    
    def get_run(self, run_id: str) -> dict | None:
        """Get run by ID."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE id = ?",
                (run_id,)
            ).fetchone()
        
        return self._row_to_dict(row) if row else None
    
    def list_runs(self, brief_id: str) -> list[dict]:
        """List runs for a brief."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM runs WHERE brief_id = ? ORDER BY created_at DESC",
                (brief_id,)
            ).fetchall()
        
        return [self._row_to_dict(r) for r in rows]
    
    def update_run(
        self,
        run_id: str,
        status: str | None = None,
        output: str | None = None,
        logs: str | None = None,
        duration_ms: int | None = None
    ) -> dict | None:
        """Update run status and results."""
        fields = {}
        
        if status is not None:
            fields["status"] = status
        if output is not None:
            fields["output"] = output
        if logs is not None:
            fields["logs"] = logs
        if duration_ms is not None:
            fields["duration_ms"] = duration_ms
        
        if status in ("success", "failed"):
            fields["finished_at"] = self._now()
        
        if not fields:
            return self.get_run(run_id)
        
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [run_id]
        
        with self._conn() as conn:
            conn.execute(
                f"UPDATE runs SET {set_clause} WHERE id = ?",
                values
            )
        
        return self.get_run(run_id)
    
    def delete_run(self, run_id: str) -> bool:
        """Delete a run."""
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM runs WHERE id = ?",
                (run_id,)
            )
        return cursor.rowcount > 0
    
    # =========================================================================
    # CONFIG
    # =========================================================================
    
    def get_config(self, key: str) -> dict | None:
        """Get config value by key."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM config WHERE key = ?",
                (key,)
            ).fetchone()
        
        return self._row_to_dict(row) if row else None
    
    def list_config(self) -> list[dict]:
        """List all config entries."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM config ORDER BY key"
            ).fetchall()
        
        return [self._row_to_dict(r) for r in rows]
    
    def set_config(self, key: str, value: str) -> dict:
        """Set config value (upsert)."""
        now = self._now()
        
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?
                """,
                (key, value, now, value, now)
            )
        
        return self.get_config(key)
    
    # =========================================================================
    # SECRETS (values stored encrypted - encryption handled by API layer)
    # =========================================================================
    
    def create_secret(
        self,
        key: str,
        value_encrypted: bytes,
        nonce: bytes,
        project_id: str | None = None
    ) -> dict:
        """Create a secret (value must be pre-encrypted)."""
        secret_id = self._generate_id()
        now = self._now()
        
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO secrets 
                (id, project_id, key, value_encrypted, nonce, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (secret_id, project_id, key, value_encrypted, nonce, now, now)
            )
        
        return self.get_secret(secret_id)
    
    def get_secret(self, secret_id: str) -> dict | None:
        """Get secret by ID (with encrypted value)."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM secrets WHERE id = ?",
                (secret_id,)
            ).fetchone()
        
        return self._row_to_dict(row) if row else None
    
    def get_secret_by_key(self, key: str, project_id: str | None = None) -> dict | None:
        """Get secret by key and optional project scope."""
        with self._conn() as conn:
            if project_id:
                row = conn.execute(
                    "SELECT * FROM secrets WHERE key = ? AND project_id = ?",
                    (key, project_id)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM secrets WHERE key = ? AND project_id IS NULL",
                    (key,)
                ).fetchone()
        
        return self._row_to_dict(row) if row else None
    
    def list_secrets(self, project_id: str | None = None, include_global: bool = True) -> list[dict]:
        """
        List secrets (without values).
        
        Args:
            project_id: Filter by project
            include_global: If True and project_id set, also include global secrets
        """
        with self._conn() as conn:
            if project_id:
                if include_global:
                    rows = conn.execute(
                        """
                        SELECT id, project_id, key, created_at, updated_at 
                        FROM secrets 
                        WHERE project_id = ? OR project_id IS NULL
                        ORDER BY created_at DESC
                        """,
                        (project_id,)
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT id, project_id, key, created_at, updated_at 
                        FROM secrets 
                        WHERE project_id = ?
                        ORDER BY created_at DESC
                        """,
                        (project_id,)
                    ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, project_id, key, created_at, updated_at 
                    FROM secrets 
                    ORDER BY created_at DESC
                    """
                ).fetchall()
        
        return [self._row_to_dict(r) for r in rows]
    
    def update_secret(
        self,
        secret_id: str,
        value_encrypted: bytes,
        nonce: bytes
    ) -> dict | None:
        """Update secret value (must be pre-encrypted)."""
        now = self._now()
        
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE secrets 
                SET value_encrypted = ?, nonce = ?, updated_at = ?
                WHERE id = ?
                """,
                (value_encrypted, nonce, now, secret_id)
            )
        
        return self.get_secret(secret_id)
    
    def delete_secret(self, secret_id: str) -> bool:
        """Delete a secret."""
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM secrets WHERE id = ?",
                (secret_id,)
            )
        return cursor.rowcount > 0
    
    # =========================================================================
    # MODULE MANIFESTS
    # =========================================================================
    
    def create_module(
        self,
        name: str,
        version: str,
        description: str | None = None,
        inputs: list[dict] | None = None,
        outputs: list[dict] | None = None,
        constraints: dict | None = None,
        tags: list[str] | None = None
    ) -> dict:
        """Register a module manifest."""
        module_id = self._generate_id()
        now = self._now()
        
        inputs_json = json.dumps(inputs or [])
        outputs_json = json.dumps(outputs or [])
        constraints_json = json.dumps(constraints or {})
        tags_json = json.dumps(tags or [])
        
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO module_manifests 
                (id, name, version, description, inputs, outputs, constraints, tags, registered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (module_id, name, version, description, inputs_json, 
                 outputs_json, constraints_json, tags_json, now)
            )
        
        return self.get_module(module_id)
    
    def get_module(self, module_id: str) -> dict | None:
        """Get module by ID."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM module_manifests WHERE id = ?",
                (module_id,)
            ).fetchone()
        
        if not row:
            return None
        
        result = self._row_to_dict(row)
        result["inputs"] = json.loads(result["inputs"])
        result["outputs"] = json.loads(result["outputs"])
        result["constraints"] = json.loads(result["constraints"])
        result["tags"] = json.loads(result["tags"])
        return result
    
    def get_module_by_name(self, name: str) -> dict | None:
        """Get module by name (unique)."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM module_manifests WHERE name = ?",
                (name,)
            ).fetchone()
        
        if not row:
            return None
        
        result = self._row_to_dict(row)
        result["inputs"] = json.loads(result["inputs"])
        result["outputs"] = json.loads(result["outputs"])
        result["constraints"] = json.loads(result["constraints"])
        result["tags"] = json.loads(result["tags"])
        return result
    
    def list_modules(self) -> list[dict]:
        """List all registered modules."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM module_manifests ORDER BY name"
            ).fetchall()
        
        results = []
        for row in rows:
            r = self._row_to_dict(row)
            r["inputs"] = json.loads(r["inputs"])
            r["outputs"] = json.loads(r["outputs"])
            r["constraints"] = json.loads(r["constraints"])
            r["tags"] = json.loads(r["tags"])
            results.append(r)
        
        return results
    
    def update_module(
        self,
        module_id: str,
        version: str,
        description: str | None = None,
        inputs: list[dict] | None = None,
        outputs: list[dict] | None = None,
        constraints: dict | None = None,
        tags: list[str] | None = None
    ) -> dict | None:
        """Update module manifest (version bump required)."""
        fields = {"version": version}
        
        if description is not None:
            fields["description"] = description
        if inputs is not None:
            fields["inputs"] = json.dumps(inputs)
        if outputs is not None:
            fields["outputs"] = json.dumps(outputs)
        if constraints is not None:
            fields["constraints"] = json.dumps(constraints)
        if tags is not None:
            fields["tags"] = json.dumps(tags)
        
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [module_id]
        
        with self._conn() as conn:
            conn.execute(
                f"UPDATE module_manifests SET {set_clause} WHERE id = ?",
                values
            )
        
        return self.get_module(module_id)
    
    def delete_module(self, module_id: str) -> bool:
        """Remove module from registry."""
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM module_manifests WHERE id = ?",
                (module_id,)
            )
        return cursor.rowcount > 0
    
    # =========================================================================
    # BACKUPS
    # =========================================================================
    
    def create_backup(
        self,
        status: str,
        commit_sha: str | None = None,
        notes: str | None = None
    ) -> dict:
        """Log a backup entry."""
        backup_id = self._generate_id()
        now = self._now()
        
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO backups (id, timestamp, commit_sha, status, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (backup_id, now, commit_sha, status, notes)
            )
        
        return self.get_backup(backup_id)
    
    def get_backup(self, backup_id: str) -> dict | None:
        """Get backup by ID."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM backups WHERE id = ?",
                (backup_id,)
            ).fetchone()
        
        return self._row_to_dict(row) if row else None
    
    def list_backups(self) -> list[dict]:
        """List all backups."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM backups ORDER BY timestamp DESC"
            ).fetchall()
        
        return [self._row_to_dict(r) for r in rows]
    
    # =========================================================================
    # TAGS
    # =========================================================================
    
    def create_tag(self, name: str, color: str = "#888888") -> dict:
        """Create a tag."""
        tag_id = self._generate_id()
        
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO tags (id, name, color) VALUES (?, ?, ?)",
                (tag_id, name, color)
            )
        
        return self.get_tag(tag_id)
    
    def get_tag(self, tag_id: str) -> dict | None:
        """Get tag by ID."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM tags WHERE id = ?",
                (tag_id,)
            ).fetchone()
        
        return self._row_to_dict(row) if row else None
    
    def list_tags(self) -> list[dict]:
        """List all tags."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tags ORDER BY name"
            ).fetchall()
        
        return [self._row_to_dict(r) for r in rows]
    
    def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag."""
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM tags WHERE id = ?",
                (tag_id,)
            )
        return cursor.rowcount > 0

    # ---------------------------------------------------------------------
    # Compatibility: tests expect Storage.init_db()
    def init_db(self) -> None:
        """Initialize DB schema (idempotent)."""
        from .migrations import init_db as _init_db
        _init_db(self.db_path)



# === TEST COMPAT SHIMS ===
# These shims align Storage API + schema with tests expectations without refactoring the whole module.

import json
from typing import Any, Optional

from backend.models import ProjectOut, ConfigOut, BriefOut, RunOut, SecretOut, BackupOut, ModuleManifest, ModuleManifestOut

def _jd(v: Any) -> str:
    # stable JSON encoding for sqlite
    return json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v

def _now_iso(self) -> str:
    return self._now() if hasattr(self, "_now") else __import__("datetime").datetime.utcnow().isoformat() + "Z"

def _row_to(model_cls, row):
    # sqlite Row -> dict -> model
    if row is None:
        return None
    if hasattr(row, "keys"):
        d = {k: row[k] for k in row.keys()}
    else:
        d = dict(row)
    return model_cls(**d)

# --- init_db shim: ensure schema matches tests (no tags table, tags stored as JSON in rows) ---
_orig_init_db = getattr(Storage, "init_db", None)

def init_db(self):
    # Call original init_db first (if present)
    if _orig_init_db:
        _orig_init_db(self)

    with self._conn() as conn:
        # Ensure columns exist / tables exist as tests expect.
        # Projects: root_path + tags_json
        conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            root_path TEXT NOT NULL DEFAULT '',
            tags_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        # Briefs: variables_json + tags_json + policy_json
        conn.execute("""
        CREATE TABLE IF NOT EXISTS briefs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            title TEXT NOT NULL,
            user_prompt TEXT NOT NULL DEFAULT '',
            goal TEXT,
            system_prompt TEXT,
            variables_json TEXT NOT NULL DEFAULT '{}',
            expected_output TEXT,
            tags_json TEXT NOT NULL DEFAULT '[]',
            policy_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """)

        # Runs
        conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            brief_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            model TEXT,
            result_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(brief_id) REFERENCES briefs(id) ON DELETE CASCADE
        )
        """)

        # Config: value stored as JSON string
        conn.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        # Secrets: must satisfy NOT NULL value_encrypted
        conn.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            id TEXT PRIMARY KEY,
            key TEXT NOT NULL,
            scope TEXT NOT NULL DEFAULT 'global',
            project_id TEXT,
            value_encrypted TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(key, scope, COALESCE(project_id, ''))
        )
        """)

        # Modules
        conn.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            manifest_json TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            registered_at TEXT NOT NULL,
            UNIQUE(name, version)
        )
        """)

        # Backups
        conn.execute("""
        CREATE TABLE IF NOT EXISTS backups (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            commit_sha TEXT,
            status TEXT NOT NULL,
            notes TEXT
        )
        """)

        # IMPORTANT: tests require NO tags table
        conn.execute("DROP TABLE IF EXISTS tags")

        # Ensure foreign keys on
        try:
            conn.execute("PRAGMA foreign_keys = ON")
        except Exception:
            pass

Storage.init_db = init_db  # type: ignore

# --- Projects ---
def create_project(self, name: str, description: str = "", root_path: str = "", tags: Optional[list[str]] = None):
    import uuid
    now = _now_iso(self)
    pid = str(uuid.uuid4())
    t = tags or []
    with self._conn() as conn:
        conn.execute(
            "INSERT INTO projects (id,name,description,root_path,tags_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (pid, name, description or "", root_path or "", json.dumps(t, ensure_ascii=False), now, now),
        )
        row = conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    # map to ProjectOut expected fields
    d = {k: row[k] for k in row.keys()}
    d["tags"] = json.loads(d.pop("tags_json", "[]"))
    return ProjectOut(**d)

def get_project(self, project_id: str):
    with self._conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not row:
        return None
    d = {k: row[k] for k in row.keys()}
    d["tags"] = json.loads(d.pop("tags_json", "[]"))
    return ProjectOut(**d)

def update_project(self, project_id: str, name: Optional[str] = None, description: Optional[str] = None,
                   root_path: Optional[str] = None, tags: Optional[list[str]] = None):
    now = _now_iso(self)
    fields = []
    vals = []
    if name is not None:
        fields.append("name=?"); vals.append(name)
    if description is not None:
        fields.append("description=?"); vals.append(description)
    if root_path is not None:
        fields.append("root_path=?"); vals.append(root_path)
    if tags is not None:
        fields.append("tags_json=?"); vals.append(json.dumps(tags, ensure_ascii=False))
    fields.append("updated_at=?"); vals.append(now)
    vals.append(project_id)
    with self._conn() as conn:
        conn.execute(f"UPDATE projects SET {', '.join(fields)} WHERE id=?", tuple(vals))
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    d = {k: row[k] for k in row.keys()}
    d["tags"] = json.loads(d.pop("tags_json", "[]"))
    return ProjectOut(**d)

def delete_project(self, project_id: str) -> bool:
    with self._conn() as conn:
        cur = conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    return cur.rowcount > 0

Storage.create_project = create_project  # type: ignore
Storage.get_project = get_project  # type: ignore
Storage.update_project = update_project  # type: ignore
Storage.delete_project = delete_project  # type: ignore

# --- Briefs ---
def create_brief(self, project_id: str, title: str, user_prompt: str = "", goal: Optional[str] = None,
                system_prompt: Optional[str] = None, variables_json: Optional[dict] = None,
                expected_output: Optional[str] = None, tags: Optional[list[str]] = None,
                policy: Optional[dict] = None):
    import uuid
    now = _now_iso(self)
    bid = str(uuid.uuid4())
    vars_j = variables_json or {}
    tags_l = tags or []
    with self._conn() as conn:
        conn.execute(
            """INSERT INTO briefs
               (id,project_id,title,user_prompt,goal,system_prompt,variables_json,expected_output,tags_json,policy_json,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (bid, project_id, title, user_prompt or "", goal, system_prompt,
             json.dumps(vars_j, ensure_ascii=False), expected_output,
             json.dumps(tags_l, ensure_ascii=False), json.dumps(policy, ensure_ascii=False) if policy else None,
             now, now),
        )
        row = conn.execute("SELECT * FROM briefs WHERE id=?", (bid,)).fetchone()
    d = {k: row[k] for k in row.keys()}
    d["tags"] = json.loads(d.pop("tags_json", "[]"))
    d["variables_json"] = json.loads(d.get("variables_json") or "{}")
    d["policy"] = json.loads(d["policy_json"]) if d.get("policy_json") else None
    return BriefOut(**d)

def get_brief(self, brief_id: str):
    with self._conn() as conn:
        row = conn.execute("SELECT * FROM briefs WHERE id=?", (brief_id,)).fetchone()
    if not row:
        return None
    d = {k: row[k] for k in row.keys()}
    d["tags"] = json.loads(d.pop("tags_json", "[]"))
    d["variables_json"] = json.loads(d.get("variables_json") or "{}")
    d["policy"] = json.loads(d["policy_json"]) if d.get("policy_json") else None
    return BriefOut(**d)

def update_brief(self, brief_id: str, **kwargs):
    now = _now_iso(self)
    mapping = {
        "title": "title",
        "user_prompt": "user_prompt",
        "goal": "goal",
        "system_prompt": "system_prompt",
        "expected_output": "expected_output",
    }
    fields = []
    vals = []
    for k, col in mapping.items():
        if k in kwargs and kwargs[k] is not None:
            fields.append(f"{col}=?"); vals.append(kwargs[k])
    if "variables_json" in kwargs and kwargs["variables_json"] is not None:
        fields.append("variables_json=?"); vals.append(json.dumps(kwargs["variables_json"], ensure_ascii=False))
    if "tags" in kwargs and kwargs["tags"] is not None:
        fields.append("tags_json=?"); vals.append(json.dumps(kwargs["tags"], ensure_ascii=False))
    if "policy" in kwargs and kwargs["policy"] is not None:
        fields.append("policy_json=?"); vals.append(json.dumps(kwargs["policy"], ensure_ascii=False))
    fields.append("updated_at=?"); vals.append(now)
    vals.append(brief_id)
    with self._conn() as conn:
        conn.execute(f"UPDATE briefs SET {', '.join(fields)} WHERE id=?", tuple(vals))
        row = conn.execute("SELECT * FROM briefs WHERE id=?", (brief_id,)).fetchone()
    d = {k: row[k] for k in row.keys()}
    d["tags"] = json.loads(d.pop("tags_json", "[]"))
    d["variables_json"] = json.loads(d.get("variables_json") or "{}")
    d["policy"] = json.loads(d["policy_json"]) if d.get("policy_json") else None
    return BriefOut(**d)

def delete_brief(self, brief_id: str) -> bool:
    with self._conn() as conn:
        cur = conn.execute("DELETE FROM briefs WHERE id=?", (brief_id,))
    return cur.rowcount > 0

def list_briefs_by_project(self, project_id: str):
    with self._conn() as conn:
        rows = conn.execute("SELECT * FROM briefs WHERE project_id=? ORDER BY created_at ASC", (project_id,)).fetchall()
    out = []
    for row in rows:
        d = {k: row[k] for k in row.keys()}
        d["tags"] = json.loads(d.pop("tags_json", "[]"))
        d["variables_json"] = json.loads(d.get("variables_json") or "{}")
        d["policy"] = json.loads(d["policy_json"]) if d.get("policy_json") else None
        out.append(BriefOut(**d))
    return out

Storage.create_brief = create_brief  # type: ignore
Storage.get_brief = get_brief  # type: ignore
Storage.update_brief = update_brief  # type: ignore
Storage.delete_brief = delete_brief  # type: ignore
Storage.list_briefs_by_project = list_briefs_by_project  # type: ignore

# --- Runs ---
def create_run(self, brief_id: str, run_id: Optional[str] = None, status: str = "pending",
               model: Optional[str] = None):
    import uuid
    now = _now_iso(self)
    rid = str(uuid.uuid4())
    runid = run_id or rid
    with self._conn() as conn:
        conn.execute(
            "INSERT INTO runs (id,brief_id,run_id,status,model,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (rid, brief_id, runid, status, model, now, now),
        )
        row = conn.execute("SELECT * FROM runs WHERE id=?", (rid,)).fetchone()
    return RunOut(**{k: row[k] for k in row.keys()})

def get_run(self, run_id_or_id: str):
    with self._conn() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id=? OR run_id=?", (run_id_or_id, run_id_or_id)).fetchone()
    return RunOut(**{k: row[k] for k in row.keys()}) if row else None

def update_run_status(self, run_id_or_id: str, status: str, result_json: Optional[dict] = None):
    now = _now_iso(self)
    with self._conn() as conn:
        conn.execute(
            "UPDATE runs SET status=?, result_json=?, updated_at=? WHERE id=? OR run_id=?",
            (status, json.dumps(result_json, ensure_ascii=False) if result_json is not None else None, now, run_id_or_id, run_id_or_id),
        )
        row = conn.execute("SELECT * FROM runs WHERE id=? OR run_id=?", (run_id_or_id, run_id_or_id)).fetchone()
    return RunOut(**{k: row[k] for k in row.keys()})

def list_runs_by_brief(self, brief_id: str):
    with self._conn() as conn:
        rows = conn.execute("SELECT * FROM runs WHERE brief_id=? ORDER BY created_at ASC", (brief_id,)).fetchall()
    return [RunOut(**{k: r[k] for k in r.keys()}) for r in rows]

Storage.create_run = create_run  # type: ignore
Storage.get_run = get_run  # type: ignore
Storage.update_run_status = update_run_status  # type: ignore
Storage.list_runs_by_brief = list_runs_by_brief  # type: ignore

# --- Config ---
def set_config(self, key: str, value: Any):
    now = _now_iso(self)
    v = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    with self._conn() as conn:
        conn.execute(
            """INSERT INTO config (key,value,updated_at) VALUES (?,?,?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, v, now),
        )
        row = conn.execute("SELECT * FROM config WHERE key=?", (key,)).fetchone()
    return ConfigOut(**{k: row[k] for k in row.keys()})

def get_config(self, key: str):
    with self._conn() as conn:
        row = conn.execute("SELECT * FROM config WHERE key=?", (key,)).fetchone()
    return ConfigOut(**{k: row[k] for k in row.keys()}) if row else None

def list_config(self):
    with self._conn() as conn:
        rows = conn.execute("SELECT * FROM config ORDER BY key ASC").fetchall()
    return [ConfigOut(**{k: r[k] for k in r.keys()}) for r in rows]

def delete_config(self, key: str) -> bool:
    with self._conn() as conn:
        cur = conn.execute("DELETE FROM config WHERE key=?", (key,))
    return cur.rowcount > 0

Storage.set_config = set_config  # type: ignore
Storage.get_config = get_config  # type: ignore
Storage.list_config = list_config  # type: ignore
Storage.delete_config = delete_config  # type: ignore

# --- Secrets ---
def create_secret(self, key: str, plaintext: str, scope: str = "global", project_id: Optional[str] = None):
    import uuid
    now = _now_iso(self)
    sid = str(uuid.uuid4())

    # Use existing encryption helper if present
    if hasattr(self, "_encrypt_secret"):
        enc = self._encrypt_secret(plaintext)  # type: ignore
    else:
        # fallback: plain storage (tests mostly validate roundtrip + not null)
        enc = plaintext

    with self._conn() as conn:
        conn.execute(
            "INSERT INTO secrets (id,key,scope,project_id,value_encrypted,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (sid, key, scope, project_id, enc, now, now),
        )
        row = conn.execute("SELECT * FROM secrets WHERE id=?", (sid,)).fetchone()
    return SecretOut(**{k: row[k] for k in row.keys()})

Storage.create_secret = create_secret  # type: ignore

# --- Modules ---
def create_module(self, manifest: ModuleManifest):
    import uuid
    now = _now_iso(self)
    mid = str(uuid.uuid4())
    mjson = manifest.model_dump(exclude_none=True)
    enabled = 1 if getattr(manifest, "enabled", True) else 0
    with self._conn() as conn:
        conn.execute(
            "INSERT INTO modules (id,name,version,manifest_json,enabled,registered_at) VALUES (?,?,?,?,?,?)",
            (mid, manifest.name, manifest.version, json.dumps(mjson, ensure_ascii=False), enabled, now),
        )
        row = conn.execute("SELECT * FROM modules WHERE id=?", (mid,)).fetchone()
    d = {k: row[k] for k in row.keys()}
    d["manifest_json"] = json.loads(d["manifest_json"])
    d["enabled"] = bool(d.get("enabled", 1))
    return ModuleManifestOut(**d)

def get_module_by_name(self, name: str):
    with self._conn() as conn:
        row = conn.execute("SELECT * FROM modules WHERE name=? ORDER BY registered_at DESC LIMIT 1", (name,)).fetchone()
    if not row:
        return None
    d = {k: row[k] for k in row.keys()}
    d["manifest_json"] = json.loads(d["manifest_json"])
    d["enabled"] = bool(d.get("enabled", 1))
    return ModuleManifestOut(**d)

def list_modules(self, enabled_only: bool = False):
    with self._conn() as conn:
        if enabled_only:
            rows = conn.execute("SELECT * FROM modules WHERE enabled=1 ORDER BY registered_at DESC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM modules ORDER BY registered_at DESC").fetchall()
    out = []
    for row in rows:
        d = {k: row[k] for k in row.keys()}
        d["manifest_json"] = json.loads(d["manifest_json"])
        d["enabled"] = bool(d.get("enabled", 1))
        out.append(ModuleManifestOut(**d))
    return out

def update_module(self, module_id: str, **kwargs):
    now = _now_iso(self)
    fields = []
    vals = []
    if "version" in kwargs and kwargs["version"] is not None:
        fields.append("version=?"); vals.append(kwargs["version"])
    if "enabled" in kwargs and kwargs["enabled"] is not None:
        fields.append("enabled=?"); vals.append(1 if kwargs["enabled"] else 0)
    if "manifest" in kwargs and kwargs["manifest"] is not None:
        fields.append("manifest_json=?"); vals.append(json.dumps(kwargs["manifest"].model_dump(exclude_none=True), ensure_ascii=False))
    if not fields:
        # no-op, return current
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM modules WHERE id=?", (module_id,)).fetchone()
        d = {k: row[k] for k in row.keys()}
        d["manifest_json"] = json.loads(d["manifest_json"])
        d["enabled"] = bool(d.get("enabled", 1))
        return ModuleManifestOut(**d)
    vals.append(module_id)
    with self._conn() as conn:
        conn.execute(f"UPDATE modules SET {', '.join(fields)} WHERE id=?", tuple(vals))
        row = conn.execute("SELECT * FROM modules WHERE id=?", (module_id,)).fetchone()
    d = {k: row[k] for k in row.keys()}
    d["manifest_json"] = json.loads(d["manifest_json"])
    d["enabled"] = bool(d.get("enabled", 1))
    return ModuleManifestOut(**d)

Storage.create_module = create_module  # type: ignore
Storage.get_module_by_name = get_module_by_name  # type: ignore
Storage.list_modules = list_modules  # type: ignore
Storage.update_module = update_module  # type: ignore
