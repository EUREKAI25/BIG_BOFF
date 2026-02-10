"""
EURKAI_COCKPIT — Secrets Module Tests
Version: 1.0.0

Comprehensive tests for:
- AES-256-GCM encryption/decryption
- Argon2 key derivation
- Gate password verification
- Copy-gated reveal (list != reveal)
- Audit logging

Acceptance criteria:
- list_secrets() NEVER returns plaintext values
- reveal_secret() requires gate password
- All actions are logged
"""

import os
import pytest
import tempfile
from pathlib import Path

# Set up environment before imports
os.environ["EURKAI_SECRET_KEY"] = "8B8vXQ3qZ2xq2z5x5Y9kL3mN6pR9sT2w4A7cF0hJ1kL="

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.secrets.crypto import (
    SecretCrypto,
    EncryptedPayload,
    derive_key,
    hash_password,
    verify_password_strength,
    generate_secure_password,
    AES_KEY_SIZE,
    NONCE_SIZE,
    ARGON2_SALT_LEN,
)

from backend.secrets.service import (
    SecretsService,
    SecretMetadata,
    SecretLogEntry,
    RevealResult,
    SecretAction,
    ActionResult,
)


# ============================================
# MOCK STORAGE FOR TESTING
# ============================================

class MockStorage:
    """Minimal storage mock for testing secrets service."""
    
    def __init__(self, db_path: Path):
        import sqlite3
        self.db_path = db_path
        self._conn = None
        self._init_db()
    
    def _init_db(self):
        import sqlite3
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            PRAGMA foreign_keys = ON;
            
            CREATE TABLE IF NOT EXISTS config (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL UNIQUE,
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            
            CREATE TABLE IF NOT EXISTS secrets (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL,
                encrypted_value BLOB NOT NULL,
                nonce BLOB NOT NULL,
                scope TEXT NOT NULL DEFAULT 'global',
                project_id TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(key, scope, project_id)
            );
        """)
        conn.commit()
        conn.close()
    
    def connection(self):
        import sqlite3
        from contextlib import contextmanager
        
        @contextmanager
        def _conn():
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except:
                conn.rollback()
                raise
            finally:
                conn.close()
        
        return _conn()
    
    def get_config(self, key: str):
        import json
        from dataclasses import dataclass
        
        @dataclass
        class Config:
            id: str
            key: str
            value_json: any
            updated_at: str
        
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM config WHERE key = ?", (key,)
            ).fetchone()
            if row:
                return Config(
                    id=row["id"],
                    key=row["key"],
                    value_json=json.loads(row["value_json"]),
                    updated_at=row["updated_at"]
                )
        return None
    
    def set_config(self, key: str, value):
        import json
        import uuid
        from datetime import datetime, timezone
        
        with self.connection() as conn:
            existing = conn.execute(
                "SELECT id FROM config WHERE key = ?", (key,)
            ).fetchone()
            
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            if existing:
                conn.execute(
                    "UPDATE config SET value_json = ?, updated_at = ? WHERE key = ?",
                    (json.dumps(value), now, key)
                )
            else:
                conn.execute(
                    "INSERT INTO config (id, key, value_json, updated_at) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), key, json.dumps(value), now)
                )
    
    def get_secret(self, secret_id: str):
        from dataclasses import dataclass
        from typing import Optional
        
        @dataclass
        class Secret:
            id: str
            key: str
            encrypted_value: bytes
            nonce: bytes
            scope: str
            project_id: Optional[str]
            created_at: str
            updated_at: str
        
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM secrets WHERE id = ?", (secret_id,)
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
    
    def get_secret_by_key(self, key: str, scope: str = "global", project_id=None):
        from dataclasses import dataclass
        from typing import Optional
        
        @dataclass
        class Secret:
            id: str
            key: str
            encrypted_value: bytes
            nonce: bytes
            scope: str
            project_id: Optional[str]
            created_at: str
            updated_at: str
        
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
    
    def list_secrets(self, scope=None, project_id=None):
        from dataclasses import dataclass
        from typing import Optional
        
        @dataclass
        class Secret:
            id: str
            key: str
            encrypted_value: bytes
            nonce: bytes
            scope: str
            project_id: Optional[str]
            created_at: str
            updated_at: str
        
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
    
    def delete_secret(self, secret_id: str) -> bool:
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM secrets WHERE id = ?", (secret_id,))
            return cursor.rowcount > 0


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def temp_db():
    """Create temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def storage(temp_db):
    """Create mock storage instance."""
    return MockStorage(temp_db)


@pytest.fixture
def service(storage):
    """Create secrets service with initialized gate password."""
    svc = SecretsService(storage)
    svc.initialize_gate_password("TestPassword123!")
    return svc


@pytest.fixture
def gate_password():
    """Standard test gate password."""
    return "TestPassword123!"


# ============================================
# CRYPTO TESTS
# ============================================

class TestCrypto:
    """Test AES-256-GCM encryption."""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Encryption and decryption produce original value."""
        crypto = SecretCrypto("test-password")
        original = "super-secret-api-key"
        
        encrypted = crypto.encrypt(original)
        decrypted = crypto.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_produces_different_ciphertext(self):
        """Same plaintext produces different ciphertext (unique salt/nonce)."""
        crypto = SecretCrypto("test-password")
        
        enc1 = crypto.encrypt("same-value")
        enc2 = crypto.encrypt("same-value")
        
        assert enc1.ciphertext != enc2.ciphertext
        assert enc1.nonce != enc2.nonce
        assert enc1.salt != enc2.salt
    
    def test_wrong_password_fails(self):
        """Decryption with wrong password fails."""
        crypto1 = SecretCrypto("correct-password")
        crypto2 = SecretCrypto("wrong-password")
        
        encrypted = crypto1.encrypt("secret")
        
        with pytest.raises(ValueError, match="Decryption failed"):
            crypto2.decrypt(encrypted)
    
    def test_bytes_serialization(self):
        """Encrypt/decrypt via bytes serialization."""
        crypto = SecretCrypto("my-password")
        original = "test-value"
        
        encrypted_bytes = crypto.encrypt_to_bytes(original)
        decrypted = crypto.decrypt_from_bytes(encrypted_bytes)
        
        assert decrypted == original
    
    def test_payload_structure(self):
        """EncryptedPayload has correct structure."""
        crypto = SecretCrypto("pwd")
        payload = crypto.encrypt("value")
        
        assert len(payload.nonce) == NONCE_SIZE
        assert len(payload.salt) == ARGON2_SALT_LEN
        assert len(payload.ciphertext) > 0


class TestKeyDerivation:
    """Test Argon2 key derivation."""
    
    def test_derive_key_length(self):
        """Derived key has correct length."""
        key, salt = derive_key("password")
        
        assert len(key) == AES_KEY_SIZE
        assert len(salt) == ARGON2_SALT_LEN
    
    def test_same_salt_same_key(self):
        """Same password + salt produces same key."""
        key1, salt = derive_key("password")
        key2, _ = derive_key("password", salt)
        
        assert key1 == key2
    
    def test_different_password_different_key(self):
        """Different passwords produce different keys."""
        key1, salt = derive_key("password1")
        key2, _ = derive_key("password2", salt)
        
        assert key1 != key2


class TestPasswordUtils:
    """Test password utilities."""
    
    def test_hash_password_consistent(self):
        """Same password produces same hash."""
        hash1 = hash_password("test")
        hash2 = hash_password("test")
        
        assert hash1 == hash2
    
    def test_hash_password_different(self):
        """Different passwords produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        
        assert hash1 != hash2
    
    def test_verify_password_strength_valid(self):
        """Strong password passes verification."""
        is_valid, issues = verify_password_strength("SecureP@ss123")
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_verify_password_strength_too_short(self):
        """Short password fails."""
        is_valid, issues = verify_password_strength("Ab1")
        
        assert is_valid is False
        assert any("8 characters" in i for i in issues)
    
    def test_generate_secure_password(self):
        """Generated passwords meet requirements."""
        pwd = generate_secure_password(32)
        
        assert len(pwd) == 32
        # Should have mixed chars
        assert any(c.isupper() for c in pwd)
        assert any(c.islower() for c in pwd)


# ============================================
# SERVICE TESTS
# ============================================

class TestGatePassword:
    """Test gate password management."""
    
    def test_initialize_gate_password(self, storage):
        """Gate password can be initialized."""
        service = SecretsService(storage)
        
        success, msg = service.initialize_gate_password("SecurePass123!")
        
        assert success is True
        assert service.is_gate_initialized() is True
    
    def test_cannot_reinitialize(self, service):
        """Gate password cannot be set twice."""
        success, msg = service.initialize_gate_password("NewPassword123!")
        
        assert success is False
        assert "already initialized" in msg
    
    def test_verify_correct_password(self, service, gate_password):
        """Correct password verifies."""
        assert service.verify_gate_password(gate_password) is True
    
    def test_verify_wrong_password(self, service):
        """Wrong password fails verification."""
        assert service.verify_gate_password("wrong-password") is False
    
    def test_weak_password_rejected(self, storage):
        """Weak passwords are rejected."""
        service = SecretsService(storage)
        
        success, msg = service.initialize_gate_password("weak")
        
        assert success is False
        assert "Weak password" in msg


class TestSecretsCRUD:
    """Test secret CRUD operations."""
    
    def test_create_secret(self, service, gate_password):
        """Create secret stores encrypted value."""
        meta, msg = service.create_secret(
            key="API_KEY",
            plaintext="sk-secret-value",
            gate_password=gate_password,
            source="cli"
        )
        
        assert meta is not None
        assert meta.key == "API_KEY"
        assert meta.scope == "global"
        assert "created" in msg.lower()
    
    def test_create_secret_wrong_password(self, service):
        """Create with wrong password fails."""
        meta, msg = service.create_secret(
            key="TEST",
            plaintext="value",
            gate_password="wrong",
            source="cli"
        )
        
        assert meta is None
        assert "Invalid gate password" in msg
    
    def test_create_duplicate_fails(self, service, gate_password):
        """Cannot create duplicate key in same scope."""
        service.create_secret("DUPE", "val1", gate_password)
        
        meta, msg = service.create_secret("DUPE", "val2", gate_password)
        
        assert meta is None
        assert "already exists" in msg
    
    def test_list_secrets_no_values(self, service, gate_password):
        """List returns metadata but NEVER plaintext values."""
        service.create_secret("KEY1", "secret1", gate_password)
        service.create_secret("KEY2", "secret2", gate_password)
        
        secrets = service.list_secrets()
        
        assert len(secrets) == 2
        for s in secrets:
            assert isinstance(s, SecretMetadata)
            # Verify no value attribute
            assert not hasattr(s, "value")
            assert not hasattr(s, "plaintext")
            # Only safe fields
            assert s.key in ["KEY1", "KEY2"]
            assert s.id is not None
            assert s.scope == "global"
    
    def test_delete_secret(self, service, gate_password):
        """Delete removes secret."""
        meta, _ = service.create_secret("DELETE_ME", "value", gate_password)
        
        success, msg = service.delete_secret(meta.id, gate_password)
        
        assert success is True
        
        # Verify deleted
        secrets = service.list_secrets()
        assert len(secrets) == 0


class TestCopyGating:
    """Test copy-gated reveal functionality.
    
    ACCEPTANCE CRITERIA:
    - list_secrets() != reveal_secret()
    - reveal only works with correct gate password
    """
    
    def test_list_does_not_reveal(self, service, gate_password):
        """List endpoint never exposes secret values."""
        service.create_secret("HIDDEN", "super-secret-value", gate_password)
        
        secrets = service.list_secrets()
        
        # SecretMetadata has no value field
        secret = secrets[0]
        data = secret.to_dict()
        
        assert "value" not in data
        assert "plaintext" not in data
        assert "encrypted_value" not in data
        assert "super-secret-value" not in str(data)
    
    def test_reveal_requires_password(self, service, gate_password):
        """Reveal fails without correct password."""
        meta, _ = service.create_secret("SECRET", "hidden-value", gate_password)
        
        # Try reveal with wrong password
        result = service.reveal_secret(meta.id, "wrong-password")
        
        assert result.success is False
        assert result.value is None
        assert "Invalid gate password" in result.error
    
    def test_reveal_with_correct_password(self, service, gate_password):
        """Reveal succeeds with correct password."""
        original_value = "my-api-key-12345"
        meta, _ = service.create_secret("API", original_value, gate_password)
        
        result = service.reveal_secret(meta.id, gate_password)
        
        assert result.success is True
        assert result.value == original_value
        assert result.error is None
    
    def test_copy_requires_password(self, service, gate_password):
        """Copy action also requires password."""
        meta, _ = service.create_secret("COPY_TEST", "value", gate_password)
        
        # Wrong password
        result = service.copy_secret(meta.id, "wrong")
        assert result.success is False
        
        # Correct password
        result = service.copy_secret(meta.id, gate_password)
        assert result.success is True
        assert result.value == "value"
    
    def test_reveal_nonexistent_secret(self, service, gate_password):
        """Reveal non-existent secret fails gracefully."""
        result = service.reveal_secret("fake-id", gate_password)
        
        assert result.success is False
        assert "not found" in result.error


class TestAuditLogging:
    """Test secret access logging."""
    
    def test_create_logged(self, service, gate_password):
        """Create action is logged."""
        service.create_secret("LOG_TEST", "value", gate_password, source="cli")
        
        logs = service.get_logs()
        
        assert len(logs) >= 1
        create_log = next((l for l in logs if l.action == "create"), None)
        assert create_log is not None
        assert create_log.secret_key == "LOG_TEST"
        assert create_log.result == "success"
        assert create_log.source == "cli"
    
    def test_list_logged(self, service, gate_password):
        """List action is logged."""
        service.list_secrets(source="api")
        
        logs = service.get_logs()
        
        list_log = next((l for l in logs if l.action == "list"), None)
        assert list_log is not None
        assert list_log.source == "api"
    
    def test_reveal_success_logged(self, service, gate_password):
        """Successful reveal is logged."""
        meta, _ = service.create_secret("REVEAL_LOG", "val", gate_password)
        service.reveal_secret(meta.id, gate_password, source="ui")
        
        logs = service.get_logs(secret_id=meta.id, action="reveal")
        
        assert len(logs) == 1
        assert logs[0].result == "success"
        assert logs[0].source == "ui"
    
    def test_reveal_failure_logged(self, service, gate_password):
        """Failed reveal is logged with reason."""
        meta, _ = service.create_secret("FAIL_LOG", "val", gate_password)
        service.reveal_secret(meta.id, "wrong-password")
        
        logs = service.get_logs(secret_id=meta.id, action="reveal")
        
        assert len(logs) == 1
        assert logs[0].result == "fail"
        assert "Invalid gate password" in logs[0].reason
    
    def test_log_never_contains_value(self, service, gate_password):
        """Logs never contain secret values."""
        secret_value = "super-secret-api-key-xyz"
        meta, _ = service.create_secret("NO_VALUE_LOG", secret_value, gate_password)
        service.reveal_secret(meta.id, gate_password)
        service.copy_secret(meta.id, gate_password)
        
        logs = service.get_logs()
        
        for log in logs:
            log_str = str(log.to_dict())
            assert secret_value not in log_str


class TestScopes:
    """Test global vs project scoping."""
    
    def test_global_scope_default(self, service, gate_password):
        """Secrets default to global scope."""
        meta, _ = service.create_secret("GLOBAL", "val", gate_password)
        
        assert meta.scope == "global"
        assert meta.project_id is None
    
    def test_project_scope(self, service, gate_password):
        """Project-scoped secrets store project_id."""
        meta, _ = service.create_secret(
            "PROJECT_SECRET",
            "val",
            gate_password,
            scope="project",
            project_id="proj-123"
        )
        
        assert meta.scope == "project"
        assert meta.project_id == "proj-123"
    
    def test_same_key_different_scopes(self, service, gate_password):
        """Same key allowed in different scopes."""
        meta1, _ = service.create_secret(
            "SHARED_KEY", "global-val", gate_password, scope="global"
        )
        meta2, _ = service.create_secret(
            "SHARED_KEY", "project-val", gate_password,
            scope="project", project_id="proj-1"
        )
        
        assert meta1 is not None
        assert meta2 is not None
        assert meta1.id != meta2.id


# ============================================
# ACCEPTANCE TESTS
# ============================================

class TestAcceptance:
    """
    Final acceptance tests per C06 requirements:
    - list != reveal
    - reveal only with gate
    """
    
    def test_acceptance_list_never_reveals(self, service, gate_password):
        """
        ACCEPTANCE: List endpoint NEVER returns plaintext values.
        """
        # Create multiple secrets
        secrets_data = [
            ("DB_PASSWORD", "postgres123"),
            ("API_KEY", "sk-abcdef123456"),
            ("JWT_SECRET", "jwt-super-secret-key"),
        ]
        
        for key, value in secrets_data:
            service.create_secret(key, value, gate_password)
        
        # List all secrets
        listed = service.list_secrets()
        
        # Verify no plaintext leaked
        for meta in listed:
            # Check object has no value fields
            assert not hasattr(meta, "value")
            assert not hasattr(meta, "plaintext")
            assert not hasattr(meta, "decrypted")
            
            # Check serialized dict
            data = meta.to_dict()
            for key, value in secrets_data:
                assert value not in str(data)
    
    def test_acceptance_reveal_only_with_gate(self, service, gate_password):
        """
        ACCEPTANCE: Reveal/copy requires gate password.
        """
        secret_value = "my-very-secret-value-12345"
        meta, _ = service.create_secret("GATED", secret_value, gate_password)
        
        # Without password: fail
        result_no_pwd = service.reveal_secret(meta.id, "")
        assert result_no_pwd.success is False
        assert result_no_pwd.value is None
        
        # Wrong password: fail
        result_wrong = service.reveal_secret(meta.id, "incorrect")
        assert result_wrong.success is False
        assert result_wrong.value is None
        
        # Correct password: success
        result_ok = service.reveal_secret(meta.id, gate_password)
        assert result_ok.success is True
        assert result_ok.value == secret_value
    
    def test_acceptance_all_actions_logged(self, service, gate_password):
        """
        ACCEPTANCE: All actions are logged.
        """
        # Perform various actions
        meta, _ = service.create_secret("LOGGED", "val", gate_password)
        service.list_secrets()
        service.reveal_secret(meta.id, gate_password)
        service.reveal_secret(meta.id, "wrong")  # Failed attempt
        service.copy_secret(meta.id, gate_password)
        service.delete_secret(meta.id, gate_password)
        
        logs = service.get_logs()
        actions = [l.action for l in logs]
        
        assert "create" in actions
        assert "list" in actions
        assert "reveal" in actions
        assert "copy" in actions
        assert "delete" in actions
        
        # Verify failed attempt logged
        failed = [l for l in logs if l.result == "fail"]
        assert len(failed) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
