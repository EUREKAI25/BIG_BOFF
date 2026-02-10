"""
EURKAI_COCKPIT — Projects API Routes
Version: 1.0.0
"""

from fastapi import APIRouter, status

from ..models import ProjectCreate, ProjectUpdate, ProjectOut
from .deps import StorageDep, TokenDep, success_response, not_found

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
async def list_projects(storage: StorageDep, _: TokenDep):
    """GET /api/projects — Liste tous les projets."""
    projects = storage.list_projects()
    return success_response(projects)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, storage: StorageDep, _: TokenDep):
    """POST /api/projects — Créer un projet."""
    project = storage.create_project(
        name=data.name,
        description=data.description
    )
    return success_response(project)


@router.get("/{project_id}")
async def get_project(project_id: str, storage: StorageDep, _: TokenDep):
    """GET /api/projects/{id} — Détail projet."""
    project = storage.get_project(project_id)
    if not project:
        raise not_found("Project")
    return success_response(project)


@router.put("/{project_id}")
async def update_project(
    project_id: str, 
    data: ProjectUpdate, 
    storage: StorageDep, 
    _: TokenDep
):
    """PUT /api/projects/{id} — Modifier projet."""
    existing = storage.get_project(project_id)
    if not existing:
        raise not_found("Project")
    
    project = storage.update_project(
        project_id,
        name=data.name,
        description=data.description
    )
    return success_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, storage: StorageDep, _: TokenDep):
    """DELETE /api/projects/{id} — Supprimer (cascade briefs)."""
    existing = storage.get_project(project_id)
    if not existing:
        raise not_found("Project")
    
    storage.delete_project(project_id)
    return None
