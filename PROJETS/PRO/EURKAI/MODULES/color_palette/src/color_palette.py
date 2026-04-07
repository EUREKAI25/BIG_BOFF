"""
color_palette.py — EURKAI Color Palette Engine

Génère un système de couleurs cohérent, accessible et contextuel.

Garanties :
    - Toutes les couleurs dérivent d'une base hue unique
    - WCAG AA minimum sur text_primary / text_secondary
    - Aucun rôle dupliqué (text ≠ background)
    - Zéro aléatoire — même input → même output

Input  : VisualIntent (produit par visual_intent_engine)
Output : Palette — schéma JSON strict

Usage :
    from color_palette import generate_palette

    palette = generate_palette(visual_intent)
"""

from __future__ import annotations

import colorsys
import re
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# COLOR MATH — HSL ↔ Hex, Luminance, Contrast Ratio (WCAG 2.1)
# ─────────────────────────────────────────────────────────────────────────────

_HEX_RE = re.compile(r"^#[0-9a-f]{6}$")


def _is_valid_hex(color: str) -> bool:
    return isinstance(color, str) and bool(_HEX_RE.match(color.lower()))


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    """h: 0–360, s: 0–100, l: 0–100 → #rrggbb. colorsys uses HLS order."""
    r, g, b = colorsys.hls_to_rgb(
        (h % 360) / 360.0,
        max(0.0, min(1.0, l / 100.0)),
        max(0.0, min(1.0, s / 100.0)),
    )
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, round(r * 255))),
        max(0, min(255, round(g * 255))),
        max(0, min(255, round(b * 255))),
    )


