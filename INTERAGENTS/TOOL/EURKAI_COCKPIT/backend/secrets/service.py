"""
EURKAI_COCKPIT — Secrets Service
Version: 1.0.0

High-level secrets management with:
- Create/list/delete secrets
- Copy-gated reveal (requires gate password)
- Comprehensive audit logging

Security principles:
- List endpoint NEVER returns plaintext
- Reveal requires gate password verification
- All access logged to database
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

from .crypto import (
    SecretCrypto,
    EncryptedPayload,
    hash_password,
    verify_password_strength,
)

if TYPE_CHECKING:
    import sqlite3


# ============================================
# CONSTANTS
# ============================================

GATE_PASSWORD_CONFIG_KEY = "secrets.gate_password_hash"


# ============================================
# ENUMS
# ============================================

class SecretScope(str, Enum):
    """Secret visibility scope."""
    GLOBAL = "global"
    PROJECT = "project"


class SecretAction(str, Enum):
    """Actions performed on secrets."""
    CREATE = "create"
    LIST = "list"
    REVEAL = "reveal"
    COPY = "copy"
    UPDATE = "update"
    DELETE = "delete"


class SecretSource(str, Enum):
    """Source of secret access."""
    CLI = "cli"
    API = "api"
    UI = "ui"


class ActionResult(str, Enum):
    """Result of secret action."""
    SUCCESS = "success"
    FAIL = "fail"


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class SecretMetadata:
    """Secret metadata (no plaintext value)."""
    id: str
    key: str
    scope: str
    project_id: Optional[str]
    created_at: str
    updated_at: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (safe for API response)."""
        return {
            "id": self.id,
            "key": self.key,
            "scope": self.scope,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            # NEVER include value
        }


@dataclass
class SecretLogEntry:
    """Audit log entry for secret access."""
    id: str
    timestamp: str
    secret_id: str
    secret_key: str
    scope: str
    action: str
    result: str
    source: str
    reason: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "secret_id": self.secret_id,
            "secret_key": self.secret_key,
            "scope": self.scope,
            "action": self.action,
            "result": self.result,
            "source": self.source,
            "reason": self.reason,
        }


@dataclass
class RevealResult:
    """Result of reveal/copy operation."""
    success: bool
    value: Optional[str] = None
    error: Optional[str] = None


# ============================================
# HELPER FUNCTIONS
# ============================================

def _utc_now() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_uuid() -> str:
    """Generate a new UUID v4."""
    return str(uuid.uuid4())


# ============================================
# SECRETS SERVICE
# ============================================

