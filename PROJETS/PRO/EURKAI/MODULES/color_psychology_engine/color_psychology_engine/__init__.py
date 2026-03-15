"""
color_psychology_engine
────────────────────────
Module EURKAI standalone — recommandations colorées basées sur
la psychologie des couleurs, les conventions sectorielles et les valeurs de marque.

Zero LLM, zero dépendance externe, pur Python.

Usage :
    from color_psychology_engine import get_color_recommendation
    from color_psychology_engine.schemas import PsychologyInput

    rec = get_color_recommendation(PsychologyInput(
        industry="finance",
        brand_values=["trust", "innovation"],
        tone="premium",
    ))
    print(rec.preferred_colors)  # ["navy", "deep_blue", "indigo", ...]
"""

from .schemas import PsychologyInput, ColorRecommendation
from .suggestion_resolver import resolve as get_color_recommendation
from .industry_color_map import get_industry_profile, list_industries
from .emotion_color_map import get_emotion_profile, get_tone_profile

__version__ = "0.1.0"

__all__ = [
    "PsychologyInput",
    "ColorRecommendation",
    "get_color_recommendation",
    "get_industry_profile",
    "list_industries",
    "get_emotion_profile",
    "get_tone_profile",
]
