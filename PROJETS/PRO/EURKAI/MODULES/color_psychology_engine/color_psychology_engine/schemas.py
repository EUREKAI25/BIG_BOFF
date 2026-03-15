"""
color_psychology_engine.schemas
─────────────────────────────────
Types de données du module.
Outputs = suggestions colorées sémantiques (noms, pas hex).
Ces suggestions biaisent palette_generator en aval.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PsychologyInput:
    industry:        Optional[str]   = None
    brand_values:    List[str]       = field(default_factory=list)
    tone:            Optional[str]   = None
    target_audience: Optional[str]   = None
    region:          Optional[str]   = None
    style_tags:      List[str]       = field(default_factory=list)


@dataclass
class ColorRecommendation:
    """
    Suggestions colorées sémantiques à destination de palette_generator.
    Toutes les valeurs sont des noms de couleurs (navy, gold, ivory...)
    ou des descripteurs (cool, warm, vivid).
    """
    preferred_colors:    List[str]         = field(default_factory=list)
    accent_candidates:   List[str]         = field(default_factory=list)
    neutral_candidates:  List[str]         = field(default_factory=list)
    avoid_colors:        List[str]         = field(default_factory=list)
    saturation_level:    str               = "medium"   # low / medium / high / vivid
    contrast_style:      str               = "balanced" # clean / balanced / high / dramatic
    color_temperature:   str               = "neutral"  # warm / neutral / cool
    dominant_emotion:    Optional[str]     = None
    score_breakdown:     dict              = field(default_factory=dict)
    confidence:          float             = 0.0        # 0..1
