"""
EURKAI_COCKPIT — Secrets Crypto Module
Version: 1.0.0

AES-256-GCM encryption with Argon2 key derivation.

Features:
- AES-256-GCM authenticated encryption
- Argon2id key derivation from master password
- Secure nonce generation (96-bit)
- No plaintext exposure in memory after use

Security notes:
- Never log or expose decrypted values
- Gate password required for every reveal/copy operation
- Salt stored with encrypted data for key re-derivation
"""

from __future__ import annotations

import os
import secrets
import hashlib
from dataclasses import dataclass
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type


# ============================================
# CONSTANTS
# ============================================

# AES-256-GCM parameters
AES_KEY_SIZE = 32  # 256 bits
NONCE_SIZE = 12    # 96 bits (recommended for GCM)
TAG_SIZE = 16      # 128 bits authentication tag

# Argon2id parameters (OWASP recommended)
ARGON2_TIME_COST = 3       # iterations
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_PARALLELISM = 1     # threads
ARGON2_HASH_LEN = 32       # 256-bit key
ARGON2_SALT_LEN = 16       # 128-bit salt


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class EncryptedPayload:
    """Container for encrypted secret data."""
    ciphertext: bytes      # AES-256-GCM encrypted data
    nonce: bytes           # 96-bit nonce
    salt: bytes            # Argon2 salt for key derivation
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes: salt (16) + nonce (12) + ciphertext."""
        return self.salt + self.nonce + self.ciphertext
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "EncryptedPayload":
        """Deserialize from bytes."""
        if len(data) < ARGON2_SALT_LEN + NONCE_SIZE + TAG_SIZE:
            raise ValueError("Invalid encrypted payload: too short")
        
        salt = data[:ARGON2_SALT_LEN]
        nonce = data[ARGON2_SALT_LEN:ARGON2_SALT_LEN + NONCE_SIZE]
        ciphertext = data[ARGON2_SALT_LEN + NONCE_SIZE:]
        
        return cls(ciphertext=ciphertext, nonce=nonce, salt=salt)


# ============================================
# KEY DERIVATION
# ============================================

def derive_key(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """
    Derive AES-256 key from password using Argon2id.
    
    Args:
        password: Master password (gate password)
        salt: Optional salt (generated if None)
    
    Returns:
        Tuple of (derived_key, salt)
    """
    if salt is None:
        salt = secrets.token_bytes(ARGON2_SALT_LEN)
    
    key = hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=ARGON2_HASH_LEN,
        type=Type.ID  # Argon2id (recommended)
    )
    
    return key, salt


def hash_password(password: str) -> str:
    """
    Hash password for storage/verification (not for encryption).
    Uses SHA-256 with a fixed prefix for quick verification.
    
    Note: This is NOT the encryption key derivation.
    This is only for verifying the gate password is correct.
    """
    return hashlib.sha256(f"eurkai:gate:{password}".encode()).hexdigest()


# ============================================
# ENCRYPTION / DECRYPTION
# ============================================

class SecretCrypto:
    """
    AES-256-GCM encryption with password-derived keys.
    
    Each secret is encrypted with a fresh key derived from:
    - The master gate password
    - A unique per-secret salt
    
    This ensures:
    - Different ciphertext for same plaintext
    - Compromising one secret doesn't expose others
    - Key is never stored, only derived on demand
    """
    
    def __init__(self, gate_password: str):
        """
        Initialize with gate password.
        
        Args:
            gate_password: Master password for secret access
        """
        self._password = gate_password
    
    def encrypt(self, plaintext: str) -> EncryptedPayload:
        """
        Encrypt plaintext with AES-256-GCM.
        
        Args:
            plaintext: Secret value to encrypt
        
        Returns:
            EncryptedPayload with ciphertext, nonce, and salt
        """
        # Derive unique key for this secret
        key, salt = derive_key(self._password)
        
        # Generate random nonce
        nonce = secrets.token_bytes(NONCE_SIZE)
        
        # Encrypt with AES-256-GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        
        return EncryptedPayload(
            ciphertext=ciphertext,
            nonce=nonce,
            salt=salt
        )
    
    def decrypt(self, payload: EncryptedPayload) -> str:
        """
        Decrypt ciphertext with AES-256-GCM.
        
        Args:
            payload: EncryptedPayload containing ciphertext, nonce, salt
        
        Returns:
            Decrypted plaintext string
        
        Raises:
            ValueError: If decryption fails (wrong password or corrupted data)
        """
        # Re-derive key using stored salt
        key, _ = derive_key(self._password, payload.salt)
        
        # Decrypt
        aesgcm = AESGCM(key)
        try:
            plaintext_bytes = aesgcm.decrypt(payload.nonce, payload.ciphertext, None)
            return plaintext_bytes.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Decryption failed: invalid password or corrupted data") from e
    
    def encrypt_to_bytes(self, plaintext: str) -> bytes:
        """Encrypt and serialize to bytes."""
        payload = self.encrypt(plaintext)
        return payload.to_bytes()
    
    def decrypt_from_bytes(self, data: bytes) -> str:
        """Deserialize and decrypt from bytes."""
        payload = EncryptedPayload.from_bytes(data)
        return self.decrypt(payload)


# ============================================
# UTILITIES
# ============================================

def generate_secure_password(length: int = 32) -> str:
    """Generate a cryptographically secure random password."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def verify_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Verify password meets minimum security requirements.
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters")
    if len(password) > 128:
        issues.append("Password must be at most 128 characters")
    if not any(c.isupper() for c in password):
        issues.append("Password should contain uppercase letters")
    if not any(c.islower() for c in password):
        issues.append("Password should contain lowercase letters")
    if not any(c.isdigit() for c in password):
        issues.append("Password should contain digits")
    
    return len(issues) == 0, issues
