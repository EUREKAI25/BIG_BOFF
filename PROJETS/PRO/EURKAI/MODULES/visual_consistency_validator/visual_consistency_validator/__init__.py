"""
visual_consistency_validator
────────────────────────────
Module EURKAI standalone — valide la cohérence de tous les assets visuels
générés (logo, palette, typo, icônes, UI, visuals) contre un DesignDNA.

Zero LLM. Sortie déterministe.

Pipeline :
  ValidationInput (DesignDNA + assets) → [checkers] → ValidationReport

Usage :
    from visual_consistency_validator import validate

    from visual_consistency_validator.schemas import (
        ValidationInput, PaletteAsset, TypographyAsset
    )

    report = validate(ValidationInput(
        design_dna={"style_archetype": "startup_clean", "typography_style": "geometric_sans", ...},
        palette=PaletteAsset(primary_colors=["#1a53ff", "#001f5c"], saturation_level="medium"),
        typography=TypographyAsset(style="geometric_sans", weight_hint="medium"),
    ))

    print(report.status)        # "valid"
    print(report.overall_score) # 0.94
    print(report.warnings)      # []
"""

from .schemas import (
    ValidationInput, ValidationReport, CheckResult,
    LogoAsset, PaletteAsset, TypographyAsset,
    IconAsset, UIThemeAsset, VisualAsset,
)
from .validator import validate

__version__ = "0.1.0"

__all__ = [
    "validate",
    "ValidationInput",
    "ValidationReport",
    "CheckResult",
    "LogoAsset",
    "PaletteAsset",
    "TypographyAsset",
    "IconAsset",
    "UIThemeAsset",
    "VisualAsset",
]
