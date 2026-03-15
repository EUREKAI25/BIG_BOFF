"""
palette_generator
──────────────────
Module EURKAI standalone de génération de palettes de couleurs.

Génère plusieurs variantes d'harmonie chromatique depuis une couleur de base :
monochromatic, analogous, complementary, split_complementary, triadic, tetradic,
+ black_and_white_variant, metal_variant, minimal, ui_safe (WCAG).

Entièrement algorithmique (stdlib Python) — aucune dépendance externe requise.
Pillow optionnel pour l'export PNG.

Usage rapide :
    from palette_generator import generate_palette
    from palette_generator.schemas import PaletteInput, PaletteScenario

    output = generate_palette(
        PaletteInput(
            base_color="#3B82F6",
            scenario=PaletteScenario.UI,
        ),
        output_dir="/tmp/palettes",
    )

Intégration FastAPI :
    from palette_generator.router import router as palette_router
    app.include_router(palette_router)
"""

from .schemas import (
    ColorValue,
    TonalScale,
    Palette,
    BWVariant,
    MetalPalette,
    PaletteSet,
    PaletteInput,
    PaletteOutput,
    BrandDNAInput,
    PaletteScenario,
    HarmonyType,
    MetalFinish,
    WCAGLevel,
    AccessibilityReport,
    ContrastCheck,
)
from .generator import generate_palette
from .color_utils import (
    hex_to_rgb, rgb_to_hex, hex_to_hsl, hsl_to_hex,
    contrast_ratio, make_color,
)

__version__ = "0.1.0"

__all__ = [
    # Schemas
    "ColorValue", "TonalScale", "Palette", "BWVariant", "MetalPalette",
    "PaletteSet", "PaletteInput", "PaletteOutput", "BrandDNAInput",
    "PaletteScenario", "HarmonyType", "MetalFinish", "WCAGLevel",
    "AccessibilityReport", "ContrastCheck",
    # Fonction principale
    "generate_palette",
    # Utils exposés
    "hex_to_rgb", "rgb_to_hex", "hex_to_hsl", "hsl_to_hex",
    "contrast_ratio", "make_color",
]