class SecretsService:
    """
    Secrets management service with copy-gating.
    
    Usage:
        service = SecretsService(storage)
        
        # Initialize gate password (first time only)
        service.initialize_gate_password("my-secure-password")
        
        # Create a secret
        service.create_secret("API_KEY", "sk-xxx", "my-password", source="cli")
        
        # List secrets (never returns values)
        secrets = service.list_secrets()
        
        # Reveal with gate password
        result = service.reveal_secret(secret_id, "my-password", source="cli")
        if result.success:
            print(result.value)
    """
    
    def __init__(self, storage: Any):
        """
        Initialize service with storage backend.
        
        Args:
            storage: Storage instance (from C02)
        """
        self._storage = storage
        self._ensure_log_table()
    
    def _ensure_log_table(self) -> None:
        """Ensure secret_logs table exists."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS secret_logs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            secret_id TEXT NOT NULL,
            secret_key TEXT NOT NULL,
            scope TEXT NOT NULL,
            action TEXT NOT NULL,
            result TEXT NOT NULL,
            source TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_secret_logs_secret ON secret_logs(secret_id);
        CREATE INDEX IF NOT EXISTS idx_secret_logs_action ON secret_logs(action);
        CREATE INDEX IF NOT EXISTS idx_secret_logs_timestamp ON secret_logs(timestamp);
        """
        with self._storage.connection() as conn:
            conn.executescript(create_sql)
    
    # ----------------------------------------
    # GATE PASSWORD MANAGEMENT
    # ----------------------------------------
    
    def is_gate_initialized(self) -> bool:
        """Check if gate password has been set."""
        config = self._storage.get_config(GATE_PASSWORD_CONFIG_KEY)
        return config is not None
    
    def initialize_gate_password(self, password: str) -> tuple[bool, str]:
        """
        Initialize the master gate password.
        
        Args:
            password: Master gate password
        
        Returns:
            Tuple of (success, message)
        """
        if self.is_gate_initialized():
            return False, "Gate password already initialized"
        
        is_valid, issues = verify_password_strength(password)
        if not is_valid:
            return False, f"Weak password: {', '.join(issues)}"
        
        password_hash = hash_password(password)
        self._storage.set_config(GATE_PASSWORD_CONFIG_KEY, password_hash)
        
        return True, "Gate password initialized"
    
    def verify_gate_password(self, password: str) -> bool:
        """Verify gate password is correct."""
        config = self._storage.get_config(GATE_PASSWORD_CONFIG_KEY)
        if config is None:
            return False
        
        return config.value_json == hash_password(password)
    
    def change_gate_password(
        self, 
        old_password: str, 
        new_password: str
    ) -> tuple[bool, str]:
        """
        Change the gate password and re-encrypt all secrets.
        
        Args:
            old_password: Current gate password
            new_password: New gate password
        
        Returns:
            Tuple of (success, message)
        """
        if not self.verify_gate_password(old_password):
            return False, "Invalid current password"
        
        is_valid, issues = verify_password_strength(new_password)
        if not is_valid:
            return False, f"Weak new password: {', '.join(issues)}"
        
        # Re-encrypt all secrets
        old_crypto = SecretCrypto(old_password)
        new_crypto = SecretCrypto(new_password)
        
        secrets = self._storage.list_secrets()
        for secret in secrets:
            try:
                # Decrypt with old password
                payload = EncryptedPayload.from_bytes(
                    secret.encrypted_value + secret.nonce
                )
                # Actually the storage format is different, handle properly
                payload = EncryptedPayload(
                    ciphertext=secret.encrypted_value,
                    nonce=secret.nonce,
                    salt=secret.nonce[:16]  # Migration: use nonce as salt placeholder
                )
                plaintext = old_crypto.decrypt_from_bytes(
                    secret.encrypted_value
                )
                
                # Re-encrypt with new password
                new_encrypted = new_crypto.encrypt_to_bytes(plaintext)
                
                # Update in database
                self._storage.update_secret_raw(
                    secret.id,
                    new_encrypted[16:28],  # nonce
                    new_encrypted[28:]     # ciphertext
                )
            except Exception as e:
                return False, f"Re-encryption failed for {secret.key}: {e}"
        
        # Update password hash
        self._storage.set_config(GATE_PASSWORD_CONFIG_KEY, hash_password(new_password))
        
        return True, f"Password changed, {len(secrets)} secrets re-encrypted"
    
    # ----------------------------------------
    # SECRET CRUD
    # ----------------------------------------
    
    def create_secret(
        self,
        key: str,
        plaintext: str,
        gate_password: str,
        scope: str = "global",
        project_id: Optional[str] = None,
        source: str = "api"
    ) -> tuple[Optional[SecretMetadata], str]:
        """
        Create a new encrypted secret.
        
        Args:
            key: Secret key/name
            plaintext: Secret value (will be encrypted)
            gate_password: Gate password for encryption
            scope: "global" or "project"
            project_id: Project ID if scope is "project"
            source: Source of action (cli/api/ui)
        
        Returns:
            Tuple of (SecretMetadata or None, message)
        """
        # Verify gate password
        if not self.verify_gate_password(gate_password):
            self._log_action(
                secret_id="",
                secret_key=key,
                scope=scope,
                action=SecretAction.CREATE,
                result=ActionResult.FAIL,
                source=source,
                reason="Invalid gate password"
            )
            return None, "Invalid gate password"
        
        # Check for duplicate
        existing = self._storage.get_secret_by_key(key, scope, project_id)
        if existing:
            self._log_action(
                secret_id=existing.id,
                secret_key=key,
                scope=scope,
                action=SecretAction.CREATE,
                result=ActionResult.FAIL,
                source=source,
                reason="Secret already exists"
            )
            return None, f"Secret '{key}' already exists in scope '{scope}'"
        
        # Encrypt
        crypto = SecretCrypto(gate_password)
        encrypted_bytes = crypto.encrypt_to_bytes(plaintext)
        
        # Parse encrypted payload
        payload = EncryptedPayload.from_bytes(encrypted_bytes)
        
        # Store (using existing storage interface with slight adaptation)
        secret = self._create_secret_raw(
            key=key,
            encrypted_value=encrypted_bytes,
            nonce=payload.nonce,
            scope=scope,
            project_id=project_id
        )
        
        # Log success
        self._log_action(
            secret_id=secret.id,
            secret_key=key,
            scope=scope,
            action=SecretAction.CREATE,
            result=ActionResult.SUCCESS,
            source=source
        )
        
        return SecretMetadata(
            id=secret.id,
            key=secret.key,
            scope=secret.scope,
            project_id=secret.project_id,
            created_at=secret.created_at,
            updated_at=secret.updated_at
        ), "Secret created"
    
    def _create_secret_raw(
        self,
        key: str,
        encrypted_value: bytes,
        nonce: bytes,
        scope: str,
        project_id: Optional[str]
    ) -> Any:
        """Create secret with raw encrypted bytes."""
        secret_id = _generate_uuid()
        now = _utc_now()
        
        with self._storage.connection() as conn:
            conn.execute(
                """INSERT INTO secrets 
                   (id, key, encrypted_value, nonce, scope, project_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (secret_id, key, encrypted_value, nonce, scope, project_id, now, now)
            )
        
        return self._storage.get_secret(secret_id)
    
    def list_secrets(
        self,
        scope: Optional[str] = None,
        project_id: Optional[str] = None,
        source: str = "api"
    ) -> list[SecretMetadata]:
        """
        List secrets metadata (NEVER returns values).
        
        Args:
            scope: Filter by scope
            project_id: Filter by project
            source: Source of action
        
        Returns:
            List of SecretMetadata (no plaintext values)
        """
        secrets = self._storage.list_secrets(scope, project_id)
        
        # Log list action (single entry, not per-secret)
        self._log_action(
            secret_id="*",
            secret_key="*",
            scope=scope or "all",
            action=SecretAction.LIST,
            result=ActionResult.SUCCESS,
            source=source
        )
        
        return [
            SecretMetadata(
                id=s.id,
                key=s.key,
                scope=s.scope,
                project_id=s.project_id,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
            for s in secrets
        ]
    
    def reveal_secret(
        self,
        secret_id: str,
        gate_password: str,
        source: str = "api"
    ) -> RevealResult:
        """
        Reveal (decrypt) a secret value.
        
        GATED: Requires gate password.
        
        Args:
            secret_id: Secret ID to reveal
            gate_password: Gate password
            source: Source of action
        
        Returns:
            RevealResult with success/value/error
        """
        secret = self._storage.get_secret(secret_id)
        if not secret:
            self._log_action(
                secret_id=secret_id,
                secret_key="unknown",
                scope="unknown",
                action=SecretAction.REVEAL,
                result=ActionResult.FAIL,
                source=source,
                reason="Secret not found"
            )
            return RevealResult(success=False, error="Secret not found")
        
        # Verify gate password
        if not self.verify_gate_password(gate_password):
            self._log_action(
                secret_id=secret_id,
                secret_key=secret.key,
                scope=secret.scope,
                action=SecretAction.REVEAL,
                result=ActionResult.FAIL,
                source=source,
                reason="Invalid gate password"
            )
            return RevealResult(success=False, error="Invalid gate password")
        
        # Decrypt
        try:
            crypto = SecretCrypto(gate_password)
            plaintext = crypto.decrypt_from_bytes(secret.encrypted_value)
            
            self._log_action(
                secret_id=secret_id,
                secret_key=secret.key,
                scope=secret.scope,
                action=SecretAction.REVEAL,
                result=ActionResult.SUCCESS,
                source=source
            )
            
            return RevealResult(success=True, value=plaintext)
        except Exception as e:
            self._log_action(
                secret_id=secret_id,
                secret_key=secret.key,
                scope=secret.scope,
                action=SecretAction.REVEAL,
                result=ActionResult.FAIL,
                source=source,
                reason=f"Decryption error: {type(e).__name__}"
            )
            return RevealResult(success=False, error="Decryption failed")
    
    def copy_secret(
        self,
        secret_id: str,
        gate_password: str,
        source: str = "api"
    ) -> RevealResult:
        """
        Copy secret value (same as reveal, different action logged).
        
        GATED: Requires gate password.
        
        Args:
            secret_id: Secret ID to copy
            gate_password: Gate password
            source: Source of action
        
        Returns:
            RevealResult with success/value/error
        """
        secret = self._storage.get_secret(secret_id)
        if not secret:
            self._log_action(
                secret_id=secret_id,
                secret_key="unknown",
                scope="unknown",
                action=SecretAction.COPY,
                result=ActionResult.FAIL,
                source=source,
                reason="Secret not found"
            )
            return RevealResult(success=False, error="Secret not found")
        
        # Verify gate password
        if not self.verify_gate_password(gate_password):
            self._log_action(
                secret_id=secret_id,
                secret_key=secret.key,
                scope=secret.scope,
                action=SecretAction.COPY,
                result=ActionResult.FAIL,
                source=source,
                reason="Invalid gate password"
            )
            return RevealResult(success=False, error="Invalid gate password")
        
        # Decrypt
        try:
            crypto = SecretCrypto(gate_password)
            plaintext = crypto.decrypt_from_bytes(secret.encrypted_value)
            
            self._log_action(
                secret_id=secret_id,
                secret_key=secret.key,
                scope=secret.scope,
                action=SecretAction.COPY,
                result=ActionResult.SUCCESS,
                source=source
            )
            
            return RevealResult(success=True, value=plaintext)
        except Exception:
            self._log_action(
                secret_id=secret_id,
                secret_key=secret.key,
                scope=secret.scope,
                action=SecretAction.COPY,
                result=ActionResult.FAIL,
                source=source,
                reason="Decryption error"
            )
            return RevealResult(success=False, error="Decryption failed")
    
    def delete_secret(
        self,
        secret_id: str,
        gate_password: str,
        source: str = "api"
    ) -> tuple[bool, str]:
        """
        Delete a secret.
        
        Args:
            secret_id: Secret ID to delete
            gate_password: Gate password
            source: Source of action
        
        Returns:
            Tuple of (success, message)
        """
        secret = self._storage.get_secret(secret_id)
        if not secret:
            return False, "Secret not found"
        
        # Verify gate password
        if not self.verify_gate_password(gate_password):
            self._log_action(
                secret_id=secret_id,
                secret_key=secret.key,
                scope=secret.scope,
                action=SecretAction.DELETE,
                result=ActionResult.FAIL,
                source=source,
                reason="Invalid gate password"
            )
            return False, "Invalid gate password"
        
        # Delete
        deleted = self._storage.delete_secret(secret_id)
        
        self._log_action(
            secret_id=secret_id,
            secret_key=secret.key,
            scope=secret.scope,
            action=SecretAction.DELETE,
            result=ActionResult.SUCCESS if deleted else ActionResult.FAIL,
            source=source
        )
        
        return deleted, "Secret deleted" if deleted else "Delete failed"
    
    # ----------------------------------------
    # LOGGING
    # ----------------------------------------
    
    def _log_action(
        self,
        secret_id: str,
        secret_key: str,
        scope: str,
        action: SecretAction,
        result: ActionResult,
        source: str,
        reason: Optional[str] = None
    ) -> None:
        """Log secret access to database."""
        log_id = _generate_uuid()
        timestamp = _utc_now()
        
        with self._storage.connection() as conn:
            conn.execute(
                """INSERT INTO secret_logs 
                   (id, timestamp, secret_id, secret_key, scope, action, result, source, reason, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (log_id, timestamp, secret_id, secret_key, scope,
                 action.value, result.value, source, reason, timestamp)
            )
    
    def get_logs(
        self,
        secret_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> list[SecretLogEntry]:
        """
        Retrieve secret access logs.
        
        Args:
            secret_id: Filter by secret ID
            action: Filter by action type
            limit: Maximum entries to return
        
        Returns:
            List of SecretLogEntry
        """
        with self._storage.connection() as conn:
            query = "SELECT * FROM secret_logs WHERE 1=1"
            params: list[Any] = []
            
            if secret_id:
                query += " AND secret_id = ?"
                params.append(secret_id)
            
            if action:
                query += " AND action = ?"
                params.append(action)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            
            return [
                SecretLogEntry(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    secret_id=row["secret_id"],
                    secret_key=row["secret_key"],
                    scope=row["scope"],
                    action=row["action"],
                    result=row["result"],
                    source=row["source"],
                    reason=row["reason"]
                )
                for row in rows
            ]
