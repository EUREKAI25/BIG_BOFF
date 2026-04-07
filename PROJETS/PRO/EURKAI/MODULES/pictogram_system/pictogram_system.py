"""
pictogram_system
────────────────
Generates parametric SVG pictograms from StyleDNA.
No external assets. Fully deterministic.

Every pictogram shares:
  - same stroke rules   (width, linecap, linejoin)
  - same grid           (24 / 48 / 16 px viewBox)
  - same corner style   (corner_radius applied to all rect primitives)
  - StyleDNA-derived color

Three categories:
  functional  — 24×24 px, utility icons         (9 pictograms)
  feature     — 48×48 px, rich pictograms        (5 pictograms)
  markers     — 16×16 px, decorative accents     (4 pictograms)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


# ─── Schema ──────────────────────────────────────────────────────────────────

@dataclass
class PictogramParams:
    """
    Rendering parameters derived from StyleDNA / VisualFamily.
    Drives every SVG primitive in every pictogram — the single source of
    visual personality for the entire set.
    """
    stroke_width:  float = 2.0
    linecap:  Literal["butt", "square", "round"] = "round"
    linejoin: Literal["miter", "round", "bevel"]  = "round"
    corner_radius: float = 0.0     # applied uniformly to all <rect> elements
    color:   str = "#1A1A1A"       # stroke + closed-path fill color
    fill:    str = "none"          # "none" → outline-only; hex → semi-filled
    family:  str = "startup_clean" # originating VisualFamily (informational)


@dataclass
class PictogramSet:
    """
    A coherent SVG pictogram set for a single project.
    All entries share PictogramParams — guaranteeing visual consistency.
    """
    params:     PictogramParams
    functional: dict[str, str] = field(default_factory=dict)  # name → SVG
    feature:    dict[str, str] = field(default_factory=dict)  # name → SVG
    markers:    dict[str, str] = field(default_factory=dict)  # name → SVG

    @property
    def all(self) -> dict[str, str]:
        return {**self.functional, **self.feature, **self.markers}


# ─── Generation rules — VisualFamily → PictogramParams ───────────────────────
#
# Each family maps to a distinct visual personality:
#   refined     → hairline stroke, sharp caps (butt/miter), no corner rounding
#   structured  → medium stroke, square caps, subtle rounding
#   electric    → medium/bold stroke, square-or-round caps, sharp corners
#   warm        → bold stroke, round caps + linejoin, generous corner radius

_FAMILY_RULES: dict[str, dict] = {
    # ── Refined ───────────────────────────────────────────────────────────────
    "luxury_minimal":     dict(stroke_width=1.5, linecap="butt",   linejoin="miter", corner_radius=0.0),
    "editorial_magazine": dict(stroke_width=1.5, linecap="butt",   linejoin="miter", corner_radius=0.0),
    "premium_craft":      dict(stroke_width=1.5, linecap="butt",   linejoin="miter", corner_radius=1.0),
    # ── Structured ────────────────────────────────────────────────────────────
    "corporate_pro":      dict(stroke_width=2.0, linecap="square", linejoin="miter", corner_radius=2.0),
    "startup_clean":      dict(stroke_width=2.0, linecap="square", linejoin="round", corner_radius=4.0),
    # ── Electric ──────────────────────────────────────────────────────────────
    "tech_futurist":      dict(stroke_width=2.0, linecap="square", linejoin="miter", corner_radius=0.0),
    "bold_challenger":    dict(stroke_width=2.5, linecap="round",  linejoin="round", corner_radius=0.0),
    "creative_studio":    dict(stroke_width=2.0, linecap="round",  linejoin="round", corner_radius=4.0),
    # ── Warm ──────────────────────────────────────────────────────────────────
    "organic_natural":    dict(stroke_width=2.0, linecap="round",  linejoin="round", corner_radius=6.0),
    "playful_brand":      dict(stroke_width=2.5, linecap="round",  linejoin="round", corner_radius=8.0),
    "warm_human":         dict(stroke_width=2.0, linecap="round",  linejoin="round", corner_radius=6.0),
    "brutalist":          dict(stroke_width=3.0, linecap="square", linejoin="miter", corner_radius=0.0),
}


def params_from_style_dna(
    archetype: str,
    color: str = "#1A1A1A",
    fill:  str = "none",
) -> PictogramParams:
    """
    Build PictogramParams from a VisualFamily archetype name.
    Unknown archetypes fall back to startup_clean rules.
    """
    rules = _FAMILY_RULES.get(archetype, _FAMILY_RULES["startup_clean"])
    return PictogramParams(color=color, fill=fill, family=archetype, **rules)


# ─── Internal drawing DSL ─────────────────────────────────────────────────────
# Every pictogram is expressed as a list of drawing tuples.
# Coordinates are in the final SVG viewBox space (no normalization layer).
#
# Primitives:
#   ("line",   x1, y1, x2, y2)
#   ("rect",   x, y, w, h)              ← corner_radius applied by renderer
#   ("circle", cx, cy, r)
#   ("poly",   [(x,y), ...], close)     ← close=True → <polygon>, False → <polyline>
#   ("path",   d_string)                ← raw SVG path data; used only for curves

_L  = lambda x1, y1, x2, y2:       ("line",   x1,  y1,  x2,  y2)
_R  = lambda x, y, w, h:            ("rect",   x,   y,   w,   h)
_C  = lambda cx, cy, r:             ("circle", cx,  cy,  r)
_PL = lambda pts, close=False:      ("poly",   pts, close)
_P  = lambda d:                     ("path",   d)


# ─── Functional icons — 24×24 viewBox, 2 px padding (active area 2..22) ──────

_FUNCTIONAL: dict[str, list] = {

    # House outline with door
    "home": [
        _PL([(3, 13), (12, 4), (21, 13)]),     # roof ridge
        _L(5, 13, 5, 22),                       # left wall
        _L(19, 13, 19, 22),                     # right wall
        _L(5, 22, 19, 22),                      # ground line
        _R(9, 15, 6, 7),                        # door
    ],

    # Magnifying glass
    "search": [
        _C(10, 10, 6.5),                        # lens
        _L(14.6, 14.6, 21, 21),                # handle
    ],

    # Right arrow with shaft
    "arrow_right": [
        _L(2, 12, 18, 12),                      # shaft
        _PL([(12, 6), (18, 12), (12, 18)]),    # arrowhead
    ],

    # Checkmark
    "check": [
        _PL([(2, 12), (8, 18), (22, 5)]),
    ],

    # Dismissal cross
    "close": [
        _L(4, 4, 20, 20),
        _L(20, 4, 4, 20),
    ],

    # Navigation hamburger
    "menu": [
        _L(2, 6,  22, 6),
        _L(2, 12, 22, 12),
        _L(2, 18, 22, 18),
    ],

    # Abstract user (head + shoulders)
    "user": [
        _C(12, 8, 4.5),                         # head
        _P("M 4,22 Q 4,14 12,14 Q 20,14 20,22"),  # shoulders curve
    ],

    # Envelope
    "mail": [
        _R(2, 6, 20, 14),                       # envelope body
        _PL([(2, 6), (12, 14), (22, 6)]),       # V-flap
    ],

    # Adjustment sliders (settings)
    "settings": [
        _L(2, 6,  22, 6),   _C(8,  6,  2.5),   # slider 1
        _L(2, 12, 22, 12),  _C(16, 12, 2.5),   # slider 2
        _L(2, 18, 22, 18),  _C(10, 18, 2.5),   # slider 3
    ],
}


# ─── Feature pictograms — 48×48 viewBox, 4 px padding (active area 4..44) ───

_FEATURE: dict[str, list] = {

    # Bar chart + ascending trend line
    "chart_growth": [
        _R(4,  28, 11, 20),                     # short bar
        _R(19, 16, 11, 32),                     # mid bar
        _R(34, 6,  11, 42),                     # tall bar
        _PL([(4, 26), (24, 14), (44, 4)]),      # trend line
    ],

    # Shield (flat top, curved sides, pointed bottom)
    "shield": [
        _P("M 24,4 L 44,11 L 44,26 Q 44,38 24,45 Q 4,38 4,26 L 4,11 Z"),
    ],

    # Lightning bolt (energy / action)
    "lightning": [
        _P("M 28,4 L 14,26 L 24,26 L 18,44 L 34,22 L 24,22 Z"),
    ],

    # 4-pointed star (outer r=20, inner r=7 on diagonals)
    "star_four": [
        _P("M 24,4 L 29,19 L 44,24 L 29,29 L 24,44 L 19,29 L 4,24 L 19,19 Z"),
    ],

    # 2×2 module grid (apps / dashboard)
    "grid_modules": [
        _R(4,  4,  18, 18),
        _R(26, 4,  18, 18),
        _R(4,  26, 18, 18),
        _R(26, 26, 18, 18),
    ],
}


# ─── Visual markers — 16×16 viewBox, 2 px padding (active area 2..14) ────────

_MARKERS: dict[str, list] = {

    # Rotated square (editorial accent / bullet)
    "diamond": [
        _PL([(8, 2), (14, 8), (8, 14), (2, 8)], close=True),
    ],

    # Three-dot rhythm marker
    "dot_trio": [
        _C(4, 8, 1.8),
        _C(8, 8, 1.8),
        _C(12, 8, 1.8),
    ],

    # Right chevron (breadcrumb / navigation cue)
    "chevron_right": [
        _PL([(5, 2), (11, 8), (5, 14)]),
    ],

    # Plus / add action
    "plus": [
        _L(8, 2,  8, 14),
        _L(2, 8, 14, 8),
    ],
}


# ─── Renderer ─────────────────────────────────────────────────────────────────

def _render_elem(elem: tuple, p: PictogramParams) -> str:
    sw   = p.stroke_width
    cap  = p.linecap
    join = p.linejoin
    col  = p.color
    cr   = p.corner_radius
    fill = p.fill

    kind = elem[0]

    if kind == "line":
        _, x1, y1, x2, y2 = elem
        return (
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"'
            f' stroke="{col}" stroke-width="{sw}" stroke-linecap="{cap}"/>'
        )

    if kind == "rect":
        _, x, y, w, h = elem
        rx = f' rx="{cr}"' if cr else ""
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}"'
            f' fill="{fill}" stroke="{col}" stroke-width="{sw}"{rx}/>'
        )

    if kind == "circle":
        _, cx, cy, r = elem
        return (
            f'<circle cx="{cx}" cy="{cy}" r="{r}"'
            f' fill="{fill}" stroke="{col}" stroke-width="{sw}"/>'
        )

    if kind == "poly":
        _, pts, close = elem
        pts_str = " ".join(f"{x},{y}" for x, y in pts)
        tag = "polygon" if close else "polyline"
        return (
            f'<{tag} points="{pts_str}" fill="{fill}"'
            f' stroke="{col}" stroke-width="{sw}"'
            f' stroke-linecap="{cap}" stroke-linejoin="{join}"/>'
        )

    if kind == "path":
        _, d = elem
        return (
            f'<path d="{d}" fill="{fill}"'
            f' stroke="{col}" stroke-width="{sw}"'
            f' stroke-linecap="{cap}" stroke-linejoin="{join}"/>'
        )

    return ""


def _render_svg(defs: list, p: PictogramParams, size: int) -> str:
    inner = "\n  ".join(_render_elem(e, p) for e in defs)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {size} {size}" width="{size}" height="{size}"'
        f' fill="none">\n  {inner}\n</svg>'
    )


# ─── Public API ───────────────────────────────────────────────────────────────

def generate_pictogram_set(
    archetype: str,
    color: str = "#1A1A1A",
    fill:  str = "none",
) -> PictogramSet:
    """
    Generate a full PictogramSet for a given archetype and color.

    All pictograms share the same stroke rules and corner style — derived
    from the archetype via _FAMILY_RULES.  Pass a different color to produce
    alternate-color variants (e.g. white-on-dark, accent-colored).
    """
    p = params_from_style_dna(archetype, color=color, fill=fill)

    return PictogramSet(
        params=p,
        functional={
            name: _render_svg(defs, p, 24)
            for name, defs in _FUNCTIONAL.items()
        },
        feature={
            name: _render_svg(defs, p, 48)
            for name, defs in _FEATURE.items()
        },
        markers={
            name: _render_svg(defs, p, 16)
            for name, defs in _MARKERS.items()
        },
    )
