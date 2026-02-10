"""
EURKAI_COCKPIT — API Dependencies
Version: 1.0.0

Shared dependencies: storage, auth, encryption.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import time
from datetime import datetime
from functools import lru_cache
from typing import Annotated, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from fastapi import Depends, Header, HTTPException, status

from ..storage import Storage
from ..models import ResponseMeta, ErrorDetail, ErrorResponse


# =============================================================================
# STORAGE SINGLETON
# =============================================================================

@lru_cache()
def get_storage() -> Storage:
    """Get storage singleton."""
    db_path = os.environ.get("EURKAI_DB_PATH")
    return Storage(db_path=db_path, auto_init=True)


StorageDep = Annotated[Storage, Depends(get_storage)]


# =============================================================================
# AUTH TOKEN (configurable)
# =============================================================================

def get_api_token() -> str | None:
    """
    Get API token from environment.
    If EURKAI_TOKEN is empty or not set, auth is disabled.
    """
    return os.environ.get("EURKAI_TOKEN") or None


async def verify_token(x_eurkai_token: Annotated[str | None, Header()] = None) -> bool:
    """
    Verify API token if configured.
    
    Rules (from C03 response):
    - Token stored in config locale
    - Header: X-EURKAI-TOKEN
    - Désactivable explicitement pour usage local/dev
    """
    expected_token = get_api_token()
    
    # Auth disabled
    if not expected_token:
        return True
    
    # Auth enabled but no token provided
    if not x_eurkai_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ERR_UNAUTHORIZED", "message": "Token required"}
        )
    
    # Token mismatch
    if not secrets.compare_digest(x_eurkai_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ERR_UNAUTHORIZED", "message": "Invalid token"}
        )
    
    return True


TokenDep = Annotated[bool, Depends(verify_token)]


# =============================================================================
# SECRETS ENCRYPTION (AES-256 via Fernet)
# =============================================================================

# In-memory session store for secrets unlock
_sessions: dict[str, float] = {}  # token -> expiry timestamp
SESSION_TTL = 300  # 5 minutes


def get_master_password() -> str | None:
    """Get master password from environment (for key derivation)."""
    return os.environ.get("EURKAI_MASTER_PASSWORD")


def derive_key(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """
    Derive encryption key from password using PBKDF2.
    
    Returns:
        (key, salt) tuple
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def encrypt_value(value: str, password: str) -> tuple[bytes, bytes]:
    """
    Encrypt a value with AES-256 (via Fernet).
    
    Returns:
        (encrypted_value, nonce) - nonce contains salt for key derivation
    """
    key, salt = derive_key(password)
    f = Fernet(key)
    encrypted = f.encrypt(value.encode())
    return encrypted, salt


def decrypt_value(encrypted: bytes, nonce: bytes, password: str) -> str:
    """Decrypt a value."""
    key, _ = derive_key(password, salt=nonce)
    f = Fernet(key)
    return f.decrypt(encrypted).decode()


def create_session_token() -> str:
    """Create a random session token."""
    return secrets.token_urlsafe(32)


def store_session(token: str) -> None:
    """Store session with TTL."""
    _sessions[token] = time.time() + SESSION_TTL
    # Cleanup expired
    now = time.time()
    expired = [t for t, exp in _sessions.items() if exp < now]
    for t in expired:
        del _sessions[t]


def verify_session(token: str) -> bool:
    """Verify session token is valid and not expired."""
    expiry = _sessions.get(token)
    if not expiry:
        return False
    if time.time() > expiry:
        del _sessions[token]
        return False
    return True


async def require_session(
    x_session_token: Annotated[str | None, Header()] = None
) -> bool:
    """Require valid session token for secret operations."""
    if not x_session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ERR_UNAUTHORIZED", "message": "Session token required. Use POST /api/secrets/unlock first."}
        )
    
    if not verify_session(x_session_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ERR_UNAUTHORIZED", "message": "Session expired or invalid"}
        )
    
    return True


SessionDep = Annotated[bool, Depends(require_session)]


# =============================================================================
# ERROR HELPERS
# =============================================================================

def not_found(resource: str = "Resource") -> HTTPException:
    """Create 404 error."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "ERR_NOT_FOUND", "message": f"{resource} not found"}
    )


def validation_error(message: str, details: dict | None = None) -> HTTPException:
    """Create 400 validation error."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": "ERR_VALIDATION", "message": message, "details": details}
    )


def conflict_error(message: str) -> HTTPException:
    """Create 409 conflict error."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": "ERR_CONFLICT", "message": message}
    )


# =============================================================================
# RESPONSE WRAPPER
# =============================================================================

def success_response(data: any) -> dict:
    """Wrap data in success response format (C01 Contract 4)."""
    return {
        "success": True,
        "data": data,
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0"
        }
    }
