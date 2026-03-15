"""
visual_consistency_validator.layout_checker
────────────────────────────────────────────
Vérifie la cohérence du thème UI / layout avec le DesignDNA.

Critères :
- layout_style correspond au hint du DesignDNA
- visual_style cohérent avec l'archétype
- spacing et border_radius adaptés au ton
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from .schemas import CheckResult, UIThemeAsset

# Profils de layout par archétype
_ARCHETYPE_LAYOUT_MAP: Dict[str, Dict[str, Any]] = {
    "luxury_minimal": {
        "preferred_layouts":    ["centered_minimal", "clean_grid", "editorial_white"],
        "preferred_visuals":    ["minimal_luxury", "premium_white", "editorial_minimal"],
        "preferred_spacing":    ["spacious", "very_spacious"],
        "preferred_radius":     ["none", "small"],
        "incompatible_layouts": ["dense_grid", "card_overload", "playful_chaos"],
    },
    "startup_clean": {
        "preferred_layouts":    ["clean_grid", "modular_grid", "card_layout"],
        "preferred_visuals":    ["minimal_tech", "clean_white", "product_focus"],
        "preferred_spacing":    ["balanced", "spacious"],
        "preferred_radius":     ["small", "medium"],
        "incompatible_layouts": ["editorial_chaos", "dense_magazine", "organic_flow"],
    },
    "editorial_magazine": {
        "preferred_layouts":    ["editorial_flow", "magazine_grid", "dynamic_columns"],
        "preferred_visuals":    ["editorial_bold", "contrast_layout", "typographic_focus"],
        "preferred_spacing":    ["tight", "balanced"],
        "preferred_radius":     ["none", "small"],
        "incompatible_layouts": ["card_layout", "dashboard_grid", "centered_minimal"],
    },
    "tech_futurist": {
        "preferred_layouts":    ["dashboard_grid", "asymmetric_tech", "data_layout"],
        "preferred_visuals":    ["futuristic_dark", "neon_tech"],
        "preferred_spacing":    ["tight", "balanced"],
        "preferred_radius":     ["none", "small"],
        "incompatible_layouts": ["organic_flow", "centered_minimal", "warm_card"],
    },
    "creative_studio": {
        "preferred_layouts":    ["experimental_grid", "portfolio_masonry", "creative_flow"],
        "preferred_visuals":    ["expressive_visual", "art_directed"],
        "preferred_spacing":    ["variable", "generous"],
        "preferred_radius":     ["none", "variable"],
        "incompatible_layouts": ["corporate_grid", "dashboard_grid"],
    },
    "brutalist": {
        "preferred_layouts":    ["rigid_grid", "full_width", "oversize_sections"],
        "preferred_visuals":    ["brutalist_raw", "bold_graphic"],
        "preferred_spacing":    ["tight", "none"],
        "preferred_radius":     ["none"],
        "incompatible_layouts": ["card_layout", "soft_grid", "rounded_layout"],
    },
    "organic_natural": {
        "preferred_layouts":    ["organic_flow", "soft_sections", "wave_layout"],
        "preferred_visuals":    ["warm_organic", "earthy_natural"],
        "preferred_spacing":    ["balanced", "spacious"],
        "preferred_radius":     ["large", "circular"],
        "incompatible_layouts": ["rigid_grid", "dashboard_grid", "dense_grid"],
    },
    "playful_brand": {
        "preferred_layouts":    ["playful_card", "colorful_grid", "fun_flow"],
        "preferred_visuals":    ["playful_colorful", "fun_graphic"],
        "preferred_spacing":    ["balanced", "generous"],
        "preferred_radius":     ["large", "circular"],
        "incompatible_layouts": ["rigid_grid", "corporate_grid", "editorial_minimal"],
    },
    "corporate_pro": {
        "preferred_layouts":    ["corporate_grid", "structured_sections", "clean_columns"],
        "preferred_visuals":    ["corporate_clean", "professional_neutral"],
        "preferred_spacing":    ["balanced", "spacious"],
        "preferred_radius":     ["small", "none"],
        "incompatible_layouts": ["experimental_grid", "organic_flow", "playful_chaos"],
    },
    "premium_craft": {
        "preferred_layouts":    ["centered_story", "product_focus", "editorial_natural"],
        "preferred_visuals":    ["craft_premium", "warm_artisan"],
        "preferred_spacing":    ["spacious", "generous"],
        "preferred_radius":     ["small", "none"],
        "incompatible_layouts": ["dashboard_grid", "dense_grid", "corporate_grid"],
    },
    "bold_challenger": {
        "preferred_layouts":    ["full_width_hero", "diagonal_layout", "impact_grid"],
        "preferred_visuals":    ["bold_dynamic", "energetic_visual"],
        "preferred_spacing":    ["tight", "balanced"],
        "preferred_radius":     ["none", "small"],
        "incompatible_layouts": ["soft_grid", "centered_minimal", "organic_flow"],
    },
    "warm_human": {
        "preferred_layouts":    ["warm_card", "soft_sections", "community_grid"],
        "preferred_visuals":    ["warm_human_visual", "friendly_lifestyle"],
        "preferred_spacing":    ["balanced", "spacious"],
        "preferred_radius":     ["medium", "large"],
        "incompatible_layouts": ["rigid_grid", "dashboard_grid", "brutalist_grid"],
    },
}


def check_layout(
    asset: UIThemeAsset,
    design_dna: Dict[str, Any],
) -> CheckResult:
    """
    Vérifie la cohérence du layout/thème UI avec le DesignDNA.
    """
    warnings: List[str] = []
    suggestions: List[str] = []
    details: Dict[str, Any] = {}
    score = 1.0

    dna_layout_style = design_dna.get("layout_style")
    dna_visual_style = design_dna.get("visual_style")
    dna_archetype    = design_dna.get("style_archetype")

    rules = _ARCHETYPE_LAYOUT_MAP.get(dna_archetype or "", {})
    pref_layouts    = rules.get("preferred_layouts", [])
    pref_visuals    = rules.get("preferred_visuals", [])
    pref_spacing    = rules.get("preferred_spacing", [])
    pref_radius     = rules.get("preferred_radius", [])
    incompat_layout = rules.get("incompatible_layouts", [])

    # ── Layout style ──────────────────────────────────────────────────────────
    if asset.layout_style:
        if asset.layout_style == dna_layout_style:
            details["layout_match"] = "exact"
        elif asset.layout_style in pref_layouts:
            details["layout_match"] = "compatible"
            score -= 0.05
        elif asset.layout_style in incompat_layout:
            score -= 0.25
            details["layout_match"] = "incompatible"
            warnings.append(
                f"Layout '{asset.layout_style}' incompatible avec l'archétype '{dna_archetype}'."
            )
            suggestions.append(
                f"Utiliser : {', '.join(pref_layouts[:3])} (attendu : '{dna_layout_style}')."
            )
        else:
            score -= 0.10
            details["layout_match"] = "neutral"
            if dna_layout_style:
                warnings.append(
                    f"Layout '{asset.layout_style}' non optimal (attendu : '{dna_layout_style}')."
                )

    elif dna_layout_style:
        score -= 0.10
        warnings.append("Layout style non renseigné dans l'asset UI.")

    # ── Visual style ──────────────────────────────────────────────────────────
    if asset.visual_style:
        if asset.visual_style == dna_visual_style:
            details["visual_match"] = "exact"
        elif asset.visual_style in pref_visuals:
            details["visual_match"] = "compatible"
        else:
            score -= 0.08
            details["visual_match"] = "neutral"
            if dna_visual_style:
                warnings.append(
                    f"Style visuel UI '{asset.visual_style}' non optimal (attendu : '{dna_visual_style}')."
                )

    # ── Spacing ───────────────────────────────────────────────────────────────
    if asset.spacing_type and pref_spacing:
        if asset.spacing_type in pref_spacing:
            details["spacing_match"] = "ok"
        else:
            score -= 0.07
            details["spacing_match"] = "mismatch"
            warnings.append(
                f"Espacement '{asset.spacing_type}' peu cohérent avec '{dna_archetype}'."
            )
            suggestions.append(f"Préférer : {', '.join(pref_spacing)}.")

    # ── Border radius ─────────────────────────────────────────────────────────
    if asset.border_radius and pref_radius:
        if asset.border_radius in pref_radius:
            details["radius_match"] = "ok"
        else:
            score -= 0.07
            details["radius_match"] = "mismatch"
            warnings.append(
                f"Border radius '{asset.border_radius}' peu cohérent avec '{dna_archetype}'."
            )
            suggestions.append(f"Préférer : {', '.join(pref_radius)}.")

    score = max(0.0, min(1.0, score))
    return CheckResult(
        checker="layout",
        score=round(score, 3),
        passed=score >= 0.80,
        warnings=warnings,
        suggestions=suggestions,
        details=details,
    )
