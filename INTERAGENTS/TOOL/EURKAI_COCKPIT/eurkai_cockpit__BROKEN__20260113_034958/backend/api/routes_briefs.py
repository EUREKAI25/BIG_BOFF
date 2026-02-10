"""
EURKAI_COCKPIT — Briefs API Routes
Version: 1.0.0
"""

from typing import Optional

from fastapi import APIRouter, Query, status

from ..models import BriefCreate, BriefUpdate, BriefOut, RunOut
from .deps import StorageDep, TokenDep, success_response, not_found, validation_error

router = APIRouter(prefix="/api/briefs", tags=["briefs"])


@router.get("")
async def list_briefs(
    storage: StorageDep, 
    _: TokenDep,
    project_id: Optional[str] = Query(None, description="Filter by project")
):
    """GET /api/briefs — Liste (filtre ?project_id=)."""
    briefs = storage.list_briefs(project_id=project_id)
    return success_response(briefs)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_brief(data: BriefCreate, storage: StorageDep, _: TokenDep):
    """POST /api/briefs — Créer brief (project_id requis)."""
    # Verify project exists
    project = storage.get_project(data.project_id)
    if not project:
        raise validation_error(
            "Invalid project_id",
            {"project_id": "Project does not exist"}
        )
    
    policy_dict = None
    if data.policy:
        policy_dict = data.policy.model_dump()
    
    brief = storage.create_brief(
        project_id=data.project_id,
        title=data.title,
        user_prompt=data.user_prompt,
        goal=data.goal,
        system_prompt=data.system_prompt,
        variables=data.variables,
        expected_output=data.expected_output,
        tags=data.tags,
        policy=policy_dict
    )
    return success_response(brief)


@router.get("/{brief_id}")
async def get_brief(brief_id: str, storage: StorageDep, _: TokenDep):
    """GET /api/briefs/{id} — Détail brief."""
    brief = storage.get_brief(brief_id)
    if not brief:
        raise not_found("Brief")
    return success_response(brief)


@router.put("/{brief_id}")
async def update_brief(
    brief_id: str, 
    data: BriefUpdate, 
    storage: StorageDep, 
    _: TokenDep
):
    """PUT /api/briefs/{id} — Modifier brief."""
    existing = storage.get_brief(brief_id)
    if not existing:
        raise not_found("Brief")
    
    update_data = data.model_dump(exclude_unset=True)
    if "policy" in update_data and update_data["policy"]:
        update_data["policy"] = data.policy.model_dump()
    
    brief = storage.update_brief(brief_id, **update_data)
    return success_response(brief)


@router.delete("/{brief_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brief(brief_id: str, storage: StorageDep, _: TokenDep):
    """DELETE /api/briefs/{id} — Supprimer brief."""
    existing = storage.get_brief(brief_id)
    if not existing:
        raise not_found("Brief")
    
    storage.delete_brief(brief_id)
    return None


@router.post("/{brief_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def trigger_run(brief_id: str, storage: StorageDep, _: TokenDep):
    """POST /api/briefs/{id}/run — Lancer un run."""
    brief = storage.get_brief(brief_id)
    if not brief:
        raise not_found("Brief")
    
    # Create pending run
    run = storage.create_run(brief_id=brief_id)
    
    return success_response({"run_id": run["id"], "status": "pending"})


@router.get("/{brief_id}/runs")
async def list_runs(brief_id: str, storage: StorageDep, _: TokenDep):
    """GET /api/briefs/{id}/runs — Historique runs du brief."""
    brief = storage.get_brief(brief_id)
    if not brief:
        raise not_found("Brief")
    
    runs = storage.list_runs(brief_id)
    return success_response(runs)
