"""
color_psychology_engine.emotion_color_map
───────────────────────────────────────────
Mapping émotion / valeur de marque → couleurs associées.

Utilisé pour :
  - brand_values : ["trust", "innovation", "energy"]
  - tone : "premium", "playful", "bold"
  - style_tags : ["minimal", "tech", "organic"]
  - target_audience : influence le registre chromatique

Chaque signal porte :
  colors      : couleurs principales évoquées
  temperature : warm / neutral / cool
  saturation  : low / medium / high / vivid
  weight      : importance relative du signal (0..1)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class EmotionProfile:
    colors:      List[str]
    temperature: str          # warm / neutral / cool
    saturation:  str          # low / medium / high / vivid
    weight:      float = 1.0  # pertinence relative


# ─── Émotions & valeurs de marque ────────────────────────────────────────────

_EMOTION_MAP: dict[str, EmotionProfile] = {
    # Confiance & autorité
    "trust":         EmotionProfile(["navy", "deep_blue", "steel_blue"], "cool", "medium"),
    "authority":     EmotionProfile(["navy", "charcoal", "black"], "cool", "low"),
    "stability":     EmotionProfile(["navy", "slate_blue", "forest_green"], "cool", "medium"),
    "reliability":   EmotionProfile(["dark_blue", "forest_green", "charcoal"], "cool", "medium"),
    "security":      EmotionProfile(["deep_blue", "dark_green", "slate"], "cool", "low"),

    # Énergie & dynamisme
    "energy":        EmotionProfile(["red", "orange", "bright_yellow"], "warm", "vivid"),
    "dynamic":       EmotionProfile(["electric_blue", "red", "orange"], "neutral", "high"),
    "bold":          EmotionProfile(["black", "red", "electric_blue"], "neutral", "high"),
    "powerful":      EmotionProfile(["deep_red", "black", "charcoal"], "neutral", "medium"),
    "sport":         EmotionProfile(["red", "orange", "neon_yellow"], "warm", "vivid"),

    # Innovation & technologie
    "innovation":    EmotionProfile(["purple", "electric_blue", "cyan"], "cool", "high"),
    "disruption":    EmotionProfile(["electric_purple", "neon_blue", "magenta"], "cool", "vivid"),
    "futurism":      EmotionProfile(["cyan", "electric_blue", "silver"], "cool", "high"),
    "creativity":    EmotionProfile(["purple", "magenta", "coral"], "neutral", "high"),
    "intelligence":  EmotionProfile(["indigo", "deep_blue", "silver"], "cool", "medium"),

    # Nature & durabilité
    "nature":        EmotionProfile(["forest_green", "sage", "earth_brown"], "warm", "medium"),
    "sustainability": EmotionProfile(["sage_green", "olive", "terracotta"], "warm", "medium"),
    "organic":       EmotionProfile(["earth_brown", "sage", "warm_beige"], "warm", "low"),
    "freshness":     EmotionProfile(["mint", "sky_blue", "lime"], "cool", "medium"),
    "calm":          EmotionProfile(["soft_blue", "teal", "sage"], "cool", "low"),

    # Premium & luxe
    "premium":       EmotionProfile(["black", "gold", "deep_charcoal"], "neutral", "low"),
    "luxury":        EmotionProfile(["black", "ivory", "gold", "rose_gold"], "neutral", "low"),
    "exclusive":     EmotionProfile(["midnight", "platinum", "champagne"], "cool", "low"),
    "elegance":      EmotionProfile(["black", "ivory", "mauve"], "neutral", "low"),
    "sophistication": EmotionProfile(["deep_purple", "charcoal", "gold"], "neutral", "low"),

    # Chaleur & humanité
    "warmth":        EmotionProfile(["terracotta", "warm_orange", "coral"], "warm", "medium"),
    "care":          EmotionProfile(["soft_teal", "warm_pink", "lavender"], "warm", "low"),
    "community":     EmotionProfile(["warm_orange", "yellow", "green"], "warm", "medium"),
    "empathy":       EmotionProfile(["warm_pink", "lavender", "peach"], "warm", "low"),
    "human":         EmotionProfile(["terracotta", "warm_beige", "blush"], "warm", "medium"),

    # Jeu & créativité
    "playful":       EmotionProfile(["bright_yellow", "coral", "sky_blue", "lime"], "warm", "vivid"),
    "fun":           EmotionProfile(["orange", "hot_pink", "bright_yellow"], "warm", "vivid"),
    "friendly":      EmotionProfile(["sky_blue", "warm_yellow", "green"], "warm", "high"),
    "youthful":      EmotionProfile(["electric_blue", "lime", "magenta"], "neutral", "vivid"),
    "accessible":    EmotionProfile(["sky_blue", "green", "warm_yellow"], "neutral", "medium"),

    # Minimalisme & pureté
    "minimal":       EmotionProfile(["off_white", "light_gray", "near_black"], "neutral", "low"),
    "clean":         EmotionProfile(["white", "cool_gray", "sky_blue"], "cool", "low"),
    "clarity":       EmotionProfile(["white", "light_blue", "silver"], "cool", "low"),
    "pure":          EmotionProfile(["white", "ivory", "pale_gray"], "neutral", "low"),
    "simplicity":    EmotionProfile(["light_gray", "off_white", "charcoal"], "neutral", "low"),

    # Confiance médicale / scientifique
    "clinical":      EmotionProfile(["white", "sky_blue", "teal"], "cool", "low"),
    "scientific":    EmotionProfile(["deep_blue", "teal", "silver"], "cool", "medium"),
    "precision":     EmotionProfile(["steel_blue", "silver", "charcoal"], "cool", "medium"),
}

# ─── Tones ────────────────────────────────────────────────────────────────────

_TONE_MAP: dict[str, EmotionProfile] = {
    "premium":      EmotionProfile(["black", "gold", "ivory"], "neutral", "low", 0.9),
    "modern":       EmotionProfile(["electric_blue", "white", "charcoal"], "cool", "medium", 0.8),
    "playful":      EmotionProfile(["coral", "sky_blue", "yellow"], "warm", "vivid", 0.8),
    "professional": EmotionProfile(["navy", "cool_gray", "white"], "cool", "low", 0.8),
    "trustworthy":  EmotionProfile(["deep_blue", "forest_green", "gray"], "cool", "medium", 0.8),
    "bold":         EmotionProfile(["black", "red", "electric_blue"], "neutral", "high", 0.9),
    "elegant":      EmotionProfile(["black", "ivory", "mauve"], "neutral", "low", 0.9),
    "minimal":      EmotionProfile(["off_white", "charcoal", "light_gray"], "neutral", "low", 0.8),
    "warm":         EmotionProfile(["terracotta", "warm_orange", "cream"], "warm", "medium", 0.8),
    "cool":         EmotionProfile(["electric_blue", "silver", "white"], "cool", "medium", 0.8),
    "organic":      EmotionProfile(["sage", "earth_brown", "warm_ivory"], "warm", "low", 0.8),
    "vibrant":      EmotionProfile(["coral", "turquoise", "lime"], "warm", "vivid", 0.8),
    "dark":         EmotionProfile(["near_black", "charcoal", "deep_purple"], "cool", "low", 0.8),
    "pastel":       EmotionProfile(["blush", "lavender", "mint", "sky_blue"], "neutral", "low", 0.7),
    "editorial":    EmotionProfile(["black", "white", "deep_red"], "neutral", "high", 0.9),
    "tech":         EmotionProfile(["electric_blue", "cyan", "dark_gray"], "cool", "high", 0.8),
    "artisan":      EmotionProfile(["terracotta", "olive", "cream"], "warm", "medium", 0.7),
    "retro":        EmotionProfile(["mustard", "terracotta", "teal"], "warm", "medium", 0.7),
}

# ─── Audience ─────────────────────────────────────────────────────────────────

_AUDIENCE_MAP: dict[str, EmotionProfile] = {
    "professionals":    EmotionProfile(["navy", "charcoal", "cool_gray"], "cool", "low", 0.6),
    "b2b":              EmotionProfile(["navy", "deep_blue", "slate"], "cool", "medium", 0.6),
    "b2c":              EmotionProfile(["bright_blue", "orange", "green"], "neutral", "medium", 0.5),
    "millennials":      EmotionProfile(["electric_blue", "coral", "teal"], "neutral", "high", 0.6),
    "gen_z":            EmotionProfile(["neon", "electric_purple", "lime"], "neutral", "vivid", 0.7),
    "seniors":          EmotionProfile(["soft_blue", "warm_gray", "sage"], "warm", "low", 0.6),
    "kids":             EmotionProfile(["bright_red", "yellow", "sky_blue"], "warm", "vivid", 0.8),
    "women":            EmotionProfile(["blush", "rose", "mauve", "teal"], "warm", "medium", 0.5),
    "luxury_consumers": EmotionProfile(["gold", "black", "ivory"], "neutral", "low", 0.8),
    "mass_market":      EmotionProfile(["bright_blue", "red", "yellow"], "warm", "high", 0.5),
}

# ─── Style tags ───────────────────────────────────────────────────────────────

_STYLE_TAG_MAP: dict[str, EmotionProfile] = {
    "minimal":    EmotionProfile(["off_white", "light_gray", "charcoal"], "neutral", "low", 0.5),
    "tech":       EmotionProfile(["electric_blue", "cyan", "dark_gray"], "cool", "high", 0.6),
    "organic":    EmotionProfile(["sage", "earth_brown", "warm_ivory"], "warm", "low", 0.5),
    "geometric":  EmotionProfile(["deep_blue", "charcoal", "white"], "cool", "medium", 0.4),
    "retro":      EmotionProfile(["mustard", "terracotta", "teal"], "warm", "medium", 0.5),
    "editorial":  EmotionProfile(["black", "white", "deep_red"], "neutral", "high", 0.5),
    "dark":       EmotionProfile(["near_black", "deep_purple", "charcoal"], "cool", "medium", 0.6),
    "colorful":   EmotionProfile(["coral", "turquoise", "lime", "magenta"], "warm", "vivid", 0.6),
    "pastel":     EmotionProfile(["blush", "lavender", "mint"], "neutral", "low", 0.5),
    "bold":       EmotionProfile(["black", "electric_blue", "red"], "neutral", "high", 0.6),
    "luxurious":  EmotionProfile(["black", "gold", "ivory"], "neutral", "low", 0.7),
    "playful":    EmotionProfile(["coral", "sky_blue", "yellow"], "warm", "vivid", 0.6),
    "clean":      EmotionProfile(["white", "sky_blue", "silver"], "cool", "low", 0.5),
    "natural":    EmotionProfile(["forest_green", "sage", "terracotta"], "warm", "medium", 0.5),
}


# ─── Accesseurs ──────────────────────────────────────────────────────────────

def get_emotion_profile(value: str) -> EmotionProfile | None:
    key = value.lower().strip().replace(" ", "_").replace("-", "_")
    return _EMOTION_MAP.get(key)


def get_tone_profile(tone: str) -> EmotionProfile | None:
    key = tone.lower().strip().replace(" ", "_")
    return _TONE_MAP.get(key)


def get_audience_profile(audience: str) -> EmotionProfile | None:
    key = audience.lower().strip().replace(" ", "_").replace("-", "_")
    return _AUDIENCE_MAP.get(key)


def get_style_profile(tag: str) -> EmotionProfile | None:
    key = tag.lower().strip().replace(" ", "_")
    return _STYLE_TAG_MAP.get(key)
