"""
theme_generator.font_map
─────────────────────────
Mapping profils typographiques → polices concrètes.

Le système ne cherche jamais à identifier une police depuis une image.
Il détecte un profil sémantique, puis sélectionne une police dans une
bibliothèque interne.

Tous les profils de display, body et accent sont listés ici.
Extensible sans casser les thèmes existants.
"""

from __future__ import annotations
from typing import List, Optional


# ─── Bibliothèques de polices par profil ─────────────────────────────────────

DISPLAY_FONT_MAP: dict[str, List[str]] = {
    "bold_condensed_geometric": ["Anton", "Bebas Neue", "League Spartan"],
    "thin_elegant_serif":       ["Playfair Display", "Cormorant Garamond", "EB Garamond"],
    "grotesque_heavy":          ["Space Grotesk", "DM Sans", "Syne"],
    "editorial_contrast":       ["Fraunces", "Bodoni Moda", "Playfair Display"],
    "tech_mono":                ["JetBrains Mono", "Space Mono", "Fira Code"],
    "playful_rounded":          ["Nunito", "Fredoka", "Poppins"],
    "neutral_sans":             ["Inter", "Manrope", "DM Sans"],
    "warm_humanist":            ["Nunito Sans", "Raleway", "Josefin Sans"],
    "condensed_athletic":       ["Oswald", "Barlow Condensed", "Archivo Narrow"],
    "artisan_slab":             ["Zilla Slab", "Roboto Slab", "Arvo"],
}

BODY_FONT_MAP: dict[str, List[str]] = {
    "neutral_humanist_sans":    ["Inter", "Manrope", "Source Sans 3"],
    "warm_serif":               ["Lora", "Merriweather", "PT Serif"],
    "editorial_serif":          ["Playfair Display", "EB Garamond", "Cormorant Garamond"],
    "geometric_sans":           ["DM Sans", "Jost", "Outfit"],
    "readable_slab":            ["Roboto Slab", "Zilla Slab", "Crete Round"],
    "tech_mono":                ["JetBrains Mono", "Fira Code", "Space Mono"],
    "soft_rounded":             ["Nunito", "Poppins", "Quicksand"],
}

ACCENT_FONT_MAP: dict[str, List[str]] = {
    "handwritten_marker":   ["Caveat", "Kalam", "Patrick Hand"],
    "script_elegant":       ["Dancing Script", "Pacifico", "Great Vibes"],
    "display_italic":       ["Fraunces", "Cormorant Garamond"],
}

# ─── Tone → style preset ─────────────────────────────────────────────────────
# Mapping du ton émotionnel vers le style preset du theme_generator existant

TONE_TO_PRESET: dict[str, str] = {
    "premium":  "minimal",
    "calm":     "flat",
    "bold":     "bold",
    "playful":  "rounded",
    "raw":      "dark",
    "tech":     "dark",
    "warm":     "elevated",
    "fresh":    "rounded",
    "neutral":  "flat",
}

# ─── Complexity → animation style ────────────────────────────────────────────

COMPLEXITY_TO_ANIMATION: dict[str, str] = {
    "minimal":  "subtle",
    "moderate": "moderate",
    "rich":     "rich",
}

# ─── Geometry → radius overrides ─────────────────────────────────────────────
# Seulement les cas qui s'écartent du preset par défaut

RADIUS_OVERRIDE: dict[str, dict] = {
    "none":     {"sm": "0px",  "md": "0px",   "lg": "0px",   "xl": "0px"},
    "sharp":    {"sm": "2px",  "md": "4px",   "lg": "6px",   "xl": "8px"},
    "small":    {"sm": "4px",  "md": "6px",   "lg": "8px",   "xl": "12px"},
    # "medium" et "large" → laissé au style preset
    "circular": {"sm": "20px", "md": "40px",  "lg": "60px",  "xl": "9999px"},
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_display_font(profile: str) -> str:
    """Retourne la première police pour un profil display."""
    fonts = DISPLAY_FONT_MAP.get(profile) or DISPLAY_FONT_MAP["neutral_sans"]
    return fonts[0]


def get_body_font(profile: str) -> str:
    """Retourne la première police pour un profil body."""
    fonts = BODY_FONT_MAP.get(profile) or BODY_FONT_MAP["neutral_humanist_sans"]
    return fonts[0]


def get_accent_font(profile: Optional[str]) -> Optional[str]:
    """Retourne la première police accent, ou None."""
    if not profile:
        return None
    fonts = ACCENT_FONT_MAP.get(profile)
    return fonts[0] if fonts else None


def get_google_fonts_url(heading_font: str, body_font: str, accent_font: Optional[str] = None) -> str:
    """Génère l'URL Google Fonts pour les polices sélectionnées."""
    seen = {}
    for font, weights in [
        (heading_font, "400;700;900"),
        (body_font,    "400;500;700"),
    ]:
        if font not in seen:
            seen[font] = weights

    if accent_font and accent_font not in seen:
        seen[accent_font] = "400;700"

    parts = [
        f"family={f.replace(' ', '+')}:wght@{w}"
        for f, w in seen.items()
    ]
    return "https://fonts.googleapis.com/css2?" + "&".join(parts) + "&display=swap"
