"""
EURKAI_COCKPIT — Secrets API Routes
Version: 1.0.0

Secrets flow (C01 SPEC_V1):
1. POST /secrets/unlock {master_password} → session_token
2. GET /secrets/{id}/copy with X-Session-Token header → decrypted value
"""

import os
from typing import Optional

from fastapi import APIRouter, Query, status

from ..models import (
    SecretCreate, SecretUpdate, SecretOut,
    SecretUnlock, SecretUnlockResponse, SecretCopyResponse
)
from .deps import (
    StorageDep, TokenDep, SessionDep,
    success_response, not_found, validation_error,
    get_master_password, encrypt_value, decrypt_value,
    create_session_token, store_session, SESSION_TTL
)

router = APIRouter(prefix="/api/secrets", tags=["secrets"])


@router.get("")
async def list_secrets(
    storage: StorageDep, 
    _: TokenDep,
    project_id: Optional[str] = Query(None, description="Filter by project")
):
    """
    GET /api/secrets — Liste (clés seulement, jamais valeurs).
    """
    secrets = storage.list_secrets(project_id=project_id)
    return success_response(secrets)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_secret(data: SecretCreate, storage: StorageDep, _: TokenDep):
    """
    POST /api/secrets — Créer secret.
    Value is encrypted before storage.
    """
    master_pwd = get_master_password()
    if not master_pwd:
        raise validation_error(
            "Master password not configured",
            {"hint": "Set EURKAI_MASTER_PASSWORD environment variable"}
        )
    
    # Check for duplicate key
    existing = storage.get_secret_by_key(data.key, data.project_id)
    if existing:
        raise validation_error(
            "Secret key already exists",
            {"key": data.key, "project_id": data.project_id}
        )
    
    # Encrypt value
    encrypted, nonce = encrypt_value(data.value, master_pwd)
    
    secret = storage.create_secret(
        key=data.key,
        value_encrypted=encrypted,
        nonce=nonce,
        project_id=data.project_id
    )
    
    # Return without encrypted fields
    return success_response({
        "id": secret["id"],
        "key": secret["key"],
        "project_id": secret["project_id"],
        "created_at": secret["created_at"],
        "updated_at": secret["updated_at"]
    })


@router.post("/unlock")
async def unlock_secrets(data: SecretUnlock, _: TokenDep):
    """
    POST /api/secrets/unlock — Déverrouiller session (mdp master).
    Returns session_token valid for TTL seconds.
    """
    master_pwd = get_master_password()
    if not master_pwd:
        raise validation_error(
            "Master password not configured",
            {"hint": "Set EURKAI_MASTER_PASSWORD environment variable"}
        )
    
    # Verify password matches
    if data.master_password != master_pwd:
        raise validation_error("Invalid master password")
    
    # Create session
    token = create_session_token()
    store_session(token)
    
    return success_response({
        "session_token": token,
        "ttl": SESSION_TTL
    })


@router.get("/{secret_id}/copy")
async def copy_secret(
    secret_id: str, 
    storage: StorageDep, 
    _: TokenDep,
    __: SessionDep  # Requires valid session
):
    """
    GET /api/secrets/{id}/copy — Copier valeur (gate mdp requis).
    Requires X-Session-Token header from unlock.
    """
    secret = storage.get_secret(secret_id)
    if not secret:
        raise not_found("Secret")
    
    master_pwd = get_master_password()
    if not master_pwd:
        raise validation_error("Master password not configured")
    
    # Decrypt value
    try:
        decrypted = decrypt_value(
            secret["value_encrypted"],
            secret["nonce"],
            master_pwd
        )
    except Exception as e:
        raise validation_error(f"Decryption failed: {str(e)}")
    
    return success_response({"value": decrypted})


@router.put("/{secret_id}")
async def update_secret(
    secret_id: str, 
    data: SecretUpdate, 
    storage: StorageDep, 
    _: TokenDep
):
    """PUT /api/secrets/{id} — Modifier secret."""
    existing = storage.get_secret(secret_id)
    if not existing:
        raise not_found("Secret")
    
    master_pwd = get_master_password()
    if not master_pwd:
        raise validation_error("Master password not configured")
    
    # Encrypt new value
    encrypted, nonce = encrypt_value(data.value, master_pwd)
    
    secret = storage.update_secret(
        secret_id,
        value_encrypted=encrypted,
        nonce=nonce
    )
    
    # Return without encrypted fields
    return success_response({
        "id": secret["id"],
        "key": secret["key"],
        "project_id": secret["project_id"],
        "created_at": secret["created_at"],
        "updated_at": secret["updated_at"]
    })


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(secret_id: str, storage: StorageDep, _: TokenDep):
    """DELETE /api/secrets/{id} — Supprimer secret."""
    existing = storage.get_secret(secret_id)
    if not existing:
        raise not_found("Secret")
    
    storage.delete_secret(secret_id)
    return None
