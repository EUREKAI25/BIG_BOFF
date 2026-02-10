"""
EURKAI_COCKPIT — Runs API Routes
Version: 1.0.0
"""

from fastapi import APIRouter, status

from .deps import StorageDep, TokenDep, success_response, not_found

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/{run_id}")
async def get_run(run_id: str, storage: StorageDep, _: TokenDep):
    """GET /api/runs/{id} — Détail run."""
    run = storage.get_run(run_id)
    if not run:
        raise not_found("Run")
    return success_response(run)


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_run(run_id: str, storage: StorageDep, _: TokenDep):
    """DELETE /api/runs/{id} — Supprimer run."""
    existing = storage.get_run(run_id)
    if not existing:
        raise not_found("Run")
    
    storage.delete_run(run_id)
    return None
