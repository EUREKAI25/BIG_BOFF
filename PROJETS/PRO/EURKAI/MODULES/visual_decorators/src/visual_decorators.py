"""
visual_decorators.py — EURKAI Visual Decorators Engine

Génère la couche de signature visuelle décorative d'une page.
Cohérente, intentionnelle, non aléatoire.

Ce module est sur la COHÉRENCE SYSTÉMIQUE, pas sur le rendu.
Il définit : quels éléments décoratifs, dans quel style, à quelle intensité.

Chaque élément doit être réutilisé uniformément à travers la page.

Input  : VisualIntent (produit par visual_intent_engine)
Output : Decorators — schéma JSON strict

Usage :
    from visual_decorators import generate_visual_decorators

    decorators = generate_visual_decorators(visual_intent)
"""

from __future__ import annotations

import json
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# VALID ENUM VALUES — validation stricte
# ─────────────────────────────────────────────────────────────────────────────

_VALID_BORDER_STYLE    = {"none", "solid", "dashed", "double", "glow", "dotted"}
_VALID_BORDER_THICKNESS = {"none", "thin", "medium", "thick"}
_VALID_BORDER_RADIUS   = {"none", "small", "medium", "large", "full"}
_VALID_BORDER_PATTERN  = {"none", "uniform", "top-only", "accent", "frame"}

_VALID_DIVIDER_TYPE    = {"none", "line", "space", "ornament", "gradient", "zigzag"}
_VALID_DIVIDER_STYLE   = {"none", "minimal", "bold", "decorative", "subtle"}

_VALID_ICON_STYLE      = {"line", "filled", "duotone", "outline-filled"}
_VALID_ICON_STROKE     = {"thin", "medium", "thick"}
_VALID_ICON_CORNER     = {"sharp", "rounded", "mixed"}
_VALID_ICON_COMPLEXITY = {"simple", "medium", "detailed"}

_VALID_MOTIF_TYPE      = {"none", "geometric", "blob", "grid-fragment", "diagonal-cut",
                           "noise", "dot-pattern", "line-pattern", "wave"}
_VALID_MOTIF_USAGE     = {"none", "background", "section-accent", "corner", "full-bleed"}

_VALID_OVERLAY_TYPE    = {"none", "gradient", "noise", "duotone", "vignette", "scanlines"}
_VALID_OVERLAY_INTENSITY = {"none", "subtle", "medium", "strong"}


# ─────────────────────────────────────────────────────────────────────────────
# DECORATOR PRESETS — par contexte produit
# ─────────────────────────────────────────────────────────────────────────────
# Organisés par emotional_goal + brand_positioning, mappés depuis le context
# du VisualIntent.

