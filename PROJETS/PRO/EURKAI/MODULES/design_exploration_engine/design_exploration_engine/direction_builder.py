"""
design_exploration_engine.direction_builder
────────────────────────────────────────────
Assemble une DesignDirection complète à partir d'un archétype cible
et du DesignDNA source.

Chaque direction conserve les informations de marque (industry, brand_values,
target_audience) mais explore différents vecteurs stylistiques.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from .schemas import DesignDirection
from .palette_variator    import get_palette_bias
from .typography_variator import get_typography_style, get_wordmark_weight

# ─── Style complet par archétype ─────────────────────────────────────────────

_ARCHETYPE_STYLE: Dict[str, Dict[str, str]] = {
    "luxury_minimal": {
        "name":              "Luxury Minimal",
        "tagline":           "Élégance épurée, sobriété assumée",
        "icon_style":        "refined_line",
        "visual_style":      "minimal_luxury",
        "layout_style":      "centered_minimal",
        "image_style":       "soft_light_photography",
        "composition_style": "balanced_asymmetric",
        "motion_energy":     "subtle",
        "logo_structure":    "wordmark",
    },
    "startup_clean": {
        "name":              "Clean Tech",
        "tagline":           "Clarté moderne, efficacité maximale",
        "icon_style":        "line",
        "visual_style":      "minimal_tech",
        "layout_style":      "clean_grid",
        "image_style":       "soft_light_photography",
        "composition_style": "clean_grid",
        "motion_energy":     "subtle",
        "logo_structure":    "icon_wordmark",
    },
    "editorial_magazine": {
        "name":              "Editorial Bold",
        "tagline":           "La force de la typographie au service de la marque",
        "icon_style":        "refined_line",
        "visual_style":      "editorial_bold",
        "layout_style":      "editorial_flow",
        "image_style":       "editorial_photography",
        "composition_style": "editorial_grid",
        "motion_energy":     "moderate",
        "logo_structure":    "wordmark",
    },
    "tech_futurist": {
        "name":              "Future Tech",
        "tagline":           "Vision futuriste, interface du lendemain",
        "icon_style":        "geometric",
        "visual_style":      "futuristic_dark",
        "layout_style":      "dashboard_grid",
        "image_style":       "dark_atmosphere",
        "composition_style": "dynamic_asymmetric",
        "motion_energy":     "dynamic",
        "logo_structure":    "abstract_symbol",
    },
    "creative_studio": {
        "name":              "Creative Studio",
        "tagline":           "Expression libre, identité unique",
        "icon_style":        "expressive_icon",
        "visual_style":      "expressive_visual",
        "layout_style":      "experimental_grid",
        "image_style":       "custom_illustration",
        "composition_style": "layered",
        "motion_energy":     "dynamic",
        "logo_structure":    "icon_wordmark",
    },
    "brutalist": {
        "name":              "Raw Brutalist",
        "tagline":           "Brut, direct, mémorable",
        "icon_style":        "filled_bold",
        "visual_style":      "brutalist_raw",
        "layout_style":      "rigid_grid",
        "image_style":       "high_contrast_bw",
        "composition_style": "full_bleed",
        "motion_energy":     "none",
        "logo_structure":    "wordmark",
    },
    "organic_natural": {
        "name":              "Organic Natural",
        "tagline":           "Authenticité, nature, chaleur humaine",
        "icon_style":        "organic_line",
        "visual_style":      "warm_organic",
        "layout_style":      "organic_flow",
        "image_style":       "nature_photography",
        "composition_style": "organic_layout",
        "motion_energy":     "subtle",
        "logo_structure":    "emblem",
    },
    "playful_brand": {
        "name":              "Playful Brand",
        "tagline":           "Fun, coloré, accessible à tous",
        "icon_style":        "filled_rounded",
        "visual_style":      "playful_colorful",
        "layout_style":      "playful_card",
        "image_style":       "bright_photography",
        "composition_style": "layered_fun",
        "motion_energy":     "dynamic",
        "logo_structure":    "icon_wordmark",
    },
    "corporate_pro": {
        "name":              "Corporate Pro",
        "tagline":           "Confiance professionnelle, image institutionnelle",
        "icon_style":        "neutral_line",
        "visual_style":      "corporate_clean",
        "layout_style":      "corporate_grid",
        "image_style":       "business_photography",
        "composition_style": "structured_layout",
        "motion_energy":     "none",
        "logo_structure":    "wordmark",
    },
    "premium_craft": {
        "name":              "Premium Craft",
        "tagline":           "Savoir-faire artisanal, qualité premium",
        "icon_style":        "refined_line",
        "visual_style":      "craft_premium",
        "layout_style":      "centered_story",
        "image_style":       "artisan_photography",
        "composition_style": "product_hero",
        "motion_energy":     "subtle",
        "logo_structure":    "emblem",
    },
    "bold_challenger": {
        "name":              "Bold Challenger",
        "tagline":           "Énergie brute, impact maximal",
        "icon_style":        "filled_bold",
        "visual_style":      "bold_dynamic",
        "layout_style":      "full_width_hero",
        "image_style":       "action_photography",
        "composition_style": "diagonal_flow",
        "motion_energy":     "dynamic",
        "logo_structure":    "icon_wordmark",
    },
    "warm_human": {
        "name":              "Warm Human",
        "tagline":           "Empathie, accessibilité, lien humain",
        "icon_style":        "soft_line",
        "visual_style":      "warm_human_visual",
        "layout_style":      "warm_card",
        "image_style":       "candid_photography",
        "composition_style": "balanced_natural",
        "motion_energy":     "subtle",
        "logo_structure":    "icon_wordmark",
    },
}

# Descriptions de différenciation selon la relation
_DIFFERENTIATION_LABELS: Dict[str, List[str]] = {
    "source":    ["Fidèle au brief initial", "Direction de référence"],
    "natural":   ["Variation harmonieuse", "Même territoire, esthétique évoluée"],
    "contrast":  ["Direction contrastée", "Territoire créatif différent", "Alternative créative"],
    "wild_card": ["Direction audacieuse", "Rupture créative assumée", "Inattendu mais cohérent"],
    "alternate": ["Direction alternative", "Exploration complémentaire"],
}


def build_direction(
    archetype: str,
    direction_id: str,
    family: str,
    relation: str,
    source_dna: Dict[str, Any],
    index: int,
) -> DesignDirection:
    """
    Assemble une DesignDirection complète.
    """
    style = _ARCHETYPE_STYLE.get(archetype, {})

    # Nom : utiliser le nom de l'archétype + indice si plusieurs directions similaires
    name = style.get("name", archetype.replace("_", " ").title())
    tagline = style.get("tagline", "")

    palette = get_palette_bias(archetype, source_dna=source_dna, relation=relation)
    typo    = get_typography_style(archetype)
    weight  = get_wordmark_weight(archetype)

    differentiations = _DIFFERENTIATION_LABELS.get(relation, ["Direction alternative"])

    return DesignDirection(
        id=direction_id,
        name=name,
        tagline=tagline,
        style_archetype=archetype,
        palette_bias=palette,
        typography_style=typo,
        icon_style=style.get("icon_style"),
        visual_style=style.get("visual_style"),
        layout_style=style.get("layout_style"),
        image_style=style.get("image_style"),
        composition_style=style.get("composition_style"),
        motion_energy=style.get("motion_energy"),
        logo_structure_hint=style.get("logo_structure"),
        wordmark_weight_hint=weight,
        direction_family=family,
        differentiation=differentiations,
        confidence=1.0 if relation == "source" else (0.90 if relation == "natural" else 0.80),
    )
