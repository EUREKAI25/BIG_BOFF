"""
design_exploration_engine.typography_variator
──────────────────────────────────────────────
Retourne le style typographique adapté à chaque archétype.
Cohérent avec les règles du visual_consistency_validator.
"""

from __future__ import annotations
from typing import Dict, Optional

_ARCHETYPE_TYPOGRAPHY: Dict[str, str] = {
    "luxury_minimal":    "elegant_serif",
    "startup_clean":     "geometric_sans",
    "editorial_magazine":"editorial_serif",
    "tech_futurist":     "tech_sans",
    "creative_studio":   "expressive_display",
    "brutalist":         "grotesque_sans",
    "organic_natural":   "humanist_sans",
    "playful_brand":     "rounded_sans",
    "corporate_pro":     "corporate_sans",
    "premium_craft":     "artisan_serif",
    "bold_challenger":   "condensed_sans",
    "warm_human":        "soft_sans",
}

_ARCHETYPE_WEIGHT: Dict[str, str] = {
    "luxury_minimal":    "light",
    "startup_clean":     "medium",
    "editorial_magazine":"bold",
    "tech_futurist":     "medium",
    "creative_studio":   "bold",
    "brutalist":         "black",
    "organic_natural":   "regular",
    "playful_brand":     "bold",
    "corporate_pro":     "medium",
    "premium_craft":     "regular",
    "bold_challenger":   "black",
    "warm_human":        "regular",
}


def get_typography_style(archetype: str) -> str:
    return _ARCHETYPE_TYPOGRAPHY.get(archetype, "geometric_sans")


def get_wordmark_weight(archetype: str) -> str:
    return _ARCHETYPE_WEIGHT.get(archetype, "medium")
