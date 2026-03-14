"""
Router FastAPI — POST /v1/pipeline/prevalidate

Montage dans l'app principale :
    from pipeline_validator.router import router as pipeline_router
    app.include_router(pipeline_router, prefix="/v1")
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from .contracts import ContractRegistry
from .validator import PipelineValidator, PipelineValidationResult

router   = APIRouter(tags=["pipeline"])
registry = ContractRegistry()
validator = PipelineValidator(registry)


# ---------------------------------------------------------------------------
# Schémas de requête
# ---------------------------------------------------------------------------

class PipelineStep(BaseModel):
    module: str

class PrevalidateRequest(BaseModel):
    """
    Deux formats acceptés :

    Format simple :
        { "modules": ["extract_brand_dna", "generate_theme", "render_css_bundle"] }

    Format enrichi :
        { "pipeline": [{"module": "extract_brand_dna"}, ...] }

    Si les deux sont fournis, pipeline a priorité.
    """
    modules:  Optional[List[str]]       = None
    pipeline: Optional[List[PipelineStep]] = None

    @field_validator("modules", "pipeline", mode="before")
    @classmethod
    def at_least_one(cls, v):
        return v

    def resolved_modules(self) -> List[str]:
        if self.pipeline:
            return [step.module for step in self.pipeline]
        if self.modules:
            return self.modules
        return []


# ---------------------------------------------------------------------------
# Schémas de réponse
# ---------------------------------------------------------------------------

class TransitionOut(BaseModel):
    from_module:  str
    to_module:    str
    shared_datas: List[str]

class BreakOut(BaseModel):
    break_index:     int
    from_module:     str
    to_module:       str
    outputs:         List[str]
    expected_inputs: List[str]
    shared_datas:    List[str]
    suggestions:     List[str]  # modules directs compatibles depuis from_module
    bridges:         List[str]  # modules pouvant s'insérer entre les deux

class ReportOut(BaseModel):
    modules:          List[str]
    data_types_used:  List[str]
    has_sink:         bool
    terminal_outputs: List[str]

class PrevalidateResponse(BaseModel):
    valid:       bool
    transitions: List[TransitionOut]         = []
    error:       Optional[str]               = None
    break_info:  Optional[BreakOut]          = None
    report:      Optional[ReportOut]         = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/pipeline/prevalidate",
    response_model=PrevalidateResponse,
    summary="Prévalider un pipeline de modules",
    description=(
        "Vérifie si une séquence de modules peut être chaînée. "
        "Règle : outputs(A) ∩ inputs(B) ≠ ∅ pour chaque transition. "
        "**Temporaire MVP** — sera remplacé par les SuperTools."
    ),
)
def prevalidate_pipeline(body: PrevalidateRequest) -> PrevalidateResponse:

    module_ids = body.resolved_modules()

    if not module_ids:
        return PrevalidateResponse(valid=False, error="empty_pipeline")

    result: PipelineValidationResult = validator.validate(module_ids)

    return PrevalidateResponse(
        valid       = result.valid,
        transitions = [
            TransitionOut(
                from_module  = t.from_module,
                to_module    = t.to_module,
                shared_datas = t.shared_datas,
            )
            for t in result.transitions
        ],
        error      = result.error,
        break_info = BreakOut(**vars(result.break_info)) if result.break_info else None,
        report     = ReportOut(**vars(result.report))    if result.report    else None,
    )


# ---------------------------------------------------------------------------
# Endpoint bonus — catalogue des contrats connus
# ---------------------------------------------------------------------------

@router.get(
    "/pipeline/contracts",
    summary="Lister tous les contrats de modules connus",
)
def list_contracts():
    return {
        mid: {
            "input_datas":  c.input_datas,
            "output_datas": c.output_datas,
            "description":  c.description,
        }
        for mid, c in registry._cache.items()
    }


@router.get(
    "/pipeline/contracts/{module_id}/next",
    summary="Modules compatibles après module_id",
)
def compatible_next(module_id: str):
    try:
        return {"module_id": module_id, "compatible_next": registry.compatible_next(module_id)}
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(404, f"Module inconnu : {module_id}")


@router.get(
    "/pipeline/contracts/{module_id}/prev",
    summary="Modules compatibles avant module_id",
)
def compatible_prev(module_id: str):
    try:
        return {"module_id": module_id, "compatible_prev": registry.compatible_prev(module_id)}
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(404, f"Module inconnu : {module_id}")
