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
    "finance":        ["bank", "banque", "finance", "fintech", "investment", "assurance", "insurance"],
    "healthcare":     ["health", "santé", "medical", "médical", "pharma", "clinic", "wellness"],
    "technology":     ["software", "logiciel", "app", "digital", "platform", "platforme"],
    "saas":           ["saas", "b2b software", "subscription", "dashboard", "workflow"],
    "b2b_enterprise": ["infrastructure", "data infrastructure", "enterprise", "b2b", "devops",
                       "developer tool", "developer tools", "engineering", "data platform",
                       "automation", "orchestration", "cto", "technical team", "engineers"],
    "media_editorial":["editorial", "magazine", "art book", "art books", "publication",
                       "publishing", "literary", "philosophy", "slow living", "culture",
                       "aesthetics", "fine art", "contemporary art", "art journal",
                       "revue", "photographie", "photography", "poetic"],
    "luxury":         ["luxury", "luxe", "premium", "haute couture", "prestige", "high-end"],
    "food":           ["food", "restaurant", "cuisine", "eat", "manger", "beverage", "drink"],
    "eco":            ["eco", "green", "sustainable", "durability", "environment", "nature"],
    "education":      ["education", "learning", "école", "school", "cours", "training"],
    "sport":          ["sport", "fitness", "athletic", "performance", "gym"],
    "gaming":         ["game", "gaming", "jeu", "play", "esport"],
    "nightlife_event":["nightlife", "club", "rave", "concert", "festival", "event", "music",
                       "performance", "immersive", "dj", "electronic", "underground"],
}

_VALUE_KEYWORDS = {
    "trust":       ["trust", "confiance", "reliable", "sécurité", "security"],
    "innovation":  ["innovation", "innovant", "cutting-edge", "disruptive", "nouveau"],
    "energy":      ["energy", "énergie", "dynamic", "dynamique", "bold"],
    "nature":      ["nature", "eco", "green", "organic", "naturel"],
    "premium":     ["premium", "luxe", "luxury", "exclusive", "haut de gamme"],
    "playful":     ["fun", "playful", "joyeux", "ludique", "colorful"],
    "minimal":     ["minimal", "simple", "clean", "épuré", "clarity"],
    "community":   ["community", "communauté", "social", "people", "humain"],
    "structured":  ["structured", "structuré", "systematic", "precise", "rigorous",
                    "reliable", "dependable", "swiss", "geometric", "grid"],
    "authority":   ["enterprise", "b2b", "cto", "engineering", "infrastructure",
                    "professional", "institutional"],
    "elegance":    ["elegant", "élégant", "refined", "timeless", "quiet", "slow living",
                    "intellectual", "aesthetic", "contemplative", "understated"],
    "boldness":    ["vibrant", "energetic", "immersive", "chaotic", "controlled", "bold",
                    "experimental", "expressive", "neon", "electric"],
}

# Mots déclenchés dans les clauses "avoid / éviter / ne pas" — signaux NÉGATIFS
_AVOID_TRIGGER_PHRASES = [
    r"avoid\s*[:\-–]?\s*(.+?)(?:\.|$)",
    r"éviter\s*[:\-–]?\s*(.+?)(?:\.|$)",
    r"ne pas\s*[:\-–]?\s*(.+?)(?:\.|$)",
    r"no\s+(.+?)(?:\.|$)",
    r"sans\s+(.+?)(?:\.|$)",
]
# Valeurs à supprimer si elles apparaissent dans une clause avoid
_AVOID_NEGATIVE_VALUES = {
    "playful": ["playful", "fun", "colorful", "friendly", "ludique", "joyeux"],
    "energy":  ["bright", "vibrant", "gradients", "gradient", "startup colors"],
    "premium": [],  # rarement négatif
}


def _extract_avoid_words(text: str) -> set[str]:
    """Extrait les mots présents dans des clauses 'avoid / éviter / ne pas'."""
    avoid_words: set[str] = set()
    for pattern in _AVOID_TRIGGER_PHRASES:
        for m in re.finditer(pattern, text.lower(), re.IGNORECASE):
            segment = m.group(1) if m.lastindex else m.group(0)
            avoid_words.update(re.findall(r"\b\w+\b", segment.lower()))
    return avoid_words


def _extract_from_text(text: str) -> BriefInput:
    """Extraction naïve par mots-clés depuis un texte libre."""
    text_lower = text.lower()
    words = set(re.findall(r"\b\w+\b", text_lower))

    # Mots dans les clauses "avoid" — à exclure des signaux positifs
    avoid_words = _extract_avoid_words(text)

    # Industrie — mots dans avoid ne comptent pas comme signaux industry positifs
    industry = None
    industry_scores: dict[str, int] = {}
    for ind, kws in _INDUSTRY_KEYWORDS.items():
        hits = sum(1 for kw in kws
                   if kw in text_lower and not any(aw in kw or kw == aw for aw in avoid_words))
        if hits:
            industry_scores[ind] = hits
    if industry_scores:
        industry = max(industry_scores, key=lambda k: industry_scores[k])

    # Valeurs — ignorer si le mot clé était dans une clause avoid
    brand_values = []
    for val, kws in _VALUE_KEYWORDS.items():
        matching = [kw for kw in kws if kw in text_lower]
        non_avoided = [kw for kw in matching if not any(aw in kw or kw in aw for aw in avoid_words)]
        if non_avoided:
            brand_values.append(val)

    # Supprimer les valeurs explicitement dans avoid
    for val, triggers in _AVOID_NEGATIVE_VALUES.items():
        if any(t in avoid_words for t in triggers):
            brand_values = [v for v in brand_values if v != val]

    # Keywords : mots significatifs (longueur > 4, non stopwords, non avoid)
    _STOPWORDS = {
        "the", "a", "an", "and", "or", "for", "to", "of", "in", "is",
        "that", "this", "with", "are", "our", "we", "will", "une", "un",
        "le", "la", "les", "des", "pour", "avec", "dans", "qui",
        "avoid", "éviter", "must", "should", "never", "everywhere",
    }
    keywords = [w for w in words
                if len(w) > 4 and w not in _STOPWORDS and w not in avoid_words][:10]

    return BriefInput(
        industry=industry,
        brand_values=brand_values[:6],
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
