"""
design_exploration_engine.archetype_variator
──────────────────────────────────────────────
Sélectionne N archetypes distincts à partir d'un archétype source.

Stratégie :
1. L'archétype source est toujours inclus en direction 1 (exploration fidèle).
2. Les autres directions explorent des archétypes voisins ou contrastants
   selon la famille de direction demandée.
3. La diversité est maximisée : pas deux directions trop proches.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple

# ─── Familles de directions ───────────────────────────────────────────────────
# Chaque famille regroupe des archetypes stylistiquement proches

_DIRECTION_FAMILIES: Dict[str, List[str]] = {
    "clean_modern":         ["startup_clean", "corporate_pro", "editorial_magazine"],
    "premium_luxury":       ["luxury_minimal", "premium_craft", "editorial_magazine"],
    "tech_futuristic":      ["tech_futurist", "startup_clean", "bold_challenger"],
    "creative_experimental":["creative_studio", "brutalist", "editorial_magazine"],
    "editorial_minimal":    ["editorial_magazine", "luxury_minimal", "startup_clean"],
    "organic_nature":       ["organic_natural", "warm_human", "premium_craft"],
    "bold_energetic":       ["bold_challenger", "tech_futurist", "playful_brand"],
    "warm_accessible":      ["warm_human", "organic_natural", "playful_brand"],
    "artisan_premium":      ["premium_craft", "luxury_minimal", "organic_natural"],
    "corporate_trust":      ["corporate_pro", "warm_human", "startup_clean"],
}

# Pour chaque archétype : quels sont les archétypes de "variation naturelle"
# (proches mais distincts) et de "contraste créatif" (différents mais cohérents)
_ARCHETYPE_NEIGHBORS: Dict[str, Dict[str, List[str]]] = {
    "luxury_minimal": {
        "natural":    ["editorial_magazine", "premium_craft"],
        "contrast":   ["tech_futurist", "startup_clean"],
        "wild_card":  ["creative_studio", "brutalist"],
    },
    "startup_clean": {
        "natural":    ["corporate_pro", "tech_futurist"],
        "contrast":   ["editorial_magazine", "luxury_minimal"],
        "wild_card":  ["bold_challenger", "creative_studio"],
    },
    "editorial_magazine": {
        "natural":    ["luxury_minimal", "creative_studio"],
        "contrast":   ["startup_clean", "corporate_pro"],
        "wild_card":  ["brutalist", "tech_futurist"],
    },
    "tech_futurist": {
        "natural":    ["startup_clean", "bold_challenger"],
        "contrast":   ["organic_natural", "warm_human"],
        "wild_card":  ["creative_studio", "brutalist"],
    },
    "creative_studio": {
        "natural":    ["editorial_magazine", "brutalist"],
        "contrast":   ["corporate_pro", "startup_clean"],
        "wild_card":  ["playful_brand", "tech_futurist"],
    },
    "brutalist": {
        "natural":    ["creative_studio", "bold_challenger"],
        "contrast":   ["luxury_minimal", "warm_human"],
        "wild_card":  ["editorial_magazine", "tech_futurist"],
    },
    "organic_natural": {
        "natural":    ["warm_human", "premium_craft"],
        "contrast":   ["tech_futurist", "bold_challenger"],
        "wild_card":  ["luxury_minimal", "editorial_magazine"],
    },
    "playful_brand": {
        "natural":    ["warm_human", "creative_studio"],
        "contrast":   ["luxury_minimal", "corporate_pro"],
        "wild_card":  ["bold_challenger", "organic_natural"],
    },
    "corporate_pro": {
        "natural":    ["startup_clean", "warm_human"],
        "contrast":   ["creative_studio", "brutalist"],
        "wild_card":  ["luxury_minimal", "editorial_magazine"],
    },
    "premium_craft": {
        "natural":    ["luxury_minimal", "organic_natural"],
        "contrast":   ["tech_futurist", "bold_challenger"],
        "wild_card":  ["editorial_magazine", "creative_studio"],
    },
    "bold_challenger": {
        "natural":    ["tech_futurist", "creative_studio"],
        "contrast":   ["luxury_minimal", "warm_human"],
        "wild_card":  ["brutalist", "playful_brand"],
    },
    "warm_human": {
        "natural":    ["organic_natural", "playful_brand"],
        "contrast":   ["tech_futurist", "corporate_pro"],
        "wild_card":  ["premium_craft", "startup_clean"],
    },
}

# Mapping archétype → famille principale
_ARCHETYPE_TO_FAMILY: Dict[str, str] = {
    "luxury_minimal":   "premium_luxury",
    "startup_clean":    "clean_modern",
    "editorial_magazine": "editorial_minimal",
    "tech_futurist":    "tech_futuristic",
    "creative_studio":  "creative_experimental",
    "brutalist":        "creative_experimental",
    "organic_natural":  "organic_nature",
    "playful_brand":    "warm_accessible",
    "corporate_pro":    "corporate_trust",
    "premium_craft":    "artisan_premium",
    "bold_challenger":  "bold_energetic",
    "warm_human":       "warm_accessible",
}


def select_archetypes(
    source_archetype: str,
    n: int = 3,
) -> List[Tuple[str, str, str]]:
    """
    Sélectionne N (archétype, famille, relation) distincts pour les N directions.

    Returns: liste de (archétype, famille, relation_to_source)
    où relation_to_source = "source" | "natural" | "contrast" | "wild_card"
    """
    n = max(2, min(5, n))
    neighbors = _ARCHETYPE_NEIGHBORS.get(source_archetype, {})

    result: List[Tuple[str, str, str]] = []
    used: set = {source_archetype}

    # Direction 1 : toujours l'archétype source (exploration fidèle)
    family = _ARCHETYPE_TO_FAMILY.get(source_archetype, "clean_modern")
    result.append((source_archetype, family, "source"))

    # Direction 2 : variation naturelle (proche mais légèrement différent)
    if n >= 2:
        for a in neighbors.get("natural", []):
            if a not in used:
                f = _ARCHETYPE_TO_FAMILY.get(a, "clean_modern")
                result.append((a, f, "natural"))
                used.add(a)
                break

    # Direction 3 : contraste créatif (différent mais cohérent avec le brief)
    if n >= 3:
        for a in neighbors.get("contrast", []):
            if a not in used:
                f = _ARCHETYPE_TO_FAMILY.get(a, "clean_modern")
                result.append((a, f, "contrast"))
                used.add(a)
                break

    # Direction 4 : wild card (audacieux, inattendu)
    if n >= 4:
        for a in neighbors.get("wild_card", []):
            if a not in used:
                f = _ARCHETYPE_TO_FAMILY.get(a, "clean_modern")
                result.append((a, f, "wild_card"))
                used.add(a)
                break

    # Direction 5 : si encore besoin, piocher dans les naturels restants
    if n >= 5:
        all_archetypes = list(_ARCHETYPE_NEIGHBORS.keys())
        for a in all_archetypes:
            if a not in used and len(result) < n:
                f = _ARCHETYPE_TO_FAMILY.get(a, "clean_modern")
                result.append((a, f, "alternate"))
                used.add(a)

    return result[:n]
