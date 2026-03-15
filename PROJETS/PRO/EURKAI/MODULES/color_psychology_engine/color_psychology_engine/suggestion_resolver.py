"""
color_psychology_engine.suggestion_resolver
─────────────────────────────────────────────
Point d'entrée principal. Orchestre weighting_engine et produit
un ColorRecommendation prêt à être passé à palette_generator.

Logique :
  1. Instancier ColorScoreAggregator
  2. Nourrir avec chaque signal (industry, values, tone, tags, audience)
  3. Ajouter exploration (3%)
  4. Résoudre temperature, saturation, contrast_style
  5. Retourner ColorRecommendation

contrast_style est dérivé de la combinaison saturation + temperature :
  vivid + cool  → dramatic
  high          → high
  low + warm    → soft
  low + cool    → clean
  sinon         → balanced
"""

from __future__ import annotations

from .schemas import PsychologyInput, ColorRecommendation
from .weighting_engine import ColorScoreAggregator


_SAT_CONTRAST_MAP: dict[tuple, str] = {
    ("vivid",  "cool"):    "dramatic",
    ("vivid",  "warm"):    "dramatic",
    ("vivid",  "neutral"): "high",
    ("high",   "cool"):    "high",
    ("high",   "warm"):    "high",
    ("high",   "neutral"): "high",
    ("low",    "warm"):    "soft",
    ("low",    "cool"):    "clean",
    ("low",    "neutral"): "clean",
    ("medium", "cool"):    "balanced",
    ("medium", "warm"):    "balanced",
    ("medium", "neutral"): "balanced",
}

_EMOTION_LABELS: dict[str, str] = {
    "trust":      "trust",
    "energy":     "energy",
    "innovation": "innovation",
    "nature":     "nature",
    "premium":    "premium",
    "luxury":     "luxury",
    "playful":    "playful",
    "calm":       "calm",
    "elegance":   "elegance",
}


def resolve(input_data: PsychologyInput) -> ColorRecommendation:
    """
    Génère une ColorRecommendation depuis un PsychologyInput.
    """
    agg = ColorScoreAggregator()

    # Industry (40%)
    if input_data.industry:
        agg.add_industry(input_data.industry, weight=0.40)

    # Brand values (30% réparti entre les valeurs)
    if input_data.brand_values:
        w_per_value = 0.30 / max(len(input_data.brand_values), 1)
        for value in input_data.brand_values:
            agg.add_brand_value(value, weight=w_per_value)

    # Tone (20%)
    if input_data.tone:
        agg.add_tone(input_data.tone, weight=0.20)

    # Style tags (7% réparti)
    if input_data.style_tags:
        w_per_tag = 0.07 / max(len(input_data.style_tags), 1)
        agg.add_style_tags(input_data.style_tags, weight_per_tag=w_per_tag)

    # Audience (modificateur)
    if input_data.target_audience:
        agg.add_audience(input_data.target_audience)

    # Exploration (3%)
    agg.add_exploration(weight=0.03)

    # Résolution
    temperature  = agg.resolve_temperature()
    saturation   = agg.resolve_saturation()
    contrast_style = _SAT_CONTRAST_MAP.get((saturation, temperature), "balanced")

    # Dominant emotion : première brand_value reconnue, sinon tone
    dominant = None
    for v in (input_data.brand_values or []):
        if v.lower() in _EMOTION_LABELS:
            dominant = _EMOTION_LABELS[v.lower()]
            break
    if not dominant and input_data.tone:
        dominant = input_data.tone.lower()

    return ColorRecommendation(
        preferred_colors=agg.top_preferred(n=4),
        accent_candidates=agg.top_accents(n=3),
        neutral_candidates=agg.top_neutrals(n=3),
        avoid_colors=agg.top_avoid(n=4),
        saturation_level=saturation,
        contrast_style=contrast_style,
        color_temperature=temperature,
        dominant_emotion=dominant,
        score_breakdown=agg.score_breakdown,
        confidence=agg.confidence,
    )
