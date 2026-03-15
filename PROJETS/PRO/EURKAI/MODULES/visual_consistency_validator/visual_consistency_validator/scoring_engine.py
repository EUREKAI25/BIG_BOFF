"""
visual_consistency_validator.scoring_engine
────────────────────────────────────────────
Agrège les scores des checkers individuels en un score global.

Pondération par défaut :
  palette      → 25 %
  typography   → 20 %
  icon_style   → 20 %
  visual_style → 20 %
  layout       → 15 %

Seuls les checkers exécutés (assets fournis) entrent dans le calcul.
"""

from __future__ import annotations
from typing import Dict, List, Optional

from .schemas import CheckResult, ValidationReport

# Pondérations par checker
_DEFAULT_WEIGHTS: Dict[str, float] = {
    "palette":      0.25,
    "typography":   0.20,
    "icon_style":   0.20,
    "visual_style": 0.20,
    "layout":       0.15,
}

# Seuils de statut
_THRESHOLD_VALID    = 0.80
_THRESHOLD_REVISION = 0.60


def compute_report(
    checks: List[CheckResult],
    threshold: float = _THRESHOLD_VALID,
) -> ValidationReport:
    """
    Calcule le ValidationReport final à partir des CheckResults.

    - Score global : moyenne pondérée des checkers exécutés,
      poids renormalisés à 1.0 sur les seuls checkers présents.
    - Statut : "valid" / "needs_revision" / "rejected"
    """
    if not checks:
        return ValidationReport(
            status="valid",
            overall_score=1.0,
            threshold=threshold,
        )

    # Scores individuels
    scores_by_checker: Dict[str, float] = {c.checker: c.score for c in checks}

    # Renormalisation des poids (seuls les checkers présents comptent)
    present = [k for k in _DEFAULT_WEIGHTS if k in scores_by_checker]
    raw_sum = sum(_DEFAULT_WEIGHTS[k] for k in present)
    if raw_sum == 0:
        raw_sum = 1.0

    weighted_sum = sum(
        _DEFAULT_WEIGHTS[k] * scores_by_checker[k]
        for k in present
    )
    overall = weighted_sum / raw_sum

    # Collecte warnings + suggestions
    all_warnings:    List[str] = []
    all_suggestions: List[str] = []
    for c in checks:
        all_warnings.extend(c.warnings)
        all_suggestions.extend(c.suggestions)

    # Dédupliquer tout en préservant l'ordre
    seen: set = set()
    unique_warnings: List[str] = []
    for w in all_warnings:
        if w not in seen:
            seen.add(w)
            unique_warnings.append(w)

    seen2: set = set()
    unique_suggestions: List[str] = []
    for s in all_suggestions:
        if s not in seen2:
            seen2.add(s)
            unique_suggestions.append(s)

    # Statut
    if overall >= _THRESHOLD_VALID:
        status = "valid"
    elif overall >= _THRESHOLD_REVISION:
        status = "needs_revision"
    else:
        status = "rejected"

    return ValidationReport(
        status=status,
        overall_score=round(overall, 3),
        palette_score=scores_by_checker.get("palette"),
        typography_score=scores_by_checker.get("typography"),
        icon_style_score=scores_by_checker.get("icon_style"),
        visual_style_score=scores_by_checker.get("visual_style"),
        layout_score=scores_by_checker.get("layout"),
        warnings=unique_warnings,
        suggestions=unique_suggestions,
        checks=checks,
        threshold=threshold,
        trace={
            "checkers_run": [c.checker for c in checks],
            "weights_used": {k: round(_DEFAULT_WEIGHTS[k] / raw_sum, 3) for k in present},
        },
    )
