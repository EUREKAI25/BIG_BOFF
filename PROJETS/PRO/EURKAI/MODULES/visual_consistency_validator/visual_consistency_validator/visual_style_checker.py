"""
visual_consistency_validator.visual_style_checker
──────────────────────────────────────────────────
Vérifie la cohérence du style visuel global (image_style, visual_style,
composition_style, motion_energy) avec le DesignDNA.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from .schemas import CheckResult, VisualAsset

# Profils de compatibilité par archétype
_ARCHETYPE_VISUAL_MAP: Dict[str, Dict[str, Any]] = {
    "luxury_minimal": {
        "preferred_image_styles":    ["soft_light_photography", "high_key_photography", "fine_art_photography"],
        "preferred_visual_styles":   ["minimal_luxury", "premium_white", "editorial_minimal"],
        "preferred_compositions":    ["balanced_asymmetric", "centered_minimal", "rule_of_thirds"],
        "preferred_motion_energies": ["none", "subtle"],
        "incompatible_image_styles": ["grungy_photo", "cartoon_illustration", "vibrant_pop"],
    },
    "startup_clean": {
        "preferred_image_styles":    ["soft_light_photography", "device_mockup", "abstract_gradient"],
        "preferred_visual_styles":   ["minimal_tech", "clean_white", "product_focus"],
        "preferred_compositions":    ["clean_grid", "balanced_asymmetric", "centered"],
        "preferred_motion_energies": ["subtle", "moderate"],
        "incompatible_image_styles": ["grungy_photo", "vintage_film", "painterly"],
    },
    "editorial_magazine": {
        "preferred_image_styles":    ["editorial_photography", "high_contrast_photo", "cinematic_photography"],
        "preferred_visual_styles":   ["editorial_bold", "contrast_layout", "typographic_focus"],
        "preferred_compositions":    ["editorial_grid", "dynamic_layout", "full_bleed"],
        "preferred_motion_energies": ["moderate", "dynamic"],
        "incompatible_image_styles": ["cartoon_illustration", "flat_design", "product_mockup"],
    },
    "tech_futurist": {
        "preferred_image_styles":    ["dark_atmosphere", "neon_glow", "3d_render", "abstract_tech"],
        "preferred_visual_styles":   ["futuristic_dark", "neon_tech", "cyberpunk_light"],
        "preferred_compositions":    ["dynamic_asymmetric", "edge_heavy", "diagonal_flow"],
        "preferred_motion_energies": ["moderate", "dynamic"],
        "incompatible_image_styles": ["warm_organic", "soft_light_photography", "nature_photo"],
    },
    "creative_studio": {
        "preferred_image_styles":    ["custom_illustration", "mixed_media", "art_direction"],
        "preferred_visual_styles":   ["expressive_visual", "art_directed", "creative_chaos"],
        "preferred_compositions":    ["experimental", "collage", "layered"],
        "preferred_motion_energies": ["moderate", "dynamic"],
        "incompatible_image_styles": ["stock_corporate", "flat_neutral", "device_mockup"],
    },
    "brutalist": {
        "preferred_image_styles":    ["high_contrast_bw", "raw_photography", "flat_graphic"],
        "preferred_visual_styles":   ["brutalist_raw", "bold_graphic", "typographic_brutalist"],
        "preferred_compositions":    ["rigid_grid", "oversize_type", "full_bleed"],
        "preferred_motion_energies": ["none", "subtle"],
        "incompatible_image_styles": ["soft_light_photography", "pastel_illustration", "nature_photo"],
    },
    "organic_natural": {
        "preferred_image_styles":    ["nature_photography", "warm_organic_photo", "hand_drawn_illustration"],
        "preferred_visual_styles":   ["warm_organic", "earthy_natural", "artisan_visual"],
        "preferred_compositions":    ["organic_layout", "balanced_natural", "soft_flow"],
        "preferred_motion_energies": ["none", "subtle"],
        "incompatible_image_styles": ["neon_glow", "abstract_tech", "dark_atmosphere"],
    },
    "playful_brand": {
        "preferred_image_styles":    ["cartoon_illustration", "bright_photography", "colorful_flat"],
        "preferred_visual_styles":   ["playful_colorful", "fun_graphic", "vibrant_pop"],
        "preferred_compositions":    ["dynamic_layout", "playful_asymmetric", "layered_fun"],
        "preferred_motion_energies": ["moderate", "dynamic"],
        "incompatible_image_styles": ["dark_atmosphere", "high_contrast_bw", "minimal_luxury"],
    },
    "corporate_pro": {
        "preferred_image_styles":    ["business_photography", "clean_office", "professional_portrait"],
        "preferred_visual_styles":   ["corporate_clean", "professional_neutral", "data_visual"],
        "preferred_compositions":    ["clean_grid", "structured_layout", "centered"],
        "preferred_motion_energies": ["none", "subtle"],
        "incompatible_image_styles": ["cartoon_illustration", "neon_glow", "grungy_photo"],
    },
    "premium_craft": {
        "preferred_image_styles":    ["artisan_photography", "warm_product_photo", "macro_texture"],
        "preferred_visual_styles":   ["craft_premium", "warm_artisan", "texture_focus"],
        "preferred_compositions":    ["centered_detail", "rule_of_thirds", "product_hero"],
        "preferred_motion_energies": ["none", "subtle"],
        "incompatible_image_styles": ["tech_3d", "neon_glow", "corporate_stock"],
    },
    "bold_challenger": {
        "preferred_image_styles":    ["action_photography", "high_contrast_photo", "dynamic_sport"],
        "preferred_visual_styles":   ["bold_dynamic", "energetic_visual", "challenger_graphic"],
        "preferred_compositions":    ["diagonal_flow", "dynamic_asymmetric", "full_bleed"],
        "preferred_motion_energies": ["dynamic"],
        "incompatible_image_styles": ["soft_light_photography", "pastel_illustration", "minimal_product"],
    },
    "warm_human": {
        "preferred_image_styles":    ["candid_photography", "warm_portrait", "community_photo"],
        "preferred_visual_styles":   ["warm_human_visual", "friendly_lifestyle", "inclusive_photo"],
        "preferred_compositions":    ["balanced_natural", "soft_flow", "centered"],
        "preferred_motion_energies": ["none", "subtle"],
        "incompatible_image_styles": ["dark_atmosphere", "neon_glow", "abstract_tech"],
    },
}

_MOTION_ORDER = ["none", "subtle", "moderate", "dynamic"]


def _motion_distance(a: str, b: str) -> int:
    try:
        return abs(_MOTION_ORDER.index(a) - _MOTION_ORDER.index(b))
    except ValueError:
        return 1


def check_visual_style(
    asset: VisualAsset,
    design_dna: Dict[str, Any],
) -> CheckResult:
    """
    Vérifie la cohérence du style visuel avec le DesignDNA.
    """
    warnings: List[str] = []
    suggestions: List[str] = []
    details: Dict[str, Any] = {}
    score = 1.0

    dna_image_style  = design_dna.get("image_style")
    dna_visual_style = design_dna.get("visual_style")
    dna_composition  = design_dna.get("composition_style")
    dna_motion       = design_dna.get("motion_energy", "subtle")
    dna_archetype    = design_dna.get("style_archetype")

    rules = _ARCHETYPE_VISUAL_MAP.get(dna_archetype or "", {})
    pref_image    = rules.get("preferred_image_styles", [])
    pref_visual   = rules.get("preferred_visual_styles", [])
    pref_compo    = rules.get("preferred_compositions", [])
    pref_motion   = rules.get("preferred_motion_energies", [])
    incompat_img  = rules.get("incompatible_image_styles", [])

    # ── Image style ───────────────────────────────────────────────────────────
    if asset.image_style:
        if asset.image_style == dna_image_style:
            details["image_style"] = "exact"
        elif asset.image_style in pref_image:
            details["image_style"] = "compatible"
            score -= 0.05
        elif asset.image_style in incompat_img:
            score -= 0.25
            details["image_style"] = "incompatible"
            warnings.append(
                f"Style d'image '{asset.image_style}' incompatible avec '{dna_archetype}'."
            )
            suggestions.append(
                f"Utiliser : {', '.join(pref_image[:3])}."
            )
        elif dna_image_style:
            score -= 0.10
            details["image_style"] = "neutral"
            warnings.append(
                f"Style d'image '{asset.image_style}' non optimal pour '{dna_archetype}' "
                f"(attendu : '{dna_image_style}')."
            )

    # ── Visual style ──────────────────────────────────────────────────────────
    if asset.composition_style:
        if asset.composition_style == dna_composition:
            details["composition"] = "exact"
        elif asset.composition_style in pref_compo:
            details["composition"] = "compatible"
        else:
            score -= 0.08
            details["composition"] = "mismatch"
            if dna_composition:
                warnings.append(
                    f"Composition '{asset.composition_style}' peu cohérente (attendu : '{dna_composition}')."
                )

    # ── Motion energy ─────────────────────────────────────────────────────────
    if asset.motion_energy:
        actual_motion = asset.motion_energy
        if actual_motion == dna_motion:
            details["motion_energy"] = "exact"
        elif actual_motion in pref_motion:
            details["motion_energy"] = "compatible"
            score -= 0.03
        else:
            dist = _motion_distance(actual_motion, dna_motion)
            penalty = 0.08 * dist
            score -= min(penalty, 0.20)
            details["motion_energy"] = "mismatch"
            warnings.append(
                f"Énergie de mouvement '{actual_motion}' éloignée de '{dna_motion}'."
            )
            suggestions.append(
                f"Ajuster vers : '{dna_motion}' ou {', '.join(pref_motion)}."
            )

    score = max(0.0, min(1.0, score))
    return CheckResult(
        checker="visual_style",
        score=round(score, 3),
        passed=score >= 0.80,
        warnings=warnings,
        suggestions=suggestions,
        details=details,
    )
