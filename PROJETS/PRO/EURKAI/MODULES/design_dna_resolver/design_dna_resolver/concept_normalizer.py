"""
design_dna_resolver.concept_normalizer
────────────────────────────────────────
Normalise les concepts issus du brief vers des formes canoniques
utilisées dans les mappings des autres modules.

Exemples :
  "Fintech" → "fintech"
  "modern premium" → "modern_premium"
  "young professionals" → "young_professionals"
  "B2B" → "b2b"
"""

from __future__ import annotations
import re
from typing import Optional


# ─── Industries ───────────────────────────────────────────────────────────────

_INDUSTRY_NORMALIZE: dict[str, str] = {
    # Aliases → canonical
    "tech": "technology",
    "it": "technology",
    "software": "technology",
    "digital": "technology",
    "finance": "finance",
    "banking": "finance",
    "bank": "finance",
    "fintech": "fintech",
    "financial technology": "fintech",
    "health": "healthcare",
    "medical": "healthcare",
    "pharma": "healthcare",
    "pharmaceutique": "healthcare",
    "sante": "healthcare",
    "santé": "healthcare",
    "luxury": "luxury",
    "luxe": "luxury",
    "mode": "fashion",
    "fashion": "fashion",
    "clothing": "fashion",
    "food": "food",
    "restaurant": "food",
    "restauration": "food",
    "cuisine": "food",
    "saas": "saas",
    "b2b software": "saas",
    "eco": "eco",
    "green": "eco",
    "sustainable": "eco",
    "environnement": "eco",
    "environment": "eco",
    "education": "education",
    "learning": "education",
    "school": "education",
    "e-learning": "education",
    "sport": "sport",
    "fitness": "sport",
    "sports": "sport",
    "gaming": "gaming",
    "game": "gaming",
    "games": "gaming",
    "real estate": "real_estate",
    "immobilier": "real_estate",
    "realty": "real_estate",
    "beauty": "beauty",
    "cosmetics": "beauty",
    "cosmetique": "beauty",
    "cosmétique": "beauty",
    "kids": "kids",
    "children": "kids",
    "travel": "travel",
    "tourisme": "travel",
    "tourism": "travel",
    "nonprofit": "nonprofit",
    "ngo": "nonprofit",
    "association": "nonprofit",
    "wellness": "wellness",
}


# ─── Tones ────────────────────────────────────────────────────────────────────

_TONE_NORMALIZE: dict[str, str] = {
    "modern premium": "modern_premium",
    "modern_premium": "modern_premium",
    "premium modern": "modern_premium",
    "clean modern": "modern",
    "premium": "premium",
    "luxe": "premium",
    "luxury": "luxury",
    "playful": "playful",
    "fun": "playful",
    "ludique": "playful",
    "bold": "bold",
    "minimal": "minimal",
    "minimaliste": "minimal",
    "professional": "professional",
    "pro": "professional",
    "professionnel": "professional",
    "trustworthy": "trustworthy",
    "elegant": "elegant",
    "élégant": "elegant",
    "organic": "organic",
    "naturel": "organic",
    "natural": "organic",
    "vibrant": "vibrant",
    "editorial": "editorial",
    "dark": "dark",
    "tech": "tech",
    "modern": "modern",
    "warm": "warm",
    "cool": "cool",
    "retro": "retro",
    "rétro": "retro",
    "artisan": "artisan",
}


# ─── Audiences ────────────────────────────────────────────────────────────────

_AUDIENCE_NORMALIZE: dict[str, str] = {
    "young professionals": "young_professionals",
    "young_professionals": "young_professionals",
    "professionals": "professionals",
    "professionnels": "professionals",
    "b2b": "b2b",
    "business": "b2b",
    "b2c": "b2c",
    "consumers": "b2c",
    "millennials": "millennials",
    "gen z": "gen_z",
    "gen_z": "gen_z",
    "genz": "gen_z",
    "generation z": "gen_z",
    "seniors": "seniors",
    "kids": "kids",
    "enfants": "kids",
    "children": "kids",
    "women": "women",
    "femmes": "women",
    "luxury consumers": "luxury_consumers",
    "mass market": "mass_market",
    "grand public": "mass_market",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _slug(text: str) -> str:
    """Minuscules + underscores."""
    return re.sub(r"[\s\-]+", "_", text.lower().strip())


def _lookup(text: str, table: dict[str, str]) -> Optional[str]:
    key = text.lower().strip()
    if key in table:
        return table[key]
    # Essai avec slug
    slugged = _slug(key)
    return table.get(slugged, key)   # retourne le slug si non trouvé


# ─── Fonctions publiques ──────────────────────────────────────────────────────

def normalize_industry(value: str) -> str:
    return _lookup(value, _INDUSTRY_NORMALIZE)


def normalize_tone(value: str) -> str:
    return _lookup(value, _TONE_NORMALIZE)


def normalize_audience(value: str) -> str:
    return _lookup(value, _AUDIENCE_NORMALIZE)


def normalize_brand_value(value: str) -> str:
    """Normalise une valeur de marque en snake_case lowercase."""
    return _slug(value)