_PRESETS: dict[str, dict] = {

    # ── Trust (finance, saas, health) ─────────────────────────────────────────
    "trust": {
        "borders":   {"style": "solid",    "thickness": "thin",   "radius": "small",  "pattern": "top-only"},
        "dividers":  {"type": "line",      "style": "minimal"},
        "icons":     {"style": "line",     "stroke": "thin",      "corner_style": "sharp",   "complexity": "simple"},
        "motifs":    {"type": "none",      "usage": "none"},
        "overlays":  {"type": "none",      "intensity": "none"},
    },

    # ── Excitement (gaming, event) ─────────────────────────────────────────────
    "excitement": {
        "borders":   {"style": "glow",     "thickness": "medium", "radius": "none",   "pattern": "frame"},
        "dividers":  {"type": "zigzag",    "style": "bold"},
        "icons":     {"style": "filled",   "stroke": "thick",     "corner_style": "sharp",   "complexity": "medium"},
        "motifs":    {"type": "diagonal-cut", "usage": "section-accent"},
        "overlays":  {"type": "scanlines", "intensity": "subtle"},
    },

    # ── Desire (ecommerce, dating, food, travel) ───────────────────────────────
    "desire": {
        "borders":   {"style": "solid",    "thickness": "thin",   "radius": "medium", "pattern": "accent"},
        "dividers":  {"type": "gradient",  "style": "subtle"},
        "icons":     {"style": "duotone",  "stroke": "medium",    "corner_style": "rounded", "complexity": "simple"},
        "motifs":    {"type": "blob",      "usage": "background"},
        "overlays":  {"type": "gradient",  "intensity": "subtle"},
    },

    # ── Calm (health, wellness) ────────────────────────────────────────────────
    "calm": {
        "borders":   {"style": "solid",    "thickness": "thin",   "radius": "large",  "pattern": "uniform"},
        "dividers":  {"type": "space",     "style": "subtle"},
        "icons":     {"style": "line",     "stroke": "thin",      "corner_style": "rounded", "complexity": "simple"},
        "motifs":    {"type": "wave",      "usage": "background"},
        "overlays":  {"type": "none",      "intensity": "none"},
    },

    # ── Curiosity (editorial, education) ──────────────────────────────────────
    "curiosity": {
        "borders":   {"style": "dashed",   "thickness": "thin",   "radius": "none",   "pattern": "accent"},
        "dividers":  {"type": "ornament",  "style": "decorative"},
        "icons":     {"style": "outline-filled", "stroke": "medium", "corner_style": "mixed", "complexity": "medium"},
        "motifs":    {"type": "grid-fragment", "usage": "section-accent"},
        "overlays":  {"type": "noise",     "intensity": "subtle"},
    },

    # ── Authority (agency, b2b, institution) ──────────────────────────────────
    "authority": {
        "borders":   {"style": "solid",    "thickness": "medium", "radius": "none",   "pattern": "top-only"},
        "dividers":  {"type": "line",      "style": "bold"},
        "icons":     {"style": "filled",   "stroke": "medium",    "corner_style": "sharp",   "complexity": "simple"},
        "motifs":    {"type": "geometric", "usage": "corner"},
        "overlays":  {"type": "none",      "intensity": "none"},
    },

    # ── Default (fallback générique) ──────────────────────────────────────────
    "default": {
        "borders":   {"style": "solid",    "thickness": "thin",   "radius": "small",  "pattern": "uniform"},
        "dividers":  {"type": "line",      "style": "minimal"},
        "icons":     {"style": "line",     "stroke": "medium",    "corner_style": "rounded", "complexity": "simple"},
        "motifs":    {"type": "none",      "usage": "none"},
        "overlays":  {"type": "none",      "intensity": "none"},
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# BRAND POSITIONING ADJUSTMENTS — fine-tune sur le preset emotional_goal
# ─────────────────────────────────────────────────────────────────────────────

_POSITIONING_ADJUSTMENTS: dict[str, dict] = {

    "premium": {
        "borders":  {"style": "double",   "thickness": "thin",   "radius": "none",   "pattern": "frame"},
        "dividers": {"type": "line",      "style": "decorative"},
        "icons":    {"stroke": "thin",    "corner_style": "sharp"},
        "motifs":   {"type": "none",      "usage": "none"},
        "overlays": {"type": "gradient",  "intensity": "subtle"},
    },

    "disruptive": {
        "borders":  {"style": "dashed",   "thickness": "thick",  "radius": "none",   "pattern": "accent"},
        "dividers": {"type": "zigzag",    "style": "bold"},
        "icons":    {"style": "filled",   "stroke": "thick",     "corner_style": "sharp"},
        "motifs":   {"type": "diagonal-cut", "usage": "full-bleed"},
        "overlays": {"type": "scanlines", "intensity": "medium"},
    },

    "playful": {
        "borders":  {"radius": "large",   "pattern": "uniform"},
        "dividers": {"type": "gradient",  "style": "decorative"},
        "icons":    {"corner_style": "rounded", "complexity": "medium"},
        "motifs":   {"type": "blob",      "usage": "section-accent"},
        "overlays": {"type": "none",      "intensity": "none"},
    },

    "accessible": {
        "borders":  {"radius": "medium",  "pattern": "uniform"},
        "icons":    {"stroke": "medium",  "corner_style": "rounded"},
        "motifs":   {"type": "none",      "usage": "none"},
        "overlays": {"type": "none",      "intensity": "none"},
    },

    "serious": {
        "borders":  {"radius": "none",    "pattern": "top-only"},
        "dividers": {"style": "minimal"},
        "icons":    {"corner_style": "sharp", "complexity": "simple"},
        "motifs":   {"type": "none",      "usage": "none"},
        "overlays": {"type": "none",      "intensity": "none"},
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# STYLE FAMILY OVERRIDES — certaines style families ont des decorators forts
# ─────────────────────────────────────────────────────────────────────────────

_STYLE_FAMILY_OVERRIDES: dict[str, dict] = {

    "editorial_luxury": {
        "borders":  {"style": "double",   "thickness": "thin",  "radius": "none",   "pattern": "frame"},
        "dividers": {"type": "line",      "style": "decorative"},
        "icons":    {"style": "line",     "stroke": "thin",     "corner_style": "sharp",   "complexity": "simple"},
        "motifs":   {"type": "none",      "usage": "none"},
        "overlays": {"type": "none",      "intensity": "none"},
    },

    "brutalist": {
        "borders":  {"style": "solid",    "thickness": "thick", "radius": "none",   "pattern": "frame"},
        "dividers": {"type": "line",      "style": "bold"},
        "icons":    {"style": "filled",   "stroke": "thick",    "corner_style": "sharp",   "complexity": "simple"},
        "motifs":   {"type": "grid-fragment", "usage": "full-bleed"},
        "overlays": {"type": "none",      "intensity": "none"},
    },

    "tech_minimal": {
        "borders":  {"style": "solid",    "thickness": "thin",  "radius": "small",  "pattern": "top-only"},
        "dividers": {"type": "line",      "style": "minimal"},
        "icons":    {"style": "line",     "stroke": "thin",     "corner_style": "sharp",   "complexity": "simple"},
        "motifs":   {"type": "dot-pattern", "usage": "background"},
        "overlays": {"type": "none",      "intensity": "none"},
    },

    "experimental_grid": {
        "borders":  {"style": "dashed",   "thickness": "medium","radius": "none",   "pattern": "accent"},
        "dividers": {"type": "zigzag",    "style": "decorative"},
        "icons":    {"style": "outline-filled", "stroke": "medium", "corner_style": "mixed", "complexity": "detailed"},
        "motifs":   {"type": "grid-fragment", "usage": "full-bleed"},
        "overlays": {"type": "noise",     "intensity": "medium"},
    },

    "premium_brand": {
        "borders":  {"style": "solid",    "thickness": "thin",  "radius": "none",   "pattern": "frame"},
        "dividers": {"type": "line",      "style": "decorative"},
        "icons":    {"style": "duotone",  "stroke": "thin",     "corner_style": "rounded", "complexity": "simple"},
        "motifs":   {"type": "none",      "usage": "none"},
        "overlays": {"type": "gradient",  "intensity": "subtle"},
    },

    "bold_marketing": {
        "borders":  {"style": "solid",    "thickness": "thick", "radius": "small",  "pattern": "frame"},
        "dividers": {"type": "gradient",  "style": "bold"},
        "icons":    {"style": "filled",   "stroke": "thick",    "corner_style": "rounded", "complexity": "medium"},
        "motifs":   {"type": "diagonal-cut", "usage": "section-accent"},
        "overlays": {"type": "gradient",  "intensity": "subtle"},
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _deep_copy(d: dict) -> dict:
    return json.loads(json.dumps(d))


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base — uniquement les clés présentes dans override."""
    result = _deep_copy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key].update(value)
        elif key in result:
            result[key] = value
    return result


def _validate(val: Any, valid: set, fallback: str) -> str:
    return val if (isinstance(val, str) and val in valid) else fallback


def _validate_and_clean(decorators: dict) -> dict:
    """Garantit la conformité stricte du schéma de sortie."""
    b = decorators.get("borders", {})
    d = decorators.get("dividers", {})
    i = decorators.get("icons", {})
    m = decorators.get("motifs", {})
    o = decorators.get("overlays", {})

    return {
        "borders": {
            "style":     _validate(b.get("style"),     _VALID_BORDER_STYLE,     "solid"),
            "thickness": _validate(b.get("thickness"), _VALID_BORDER_THICKNESS, "thin"),
            "radius":    _validate(b.get("radius"),    _VALID_BORDER_RADIUS,    "small"),
            "pattern":   _validate(b.get("pattern"),   _VALID_BORDER_PATTERN,   "uniform"),
        },
        "dividers": {
            "type":  _validate(d.get("type"),  _VALID_DIVIDER_TYPE,  "line"),
            "style": _validate(d.get("style"), _VALID_DIVIDER_STYLE, "minimal"),
        },
        "icons": {
            "style":        _validate(i.get("style"),        _VALID_ICON_STYLE,       "line"),
            "stroke":       _validate(i.get("stroke"),       _VALID_ICON_STROKE,      "medium"),
            "corner_style": _validate(i.get("corner_style"), _VALID_ICON_CORNER,      "rounded"),
            "complexity":   _validate(i.get("complexity"),   _VALID_ICON_COMPLEXITY,  "simple"),
        },
        "motifs": {
            "type":  _validate(m.get("type"),  _VALID_MOTIF_TYPE,  "none"),
            "usage": _validate(m.get("usage"), _VALID_MOTIF_USAGE, "none"),
        },
        "overlays": {
            "type":      _validate(o.get("type"),      _VALID_OVERLAY_TYPE,      "none"),
            "intensity": _validate(o.get("intensity"), _VALID_OVERLAY_INTENSITY, "none"),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_visual_decorators(visual_intent: dict) -> dict:
    """
    Génère la couche de signature visuelle décorative.

    Produit un système décoratif cohérent — peu d'éléments, utilisés uniformément.
    Chaque composant (border, divider, icon, motif, overlay) partage le même
    langage visuel.

    Args:
        visual_intent : dict produit par generate_visual_intent()
                        Champs utilisés :
                          - context.emotional_goal
                          - context.brand_positioning
                          - art_direction.style_family
                          - art_direction.intensity
                          - composition_bias

    Returns:
        dict strict conforme au schéma Decorators (zéro champ manquant)

    Logique de priorité :
        1. Style family connue → override complet (style family prime sur tout)
        2. Sinon : preset emotional_goal comme base
        3. Fine-tune brand_positioning par-dessus
    """
    context    = visual_intent.get("context", {})
    ad         = visual_intent.get("art_direction", {})
    cb         = visual_intent.get("composition_bias", {})

    emotional_goal    = context.get("emotional_goal", "")
    brand_positioning = context.get("brand_positioning", "")
    style_family      = ad.get("style_family", "")
    intensity         = ad.get("intensity", "low")

    # ── 1. Style family connue → override complet ─────────────────────────────
    if style_family in _STYLE_FAMILY_OVERRIDES:
        base = _deep_copy(_STYLE_FAMILY_OVERRIDES[style_family])
        # En mode strong/hybrid à haute intensité, amplifier les overlays
        if intensity == "high" and base["overlays"]["type"] == "none":
            if style_family in ("experimental_grid",):
                base["overlays"] = {"type": "noise", "intensity": "medium"}
        return _validate_and_clean(base)

    # ── 2. Base depuis emotional_goal ─────────────────────────────────────────
    base_key = emotional_goal if emotional_goal in _PRESETS else "default"
    decorators = _deep_copy(_PRESETS[base_key])

    # ── 3. Fine-tune depuis brand_positioning ─────────────────────────────────
    if brand_positioning in _POSITIONING_ADJUSTMENTS:
        adj = _POSITIONING_ADJUSTMENTS[brand_positioning]
        decorators = _deep_merge(decorators, adj)

    # ── 4. Ajustement selon intensity ─────────────────────────────────────────
    # intensity=high → éléments plus présents
    # intensity=low  → réduction maximale
    if intensity == "low":
        decorators["motifs"]["type"]      = "none"
        decorators["motifs"]["usage"]     = "none"
        decorators["overlays"]["type"]    = "none"
        decorators["overlays"]["intensity"] = "none"
        if decorators["borders"]["thickness"] in ("medium", "thick"):
            decorators["borders"]["thickness"] = "thin"

    elif intensity == "high" and decorators["overlays"]["type"] == "none":
        # Ajouter un overlay léger pour renforcer le caractère
        if decorators["motifs"]["type"] in ("diagonal-cut", "grid-fragment", "noise"):
            decorators["overlays"] = {"type": "noise", "intensity": "subtle"}

    # ── 5. Ajustement densité → richesse décorative ───────────────────────────
    density = cb.get("density", "medium")
    if density == "low" and decorators["motifs"]["usage"] == "full-bleed":
        decorators["motifs"]["usage"] = "corner"

    # ── 6. Validation et nettoyage ────────────────────────────────────────────
    return _validate_and_clean(decorators)
