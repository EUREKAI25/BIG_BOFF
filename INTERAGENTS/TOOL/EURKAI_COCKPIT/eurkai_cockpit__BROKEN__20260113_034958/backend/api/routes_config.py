"""
EURKAI_COCKPIT — Config API Routes
Version: 1.0.0
"""

from fastapi import APIRouter

from ..models import ConfigUpdate
from .deps import StorageDep, TokenDep, success_response

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
async def list_config(storage: StorageDep, _: TokenDep):
    """GET /api/config — Liste config."""
    config = storage.list_config()
    return success_response(config)


@router.put("/{key}")
async def update_config(key: str, data: ConfigUpdate, storage: StorageDep, _: TokenDep):
    """PUT /api/config/{key} — Modifier valeur (upsert)."""
    config = storage.set_config(key, data.value)
    return success_response(config)
