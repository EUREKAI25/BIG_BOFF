"""
palette_generator.color_utils
───────────────────────────────
Fonctions de conversion et calcul HSL/RGB/Hex.
Pure Python stdlib — aucune dépendance externe.

Conventions :
  H = 0..360 (degrés)
  S = 0..1
  L = 0..1
  RGB = (0..255, 0..255, 0..255)
"""

from __future__ import annotations
import colorsys
import re
from typing import Tuple

from .schemas import ColorValue


# ─── Conversions ──────────────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Retourne (H 0..360, S 0..1, L 0..1)."""
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return h * 360, s, l


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """Entrée : H 0..360, S 0..1, L 0..1. Sortie : RGB 0..255."""
    r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
    return round(r * 255), round(g * 255), round(b * 255)


def hex_to_hsl(hex_color: str) -> Tuple[float, float, float]:
    return rgb_to_hsl(*hex_to_rgb(hex_color))


def hsl_to_hex(h: float, s: float, l: float) -> str:
    return rgb_to_hex(*hsl_to_rgb(h, s, l))


def is_valid_hex(value: str) -> bool:
    return bool(re.match(r'^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$', value))


def normalize_hex(value: str) -> str:
    """Normalise et valide un hex. Lève ValueError si invalide."""
    value = value.strip()
    if not value.startswith("#"):
        value = "#" + value
    if not is_valid_hex(value):
        raise ValueError(f"Couleur hex invalide : {value!r}")
    h = value.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()


# ─── Luminance relative (WCAG) ────────────────────────────────────────────────

def _linearize(c: float) -> float:
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(r: int, g: int, b: int) -> float:
    """Luminance relative WCAG 2.1 (0..1)."""
    return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Ratio de contraste WCAG entre deux couleurs hex."""
    l1 = relative_luminance(*hex_to_rgb(hex1))
    l2 = relative_luminance(*hex_to_rgb(hex2))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ─── Manipulation HSL ────────────────────────────────────────────────────────

def rotate_hue(hex_color: str, degrees: float) -> str:
    h, s, l = hex_to_hsl(hex_color)
    return hsl_to_hex((h + degrees) % 360, s, l)


def set_lightness(hex_color: str, lightness: float) -> str:
    h, s, _ = hex_to_hsl(hex_color)
    return hsl_to_hex(h, s, max(0.0, min(1.0, lightness)))


def set_saturation(hex_color: str, saturation: float) -> str:
    h, _, l = hex_to_hsl(hex_color)
    return hsl_to_hex(h, max(0.0, min(1.0, saturation)), l)


def tint(hex_color: str, factor: float) -> str:
    """Mélange avec blanc (factor 0..1 = pourcentage de blanc ajouté)."""
    r, g, b = hex_to_rgb(hex_color)
    r2 = round(r + (255 - r) * factor)
    g2 = round(g + (255 - g) * factor)
    b2 = round(b + (255 - b) * factor)
    return rgb_to_hex(r2, g2, b2)


def shade(hex_color: str, factor: float) -> str:
    """Mélange avec noir (factor 0..1 = pourcentage de noir ajouté)."""
    r, g, b = hex_to_rgb(hex_color)
    r2 = round(r * (1 - factor))
    g2 = round(g * (1 - factor))
    b2 = round(b * (1 - factor))
    return rgb_to_hex(r2, g2, b2)


def darken(hex_color: str, amount: float) -> str:
    """Réduit la luminosité HSL de `amount` (0..1)."""
    h, s, l = hex_to_hsl(hex_color)
    return hsl_to_hex(h, s, max(0.0, l - amount))


def lighten(hex_color: str, amount: float) -> str:
    """Augmente la luminosité HSL de `amount` (0..1)."""
    h, s, l = hex_to_hsl(hex_color)
    return hsl_to_hex(h, s, min(1.0, l + amount))


def desaturate(hex_color: str, amount: float) -> str:
    h, s, l = hex_to_hsl(hex_color)
    return hsl_to_hex(h, max(0.0, s - amount), l)


# ─── ColorValue factory ───────────────────────────────────────────────────────

def make_color(hex_color: str, name: str = None, role: str = None) -> ColorValue:
    hex_color = normalize_hex(hex_color)
    rgb = hex_to_rgb(hex_color)
    hsl = rgb_to_hsl(*rgb)
    return ColorValue(hex=hex_color, rgb=rgb, hsl=hsl, name=name, role=role)


# ─── Utilitaires ─────────────────────────────────────────────────────────────

def is_dark(hex_color: str) -> bool:
    return relative_luminance(*hex_to_rgb(hex_color)) < 0.18


def is_light(hex_color: str) -> bool:
    return relative_luminance(*hex_to_rgb(hex_color)) > 0.65


def best_text_color(bg_hex: str) -> str:
    """Retourne #111111 ou #F9F9F9 selon le fond."""
    return "#111111" if is_light(bg_hex) else "#F9F9F9"
