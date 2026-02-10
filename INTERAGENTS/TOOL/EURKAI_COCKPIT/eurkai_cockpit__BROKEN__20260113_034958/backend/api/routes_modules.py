"""
EURKAI_COCKPIT — Modules API Routes
Version: 1.0.0

Module registry following C01 MANIFESTS.md.
No entry_point in v1 — backend doesn't execute modules.
"""

from typing import Optional

from fastapi import APIRouter, Query, status

from ..models import ModuleManifestCreate, ModuleManifestOut, CompatibilityResult
from .deps import StorageDep, TokenDep, success_response, not_found, validation_error, conflict_error

router = APIRouter(prefix="/api/modules", tags=["modules"])


def parse_semver(version: str) -> tuple[int, int, int]:
    """Parse semver string to tuple for comparison."""
    parts = version.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def check_compatibility(module_a: dict, module_b: dict) -> dict:
    """
    Vérifie si les outputs de A peuvent alimenter les inputs de B.
    
    From C01 MANIFESTS.md — Algorithm section.
    """
    mappings = []
    
    for output in module_a.get("outputs", []):
        for input_ in module_b.get("inputs", []):
            if output["type"] == input_["type"]:
                mappings.append({
                    "from": f"{module_a['name']}.{output['name']}",
                    "to": f"{module_b['name']}.{input_['name']}",
                    "type": output["type"]
                })
    
    # Vérifier que tous les inputs required de B sont satisfaits
    required_inputs = [i for i in module_b.get("inputs", []) if i.get("required", True)]
    satisfied = set()
    
    for m in mappings:
        input_name = m["to"].split(".")[1]
        satisfied.add(input_name)
    
    missing = [i["name"] for i in required_inputs if i["name"] not in satisfied]
    
    result = {
        "compatible": len(missing) == 0,
        "mappings": mappings,
        "missing_required": missing
    }
    
    # Add suggestion if not compatible
    if missing:
        result["suggestion"] = (
            f"{module_a['name']} outputs cannot satisfy {module_b['name']} "
            f"required inputs: {', '.join(missing)}"
        )
    
    return result


@router.get("")
async def list_modules(storage: StorageDep, _: TokenDep):
    """GET /api/modules — Liste manifests."""
    modules = storage.list_modules()
    return success_response(modules)


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_module(data: ModuleManifestCreate, storage: StorageDep, _: TokenDep):
    """
    POST /api/modules — Enregistrer manifest.
    
    Rules:
    - Same name + same version = REJECT (conflict)
    - Same name + higher version = UPDATE
    """
    existing = storage.get_module_by_name(data.name)
    
    if existing:
        existing_ver = parse_semver(existing["version"])
        new_ver = parse_semver(data.version)
        
        if new_ver == existing_ver:
            raise conflict_error(
                f"Module {data.name} version {data.version} already exists"
            )
        
        if new_ver <= existing_ver:
            raise validation_error(
                f"Version must be greater than existing ({existing['version']})"
            )
        
        # Update existing module
        inputs = [i.model_dump() for i in data.inputs]
        outputs = [o.model_dump() for o in data.outputs]
        constraints = data.constraints.model_dump() if data.constraints else None
        
        module = storage.update_module(
            existing["id"],
            version=data.version,
            description=data.description,
            inputs=inputs,
            outputs=outputs,
            constraints=constraints,
            tags=data.tags
        )
        return success_response(module)
    
    # Create new module
    inputs = [i.model_dump() for i in data.inputs]
    outputs = [o.model_dump() for o in data.outputs]
    constraints = data.constraints.model_dump() if data.constraints else None
    
    module = storage.create_module(
        name=data.name,
        version=data.version,
        description=data.description,
        inputs=inputs,
        outputs=outputs,
        constraints=constraints,
        tags=data.tags
    )
    return success_response(module)


@router.get("/compatible")
async def check_module_compatibility(
    storage: StorageDep,
    _: TokenDep,
    from_module: str = Query(..., alias="from", description="Source module name"),
    to_module: str = Query(..., alias="to", description="Target module name")
):
    """
    GET /api/modules/compatible?from=A&to=B — Vérifier compatibilité i/o.
    """
    module_a = storage.get_module_by_name(from_module)
    if not module_a:
        raise not_found(f"Module '{from_module}'")
    
    module_b = storage.get_module_by_name(to_module)
    if not module_b:
        raise not_found(f"Module '{to_module}'")
    
    result = check_compatibility(module_a, module_b)
    return success_response(result)


@router.get("/{module_id}")
async def get_module(module_id: str, storage: StorageDep, _: TokenDep):
    """GET /api/modules/{id} — Détail manifest."""
    module = storage.get_module(module_id)
    if not module:
        raise not_found("Module")
    return success_response(module)


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(module_id: str, storage: StorageDep, _: TokenDep):
    """DELETE /api/modules/{id} — Retirer du registry."""
    existing = storage.get_module(module_id)
    if not existing:
        raise not_found("Module")
    
    storage.delete_module(module_id)
    return None
