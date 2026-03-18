#!/usr/bin/env python3
"""
generate_brand_charter.py
─────────────────────────
Test orchestrator — EURKAI design pipeline validator.

Pipeline :
    brief → design_dna_resolver → color_psychology_engine → palette_generator
          → design_exploration_engine → theme_generator (via StyleDNA)

Outputs one HTML brand charter per project in output/<project_name>/.

Usage :
    python generate_brand_charter.py                    # all 3 test briefs
    python generate_brand_charter.py --project vectorstack
    python generate_brand_charter.py --brief "..." --name "MyProject"

Note : brand_generator excluded (requires LLM).
       StyleDNA is assembled from deterministic module outputs.
"""

from __future__ import annotations

import sys
import json
import argparse
import textwrap
import html as html_lib
from pathlib import Path
from dataclasses import asdict
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).parent
MODULES_DIR = SCRIPT_DIR / "MODULES"
OUTPUT_DIR  = SCRIPT_DIR / "output"

for _mod in sorted(MODULES_DIR.iterdir()):
    if _mod.is_dir() and not _mod.name.startswith(("_", ".")):
        sys.path.insert(0, str(_mod))

# ── Module imports (graceful degradation) ─────────────────────────────────────

_import_errors: list[str] = []

try:
    from design_dna_resolver import resolve as _resolve_dna
except ImportError as e:
    _import_errors.append(f"design_dna_resolver: {e}")
    _resolve_dna = None  # type: ignore

try:
    from color_psychology_engine import get_color_recommendation as _get_psych
    from color_psychology_engine import PsychologyInput
except ImportError as e:
    _import_errors.append(f"color_psychology_engine: {e}")
    _get_psych = None  # type: ignore

try:
    from palette_generator import generate_palette as _gen_palette
    from palette_generator import PaletteInput, PaletteScenario
except ImportError as e:
    _import_errors.append(f"palette_generator: {e}")
    _gen_palette = None  # type: ignore

try:
    from design_exploration_engine import explore as _explore
except ImportError as e:
    _import_errors.append(f"design_exploration_engine: {e}")
    _explore = None  # type: ignore

try:
    from theme_generator import ThemeGenerator as _ThemeGenerator
    from theme_generator.style_dna import (
        StyleDNA, PaletteProfile, TypographyProfile,
        GeometryProfile, OrnamentProfile, LayoutProfile,
    )
    from theme_generator.theme_translation import translate as _translate
    _theme_ok = True
except ImportError as e:
    _import_errors.append(f"theme_generator: {e}")
    _theme_ok = False

# ── Mapping tables ────────────────────────────────────────────────────────────

SEMANTIC_COLOR_HEX: dict[str, str] = {
    # Blues
    "navy": "#1a2942", "navy blue": "#1a2942", "deep navy": "#0d1b2a",
    "dark navy": "#0f172a", "midnight blue": "#1e3a5f", "midnight": "#1e1b4b",
    "royal blue": "#2347aa", "blue": "#2563eb", "medium blue": "#1d4ed8",
    "steel blue": "#3b82f6", "cobalt": "#1e40af", "cobalt blue": "#1e40af",
    "indigo": "#4338ca", "slate blue": "#6366f1", "periwinkle": "#818cf8",
    "light blue": "#60a5fa", "sky blue": "#38bdf8", "petrol blue": "#164e63",
    "teal": "#0f766e", "dark teal": "#134e4a", "cyan": "#06b6d4",
    "prussian blue": "#1e3a5f", "powder blue": "#bae6fd",
    # Greens
    "green": "#16a34a", "forest green": "#166534", "dark green": "#14532d",
    "emerald": "#059669", "sage": "#84a98c", "olive": "#6b7c3e",
    "olive green": "#4d6b3e", "mint": "#6ee7b7", "moss": "#6b7c3e",
    "bottle green": "#0d3d2d", "hunter green": "#1b4332", "pine": "#1b4332",
    # Reds / Pinks
    "red": "#dc2626", "crimson": "#b91c1c", "dark red": "#991b1b",
    "warm red": "#e53e3e", "burgundy": "#7f1d1d", "wine": "#881337",
    "bordeaux": "#7f1d1d", "rose": "#f43f5e", "blush": "#fda4af",
    "pink": "#ec4899", "hot pink": "#db2777", "fuchsia": "#c026d3",
    # Oranges / Yellows / Golds
    "coral": "#f97316", "terracotta": "#c2532e", "rust": "#c2410c",
    "orange": "#ea580c", "amber": "#d97706", "warm orange": "#f97316",
    "gold": "#ca8a04", "golden": "#b45309", "yellow": "#eab308",
    "mustard": "#a16207", "ochre": "#b45309", "warm gold": "#c49a0a",
    # Purples
    "purple": "#7c3aed", "violet": "#8b5cf6", "lavender": "#a78bfa",
    "magenta": "#c026d3", "plum": "#7e22ce", "mauve": "#a855f7",
    "deep purple": "#4c1d95", "eggplant": "#4a044e",
    # Neutrals
    "black": "#111111", "rich black": "#0a0a0a", "deep black": "#050505",
    "charcoal": "#2c2c2c", "graphite": "#404040", "anthracite": "#2d2d2d",
    "dark gray": "#525252", "gray": "#737373", "cool gray": "#6b7280",
    "warm gray": "#78716c", "taupe": "#736b5e", "slate": "#64748b",
    "silver": "#a3a3a3", "light gray": "#d4d4d4", "pale gray": "#e5e7eb",
    "cream": "#fdf6e3", "ivory": "#fffff0", "warm ivory": "#f9f5f0",
    "off white": "#fafaf8", "white": "#ffffff", "warm white": "#fafaf0",
    # Browns / Earthtones
    "brown": "#92400e", "chocolate": "#713f12", "sienna": "#b45309",
    "tan": "#d4a264", "beige": "#d9c8a9", "sand": "#c4a988",
    "warm beige": "#e8d5b7", "caramel": "#c4843c",
}

ARCHETYPE_FALLBACK_HEX: dict[str, str] = {
    "luxury_minimal":     "#0a0a0a",
    "startup_clean":      "#2563eb",
    "editorial_magazine": "#1a1a1a",
    "tech_futurist":      "#0f172a",
    "creative_studio":    "#7c3aed",
    "brutalist":          "#111111",
    "organic_natural":    "#166534",
    "playful_brand":      "#ec4899",
    "corporate_pro":      "#1d4ed8",
    "premium_craft":      "#92400e",
    "bold_challenger":    "#dc2626",
    "warm_human":         "#f97316",
}

ARCHETYPE_TO_TONE: dict[str, str] = {
    "luxury_minimal":     "premium",
    "startup_clean":      "calm",
    "editorial_magazine": "premium",
    "tech_futurist":      "tech",
    "creative_studio":    "playful",
    "brutalist":          "raw",
    "organic_natural":    "calm",
    "playful_brand":      "playful",
    "corporate_pro":      "calm",
    "premium_craft":      "premium",
    "bold_challenger":    "bold",
    "warm_human":         "playful",
}

ARCHETYPE_TO_COMPLEXITY: dict[str, str] = {
    "luxury_minimal":     "minimal",
    "startup_clean":      "moderate",
    "editorial_magazine": "moderate",
    "tech_futurist":      "rich",
    "creative_studio":    "rich",
    "brutalist":          "moderate",
    "organic_natural":    "moderate",
    "playful_brand":      "rich",
    "corporate_pro":      "minimal",
    "premium_craft":      "moderate",
    "bold_challenger":    "rich",
    "warm_human":         "moderate",
}

TYPO_TO_DISPLAY_PROFILE: dict[str, str] = {
    "geometric_sans":             "bold_condensed_geometric",
    "humanist_sans":              "neutral_sans",
    "editorial_serif":            "thin_elegant_serif",
    "editorial_sans":             "neutral_sans",
    "tech_mono":                  "neutral_sans",
    "brutalist_display":          "bold_condensed_geometric",
    "organic_serif":              "thin_elegant_serif",
    "playful_display":            "bold_condensed_geometric",
    "corporate_sans":             "neutral_sans",
    "craft_serif":                "thin_elegant_serif",
    "bold_condensed":             "bold_condensed_geometric",
    "warm_rounded":               "neutral_sans",
    # Keys from design_dna_resolver.style_mapper
    "display_serif":              "thin_elegant_serif",
    "display_serif_editorial":    "thin_elegant_serif",
    "condensed_tech_sans":        "bold_condensed_geometric",
    "expressive_display":         "bold_condensed_geometric",
    "grotesque_bold":             "bold_condensed_geometric",
    "humanist_sans_organic":      "neutral_sans",
    "rounded_sans":               "neutral_sans",
    "transitional_sans":          "neutral_sans",
    "serif_artisan":              "thin_elegant_serif",
    "condensed_bold_sans":        "bold_condensed_geometric",
    "humanist_rounded_sans":      "neutral_sans",
}

LAYOUT_TO_RADIUS: dict[str, str] = {
    "geometric_grid":      "small",
    "editorial_grid":      "none",
    "fluid_organic":       "large",
    "brutalist_grid":      "none",
    "compact_grid":        "small",
    "asymmetric":          "none",
    "playful_layout":      "large",
    "corporate_grid":      "small",
    "craft_layout":        "medium",
    "card_based":          "medium",
    # Keys from design_dna_resolver.style_mapper
    "spacious_minimal":    "none",
    "clean_grid":          "small",
    "editorial_asymmetric":"none",
    "dark_grid":           "small",
    "fluid_creative":      "large",
    "raw_asymmetric":      "none",
    "breathing_organic":   "large",
    "card_playful":        "large",
    "structured_grid":     "small",
    "editorial_rich":      "small",
    "high_contrast_grid":  "none",
    "open_breathing":      "medium",
}

# Density and rhythm per layout_style (used to populate LayoutProfile)
LAYOUT_TO_DENSITY: dict[str, str] = {
    "spacious_minimal":    "minimal",
    "editorial_asymmetric":"minimal",
    "editorial_rich":      "minimal",
    "editorial_grid":      "minimal",
    "clean_grid":          "moderate",
    "geometric_grid":      "moderate",
    "dark_grid":           "moderate",
    "corporate_grid":      "moderate",
    "structured_grid":     "moderate",
    "compact_grid":        "dense",
    "high_contrast_grid":  "dense",
    "raw_asymmetric":      "dense",
    "card_playful":        "moderate",
    "fluid_creative":      "moderate",
    "breathing_organic":   "minimal",
    "open_breathing":      "minimal",
    "craft_layout":        "moderate",
    "card_based":          "moderate",
    "playful_layout":      "moderate",
}

LAYOUT_TO_RHYTHM: dict[str, str] = {
    "editorial_asymmetric":"editorial",
    "editorial_rich":      "editorial",
    "editorial_grid":      "editorial",
    "spacious_minimal":    "spacious",
    "breathing_organic":   "spacious",
    "open_breathing":      "spacious",
    "clean_grid":          "balanced",
    "geometric_grid":      "balanced",
    "corporate_grid":      "balanced",
    "structured_grid":     "balanced",
    "card_based":          "balanced",
    "fluid_creative":      "dynamic",
    "card_playful":        "dynamic",
    "playful_layout":      "dynamic",
    "dark_grid":           "tight",
    "compact_grid":        "tight",
    "high_contrast_grid":  "tight",
    "raw_asymmetric":      "tight",
}

CONTRAST_MAP: dict[str, str] = {
    "clean": "low", "soft": "low",
    "balanced": "medium",
    "high": "high", "dramatic": "high",
}

# ── Utilities ─────────────────────────────────────────────────────────────────

def semantic_to_hex(name: str, fallback: str = "#2563eb") -> str:
    if not name:
        return fallback
    lower = name.lower().strip()
    if lower in SEMANTIC_COLOR_HEX:
        return SEMANTIC_COLOR_HEX[lower]
    for key, val in SEMANTIC_COLOR_HEX.items():
        if key in lower or lower in key:
            return val
    return fallback


