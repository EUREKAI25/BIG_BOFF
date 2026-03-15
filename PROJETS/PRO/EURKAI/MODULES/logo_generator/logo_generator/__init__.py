"""
logo_generator
──────────────
Module EURKAI de génération de logos vectoriels via Recraft v3.

Pipeline :
  LogoDNA → generate_concepts (×N) → select_concept (none/ai/human)
          → export_variants (×5 SVG) → LogoOutput

Usage rapide :
    from logo_generator import generate_concepts, select_concept, export_variants
    from logo_generator.schemas import LogoDNA, LogoType, ArbitrationConfig

Intégration FastAPI :
    from logo_generator.router import router as logo_router
    app.include_router(logo_router)
"""

from .schemas import (
    BrandDNA,
    LogoDNA,
    LogoType,
    LogoStructure,
    ArbitrationConfig,
    ArbitrationMode,
    BackgroundMode,
    LogoConcept,
    LogoVariant,
    LogoVariantSet,
    LogoOutput,
)
from .generator import generate_concepts
from .arbitration import select_concept
from .exporter import export_variants
from .vector_optimizer import optimize_svg

__version__ = "0.1.0"

__all__ = [
    # Schemas
    "BrandDNA",
    "LogoDNA",
    "LogoType",
    "LogoStructure",
    "ArbitrationConfig",
    "ArbitrationMode",
    "BackgroundMode",
    "LogoConcept",
    "LogoVariant",
    "LogoVariantSet",
    "LogoOutput",
    # Fonctions principales
    "generate_concepts",
    "select_concept",
    "export_variants",
    "optimize_svg",
]