def _luminance(hex_color: str) -> float:
    """Relative luminance — WCAG 2.1 §1.4.3."""
    h = hex_color.lstrip("#")
    def _lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (_lin(int(h[i:i+2], 16) / 255.0) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex1: str, hex2: str) -> float:
    l1, l2 = _luminance(hex1), _luminance(hex2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def _wcag_grade(ratio: float) -> str:
    if ratio >= 7.0:  return "AAA"
    if ratio >= 4.5:  return "AA"
    if ratio >= 3.0:  return "AA Large"
    return "FAIL"


def _fix_contrast(h: float, s: float, l: float,
                  bg: str, target: float, dark_mode: bool) -> str:
    """
    Ajuste la lightness jusqu'à atteindre le ratio cible.
    Dark mode → on monte la lightness. Light mode → on la descend.
    """
    step = 2.0 if dark_mode else -2.0
    cur = l
    for _ in range(60):
        col = _hsl_to_hex(h, s, cur)
        if _contrast_ratio(col, bg) >= target:
            return col
        cur = max(0.0, min(100.0, cur + step))
    return _hsl_to_hex(h, s, cur)


# ─────────────────────────────────────────────────────────────────────────────
# STYLE FAMILY PALETTES — palettes prédéfinies (priment sur tout)
# ─────────────────────────────────────────────────────────────────────────────

_STYLE_FAMILY_PALETTES: dict[str, dict] = {

    "editorial_luxury": {
        "primary":        "#f0ece0",   # warm cream
        "secondary":      "#c8b078",   # gold
        "accent":         "#a08840",   # deep gold
        "background":     "#090806",   # near-black warm
        "surface":        "#110f0a",
        "text_primary":   "#f0ece0",
        "text_secondary": "#8a7a60",
        "border":         "#2a2214",
        "states": {"success": "#4a8c4a", "warning": "#a07830", "error": "#8c3535"},
    },

    "brutalist": {
        "primary":        "#ffffff",
        "secondary":      "#aaaaaa",
        "accent":         "#ff2200",   # stark red
        "background":     "#000000",
        "surface":        "#0f0f0f",
        "text_primary":   "#ffffff",
        "text_secondary": "#999999",
        "border":         "#333333",
        "states": {"success": "#00cc44", "warning": "#ffbb00", "error": "#ff2200"},
    },

    "tech_minimal": {
        "primary":        "#1a73e8",   # blue
        "secondary":      "#5f6368",   # gray
        "accent":         "#1a73e8",
        "background":     "#ffffff",
        "surface":        "#f8f9fa",
        "text_primary":   "#202124",
        "text_secondary": "#5f6368",
        "border":         "#dadce0",
        "states": {"success": "#188038", "warning": "#f29900", "error": "#d93025"},
    },

    "experimental_grid": {
        "primary":        "#c026d3",   # fuchsia
        "secondary":      "#7c3aed",   # violet
        "accent":         "#f0abfc",   # light fuchsia
        "background":     "#03030a",
        "surface":        "#0d0a18",
        "text_primary":   "#f0e6ff",
        "text_secondary": "#8a7aaa",
        "border":         "#1e1430",
        "states": {"success": "#22c55e", "warning": "#f59e0b", "error": "#ef4444"},
    },

    "premium_brand": {
        "primary":        "#d4af6a",   # warm gold
        "secondary":      "#8b7355",
        "accent":         "#f5d78e",   # light gold
        "background":     "#0a0806",
        "surface":        "#141008",
        "text_primary":   "#f5f0e8",
        "text_secondary": "#8a7a60",
        "border":         "#2a2015",
        "states": {"success": "#4a8c4a", "warning": "#b08030", "error": "#8c3535"},
    },

    "bold_marketing": {
        "primary":        "#ff5533",   # vivid orange-red
        "secondary":      "#ff8c42",
        "accent":         "#ffdf00",   # yellow
        "background":     "#080808",
        "surface":        "#141414",
        "text_primary":   "#ffffff",
        "text_secondary": "#aaaaaa",
        "border":         "#2a2a2a",
        "states": {"success": "#22c55e", "warning": "#f59e0b", "error": "#ef4444"},
    },
}

# Style families qui utilisent un fond clair
_LIGHT_BG_STYLES = {"tech_minimal"}


# ─────────────────────────────────────────────────────────────────────────────
# BASE HUE — par objectif émotionnel
# ─────────────────────────────────────────────────────────────────────────────

_BASE_HUE: dict[str, float] = {
    "trust":      220.0,   # blue
    "excitement": 350.0,   # red-pink
    "desire":     340.0,   # warm pink
    "calm":       168.0,   # teal-green
    "curiosity":  268.0,   # purple
    "authority":  218.0,   # navy
    "default":    220.0,
}

_ACCENT_OFFSET: dict[str, float] = {
    "trust":      150.0,   # orange (split-complementary)
    "excitement":  30.0,   # yellow-orange
    "desire":      30.0,   # coral
    "calm":       180.0,   # pink (complementary)
    "curiosity":   90.0,   # yellow-green
    "authority":  150.0,   # orange
    "default":    150.0,
}


# ─────────────────────────────────────────────────────────────────────────────
# DARK / LIGHT MODE DETECTION
# ─────────────────────────────────────────────────────────────────────────────

_DARK_PRODUCTS  = {"gaming", "luxury", "event", "agency", "editorial"}
_LIGHT_PRODUCTS = {"saas", "finance", "health", "education", "food",
                   "travel", "ecommerce", "dating", "generic"}


def _is_dark_mode(visual_intent: dict, ctx: dict | None = None) -> bool:
    if ctx is None:
        ctx = visual_intent.get("context", {})
    product_type = ctx.get("product_type", "generic")
    brand_pos    = ctx.get("brand_positioning", "")
    style_family = visual_intent.get("art_direction", {}).get("style_family", "neutral")

    if style_family in _STYLE_FAMILY_PALETTES:
        return style_family not in _LIGHT_BG_STYLES
    if product_type in _LIGHT_PRODUCTS:
        return False
    if product_type in _DARK_PRODUCTS:
        return True
    return brand_pos in ("premium", "disruptive")


# ─────────────────────────────────────────────────────────────────────────────
# BRAND POSITIONING MODIFIERS
# ─────────────────────────────────────────────────────────────────────────────

_POSITIONING_MOD: dict[str, dict] = {
    "premium":    {"sat_delta": -18, "acc_offset": 30,  "acc_sat_delta": -15},
    "disruptive": {"sat_delta": +15, "acc_offset": 180, "acc_sat_delta": +10},
    "playful":    {"sat_delta": +12, "acc_offset": 60,  "acc_sat_delta": +15},
    "accessible": {"sat_delta":   0, "acc_offset": None, "acc_sat_delta":  0},
    "serious":    {"sat_delta": -15, "acc_offset": None, "acc_sat_delta": -10},
}


# ─────────────────────────────────────────────────────────────────────────────
# PALETTE BUILDERS — dark / light depuis hue
# ─────────────────────────────────────────────────────────────────────────────

def _build_dark(h: float, acc_h: float, sat: float, acc_sat: float) -> dict:
    bg  = _hsl_to_hex(h, sat * 0.18, 7.0)
    suf = _hsl_to_hex(h, sat * 0.14, 11.0)
    brd = _hsl_to_hex(h, sat * 0.22, 20.0)
    pri = _hsl_to_hex(h, min(100.0, sat * 0.85), 58.0)
    sec = _hsl_to_hex(h, min(100.0, sat * 0.50), 40.0)
    acc = _hsl_to_hex(acc_h, min(100.0, acc_sat), 64.0)
    tp  = _fix_contrast(h, 5.0, 94.0, bg,  4.5, True)
    ts  = _fix_contrast(h, 5.0, 58.0, suf, 4.5, True)
    return {"background": bg, "surface": suf, "border": brd,
            "primary": pri, "secondary": sec, "accent": acc,
            "text_primary": tp, "text_secondary": ts}


def _build_light(h: float, acc_h: float, sat: float, acc_sat: float) -> dict:
    bg  = _hsl_to_hex(h, sat * 0.08, 99.0)
    suf = _hsl_to_hex(h, sat * 0.12, 95.0)
    brd = _hsl_to_hex(h, sat * 0.18, 87.0)
    pri = _hsl_to_hex(h, min(100.0, sat * 0.85), 36.0)
    sec = _hsl_to_hex(h, min(100.0, sat * 0.45), 50.0)
    acc = _hsl_to_hex(acc_h, min(100.0, acc_sat), 38.0)
    tp  = _fix_contrast(h, 12.0, 9.0,  bg,  4.5, False)
    ts  = _fix_contrast(h,  8.0, 40.0, suf, 4.5, False)
    return {"background": bg, "surface": suf, "border": brd,
            "primary": pri, "secondary": sec, "accent": acc,
            "text_primary": tp, "text_secondary": ts}


def _build_states(dark_mode: bool) -> dict:
    if dark_mode:
        return {
            "success": _hsl_to_hex(142.0, 60.0, 48.0),
            "warning": _hsl_to_hex( 40.0, 88.0, 54.0),
            "error":   _hsl_to_hex(  0.0, 70.0, 56.0),
        }
    return {
        "success": _hsl_to_hex(142.0, 60.0, 28.0),
        "warning": _hsl_to_hex( 40.0, 85.0, 32.0),
        "error":   _hsl_to_hex(  0.0, 65.0, 36.0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# CONTRAST SCORES
# ─────────────────────────────────────────────────────────────────────────────

def _compute_contrast_scores(palette: dict) -> dict:
    """WCAG grades : text_primary/bg + text_secondary/surface."""
    tp = palette.get("text_primary",   "#ffffff")
    ts = palette.get("text_secondary", "#aaaaaa")
    bg = palette.get("background",     "#000000")
    su = palette.get("surface",        "#000000")
    return {
        "body_text":  _wcag_grade(_contrast_ratio(tp, bg)),
        "large_text": _wcag_grade(_contrast_ratio(ts, su)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION — schéma strict
# ─────────────────────────────────────────────────────────────────────────────

_COLOR_KEYS  = ("primary", "secondary", "accent", "background", "surface",
                "text_primary", "text_secondary", "border")
_STATE_KEYS  = ("success", "warning", "error")


def _validate_and_clean(palette: dict) -> dict:
    def _safe(val: Any, fallback: str = "#888888") -> str:
        return val.lower() if (_is_valid_hex(val)) else fallback

    result = {k: _safe(palette.get(k)) for k in _COLOR_KEYS}
    states = palette.get("states", {})
    result["states"] = {k: _safe(states.get(k)) for k in _STATE_KEYS}
    cs = palette.get("contrast_score", {})
    result["contrast_score"] = {
        "body_text":  str(cs.get("body_text",  "FAIL")),
        "large_text": str(cs.get("large_text", "FAIL")),
    }
    return result


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_palette(
    visual_intent: dict,
    context: dict | None = None,
) -> dict:
    """
    Génère un système de couleurs cohérent, accessible et contextuel.

    Args:
        visual_intent : dict produit par generate_visual_intent().
                        Champs utilisés : context.emotional_goal,
                        context.brand_positioning, context.product_type,
                        art_direction.style_family, art_direction.intensity.
        context       : dict optionnel — écrase visual_intent["context"] si fourni.

    Returns:
        dict strict conforme au schéma Palette.

    Garanties :
        - Toutes les valeurs sont des hex #rrggbb valides.
        - contrast_score.body_text ≥ WCAG AA (text_primary sur background).
        - contrast_score.large_text ≥ WCAG AA (text_secondary sur surface).
        - Tout dérive d'une base hue (sauf style family override).

    Logique de priorité :
        1. style_family connue → palette prédéfinie (prime sur tout)
        2. emotional_goal → base hue
        3. brand_positioning → ajustements saturation + offset accent
        4. product_type → dark vs light mode
    """
    ctx = context if context is not None else visual_intent.get("context", {})

    emotional_goal    = ctx.get("emotional_goal",    "default")
    brand_positioning = ctx.get("brand_positioning", "")
    style_family      = visual_intent.get("art_direction", {}).get("style_family", "neutral")

    # ── 1. Style family prédéfinie ────────────────────────────────────────────
    if style_family in _STYLE_FAMILY_PALETTES:
        base = dict(_STYLE_FAMILY_PALETTES[style_family])
        dark = style_family not in _LIGHT_BG_STYLES
        base.setdefault("states", _build_states(dark))
        base["contrast_score"] = _compute_contrast_scores(base)
        return _validate_and_clean(base)

    # ── 2. Base hue depuis emotional_goal ─────────────────────────────────────
    base_h   = _BASE_HUE.get(emotional_goal, _BASE_HUE["default"])
    offset_h = _ACCENT_OFFSET.get(emotional_goal, 150.0)
    base_sat = 72.0
    acc_sat  = 85.0

    # ── 3. Ajustements brand_positioning ─────────────────────────────────────
    if brand_positioning in _POSITIONING_MOD:
        mod      = _POSITIONING_MOD[brand_positioning]
        base_sat = max(0.0, min(100.0, base_sat + mod["sat_delta"]))
        acc_sat  = max(0.0, min(100.0, acc_sat  + mod["acc_sat_delta"]))
        if mod["acc_offset"] is not None:
            offset_h = float(mod["acc_offset"])

    acc_h = (base_h + offset_h) % 360.0

    # ── 4. Dark / light mode ──────────────────────────────────────────────────
    dark_mode = _is_dark_mode(visual_intent, ctx)
    palette   = (_build_dark if dark_mode else _build_light)(base_h, acc_h, base_sat, acc_sat)

    # ── 5. States ─────────────────────────────────────────────────────────────
    palette["states"] = _build_states(dark_mode)

    # ── 6. Contrast scores ────────────────────────────────────────────────────
    palette["contrast_score"] = _compute_contrast_scores(palette)

    return _validate_and_clean(palette)
