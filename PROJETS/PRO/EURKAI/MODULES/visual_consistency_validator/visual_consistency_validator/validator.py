"""
visual_consistency_validator.validator
───────────────────────────────────────
Orchestrateur principal.

validate(input_data) → ValidationReport

Pipeline :
  ValidationInput
    → palette_checker    (si asset.palette fourni)
    → typography_checker (si asset.typography fourni)
    → icon_style_checker (si asset.icons fourni)
    → visual_style_checker (si asset.visuals fourni)
    → layout_checker     (si asset.ui_theme fourni)
    → scoring_engine     → ValidationReport
"""

from __future__ import annotations
from typing import List

from .schemas import ValidationInput, ValidationReport, CheckResult
from .palette_checker     import check_palette
from .typography_checker  import check_typography
from .icon_style_checker  import check_icon_style
from .visual_style_checker import check_visual_style
from .layout_checker      import check_layout
from .scoring_engine      import compute_report


def validate(input_data: ValidationInput, threshold: float = 0.80) -> ValidationReport:
    """
    Valide tous les assets fournis contre le DesignDNA.

    Les checkers ne sont exécutés que si l'asset correspondant est présent.
    """
    dna    = input_data.design_dna or {}
    checks: List[CheckResult] = []

    if input_data.palette is not None:
        checks.append(check_palette(input_data.palette, dna))

    if input_data.typography is not None:
        checks.append(check_typography(input_data.typography, dna))

    if input_data.icons is not None:
        checks.append(check_icon_style(input_data.icons, dna))

    if input_data.visuals is not None:
        checks.append(check_visual_style(input_data.visuals, dna))

    if input_data.ui_theme is not None:
        checks.append(check_layout(input_data.ui_theme, dna))

    return compute_report(checks, threshold=threshold)
