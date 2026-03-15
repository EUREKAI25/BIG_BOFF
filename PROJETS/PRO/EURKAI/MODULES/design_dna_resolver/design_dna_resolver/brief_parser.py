"""
design_dna_resolver.brief_parser
──────────────────────────────────
Parse un brief en entrée (dict structuré ou texte libre)
et retourne un BriefInput normalisé.

Formats acceptés :
  • dict Python / JSON avec clés standard
  • texte libre (extraction par mots-clés)

Pour le texte libre, on extrait par correspondance de mots-clés
sans LLM : regex + lookup tables.
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Union

from .schemas import BriefInput
from .concept_normalizer import normalize_industry, normalize_tone, normalize_audience


# ─── Clés acceptées dans un dict structuré ───────────────────────────────────

_FIELD_ALIASES = {
    "industry":        ["industry", "secteur", "sector", "domain", "domaine"],
    "brand_values":    ["brand_values", "values", "valeurs", "core_values"],
    "tone":            ["tone", "ton", "voice", "positioning", "positionnement"],
    "target_audience": ["target_audience", "audience", "cible", "target", "users"],
    "keywords":        ["keywords", "mots_cles", "mots-clés", "tags", "descriptors"],
    "style_tags":      ["style_tags", "style", "visual_style", "design_style"],
    "project_name":    ["project_name", "name", "brand_name", "nom", "project"],
    "region":          ["region", "country", "pays", "locale", "market"],
}


def _find_key(data: dict, field: str) -> Optional[Any]:
    for alias in _FIELD_ALIASES.get(field, [field]):
        if alias in data:
            return data[alias]
    return None


def _to_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).lower().strip() for v in value if v]
    if isinstance(value, str):
        return [v.strip().lower() for v in re.split(r"[,;/]", value) if v.strip()]
    return []


# ─── Extraction depuis texte libre ───────────────────────────────────────────

# Industries détectables dans le texte
_INDUSTRY_KEYWORDS = {
    "finance": ["bank", "banque", "finance", "fintech", "investment", "assurance", "insurance"],
    "healthcare": ["health", "santé", "medical", "médical", "pharma", "clinic", "wellness"],
    "technology": ["tech", "software", "logiciel", "app", "digital", "platform", "platforme"],
    "saas": ["saas", "b2b software", "subscription", "dashboard", "workflow"],
    "luxury": ["luxury", "luxe", "premium", "haute couture", "prestige"],
    "food": ["food", "restaurant", "cuisine", "eat", "manger", "beverage", "drink"],
    "eco": ["eco", "green", "sustainable", "durability", "environment", "nature"],
    "education": ["education", "learning", "école", "school", "cours", "training"],
    "sport": ["sport", "fitness", "athletic", "performance", "gym"],
    "gaming": ["game", "gaming", "jeu", "play", "esport"],
}

_VALUE_KEYWORDS = {
    "trust": ["trust", "confiance", "reliable", "sécurité", "security"],
    "innovation": ["innovation", "innovant", "cutting-edge", "disruptive", "nouveau"],
    "energy": ["energy", "énergie", "dynamic", "dynamique", "bold"],
    "nature": ["nature", "eco", "green", "organic", "naturel"],
    "premium": ["premium", "luxe", "luxury", "exclusive", "haut de gamme"],
    "playful": ["fun", "playful", "joyeux", "ludique", "colorful"],
    "minimal": ["minimal", "simple", "clean", "épuré", "clarity"],
    "community": ["community", "communauté", "social", "people", "humain"],
}


def _extract_from_text(text: str) -> BriefInput:
    """Extraction naïve par mots-clés depuis un texte libre."""
    text_lower = text.lower()
    words = set(re.findall(r"\b\w+\b", text_lower))

    # Industrie
    industry = None
    for ind, kws in _INDUSTRY_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            industry = ind
            break

    # Valeurs
    brand_values = []
    for val, kws in _VALUE_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            brand_values.append(val)

    # Keywords : mots significatifs (longueur > 4, non stopwords)
    _STOPWORDS = {
        "the", "a", "an", "and", "or", "for", "to", "of", "in", "is",
        "that", "this", "with", "are", "our", "we", "will", "une", "un",
        "le", "la", "les", "des", "pour", "avec", "dans", "qui",
    }
    keywords = [w for w in words if len(w) > 4 and w not in _STOPWORDS][:10]

    return BriefInput(
        industry=industry,
        brand_values=brand_values[:4],
        keywords=keywords,
        raw_text=text,
    )


# ─── Point d'entrée ──────────────────────────────────────────────────────────

def parse_brief(brief: Union[str, Dict]) -> BriefInput:
    """
    Parse un brief (dict ou texte) en BriefInput normalisé.
    """
    if isinstance(brief, str):
        result = _extract_from_text(brief)
    else:
        industry_raw   = _find_key(brief, "industry")
        values_raw     = _find_key(brief, "brand_values")
        tone_raw       = _find_key(brief, "tone")
        audience_raw   = _find_key(brief, "target_audience")
        keywords_raw   = _find_key(brief, "keywords")
        style_raw      = _find_key(brief, "style_tags")
        name_raw       = _find_key(brief, "project_name")
        region_raw     = _find_key(brief, "region")

        result = BriefInput(
            project_name=str(name_raw).strip() if name_raw else None,
            industry=str(industry_raw).lower().strip() if industry_raw else None,
            brand_values=_to_list(values_raw),
            tone=str(tone_raw).lower().strip() if tone_raw else None,
            target_audience=str(audience_raw).lower().strip() if audience_raw else None,
            keywords=_to_list(keywords_raw),
            style_tags=_to_list(style_raw),
            region=str(region_raw).lower().strip() if region_raw else None,
        )

    # Normalisation des concepts
    if result.industry:
        result.industry = normalize_industry(result.industry)
    if result.tone:
        result.tone = normalize_tone(result.tone)
    if result.target_audience:
        result.target_audience = normalize_audience(result.target_audience)

    return result
