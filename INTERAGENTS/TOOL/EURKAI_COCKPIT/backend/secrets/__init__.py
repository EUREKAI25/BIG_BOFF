"""
EURKAI_COCKPIT — Secrets Module
Version: 1.0.0

Secure secrets management with:
- AES-256-GCM encryption
- Argon2id key derivation
- Copy-gated access (password required for reveal)
- Comprehensive audit logging

Public API:
-----------
- SecretsService: Main service class
- SecretMetadata: Secret info without value
- SecretLogEntry: Audit log entry
- RevealResult: Result of reveal/copy operations
- SecretCrypto: Low-level encryption (advanced use)

Usage:
------
    from backend.secrets import SecretsService
    
    # Initialize with storage
    service = SecretsService(storage)
    
    # Set up gate password (once)
    service.initialize_gate_password("my-secure-password")
    
    # Create secret
    meta, msg = service.create_secret(
        key="API_KEY",
        plaintext="sk-xxx",
        gate_password="my-secure-password",
        source="cli"
    )
    
    # List (never shows values)
    secrets = service.list_secrets()
    
    # Reveal (requires password)
    result = service.reveal_secret(meta.id, "my-secure-password")
    if result.success:
        print(result.value)

Security Notes:
---------------
1. Gate password is NEVER stored (only hash for verification)
2. Each secret has unique encryption salt
3. List endpoint NEVER returns plaintext values
4. All access is logged with timestamp, action, result
5. Failed password attempts are logged
"""

from .crypto import (
    SecretCrypto,
    EncryptedPayload,
    derive_key,
    hash_password,
    verify_password_strength,
    generate_secure_password,
    # Constants
    AES_KEY_SIZE,
    NONCE_SIZE,
    ARGON2_TIME_COST,
    ARGON2_MEMORY_COST,
)

from .service import (
    SecretsService,
    SecretMetadata,
    SecretLogEntry,
    RevealResult,
    SecretScope,
    SecretAction,
    SecretSource,
    ActionResult,
    GATE_PASSWORD_CONFIG_KEY,
)

__version__ = "1.0.0"

__all__ = [
    # Main service
    "SecretsService",
    
    # Data types
    "SecretMetadata",
    "SecretLogEntry",
    "RevealResult",
    
    # Enums
    "SecretScope",
    "SecretAction",
    "SecretSource",
    "ActionResult",
    
    # Crypto (advanced)
    "SecretCrypto",
    "EncryptedPayload",
    "derive_key",
    "hash_password",
    "verify_password_strength",
    "generate_secure_password",
    
    # Constants
    "GATE_PASSWORD_CONFIG_KEY",
    "AES_KEY_SIZE",
    "NONCE_SIZE",
    "ARGON2_TIME_COST",
    "ARGON2_MEMORY_COST",
    
    # Version
    "__version__",
]
