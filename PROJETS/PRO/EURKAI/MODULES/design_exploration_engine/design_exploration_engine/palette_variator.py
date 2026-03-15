"""
design_exploration_engine.palette_variator
───────────────────────────────────────────
Génère un palette_bias (liste de couleurs sémantiques) adapté à chaque archétype
et cohérent avec les hints du DesignDNA source.

Utilise la même logique sémantique que color_psychology_engine mais appliquée
à une sélection d'archétypes (pas à un brief).
"""

from __future__ import annotations
from typing import Dict, List, Optional

# Profil de palette par archétype (couleurs sémantiques, pas hex)
_ARCHETYPE_PALETTE: Dict[str, Dict[str, List[str]]] = {
    "luxury_minimal": {
        "primary":  ["black", "off_white", "champagne"],
        "accent":   ["gold", "platinum", "deep_burgundy"],
        "neutral":  ["warm_gray", "ivory", "cream"],
    },
    "startup_clean": {
        "primary":  ["electric_blue", "navy", "indigo"],
        "accent":   ["cyan", "teal", "violet"],
        "neutral":  ["white", "light_gray", "charcoal"],
    },
    "editorial_magazine": {
        "primary":  ["black", "white", "deep_red"],
        "accent":   ["gold", "crimson", "forest_green"],
        "neutral":  ["off_white", "warm_gray"],
    },
    "tech_futurist": {
        "primary":  ["deep_navy", "near_black", "charcoal"],
        "accent":   ["neon_cyan", "electric_purple", "neon_green"],
        "neutral":  ["dark_gray", "slate"],
    },
    "creative_studio": {
        "primary":  ["vivid_coral", "electric_yellow", "hot_pink"],
        "accent":   ["violet", "turquoise", "lime"],
        "neutral":  ["white", "off_white", "light_gray"],
    },
    "brutalist": {
        "primary":  ["black", "white", "raw_yellow"],
        "accent":   ["vivid_red", "neon_green"],
        "neutral":  ["concrete_gray"],
    },
    "organic_natural": {
        "primary":  ["forest_green", "sage", "terracotta"],
        "accent":   ["amber", "warm_beige", "dusty_rose"],
        "neutral":  ["off_white", "cream", "sand"],
    },
    "playful_brand": {
        "primary":  ["coral", "sunshine_yellow", "sky_blue"],
        "accent":   ["hot_pink", "mint", "lavender"],
        "neutral":  ["white", "light_gray"],
    },
    "corporate_pro": {
        "primary":  ["navy", "slate_gray", "steel_blue"],
        "accent":   ["teal", "sky_blue", "warm_gray"],
        "neutral":  ["white", "light_gray", "charcoal"],
    },
    "premium_craft": {
        "primary":  ["deep_brown", "caramel", "warm_beige"],
        "accent":   ["gold", "terracotta", "olive"],
        "neutral":  ["cream", "off_white", "sand"],
    },
    "bold_challenger": {
        "primary":  ["vivid_red", "charcoal", "black"],
        "accent":   ["electric_orange", "neon_yellow", "white"],
        "neutral":  ["dark_gray", "concrete_gray"],
    },
    "warm_human": {
        "primary":  ["warm_coral", "soft_peach", "dusty_rose"],
        "accent":   ["terracotta", "amber", "sage"],
        "neutral":  ["cream", "warm_white", "sand"],
    },
}


def get_palette_bias(
    archetype: str,
    source_dna: Optional[Dict] = None,
    relation: str = "source",
) -> List[str]:
    """
    Retourne une liste de couleurs sémantiques pour un archétype donné.

    - Si relation == "source" : utilise les preferred_colors du DesignDNA si disponibles.
    - Sinon : utilise le profil de l'archétype cible.
    """
    # Si direction source, honorer le palette_bias du DNA d'origine
    if relation == "source" and source_dna:
        pb = source_dna.get("palette_bias") or {}
        preferred = pb.get("preferred_colors", [])
        if preferred:
            return preferred

    profile = _ARCHETYPE_PALETTE.get(archetype, {})
    primary = profile.get("primary", [])
    accent  = profile.get("accent", [])

    # Retourner 4-6 couleurs (2-3 primary + 2 accent)
    result = primary[:3] + accent[:2]
    return result
