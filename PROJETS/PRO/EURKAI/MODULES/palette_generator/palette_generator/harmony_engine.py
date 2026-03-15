"""
palette_generator.harmony_engine
──────────────────────────────────
Génère les palettes d'harmonie chromatique depuis une couleur de base.
Algorithmes HSL purs — aucune dépendance externe.

Harmonies supportées :
  monochromatic, analogous, complementary,
  split_complementary, triadic, tetradic
"""

from __future__ import annotations
from typing import List

from .schemas import ColorValue, HarmonyType, Palette
from .color_utils import (
    make_color, rotate_hue, set_lightness, set_saturation,
    hex_to_hsl, hsl_to_hex, darken, lighten, desaturate
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _neutralize(hex_color: str, n: int = 3) -> List[ColorValue]:
    """Génère n neutres (faible saturation) depuis la teinte de base."""
    h, s, l = hex_to_hsl(hex_color)
    result = []
    for i, (sat, light, lbl) in enumerate([
        (0.06, 0.96, "neutral_lightest"),
        (0.05, 0.88, "neutral_light"),
        (0.08, 0.60, "neutral_mid"),
        (0.10, 0.25, "neutral_dark"),
        (0.06, 0.10, "neutral_darkest"),
    ][:n]):
        result.append(make_color(hsl_to_hex(h, sat, light), name=lbl, role="neutral"))
    return result


def _build_palette(
    harmony: str,
    primary_hexes: List[str],
    secondary_hexes: List[str],
    accent_hexes: List[str],
    base_hex: str,
) -> Palette:
    primary   = [make_color(h, role="primary")   for h in primary_hexes]
    secondary = [make_color(h, role="secondary") for h in secondary_hexes]
    accent    = [make_color(h, role="accent")    for h in accent_hexes]
    neutral   = _neutralize(base_hex, n=4)
    return Palette(
        harmony=harmony,
        primary=primary,
        secondary=secondary,
        accent=accent,
        neutral=neutral,
    )


# ─── Harmonies ───────────────────────────────────────────────────────────────

def monochromatic(base_hex: str) -> Palette:
    h, s, l = hex_to_hsl(base_hex)
    primaries = [
        hsl_to_hex(h, s, 0.85),
        hsl_to_hex(h, s, 0.65),
        base_hex,
        hsl_to_hex(h, s, 0.35),
        hsl_to_hex(h, s, 0.18),
    ]
    secondaries = [
        hsl_to_hex(h, max(0, s - 0.15), 0.75),
        hsl_to_hex(h, max(0, s - 0.15), 0.50),
    ]
    accents = [
        hsl_to_hex(h, min(1, s + 0.15), 0.60),
    ]
    return _build_palette(HarmonyType.MONOCHROMATIC.value, primaries, secondaries, accents, base_hex)


def analogous(base_hex: str, spread: float = 30.0) -> Palette:
    primaries = [
        rotate_hue(base_hex, -spread),
        base_hex,
        rotate_hue(base_hex, spread),
    ]
    secondaries = [lighten(p, 0.15) for p in primaries[:2]]
    accents = [darken(primaries[1], 0.12)]
    return _build_palette(HarmonyType.ANALOGOUS.value, primaries, secondaries, accents, base_hex)


def complementary(base_hex: str) -> Palette:
    comp = rotate_hue(base_hex, 180)
    h, s, l = hex_to_hsl(base_hex)
    primaries = [
        base_hex,
        hsl_to_hex(h, s, max(0.1, l - 0.12)),
        hsl_to_hex(h, s, min(0.95, l + 0.12)),
    ]
    secondaries = [
        comp,
        lighten(comp, 0.15),
    ]
    accents = [darken(comp, 0.10)]
    return _build_palette(HarmonyType.COMPLEMENTARY.value, primaries, secondaries, accents, base_hex)


def split_complementary(base_hex: str) -> Palette:
    split1 = rotate_hue(base_hex, 150)
    split2 = rotate_hue(base_hex, 210)
    primaries = [base_hex, lighten(base_hex, 0.12), darken(base_hex, 0.12)]
    secondaries = [split1, lighten(split1, 0.15)]
    accents = [split2, darken(split2, 0.10)]
    return _build_palette(HarmonyType.SPLIT_COMPLEMENTARY.value, primaries, secondaries, accents, base_hex)


def triadic(base_hex: str) -> Palette:
    tri1 = rotate_hue(base_hex, 120)
    tri2 = rotate_hue(base_hex, 240)
    primaries = [base_hex, lighten(base_hex, 0.15)]
    secondaries = [tri1, lighten(tri1, 0.15)]
    accents = [tri2, darken(tri2, 0.10)]
    return _build_palette(HarmonyType.TRIADIC.value, primaries, secondaries, accents, base_hex)


def tetradic(base_hex: str) -> Palette:
    tet1 = rotate_hue(base_hex, 90)
    tet2 = rotate_hue(base_hex, 180)
    tet3 = rotate_hue(base_hex, 270)
    primaries = [base_hex, darken(base_hex, 0.10)]
    secondaries = [tet1, lighten(tet1, 0.12)]
    accents = [tet2, tet3]
    return _build_palette(HarmonyType.TETRADIC.value, primaries, secondaries, accents, base_hex)


def minimal(base_hex: str) -> Palette:
    """Palette épurée : 1 couleur vive + neutres."""
    h, s, l = hex_to_hsl(base_hex)
    primaries = [base_hex]
    secondaries = [hsl_to_hex(h, max(0, s - 0.20), 0.92)]
    accents = [hsl_to_hex(h, min(1, s + 0.10), l)]
    return _build_palette("minimal", primaries, secondaries, accents, base_hex)


# ─── Dispatch ─────────────────────────────────────────────────────────────────

_HARMONY_FN = {
    HarmonyType.MONOCHROMATIC:       monochromatic,
    HarmonyType.ANALOGOUS:           analogous,
    HarmonyType.COMPLEMENTARY:       complementary,
    HarmonyType.SPLIT_COMPLEMENTARY: split_complementary,
    HarmonyType.TRIADIC:             triadic,
    HarmonyType.TETRADIC:            tetradic,
}


def generate_all_harmonies(base_hex: str) -> dict[str, Palette]:
    """Génère toutes les harmonies depuis une couleur de base."""
    result = {}
    for harmony_type, fn in _HARMONY_FN.items():
        result[harmony_type.value] = fn(base_hex)
    result["minimal"] = minimal(base_hex)
    return result
