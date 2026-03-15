"""
palette_generator.generator
─────────────────────────────
Orchestrateur principal. Assemble tous les sous-modules.

Pipeline :
  PaletteInput
    → resolve base_hex (depuis base_color | base_colors | brand_dna.palette)
    → ScenarioConfig (quelles harmonies, BW, metal, WCAG)
    → harmony_engine → Palette par harmonie
    → color_scale_generator → TonalScale pour primary
    → bw_palette_generator → BWVariant
    → metal_palette_generator → MetalPalette
    → contrast_validator → AccessibilityReport + ui_safe
    → PaletteSet
    → palette_exporter (optionnel)
    → PaletteOutput
"""

from __future__ import annotations
import time
from typing import Optional

from .schemas import PaletteInput, PaletteOutput, PaletteSet, PaletteScenario
from .color_utils import normalize_hex
from .harmony_engine import generate_all_harmonies, minimal
from .color_scale_generator import generate_scale
from .bw_palette_generator import generate_bw_variant
from .metal_palette_generator import generate_metal_palette, auto_detect_finish
from .contrast_validator import validate_palette, generate_ui_safe
from .palette_scenarios import get_config


def _resolve_base_hex(input_data: PaletteInput) -> str:
    """Détermine la couleur de base depuis les différents types d'input."""
    if input_data.base_color:
        return normalize_hex(input_data.base_color)
    if input_data.base_colors:
        return normalize_hex(input_data.base_colors[0])
    if input_data.brand_dna and input_data.brand_dna.palette:
        return normalize_hex(input_data.brand_dna.palette[0])
    raise ValueError(
        "Aucune couleur de base fournie. "
        "Renseigner base_color, base_colors, ou brand_dna.palette."
    )


def generate_palette(
    input_data: PaletteInput,
    output_dir: Optional[str] = None,
    export_formats: list[str] = None,
) -> PaletteOutput:
    """
    Génère la PaletteSet complète selon le scénario.

    Args:
        input_data:      PaletteInput (couleur de base + scénario + options)
        output_dir:      Si fourni, exporte les fichiers dans ce répertoire
        export_formats:  Liste de formats à exporter ("json", "tokens", "svg", "png")
                         Défaut : tous si output_dir fourni

    Returns:
        PaletteOutput avec palette_set + export_paths + trace
    """
    t0 = time.time()

    base_hex = _resolve_base_hex(input_data)
    config = get_config(input_data.scenario)

    # Génération de toutes les harmonies
    all_harmonies = generate_all_harmonies(base_hex)

    # Assemblage du PaletteSet
    palette_set = PaletteSet(
        base_hex=base_hex,
        scenario=input_data.scenario,
    )

    # Harmonies selon scénario
    for harmony_type in config.harmonies:
        palette = all_harmonies.get(harmony_type.value)
        if palette:
            # Générer la scale tonale pour la couleur primaire
            if palette.primary:
                scale = generate_scale(palette.primary[0].hex, name="primary")
                palette.tonal_scales = [scale]
            setattr(palette_set, harmony_type.value, palette)

    # Minimal
    if config.generate_minimal:
        min_palette = minimal(base_hex)
        palette_set.minimal = min_palette

    # Black & White
    if config.generate_bw:
        palette_set.black_and_white_variant = generate_bw_variant(base_hex)

    # Metal
    if config.generate_metal:
        finish = input_data.metal_finish or auto_detect_finish(base_hex)
        palette_set.metal_variant = generate_metal_palette(base_hex, finish)

    # WCAG + ui_safe
    ref_palette = (
        palette_set.monochromatic
        or palette_set.complementary
        or palette_set.analogous
        or palette_set.minimal
    )
    if ref_palette and config.validate_wcag:
        palette_set.accessibility_report = validate_palette(ref_palette, config.wcag_level)

    if ref_palette and config.generate_ui_safe:
        palette_set.ui_safe = generate_ui_safe(ref_palette, config.wcag_level)

    elapsed = round(time.time() - t0, 2)

    # Export fichiers si output_dir fourni
    export_paths = {}
    if output_dir:
        from .palette_exporter import export_all
        export_paths = export_all(palette_set, output_dir)

    trace = {
        "base_hex": base_hex,
        "scenario": input_data.scenario.value,
        "harmonies_generated": [h.value for h in config.harmonies],
        "bw_generated": config.generate_bw,
        "metal_generated": config.generate_metal,
        "wcag_validated": config.validate_wcag,
        "ui_safe_generated": config.generate_ui_safe,
        "elapsed_seconds": elapsed,
    }

    return PaletteOutput(
        palette_set=palette_set,
        export_paths=export_paths,
        trace=trace,
    )
