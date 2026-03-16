"""
theme_generator.theme_translation
───────────────────────────────────
Convertit un StyleDNA en ThemePreset compatible avec theme_generator.

C'est la couche clé qui relie le pipeline visuel au compilateur existant.
Déterministe : même StyleDNA → même ThemePreset.
"""

from __future__ import annotations
import colorsys
from typing import Optional

from .style_dna import StyleDNA
from .font_map import (
    get_display_font, get_body_font, get_accent_font, get_google_fonts_url,
    TONE_TO_PRESET, COMPLEXITY_TO_ANIMATION, RADIUS_OVERRIDE,
)


# ─── Color helpers ────────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_str(r: int, g: int, b: int) -> str:
    return f"rgb({r}, {g}, {b})"


def _hex_to_rgb_str(hex_color: str) -> str:
    return _rgb_to_str(*_hex_to_rgb(hex_color))


def _lighten(hex_color: str, amount: float = 0.12) -> str:
    """Éclaircit une couleur hex de `amount` (0-1) en HSL."""
    r, g, b = (_c / 255 for _c in _hex_to_rgb(hex_color))
    h, s, l = colorsys.rgb_to_hls(r, g, b)
    l = min(1.0, l + amount)
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(int(r2*255), int(g2*255), int(b2*255))


def _darken(hex_color: str, amount: float = 0.12) -> str:
    """Assombrit une couleur hex de `amount` (0-1) en HSL."""
    r, g, b = (_c / 255 for _c in _hex_to_rgb(hex_color))
    h, s, l = colorsys.rgb_to_hls(r, g, b)
    l = max(0.0, l - amount)
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(int(r2*255), int(g2*255), int(b2*255))


def _color_system_from_hex(base_hex: str) -> dict:
    """Génère primary ou secondary color_system depuis une couleur hex."""
    return {
        "base":  _hex_to_rgb_str(base_hex),
        "light": _hex_to_rgb_str(_lighten(base_hex, 0.12)),
        "dark":  _hex_to_rgb_str(_darken(base_hex, 0.12)),
    }


def _fallback_color(index: int, colors: list, fallbacks: list) -> str:
    """Retourne colors[index] si disponible, sinon fallbacks[index]."""
    if index < len(colors) and colors[index]:
        return colors[index]
    return fallbacks[index] if index < len(fallbacks) else fallbacks[0]


# ─── Traduction principale ────────────────────────────────────────────────────

_FALLBACK_DOMINANT = ["#667eea", "#764ba2", "#48bb78"]
_FALLBACK_NEUTRAL  = ["#ffffff", "#2d3748"]


def translate(style_dna: StyleDNA) -> dict:
    """
    Convertit un StyleDNA en ThemePreset consommable par ThemeGenerator.

    Returns: dict ThemePreset (compatible avec theme_generator.generate())
    """
    pp = style_dna.palette_profile
    tp = style_dna.typography_profile
    gp = style_dna.geometry_profile

    # ── Couleurs ─────────────────────────────────────────────────────────────
    primary_hex   = _fallback_color(0, pp.dominant, _FALLBACK_DOMINANT)
    secondary_hex = _fallback_color(1, pp.dominant, _FALLBACK_DOMINANT)

    # Si une couleur d'accent est définie, elle devient secondary
    if pp.accent:
        secondary_hex = pp.accent[0]

    color_system = {
        "primary":   _color_system_from_hex(primary_hex),
        "secondary": _color_system_from_hex(secondary_hex),
    }

    # ── Mode sombre ───────────────────────────────────────────────────────────
    mood = "dark" if style_dna.emotional_tone in ("raw", "tech") else None

    # ── Style preset ──────────────────────────────────────────────────────────
    style_preset_name = TONE_TO_PRESET.get(style_dna.emotional_tone, "flat")

    # ── Radius overrides (si la géométrie s'écarte du preset) ─────────────────
    style_overrides: dict = {}
    radius_key = gp.border_radius
    if radius_key in RADIUS_OVERRIDE:
        style_overrides["radius"] = RADIUS_OVERRIDE[radius_key]

    # ── Animation ─────────────────────────────────────────────────────────────
    animation_style = COMPLEXITY_TO_ANIMATION.get(style_dna.complexity_level, "subtle")

    # ── Typographie ───────────────────────────────────────────────────────────
    heading_font = get_display_font(tp.display)
    body_font    = get_body_font(tp.body)
    accent_font  = get_accent_font(tp.accent)

    google_fonts_url = get_google_fonts_url(heading_font, body_font, accent_font)

    # ── Assemblage ThemePreset ─────────────────────────────────────────────────
    preset: dict = {
        "color_system":       color_system,
        "style_preset_name":  style_preset_name,
        "animation_style":    animation_style,
        "font_family_headings": heading_font,
        "font_family_body":     body_font,
        "font_google_url":      google_fonts_url,
        "font_weights": {"normal": 400, "medium": 500, "bold": 700},
    }

    if mood:
        preset["mood"] = mood

    if style_overrides:
        preset["style_overrides"] = style_overrides

    # Méta (non utilisé par le generator mais utile pour debug)
    preset["_source"] = {
        "emotional_tone":   style_dna.emotional_tone,
        "complexity_level": style_dna.complexity_level,
        "aesthetic_tags":   style_dna.aesthetic_tags,
        "source_type":      style_dna.source_type,
    }

    return preset
