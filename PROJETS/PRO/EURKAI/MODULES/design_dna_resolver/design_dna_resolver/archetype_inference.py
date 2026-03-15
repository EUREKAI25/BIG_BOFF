"""
design_dna_resolver.archetype_inference
────────────────────────────────────────
Infère le StyleArchetype depuis les signaux du brief.

Archetypes disponibles :
  luxury_minimal      → luxe, premium, épuré, noir/or
  startup_clean       → tech/saas, moderne, clean, géométrique
  editorial_magazine  → fashion/media, bold, haute-contraste, typographique
  tech_futurist       → gaming/cyber, dark, néon, futuriste
  creative_studio     → agence créative, vibrant, expressif, asymétrique
  brutalist           → art/architecture, brut, monochrome, fort contraste
  organic_natural     → eco/wellness, terres, chaud, organique
  playful_brand       → kids/food/B2C, vif, arrondi, joyeux
  corporate_pro       → finance/B2B/conseil, neutre, structuré, professionnel
  premium_craft       → artisan/gastronomie/luxe accessible, chaud, riche, textures
  bold_challenger     → disruptif, sport/energy/startup audacieuse, contraste maximal
  warm_human          → nonprofit/santé/communauté, chaleureux, accessible

Algorithme : score par archétype, somme des signaux, retourne le top.
"""

from __future__ import annotations
from collections import defaultdict

from .schemas import BriefInput


# ─── Profils d'archétype ─────────────────────────────────────────────────────

# Chaque archétype pondère ses signaux déclencheurs.
# Format : {signal_type: {value: score}}

