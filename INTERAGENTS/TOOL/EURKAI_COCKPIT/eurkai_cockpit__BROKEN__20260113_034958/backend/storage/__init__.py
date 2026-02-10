"""
EURKAI_COCKPIT Storage Layer (public exports)
"""

from .storage import Storage
from .migrations import init_db, get_db_path, get_schema_version

# Public DTOs expected by tests / external callers
from backend.models import (
    ProjectOut as Project,
    BriefOut as Brief,
    RunOut as Run,
    ModuleManifestOut as Module,
    ModuleManifestOut as ModuleManifest,
    ConfigOut as Config,
    SecretOut as Secret,
    BackupOut as Backup,
)


# ---------------------------------------------------------------------
# Compatibility: tests expect a lightweight input model named ModuleManifest
try:
    from pydantic import BaseModel, Field
    from typing import Any, Optional, List, Dict
    class ModuleManifest(BaseModel):
        name: str
        version: str
        description: str = ""
        inputs: List[Dict[str, Any]] = Field(default_factory=list)
        outputs: List[Dict[str, Any]] = Field(default_factory=list)
        constraints: Dict[str, Any] = Field(default_factory=lambda: {"hard": [], "soft": []})
        tags: List[str] = Field(default_factory=list)
        enabled: bool = True
        # optional fields (output DB may fill them)
        id: Optional[str] = None
        registered_at: Optional[str] = None
except Exception:
    ModuleManifest = None  # type: ignore

__all__ = [
    "Storage",
    "init_db",
    "init_database",
    "get_db_path",
    "get_schema_version",
    "SCHEMA_VERSION",
    "generate_uuid",
    "utc_now",
    "Project",
    "Brief",
    "Run",
    "Module",
    "ModuleManifest",
    "Config",
    "Secret",
    "SecretEncryption",
    "Backup",
]

# Secret encryption policy/type expected by tests
try:
    from backend.models import SecretEncryption  # type: ignore
except Exception:
    try:
        from backend.secrets.crypto import SecretEncryption  # type: ignore
    except Exception:
        SecretEncryption = None  # type: ignore

# Utilities expected by tests
import uuid as _uuid

def generate_uuid() -> str:
    return str(_uuid.uuid4())

from enum import Enum
from datetime import datetime, timezone

def utc_now() -> str:
    """UTC timestamp in ISO8601 string format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")# Backwards-compatible alias expected by tests
init_database = init_db


# Schema version constant expected by tests
SCHEMA_VERSION = 1
class SecretEncryption:
    """Simple AES-256-GCM helper used by tests."""

    def __init__(self, key: str | None = None):
        # Key comes from env (same as the rest of the project), fallback to deterministic dev key.
        import os, hashlib
        raw = (key or os.getenv("EURKAI_SECRET_KEY") or "dev-local-key-change-me").encode("utf-8")
        # derive 32 bytes
        self._key = hashlib.sha256(raw).digest()

    def encrypt(self, plaintext: str) -> str:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import os, base64
        aes = AESGCM(self._key)
        nonce = os.urandom(12)
        ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ct).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import base64
        raw = base64.b64decode(ciphertext.encode("utf-8"))
        nonce, ct = raw[:12], raw[12:]
        aes = AESGCM(self._key)
        pt = aes.decrypt(nonce, ct, None)
        return pt.decode("utf-8")



# ---------------------------------------------------------------------
# Compatibility: tests expect SecretEncryption.encrypt() -> (ciphertext, nonce)
# We keep your internal encrypt/decrypt but expose pair helpers.
try:
    import base64
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    def _se_encrypt_pair(self, plaintext: str):
        nonce = __import__("os").urandom(12)
        aes = AESGCM(self._key)
        ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(ct).decode("utf-8"), base64.b64encode(nonce).decode("utf-8")

    def _se_decrypt_pair(self, ciphertext_b64: str, nonce_b64: str) -> str:
        ct = base64.b64decode(ciphertext_b64.encode("utf-8"))
        nonce = base64.b64decode(nonce_b64.encode("utf-8"))
        aes = AESGCM(self._key)
        pt = aes.decrypt(nonce, ct, None)
        return pt.decode("utf-8")

    # Monkeypatch methods expected by tests
    SecretEncryption.encrypt = _se_encrypt_pair  # type: ignore
    SecretEncryption.decrypt = _se_decrypt_pair  # type: ignore
except Exception:
    pass
