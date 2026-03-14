"""
pipeline_validator — prévalidation externe de pipelines de modules EURKAI.

Usage minimal :
    from pipeline_validator.contracts import ContractRegistry
    from pipeline_validator.validator import PipelineValidator

    registry  = ContractRegistry()
    validator = PipelineValidator(registry)
    result    = validator.validate(["extract_brand_dna", "generate_theme", "render_css_bundle"])

Montage FastAPI :
    from pipeline_validator.router import router as pipeline_router
    app.include_router(pipeline_router, prefix="/v1")

Temporaire MVP — sera remplacé par les SuperTools.
"""
from .contracts import ContractRegistry, ModuleContract
from .validator import PipelineValidator, PipelineValidationResult

__all__ = [
    "ContractRegistry",
    "ModuleContract",
    "PipelineValidator",
    "PipelineValidationResult",
]