_ARCHETYPE_SIGNALS: dict[str, dict] = {

    "luxury_minimal": {
        "industry":    {"luxury": 3.0, "fashion": 1.5, "beauty": 1.5, "real_estate": 1.0},
        "tone":        {"luxury": 3.0, "premium": 2.5, "modern_premium": 2.5, "elegant": 2.0, "minimal": 1.5},
        "values":      {"premium": 2.0, "luxury": 2.0, "elegance": 2.0, "exclusivity": 1.5, "sophistication": 1.5},
        "keywords":    {"exclusive": 2.0, "prestige": 2.0, "timeless": 1.5, "refined": 1.5, "gold": 1.0},
    },

    "startup_clean": {
        "industry":    {"technology": 2.5, "saas": 3.0, "fintech": 2.0},
        "tone":        {"modern": 2.0, "modern_premium": 1.5, "minimal": 1.5, "tech": 2.0, "professional": 1.0},
        "values":      {"innovation": 2.0, "efficiency": 2.0, "simplicity": 1.5, "trust": 1.0},
        "keywords":    {"clean": 2.0, "digital": 2.0, "platform": 1.5, "dashboard": 1.5, "saas": 1.5, "app": 1.5},
    },

    "editorial_magazine": {
        "industry":    {"fashion": 3.0, "beauty": 2.0, "luxury": 1.5, "travel": 1.5},
        "tone":        {"editorial": 3.0, "bold": 2.0, "elegant": 1.5},
        "values":      {"elegance": 1.5, "bold": 2.0, "sophistication": 1.5},
        "keywords":    {"editorial": 2.5, "fashion": 2.0, "magazine": 2.5, "photography": 1.5, "campaign": 1.5},
    },

    "tech_futurist": {
        "industry":    {"gaming": 3.0, "technology": 2.0, "fintech": 1.5},
        "tone":        {"tech": 2.5, "dark": 2.5, "bold": 1.5, "vibrant": 1.5},
        "values":      {"innovation": 2.0, "disruption": 2.5, "futurism": 3.0, "energy": 1.5},
        "keywords":    {"neon": 2.0, "cyber": 2.5, "futur": 2.0, "dark": 2.0, "electric": 2.0, "metaverse": 2.0},
    },

    "creative_studio": {
        "industry":    {"technology": 1.0, "education": 1.0},
        "tone":        {"vibrant": 2.5, "creative": 2.5, "bold": 1.5, "playful": 1.5},
        "values":      {"creativity": 3.0, "expression": 2.5, "innovation": 1.5},
        "keywords":    {"creative": 2.5, "studio": 2.5, "design": 2.0, "agency": 2.0, "colorful": 2.0, "expressive": 2.0},
    },

    "brutalist": {
        "industry":    {},
        "tone":        {"bold": 2.5, "editorial": 2.0, "dark": 1.5},
        "values":      {"bold": 2.5, "rawness": 3.0, "honesty": 2.0},
        "keywords":    {"brutalist": 3.0, "raw": 2.0, "contrast": 2.0, "minimal": 1.5, "architecture": 2.0, "art": 1.5},
    },

    "organic_natural": {
        "industry":    {"eco": 3.0, "wellness": 3.0, "food": 1.5, "food_premium": 2.0},
        "tone":        {"organic": 3.0, "warm": 2.0, "natural": 3.0, "artisan": 2.0},
        "values":      {"nature": 3.0, "sustainability": 3.0, "organic": 2.5, "authenticity": 2.0},
        "keywords":    {"natural": 2.5, "organic": 2.5, "green": 2.0, "eco": 2.5, "earth": 2.0, "plant": 1.5},
    },

    "playful_brand": {
        "industry":    {"kids": 3.0, "food": 2.0, "education": 2.0, "gaming": 1.5},
        "tone":        {"playful": 3.0, "fun": 3.0, "vibrant": 2.0, "warm": 1.5},
        "values":      {"playful": 3.0, "fun": 2.5, "energy": 1.5, "community": 1.5},
        "keywords":    {"fun": 2.5, "playful": 2.5, "colorful": 2.0, "joyful": 2.0, "kids": 2.0, "bright": 1.5},
    },

    "corporate_pro": {
        "industry":    {"finance": 3.0, "real_estate": 2.0, "healthcare": 1.5},
        "tone":        {"professional": 3.0, "trustworthy": 2.5, "modern": 1.0},
        "values":      {"trust": 2.5, "stability": 2.5, "authority": 2.0, "reliability": 2.0},
        "keywords":    {"corporate": 2.5, "professional": 2.0, "b2b": 2.0, "enterprise": 2.5, "consulting": 2.0},
    },

    "premium_craft": {
        "industry":    {"food_premium": 3.0, "luxury": 2.0, "beauty": 1.5, "travel": 1.5},
        "tone":        {"artisan": 3.0, "premium": 2.0, "warm": 1.5, "organic": 1.5},
        "values":      {"premium": 2.0, "craft": 3.0, "quality": 2.5, "authenticity": 2.5},
        "keywords":    {"artisan": 2.5, "craft": 2.5, "handmade": 2.0, "quality": 2.0, "gourmet": 2.5, "heritage": 2.0},
    },

    "bold_challenger": {
        "industry":    {"sport": 3.0, "gaming": 2.0, "fintech": 1.5},
        "tone":        {"bold": 3.0, "vibrant": 2.0, "dark": 1.5},
        "values":      {"energy": 2.5, "bold": 3.0, "disruption": 2.5, "dynamic": 2.5},
        "keywords":    {"bold": 2.5, "challenger": 2.5, "disruption": 2.5, "sport": 2.0, "athlete": 2.0, "power": 2.0},
    },

    "warm_human": {
        "industry":    {"nonprofit": 3.0, "healthcare": 2.0, "wellness": 2.0, "education": 1.5},
        "tone":        {"warm": 3.0, "friendly": 2.5, "trustworthy": 1.5},
        "values":      {"warmth": 3.0, "community": 3.0, "care": 3.0, "empathy": 3.0, "human": 2.5},
        "keywords":    {"community": 2.5, "care": 2.5, "human": 2.0, "people": 2.0, "accessible": 2.0, "social": 2.0},
    },
}


def infer_archetype(brief: BriefInput) -> tuple[str, float, dict]:
    """
    Retourne (archetype_name, confidence, score_breakdown).
    confidence = score_winner / max_possible * 100 (normalisé 0..1)
    """
    scores: dict[str, float] = defaultdict(float)

    for archetype, signals in _ARCHETYPE_SIGNALS.items():
        # Industry
        if brief.industry:
            scores[archetype] += signals["industry"].get(brief.industry, 0.0)

        # Tone
        if brief.tone:
            scores[archetype] += signals["tone"].get(brief.tone, 0.0)

        # Brand values
        for val in brief.brand_values:
            scores[archetype] += signals["values"].get(val, 0.0)

        # Keywords + style_tags (poids réduit)
        for kw in brief.keywords + brief.style_tags:
            kw_l = kw.lower()
            scores[archetype] += signals["keywords"].get(kw_l, 0.0) * 0.5

    if not scores or max(scores.values()) == 0:
        return "startup_clean", 0.3, {}

    winner = max(scores, key=lambda k: scores[k])
    total = sum(scores.values())
    confidence = min(1.0, scores[winner] / max(total, 1) * 3)

    breakdown = {k: round(v, 2) for k, v in sorted(scores.items(), key=lambda x: -x[1])[:5]}
    return winner, round(confidence, 2), breakdown
