"""
brand_generator
────────────────
Module EURKAI de génération de directions créatives de marque.

Génère 3 BrandDirection cohérentes et distinctes à partir d'un brief + BrandDNA.
Chaque direction est consommable directement par :
  logo_generator, font_generator, icon_font_generator,
  palette_generator, webdesign_generator, image_generator

Usage rapide :
    from brand_generator import generate_brand_directions
    from brand_generator.schemas import BrandGeneratorInput, BrandDNA

Intégration FastAPI :
    from brand_generator.router import router as brand_router
    app.include_router(brand_router)
"""

from .schemas import (
    BrandDNA,
    PaletteProfile,
    TypographyProfile,
    BrandDirection,
    BrandGeneratorInput,
    BrandGeneratorOutput,
)
from .generator import generate_brand_directions

__version__ = "0.1.0"

__all__ = [
    "BrandDNA",
    "PaletteProfile",
    "TypographyProfile",
    "BrandDirection",
    "BrandGeneratorInput",
    "BrandGeneratorOutput",
    "generate_brand_directions",
]
