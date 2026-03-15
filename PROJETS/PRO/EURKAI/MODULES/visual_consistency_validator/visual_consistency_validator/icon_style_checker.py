"""
visual_consistency_validator.icon_style_checker
─────────────────────────────────────────────────
Vérifie la cohérence du style d'icônes avec le DesignDNA.

Critères :
- icon_style correspond au hint du DesignDNA
- corner_radius compatible avec l'archétype (sharp vs rounded)
- weight des icônes cohérent avec le ton
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from .schemas import CheckResult, IconAsset

# Styles d'icônes compatibles par archétype
_ARCHETYPE_ICON_MAP: Dict[str, Dict[str, Any]] = {
    "luxury_minimal": {
        "preferred_styles": ["refined_line", "thin_line", "minimal_line"],
        "preferred_radius": ["sharp", "slightly_rounded"],
        "preferred_weights": ["thin", "light", "regular"],
        "incompatible_styles": ["filled_bold", "cartoon", "colorful_duotone"],
    },
    "startup_clean": {
        "preferred_styles": ["line", "outline", "minimal_line"],
        "preferred_radius": ["slightly_rounded", "rounded"],
        "preferred_weights": ["regular", "medium"],
        "incompatible_styles": ["cartoon", "ornate", "blackletter"],
    },
    "editorial_magazine": {
        "preferred_styles": ["refined_line", "editorial_icon", "thin_line"],
        "preferred_radius": ["sharp", "slightly_rounded"],
        "preferred_weights": ["thin", "light", "regular"],
        "incompatible_styles": ["cartoon", "filled_bold", "colorful_duotone"],
    },
    "tech_futurist": {
        "preferred_styles": ["geometric", "angular_line", "sharp_outline"],
        "preferred_radius": ["sharp", "none"],
        "preferred_weights": ["regular", "medium"],
        "incompatible_styles": ["organic", "rounded_filled", "cartoon"],
    },
    "creative_studio": {
        "preferred_styles": ["expressive_icon", "duotone", "custom_illustrated"],
        "preferred_radius": ["rounded", "variable"],
        "preferred_weights": ["regular", "bold"],
        "incompatible_styles": ["neutral_line", "corporate_icon"],
    },
    "brutalist": {
        "preferred_styles": ["filled_bold", "block_icon", "outlined_heavy"],
        "preferred_radius": ["sharp", "none"],
        "preferred_weights": ["bold", "heavy"],
        "incompatible_styles": ["thin_line", "refined_line", "cartoon"],
    },
    "organic_natural": {
        "preferred_styles": ["organic_line", "soft_outline", "illustrated_natural"],
        "preferred_radius": ["rounded", "circular"],
        "preferred_weights": ["light", "regular"],
        "incompatible_styles": ["angular_line", "sharp_outline", "geometric"],
    },
    "playful_brand": {
        "preferred_styles": ["filled_rounded", "cartoon", "colorful_duotone"],
        "preferred_radius": ["rounded", "circular"],
        "preferred_weights": ["regular", "bold"],
        "incompatible_styles": ["thin_line", "sharp_outline", "refined_line"],
    },
    "corporate_pro": {
        "preferred_styles": ["neutral_line", "corporate_icon", "outline"],
        "preferred_radius": ["slightly_rounded", "sharp"],
        "preferred_weights": ["regular", "medium"],
        "incompatible_styles": ["cartoon", "expressive_icon", "colorful_duotone"],
    },
    "premium_craft": {
        "preferred_styles": ["refined_line", "artisan_icon", "organic_line"],
        "preferred_radius": ["slightly_rounded", "sharp"],
        "preferred_weights": ["light", "regular"],
        "incompatible_styles": ["cartoon", "filled_bold", "tech_geometric"],
    },
    "bold_challenger": {
        "preferred_styles": ["filled_bold", "solid_icon", "outlined_heavy"],
        "preferred_radius": ["sharp", "none"],
        "preferred_weights": ["bold", "heavy"],
        "incompatible_styles": ["thin_line", "refined_line", "cartoon"],
    },
    "warm_human": {
        "preferred_styles": ["soft_line", "friendly_icon", "organic_line"],
        "preferred_radius": ["rounded", "circular"],
        "preferred_weights": ["regular", "medium"],
        "incompatible_styles": ["sharp_outline", "angular_line", "geometric"],
    },
}


def check_icon_style(
    asset: IconAsset,
    design_dna: Dict[str, Any],
) -> CheckResult:
    """
    Vérifie la cohérence du style d'icônes avec le DesignDNA.
    """
    warnings: List[str] = []
    suggestions: List[str] = []
    details: Dict[str, Any] = {}
    score = 1.0

    dna_icon_style = design_dna.get("icon_style")
    dna_archetype  = design_dna.get("style_archetype")

    archetype_rules     = _ARCHETYPE_ICON_MAP.get(dna_archetype or "", {})
    preferred_styles    = archetype_rules.get("preferred_styles", [])
    preferred_radius    = archetype_rules.get("preferred_radius", [])
    preferred_weights   = archetype_rules.get("preferred_weights", [])
    incompatible_styles = archetype_rules.get("incompatible_styles", [])

    # ── Style match ───────────────────────────────────────────────────────────
    if dna_icon_style and asset.style:
        if asset.style == dna_icon_style:
            details["style_match"] = "exact"
        elif asset.style in preferred_styles:
            details["style_match"] = "compatible"
            score -= 0.05
        elif asset.style in incompatible_styles:
            score -= 0.30
            details["style_match"] = "incompatible"
            warnings.append(
                f"Style d'icônes '{asset.style}' incompatible avec l'archétype '{dna_archetype}'."
            )
            suggestions.append(
                f"Utiliser un style parmi : {', '.join(preferred_styles[:3])} "
                f"(attendu : '{dna_icon_style}')."
            )
        else:
            score -= 0.10
            details["style_match"] = "neutral"
    elif dna_icon_style and not asset.style:
        score -= 0.15
        warnings.append("Style d'icônes non renseigné dans l'asset.")
        suggestions.append(f"Renseigner le style (attendu : '{dna_icon_style}').")

    # ── Corner radius ─────────────────────────────────────────────────────────
    if asset.corner_radius and preferred_radius:
        if asset.corner_radius in preferred_radius:
            details["radius_match"] = "ok"
        else:
            score -= 0.10
            details["radius_match"] = "mismatch"
            warnings.append(
                f"Corner radius '{asset.corner_radius}' peu cohérent avec l'archétype '{dna_archetype}'."
            )
            suggestions.append(
                f"Préférer : {', '.join(preferred_radius)}."
            )

    # ── Icon weight ───────────────────────────────────────────────────────────
    if asset.weight and preferred_weights:
        if asset.weight in preferred_weights:
            details["weight_match"] = "ok"
        else:
            score -= 0.10
            details["weight_match"] = "mismatch"
            warnings.append(
                f"Grammage icônes '{asset.weight}' peu cohérent avec l'archétype '{dna_archetype}'."
            )
            suggestions.append(
                f"Préférer un grammage parmi : {', '.join(preferred_weights)}."
            )

    score = max(0.0, min(1.0, score))
    return CheckResult(
        checker="icon_style",
        score=round(score, 3),
        passed=score >= 0.80,
        warnings=warnings,
        suggestions=suggestions,
        details=details,
    )