def hex_luminance(h: str) -> float:
    h = h.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    def lc(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lc(r) + 0.7152 * lc(g) + 0.0722 * lc(b)


def text_on(bg_hex: str) -> str:
    """Return '#fff' or '#111' depending on bg luminance."""
    return "#fff" if hex_luminance(bg_hex) < 0.35 else "#111"


def extract_palette_hex(palette_set, preferred: list[str] | None = None) -> tuple[str, str, str, str]:
    """Return (primary, secondary, accent, neutral) hex from PaletteSet."""
    primary = secondary = accent = neutral = None

    if palette_set:
        for harm in ("complementary", "analogous", "monochromatic", "triadic"):
            h = getattr(palette_set, harm, None)
            if h is None:
                continue
            if not primary and getattr(h, "primary", None):
                primary = h.primary[0].hex
            if not secondary and getattr(h, "secondary", None):
                secondary = h.secondary[0].hex
            if not accent and getattr(h, "accent", None):
                accent = h.accent[0].hex
            if not neutral and getattr(h, "neutral", None):
                neutral = h.neutral[0].hex
            if primary and secondary:
                break

    fallbacks = preferred or []
    primary  = primary  or semantic_to_hex(fallbacks[0] if fallbacks else "", "#2563eb")
    secondary = secondary or semantic_to_hex(fallbacks[1] if len(fallbacks) > 1 else "", "#7c3aed")
    accent   = accent   or semantic_to_hex(fallbacks[2] if len(fallbacks) > 2 else "", "#f97316")
    neutral  = neutral  or "#374151"
    return primary, secondary, accent, neutral


def extract_css_variables(css: str) -> dict[str, str]:
    """Parse :root block and return {name: value} dict."""
    variables: dict[str, str] = {}
    in_root = False
    for line in css.splitlines():
        stripped = line.strip()
        if ":root" in stripped:
            in_root = True
            continue
        if in_root:
            if stripped == "}":
                in_root = False
                continue
            if stripped.startswith("--") and ":" in stripped:
                parts = stripped.split(":", 1)
                name  = parts[0].strip()
                value = parts[1].strip().rstrip(";")
                variables[name] = value
    return variables

# ── Pipeline steps ────────────────────────────────────────────────────────────

def step_dna(brief_text: str, project_name: str | None = None):
    if not _resolve_dna:
        return None
    try:
        dna = _resolve_dna(brief_text)
        if project_name and not getattr(dna, "project_name", None):
            dna.project_name = project_name
        return dna
    except Exception as e:
        print(f"    ⚠️  design_dna_resolver: {e}")
        return None


def step_psychology(dna):
    if not _get_psych or dna is None:
        return None
    try:
        return _get_psych(PsychologyInput(
            industry=getattr(dna, "industry", None),
            brand_values=getattr(dna, "brand_values", []) or [],
            tone=getattr(dna, "tone", None),
            target_audience=getattr(dna, "target_audience", None),
            region=None,
            style_tags=[],
        ))
    except Exception as e:
        print(f"    ⚠️  color_psychology_engine: {e}")
        return None


def step_palette(dna, rec):
    if not _gen_palette:
        return None
    try:
        base_hex = None
        if dna and getattr(dna, "palette_bias", None):
            pref = getattr(dna.palette_bias, "preferred_colors", [])
            if pref:
                base_hex = semantic_to_hex(pref[0])
        if not base_hex and rec and getattr(rec, "preferred_colors", []):
            base_hex = semantic_to_hex(rec.preferred_colors[0])
        if not base_hex:
            archetype = getattr(dna, "style_archetype", None) if dna else None
            base_hex = ARCHETYPE_FALLBACK_HEX.get(archetype or "", "#2563eb")

        return _gen_palette(PaletteInput(
            scenario=PaletteScenario.BRAND,
            base_color=base_hex,
        ))
    except Exception as e:
        print(f"    ⚠️  palette_generator: {e}")
        return None


def step_explore(dna):
    if not _explore or dna is None:
        return None
    try:
        return _explore(asdict(dna), n_directions=3)
    except Exception as e:
        print(f"    ⚠️  design_exploration_engine: {e}")
        return None


def step_build_style_dna(dna, palette_output, rec) -> "StyleDNA":
    archetype = getattr(dna, "style_archetype", None) if dna else None
    palette_set = palette_output.palette_set if palette_output else None

    preferred: list[str] = []
    if dna:
        pb = getattr(dna, "palette_bias", None)
        if pb:
            preferred = getattr(pb, "preferred_colors", []) or []

    primary, secondary, accent, neutral = extract_palette_hex(palette_set, preferred)

    tone       = ARCHETYPE_TO_TONE.get(archetype or "", "calm")
    complexity = ARCHETYPE_TO_COMPLEXITY.get(archetype or "", "moderate")
    display_p  = TYPO_TO_DISPLAY_PROFILE.get(
        getattr(dna, "typography_style", None) or "", "neutral_sans"
    )
    layout_style = getattr(dna, "layout_style", None) or ""
    radius   = LAYOUT_TO_RADIUS.get(layout_style, "medium")
    density  = LAYOUT_TO_DENSITY.get(layout_style, "moderate")
    rhythm   = LAYOUT_TO_RHYTHM.get(layout_style, "balanced")
    temperature = getattr(rec, "color_temperature", "neutral") if rec else "neutral"
    saturation  = getattr(rec, "saturation_level",  "medium")  if rec else "medium"
    contrast    = CONTRAST_MAP.get(
        getattr(rec, "contrast_style", "balanced") if rec else "balanced",
        "medium"
    )

    return StyleDNA(
        palette_profile=PaletteProfile(
            dominant=[primary, secondary],
            accent=[accent],
            neutral=[neutral],
            temperature=temperature,
            saturation=saturation,
            contrast=contrast,
        ),
        typography_profile=TypographyProfile(
            display=display_p,
            body="neutral_humanist_sans",
        ),
        geometry_profile=GeometryProfile(
            border_radius=radius,
        ),
        ornament_profile=OrnamentProfile(),
        layout_profile=LayoutProfile(density=density, rhythm=rhythm),
        emotional_tone=tone,
        complexity_level=complexity,
        aesthetic_tags=[archetype] if archetype else [],
        source_type="brief",
    )


def step_theme(style_dna: "StyleDNA") -> tuple[dict | None, str | None]:
    if not _theme_ok:
        return None, None
    try:
        preset = _translate(style_dna)
        css    = _ThemeGenerator().generate(preset)
        return preset, css
    except Exception as e:
        print(f"    ⚠️  theme_generator: {e}")
        return None, None

# ── HTML helpers ──────────────────────────────────────────────────────────────

_CHROME_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #f0f0f0;
    color: #111;
    font-size: 14px;
    line-height: 1.6;
}
.page-wrap { max-width: 1100px; margin: 0 auto; padding: 24px; }
header.charter-header {
    background: #111;
    color: #fff;
    padding: 36px 40px 28px;
    border-radius: 8px;
    margin-bottom: 20px;
}
header.charter-header h1 { font-size: 2.2rem; font-weight: 700; letter-spacing: -0.02em; }
header.charter-header .meta { color: #999; font-size: 12px; margin-top: 6px; }
header.charter-header .badge {
    display: inline-block;
    background: #333;
    color: #aaa;
    font-size: 11px;
    padding: 2px 10px;
    border-radius: 100px;
    margin-right: 6px;
}

.section {
    background: #fff;
    border-radius: 8px;
    padding: 32px 36px;
    margin-bottom: 20px;
    border: 1px solid #e5e5e5;
}
.section-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #999;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f0f0f0;
}
h2 { font-size: 1.4rem; font-weight: 700; margin-bottom: 8px; }
h3 { font-size: 1rem; font-weight: 600; margin-bottom: 6px; }
p  { color: #444; margin-bottom: 10px; }
.brief-text {
    background: #f9f9f9;
    border-left: 3px solid #ddd;
    padding: 16px 20px;
    color: #444;
    white-space: pre-wrap;
    font-size: 13px;
    line-height: 1.7;
    border-radius: 0 4px 4px 0;
}
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.pill {
    display: inline-block;
    background: #f4f4f4;
    color: #555;
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 100px;
    margin: 2px;
}
.pill.accent { background: #111; color: #fff; }
.stat-label { font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.05em; }
.stat-value { font-size: 1.1rem; font-weight: 600; }
.info-row { display: flex; gap: 32px; margin-bottom: 20px; }
.info-item {}

/* Swatches */
.swatches { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.swatch {
    width: 56px; height: 56px;
    border-radius: 8px;
    display: flex; align-items: flex-end; justify-content: flex-start;
    padding: 4px 5px;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0;
    cursor: default;
    border: 1px solid rgba(0,0,0,.08);
}
.swatch.lg { width: 80px; height: 80px; font-size: 10px; }
.swatch-group { margin-bottom: 16px; }
.swatch-group-label { font-size: 11px; color: #999; margin-bottom: 6px; text-transform: uppercase; letter-spacing: .05em; }

/* Tonal scale */
.scale-row { display: flex; gap: 3px; margin-top: 8px; border-radius: 6px; overflow: hidden; }
.scale-step { flex: 1; height: 36px; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 600; }

/* Directions */
.direction-card {
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    padding: 20px;
    position: relative;
}
.direction-card .badge-relation {
    position: absolute; top: 12px; right: 12px;
    font-size: 10px; color: #999; background: #f5f5f5;
    padding: 2px 8px; border-radius: 100px;
}
.direction-card h3 { font-size: 1rem; font-weight: 700; }
.direction-card .tagline { color: #666; font-size: 13px; margin: 4px 0 12px; }
.hint-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px; margin-top: 10px; }
.hint-row { font-size: 11px; color: #666; }
.hint-row strong { color: #333; }

/* Typography samples */
.typo-sample {
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 20px;
}
.typo-sample .sample-display { font-size: 2rem; font-weight: 700; margin-bottom: 6px; }
.typo-sample .sample-body { font-size: 14px; line-height: 1.65; color: #444; }
.typo-label { font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }

/* Tokens */
.tokens-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.tokens-table th {
    text-align: left; padding: 6px 10px;
    background: #f9f9f9; color: #666;
    font-size: 10px; text-transform: uppercase;
    border-bottom: 1px solid #eee;
}
.tokens-table td { padding: 5px 10px; border-bottom: 1px solid #f5f5f5; color: #333; }
.tokens-table td:first-child { font-family: monospace; color: #555; }
.tokens-table td .color-dot {
    display: inline-block; width: 12px; height: 12px;
    border-radius: 50%; margin-right: 6px; vertical-align: middle;
    border: 1px solid rgba(0,0,0,.1);
}
.token-section-header { background: #f4f4f4; }
.token-section-header td { font-size: 10px; font-weight: 700; color: #888; text-transform: uppercase; letter-spacing: .05em; padding: 8px 10px; }

/* Preview */
.preview-frame {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
    margin-top: 12px;
}
.preview-label {
    font-size: 10px; text-transform: uppercase; letter-spacing: .08em;
    color: #999; padding: 6px 12px; background: #f9f9f9;
    border-bottom: 1px solid #eee;
}
.preview-body { padding: 32px; background: #fff; }

/* Raw JSON */
details { border: 1px solid #e5e5e5; border-radius: 6px; margin-bottom: 10px; }
summary {
    padding: 12px 16px; cursor: pointer; font-size: 12px;
    font-weight: 600; color: #555; user-select: none;
    list-style: none;
}
summary::-webkit-details-marker { display: none; }
summary::before { content: "▶  "; font-size: 10px; color: #aaa; }
details[open] summary::before { content: "▼  "; }
pre.json-block {
    background: #1e1e1e; color: #d4d4d4;
    font-family: monospace; font-size: 11px;
    padding: 16px 20px; overflow-x: auto;
    border-radius: 0 0 6px 6px;
    line-height: 1.5;
    max-height: 400px;
    overflow-y: auto;
}

/* Status bar */
.pipeline-status {
    display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px;
}
.pipeline-step {
    font-size: 11px; padding: 4px 12px; border-radius: 100px;
    border: 1px solid;
}
.pipeline-step.ok   { background: #f0fdf4; border-color: #86efac; color: #166534; }
.pipeline-step.fail { background: #fef2f2; border-color: #fca5a5; color: #991b1b; }
.pipeline-step.skip { background: #f9fafb; border-color: #e5e7eb; color: #9ca3af; }
"""


def _swatch(hex_color: str, label: str = "", size: str = "") -> str:
    txt = text_on(hex_color)
    cls = f"swatch{' lg' if size == 'lg' else ''}"
    lbl = html_lib.escape(label or hex_color)
    return f'<div class="{cls}" style="background:{hex_color};color:{txt};" title="{lbl}">{lbl}</div>'


def _section(title: str, content: str) -> str:
    return f"""
<div class="section">
  <div class="section-title">{html_lib.escape(title)}</div>
  {content}
</div>"""


def _pill(text: str, accent: bool = False) -> str:
    cls = "pill accent" if accent else "pill"
    return f'<span class="{cls}">{html_lib.escape(str(text))}</span>'


def _step_badge(label: str, ok: bool | None) -> str:
    if ok is None:
        cls, sym = "skip", "○"
    elif ok:
        cls, sym = "ok",   "✓"
    else:
        cls, sym = "fail", "✗"
    return f'<span class="pipeline-step {cls}">{sym} {html_lib.escape(label)}</span>'


def _json_collapsible(title: str, data: object) -> str:
    raw = json.dumps(data, indent=2, default=str)
    escaped = html_lib.escape(raw)
    return f"""<details>
  <summary>{html_lib.escape(title)}</summary>
  <pre class="json-block">{escaped}</pre>
</details>"""

# ── Section renderers ─────────────────────────────────────────────────────────

def render_overview(project_name: str, brief_text: str, pipeline_ok: dict) -> str:
    badges = "".join([
        _step_badge("design_dna",        pipeline_ok.get("dna")),
        _step_badge("color_psychology",  pipeline_ok.get("rec")),
        _step_badge("palette",           pipeline_ok.get("palette")),
        _step_badge("exploration",       pipeline_ok.get("explore")),
        _step_badge("theme_generator",   pipeline_ok.get("theme")),
        _step_badge("brand_generator",   None),   # always skipped
    ])
    brief_html = f'<div class="brief-text">{html_lib.escape(brief_text.strip())}</div>'
    return f"""
<div class="pipeline-status">{badges}</div>
<h2>{html_lib.escape(project_name)}</h2>
<p style="color:#999;font-size:12px;margin-bottom:16px;">Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
{brief_html}"""


def render_style_analysis(dna, rec) -> str:
    if dna is None:
        return "<p style='color:#999'>design_dna_resolver unavailable.</p>"

    archetype  = getattr(dna, "style_archetype", "—") or "—"
    tone       = getattr(dna, "tone",            "—") or "—"
    typo_style = getattr(dna, "typography_style","—") or "—"
    icon_style = getattr(dna, "icon_style",      "—") or "—"
    layout     = getattr(dna, "layout_style",    "—") or "—"
    visual     = getattr(dna, "visual_style",    "—") or "—"
    conf       = getattr(dna, "confidence",      0.0)
    keywords   = getattr(dna, "keywords",        []) or []
    values     = getattr(dna, "brand_values",    []) or []

    psych_row = ""
    if rec:
        pref   = ", ".join(getattr(rec, "preferred_colors",  [])[:4])
        avoid  = ", ".join(getattr(rec, "avoid_colors",      [])[:3])
        sat    = getattr(rec, "saturation_level",  "—")
        temp   = getattr(rec, "color_temperature", "—")
        cstyle = getattr(rec, "contrast_style",    "—")
        psych_row = f"""
<div style="margin-top:16px">
  <div class="section-title" style="margin-bottom:12px">Color psychology</div>
  <div class="grid-2">
    <div>
      <div class="stat-label">Recommended colors</div>
      <div style="margin-top:4px">{html_lib.escape(pref or '—')}</div>
    </div>
    <div>
      <div class="stat-label">Avoid</div>
      <div style="margin-top:4px">{html_lib.escape(avoid or '—')}</div>
    </div>
    <div>
      <div class="stat-label">Saturation</div>
      <div class="stat-value">{html_lib.escape(sat)}</div>
    </div>
    <div>
      <div class="stat-label">Temperature / Contrast</div>
      <div class="stat-value">{html_lib.escape(temp)} / {html_lib.escape(cstyle)}</div>
    </div>
  </div>
</div>"""

    kw_pills  = "".join(_pill(k) for k in keywords[:8])
    val_pills = "".join(_pill(v, accent=True) for v in values[:6])

    return f"""
<div class="info-row">
  <div class="info-item">
    <div class="stat-label">Archetype</div>
    <div class="stat-value">{html_lib.escape(archetype.replace('_', ' ').title())}</div>
  </div>
  <div class="info-item">
    <div class="stat-label">Tone</div>
    <div class="stat-value">{html_lib.escape(str(tone).title())}</div>
  </div>
  <div class="info-item">
    <div class="stat-label">Confidence</div>
    <div class="stat-value">{conf:.0%}</div>
  </div>
  <div class="info-item">
    <div class="stat-label">Typography style</div>
    <div class="stat-value">{html_lib.escape(str(typo_style))}</div>
  </div>
</div>
<div class="grid-2" style="margin-bottom:16px">
  <div>
    <div class="stat-label">Icon style</div>
    <div>{html_lib.escape(str(icon_style))}</div>
  </div>
  <div>
    <div class="stat-label">Layout style</div>
    <div>{html_lib.escape(str(layout))}</div>
  </div>
  <div>
    <div class="stat-label">Visual style</div>
    <div>{html_lib.escape(str(visual))}</div>
  </div>
</div>
<div style="margin-bottom:8px">
  <div class="stat-label" style="margin-bottom:4px">Brand values</div>
  {val_pills or '<span style="color:#999">—</span>'}
</div>
<div>
  <div class="stat-label" style="margin-bottom:4px">Keywords</div>
  {kw_pills or '<span style="color:#999">—</span>'}
</div>
{psych_row}"""


def render_directions(exploration) -> str:
    if exploration is None:
        return "<p style='color:#999'>design_exploration_engine unavailable.</p>"

    directions = getattr(exploration, "directions", [])
    source     = getattr(exploration, "source_archetype", "—")

    if not directions:
        return "<p style='color:#999'>No directions generated.</p>"

    cards = []
    for d in directions:
        name      = getattr(d, "name",             "Direction")
        tagline   = getattr(d, "tagline",          "")
        archetype = getattr(d, "style_archetype",  "—")
        family    = getattr(d, "direction_family", "—") or "—"
        typo      = getattr(d, "typography_style", "—") or "—"
        icon      = getattr(d, "icon_style",       "—") or "—"
        visual    = getattr(d, "visual_style",     "—") or "—"
        motion    = getattr(d, "motion_energy",    "—") or "—"
        layout    = getattr(d, "layout_style",     "—") or "—"
        palette_b = getattr(d, "palette_bias",     []) or []
        diff      = getattr(d, "differentiation",  []) or []
        conf      = getattr(d, "confidence",       1.0)

        diff_pills = "".join(_pill(x) for x in diff[:3])
        pb_pills   = "".join(_pill(c) for c in palette_b[:4])

        cards.append(f"""
<div class="direction-card">
  <span class="badge-relation">{html_lib.escape(family)} · {conf:.0%}</span>
  <h3>{html_lib.escape(name)}</h3>
  <div class="tagline">{html_lib.escape(tagline)}</div>
  <div class="hint-grid">
    <div class="hint-row"><strong>Archetype</strong> {html_lib.escape(archetype.replace('_', ' ').title())}</div>
    <div class="hint-row"><strong>Typography</strong> {html_lib.escape(typo)}</div>
    <div class="hint-row"><strong>Icons</strong> {html_lib.escape(icon)}</div>
    <div class="hint-row"><strong>Visual style</strong> {html_lib.escape(visual)}</div>
    <div class="hint-row"><strong>Layout</strong> {html_lib.escape(layout)}</div>
    <div class="hint-row"><strong>Motion</strong> {html_lib.escape(motion)}</div>
  </div>
  {f'<div style="margin-top:10px"><div class="stat-label" style="margin-bottom:4px">Color bias</div>{pb_pills}</div>' if pb_pills else ''}
  {f'<div style="margin-top:8px"><div class="stat-label" style="margin-bottom:4px">Differentiates via</div>{diff_pills}</div>' if diff_pills else ''}
</div>""")

    grid = f'<div class="grid-3">{"".join(cards)}</div>'
    source_line = f'<div style="margin-bottom:16px"><span class="stat-label">Source archetype:</span> <strong>{html_lib.escape(str(source).replace("_"," ").title())}</strong></div>'
    return source_line + grid


def render_palette(palette_output, style_dna) -> str:
    if style_dna is None:
        return "<p style='color:#999'>Palette unavailable.</p>"

    pp = style_dna.palette_profile
    primary_hex   = pp.dominant[0]   if pp.dominant else "#2563eb"
    secondary_hex = pp.dominant[1]   if len(pp.dominant) > 1 else "#7c3aed"
    accent_hex    = pp.accent[0]     if pp.accent   else "#f97316"
    neutral_hex   = pp.neutral[0]    if pp.neutral  else "#374151"

    meta_row = f"""
<div class="info-row" style="margin-bottom:16px">
  <div><div class="stat-label">Temperature</div><div class="stat-value">{html_lib.escape(pp.temperature)}</div></div>
  <div><div class="stat-label">Saturation</div><div class="stat-value">{html_lib.escape(pp.saturation)}</div></div>
  <div><div class="stat-label">Contrast</div><div class="stat-value">{html_lib.escape(pp.contrast)}</div></div>
</div>"""

    main_swatches = f"""
<div class="swatch-group">
  <div class="swatch-group-label">Main palette</div>
  <div class="swatches">
    {_swatch(primary_hex, "primary", "lg")}
    {_swatch(secondary_hex, "secondary", "lg")}
    {_swatch(accent_hex, "accent", "lg")}
    {_swatch(neutral_hex, "neutral")}
  </div>
</div>"""

    # Additional colors from PaletteSet harmonies
    harmony_rows = ""
    if palette_output:
        ps = palette_output.palette_set
        for harm_name in ("complementary", "analogous", "triadic"):
            harm = getattr(ps, harm_name, None)
            if harm is None:
                continue
            all_cols = (
                list(getattr(harm, "primary", []))
                + list(getattr(harm, "secondary", []))
                + list(getattr(harm, "accent", []))
            )[:8]
            if not all_cols:
                continue
            swatches = "".join(_swatch(c.hex, c.role or "") for c in all_cols)
            harmony_rows += f"""
<div class="swatch-group">
  <div class="swatch-group-label">{html_lib.escape(harm_name.title())} harmony</div>
  <div class="swatches">{swatches}</div>
</div>"""

        # Tonal scale from monochromatic
        mono = getattr(ps, "monochromatic", None)
        if mono and getattr(mono, "tonal_scales", []):
            scale = mono.tonal_scales[0]
            steps = getattr(scale, "steps", [])[:10]
            if steps:
                scale_divs = "".join(
                    f'<div class="scale-step" style="background:{s.hex};color:{text_on(s.hex)}">{getattr(s, "step", "")}</div>'
                    for s in steps
                )
                harmony_rows += f"""
<div class="swatch-group" style="margin-top:12px">
  <div class="swatch-group-label">Tonal scale (monochromatic)</div>
  <div class="scale-row">{scale_divs}</div>
</div>"""

    return meta_row + main_swatches + harmony_rows


def render_typography(preset: dict | None, style_dna: "StyleDNA | None") -> str:
    if preset is None and style_dna is None:
        return "<p style='color:#999'>Typography unavailable.</p>"

    h_font = (preset or {}).get("font_family_headings", "sans-serif")
    b_font = (preset or {}).get("font_family_body", "sans-serif")
    gf_url = (preset or {}).get("font_google_url", "")
    weights = (preset or {}).get("font_weights", {})

    dp = style_dna.typography_profile if style_dna else None
    display_p = getattr(dp, "display", "—") if dp else "—"
    body_p    = getattr(dp, "body",    "—") if dp else "—"

    import_tag = f'<link rel="stylesheet" href="{gf_url}">' if gf_url else ""

    return f"""
{import_tag}
<div class="grid-2">
  <div class="typo-sample">
    <div class="typo-label">Display / Headings — {html_lib.escape(display_p)}</div>
    <div class="sample-display" style="font-family:'{h_font}',sans-serif">
      {html_lib.escape(h_font)}
    </div>
    <div class="sample-body" style="font-family:'{h_font}',sans-serif">
      Aa Bb Cc Dd — 0123456789
    </div>
  </div>
  <div class="typo-sample">
    <div class="typo-label">Body — {html_lib.escape(body_p)}</div>
    <div class="sample-display" style="font-family:'{b_font}',sans-serif;font-size:1.4rem">
      {html_lib.escape(b_font)}
    </div>
    <div class="sample-body" style="font-family:'{b_font}',sans-serif">
      The quick brown fox jumps over the lazy dog. 0123456789.
    </div>
  </div>
</div>
<div style="margin-top:16px;display:flex;gap:20px;font-size:12px;color:#888">
  <span><strong>Weights:</strong> {html_lib.escape(str(weights))}</span>
  {'<span><strong>Google Fonts:</strong> ' + html_lib.escape(gf_url[:60]) + '…</span>' if gf_url else ''}
</div>"""


def render_tokens(css: str | None, preset: dict | None) -> str:
    if css is None:
        return "<p style='color:#999'>Theme unavailable.</p>"

    variables = extract_css_variables(css)

    categories = {
        "Colors":     [k for k in variables if "--color" in k],
        "Typography": [k for k in variables if "--font" in k],
        "Spacing":    [k for k in variables if "--spacing" in k],
        "Radius":     [k for k in variables if "--border-radius" in k],
        "Shadows":    [k for k in variables if "--shadow" in k],
        "Animation":  [k for k in variables if "--transition" in k or "--hover" in k],
    }

    rows = []
    for cat, keys in categories.items():
        if not keys:
            continue
        rows.append(f'<tr class="token-section-header"><td colspan="2">{html_lib.escape(cat)}</td></tr>')
        for k in sorted(keys):
            v = variables[k]
            dot = ""
            if ("color" in k or "shadow" in k.lower()) and v.startswith("rgb"):
                dot = f'<span class="color-dot" style="background:{v}"></span>'
            elif k.startswith("--color") and (v.startswith("#") or "rgb" in v):
                dot = f'<span class="color-dot" style="background:{v}"></span>'
            rows.append(f"<tr><td>{html_lib.escape(k)}</td><td>{dot}{html_lib.escape(v)}</td></tr>")

    table = f'<table class="tokens-table"><thead><tr><th>Token</th><th>Value</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'
    return table


# ── Rendering Contracts ───────────────────────────────────────────────────────
# A RenderingContract is the executable binding between a creative direction
# and the preview renderer. It is derived from direction.style_archetype.
# The renderer consumes ONLY the contract — no fallback to generic SaaS layout.

from dataclasses import dataclass as _dc, field as _field

@_dc
class RenderingContract:
    """Strict rendering spec derived from a DesignDirection."""
    direction_id:     str
    direction_name:   str
    archetype:        str

    # Structural tokens — each maps 1:1 to a renderer function
    hero_pattern:     str   # editorial | playful | luxury | warm_split | corporate | centered | dark_tech | raw_bold
    button_family:    str   # text_link | pill | ghost_thin | soft_rounded | corporate | solid | neon_border | raw_border
    card_family:      str   # rule_only | dashed_rounded | line_separator | soft_card | bordered_table | elevated | dark_card | thick_border
    heading_alignment:str   # left | center
    layout_rhythm:    str   # editorial | playful | airy | balanced | dense
    shadow_style:     str   # none | warm_soft | subtle | strong | glow | hard_offset
    radius_profile:   str   # zero | small | medium | large | pill

    # Colors (from preset — same across directions, structure differentiates)
    primary:   str
    secondary: str

    # Fonts (resolved from preset)
    heading_font: str
    body_font:    str


# Strict archetype → contract values. Every archetype has a distinct hero/button/card triplet.
# There is NO shared default — each archetype is explicitly defined.
_ARCHETYPE_CONTRACTS: dict[str, dict] = {
    "editorial_magazine": dict(
        hero_pattern="editorial",   button_family="text_link",   card_family="rule_only",
        heading_alignment="left",   layout_rhythm="editorial",
        shadow_style="none",        radius_profile="zero",
    ),
    "luxury_minimal": dict(
        hero_pattern="luxury",      button_family="ghost_thin",  card_family="line_separator",
        heading_alignment="center", layout_rhythm="airy",
        shadow_style="none",        radius_profile="zero",
    ),
    "playful_brand": dict(
        hero_pattern="playful",     button_family="pill",        card_family="dashed_rounded",
        heading_alignment="center", layout_rhythm="playful",
        shadow_style="warm_soft",   radius_profile="pill",
    ),
    "warm_human": dict(
        hero_pattern="warm_split",  button_family="soft_rounded", card_family="soft_card",
        heading_alignment="left",   layout_rhythm="airy",
        shadow_style="warm_soft",   radius_profile="large",
    ),
    "startup_clean": dict(
        hero_pattern="centered",    button_family="solid",        card_family="elevated",
        heading_alignment="center", layout_rhythm="balanced",
        shadow_style="subtle",      radius_profile="small",
    ),
    "corporate_pro": dict(
        hero_pattern="corporate",   button_family="corporate",    card_family="bordered_table",
        heading_alignment="left",   layout_rhythm="balanced",
        shadow_style="subtle",      radius_profile="small",
    ),
    "tech_futurist": dict(
        hero_pattern="dark_tech",   button_family="neon_border",  card_family="dark_card",
        heading_alignment="center", layout_rhythm="dense",
        shadow_style="glow",        radius_profile="small",
    ),
    "brutalist": dict(
        hero_pattern="raw_bold",    button_family="raw_border",   card_family="thick_border",
        heading_alignment="left",   layout_rhythm="dense",
        shadow_style="hard_offset", radius_profile="zero",
    ),
    "organic_natural": dict(
        hero_pattern="warm_split",  button_family="soft_rounded", card_family="soft_card",
        heading_alignment="left",   layout_rhythm="airy",
        shadow_style="warm_soft",   radius_profile="large",
    ),
    "premium_craft": dict(
        hero_pattern="luxury",      button_family="ghost_thin",   card_family="line_separator",
        heading_alignment="left",   layout_rhythm="airy",
        shadow_style="none",        radius_profile="small",
    ),
    "bold_challenger": dict(
        hero_pattern="raw_bold",    button_family="raw_border",   card_family="thick_border",
        heading_alignment="left",   layout_rhythm="dense",
        shadow_style="none",        radius_profile="zero",
    ),
    "creative_studio": dict(
        hero_pattern="centered",    button_family="pill",         card_family="dashed_rounded",
        heading_alignment="center", layout_rhythm="playful",
        shadow_style="warm_soft",   radius_profile="large",
    ),
}

_CONTRACT_FALLBACK = _ARCHETYPE_CONTRACTS["startup_clean"]


def derive_rendering_contract(
    direction,          # DesignDirection object (or dict with same keys)
    primary: str,
    secondary: str,
    heading_font: str,
    body_font: str,
) -> RenderingContract:
    """
    Derive a strict RenderingContract from a DesignDirection.
    Uses direction.style_archetype as the key — no fallback to generic layout.
    """
    archetype = (
        getattr(direction, "style_archetype", None)
        or (direction.get("style_archetype") if isinstance(direction, dict) else None)
        or "startup_clean"
    )
    d_id   = getattr(direction, "id",   None) or direction.get("id",   "dir")   if not isinstance(direction, str) else "dir"
    d_name = getattr(direction, "name", None) or direction.get("name", archetype) if not isinstance(direction, str) else archetype
    base = _ARCHETYPE_CONTRACTS.get(archetype, _CONTRACT_FALLBACK)
    return RenderingContract(
        direction_id=d_id,
        direction_name=d_name,
        archetype=archetype,
        primary=primary,
        secondary=secondary,
        heading_font=heading_font,
        body_font=body_font,
        **base,
    )


# ── Per-contract renderers (no internal fallback — each mode is explicit) ─────

def _render_hero_from_contract(c: RenderingContract) -> str:
    p, hf, bf = c.primary, c.heading_font, c.body_font
    r = {"zero":"0px","small":"6px","medium":"10px","large":"16px","pill":"24px"}.get(c.radius_profile,"6px")

    if c.hero_pattern == "editorial":
        return f"""<div style="background:#fff;padding:52px 0 36px;border-bottom:2px solid #111">
  <div style="max-width:680px">
    <div style="font-size:9px;letter-spacing:.3em;text-transform:uppercase;color:#aaa;margin-bottom:20px">N°47 · PRINTEMPS 2026</div>
    <h1 style="font-family:'{hf}',Georgia,'Times New Roman',serif;font-size:4rem;font-weight:300;line-height:.95;letter-spacing:-.02em;color:#111;margin-bottom:20px">La beauté<br>du silence</h1>
    <div style="width:40px;height:2px;background:#111;margin-bottom:20px"></div>
    <p style="font-family:'{bf}',sans-serif;font-size:14px;color:#555;line-height:1.75;max-width:540px;margin-bottom:24px">Un essai sur la contemplation, la lenteur et les formes que prend l'attention dans une époque saturée de bruit et d'images.</p>
    <span style="font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:#111;border-bottom:1px solid #111;padding-bottom:2px;cursor:pointer">LIRE L'ARTICLE →</span>
  </div>
</div>"""

    if c.hero_pattern == "luxury":
        return f"""<div style="background:#0a0a0a;padding:72px 40px;text-align:center">
  <div style="font-size:8px;letter-spacing:.45em;text-transform:uppercase;color:#555;margin-bottom:32px">EST. MMXXVI</div>
  <h1 style="font-family:'{hf}',Georgia,'Times New Roman',serif;font-size:3.5rem;font-weight:200;color:#f0ebe3;letter-spacing:.06em;line-height:1.25;margin-bottom:20px">A world apart</h1>
  <div style="width:36px;height:1px;background:#444;margin:0 auto 28px"></div>
  <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#888;letter-spacing:.08em;max-width:360px;margin:0 auto 36px;line-height:1.9">For those who seek substance over spectacle.</p>
  <button style="background:transparent;color:#e0dbd4;border:1px solid #555;padding:11px 40px;border-radius:0;font-size:9px;letter-spacing:.28em;text-transform:uppercase;cursor:pointer">DISCOVER</button>
</div>"""

    if c.hero_pattern == "playful":
        return f"""<div style="background:{p};padding:56px 32px;border-radius:{r};text-align:center">
  <div style="font-size:3.2rem;margin-bottom:16px">🕯️ ✨ 🎉</div>
  <h1 style="font-family:'{hf}',sans-serif;font-size:2.8rem;font-weight:800;color:#fff;line-height:1.1;margin-bottom:14px">Make their day<br>unforgettable!</h1>
  <p style="font-family:'{bf}',sans-serif;color:rgba(255,255,255,.82);max-width:380px;margin:0 auto 28px;font-size:15px;line-height:1.65">Create a magical birthday page in minutes. Send joy, not just a message.</p>
  <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
    <button style="background:#fff;color:{p};border:none;padding:14px 32px;border-radius:100px;font-size:15px;font-weight:700;cursor:pointer">🎂 Create a page</button>
    <button style="background:rgba(255,255,255,.15);color:#fff;border:2px solid rgba(255,255,255,.5);padding:14px 28px;border-radius:100px;font-size:14px;cursor:pointer">See examples →</button>
  </div>
</div>"""

    if c.hero_pattern == "warm_split":
        return f"""<div style="background:#fff5f0;padding:48px 36px">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:center">
    <div>
      <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:#999;margin-bottom:16px">COMMUNITY PLATFORM</div>
      <h1 style="font-family:'{hf}',sans-serif;font-size:2.4rem;font-weight:600;color:#1a1a1a;line-height:1.2;margin-bottom:16px">Built for people,<br>not pipelines</h1>
      <p style="font-family:'{bf}',sans-serif;font-size:14px;color:#666;line-height:1.7;margin-bottom:24px">Real connection. Real care. Technology that feels human.</p>
      <button style="background:{p};color:#fff;border:none;padding:12px 28px;border-radius:12px;font-size:14px;font-weight:600;cursor:pointer">Get started</button>
    </div>
    <div style="background:#fff;border-radius:16px;padding:28px;box-shadow:0 4px 20px rgba(0,0,0,.06)">
      <p style="font-family:'{bf}',sans-serif;font-size:14px;font-style:italic;color:#555;line-height:1.7;margin-bottom:16px">"This changed how we connect as a team — it feels like it was made for us."</p>
      <div style="display:flex;align-items:center;gap:12px">
        <div style="width:36px;height:36px;border-radius:50%;background:#f0e0d8"></div>
        <div style="font-size:12px;color:#999">Sarah M. · Product Designer</div>
      </div>
    </div>
  </div>
</div>"""

    if c.hero_pattern == "corporate":
        return f"""<div style="background:#f8f9fa;padding:48px 40px;border-left:4px solid {p}">
  <div style="max-width:560px">
    <div style="font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:{p};margin-bottom:16px">ENTERPRISE PLATFORM</div>
    <h1 style="font-family:'{hf}',sans-serif;font-size:2.4rem;font-weight:700;color:#111;line-height:1.2;margin-bottom:18px">Build something<br>meaningful</h1>
    <p style="font-family:'{bf}',sans-serif;font-size:14px;color:#555;line-height:1.7;margin-bottom:24px">Trusted by 2,000+ organizations worldwide. SOC 2 compliant.</p>
    <div style="display:flex;gap:12px">
      <button style="background:{p};color:#fff;border:none;padding:12px 24px;border-radius:4px;font-size:13px;font-weight:600;cursor:pointer">Schedule a demo</button>
      <button style="background:transparent;color:{p};border:1.5px solid {p};padding:12px 24px;border-radius:4px;font-size:13px;cursor:pointer">Learn more</button>
    </div>
  </div>
</div>"""

    if c.hero_pattern == "dark_tech":
        return f"""<div style="background:#0d1117;padding:56px 32px;text-align:center">
  <div style="font-size:9px;letter-spacing:.25em;text-transform:uppercase;color:#3b82f6;margin-bottom:20px">INFRASTRUCTURE PLATFORM v3</div>
  <h1 style="font-family:'{hf}',sans-serif;font-size:2.8rem;font-weight:700;color:#e2e8f0;line-height:1.1;margin-bottom:16px">Build faster.<br>Scale smarter.</h1>
  <p style="font-family:'{bf}',sans-serif;color:#6b7280;max-width:440px;margin:0 auto 28px;font-size:14px;line-height:1.7">Zero-downtime deployments. Real-time observability. Full control.</p>
  <div style="display:flex;gap:12px;justify-content:center">
    <button style="background:{p};color:#fff;border:none;padding:12px 28px;border-radius:4px;font-size:13px;font-weight:600;cursor:pointer">Start for free →</button>
    <button style="background:transparent;color:#94a3b8;border:1px solid #374151;padding:12px 28px;border-radius:4px;font-size:13px;cursor:pointer">View docs</button>
  </div>
</div>"""

    if c.hero_pattern == "raw_bold":
        return f"""<div style="background:#fff;padding:40px;border:3px solid #111">
  <div style="font-size:8px;letter-spacing:.25em;color:#999;margin-bottom:16px">THE CHALLENGER PLATFORM / V.1 / 2026</div>
  <h1 style="font-family:'{hf}',sans-serif;font-size:4rem;font-weight:900;color:#111;line-height:.88;text-transform:uppercase;margin-bottom:24px">BUILD.<br>BREAK.<br>WIN.</h1>
  <button style="background:#111;color:#fff;border:none;padding:14px 36px;border-radius:0;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;cursor:pointer">START NOW →</button>
</div>"""

    # centered — startup_clean default
    return f"""<div style="background:{p};padding:52px 32px;text-align:center;border-radius:{r}">
  <h1 style="font-family:'{hf}',sans-serif;color:#fff;font-size:2.4rem;font-weight:700;margin-bottom:12px;line-height:1.1">Build something meaningful</h1>
  <p style="font-family:'{bf}',sans-serif;color:rgba(255,255,255,.82);max-width:480px;margin:0 auto 24px;font-size:15px;line-height:1.65">A platform built for people who care about craft, clarity, and impact.</p>
  <div style="display:flex;gap:12px;justify-content:center">
    <button style="background:#fff;color:{p};border:none;padding:12px 24px;border-radius:{r};font-size:14px;font-weight:600;cursor:pointer">Get started</button>
    <button style="background:rgba(255,255,255,.14);color:#fff;border:1px solid rgba(255,255,255,.45);padding:12px 24px;border-radius:{r};font-size:14px;cursor:pointer">Learn more</button>
  </div>
</div>"""


def _render_buttons_from_contract(c: RenderingContract) -> str:
    p, s, hf = c.primary, c.secondary, c.heading_font
    r = {"zero":"0px","small":"5px","medium":"8px","large":"12px","pill":"100px"}.get(c.radius_profile,"5px")

    if c.button_family == "text_link":
        return f"""<div style="display:flex;gap:32px;align-items:center;flex-wrap:wrap;padding:4px 0">
  <span style="font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:#111;border-bottom:1px solid #111;padding-bottom:2px;cursor:pointer">LIRE L'ARTICLE →</span>
  <span style="font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:#aaa;cursor:pointer">S'ABONNER</span>
  <span style="font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:#aaa;cursor:pointer">ARCHIVES</span>
</div>"""

    if c.button_family == "pill":
        return f"""<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
  <button style="background:{p};color:#fff;border:none;padding:12px 28px;border-radius:100px;font-size:14px;font-weight:700;cursor:pointer">🎂 Primary</button>
  <button style="background:{s};color:#fff;border:none;padding:12px 28px;border-radius:100px;font-size:14px;font-weight:600;cursor:pointer">Secondary</button>
  <button style="background:transparent;color:{p};border:2px solid {p};padding:12px 28px;border-radius:100px;font-size:14px;cursor:pointer">Outline</button>
  <button style="background:transparent;color:#999;border:2px dashed #ddd;padding:12px 28px;border-radius:100px;font-size:14px;cursor:pointer">Ghost ✨</button>
</div>"""

    if c.button_family == "ghost_thin":
        return f"""<div style="display:flex;gap:20px;flex-wrap:wrap;align-items:center">
  <button style="background:transparent;color:#111;border:1px solid #888;padding:10px 32px;border-radius:0;font-size:9px;letter-spacing:.2em;text-transform:uppercase;cursor:pointer">DISCOVER</button>
  <button style="background:transparent;color:#aaa;border:1px solid #ddd;padding:10px 32px;border-radius:0;font-size:9px;letter-spacing:.2em;text-transform:uppercase;cursor:pointer">COLLECTION</button>
  <span style="font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:#999;cursor:pointer">VIEW MORE →</span>
</div>"""

    if c.button_family == "soft_rounded":
        return f"""<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
  <button style="background:{p};color:#fff;border:none;padding:12px 28px;border-radius:12px;font-size:14px;font-weight:600;cursor:pointer">Get started</button>
  <button style="background:#f5f5f5;color:#333;border:none;padding:12px 28px;border-radius:12px;font-size:14px;cursor:pointer">Learn more</button>
  <button style="background:transparent;color:{p};border:1.5px solid {p};padding:12px 28px;border-radius:12px;font-size:14px;cursor:pointer">Outline</button>
</div>"""

    if c.button_family == "corporate":
        return f"""<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
  <button style="background:{p};color:#fff;border:none;padding:11px 24px;border-radius:4px;font-size:13px;font-weight:600;cursor:pointer">Schedule a demo</button>
  <button style="background:transparent;color:{p};border:1.5px solid {p};padding:11px 24px;border-radius:4px;font-size:13px;cursor:pointer">Learn more</button>
  <button style="background:transparent;color:#666;border:1.5px solid #ddd;padding:11px 24px;border-radius:4px;font-size:13px;cursor:pointer">Download PDF</button>
</div>"""

    if c.button_family == "neon_border":
        return f"""<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;background:#0d1117;padding:20px">
  <button style="background:transparent;color:{p};border:1px solid {p};padding:11px 24px;border-radius:4px;font-size:12px;font-weight:600;letter-spacing:.05em;cursor:pointer">Deploy →</button>
  <button style="background:{p};color:#fff;border:none;padding:11px 24px;border-radius:4px;font-size:12px;font-weight:600;letter-spacing:.05em;cursor:pointer">Start free</button>
  <button style="background:transparent;color:#6b7280;border:1px solid #374151;padding:11px 24px;border-radius:4px;font-size:12px;cursor:pointer">View docs</button>
</div>"""

    if c.button_family == "raw_border":
        return f"""<div style="display:flex;gap:0;flex-wrap:wrap;align-items:center">
  <button style="background:#111;color:#fff;border:3px solid #111;padding:12px 28px;border-radius:0;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;cursor:pointer">PRIMARY</button>
  <button style="background:#fff;color:#111;border:3px solid #111;padding:12px 28px;border-radius:0;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;border-left:none;cursor:pointer">SECONDARY</button>
  <button style="background:{p};color:#fff;border:3px solid {p};padding:12px 28px;border-radius:0;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;border-left:none;cursor:pointer">ACCENT</button>
</div>"""

    # solid — startup_clean default
    return f"""<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
  <button style="background:{p};color:#fff;border:none;padding:12px 24px;border-radius:{r};font-size:14px;font-weight:600;cursor:pointer">Primary</button>
  <button style="background:{s};color:#fff;border:none;padding:12px 24px;border-radius:{r};font-size:14px;font-weight:600;cursor:pointer">Secondary</button>
  <button style="background:transparent;color:{p};border:1.5px solid {p};padding:12px 24px;border-radius:{r};font-size:14px;cursor:pointer">Outline</button>
  <button style="background:transparent;color:#666;border:1.5px solid #ddd;padding:12px 24px;border-radius:{r};font-size:14px;cursor:pointer">Ghost</button>
</div>"""


def _render_cards_from_contract(c: RenderingContract) -> str:
    p, hf, bf = c.primary, c.heading_font, c.body_font
    r = {"zero":"0px","small":"5px","medium":"8px","large":"14px","pill":"20px"}.get(c.radius_profile,"5px")
    shadow = {
        "none":"none","warm_soft":"0 4px 20px rgba(0,0,0,.06)",
        "subtle":"0 1px 4px rgba(0,0,0,.08)","strong":"0 8px 32px rgba(0,0,0,.14)",
        "glow":f"0 0 20px rgba(37,99,235,.2)","hard_offset":"4px 4px 0 #111",
    }.get(c.shadow_style,"0 1px 4px rgba(0,0,0,.08)")

    if c.card_family == "rule_only":
        return f"""<div style="border-top:2px solid #111">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0">
    <div style="padding:24px 32px 24px 0;border-right:1px solid #e8e8e8">
      <div style="font-size:8px;letter-spacing:.18em;text-transform:uppercase;color:#bbb;margin-bottom:12px">ESSAI · PHILOSOPHIE</div>
      <h3 style="font-family:'{hf}',Georgia,serif;font-size:1.15rem;font-weight:400;color:#111;margin-bottom:10px;line-height:1.45">La lenteur comme résistance</h3>
      <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#777;line-height:1.75">Une réflexion sur le rapport au temps dans les pratiques créatives contemporaines.</p>
      <div style="margin-top:16px;font-size:9px;color:#bbb;letter-spacing:.06em">par S. Laurent · 12 min</div>
    </div>
    <div style="padding:24px 0 24px 32px">
      <div style="font-size:8px;letter-spacing:.18em;text-transform:uppercase;color:#bbb;margin-bottom:12px">CRITIQUE · ART</div>
      <h3 style="font-family:'{hf}',Georgia,serif;font-size:1.15rem;font-weight:400;color:#111;margin-bottom:10px;line-height:1.45">Ce que le vide dit de nous</h3>
      <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#777;line-height:1.75">Analyse des pratiques minimalistes dans l'art contemporain européen.</p>
      <div style="margin-top:16px;font-size:9px;color:#bbb;letter-spacing:.06em">par M. Dupont · 8 min</div>
    </div>
  </div>
</div>"""

    if c.card_family == "dashed_rounded":
        return f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
  <div style="background:#fff8f0;border:2px dashed rgba(0,0,0,.14);border-radius:{r};padding:28px;text-align:center">
    <div style="font-size:2.2rem;margin-bottom:12px">🎂</div>
    <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:700;color:#111;margin-bottom:8px">Birthday Pages</h3>
    <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#777;line-height:1.65">Photos, music, and heartfelt messages.</p>
  </div>
  <div style="background:#f0fff8;border:2px dashed rgba(0,0,0,.14);border-radius:{r};padding:28px;text-align:center">
    <div style="font-size:2.2rem;margin-bottom:12px">✨</div>
    <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:700;color:#111;margin-bottom:8px">Sparkle Effects</h3>
    <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#777;line-height:1.65">Confetti, animations, festive energy.</p>
  </div>
</div>"""

    if c.card_family == "line_separator":
        return f"""<div>
  <div style="padding:20px 0;border-bottom:1px solid #e0e0e0;display:flex;justify-content:space-between;align-items:baseline">
    <div>
      <h3 style="font-family:'{hf}',Georgia,serif;font-size:1rem;font-weight:300;color:#111;letter-spacing:.02em">Craftsmanship</h3>
      <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#aaa;margin-top:4px">Every detail considered, nothing superfluous.</p>
    </div>
    <span style="font-size:9px;letter-spacing:.1em;color:#ccc">01</span>
  </div>
  <div style="padding:20px 0;border-bottom:1px solid #e0e0e0;display:flex;justify-content:space-between;align-items:baseline">
    <div>
      <h3 style="font-family:'{hf}',Georgia,serif;font-size:1rem;font-weight:300;color:#111;letter-spacing:.02em">Discretion</h3>
      <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#aaa;margin-top:4px">No noise. No excess. Only what matters.</p>
    </div>
    <span style="font-size:9px;letter-spacing:.1em;color:#ccc">02</span>
  </div>
  <div style="padding:20px 0;display:flex;justify-content:space-between;align-items:baseline">
    <div>
      <h3 style="font-family:'{hf}',Georgia,serif;font-size:1rem;font-weight:300;color:#111;letter-spacing:.02em">Longevity</h3>
      <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#aaa;margin-top:4px">Timeless, not trending.</p>
    </div>
    <span style="font-size:9px;letter-spacing:.1em;color:#ccc">03</span>
  </div>
</div>"""

    if c.card_family == "soft_card":
        return f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
  <div style="background:#fff;border-radius:{r};padding:24px;box-shadow:{shadow};border:1px solid rgba(0,0,0,.04)">
    <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:600;color:#1a1a1a;margin-bottom:8px">For individuals</h3>
    <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#888;line-height:1.7">Personal tools that adapt to how you think and work.</p>
  </div>
  <div style="background:#fff;border-radius:{r};padding:24px;box-shadow:{shadow};border:1px solid rgba(0,0,0,.04)">
    <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:600;color:#1a1a1a;margin-bottom:8px">For teams</h3>
    <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#888;line-height:1.7">Shared spaces that bring people closer, not further apart.</p>
  </div>
</div>"""

    if c.card_family == "bordered_table":
        return f"""<div style="border:1.5px solid #e0e0e0;border-radius:4px;overflow:hidden">
  <div style="display:grid;grid-template-columns:auto 1fr 1fr;border-bottom:1px solid #e8e8e8;background:#f9f9f9">
    <div style="padding:10px 16px;font-size:10px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:.08em;border-right:1px solid #e8e8e8">Feature</div>
    <div style="padding:10px 16px;font-size:10px;font-weight:700;color:{p};text-transform:uppercase;letter-spacing:.08em;border-right:1px solid #e8e8e8;text-align:center">Pro</div>
    <div style="padding:10px 16px;font-size:10px;font-weight:700;color:#999;text-transform:uppercase;letter-spacing:.08em;text-align:center">Enterprise</div>
  </div>
  <div style="display:grid;grid-template-columns:auto 1fr 1fr;border-bottom:1px solid #f0f0f0">
    <div style="padding:12px 16px;font-size:12px;color:#444;border-right:1px solid #f0f0f0">SSO / SAML</div>
    <div style="padding:12px 16px;font-size:12px;color:{p};text-align:center;border-right:1px solid #f0f0f0">✓</div>
    <div style="padding:12px 16px;font-size:12px;color:{p};text-align:center">✓</div>
  </div>
  <div style="display:grid;grid-template-columns:auto 1fr 1fr">
    <div style="padding:12px 16px;font-size:12px;color:#444;border-right:1px solid #f0f0f0">Audit logs</div>
    <div style="padding:12px 16px;font-size:12px;color:#ccc;text-align:center;border-right:1px solid #f0f0f0">—</div>
    <div style="padding:12px 16px;font-size:12px;color:{p};text-align:center">✓</div>
  </div>
</div>"""

    if c.card_family == "dark_card":
        return f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
  <div style="background:#161b22;border:1px solid #30363d;border-radius:{r};padding:24px">
    <div style="font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:#3b82f6;margin-bottom:12px">COMPUTE</div>
    <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:600;color:#e2e8f0;margin-bottom:8px">Auto-scaling</h3>
    <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#6b7280;line-height:1.65">Scales from 0 to 10k instances in seconds.</p>
  </div>
  <div style="background:#161b22;border:1px solid #30363d;border-radius:{r};padding:24px">
    <div style="font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:#10b981;margin-bottom:12px">OBSERVABILITY</div>
    <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:600;color:#e2e8f0;margin-bottom:8px">Real-time metrics</h3>
    <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#6b7280;line-height:1.65">Full-stack traces, logs and alerts.</p>
  </div>
</div>"""

    if c.card_family == "thick_border":
        return f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:0">
  <div style="border:3px solid #111;padding:24px">
    <div style="font-size:8px;letter-spacing:.2em;color:#999;margin-bottom:10px">01 / FUNCTION</div>
    <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:900;text-transform:uppercase;color:#111;margin-bottom:8px">Raw power</h3>
    <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#444;line-height:1.65">No compromise. No bloat. Just function.</p>
  </div>
  <div style="border:3px solid #111;border-left:none;padding:24px">
    <div style="font-size:8px;letter-spacing:.2em;color:#999;margin-bottom:10px">02 / CONTROL</div>
    <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:900;text-transform:uppercase;color:#111;margin-bottom:8px">Your rules</h3>
    <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#444;line-height:1.65">Total ownership. Zero abstraction.</p>
  </div>
</div>"""

    # elevated — startup_clean default
    return f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
  <div style="background:#fff;border-radius:{r};padding:24px;box-shadow:{shadow};border:1px solid rgba(0,0,0,.05)">
    <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:600;color:#111;margin-bottom:8px">Feature title</h3>
    <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#666;line-height:1.65">Shape, shadow, and radius are derived from the visual profile.</p>
  </div>
  <div style="background:#fff;border-radius:{r};padding:24px;box-shadow:{shadow};border:1px solid rgba(0,0,0,.05)">
    <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:600;color:#111;margin-bottom:8px">Another feature</h3>
    <p style="font-family:'{bf}',sans-serif;font-size:12px;color:#666;line-height:1.65">Every contract produces a visually distinct result.</p>
  </div>
</div>"""


def render_direction_preview(contract: RenderingContract, scoped_css: str, font_import: str) -> str:
    """
    Render a single creative direction as a self-contained preview block.
    Consumes ONLY the RenderingContract — no external fallback.
    """
    hero    = _render_hero_from_contract(contract)
    buttons = _render_buttons_from_contract(contract)
    cards   = _render_cards_from_contract(contract)

    bg = "#0d1117" if contract.hero_pattern == "dark_tech" else "#fff"
    txt_color = "#e2e8f0" if contract.hero_pattern == "dark_tech" else "#444"

    return f"""
<div style="margin-bottom:32px;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
  <!-- Direction header -->
  <div style="background:#f5f5f5;padding:10px 20px;border-bottom:1px solid #e0e0e0;display:flex;align-items:center;gap:12px">
    <span style="font-size:11px;font-weight:700;color:#111">{contract.direction_name}</span>
    <span style="font-size:10px;color:#999;font-family:monospace">{contract.archetype}</span>
    <span style="margin-left:auto;font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#bbb">{contract.hero_pattern} / {contract.button_family} / {contract.card_family}</span>
  </div>
  <!-- Hero -->
  <div style="border-bottom:1px solid #eee">
    <div style="font-size:9px;text-transform:uppercase;letter-spacing:.1em;color:#bbb;padding:5px 12px;background:#fafafa;border-bottom:1px solid #f0f0f0">HERO</div>
    {hero}
  </div>
  <!-- Buttons -->
  <div style="border-bottom:1px solid #eee">
    <div style="font-size:9px;text-transform:uppercase;letter-spacing:.1em;color:#bbb;padding:5px 12px;background:#fafafa;border-bottom:1px solid #f0f0f0">BUTTONS</div>
    <div style="padding:20px 24px;background:{bg}">
      {buttons}
    </div>
  </div>
  <!-- Cards -->
  <div>
    <div style="font-size:9px;text-transform:uppercase;letter-spacing:.1em;color:#bbb;padding:5px 12px;background:#fafafa;border-bottom:1px solid #f0f0f0">CARDS</div>
    <div style="padding:20px 24px;background:{bg}">
      {cards}
    </div>
  </div>
</div>"""


def render_preview(preset: dict | None, css: str | None, style_dna=None, exploration=None) -> str:
    if preset is None or css is None:
        return "<p style=\'color:#999\'>Preview unavailable — theme generation failed.</p>"

    h_font = preset.get("font_family_headings", "sans-serif")
    b_font = preset.get("font_family_body",     "sans-serif")
    gf_url = preset.get("font_google_url", "")
    font_import = f'@import url("{gf_url}");' if gf_url else ""

    cs        = preset.get("color_system", {})
    primary   = cs.get("primary",   {}).get("base", "#2563eb")
    secondary = cs.get("secondary", {}).get("base", "#7c3aed")

    # Scope the theme CSS to avoid bleeding into the charter chrome
    scoped_css = css.replace(":root", "#preview-root")

    # Get directions from exploration output
    directions = []
    if exploration is not None:
        directions = getattr(exploration, "directions", []) or []

    if not directions:
        # Fallback: single preview from style_dna archetype tag
        archetype = "startup_clean"
        if style_dna:
            tags = getattr(style_dna, "aesthetic_tags", []) or []
            if tags:
                archetype = tags[0]

        class _FakeDir:
            id = "dir_0"; name = archetype; style_archetype = archetype
        contract = derive_rendering_contract(_FakeDir(), primary, secondary, h_font, b_font)
        block = render_direction_preview(contract, scoped_css, font_import)
        style_block = f"<style>{font_import}\n{scoped_css}</style>"
        return style_block + f'<div id="preview-root">{block}</div>'

    # One RenderingContract per direction → one preview block per direction
    blocks = []
    for d in directions:
        contract = derive_rendering_contract(d, primary, secondary, h_font, b_font)
        blocks.append(render_direction_preview(contract, scoped_css, font_import))

    style_block = f"<style>{font_import}\n{scoped_css}</style>"
    return style_block + f'<div id="preview-root">{"".join(blocks)}</div>'


def render_raw_json(style_dna, palette_output, preset) -> str:
    parts = []
    if style_dna is not None:
        parts.append(_json_collapsible("style_dna.json", asdict(style_dna)))
    if palette_output is not None:
        try:
            palette_dict = asdict(palette_output.palette_set)
        except Exception:
            palette_dict = {"error": "could not serialize"}
        parts.append(_json_collapsible("palette.json", palette_dict))
    if preset is not None:
        parts.append(_json_collapsible("theme_preset.json", preset))
    return "".join(parts) if parts else "<p style='color:#999'>No data.</p>"

# ── Full HTML assembly ────────────────────────────────────────────────────────

def generate_html(
    project_name: str,
    brief_text: str,
    dna,
    rec,
    palette_output,
    exploration,
    style_dna,
    preset: dict | None,
    css:    str  | None,
    pipeline_ok: dict,
) -> str:

    sections = [
        _section("01 · Project overview",
                 render_overview(project_name, brief_text, pipeline_ok)),
        _section("02 · Style analysis",
                 render_style_analysis(dna, rec)),
        _section("03 · Creative directions",
                 render_directions(exploration)),
        _section("04 · Palette",
                 render_palette(palette_output, style_dna)),
        _section("05 · Typography",
                 render_typography(preset, style_dna)),
        _section("06 · Theme tokens",
                 render_tokens(css, preset)),
        _section("07 · UI Preview",
                 render_preview(preset, css, style_dna, exploration)),
        _section("08 · Raw JSON",
                 render_raw_json(style_dna, palette_output, preset)),
    ]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_lib.escape(project_name)} — Brand Charter · EURKAI</title>
  <style>{_CHROME_CSS}</style>
</head>
<body>
<div class="page-wrap">
  <header class="charter-header">
    <div>
      <span class="badge">EURKAI</span>
      <span class="badge">pipeline-validator</span>
    </div>
    <h1>{html_lib.escape(project_name)}</h1>
    <div class="meta">Brand Charter · Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
  </header>
  {"".join(sections)}
</div>
</body>
</html>"""

# ── Test briefs ───────────────────────────────────────────────────────────────

TEST_BRIEFS: list[tuple[str, str]] = [
    (
        "VectorStack",
        textwrap.dedent("""\
        A modern SaaS platform for data infrastructure automation.
        The product targets engineers and CTOs who want reliability and control.
        The brand should feel precise, geometric, intelligent, minimal, trustworthy.
        Avoid startup clichés and overly bright colors.
        Preferred visual universe: Swiss design, modern tech interfaces, clean geometry,
        structured layouts.
        Tone: serious but elegant.
        The system should produce a visual identity that works well for dashboards,
        documentation, and developer tools.
        Industry: SaaS / data infrastructure / developer tools.
        Keywords: precision, control, reliability, automation, infrastructure.
        """),
    ),
    (
        "Atelier Nocturne",
        textwrap.dedent("""\
        An independent magazine exploring culture, philosophy and contemporary art.
        Audience: curious, educated readers interested in slow thinking and aesthetics.
        The brand should feel editorial, refined, contemplative, intellectual, timeless.
        Preferred references: European editorial design, art catalogues, museum publications.
        Tone: quiet, elegant, slightly mysterious.
        The identity should work well for long-form reading and print-inspired layouts.
        Industry: editorial / culture / art publishing.
        Keywords: culture, philosophy, aesthetics, slow reading, contemplation.
        """),
    ),
    (
        "CandleSpark",
        textwrap.dedent("""\
        A playful brand for personalized birthday websites.
        Users create small celebratory pages for friends and family.
        The brand should feel joyful, warm, handmade, festive, a little chaotic in a charming way.
        Visual universe: candles, sparkles, confetti, stickers, celebration elements.
        Tone: friendly, colorful, slightly imperfect.
        The identity must feel emotional and human rather than corporate.
        Industry: consumer / gifting / celebration.
        Keywords: birthday, celebration, personalization, joy, warmth, festive.
        """),
    ),
]


# ── Landing Page Generator ────────────────────────────────────────────────────
# Generates one complete standalone landing page per project.
# Picks the creative direction that best matches the brief.
# Output: output/<project>/landing_page.html

def _select_direction(exploration, brief_text: str):
    """
    Pick the single creative direction that best matches the brief.
    Uses keyword signals to override the primary direction when appropriate.
    """
    if exploration is None:
        return None
    directions = getattr(exploration, "directions", []) or []
    if not directions:
        return None

    brief_lower = brief_text.lower()

    # Signal mapping: if brief contains these words → prefer this archetype
    BRIEF_SIGNALS = [
        (["editorial", "magazine", "revue", "publication", "art publishing", "museum", "culture", "philosophy"], "editorial_magazine"),
        (["birthday", "celebration", "confetti", "sparkle", "festive", "playful", "candles", "gifting"], "playful_brand"),
        (["luxury", "premium", "haute", "exclusive", "couture", "maison"], "luxury_minimal"),
        (["brutalist", "raw", "brutal", "unconventional"], "brutalist"),
        (["tech", "infrastructure", "developer", "devops", "platform", "saas", "api", "data"], "startup_clean"),
    ]

    best_archetype: str | None = None
    best_score = 0
    for signals, archetype in BRIEF_SIGNALS:
        score = sum(1 for s in signals if s in brief_lower)
        if score > best_score:
            best_score = score
            best_archetype = archetype

    if best_archetype:
        # Find direction matching that archetype
        for d in directions:
            if getattr(d, "style_archetype", None) == best_archetype:
                return d

    # Fallback: direction_1 (highest confidence)
    return directions[0]


def _ctx(project_name: str, brief_text: str, dna, preset: dict | None) -> dict:
    """Extract a rendering context dict from pipeline outputs."""
    cs = (preset or {}).get("color_system", {})
    primary   = cs.get("primary",   {}).get("base", "#2563eb")
    secondary = cs.get("secondary", {}).get("base", "#7c3aed")
    h_font    = (preset or {}).get("font_family_headings", "Inter")
    b_font    = (preset or {}).get("font_family_body",     "Inter")
    gf_url    = (preset or {}).get("font_google_url", "")

    industry  = (getattr(dna, "industry",        None) or "").strip()  if dna else ""
    tone      = (getattr(dna, "tone",            None) or "").strip()  if dna else ""
    audience  = (getattr(dna, "target_audience", None) or "").strip()  if dna else ""
    values    = getattr(dna, "brand_values", []) or []
    keywords  = getattr(dna, "keywords",     []) or []

    return dict(
        name=project_name,
        slug=project_name.lower().replace(" ", "_"),
        brief_text=brief_text,
        industry=industry,
        tone=tone,
        audience=audience,
        values=values,
        keywords=keywords,
        primary=primary,
        secondary=secondary,
        h_font=h_font,
        b_font=b_font,
        gf_url=gf_url,
    )


# =============================================================================
# GENERATIVE SECTION ENGINE v3
# Chaque section = layout × copy × visual traitement, tous tirés de pools.
# Zéro template fixe. Des milliers de combinaisons réelles.
# =============================================================================


# ─────────────────────────────────────────────────────────────────────────────
# COPY ENGINE — pools par attitude, construction variée
# ─────────────────────────────────────────────────────────────────────────────

def _cp(kind, rc, rng, idx=0):
    """Generate copy from pools. kind = label/body/h_sec/quote/stat_n/stat_l/manifesto_line"""
    att  = rc["ad"]["attitude"]
    mood = rc["ad"]["mood"]
    kw   = rc["kw"]   or ["vision","qualité","impact"]
    vals = rc["vals"] or ["authenticité","excellence","engagement"]
    name = rc["name"]
    aud  = rc["audience"] or f"les passionnés de {kw[0].lower()}"

    def kw_(i, cap=True):
        w = kw[i % len(kw)]
        return w.capitalize() if cap else w.lower()
    def v_(i, cap=True):
        w = vals[i % len(vals)]
        return w.capitalize() if cap else w.lower()

    if kind == "label":
        pools = {
            "brutalist":    ["MANIFESTE","STRUCTURE","PRINCIPE","MÉTHODE","FONDEMENT","MAINTENANT","SANS FILTRE","VÉRITÉ"],
            "editorial":    ["PERSPECTIVE","VALEURS","APPROCHE","ESSENCE","POINT DE VUE","ANCRAGE","RÉFLEXION","LIGNE DIRECTRICE"],
            "experimental": ["SYSTÈME","PROTOCOLE","ARCHITECTURE","SIGNAL","VECTEUR","MATRICE","LOGIQUE","OPÉRATION"],
            "playful":      ["NOTRE UNIVERS","CE QU'ON AIME","NOTRE ADN","POURQUOI","CE QUI NOUS ANIME","LA VIBE","NOTRE SECRET"],
            "product":      ["FONCTIONNALITÉS","AVANTAGES","MÉTHODE","RÉSULTATS","NOTRE APPROCHE","LA DIFFÉRENCE","EN PRATIQUE"],
        }
        return rng.choice(pools.get(att, pools["product"]))

    elif kind == "body":
        pools = {
            "brutalist": [
                f"{v_(idx)}. Pas de compromis.",
                f"Uniquement {v_(idx, False)}.",
                f"{v_(idx)}. C'est tout.",
                f"La {v_(idx, False)} ou rien.",
                f"Ni plus, ni moins : {v_(idx, False)}.",
                f"Chaque ligne de code. Chaque détail. {v_(idx)}.",
                f"On ne transige pas sur {v_(idx, False)}.",
            ],
            "editorial": [
                f"Une question de {v_(idx, False)}.",
                f"{v_(idx)}, toujours.",
                f"Le {v_(idx, False)} comme principe fondateur.",
                f"Sans {v_(idx, False)}, rien ne tient.",
                f"Tout commence par {v_(idx, False)}.",
                f"Ce que {v_(idx, False)} signifie vraiment.",
                f"Un engagement de chaque instant : {v_(idx, False)}.",
                f"Parce que {v_(idx, False)} n'est pas négociable.",
            ],
            "experimental": [
                f"{v_(idx)} × {v_(idx+1)}.",
                f"→ {v_(idx, False)}",
                f"Système fondé sur {v_(idx, False)}.",
                f"{v_(idx)} [priorité absolue]",
                f"Variable : {v_(idx, False)}. Constante : {v_(idx+1, False)}.",
                f"input({v_(idx, False)}) → output({v_(idx+1, False)})",
                f"/{v_(idx, False)}/",
            ],
            "playful": [
                f"Parce que {v_(idx, False)}, c'est la vie !",
                f"On est fous de {v_(idx, False)}.",
                f"100% {v_(idx, False)}, toujours.",
                f"{v_(idx)} ? Oui, à fond.",
                f"Sans {v_(idx, False)}, ça ne vaut rien.",
                f"La {v_(idx, False)} ça se vit, ça ne se raconte pas.",
                f"Chaque jour, {v_(idx, False)} et {v_(idx+1, False)}.",
            ],
            "product": [
                f"Construit autour de {v_(idx, False)}.",
                f"{v_(idx)} à chaque étape.",
                f"Votre {v_(idx, False)}, notre priorité.",
                f"De la {v_(idx, False)} mesurable.",
                f"{v_(idx)} garanti, {v_(idx+1, False)} assuré.",
                f"Conçu pour {v_(idx, False)} sans effort.",
                f"{v_(idx)} intégré, pas ajouté.",
            ],
        }
        return rng.choice(pools.get(att, pools["product"]))

    elif kind == "h_sec":
        pools = {
            "brutalist":    [f"{kw_(idx).upper()}\n{kw_(idx+1).upper()}", f"{v_(idx).upper()}", f"RIEN QUE\n{kw_(idx).upper()}", f"{kw_(idx).upper()}—"],
            "editorial":    [f"{kw_(idx)},\n{kw_(idx+1)}.", f"De {kw_(idx, False)}\nà {kw_(idx+1, False)}.", f"{v_(idx)} —\n{kw_(idx)}.", f"Sur {kw_(idx, False)}."],
            "experimental": [f"{kw_(idx)}_{kw_(idx+1)}", f"/{kw_(idx)}/\n{v_(idx)}", f"[{kw_(idx)}]", f"{kw_(idx)} :: {v_(idx)}"],
            "playful":      [f"{kw_(idx)} + {kw_(idx+1)}", f"{v_(idx)} ✕ {kw_(idx)}!", f"{kw_(idx)}, {kw_(idx+1)}, {v_(idx)}.", f"{kw_(idx)}~"],
            "product":      [f"{kw_(idx)} et {kw_(idx+1)}", f"La puissance de {kw_(idx, False)}", f"{v_(idx)} et {v_(idx+1)}", f"Tout pour {kw_(idx, False)}"],
        }
        return rng.choice(pools.get(att, pools["product"]))

    elif kind == "quote":
        pool = [
            f"« {v_(0)} n'est pas une option. C'est le fondement. »",
            f"« Chaque décision doit refléter {v_(0, False)} et {v_(1, False)}. »",
            f"« Pour {aud}, {v_(0, False)} change tout. »",
            f"« {name} existe parce que {v_(0, False)} existe. »",
            f"« Nous ne faisons pas de compromis sur {v_(0, False)}. »",
            f"« {v_(0)}, {v_(1)} : ce sont nos seules règles. »",
            f"« Sans {v_(0, False)}, ce projet n'aurait aucun sens. »",
            f"« {kw_(0)} et {kw_(1)} — voilà ce qui nous définit. »",
            f"« La {v_(0, False)} est une discipline, pas une promesse. »",
            f"« {aud.capitalize()} méritent mieux. C'est pourquoi {name} existe. »",
        ]
        return rng.choice(pool)

    elif kind == "stat_n":
        pool = [
            rng.choice(["100%","94%","3×","12×","∞","01","47","2026"]),
            rng.choice(["0 compromis","1 règle","3 principes","24h","48h","7j/7"]),
            rng.choice(["+240%","+80%","×3","×10","—","///",":::"]),
        ]
        return pool[idx % len(pool)]

    elif kind == "stat_l":
        pools = {
            "brutalist":    ["IMPACT","SANS FILTRE","RÉSULTAT BRUT","OUTPUT","SIGNAL"],
            "editorial":    ["de cohérence","depuis l'origine","notre engagement","l'essentiel","en chiffres"],
            "experimental": ["output/year","signal ratio","data points","variables","iterations"],
            "playful":      ["sourires","jours heureux","clients ravis","% de joie","moments"],
            "product":      ["utilisateurs actifs","temps économisé","satisfaction","ROI","uptime"],
        }
        return rng.choice(pools.get(att, pools["product"]))

    elif kind == "manifesto_line":
        pool = {
            "brutalist": [
                f"Nous refusons {v_(idx, False)}.",
                f"{v_(idx)}. Toujours. Partout.",
                f"Aucun compromis sur {v_(idx, False)}.",
                f"La {v_(idx, False)} est notre seule loi.",
                f"{v_(idx).upper()} — sans discussion.",
            ],
            "editorial": [
                f"Nous croyons en {v_(idx, False)}.",
                f"La {v_(idx, False)} guide chaque décision.",
                f"{v_(idx)} n'est pas une valeur — c'est une pratique.",
                f"Nous ne faisons pas de compromis sur {v_(idx, False)}.",
                f"Chaque choix reflète {v_(idx, False)}.",
            ],
            "experimental": [
                f"Protocol({v_(idx, False)}) → required",
                f"if not {v_(idx, False)}: abort()",
                f"{v_(idx)} ← input invariant",
                f"assert {v_(idx, False)} is True",
                f"∀ decision: {v_(idx, False)} ∈ constraints",
            ],
            "playful": [
                f"On est là pour {v_(idx, False)}, et rien d'autre !",
                f"{v_(idx)} ? On dit toujours oui.",
                f"La {v_(idx, False)} c'est notre super-pouvoir.",
                f"Sans {v_(idx, False)}, on ne fait pas.",
                f"{v_(idx)} × 100 = {name}",
            ],
            "product": [
                f"Construire avec {v_(idx, False)} comme fondation.",
                f"Mesurer {v_(idx, False)} à chaque étape.",
                f"La {v_(idx, False)} est livrable, pas abstraite.",
                f"Garantir {v_(idx, False)} à chaque release.",
                f"{v_(idx)} intégré dès la conception.",
            ],
        }
        return rng.choice(pool.get(att, pool["product"]))

    return f"{v_(idx)}"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION VISUAL TREATMENT — appliqué par section, pas globalement
# ─────────────────────────────────────────────────────────────────────────────

def _sec_vt(rc, rng, force=None):
    """Return (section_bg_css, accent_strip_html, section_fg) for a section."""
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    bg, bg2, bdr = rc["bg"], rc["bg2"], rc["bdr"]
    fg = rc["fg"]
    att = rc["ad"]["attitude"]

    opts = force or rng.choice({
        "brutalist":    ["accent_bg","stripe_top","alt_bg","stark_border","accent_bg"],
        "editorial":    ["alt_bg","hairline","none","alt_bg","hairline"],
        "experimental": ["accent_bg","full_color","stripe_top","grid_bg","alt_bg"],
        "playful":      ["full_color","alt_bg","accent_bg","full_color"],
        "product":      ["none","alt_bg","hairline","stripe_top","none"],
    }.get(att, ["none","alt_bg"]))

    if opts == "accent_bg":
        return f"background:{p}12;border-top:1px solid {p}33", "", fg
    elif opts == "full_color":
        txt = rc["inv"]
        return f"background:{p}", f'<div style="height:3px;background:{s}"></div>', txt
    elif opts == "alt_bg":
        return f"background:{bg2}", "", fg
    elif opts == "stripe_top":
        return f"background:{bg}", f'<div style="height:3px;background:{p}"></div>', fg
    elif opts == "stark_border":
        return f"background:{bg};border-top:4px solid {fg}", "", fg
    elif opts == "hairline":
        return f"background:{bg};border-top:1px solid {bdr}", "", fg
    elif opts == "grid_bg":
        return (f"background-color:{bg};"
                f"background-image:repeating-linear-gradient(90deg,{p}0d 0,{p}0d 1px,transparent 1px,transparent 48px),"
                f"repeating-linear-gradient(0deg,{p}0d 0,{p}0d 1px,transparent 1px,transparent 48px)"), "", fg
    else:
        return f"background:{bg}", "", fg


# ─────────────────────────────────────────────────────────────────────────────
# GENERATIVE SECTION BUILDERS — 4 layouts chacun, copy from pools
# ─────────────────────────────────────────────────────────────────────────────

def _sec_features_grid(rc):
    rng  = rc["_rng"]
    kw   = rc["kw"]   or ["qualité","précision","innovation","impact","clarté","vision"]
    vals = rc["vals"] or ["excellence","engagement","durabilité"]
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    att  = rc["ad"]["attitude"]
    bg_css, strip, sfg = _sec_vt(rc, rng)
    lbl  = _cp("label", rc, rng)
    n    = rng.choice([4,6])  # vary item count

    ICONS_POOLS = {
        "brutalist":    ["█","▌","▊","◼","▪","◾"],
        "editorial":    ["—","·","◦","▸","→","›"],
        "experimental": ["◈","◉","⊕","⊗","◎","⊞"],
        "playful":      ["✦","✧","❋","✿","◉","★"],
        "product":      ["✓","⊕","→","◈","▹","◦"],
    }
    icons = ICONS_POOLS.get(att, ICONS_POOLS["product"])

    variant = rng.randint(0, 3)

    if variant == 0:
        # 3-col grid with icon + title + body
        cols = rng.choice(["1fr 1fr 1fr", "1fr 1fr"])
        items = [
            (rng.choice(icons), kw[i%len(kw)].capitalize(), _cp("body", rc, rng, i))
            for i in range(n)
        ]
        cards_html = "".join(
            f'<div style="padding:28px 0;border-top:1px solid {rc["bdr"]}">'
            f'<div style="font-size:1.2rem;color:{rng.choice([p,s,acc])};margin-bottom:12px">{icon}</div>'
            f'<h3 style="{rc["h3_css"]};margin-bottom:8px">{t}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2};line-height:1.7">{d}</p>'
            f'</div>'
            for icon,t,d in items
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:40px">{rc["section_label"](lbl)}</div>'
            f'<div style="display:grid;grid-template-columns:{cols};gap:0 40px">{cards_html}</div>'
            f'</div></section>'
        )

    elif variant == 1:
        # Editorial numbered list — horizontal
        items = [(i+1, kw[i%len(kw)].capitalize(), _cp("body", rc, rng, i)) for i in range(rng.choice([3,4]))]
        rows_html = "".join(
            f'<div style="display:flex;gap:32px;align-items:baseline;padding:24px 0;border-bottom:1px solid {rc["bdr"]}">'
            f'<span style="{rc["label_css"]};color:{p};min-width:32px">{n:02d}</span>'
            f'<h3 style="{rc["h3_css"]};flex:1">{t}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2};max-width:300px;text-align:right;line-height:1.7">{d}</p>'
            f'</div>'
            for n,t,d in items
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:32px">{rc["section_label"](lbl)}</div>'
            f'{rows_html}</div></section>'
        )

    elif variant == 2:
        # Two-column alternating: number large | content
        items = [(i+1, kw[i%len(kw)].capitalize(), _cp("body", rc, rng, i), vals[i%len(vals)].upper()) for i in range(rng.choice([3,4]))]
        rows_html = "".join(
            f'<div style="display:grid;grid-template-columns:120px 1fr;gap:24px;padding:32px 0;border-bottom:1px solid {rc["bdr"]}">'
            f'<div style="font-family:\'{rc["hf"]}\',serif;font-size:4rem;font-weight:900;color:{p}22;line-height:1">{n:02d}</div>'
            f'<div><h3 style="{rc["h3_css"]};margin-bottom:8px">{t}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2};line-height:1.7">{d}</p></div>'
            f'</div>'
            for n,t,d,_ in items
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">{rows_html}</div></section>'
        )

    else:
        # Scattered cards with color accents
        border_colors = [p, s, acc, p, s, acc]
        items = [(kw[i%len(kw)].capitalize(), _cp("body", rc, rng, i), border_colors[i%6]) for i in range(n)]
        cards_html = "".join(
            f'<div style="padding:24px;border-left:3px solid {col};background:{col}08">'
            f'<h3 style="{rc["h3_css"]};margin-bottom:8px">{t}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2};line-height:1.7">{d}</p>'
            f'</div>'
            for t,d,col in items
        )
        cols = f"repeat({rng.choice([2,3])},1fr)"
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:40px">{rc["section_label"](lbl)}</div>'
            f'<div style="display:grid;grid-template-columns:{cols};gap:16px">{cards_html}</div>'
            f'</div></section>'
        )


def _sec_values_list(rc):
    rng  = rc["_rng"]
    vals = rc["vals"] or ["authenticité","engagement","excellence","rigueur"]
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    bg_css, strip, sfg = _sec_vt(rc, rng)
    lbl  = _cp("label", rc, rng)
    n_vals = min(len(vals), rng.choice([3,4]))

    _DESCRIPTORS_POOLS = {
        "brutalist":    ["Notre socle.","Jamais négociable.","Sans exception.","La règle.","Immuable.","Absolu."],
        "editorial":    ["Notre fondement.","Un engagement de toujours.","Ce qui nous définit.","L'essentiel.","Notre ligne.","Indiscutable."],
        "experimental": ["Input requis.","Variable critique.","Constante système.","Paramètre invariant.","Dépendance core.","Root value."],
        "playful":      ["On adore ça !","Notre super-pouvoir.","100% nous.","Notre marque de fab.","Toujours et encore.","La base !"],
        "product":      ["Mesurable.","Livrable.","Garanti.","Intégré.","Documenté.","Au cœur du produit."],
    }
    att = rc["ad"]["attitude"]
    desc_pool = _DESCRIPTORS_POOLS.get(att, _DESCRIPTORS_POOLS["product"])

    variant = rng.randint(0, 3)

    if variant == 0:
        # Editorial list: number | value LARGE | descriptor
        rows = "".join(
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;padding:28px 0;border-bottom:1px solid {rc["bdr"]}">'
            f'<span style="{rc["label_css"]}">{i+1:02d}</span>'
            f'<h3 style="{rc["h2_css"]};font-size:clamp(1.4rem,3vw,2rem);flex:1;text-align:center">{vals[i].capitalize()}</h3>'
            f'<span style="{rc["body_css"]};font-size:11px;color:{fg2};max-width:180px;text-align:right">{rng.choice(desc_pool)}</span>'
            f'</div>'
            for i in range(n_vals)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:32px">{rc["section_label"](lbl)}</div>{rows}'
            f'</div></section>'
        )

    elif variant == 1:
        # Colored cards grid
        colors = [p, s, acc, p]
        cards = "".join(
            f'<div style="background:{colors[i%4]};padding:36px 28px;position:relative;overflow:hidden">'
            f'<div style="font-family:\'{rc["hf"]}\';font-size:4rem;font-weight:900;color:{rc["inv"]}11;position:absolute;top:8px;right:16px;line-height:1">{i+1}</div>'
            f'<h3 style="font-family:\'{rc["hf"]}\';font-size:1.4rem;font-weight:700;color:{rc["inv"]};margin-bottom:12px">{vals[i].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:11px;color:{rc["inv"]}bb;line-height:1.6">{rng.choice(desc_pool)}</p>'
            f'</div>'
            for i in range(n_vals)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:grid;grid-template-columns:repeat({n_vals},1fr);gap:3px">{cards}</div>'
            f'</div></section>'
        )

    elif variant == 2:
        # Oversized value words with left bar
        items = "".join(
            f'<div style="display:flex;gap:24px;align-items:center;padding:20px 0;border-bottom:1px solid {rc["bdr"]}33">'
            f'<div style="width:3px;height:40px;background:{rng.choice([p,s,acc])};flex-shrink:0"></div>'
            f'<div style="font-family:\'{rc["hf"]}\',serif;font-size:clamp(2rem,5vw,3.5rem);font-weight:700;color:{sfg};letter-spacing:-.03em;line-height:1">{vals[i].capitalize()}</div>'
            f'<span style="{rc["body_css"]};font-size:10px;color:{fg2};margin-left:auto;text-align:right;max-width:140px">{rng.choice(desc_pool)}</span>'
            f'</div>'
            for i in range(n_vals)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">{items}</div></section>'
        )

    else:
        # Two-column: list left, big statement right
        list_html = "".join(
            f'<div style="padding:16px 0;border-bottom:1px solid {rc["bdr"]}">'
            f'<span style="{rc["label_css"]};color:{rng.choice([p,s,acc])}">{vals[i].capitalize()}</span>'
            f'</div>'
            for i in range(n_vals)
        )
        stmt = _cp("h_sec", rc, rng, 0)
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center">'
            f'<div>{rc["section_label"](lbl)}<div style="margin-top:24px">{list_html}</div></div>'
            f'<div style="{rc["h2_css"]};line-height:1.1;white-space:pre-line">{stmt}</div>'
            f'</div></div></section>'
        )


def _sec_manifesto(rc):
    rng  = rc["_rng"]
    vals = rc["vals"] or ["authenticité","rigueur","vision","engagement"]
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    bg_css, strip, sfg = _sec_vt(rc, rng)
    att  = rc["ad"]["attitude"]
    n_lines = rng.choice([3,4,5])
    lines = [_cp("manifesto_line", rc, rng, i) for i in range(n_lines)]

    variant = rng.randint(0, 3)

    if variant == 0:
        # Numbered manifesto with dividers
        rows = "".join(
            f'<div style="padding:24px 0;border-bottom:1px solid {rc["bdr"]};display:flex;gap:36px;align-items:baseline">'
            f'<span style="{rc["label_css"]}">{i+1:02d}.</span>'
            f'<p style="{rc["body_css"]};font-size:1.05rem;color:{sfg};font-style:italic;line-height:1.8">{line}</p>'
            f'</div>'
            for i,line in enumerate(lines)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{rc["width_px"]};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:32px">{rc["section_label"]("MANIFESTE")}</div>{rows}'
            f'</div></section>'
        )

    elif variant == 1:
        # Oversized stream of text blocks
        blocks = "".join(
            f'<p style="font-family:\'{rc["hf"]}\';font-size:clamp(1.4rem,3.5vw,2.4rem);'
            f'font-weight:{rng.choice(["300","700"])};color:{rng.choice([sfg,p,s])};'
            f'line-height:1.2;margin-bottom:{rng.choice(["16px","32px","8px"])};'
            f'opacity:{rng.choice([1,0.6,0.4,1,0.8])}">{line}</p>'
            for line in lines
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">{blocks}</div></section>'
        )

    elif variant == 2:
        # Two-column: title left | lines right stacked
        lbl = _cp("h_sec", rc, rng, 0)
        lines_html = "".join(
            f'<p style="{rc["body_css"]};font-size:14px;color:{sfg};padding:12px 0;'
            f'border-bottom:1px solid {rc["bdr"]};line-height:1.6">{line}</p>'
            for line in lines
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:start">'
            f'<div style="{rc["h2_css"]};line-height:1.1;white-space:pre-line;position:sticky;top:80px">{lbl}</div>'
            f'<div>{lines_html}</div>'
            f'</div></div></section>'
        )

    else:
        # Full-width typographic wall
        bg_override = f"background:{p}" if att=="brutalist" else bg_css
        txt_color   = rc["inv"] if att=="brutalist" else sfg
        wall = " ".join(
            f'<span style="font-family:\'{rc["hf"]}\';font-size:clamp(1.2rem,3vw,2rem);'
            f'font-weight:{rng.choice(["900","300","700"])};'
            f'color:{rng.choice([txt_color,rc["s"],rc["acc"]])};'
            f'opacity:{rng.choice([1,0.5,0.8,0.3,1])};margin:0 12px">{line}</span>'
            for line in lines
        )
        return (
            f'<section style="padding:{sp} 0;{bg_override}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:32px 48px;line-height:1.8">{wall}</div></section>'
        )


def _sec_stats(rc):
    rng  = rc["_rng"]
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    bg_css, strip, sfg = _sec_vt(rc, rng)
    n_stats = rng.choice([3,4])
    stats = [(_cp("stat_n", rc, rng, i), _cp("stat_l", rc, rng, i)) for i in range(n_stats)]

    variant = rng.randint(0, 3)

    if variant == 0:
        # Horizontal grid
        items = "".join(
            f'<div style="text-align:center;padding:0 24px;{("border-left:1px solid "+rc["bdr"]) if i>0 else ""}">'
            f'<div style="font-family:\'{rc["hf"]}\',serif;font-size:clamp(3rem,7vw,5rem);font-weight:900;color:{rng.choice([p,s,acc])};line-height:1;letter-spacing:-.04em">{n}</div>'
            f'<div style="{rc["label_css"]};font-size:8px;margin-top:8px;color:{fg2}">{l}</div>'
            f'</div>'
            for i,(n,l) in enumerate(stats)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:flex;justify-content:space-around;align-items:center">{items}</div>'
            f'</div></section>'
        )

    elif variant == 1:
        # Stacked with left label
        items = "".join(
            f'<div style="display:flex;align-items:baseline;gap:32px;padding:24px 0;border-bottom:1px solid {rc["bdr"]}">'
            f'<div style="{rc["label_css"]};min-width:160px;color:{fg2}">{l}</div>'
            f'<div style="font-family:\'{rc["hf"]}\';font-size:clamp(2rem,5vw,4rem);font-weight:900;color:{rng.choice([p,s,acc])};letter-spacing:-.04em">{n}</div>'
            f'</div>'
            for n,l in stats
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">{items}</div></section>'
        )

    elif variant == 2:
        # Colored blocks
        colors = [p, s, acc, p]
        items = "".join(
            f'<div style="background:{colors[i%4]};padding:40px 32px">'
            f'<div style="font-family:\'{rc["hf"]}\';font-size:clamp(2.5rem,6vw,4.5rem);font-weight:900;color:{rc["inv"]};line-height:1;letter-spacing:-.04em">{n}</div>'
            f'<div style="{rc["body_css"]};font-size:10px;color:{rc["inv"]}bb;margin-top:12px;text-transform:uppercase;letter-spacing:.15em">{l}</div>'
            f'</div>'
            for i,(n,l) in enumerate(stats)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:grid;grid-template-columns:repeat({n_stats},1fr);gap:4px">{items}</div>'
            f'</div></section>'
        )

    else:
        # Giant single stat + rest in strip
        main_n, main_l = stats[0]
        rest = "".join(
            f'<div style="text-align:center">'
            f'<div style="font-family:\'{rc["hf"]}\';font-size:2rem;font-weight:900;color:{p}">{n}</div>'
            f'<div style="{rc["label_css"]};font-size:8px;color:{fg2};margin-top:4px">{l}</div>'
            f'</div>'
            for n,l in stats[1:]
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="font-family:\'{rc["hf"]}\';font-size:clamp(6rem,16vw,14rem);font-weight:900;color:{p};line-height:.85;letter-spacing:-.06em;margin-bottom:40px">{main_n}</div>'
            f'<div style="{rc["body_css"]};font-size:11px;color:{fg2};text-transform:uppercase;letter-spacing:.2em;margin-bottom:48px">{main_l}</div>'
            f'<div style="display:flex;gap:64px">{rest}</div>'
            f'</div></section>'
        )


def _sec_pull_quote(rc):
    rng  = rc["_rng"]
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    att  = rc["ad"]["attitude"]
    quote = _cp("quote", rc, rng)

    variant = rng.randint(0, 3)

    if variant == 0:
        # Centered large quote
        bg_css, strip, sfg = _sec_vt(rc, rng, "alt_bg")
        return (
            f'<section style="padding:{sp} 48px;{bg_css}">{strip}'
            f'<div style="max-width:720px;margin:0 auto;text-align:center">'
            f'<div style="font-size:4rem;color:{p};line-height:1;margin-bottom:-16px;font-family:\'{rc["hf"]}\'">"</div>'
            f'<p style="font-family:\'{rc["hf"]}\',Georgia,serif;font-size:clamp(1.3rem,3vw,2rem);font-style:italic;font-weight:300;color:{sfg};line-height:1.5;margin-bottom:24px">{quote[2:-2]}</p>'
            f'<div style="{rc["label_css"]};color:{p}">{rc["name"].upper()}</div>'
            f'</div></section>'
        )

    elif variant == 1:
        # Full-color background
        return (
            f'<section style="padding:{sp} 0;background:{p}">'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<p style="font-family:\'{rc["hf"]}\';font-size:clamp(1.8rem,4vw,3rem);font-weight:300;font-style:italic;color:{rc["inv"]};line-height:1.3">{quote}</p>'
            f'</div></section>'
        )

    elif variant == 2:
        # Left-rule quote
        bg_css, strip, sfg = _sec_vt(rc, rng)
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:flex;gap:40px;align-items:stretch">'
            f'<div style="width:4px;background:{rng.choice([p,s,acc])};flex-shrink:0"></div>'
            f'<p style="font-family:\'{rc["hf"]}\';font-size:clamp(1.4rem,3.5vw,2.5rem);font-weight:300;font-style:italic;color:{sfg};line-height:1.4">{quote}</p>'
            f'</div></div></section>'
        )

    else:
        # Split: quote left | visual right
        bg_css, strip, sfg = _sec_vt(rc, rng)
        panel = _css_visual_panel(rc, rc["visual_system"], rng)
        return (
            f'<section style="padding:0;{bg_css}">'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;min-height:320px">'
            f'<div style="padding:80px 64px;display:flex;align-items:center">'
            f'<p style="font-family:\'{rc["hf"]}\';font-size:clamp(1.3rem,3vw,2rem);font-weight:300;font-style:italic;color:{sfg};line-height:1.5">{quote}</p>'
            f'</div>'
            f'<div style="position:relative;overflow:hidden">{panel}</div>'
            f'</div></section>'
        )


def _sec_process(rc):
    rng  = rc["_rng"]
    kw   = rc["kw"]   or ["analyse","conception","exécution","livraison"]
    vals = rc["vals"] or ["rigueur","créativité","précision","impact"]
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    bg_css, strip, sfg = _sec_vt(rc, rng)
    lbl  = _cp("label", rc, rng)
    steps = min(len(kw), rng.choice([3,4]))
    step_colors = [p, s, acc, p]

    variant = rng.randint(0, 2)

    if variant == 0:
        # Horizontal steps with connector
        items = "".join(
            f'<div style="flex:1;position:relative">'
            f'<div style="width:40px;height:40px;border-radius:50%;background:{step_colors[i%4]};display:flex;align-items:center;justify-content:center;margin-bottom:20px">'
            f'<span style="{rc["body_css"]};font-size:11px;font-weight:700;color:{rc["inv"]}">{i+1}</span>'
            f'</div>'
            f'<h3 style="{rc["h3_css"]};margin-bottom:8px">{kw[i].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2};line-height:1.6">{_cp("body", rc, rng, i)}</p>'
            + (f'<div style="position:absolute;top:20px;left:40px;right:0;height:1px;background:{step_colors[i%4]}44"></div>' if i<steps-1 else "")
            + f'</div>'
            for i in range(steps)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:48px">{rc["section_label"](lbl)}</div>'
            f'<div style="display:flex;gap:24px">{items}</div>'
            f'</div></section>'
        )

    elif variant == 1:
        # Vertical numbered with large numbers
        items = "".join(
            f'<div style="display:grid;grid-template-columns:80px 1fr;gap:24px;padding:32px 0;border-bottom:1px solid {rc["bdr"]}">'
            f'<div style="font-family:\'{rc["hf"]}\';font-size:3rem;font-weight:900;color:{step_colors[i%4]};line-height:1">{i+1}</div>'
            f'<div><h3 style="{rc["h3_css"]};margin-bottom:8px">{kw[i].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:13px;color:{fg2};line-height:1.7">{_cp("body", rc, rng, i)}</p></div>'
            f'</div>'
            for i in range(steps)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">{items}</div></section>'
        )

    else:
        # Two-col: intro left | steps right
        intro = _cp("h_sec", rc, rng, 0)
        steps_html = "".join(
            f'<div style="padding:16px 0;border-left:2px solid {step_colors[i%4]};padding-left:20px;margin-bottom:12px">'
            f'<span style="{rc["label_css"]};color:{step_colors[i%4]}">{i+1:02d} — {kw[i].capitalize()}</span>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2};margin-top:4px">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(steps)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:start">'
            f'<div style="{rc["h2_css"]};line-height:1.1;white-space:pre-line;position:sticky;top:80px">{intro}</div>'
            f'<div>{steps_html}</div>'
            f'</div></div></section>'
        )


def _sec_features_list(rc):
    rng  = rc["_rng"]
    kw   = rc["kw"]   or ["performance","fiabilité","sécurité","scalabilité","simplicité"]
    vals = rc["vals"] or ["excellence","engagement","durabilité"]
    p, s = rc["p"], rc["s"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    bg_css, strip, sfg = _sec_vt(rc, rng)
    lbl  = _cp("label", rc, rng)
    n    = rng.choice([4,5,6])

    variant = rng.randint(0, 2)

    if variant == 0:
        rows = "".join(
            f'<div style="display:flex;gap:20px;align-items:baseline;padding:20px 0;border-bottom:1px solid {rc["bdr"]}">'
            f'<span style="{rc["label_css"]};color:{rng.choice([p,s])};min-width:28px">{i+1:02d}</span>'
            f'<h3 style="{rc["h3_css"]};flex:1">{kw[i%len(kw)].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2};max-width:320px;text-align:right">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(n)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:32px">{rc["section_label"](lbl)}</div>{rows}'
            f'</div></section>'
        )

    elif variant == 1:
        # Two-column masonry-like
        half = n // 2
        col1 = "".join(
            f'<div style="padding:16px 0;border-bottom:1px solid {rc["bdr"]}">'
            f'<div style="{rc["label_css"]};color:{p};margin-bottom:4px">{kw[i%len(kw)].capitalize()}</div>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2}">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(half)
        )
        col2 = "".join(
            f'<div style="padding:16px 0;border-bottom:1px solid {rc["bdr"]}">'
            f'<div style="{rc["label_css"]};color:{rc["s"]};margin-bottom:4px">{kw[(half+i)%len(kw)].capitalize()}</div>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2}">{_cp("body", rc, rng, half+i)}</p>'
            f'</div>'
            for i in range(n-half)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:32px">{rc["section_label"](lbl)}</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:40px">'
            f'<div>{col1}</div><div style="margin-top:40px">{col2}</div>'
            f'</div></div></section>'
        )

    else:
        # Inline tags cloud + descriptions
        tags = "".join(
            f'<span style="{rc["label_css"]};background:{rng.choice([p,s,rc["acc"]])}22;padding:6px 16px;border-radius:100px;margin:4px;display:inline-block">{kw[i%len(kw)].capitalize()}</span>'
            for i in range(n)
        )
        desc = _cp("body", rc, rng, 0)
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:32px">{rc["section_label"](lbl)}</div>'
            f'<div style="margin-bottom:32px">{tags}</div>'
            f'<p style="{rc["body_css"]};font-size:14px;color:{fg2};max-width:600px;line-height:1.8">{desc}</p>'
            f'</div></section>'
        )


def _sec_values_grid(rc):
    rng  = rc["_rng"]
    vals = rc["vals"] or ["authenticité","excellence","engagement","vision","rigueur","impact"]
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    bg_css, strip, sfg = _sec_vt(rc, rng)
    n    = min(len(vals), rng.choice([3,4,6]))
    cols = f"repeat({rng.choice([2,3])},1fr)"

    variant = rng.randint(0, 2)

    if variant == 0:
        cards = "".join(
            f'<div style="padding:32px;border:1px solid {rc["bdr"]}">'
            f'<div style="width:32px;height:3px;background:{[p,s,acc,p,s][i%5]};margin-bottom:20px"></div>'
            f'<h3 style="{rc["h3_css"]};margin-bottom:10px">{vals[i].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2};line-height:1.6">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(n)
        )
    elif variant == 1:
        cards = "".join(
            f'<div style="padding:28px;border-top:2px solid {[p,s,acc][i%3]}">'
            f'<div style="{rc["label_css"]};color:{[p,s,acc][i%3]};margin-bottom:16px">0{i+1}</div>'
            f'<h3 style="{rc["h3_css"]};font-size:1.3rem;margin-bottom:0">{vals[i].capitalize()}</h3>'
            f'</div>'
            for i in range(n)
        )
    else:
        cards = "".join(
            f'<div style="background:{[p,s,acc][i%3]};padding:32px">'
            f'<h3 style="font-family:\'{rc["hf"]}\';font-size:1.2rem;font-weight:700;color:{rc["inv"]};margin-bottom:8px">{vals[i].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:11px;color:{rc["inv"]}99;line-height:1.6">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(n)
        )

    return (
        f'<section style="padding:{sp} 0;{bg_css}">{strip}'
        f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
        f'<div style="display:grid;grid-template-columns:{cols};gap:{rng.choice(["3px","16px","24px"])}">{cards}</div>'
        f'</div></section>'
    )


def _sec_features_cards(rc):
    rng  = rc["_rng"]
    kw   = rc["kw"]   or ["innovation","qualité","impact","vision"]
    vals = rc["vals"] or ["excellence","engagement"]
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    bg_css, strip, sfg = _sec_vt(rc, rng)
    n    = rng.choice([3,4])
    colors = [p,s,acc,p]

    variant = rng.randint(0, 2)
    if variant == 0:
        rot = [f"rotate({rng.choice([-1.5,-1,-.5,0,.5,1,1.5])}deg)" for _ in range(n)]
        cards = "".join(
            f'<div style="background:{colors[i%4]}18;border-radius:{rc["border_radius"]};padding:28px;transform:{rot[i]};border:1px solid {colors[i%4]}33">'
            f'<div style="{rc["label_css"]};color:{colors[i%4]};margin-bottom:16px">0{i+1}</div>'
            f'<h3 style="{rc["h3_css"]};margin-bottom:8px">{kw[i%len(kw)].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{fg2}">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(n)
        )
    else:
        cards = "".join(
            f'<div style="background:{colors[i%4]};padding:32px">'
            f'<h3 style="font-family:\'{rc["hf"]}\';font-size:1.1rem;font-weight:700;color:{rc["inv"]};margin-bottom:8px">{kw[i%len(kw)].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:11px;color:{rc["inv"]}99;line-height:1.6">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(n)
        )

    return (
        f'<section style="padding:{sp} 0;{bg_css}">{strip}'
        f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
        f'<div style="display:grid;grid-template-columns:repeat({n},1fr);gap:{rng.choice(["4px","16px","24px"])}">{cards}</div>'
        f'</div></section>'
    )


# ── _ds_card compat shim ──────────────────────────────────────────────────────
def _ds_card(ds, i=0):
    p, s, bg2, bdr, r = ds["p"], ds["s"], ds["bg2"], ds["bdr"], ds["radius"]
    col = p if i % 2 == 0 else s
    cs  = ds.get("card_style","minimal")
    if cs == "filled":    return f"background:{col}1a;border-radius:{r};padding:28px"
    if cs == "shadowed":  return f"background:{bg2};border-radius:{r};padding:28px;box-shadow:0 4px 24px rgba(0,0,0,.09)"
    if cs == "bordered":  return f"background:{bg2};border:1.5px solid {col}33;border-radius:{r};padding:28px"
    return f"border-top:2px solid {col};padding:24px 0"


# ─────────────────────────────────────────────────────────────────────────────
# HERO BUILDERS v2 — no defaults, all from rc
# ─────────────────────────────────────────────────────────────────────────────

def _hero_centered_v2(rc, rng):
    p=rc["p"]; inv=rc["inv"]; br=rc["button_radius"]
    bh=rc["button_hierarchy"]; body=rc["body_css"]
    s2 = (f'<button style="background:transparent;color:{rc["fg"]};'
          f'border:1.5px solid {rc["bdr"]};padding:15px 32px;border-radius:{br};'
          f'{body};cursor:pointer">{rc["cta_s"]}</button>') if bh=="dual" and rc["cta_s"] else ""
    return (
        f'<section style="padding:{rc["spacing_v"]} 0;text-align:center;{rc["bg_art"]}">'
        f'<div style="position:relative;z-index:1;max-width:{rc["width_px"]};margin:0 auto;padding:0 48px">'
        f'{rc["industry_badge"]}'
        f'<h1 style="{rc["h1_css"]};margin:0 auto 28px;white-space:pre-line;max-width:800px">{rc["h1"]}</h1>'
        f'<p style="{body};font-size:1rem;color:{rc["fg2"]};max-width:480px;margin:0 auto 44px;line-height:{rc["body_lh"]}">{rc["sub"]}</p>'
        f'<div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap">'
        f'<button style="background:{p};color:{inv};border:none;padding:16px 44px;border-radius:{br};{body};font-weight:700;cursor:pointer">{rc["cta_p"]}</button>'
        f'{s2}'
        f'</div></div></section>'
    )


def _hero_split_v2(rc, rng):
    p=rc["p"]; inv=rc["inv"]; br=rc["button_radius"]
    bh=rc["button_hierarchy"]; body=rc["body_css"]
    panel = _css_visual_panel(rc, rc["visual_system"], rng)
    s2 = (f'<button style="background:transparent;color:{rc["fg"]};'
          f'border:1.5px solid {rc["bdr"]};padding:15px 28px;border-radius:{br};'
          f'{body};cursor:pointer">{rc["cta_s"]}</button>') if bh=="dual" and rc["cta_s"] else ""
    return (
        f'<section style="padding:0;min-height:560px;display:grid;grid-template-columns:55% 45%">'
        f'<div style="padding:100px 60px 80px;{rc["bg_art"]};display:flex;flex-direction:column;justify-content:center">'
        f'{rc["industry_badge"]}'
        f'<h1 style="{rc["h1_css"]};margin:20px 0 28px;white-space:pre-line">{rc["h1"]}</h1>'
        f'<p style="{body};font-size:1rem;color:{rc["fg2"]};max-width:400px;margin-bottom:44px;line-height:{rc["body_lh"]}">{rc["sub"]}</p>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap">'
        f'<button style="background:{p};color:{inv};border:none;padding:16px 36px;border-radius:{br};{body};font-weight:700;cursor:pointer">{rc["cta_p"]}</button>'
        f'{s2}'
        f'</div></div>'
        f'<div style="position:relative;overflow:hidden;min-height:560px">{panel}</div>'
        f'</section>'
    )


def _hero_layered_v2(rc, rng):
    p=rc["p"]; inv=rc["inv"]; br=rc["button_radius"]
    bh=rc["button_hierarchy"]; body=rc["body_css"]
    panel = _css_visual_panel(rc, rc["visual_system"], rng)
    s2 = (f'<button style="background:transparent;color:{rc["fg"]};'
          f'border:1px solid {rc["bdr"]};padding:14px 28px;border-radius:{br};'
          f'{body};cursor:pointer">{rc["cta_s"]}</button>') if bh=="dual" and rc["cta_s"] else ""
    kw  = rc["kw"] or []
    nav_kw = " ".join(
        f'<span style="{rc["label_css"]};font-size:8px;color:{rc["fg2"]}">{k.capitalize()}</span>'
        for k in kw[:5]
    )
    return (
        f'<section style="padding:80px 0 0;{rc["bg_art"]};border-bottom:1px solid {rc["bdr"]}">'
        f'<div style="max-width:{rc["width_px"]};margin:0 auto;padding:0 48px">'
        f'<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:40px;padding-bottom:60px">'
        f'<div style="max-width:640px">'
        f'{rc["industry_badge"]}'
        f'<h1 style="{rc["h1_css"]};margin:20px 0 32px;white-space:pre-line">{rc["h1"]}</h1>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap">'
        f'<button style="background:{p};color:{inv};border:none;padding:14px 36px;border-radius:{br};{body};font-weight:600;cursor:pointer">{rc["cta_p"]}</button>'
        f'{s2}'
        f'</div></div>'
        f'<div style="flex-shrink:0;position:relative;width:260px;height:280px;overflow:hidden;border-radius:{rc["border_radius"]}">{panel}</div>'
        f'</div>'
        f'<div style="display:flex;gap:24px;padding:16px 0;border-top:1px solid {rc["bdr"]}">{nav_kw}</div>'
        f'</div></section>'
    )


def _hero_fullbleed_v2(rc, rng):
    p=rc["p"]; inv=rc["inv"]; br=rc["button_radius"]
    bh=rc["button_hierarchy"]; body=rc["body_css"]
    panel = _css_visual_panel(rc, rc["visual_system"], rng)
    kw = rc["kw"] or ["IMPACT"]
    h1_raw = rc["h1"] or kw[0]
    h2_raw = kw[1].upper() if len(kw)>1 else rc["name"]
    s2 = (f'<button style="background:transparent;color:{rc["fg"]};border:1px solid {rc["bdr"]};'
          f'padding:14px 24px;{rc["label_css"]};font-size:10px;text-transform:uppercase;cursor:pointer">{rc["cta_s"]}</button>'
          ) if bh=="dual" and rc["cta_s"] else ""
    return (
        f'<section style="padding:0;min-height:640px;position:relative;display:flex;flex-direction:column;justify-content:flex-end">'
        f'{panel}'
        f'<div style="position:relative;z-index:1;max-width:{rc["width_px"]};margin:0 auto;padding:0 48px 64px;width:100%">'
        f'<div style="{rc["h1_css"]};font-size:clamp(4.5rem,13vw,11rem);margin-bottom:32px;white-space:pre-line">{h1_raw}</div>'
        f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:24px">'
        f'<p style="{body};font-size:13px;color:{rc["fg2"]};max-width:360px;line-height:1.75">{rc["sub"]}</p>'
        f'<div style="display:flex;gap:12px">'
        f'<button style="background:{p};color:{inv};border:none;padding:14px 32px;border-radius:{br};{body};font-weight:700;cursor:pointer">{rc["cta_p"]}</button>'
        f'{s2}'
        f'</div></div></div></section>'
    )


def _hero_asymmetric_v2(rc, rng):
    p=rc["p"]; inv=rc["inv"]; br=rc["button_radius"]
    bh=rc["button_hierarchy"]; body=rc["body_css"]
    panel = _css_visual_panel(rc, rc["visual_system"], rng)
    col_a = rng.choice(["60%","65%","70%"])
    col_b = f"calc(100% - {col_a})"
    s2 = (f'<button style="background:transparent;color:{rc["fg"]};border:1.5px solid {rc["bdr"]};'
          f'padding:15px 28px;border-radius:{br};{body};cursor:pointer">{rc["cta_s"]}</button>'
          ) if bh=="dual" and rc["cta_s"] else ""
    shift = rng.choice(["40px","60px","80px"])
    return (
        f'<section style="padding:0;min-height:580px;display:grid;grid-template-columns:{col_a} {col_b};align-items:stretch">'
        f'<div style="padding:100px 64px 80px;{rc["bg_art"]};display:flex;flex-direction:column;justify-content:center;position:relative">'
        f'{rc["industry_badge"]}'
        f'<h1 style="{rc["h1_css"]};margin:20px 0 28px;white-space:pre-line;padding-left:{shift}">{rc["h1"]}</h1>'
        f'<p style="{body};font-size:1rem;color:{rc["fg2"]};max-width:420px;margin-bottom:44px;line-height:{rc["body_lh"]};padding-left:{shift}">{rc["sub"]}</p>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap;padding-left:{shift}">'
        f'<button style="background:{p};color:{inv};border:none;padding:16px 36px;border-radius:{br};{body};font-weight:700;cursor:pointer">{rc["cta_p"]}</button>'
        f'{s2}'
        f'</div></div>'
        f'<div style="position:relative;overflow:hidden">{panel}</div>'
        f'</section>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR v2
# ─────────────────────────────────────────────────────────────────────────────

def _lp_dynamic_page(ctx: dict, css: str) -> str:
    import random as _rnd

    seed = ctx.get("render_seed", 42)
    rng  = _rnd.Random(seed)

    # ── Step 1: ART DIRECTION ─────────────────────────────────────────────────
    ad = _build_art_direction(ctx, rng)

    # ── Step 2: PALETTE ───────────────────────────────────────────────────────
    base_hex = ctx.get("primary", "#2563eb")
    pal = _build_palette(ad, base_hex, rng)

    # ── Step 3: TYPOGRAPHY ────────────────────────────────────────────────────
    typo = _build_typography(ad, pal, rng)

    # ── Step 4: RENDERING CONTRACT ────────────────────────────────────────────
    rc = _build_rendering_contract(ad, pal, typo, ctx, rng)

    # ── Step 5: COHERENCE VALIDATION ─────────────────────────────────────────
    assert rc.get("h1"),         "RC error: h1 missing"
    assert rc.get("hero_pattern"), "RC error: hero_pattern missing"
    assert rc.get("p"),          "RC error: primary color missing"
    assert rc.get("hf"),         "RC error: display font missing"
    assert rc.get("sections"),   "RC error: section list empty"

    # ── Step 6: RENDER ────────────────────────────────────────────────────────
    gf   = f'<link rel="stylesheet" href="{typo["gf_url"]}">' if typo.get("gf_url") else ""
    p    = rc["p"]; s = rc["s"]; inv = rc["inv"]
    bg   = rc["bg"]; fg = rc["fg"]; fg2 = rc["fg2"]; bdr = rc["bdr"]
    body = rc["body_css"]; h3c = rc["h3_css"]
    kw   = rc["kw"] or []; name = rc["name"]

    # NAV
    nav_bg = f"rgba(8,8,8,.96)" if rc["mode"]=="dark" else rc["bg"]
    nav_links = " ".join(
        f'<a style="{body};font-size:12px;color:{fg2};cursor:pointer">{k.capitalize()}</a>'
        for k in kw[:3]
    )
    nav = (
        f'<nav style="position:sticky;top:0;z-index:100;height:56px;background:{nav_bg};'
        f'border-bottom:1px solid {bdr};display:flex;align-items:center;backdrop-filter:blur(12px)">'
        f'<div style="max-width:{rc["width_px"]};margin:0 auto;padding:0 48px;width:100%;'
        f'display:flex;justify-content:space-between;align-items:center">'
        f'<span style="{h3c};font-size:1rem;font-weight:700;letter-spacing:-.01em">{name}</span>'
        f'<div style="display:flex;gap:28px;align-items:center">'
        f'{nav_links}'
        f'<button style="background:{p};color:{inv};border:none;padding:8px 20px;'
        f'border-radius:{rc["button_radius"]};{body};font-size:12px;font-weight:700;cursor:pointer">'
        f'{rc["cta_p"].split()[0]}</button>'
        f'</div></div></nav>'
    )

    # HERO
    hero_builders = {
        "centered":   _hero_centered_v2,
        "split":      _hero_split_v2,
        "layered":    _hero_layered_v2,
        "full-bleed": _hero_fullbleed_v2,
        "asymmetric": _hero_asymmetric_v2,
    }
    hero = hero_builders.get(rc["hero_pattern"], _hero_centered_v2)(rc, rng)

    # SECTIONS (reuse existing builders, rc is superset of ds)
    rc["_rng"] = rng
    sec_builders = {
        "features_grid":  _sec_features_grid,
        "features_list":  _sec_features_list,
        "features_cards": _sec_features_cards,
        "values_list":    _sec_values_list,
        "values_grid":    _sec_values_grid,
        "manifesto":      _sec_manifesto,
        "stats":          _sec_stats,
        "pull_quote":     _sec_pull_quote,
        "process":        _sec_process,
    }
    sections_html = "".join(
        sec_builders[sk](rc) for sk in rc["sections"] if sk in sec_builders
    )

    # CTA BAND
    inv_rgba = "255,255,255" if inv=="#fff" else "0,0,0"
    cta_band = (
        f'<section style="padding:{rc["spacing_v"]} 0;background:{p};text-align:center">'
        f'<div style="max-width:{rc["width_px"]};margin:0 auto;padding:0 48px">'
        f'<h2 style="{rc["h2_css"]};color:{inv};font-size:2.2rem;margin-bottom:16px">{name}</h2>'
        f'<p style="{body};font-size:14px;color:rgba({inv_rgba},.72);max-width:400px;'
        f'margin:0 auto 36px;line-height:1.85">{rc["sub"]}</p>'
        f'<button style="background:{inv};color:{p};border:none;padding:18px 52px;'
        f'border-radius:{rc["button_radius"]};{body};font-size:14px;font-weight:700;cursor:pointer">'
        f'{rc["cta_p"]}</button>'
        f'</div></section>'
    )

    footer = (
        f'<footer style="padding:40px 0;background:{rc["bg2"]};border-top:1px solid {bdr}">'
        f'<div style="max-width:{rc["width_px"]};margin:0 auto;padding:0 48px;'
        f'display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">'
        f'<span style="{h3c};font-size:.95rem;font-weight:700">{name}</span>'
        f'<div style="display:flex;gap:24px">'
        + " ".join(f'<a style="{body};font-size:11px;color:{fg2};cursor:pointer">{k.capitalize()}</a>' for k in kw[:4]) +
        f'</div>'
        f'<span style="{body};font-size:11px;color:{fg2}">\u00a9 2026 {name}</span>'
        f'</div></footer>'
    )

    reset = ("*{box-sizing:border-box;margin:0;padding:0}"
             f"body{{background:{bg};color:{fg};-webkit-font-smoothing:antialiased}}"
             "img{max-width:100%}a{text-decoration:none}")

    return (
        f'<!doctype html><html lang="fr"><head>'
        f'<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{name}</title>'
        f'{gf}'
        f'<style>{reset}{css or ""}</style>'
        f'</head><body>'
        f'{nav}{hero}{sections_html}{cta_band}{footer}'
        f'</body></html>'
    )

# ── Public API ────────────────────────────────────────────────────────────────

def generate_landing_page(
    project_name: str,
    brief_text: str,
    dna,
    exploration,
    preset: dict | None,
    css: str | None,
    render_seed: int = 42,
) -> str:
    """
    Design Instantiation Engine — generates a fully unique landing page.
    ArtDirection → Palette → Typography → RenderingContract → HTML.
    Every parameter is explicit. No fallbacks. No generic defaults.
    """
    direction = _select_direction(exploration, brief_text)
    archetype = getattr(direction, "style_archetype", "startup_clean") if direction else "startup_clean"
    tagline   = getattr(direction, "tagline", "") if direction else ""
    composition = getattr(direction, "composition_style", "") if direction else ""

    ctx = _ctx(project_name, brief_text, dna, preset)
    ctx["archetype"]   = archetype
    ctx["tagline"]     = tagline
    ctx["composition"] = composition
    ctx["render_seed"] = render_seed

    return _lp_dynamic_page(ctx, css or "")


# ── Pipeline runner ───────────────────────────────────────────────────────────

def run_pipeline(project_name: str, brief_text: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {project_name}")
    print(f"{'─' * 60}")

    slug    = project_name.lower().replace(" ", "_")
    out_dir = OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline_ok: dict[str, bool | None] = {}

    print("  [1/5] design_dna_resolver …")
    dna = step_dna(brief_text, project_name)
    pipeline_ok["dna"] = dna is not None

    print("  [2/5] color_psychology_engine …")
    rec = step_psychology(dna)
    pipeline_ok["rec"] = rec is not None

    print("  [3/5] palette_generator …")
    palette_output = step_palette(dna, rec)
    pipeline_ok["palette"] = palette_output is not None

    print("  [4/5] design_exploration_engine …")
    exploration = step_explore(dna)
    pipeline_ok["explore"] = exploration is not None

    print("  [5/5] theme_generator …")
    style_dna = step_build_style_dna(dna, palette_output, rec)
    preset, css = step_theme(style_dna)
    pipeline_ok["theme"] = preset is not None

    def _save_json(name: str, data: object) -> None:
        try:
            (out_dir / name).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            print(f"    ⚠️  Could not save {name}: {e}")

    _save_json("style_dna.json", asdict(style_dna) if style_dna else {})
    if palette_output:
        try: _save_json("palette.json", asdict(palette_output.palette_set))
        except Exception: _save_json("palette.json", {"error": "serialization failed"})
    if exploration:
        try: _save_json("creative_directions.json", asdict(exploration))
        except Exception: _save_json("creative_directions.json", {"error": "serialization failed"})
    if preset:
        _save_json("theme_preset.json", preset)
    if css:
        (out_dir / "theme.css").write_text(css, encoding="utf-8")

    import random as _r
    lp_content = generate_landing_page(
        project_name=project_name, brief_text=brief_text,
        dna=dna, exploration=exploration, preset=preset, css=css,
        render_seed=_r.randint(0, 999999),
    )
    lp_path = out_dir / "landing_page.html"
    lp_path.write_text(lp_content, encoding="utf-8")

    ok_count = sum(1 for v in pipeline_ok.values() if v is True)
    print(f"  ✅ {ok_count}/{len(pipeline_ok)} steps OK → {lp_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="EURKAI pipeline test")
    parser.add_argument("--project", metavar="NAME")
    parser.add_argument("--brief",   metavar="TEXT")
    parser.add_argument("--name",    metavar="NAME", default="Custom")
    args = parser.parse_args()

    if _import_errors:
        print("⚠️  Import errors:")
        for err in _import_errors:
            print(f"   • {err}")

    if args.brief:
        run_pipeline(args.name, args.brief)
        return

    projects = TEST_BRIEFS
    if args.project:
        slug = args.project.lower().replace(" ", "").replace("_", "")
        projects = [p for p in TEST_BRIEFS if p[0].lower().replace(" ", "").replace("_", "") == slug]
        if not projects:
            print(f"Unknown project '{args.project}'.")
            sys.exit(1)

    print(f"\n{'═' * 60}\n  EURKAI · Design Instantiation Engine v2\n  {len(projects)} project(s)\n{'═' * 60}")
    for name, brief in projects:
        run_pipeline(name, brief)
    print(f"\n{'═' * 60}\n  Done → {OUTPUT_DIR}/\n{'═' * 60}\n")


if __name__ == "__main__":
    main()



# =============================================================================
# DESIGN INSTANTIATION ENGINE v2
# brief → ArtDirection → Palette → Typography → RenderingContract → Page
# ALL parameters explicit. No fallbacks. No generic defaults.
# =============================================================================

import random as _rnd_mod

# ─────────────────────────────────────────────────────────────────────────────
# COLOR UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def _hex_to_hsl(h):
    h = h.lstrip("#")
    if len(h) != 6:
        return 0.0, 0.5, 0.5
    r,g,b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
    cmax,cmin = max(r,g,b), min(r,g,b)
    l = (cmax+cmin)/2
    if cmax == cmin:
        return 0.0, 0.0, l
    d = cmax - cmin
    s = d/(2-cmax-cmin) if l > 0.5 else d/(cmax+cmin)
    hue = ((g-b)/d % 6) if cmax==r else ((b-r)/d+2 if cmax==g else (r-g)/d+4)
    return hue*60, s, l


def _hsl_to_hex(h, s, l):
    s = max(0.0, min(1.0, s))
    l = max(0.0, min(1.0, l))
    h = h % 360
    c = (1 - abs(2*l-1)) * s
    x = c * (1 - abs((h/60)%2 - 1))
    m = l - c/2
    if h < 60:    r,g,b = c,x,0
    elif h < 120: r,g,b = x,c,0
    elif h < 180: r,g,b = 0,c,x
    elif h < 240: r,g,b = 0,x,c
    elif h < 300: r,g,b = x,0,c
    else:         r,g,b = c,0,x
    return "#{:02x}{:02x}{:02x}".format(int((r+m)*255),int((g+m)*255),int((b+m)*255))


def _text_on(hex_str):
    h = hex_str.lstrip("#")
    r,g,b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
    def lc(c): return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
    return "#fff" if 0.2126*lc(r)+0.7152*lc(g)+0.0722*lc(b) < 0.35 else "#111"


# ─────────────────────────────────────────────────────────────────────────────
# FONT LIBRARY — curated pairs by visual category
# ─────────────────────────────────────────────────────────────────────────────

_FONT_PAIRS = {
    "grotesque": [
        ("Barlow Condensed", "Barlow",
         "Barlow+Condensed:wght@100;300;700;900|Barlow:wght@300;400"),
        ("Space Grotesk", "DM Sans",
         "Space+Grotesk:wght@300;600;700|DM+Sans:ital,wght@0,300;0,400;1,300"),
        ("Syne", "Syne",
         "Syne:wght@400;600;700;800"),
        ("Unbounded", "Outfit",
         "Unbounded:wght@200;400;700|Outfit:wght@300;400"),
        ("Fjalla One", "Barlow",
         "Fjalla+One|Barlow:wght@300;400"),
    ],
    "serif": [
        ("Cormorant Garamond", "Jost",
         "Cormorant+Garamond:ital,wght@0,300;0,600;1,300;1,400|Jost:wght@300;400"),
        ("Playfair Display", "Mulish",
         "Playfair+Display:ital,wght@0,400;0,700;1,400|Mulish:wght@300;400"),
        ("Bodoni Moda", "Raleway",
         "Bodoni+Moda:ital,wght@0,400;0,700;1,400|Raleway:wght@300;400;600"),
        ("EB Garamond", "Karla",
         "EB+Garamond:ital,wght@0,400;0,500;1,400|Karla:wght@300;400"),
        ("Libre Baskerville", "Source Sans 3",
         "Libre+Baskerville:ital,wght@0,400;0,700;1,400|Source+Sans+3:wght@300;400"),
    ],
    "experimental": [
        ("Bebas Neue", "DM Mono",
         "Bebas+Neue|DM+Mono:wght@300;400"),
        ("Anton", "Space Mono",
         "Anton|Space+Mono:wght@400"),
        ("Big Shoulders Display", "Courier Prime",
         "Big+Shoulders+Display:wght@100;400;700;900|Courier+Prime:wght@400"),
        ("Russo One", "IBM Plex Mono",
         "Russo+One|IBM+Plex+Mono:ital,wght@0,300;0,400;1,300"),
        ("Oswald", "Space Grotesk",
         "Oswald:wght@200;400;700|Space+Grotesk:wght@300;400"),
    ],
    "sans": [
        ("DM Sans", "DM Sans",
         "DM+Sans:ital,wght@0,200;0,400;0,700;1,300"),
        ("Outfit", "Outfit",
         "Outfit:wght@200;300;400;600;700"),
        ("Plus Jakarta Sans", "Plus Jakarta Sans",
         "Plus+Jakarta+Sans:wght@200;300;400;600;700"),
        ("Nunito", "Nunito",
         "Nunito:wght@200;400;700;900"),
        ("Manrope", "Manrope",
         "Manrope:wght@200;400;600;700"),
    ],
}

_ARCHETYPE_FONT_CATEGORY = {
    "brutalist":          "experimental",
    "editorial_magazine": "serif",
    "luxury_minimal":     "serif",
    "tech_futurist":      "grotesque",
    "creative_studio":    "grotesque",
    "startup_clean":      "sans",
    "corporate_pro":      "sans",
    "premium_craft":      "serif",
    "bold_challenger":    "experimental",
    "organic_natural":    "serif",
    "playful_brand":      "sans",
    "warm_human":         "sans",
}


# ─────────────────────────────────────────────────────────────────────────────
# ART DIRECTION BUILDER
# ─────────────────────────────────────────────────────────────────────────────

_AD_PROFILES = {
    "brutalist":          dict(mood=["aggressive","tense","cold"],          energy="high",   geometry="sharp",               ornament="none",              attitude="brutalist"),
    "editorial_magazine": dict(mood=["enigmatic","serene","refined"],       energy="low",    geometry=["sharp","mixed"],      ornament=["none","low"],      attitude="editorial"),
    "luxury_minimal":     dict(mood=["serene","enigmatic","precious"],      energy="low",    geometry=["sharp","soft"],       ornament=["none","low"],      attitude="editorial"),
    "tech_futurist":      dict(mood=["cold","tense","energetic"],           energy="high",   geometry="sharp",               ornament=["low","medium"],    attitude="experimental"),
    "creative_studio":    dict(mood=["vibrant","energetic","tense"],        energy="high",   geometry=["sharp","mixed"],      ornament=["medium","high"],   attitude="experimental"),
    "startup_clean":      dict(mood=["energetic","serene","warm"],          energy="medium", geometry=["soft","mixed"],       ornament=["none","low"],      attitude="product"),
    "corporate_pro":      dict(mood=["serene","cold"],                      energy="low",    geometry="sharp",               ornament="none",              attitude="product"),
    "premium_craft":      dict(mood=["warm","serene","enigmatic"],          energy="low",    geometry=["soft","mixed"],       ornament=["low","medium"],    attitude="editorial"),
    "bold_challenger":    dict(mood=["aggressive","vibrant","tense"],       energy="high",   geometry="sharp",               ornament=["none","low"],      attitude="brutalist"),
    "organic_natural":    dict(mood=["warm","serene"],                      energy="low",    geometry="soft",                ornament=["low","medium"],    attitude="editorial"),
    "playful_brand":      dict(mood=["vibrant","warm","energetic"],         energy="high",   geometry="soft",                ornament=["medium","high"],   attitude="playful"),
    "warm_human":         dict(mood=["warm","vibrant","serene"],            energy="medium", geometry=["soft","mixed"],       ornament=["low","medium"],    attitude="playful"),
}


def _build_art_direction(ctx, rng):
    archetype = ctx.get("archetype", "startup_clean")
    brief_txt = (ctx.get("brief_text") or "").lower()
    profile   = _AD_PROFILES.get(archetype, _AD_PROFILES["startup_clean"])

    def pick(v): return rng.choice(v) if isinstance(v, list) else v

    # Brief signal detection
    _dark          = any(x in brief_txt for x in ["underground"," nuit ","transe","neon","techno","electro","brutal","punk","metal"," noir ","aggressif"])
    _craft         = any(x in brief_txt for x in ["artisan","forgé","céramique","terroir","poterie","domaine","vignoble","cuir","bois","argile","forge","couteaux","savoir-faire"])
    _playful       = any(x in brief_txt for x in ["fête","festif","enfant","joyeux","coloré","joueur","celebration","voyage","soleil","fleur","beauté","soin","cosmétique"])
    _editorial_sig = any(x in brief_txt for x in ["editorial","magazine","photographie","mode","photo","culture","revue","contemp"])
    _luxury_sig    = any(x in brief_txt for x in ["luxe","luxury","premium","haut de gamme","prestige","maison","couture","joaillerie","orfèvrerie"])
    _experimental  = any(x in brief_txt for x in ["expérimental","génératif","chaos","disruptif","underground","avant-garde","studio créatif"])

    # Archetype override — when design_dna_resolver defaults to startup_clean
    if not archetype or archetype == "startup_clean":
        if _dark:          archetype = "tech_futurist"
        elif _luxury_sig:  archetype = "luxury_minimal"
        elif _craft:       archetype = "premium_craft"
        elif _editorial_sig: archetype = "editorial_magazine"
        elif _experimental: archetype = "creative_studio"
        elif _playful:     archetype = "playful_brand"
        # re-fetch profile after override
        profile = _AD_PROFILES.get(archetype, _AD_PROFILES["startup_clean"])

    mood_pool = profile["mood"]
    if _dark:      mood_pool = ["aggressive","tense","cold"]
    elif _craft:   mood_pool = ["warm","enigmatic","serene"]
    elif _playful: mood_pool = ["vibrant","warm","energetic"]

    density_for_archetype = {
        "brutalist":"balanced","luxury_minimal":"minimal","editorial_magazine":"minimal",
        "playful_brand":"dense","creative_studio":"dense","tech_futurist":"balanced",
        "startup_clean":"balanced","corporate_pro":"minimal","premium_craft":"balanced",
        "bold_challenger":"dense","organic_natural":"balanced","warm_human":"balanced",
    }

    return dict(
        archetype      = archetype,
        mood           = pick(mood_pool),
        energy         = profile["energy"],
        density        = density_for_archetype.get(archetype, "balanced"),
        geometry       = pick(profile["geometry"]),
        ornament_level = pick(profile["ornament"]),
        attitude       = profile["attitude"],
        _dark          = _dark or archetype in {"brutalist","bold_challenger","tech_futurist"},
        _craft         = _craft or archetype == "premium_craft",
        _playful       = _playful and not (_dark or archetype in {"brutalist","bold_challenger"}),
    )


# ─────────────────────────────────────────────────────────────────────────────
# PALETTE ENGINE — bold derivation from base hue + ArtDirection
# ─────────────────────────────────────────────────────────────────────────────

def _build_palette(ad, base_hex, rng):
    h, sat, lit = _hex_to_hsl(base_hex)

    # Surface system from mode
    if ad["_dark"]:
        mode = "dark"
    elif ad["_craft"]:
        mode = "warm"
    elif ad["archetype"] in {"luxury_minimal","editorial_magazine"} and not ad["_playful"]:
        mode = rng.choice(["pale","dark"])
    elif ad["_playful"]:
        mode = "light"
    else:
        mode = rng.choice(["light","pale"])

    surfaces = {
        "dark":  dict(bg="#080808",bg2="#111111",fg="#ededed",fg2="#555",bdr="#1d1d1d"),
        "warm":  dict(bg="#f6efe4",bg2="#ece0cb",fg="#2c1f0f",fg2="#7a6a55",bdr="#d6c4a0"),
        "pale":  dict(bg="#f9f9f7",bg2="#f1f0ed",fg="#111111",fg2="#777",bdr="#ddddd8"),
        "light": dict(bg="#ffffff",bg2="#f4f4f4",fg="#111111",fg2="#666",bdr="#e2e2e2"),
    }[mode]

    # Primary accent strategy per archetype
    # (sat_mult, sat_add, lit_target, hue_shift_pool)
    _S = {
        "brutalist":          (1.5, 0.35, 0.58, [0, 180, 30, -30]),
        "editorial_magazine": (0.5, 0.05, 0.22, [0, 15]),
        "luxury_minimal":     (0.25, 0.0, 0.18, [0]),
        "tech_futurist":      (1.4, 0.25, 0.62, [0, 200, 30]),
        "creative_studio":    (1.5, 0.3,  0.60, [0, 90, 150, 270]),
        "startup_clean":      (1.2, 0.15, 0.55, [0, 30]),
        "corporate_pro":      (0.9, 0.0,  0.42, [0]),
        "premium_craft":      (0.6, 0.12, 0.38, [0, 20]),
        "bold_challenger":    (1.6, 0.4,  0.58, [0, 180]),
        "organic_natural":    (0.7, 0.1,  0.44, [0, 30, -30]),
        "playful_brand":      (1.3, 0.25, 0.60, [0, 120, 240]),
        "warm_human":         (1.0, 0.2,  0.55, [0, 30]),
    }
    sm, sa, lt, hpool = _S.get(ad["archetype"], (1.0, 0.0, 0.5, [0]))

    p_h = (h + rng.choice(hpool)) % 360
    p_s = min(1.0, sat * sm + sa)
    p   = _hsl_to_hex(p_h, p_s, lt)

    # Secondary — harmonic relationship
    s_shift = rng.choice(
        [120, 150, 180, 210] if ad["archetype"] in {"playful_brand","creative_studio","bold_challenger"}
        else [15, 20, 30]    if ad["archetype"] in {"editorial_magazine","luxury_minimal","premium_craft"}
        else [30, 60, 150]
    )
    s_hex = _hsl_to_hex((p_h+s_shift)%360, p_s*0.72, min(0.78, lt+0.12))

    # Accent — vibrant contrast
    acc = _hsl_to_hex((p_h+90)%360, min(1.0, p_s*1.15), min(0.72, lt*1.2))

    inv = _text_on(p)

    return dict(mode=mode, p=p, s=s_hex, acc=acc, inv=inv, **surfaces)


# ─────────────────────────────────────────────────────────────────────────────
# TYPOGRAPHY ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _build_typography(ad, pal, rng):
    font_cat = _ARCHETYPE_FONT_CATEGORY.get(ad["archetype"], "sans")
    hf, bf, gf_query = rng.choice(_FONT_PAIRS[font_cat])
    gf_url = f"https://fonts.googleapis.com/css2?family={gf_query}&display=swap"

    att = ad["attitude"]
    fg  = pal["fg"]
    p   = pal["p"]

    if att == "brutalist":
        h1_sz="clamp(4rem,11vw,8rem)"; h1_wt="900"; h1_st="normal"; h1_tr="uppercase"
        h1_ls="-.06em"; h1_lh="0.88"; lls=".3em"; lh="1.65"
    elif att == "editorial" and font_cat == "serif":
        h1_sz="clamp(3rem,7vw,5.5rem)"; h1_wt="300"; h1_st="italic"; h1_tr="none"
        h1_ls="-.01em"; h1_lh="1.05"; lls=".22em"; lh="1.9"
    elif att == "editorial":
        h1_sz="clamp(3rem,7vw,5.5rem)"; h1_wt="700"; h1_st="normal"; h1_tr="none"
        h1_ls="-.04em"; h1_lh="1.05"; lls=".2em"; lh="1.8"
    elif att == "experimental":
        tr = rng.choice(["uppercase","none"])
        h1_sz="clamp(3.5rem,10vw,8rem)"; h1_wt="900"; h1_st="normal"; h1_tr=tr
        h1_ls="-.05em"; h1_lh="0.9"; lls=".25em"; lh="1.7"
    elif att == "playful":
        h1_sz="clamp(2.5rem,6vw,4.5rem)"; h1_wt="900"; h1_st="normal"; h1_tr="none"
        h1_ls="-.02em"; h1_lh="1.1"; lls=".1em"; lh="1.75"
    else:  # product
        sz  = "clamp(3rem,7vw,5rem)" if ad["energy"]=="high" else "clamp(2.4rem,5vw,3.8rem)"
        wt  = "700" if ad["energy"]=="high" else "600"
        h1_sz=sz; h1_wt=wt; h1_st="normal"; h1_tr="none"
        h1_ls="-.025em"; h1_lh="1.1"; lls=".18em"; lh="1.75"

    h3_wt = "600" if h1_wt in ("300","400") else "700"
    h3_st = "italic" if h1_st == "italic" else "normal"

    return dict(
        hf=hf, bf=bf, gf_url=gf_url,
        h1_css=(f"font-family:'{hf}',Georgia,serif;font-size:{h1_sz};"
                f"font-weight:{h1_wt};font-style:{h1_st};text-transform:{h1_tr};"
                f"letter-spacing:{h1_ls};line-height:{h1_lh};color:{fg}"),
        h2_css=(f"font-family:'{hf}',Georgia,serif;font-size:clamp(1.8rem,4vw,2.8rem);"
                f"font-weight:{h1_wt};font-style:{h1_st};color:{fg};letter-spacing:{h1_ls}"),
        h3_css=(f"font-family:'{hf}',Georgia,serif;font-size:.95rem;"
                f"font-weight:{h3_wt};font-style:{h3_st};color:{fg}"),
        body_css=f"font-family:'{bf}',system-ui,sans-serif",
        label_css=(f"font-family:'{bf}',system-ui,sans-serif;font-size:9px;"
                   f"letter-spacing:{lls};text-transform:uppercase;color:{p};font-weight:700"),
        body_lh=lh,
    )


# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUND ART ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _build_bg_art(ad, pal, rng):
    p, s, bg = pal["p"], pal["s"], pal["bg"]
    ornament  = ad["ornament_level"]
    att       = ad["attitude"]

    if ornament == "none":
        return f"background:{bg}"

    v = rng.choice({
        "brutalist":    ["hard_grid","noise_heavy","stripe_bold","diagonal_bold"],
        "editorial":    ["radial_soft","hairline_grid","none"],
        "experimental": ["noise_heavy","hard_grid","radial_soft","stripe_bold"],
        "playful":      ["dots_multi","radial_warm","diagonal_soft"],
        "product":      ["radial_soft","dots_mono","hairline_grid","none"],
    }.get(att, ["radial_soft","none"]))

    defs = {
        "hard_grid":    (f"background-color:{bg};"
                         f"background-image:repeating-linear-gradient(0deg,{p}22 0,{p}22 1px,transparent 1px,transparent 40px),"
                         f"repeating-linear-gradient(90deg,{p}22 0,{p}22 1px,transparent 1px,transparent 40px)"),
        "noise_heavy":  (f"background-color:{bg};"
                         f"background-image:linear-gradient(45deg,{p}1a 25%,transparent 25%),"
                         f"linear-gradient(-45deg,{p}15 25%,transparent 25%),"
                         f"linear-gradient(45deg,transparent 75%,{s}11 75%),"
                         f"linear-gradient(-45deg,transparent 75%,{s}0d 75%);"
                         f"background-size:6px 6px;background-position:0 0,0 3px,3px -3px,-3px 0"),
        "stripe_bold":  (f"background-color:{bg};"
                         f"background-image:repeating-linear-gradient(45deg,{p}1e 0,{p}1e 2px,transparent 2px,transparent 24px)"),
        "diagonal_bold":(f"background-color:{bg};"
                         f"background-image:repeating-linear-gradient(135deg,{p}22 0,{p}22 3px,transparent 3px,transparent 28px)"),
        "radial_soft":  f"background:radial-gradient(ellipse at {rng.choice(['70% 30%','20% 60%','80% 80%','50% 20%'])},{p}22 0%,{bg} 60%)",
        "hairline_grid":(f"background-color:{bg};"
                         f"background-image:repeating-linear-gradient(0deg,{p}0d 0,{p}0d 1px,transparent 1px,transparent 64px),"
                         f"repeating-linear-gradient(90deg,{p}0d 0,{p}0d 1px,transparent 1px,transparent 64px)"),
        "dots_mono":    (f"background-image:radial-gradient(circle,{p}33 1.5px,transparent 1.5px);"
                         f"background-size:28px 28px;background-color:{bg}"),
        "dots_multi":   (f"background-image:radial-gradient(circle,{p}44 1.5px,transparent 1.5px),"
                         f"radial-gradient(circle,{s}33 1px,transparent 1px);"
                         f"background-size:36px 36px,20px 20px;background-position:0 0,10px 10px;background-color:{bg}"),
        "radial_warm":  f"background:radial-gradient(ellipse at 60% 40%,{p}28 0%,{s}11 40%,{bg} 70%)",
        "diagonal_soft":(f"background-color:{bg};"
                         f"background-image:repeating-linear-gradient(135deg,{p}11 0,{p}11 1px,transparent 1px,transparent 32px)"),
        "none":         f"background:{bg}",
    }
    return defs.get(v, f"background:{bg}")


# ─────────────────────────────────────────────────────────────────────────────
# CSS VISUAL PANEL — replaces all raster images
# ─────────────────────────────────────────────────────────────────────────────


def _css_visual_panel(pal, vs, rng):
    """
    Generate a CSS visual panel from VisualSystem + Palette.
    EVERY color derived from pal. No external colors. No random decorations.
    Every visual has a role: hierarchy, mood, space structure.
    """
    p, s, acc   = pal["p"], pal["s"], pal["acc"]
    bg, bg2     = pal["bg"], pal["bg2"]

    vtype       = vs["visual_type"]
    vintensity  = vs["visual_intensity"]
    vrole       = vs["visual_role"]

    # Opacity levels tied to intensity — ALL visuals use palette colors at these opacities
    _OP = {"subtle": ("18","33","0d"), "medium": ("55","88","22"), "strong": ("cc","ff","44")}
    op1, op2, op3 = _OP[vintensity]

    if vtype == "gradient":
        v = rng.choice([
            # Linear sweep — strong directional read
            f'<div style="position:absolute;inset:0;background:linear-gradient({rng.choice([120,135,150,45])}deg,{p} 0%,{s} 65%,{acc}{op3} 100%)"></div>',
            # Radial focus — pulls eye to center
            f'<div style="position:absolute;inset:0;background:radial-gradient(ellipse at {rng.choice(["60% 40%","70% 30%","40% 60%"])},{p} 0%,{s}{op2} 50%,{bg} 80%)"></div>',
            # Dual radial — creates depth
            f'<div style="position:absolute;inset:0;background:{bg2}">'
            f'<div style="position:absolute;top:0;right:0;width:80%;height:80%;background:radial-gradient(ellipse at top right,{p}{op2} 0%,transparent 65%)"></div>'
            f'<div style="position:absolute;bottom:0;left:0;width:50%;height:50%;background:radial-gradient(ellipse at bottom left,{s}{op1} 0%,transparent 60%)"></div>'
            f'</div>',
        ])

    elif vtype == "glow":
        # Glow: blurred radial sources — mood and depth
        v = rng.choice([
            f'<div style="position:absolute;inset:0;background:{bg2}">'
            f'<div style="position:absolute;top:15%;left:15%;width:70%;height:70%;background:radial-gradient(ellipse,{p}{op2} 0%,transparent 60%);filter:blur(48px)"></div>'
            f'<div style="position:absolute;top:40%;right:5%;width:45%;height:45%;background:radial-gradient(ellipse,{s}{op1} 0%,transparent 55%);filter:blur(36px)"></div>'
            f'</div>',
            f'<div style="position:absolute;inset:0;background:{bg2}">'
            f'<div style="position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:90%;height:50%;background:radial-gradient(ellipse,{acc}{op2} 0%,{p}{op1} 40%,transparent 70%);filter:blur(56px)"></div>'
            f'</div>',
        ])

    elif vtype == "shapes":
        clip_a = rng.choice(["polygon(0 0,65% 0,100% 100%,0 100%)","polygon(35% 0,100% 0,100% 100%,0 100%)","polygon(0 0,100% 0,100% 65%,0 100%)","polygon(0 35%,100% 0,100% 100%,0 100%)"])
        clip_b = rng.choice(["polygon(20% 0,100% 0,80% 100%,0 100%)","polygon(0 0,80% 0,100% 100%,20% 100%)"])
        rot1   = rng.choice([6,9,12,15])
        rot2   = rng.choice([-4,-7,-10])
        v = rng.choice([
            # Diagonal fill — structural, directional
            f'<div style="position:absolute;inset:0;background:{bg2}">'
            f'<div style="position:absolute;inset:0;background:{p};clip-path:{clip_a}"></div>'
            f'<div style="position:absolute;inset:0;background:{s};opacity:.35;clip-path:{clip_b}"></div>'
            f'</div>',
            # Rotated blocks — tension, rawness
            f'<div style="position:absolute;inset:0;background:{bg2};overflow:hidden">'
            f'<div style="position:absolute;top:-20%;left:5%;width:90%;height:140%;background:{p};transform:rotate({rot1}deg)"></div>'
            f'<div style="position:absolute;top:15%;left:20%;width:60%;height:65%;background:{s};opacity:.38;transform:rotate({rot2}deg)"></div>'
            f'<div style="position:absolute;top:30%;right:5%;width:30%;height:30%;background:{acc};opacity:.25;transform:rotate({rot1//2}deg)"></div>'
            f'</div>',
            # Concentric forms — rhythm, depth
            f'<div style="position:absolute;inset:0;background:{bg2};overflow:hidden">'
            + "".join(
                f'<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);'
                f'width:{(i+1)*18}%;height:{(i+1)*18}%;'
                f'border-radius:{rng.choice([0,12,50])}%;'
                f'border:2px solid {[p,s,acc,p,s][i]};opacity:{max(0.08,0.88-i*0.14)}"></div>'
                for i in range(5)
            ) + '</div>',
        ])

    elif vtype == "grid":
        col_count = rng.choice([5,6,7])
        row_count = rng.choice([4,5,6])
        _GRID_COLORS = [p,s,acc,bg2,bg2,bg2,bg2,bg2]
        v = rng.choice([
            # Mosaic — structural, bold
            f'<div style="position:absolute;inset:0;display:grid;grid-template-columns:repeat({col_count},1fr);grid-template-rows:repeat({row_count},1fr)">'
            + "".join(f'<div style="background:{rng.choice(_GRID_COLORS)};opacity:{rng.choice([1,0.7,0.4,0.85,0.2])}"></div>' for _ in range(col_count*row_count))
            + '</div>',
            # Vertical bars — rhythm, editorial
            f'<div style="position:absolute;inset:0;background:{bg2};overflow:hidden">'
            + "".join(f'<div style="position:absolute;top:0;bottom:0;left:{i*(100//(col_count+1))}%;width:1px;background:{rng.choice([p,s,acc])};opacity:{rng.choice([0.8,0.4,0.6,1.0])}"></div>' for i in range(1,col_count+1))
            + "".join(f'<div style="position:absolute;left:0;right:0;top:{i*(100//(row_count+1))}%;height:1px;background:{rng.choice([p,s])};opacity:{rng.choice([0.25,0.4,0.2])}"></div>' for i in range(1,row_count+1))
            + '</div>',
            # Fine texture grid
            f'<div style="position:absolute;inset:0;background-color:{bg2};'
            f'background-image:repeating-linear-gradient(0deg,{p}{op3} 0,{p}{op3} 1px,transparent 1px,transparent 32px),'
            f'repeating-linear-gradient(90deg,{p}{op3} 0,{p}{op3} 1px,transparent 1px,transparent 32px)"></div>',
        ])

    elif vtype == "noise":
        stripe_w = rng.choice([2,3,5,8])
        gap_w    = stripe_w * rng.choice([3,4,5])
        v = rng.choice([
            # Stripe field — direction, energy
            f'<div style="position:absolute;inset:0;background-color:{bg2};'
            f'background-image:repeating-linear-gradient({rng.choice([45,60,135])}deg,'
            f'{p}{op1} 0,{p}{op1} {stripe_w}px,transparent {stripe_w}px,transparent {gap_w}px,'
            f'{s}{op3} {gap_w}px,{s}{op3} {gap_w+stripe_w}px,transparent {gap_w+stripe_w}px,transparent {gap_w*2}px)"></div>',
            # Dot field — texture, rhythm
            f'<div style="position:absolute;inset:0;background-color:{bg2};'
            f'background-image:radial-gradient(circle,{p}{op2} 1.5px,transparent 1.5px),'
            f'radial-gradient(circle,{s}{op1} 1px,transparent 1px);'
            f'background-size:24px 24px,14px 14px;background-position:0 0,7px 7px"></div>',
            # Noise hash
            f'<div style="position:absolute;inset:0;background-color:{bg2};'
            f'background-image:linear-gradient(45deg,{p}{op1} 25%,transparent 25%),'
            f'linear-gradient(-45deg,{p}{op3} 25%,transparent 25%),'
            f'linear-gradient(45deg,transparent 75%,{s}{op1} 75%),'
            f'linear-gradient(-45deg,transparent 75%,{s}{op3} 75%);'
            f'background-size:8px 8px;background-position:0 0,0 4px,4px -4px,-4px 0"></div>',
        ])

    else:  # composition
        rot_a = rng.choice([6,9,12])
        rot_b = rng.choice([-4,-7,-11])
        v = rng.choice([
            # Barcode (brutalist rhythm)
            f'<div style="position:absolute;inset:0;background:{bg2};overflow:hidden">'
            + "".join(f'<div style="position:absolute;left:{i*6+rng.randint(-1,2)}%;top:0;width:{rng.choice([1,2,3,1,4])}%;height:100%;background:{rng.choice([p,s,acc])};opacity:{rng.choice([1.0,0.6,0.3,0.8,0.5])}"></div>' for i in range(16))
            + '</div>',
            # Layered rectangles — hierarchy, structure
            f'<div style="position:absolute;inset:0;background:{bg2};overflow:hidden">'
            + "".join(
                f'<div style="position:absolute;top:{10+i*20}%;left:{rng.randint(0,10)}%;'
                f'width:{rng.randint(65,95)}%;height:{rng.randint(12,22)}%;'
                f'background:{[p,s,acc,bg2][i%4]};opacity:{rng.choice([1.0,0.75,0.5,0.88])}"></div>'
                for i in range(4)
            ) + '</div>',
            # Stacked angles (asymmetric composition)
            f'<div style="position:absolute;inset:0;background:{bg2};overflow:hidden">'
            f'<div style="position:absolute;top:-30%;left:-10%;width:120%;height:90%;background:{p};transform:rotate({rot_a}deg);transform-origin:left center"></div>'
            f'<div style="position:absolute;top:20%;left:0;width:100%;height:70%;background:{s};opacity:.4;transform:rotate({rot_b}deg);transform-origin:right center"></div>'
            f'</div>',
        ])

    return v


def _build_visual_system(ad, pal, rng):
    """
    Define an explicit VisualSystem: type, role, intensity, integration.
    All parameters derived from ArtDirection. No random choices without justification.
    """
    att     = ad["attitude"]
    mood    = ad["mood"]
    ornament = ad["ornament_level"]
    energy  = ad["energy"]

    # visual_type: what kind of visual element
    type_pools = {
        "brutalist":    ["shapes", "grid", "noise", "shapes"],
        "editorial":    ["grid", "gradient", "composition"],
        "experimental": ["composition", "glow", "shapes", "noise"],
        "playful":      ["shapes", "composition", "glow"],
        "product":      ["gradient", "glow", "grid"],
    }
    # visual_role: what purpose does it serve
    role_pools = {
        "brutalist":    ["structural", "focal"],
        "editorial":    ["background", "structural"],
        "experimental": ["overlapping", "focal", "accent"],
        "playful":      ["accent", "embedded"],
        "product":      ["background", "accent"],
    }
    # visual_intensity: how strong
    intensity_from_mood = {
        "aggressive": "strong", "tense": "strong", "cold": "medium",
        "enigmatic": "medium", "serene": "subtle", "warm": "medium",
        "vibrant": "strong", "energetic": "strong",
        "precious": "subtle", "refined": "subtle",
    }
    # integration_level: how deeply embedded
    integration_pools = {
        "brutalist":    ["overlapping", "background"],
        "editorial":    ["background", "embedded"],
        "experimental": ["overlapping", "embedded"],
        "playful":      ["embedded", "overlapping"],
        "product":      ["background", "embedded"],
    }

    vtype       = rng.choice(type_pools.get(att, ["gradient"]))
    vrole       = rng.choice(role_pools.get(att, ["background"]))
    vintensity  = intensity_from_mood.get(mood, "medium")
    vintegration = rng.choice(integration_pools.get(att, ["background"]))

    # If ornament=none → force minimal
    if ornament == "none":
        vtype, vintensity = "grid", "subtle"

    # High energy overrides intensity floor
    if energy == "high" and vintensity == "subtle":
        vintensity = "medium"

    return dict(
        visual_type   = vtype,
        visual_role   = vrole,
        visual_intensity = vintensity,
        integration_level = vintegration,
    )


def _build_rendering_contract(ad, pal, typo, ctx, rng):
    archetype = ad["archetype"]
    att       = ad["attitude"]
    energy    = ad["energy"]
    density   = ad["density"]
    geometry  = ad["geometry"]
    mood      = ad["mood"]

    name      = ctx["name"]
    kw        = ctx.get("keywords") or []
    vals      = ctx.get("values")   or []
    brief_txt = (ctx.get("brief_text") or "").lower()
    audience  = (ctx.get("audience") or "").strip()
    industry  = (ctx.get("industry") or "").strip()
    tagline   = ctx.get("tagline", "")

    # ── LAYOUT ────────────────────────────────────────────────────────────────
    page_structure = {
        "brutalist":"experimental","editorial":"editorial",
        "experimental":"experimental","playful":"narrative","product":"product",
    }[att]

    hero_options = {
        "brutalist":    ["full-bleed","asymmetric"],
        "editorial":    ["layered","asymmetric"],
        "experimental": ["full-bleed","asymmetric","layered"],
        "playful":      ["centered","layered"],
        "product":      ["split","centered"],
    }
    hero_pattern = rng.choice(hero_options[att])

    section_flow = rng.choice({
        "editorial":    ["alternating","narrative"],
        "brutalist":    ["fragmented","linear"],
        "experimental": ["fragmented","narrative","alternating"],
        "playful":      ["narrative","alternating"],
        "product":      ["linear","alternating"],
    }[att])

    width_px = {"minimal":"760px","balanced":"1060px","dense":"1200px"}[density]
    spacing_v = {"low":"120px","medium":"88px","high":"64px"}[energy]

    # ── COMPONENTS ────────────────────────────────────────────────────────────
    button_family = {
        "sharp":rng.choice(["sharp","block"]),
        "soft":rng.choice(["pill","sharp"]),
        "mixed":rng.choice(["pill","sharp","text"]),
    }[geometry]
    button_radius = {"pill":"100px","sharp":"0px","block":"4px","text":"0px"}[button_family]

    button_hierarchy = (
        "single" if density=="minimal" or att in {"brutalist","experimental"} and rng.random()<0.5
        else "dual"
    )

    card_usage  = {"minimal":"none","balanced":rng.choice(["none","light","medium"]),"dense":rng.choice(["medium","heavy"])}[density]
    card_style  = rng.choice({
        "brutalist":["flat"],"editorial":["flat","outlined"],
        "experimental":["flat","outlined"],"playful":["elevated","outlined"],
        "product":["elevated","outlined","flat"],
    }[att])

    # ── SURFACE ───────────────────────────────────────────────────────────────
    border_radius = {"sharp":"0px","soft":rng.choice(["12px","16px","20px"]),"mixed":rng.choice(["4px","8px","12px"])}[geometry]
    shadow_style  = {"brutalist":"none","editorial":"none","experimental":rng.choice(["none","soft"]),"playful":rng.choice(["soft","strong"]),"product":"soft"}[att]
    divider_css   = {
        "brutalist":f"border-bottom:3px solid {pal['p']}",
        "editorial":f"border-bottom:1px solid {pal['bdr']}",
        "experimental":f"border-bottom:1px solid {pal['p']}44",
        "playful":"",
        "product":f"border-bottom:1px solid {pal['bdr']}",
    }[att]

    # ── ORNAMENT ──────────────────────────────────────────────────────────────
    bg_art = _build_bg_art(ad, pal, rng)
    visual_system = _build_visual_system(ad, pal, rng)

    # ── COPY ──────────────────────────────────────────────────────────────────
    headline_style = {
        "aggressive":"technical","tense":rng.choice(["technical","editorial"]),
        "cold":"editorial","enigmatic":"editorial","serene":"editorial",
        "warm":rng.choice(["emotional","playful"]),"vibrant":"playful",
        "energetic":rng.choice(["technical","playful"]),"precious":"editorial","refined":"editorial",
    }[mood]

    cta_tone = rng.choice({
        "brutalist":["provocative"],"editorial":["minimal","soft"],
        "experimental":["provocative","minimal"],"playful":["soft","direct"],"product":["direct"],
    }[att])

    # Headline
    if tagline:
        h1 = tagline
    elif headline_style == "technical" and kw:
        h1 = kw[0].upper() + ("\n" + kw[1].upper() if len(kw)>1 else "")
    elif headline_style == "editorial" and kw:
        h1 = kw[0].capitalize() + (",\n" + kw[1] if len(kw)>1 else "")
    elif headline_style == "playful" and vals:
        h1 = vals[0].capitalize() + " avant tout."
    elif headline_style == "emotional" and len(vals)>=2:
        h1 = vals[0].capitalize() + " et " + vals[1] + "."
    else:
        h1 = kw[0].capitalize() if kw else name

    v1 = vals[0].lower() if vals else "l'essentiel"
    v2 = vals[1].lower() if len(vals)>1 else "l'intention"
    sub = (f"Pour {audience}. " if audience else "") + f"{v1.capitalize()} et {v2}."

    # CTA
    _CTA = [
        (["événement","festival","workshop"], ("Réserver ma place", "Programme →")),
        (["viticole","vin","domaine","vignoble"], ("Découvrir les cuvées", "Notre terroir →")),
        (["forge","couteaux","lame","acier"], ("Voir les créations", "Le processus →")),
        (["galerie","art contemporain","exposition"], ("Voir les œuvres", "Contact presse →")),
        (["underground","label ","clubbers","djs"], ("Rejoindre l'univers", "Explorer →")),
        (["saas","api","b2b","infrastructure"], ("Commencer gratuitement", "Voir la démo →")),
        (["voyage","travel","aventure"], ("Explorer", "Témoignages →")),
        (["cosmétique","beauté","soin","enfant"], ("Découvrir la gamme", "Notre histoire →")),
        (["céramique","poterie","argile"], ("Parcourir la collection", "L'atelier →")),
        (["magazine","revue","publication"], ("Lire le dernier numéro", "S'abonner →")),
    ]
    cta_p, cta_s = f"Découvrir {name}", "En savoir plus →"
    for signals, ctas in _CTA:
        if any(x in brief_txt for x in signals):
            cta_p, cta_s = ctas
            break

    if cta_tone == "provocative":
        cta_p = cta_p.upper()
        cta_s = ""
    elif cta_tone == "minimal":
        cta_p = "→ " + cta_p
        cta_s = ""

    # Sections pool
    _POOLS = {
        "editorial":    ["manifesto","values_list","features_list","pull_quote"],
        "product":      ["features_grid","values_grid","stats","process"],
        "narrative":    ["manifesto","features_cards","pull_quote","values_list"],
        "experimental": ["manifesto","pull_quote","stats","values_grid","features_list"],
    }
    pool = _POOLS.get(page_structure, _POOLS["product"])
    n    = {"minimal":2,"balanced":3,"dense":4}[density]
    sections = rng.sample(pool, min(n, len(pool)))

    # Industry badge
    industry_badge = (
        f'<div style="display:inline-block;border-radius:100px;padding:4px 14px;'
        f'margin-bottom:20px;background:{pal["p"]}18">'
        f'<span style="{typo["label_css"]}">{industry.upper()}</span></div>'
    ) if industry else ""

    def section_label(text):
        return f'<span style="{typo["label_css"]}">{text}</span>'

    # Build rc — superset of ds (backward compat with section builders)
    rc = dict(
        # context
        ctx=ctx, name=name, kw=kw, vals=vals,
        audience=audience, industry=industry,
        industry_badge=industry_badge, brief_txt=brief_txt,
        section_label=section_label,
        # art direction
        ad=ad,
        # layout
        page_structure=page_structure, hero_pattern=hero_pattern,
        section_flow=section_flow, width_px=width_px, spacing_v=spacing_v,
        # components
        button_family=button_family, button_radius=button_radius,
        button_hierarchy=button_hierarchy,
        card_usage=card_usage, card_style=card_style,
        # surface
        border_radius=border_radius, radius=border_radius,
        shadow_style=shadow_style, divider_css=divider_css,
        divider_style=divider_css,
        # ornament
        bg_art=bg_art,
        # copy
        headline_style=headline_style, cta_tone=cta_tone,
        h1=h1, sub=sub, cta_p=cta_p, cta_s=cta_s,
        sections=sections,
        # palette (flat)
        **pal,
        # typography (flat)
        **typo,
        # compat keys for section builders
        typo_att=att,
        visual_system=visual_system,
    )
    return rc


# ─────────────────────────────────────────────────────────────────────────────
# HERO BUILDERS v2 — no defaults, all from rc
# ─────────────────────────────────────────────────────────────────────────────


