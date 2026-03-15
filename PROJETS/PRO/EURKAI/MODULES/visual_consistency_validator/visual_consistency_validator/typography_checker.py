"""
visual_consistency_validator.typography_checker
────────────────────────────────────────────────
Vérifie la cohérence du style typographique avec le DesignDNA.

Critères :
- typography_style correspond à celui attendu par le DesignDNA
- weight_hint cohérent avec l'archétype stylistique
- pairing_style compatible
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from .schemas import CheckResult, TypographyAsset

# Typographies compatibles par archétype stylistique
_ARCHETYPE_TYPO_MAP: Dict[str, Dict[str, Any]] = {
    "luxury_minimal": {
        "preferred_styles": ["elegant_serif", "thin_sans", "display_serif"],
        "preferred_weights": ["light", "thin", "regular"],
        "incompatible_styles": ["rounded_sans", "playful_slab", "tech_mono"],
    },
    "startup_clean": {
        "preferred_styles": ["geometric_sans", "modern_sans", "neutral_sans"],
        "preferred_weights": ["regular", "medium", "semibold"],
        "incompatible_styles": ["ornate_serif", "blackletter", "display_serif"],
    },
    "editorial_magazine": {
        "preferred_styles": ["editorial_serif", "contrast_serif", "display_serif"],
        "preferred_weights": ["regular", "bold", "black"],
        "incompatible_styles": ["tech_mono", "rounded_sans", "geometric_sans"],
    },
    "tech_futurist": {
        "preferred_styles": ["tech_sans", "tech_mono", "condensed_sans"],
        "preferred_weights": ["regular", "medium", "bold"],
        "incompatible_styles": ["ornate_serif", "script", "display_serif"],
    },
    "creative_studio": {
        "preferred_styles": ["expressive_display", "humanist_sans", "variable_font"],
        "preferred_weights": ["light", "bold", "black"],
        "incompatible_styles": ["corporate_sans", "neutral_sans"],
    },
    "brutalist": {
        "preferred_styles": ["grotesque_sans", "condensed_sans", "slab_serif"],
        "preferred_weights": ["bold", "black", "heavy"],
        "incompatible_styles": ["thin_sans", "elegant_serif", "script"],
    },
    "organic_natural": {
        "preferred_styles": ["humanist_sans", "organic_serif", "soft_slab"],
        "preferred_weights": ["light", "regular", "medium"],
        "incompatible_styles": ["tech_mono", "condensed_sans", "grotesque_sans"],
    },
    "playful_brand": {
        "preferred_styles": ["rounded_sans", "playful_slab", "fun_display"],
        "preferred_weights": ["regular", "bold", "black"],
        "incompatible_styles": ["thin_sans", "elegant_serif", "tech_mono"],
    },
    "corporate_pro": {
        "preferred_styles": ["corporate_sans", "neutral_sans", "modern_serif"],
        "preferred_weights": ["regular", "medium", "semibold"],
        "incompatible_styles": ["expressive_display", "playful_slab", "tech_mono"],
    },
    "premium_craft": {
        "preferred_styles": ["artisan_serif", "organic_serif", "slab_serif"],
        "preferred_weights": ["regular", "medium"],
        "incompatible_styles": ["tech_mono", "condensed_sans", "grotesque_sans"],
    },
    "bold_challenger": {
        "preferred_styles": ["condensed_sans", "grotesque_sans", "impact_display"],
        "preferred_weights": ["bold", "black", "heavy"],
        "incompatible_styles": ["thin_sans", "elegant_serif", "script"],
    },
    "warm_human": {
        "preferred_styles": ["humanist_sans", "soft_sans", "friendly_slab"],
        "preferred_weights": ["light", "regular", "medium"],
        "incompatible_styles": ["tech_mono", "condensed_sans", "grotesque_sans"],
    },
}


def check_typography(
    asset: TypographyAsset,
    design_dna: Dict[str, Any],
) -> CheckResult:
    """
    Vérifie la cohérence typographique avec le DesignDNA.
    """
    warnings: List[str] = []
    suggestions: List[str] = []
    details: Dict[str, Any] = {}
    score = 1.0

    dna_typo_style = design_dna.get("typography_style")
    dna_archetype  = design_dna.get("style_archetype")

    archetype_rules = _ARCHETYPE_TYPO_MAP.get(dna_archetype or "", {})
    preferred_styles    = archetype_rules.get("preferred_styles", [])
    preferred_weights   = archetype_rules.get("preferred_weights", [])
    incompatible_styles = archetype_rules.get("incompatible_styles", [])

    # ── Style match vs DesignDNA hint ─────────────────────────────────────────
    if dna_typo_style and asset.style:
        if asset.style == dna_typo_style:
            details["style_match"] = "exact"
        elif asset.style in preferred_styles:
            details["style_match"] = "compatible"
            score -= 0.05
        elif asset.style in incompatible_styles:
            score -= 0.30
            details["style_match"] = "incompatible"
            warnings.append(
                f"Style typographique '{asset.style}' incompatible avec l'archétype '{dna_archetype}'."
            )
            suggestions.append(
                f"Utiliser un style parmi : {', '.join(preferred_styles[:3])} "
                f"(attendu : '{dna_typo_style}')."
            )
        else:
            score -= 0.10
            details["style_match"] = "neutral"
            warnings.append(
                f"Style typographique '{asset.style}' non reconnu pour l'archétype '{dna_archetype}'. "
                f"Attendu : '{dna_typo_style}'."
            )
            suggestions.append(f"Vérifier la compatibilité avec : {', '.join(preferred_styles[:3])}.")

    elif dna_typo_style and not asset.style:
        score -= 0.15
        warnings.append("Style typographique non renseigné dans l'asset.")
        suggestions.append(f"Renseigner le style typographique (attendu : '{dna_typo_style}').")

    # ── Weight hint ───────────────────────────────────────────────────────────
    if asset.weight_hint and preferred_weights:
        if asset.weight_hint in preferred_weights:
            details["weight_match"] = "ok"
        else:
            score -= 0.10
            details["weight_match"] = "mismatch"
            warnings.append(
                f"Grammage '{asset.weight_hint}' peu cohérent avec l'archétype '{dna_archetype}'."
            )
            suggestions.append(
                f"Préférer un grammage parmi : {', '.join(preferred_weights)}."
            )

    score = max(0.0, min(1.0, score))
    return CheckResult(
        checker="typography",
        score=round(score, 3),
        passed=score >= 0.80,
        warnings=warnings,
        suggestions=suggestions,
        details=details,
    )
