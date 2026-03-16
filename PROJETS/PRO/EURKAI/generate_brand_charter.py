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


def _lp_nav_editorial(ctx: dict) -> str:
    p = ctx["primary"]
    return f"""
<nav style="position:sticky;top:0;z-index:100;background:#fff;border-bottom:1px solid #e0e0e0;padding:0 48px;display:flex;align-items:center;justify-content:space-between;height:56px">
  <span style="font-family:'{ctx['h_font']}',Georgia,serif;font-size:1.1rem;font-weight:400;letter-spacing:.04em;color:#111">{ctx['name'].upper()}</span>
  <div style="display:flex;gap:32px;align-items:center">
    <a style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:#666;text-decoration:none;cursor:pointer">Revue</a>
    <a style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:#666;text-decoration:none;cursor:pointer">Art</a>
    <a style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:#666;text-decoration:none;cursor:pointer">Philosophie</a>
    <a style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:#111;text-decoration:none;border-bottom:1px solid #111;padding-bottom:1px;cursor:pointer">S'abonner</a>
  </div>
</nav>"""


def _lp_nav_playful(ctx: dict) -> str:
    p = ctx["primary"]
    return f"""
<nav style="background:#fff;border-bottom:2px solid {p}20;padding:0 32px;display:flex;align-items:center;justify-content:space-between;height:60px">
  <span style="font-family:'{ctx['h_font']}',sans-serif;font-size:1.2rem;font-weight:800;color:{p}">🕯️ {ctx['name']}</span>
  <div style="display:flex;gap:24px;align-items:center">
    <a style="font-size:13px;color:#555;text-decoration:none;cursor:pointer">Examples</a>
    <a style="font-size:13px;color:#555;text-decoration:none;cursor:pointer">How it works</a>
    <button style="background:{p};color:#fff;border:none;padding:9px 20px;border-radius:100px;font-size:13px;font-weight:700;cursor:pointer">Create for free 🎉</button>
  </div>
</nav>"""


def _lp_nav_saas(ctx: dict) -> str:
    p = ctx["primary"]
    return f"""
<nav style="background:#fff;border-bottom:1px solid #e8e8e8;padding:0 48px;display:flex;align-items:center;justify-content:space-between;height:60px">
  <span style="font-family:'{ctx['h_font']}',sans-serif;font-size:1rem;font-weight:700;color:#111;letter-spacing:-.01em">{ctx['name'].upper()}</span>
  <div style="display:flex;gap:28px;align-items:center">
    <a style="font-size:13px;color:#555;text-decoration:none;cursor:pointer">Product</a>
    <a style="font-size:13px;color:#555;text-decoration:none;cursor:pointer">Docs</a>
    <a style="font-size:13px;color:#555;text-decoration:none;cursor:pointer">Pricing</a>
    <a style="font-size:13px;color:#555;text-decoration:none;cursor:pointer">Sign in</a>
    <button style="background:{p};color:#fff;border:none;padding:9px 20px;border-radius:5px;font-size:13px;font-weight:600;cursor:pointer">Get started →</button>
  </div>
</nav>"""


def _lp_nav_corporate(ctx: dict) -> str:
    p = ctx["primary"]
    return f"""
<nav style="background:#fff;border-bottom:1px solid #e8e8e8;padding:0 48px;display:flex;align-items:center;justify-content:space-between;height:60px">
  <span style="font-family:'{ctx['h_font']}',sans-serif;font-size:1rem;font-weight:700;color:#111">{ctx['name']}</span>
  <div style="display:flex;gap:28px;align-items:center">
    <a style="font-size:13px;color:#555;text-decoration:none;cursor:pointer">Solutions</a>
    <a style="font-size:13px;color:#555;text-decoration:none;cursor:pointer">Enterprise</a>
    <a style="font-size:13px;color:#555;text-decoration:none;cursor:pointer">Resources</a>
    <a style="font-size:13px;color:#555;text-decoration:none;cursor:pointer">Contact</a>
    <button style="background:{p};color:#fff;border:none;padding:9px 20px;border-radius:4px;font-size:13px;font-weight:600;cursor:pointer">Request a demo</button>
  </div>
</nav>"""


def _lp_editorial_page(ctx: dict, css: str) -> str:
    p, s = ctx["primary"], ctx["secondary"]
    hf, bf = ctx["h_font"], ctx["b_font"]
    gf = f'<link rel="stylesheet" href="{ctx["gf_url"]}">' if ctx["gf_url"] else ""
    vals = ctx["values"][:3] or ["editorial", "contemplative", "rigorous"]
    kw   = ctx["keywords"][:4] or ["culture", "philosophy", "art", "thought"]

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{ctx['name']} — Revue de culture et de philosophie</title>
  {gf}
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: '{bf}', Georgia, serif; background: #fff; color: #111; line-height: 1.6; }}
    .page {{ max-width: 1100px; margin: 0 auto; padding: 0 48px; }}
    a {{ text-decoration: none; color: inherit; cursor: pointer; }}
  </style>
</head>
<body>

{_lp_nav_editorial(ctx)}

<!-- HERO — MASTHEAD -->
<section style="padding: 80px 0 64px; border-bottom: 2px solid #111;">
  <div class="page">
    <div style="display:grid;grid-template-columns:1fr 400px;gap:64px;align-items:end">
      <div>
        <div style="font-size:9px;letter-spacing:.35em;text-transform:uppercase;color:#aaa;margin-bottom:24px">N°47 · PRINTEMPS 2026 · {ctx['industry'].upper() or 'CULTURE & PHILOSOPHIE'}</div>
        <h1 style="font-family:'{hf}',Georgia,'Times New Roman',serif;font-size:5rem;font-weight:300;line-height:.92;letter-spacing:-.025em;color:#111;margin-bottom:28px">Sur la beauté<br>de l'inachevé</h1>
        <p style="font-size:15px;color:#555;line-height:1.8;max-width:520px;margin-bottom:32px">
          Comment les œuvres laissées ouvertes — fragments, ébauches, tentatives — nous disent-elles davantage que les œuvres closes ? Une méditation sur l'incomplétude comme forme d'honnêteté.
        </p>
        <a href="#" style="font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:#111;border-bottom:1px solid #111;padding-bottom:3px">LIRE L'ARTICLE →</a>
      </div>
      <div style="border-left:1px solid #e0e0e0;padding-left:40px">
        <div style="font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:#bbb;margin-bottom:20px">À LIRE AUSSI</div>
        <div style="margin-bottom:24px;padding-bottom:24px;border-bottom:1px solid #f0f0f0">
          <div style="font-size:8px;letter-spacing:.15em;text-transform:uppercase;color:#ccc;margin-bottom:8px">ESSAI</div>
          <p style="font-size:14px;font-weight:400;color:#111;line-height:1.4;margin-bottom:6px">La lenteur comme acte politique</p>
          <span style="font-size:11px;color:#999">par M. Descamps · 14 min</span>
        </div>
        <div style="margin-bottom:24px;padding-bottom:24px;border-bottom:1px solid #f0f0f0">
          <div style="font-size:8px;letter-spacing:.15em;text-transform:uppercase;color:#ccc;margin-bottom:8px">CRITIQUE</div>
          <p style="font-size:14px;font-weight:400;color:#111;line-height:1.4;margin-bottom:6px">Ce que le silence révèle dans l'art contemporain</p>
          <span style="font-size:11px;color:#999">par A. Moreau · 9 min</span>
        </div>
        <div>
          <div style="font-size:8px;letter-spacing:.15em;text-transform:uppercase;color:#ccc;margin-bottom:8px">ENTRETIEN</div>
          <p style="font-size:14px;font-weight:400;color:#111;line-height:1.4;margin-bottom:6px">Conversation avec Hito Steyerl sur les images et la vitesse</p>
          <span style="font-size:11px;color:#999">propos recueillis par S. Laurent · 18 min</span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- SECTION 1 — DANS CE NUMÉRO -->
<section style="padding:64px 0;border-bottom:1px solid #e0e0e0">
  <div class="page">
    <div style="font-size:9px;letter-spacing:.25em;text-transform:uppercase;color:#aaa;margin-bottom:40px">DANS CE NUMÉRO</div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0">
      <div style="padding-right:40px;border-right:1px solid #e8e8e8">
        <div style="font-size:8px;letter-spacing:.15em;text-transform:uppercase;color:hsl(from {p} h s 60%);margin-bottom:16px">PHILOSOPHIE</div>
        <h2 style="font-family:'{hf}',Georgia,serif;font-size:1.3rem;font-weight:400;line-height:1.35;color:#111;margin-bottom:12px">Les formes du doute dans la pensée contemporaine</h2>
        <p style="font-size:12px;color:#777;line-height:1.75;margin-bottom:16px">Un parcours à travers cinq philosophes qui ont fait de l'incertitude une méthode, plutôt qu'un obstacle.</p>
        <span style="font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#aaa">D. Ricard · 22 min</span>
      </div>
      <div style="padding:0 40px;border-right:1px solid #e8e8e8">
        <div style="font-size:8px;letter-spacing:.15em;text-transform:uppercase;color:hsl(from {p} h s 60%);margin-bottom:16px">ART</div>
        <h2 style="font-family:'{hf}',Georgia,serif;font-size:1.3rem;font-weight:400;line-height:1.35;color:#111;margin-bottom:12px">Cartographies du vide — cinq installations européennes</h2>
        <p style="font-size:12px;color:#777;line-height:1.75;margin-bottom:16px">De Berlin à Lisbonne, des artistes travaillent l'espace comme matériau de pensée. Enquête photographique.</p>
        <span style="font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#aaa">L. Fassi · 16 min</span>
      </div>
      <div style="padding-left:40px">
        <div style="font-size:8px;letter-spacing:.15em;text-transform:uppercase;color:hsl(from {p} h s 60%);margin-bottom:16px">LITTÉRATURE</div>
        <h2 style="font-family:'{hf}',Georgia,serif;font-size:1.3rem;font-weight:400;line-height:1.35;color:#111;margin-bottom:12px">Relire W.G. Sebald en 2026</h2>
        <p style="font-size:12px;color:#777;line-height:1.75;margin-bottom:16px">Pourquoi l'écrivain allemand n'a jamais été aussi nécessaire qu'aujourd'hui. Une relectue avec les yeux de l'inquiétude.</p>
        <span style="font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#aaa">T. Nora · 11 min</span>
      </div>
    </div>
  </div>
</section>

<!-- SECTION 2 — NOTE ÉDITORIALE / PULL QUOTE -->
<section style="padding:80px 0;background:#f9f8f6;border-bottom:1px solid #e0e0e0">
  <div class="page">
    <div style="display:grid;grid-template-columns:120px 1fr;gap:64px">
      <div>
        <div style="font-size:9px;letter-spacing:.25em;text-transform:uppercase;color:#aaa;writing-mode:vertical-rl;transform:rotate(180deg)">NOTE ÉDITORIALE</div>
      </div>
      <div style="max-width:680px">
        <p style="font-family:'{hf}',Georgia,serif;font-size:1.5rem;font-weight:300;line-height:1.6;color:#222;margin-bottom:32px;font-style:italic">
          "Nous vivons dans une époque qui confond vitesse et intelligence, volume et profondeur. Cette revue est une tentative de résistance — douce, mais déterminée."
        </p>
        <div style="width:48px;height:1px;background:#ccc;margin-bottom:24px"></div>
        <p style="font-size:13px;color:#777;line-height:1.75;margin-bottom:8px">
          {ctx['name']} paraît quatre fois par an. Chaque numéro explore un thème à travers des essais, des critiques, des entretiens et des formes hybrides.
          Notre ambition : donner du temps à la pensée.
        </p>
        <p style="font-size:11px;letter-spacing:.08em;color:#aaa;text-transform:uppercase">— La rédaction</p>
      </div>
    </div>
  </div>
</section>

<!-- SECTION 3 — CTA ABONNEMENT -->
<section style="padding:80px 0;border-bottom:1px solid #e0e0e0">
  <div class="page" style="display:grid;grid-template-columns:1fr 400px;gap:64px;align-items:center">
    <div>
      <div style="font-size:9px;letter-spacing:.25em;text-transform:uppercase;color:#aaa;margin-bottom:20px">S'ABONNER</div>
      <h2 style="font-family:'{hf}',Georgia,serif;font-size:2.2rem;font-weight:300;line-height:1.2;color:#111;margin-bottom:16px">Quatre numéros par an.<br>Une pensée continue.</h2>
      <p style="font-size:13px;color:#666;line-height:1.8">Recevez chaque numéro chez vous, en France et à l'international. Accès aux archives numériques inclus.</p>
    </div>
    <div style="border:1px solid #e0e0e0;padding:36px">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid #f0f0f0">
        <div>
          <div style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#999;margin-bottom:6px">Abonnement annuel</div>
          <div style="font-size:2rem;font-weight:300;color:#111">48 €<span style="font-size:12px;color:#aaa;font-weight:400"> /an</span></div>
        </div>
        <span style="font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:#aaa;border:1px solid #e0e0e0;padding:4px 10px">PAPIER + NUMÉRIQUE</span>
      </div>
      <button style="width:100%;background:#111;color:#fff;border:none;padding:14px;font-size:10px;letter-spacing:.2em;text-transform:uppercase;cursor:pointer">S'ABONNER</button>
      <p style="font-size:10px;color:#bbb;text-align:center;margin-top:12px;letter-spacing:.05em">RÉSILIATION POSSIBLE À TOUT MOMENT</p>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer style="padding:40px 0;background:#fff">
  <div class="page" style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-family:'{hf}',Georgia,serif;font-size:.9rem;color:#999;letter-spacing:.04em">{ctx['name'].upper()}</span>
    <div style="display:flex;gap:24px">
      <a style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#ccc">Mentions légales</a>
      <a style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#ccc">Contact</a>
      <a style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#ccc">ISSN 2026-XXXX</a>
    </div>
    <span style="font-size:10px;color:#ddd">© 2026</span>
  </div>
</footer>

</body>
</html>"""


def _lp_playful_page(ctx: dict, css: str) -> str:
    p, s = ctx["primary"], ctx["secondary"]
    hf, bf = ctx["h_font"], ctx["b_font"]
    gf = f'<link rel="stylesheet" href="{ctx["gf_url"]}">' if ctx["gf_url"] else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{ctx['name']} — Create magical birthday pages</title>
  {gf}
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: '{bf}', sans-serif; background: #fff; color: #111; line-height: 1.6; }}
    .page {{ max-width: 1060px; margin: 0 auto; padding: 0 32px; }}
    a {{ text-decoration: none; color: inherit; cursor: pointer; }}
  </style>
</head>
<body>

{_lp_nav_playful(ctx)}

<!-- HERO -->
<section style="background:{p};padding:80px 32px 72px;text-align:center">
  <div class="page">
    <div style="font-size:4rem;margin-bottom:20px">🕯️ ✨ 🎉</div>
    <h1 style="font-family:'{hf}',sans-serif;font-size:3.5rem;font-weight:800;color:#fff;line-height:1.05;margin-bottom:20px">Create the birthday page<br>they'll never forget</h1>
    <p style="font-family:'{bf}',sans-serif;font-size:1.1rem;color:rgba(255,255,255,.85);max-width:500px;margin:0 auto 36px;line-height:1.65">Add photos, music, messages, and confetti. Share it in one link. Free to start.</p>
    <div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap">
      <button style="background:#fff;color:{p};border:none;padding:16px 36px;border-radius:100px;font-size:1rem;font-weight:800;cursor:pointer">🎂 Create a page — it's free</button>
      <button style="background:rgba(255,255,255,.16);color:#fff;border:2px solid rgba(255,255,255,.45);padding:16px 32px;border-radius:100px;font-size:1rem;cursor:pointer">See examples →</button>
    </div>
    <p style="font-size:12px;color:rgba(255,255,255,.55);margin-top:20px">No account needed · Ready in 5 minutes · 100% free</p>
  </div>
</section>

<!-- SECTION 1 — HOW IT WORKS -->
<section style="padding:80px 0;border-bottom:2px dashed {p}22">
  <div class="page">
    <div style="text-align:center;margin-bottom:56px">
      <h2 style="font-family:'{hf}',sans-serif;font-size:2rem;font-weight:800;color:#111;margin-bottom:12px">As easy as 1, 2, 🎁</h2>
      <p style="font-size:15px;color:#777;max-width:420px;margin:0 auto">Three steps and you're done. No design skills needed.</p>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:32px">
      <div style="text-align:center">
        <div style="width:72px;height:72px;background:{p}18;border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:2rem;margin:0 auto 20px">🎨</div>
        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:{p};font-weight:700;margin-bottom:10px">STEP 01</div>
        <h3 style="font-family:'{hf}',sans-serif;font-size:1.1rem;font-weight:700;color:#111;margin-bottom:8px">Pick a vibe</h3>
        <p style="font-size:13px;color:#777;line-height:1.7">Choose from dozens of themes — sparkly, cozy, tropical, retro. There's one for every personality.</p>
      </div>
      <div style="text-align:center">
        <div style="width:72px;height:72px;background:{s}18;border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:2rem;margin:0 auto 20px">📸</div>
        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:{s};font-weight:700;margin-bottom:10px">STEP 02</div>
        <h3 style="font-family:'{hf}',sans-serif;font-size:1.1rem;font-weight:700;color:#111;margin-bottom:8px">Add your magic</h3>
        <p style="font-size:13px;color:#777;line-height:1.7">Upload photos, write heartfelt messages, add a playlist, or record a quick video. Make it personal.</p>
      </div>
      <div style="text-align:center">
        <div style="width:72px;height:72px;background:#f0fff418;border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:2rem;margin:0 auto 20px">🔗</div>
        <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:#16a34a;font-weight:700;margin-bottom:10px">STEP 03</div>
        <h3 style="font-family:'{hf}',sans-serif;font-size:1.1rem;font-weight:700;color:#111;margin-bottom:8px">Share the joy</h3>
        <p style="font-size:13px;color:#777;line-height:1.7">Send your link by text, email, or WhatsApp. Watch them cry happy tears when they open it. 🥹</p>
      </div>
    </div>
  </div>
</section>

<!-- SECTION 2 — FEATURES -->
<section style="padding:80px 0;background:#fffbf5;border-bottom:2px dashed {p}22">
  <div class="page">
    <div style="text-align:center;margin-bottom:48px">
      <h2 style="font-family:'{hf}',sans-serif;font-size:2rem;font-weight:800;color:#111;margin-bottom:12px">Everything you need to celebrate ✨</h2>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px">
      {''.join(f"""<div style="background:#fff;border:2px dashed {p}33;border-radius:20px;padding:28px;text-align:center">
        <div style="font-size:2rem;margin-bottom:12px">{emoji}</div>
        <h3 style="font-family:'{hf}',sans-serif;font-size:.95rem;font-weight:700;color:#111;margin-bottom:8px">{title}</h3>
        <p style="font-size:12px;color:#888;line-height:1.65">{desc}</p>
      </div>""" for emoji, title, desc in [
        ("🖼️", "Photo gallery", "Add up to 50 photos and let memories do the talking."),
        ("🎵", "Music playlist", "Pick songs that remind you of them. Auto-plays on open."),
        ("💌", "Group messages", "Invite friends to contribute their own messages secretly."),
        ("🎊", "Confetti effect", "Because birthdays need at least a little chaos."),
        ("⏳", "Countdown timer", "Build suspense from 7 days out. Drama is encouraged."),
        ("📱", "Mobile-first", "Looks perfect on any device. No app download required."),
      ])}
    </div>
  </div>
</section>

<!-- SECTION 3 — TESTIMONIALS -->
<section style="padding:80px 0;border-bottom:2px dashed {p}22">
  <div class="page">
    <div style="text-align:center;margin-bottom:48px">
      <h2 style="font-family:'{hf}',sans-serif;font-size:2rem;font-weight:800;color:#111;margin-bottom:12px">People are actually crying 🥹 (happy tears)</h2>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:24px">
      {''.join(f"""<div style="background:{bg};border-radius:20px;padding:28px">
        <div style="font-size:1.5rem;margin-bottom:12px">{stars}</div>
        <p style="font-size:14px;color:#333;line-height:1.7;font-style:italic;margin-bottom:16px">"{quote}"</p>
        <div style="font-size:12px;color:#999">{author}</div>
      </div>""" for bg, stars, quote, author in [
        ("#fff8f0", "⭐⭐⭐⭐⭐", "I made one for my mom's 60th and she cried for 10 minutes. Best gift I've ever given and it was free.", "— Léa M., Lyon"),
        ("#f0fff8", "⭐⭐⭐⭐⭐", "My whole friend group contributed messages for my partner's birthday. She was completely speechless. 10/10.", "— Theo K., Berlin"),
        ("#fff0f8", "⭐⭐⭐⭐⭐", "I'm not a creative person at all but the page looked stunning. Took me 8 minutes. Sent it in 9.", "— Priya S., London"),
      ])}
    </div>
  </div>
</section>

<!-- CTA FINAL -->
<section style="background:{p};padding:80px 32px;text-align:center">
  <div class="page">
    <div style="font-size:2.5rem;margin-bottom:20px">🎂</div>
    <h2 style="font-family:'{hf}',sans-serif;font-size:2.5rem;font-weight:800;color:#fff;margin-bottom:16px">Someone's birthday is coming up.</h2>
    <p style="font-size:1rem;color:rgba(255,255,255,.85);max-width:400px;margin:0 auto 32px;line-height:1.65">Create something they'll screenshot and save forever. It takes 5 minutes and it's free.</p>
    <button style="background:#fff;color:{p};border:none;padding:18px 48px;border-radius:100px;font-size:1.1rem;font-weight:800;cursor:pointer">✨ Create your page now</button>
    <p style="font-size:11px;color:rgba(255,255,255,.5);margin-top:16px">No account needed · No credit card · Always free</p>
  </div>
</section>

<!-- FOOTER -->
<footer style="background:#111;padding:48px 0">
  <div class="page" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:20px">
    <span style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:800;color:#fff">🕯️ {ctx['name']}</span>
    <div style="display:flex;gap:24px">
      <a style="font-size:12px;color:#777">Privacy</a>
      <a style="font-size:12px;color:#777">Terms</a>
      <a style="font-size:12px;color:#777">Contact</a>
    </div>
    <span style="font-size:12px;color:#555">Made with ❤️ for birthdays everywhere · © 2026</span>
  </div>
</footer>

</body>
</html>"""


def _lp_saas_page(ctx: dict, css: str) -> str:
    p, s = ctx["primary"], ctx["secondary"]
    hf, bf = ctx["h_font"], ctx["b_font"]
    gf = f'<link rel="stylesheet" href="{ctx["gf_url"]}">' if ctx["gf_url"] else ""
    kw = ctx["keywords"][:3] or ["automation", "reliability", "control"]
    vals = ctx["values"][:3] or ["precision", "control", "reliability"]
    industry_upper = (ctx["industry"] or "INFRASTRUCTURE PLATFORM").upper()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{ctx['name']} — Data infrastructure automation for serious teams</title>
  {gf}
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: '{bf}', sans-serif; background: #fff; color: #111; line-height: 1.6; }}
    .page {{ max-width: 1080px; margin: 0 auto; padding: 0 48px; }}
    a {{ text-decoration: none; color: inherit; cursor: pointer; }}
  </style>
</head>
<body>

{_lp_nav_saas(ctx)}

<!-- HERO -->
<section style="background:{p};padding:80px 48px 72px;text-align:center">
  <div class="page">
    <div style="display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);padding:5px 16px;border-radius:100px;font-size:11px;color:rgba(255,255,255,.8);letter-spacing:.08em;margin-bottom:28px">NOW IN PUBLIC BETA — Join 2,000+ teams</div>
    <h1 style="font-family:'{hf}',sans-serif;font-size:3.5rem;font-weight:700;color:#fff;line-height:1.05;margin-bottom:20px;letter-spacing:-.02em">The infrastructure platform<br>built for precision</h1>
    <p style="font-family:'{bf}',sans-serif;font-size:1.05rem;color:rgba(255,255,255,.82);max-width:540px;margin:0 auto 36px;line-height:1.7">Automate your data infrastructure with confidence. Zero-downtime deploys, real-time observability, and full control for engineering teams who care about reliability.</p>
    <div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap">
      <button style="background:#fff;color:{p};border:none;padding:14px 32px;border-radius:5px;font-size:14px;font-weight:700;cursor:pointer">Start for free →</button>
      <button style="background:rgba(255,255,255,.12);color:#fff;border:1px solid rgba(255,255,255,.3);padding:14px 28px;border-radius:5px;font-size:14px;cursor:pointer">Schedule a demo</button>
    </div>
    <div style="display:flex;gap:40px;justify-content:center;margin-top:48px;flex-wrap:wrap">
      {''.join(f'<div style="text-align:center"><div style="font-size:1.6rem;font-weight:700;color:#fff">{val}</div><div style="font-size:11px;color:rgba(255,255,255,.55);letter-spacing:.06em;text-transform:uppercase;margin-top:4px">{label}</div></div>' for val, label in [("99.99%", "Uptime SLA"), ("<200ms", "p99 latency"), ("2,400+", "Teams"), ("10B+", "Events/day")])}
    </div>
  </div>
</section>

<!-- SECTION 1 — FEATURES -->
<section style="padding:80px 0;border-bottom:1px solid #e8e8e8">
  <div class="page">
    <div style="margin-bottom:56px">
      <div style="font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:{p};margin-bottom:12px">WHAT WE DO</div>
      <h2 style="font-family:'{hf}',sans-serif;font-size:2.2rem;font-weight:700;color:#111;margin-bottom:16px;letter-spacing:-.01em">Built for precision at scale</h2>
      <p style="font-size:15px;color:#666;max-width:540px;line-height:1.7">Every feature is designed for engineering teams that can't afford surprises.</p>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:40px">
      {''.join(f"""<div>
        <div style="width:44px;height:44px;background:{p}12;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;margin-bottom:20px">{icon}</div>
        <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:700;color:#111;margin-bottom:8px">{title}</h3>
        <p style="font-size:13px;color:#666;line-height:1.7">{desc}</p>
      </div>""" for icon, title, desc in [
        ("⚡", "Zero-downtime deploys", "Blue/green and canary deployments out of the box. Roll forward or back in under 30 seconds."),
        ("📊", "Real-time observability", "Full-stack traces, structured logs, and custom metrics. One pane of glass for your entire infrastructure."),
        ("🔒", "Security by default", "SOC 2 Type II certified. RBAC, audit logs, and end-to-end encryption. Compliance built in, not bolted on."),
        ("🔄", "Intelligent auto-scaling", "Scale from 0 to millions of requests without touching a config file. Cost-optimized automatically."),
        ("🧩", "API-first design", "Everything you can do in the UI, you can do via API. Integrate with your existing workflow in minutes."),
        ("📍", "Multi-region by default", "Deploy to 20+ regions globally. Latency-optimized routing and automatic failover included."),
      ])}
    </div>
  </div>
</section>

<!-- SECTION 2 — HOW IT WORKS -->
<section style="padding:80px 0;background:#f8f9fa;border-bottom:1px solid #e8e8e8">
  <div class="page">
    <div style="text-align:center;margin-bottom:56px">
      <div style="font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:{p};margin-bottom:12px">HOW IT WORKS</div>
      <h2 style="font-family:'{hf}',sans-serif;font-size:2.2rem;font-weight:700;color:#111;letter-spacing:-.01em">From code to production in minutes</h2>
    </div>
    <div style="position:relative">
      <div style="position:absolute;left:24px;top:0;bottom:0;width:1px;background:#e0e0e0"></div>
      {''.join(f"""<div style="display:grid;grid-template-columns:64px 1fr;gap:24px;align-items:start;margin-bottom:40px;position:relative">
        <div style="width:48px;height:48px;background:{p};border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;position:relative;z-index:1">{num}</div>
        <div style="padding-top:10px">
          <h3 style="font-family:'{hf}',sans-serif;font-size:1rem;font-weight:700;color:#111;margin-bottom:6px">{title}</h3>
          <p style="font-size:13px;color:#666;line-height:1.7;max-width:600px">{desc}</p>
        </div>
      </div>""" for num, title, desc in [
        ("01", "Connect your repository", "Link your GitHub, GitLab, or Bitbucket in one click. We detect your stack automatically."),
        ("02", "Define your infrastructure", "Use our declarative config or import your existing Terraform. No proprietary DSL to learn."),
        ("03", "Deploy with confidence", "Every push triggers a validated pipeline. Automated testing, security scanning, and staged rollout."),
        ("04", "Monitor and iterate", "Real-time dashboards, alerts, and distributed tracing. Know what's happening before your users do."),
      ])}
    </div>
  </div>
</section>

<!-- SECTION 3 — SOCIAL PROOF -->
<section style="padding:80px 0;border-bottom:1px solid #e8e8e8">
  <div class="page" style="text-align:center">
    <p style="font-size:12px;letter-spacing:.15em;text-transform:uppercase;color:#aaa;margin-bottom:40px">TRUSTED BY ENGINEERING TEAMS AT</p>
    <div style="display:flex;gap:48px;justify-content:center;align-items:center;flex-wrap:wrap;margin-bottom:56px">
      {''.join(f'<span style="font-family:\'{hf}\',sans-serif;font-size:1rem;font-weight:700;color:#ccc;letter-spacing:-.01em">{name}</span>' for name in ["Axiom", "Vercel", "PlanetScale", "Resend", "Cal.com", "Liveblocks"])}
    </div>
    <div style="background:#f8f9fa;border:1px solid #e8e8e8;border-radius:8px;padding:40px;max-width:680px;margin:0 auto;text-align:left">
      <p style="font-size:1rem;color:#333;line-height:1.75;font-style:italic;margin-bottom:20px">"We cut our infrastructure incidents by 73% in the first quarter after switching to {ctx['name']}. The observability stack alone was worth it — but the zero-downtime deploys are what convinced our CTO."</p>
      <div style="display:flex;align-items:center;gap:16px">
        <div style="width:40px;height:40px;background:{p}20;border-radius:50%"></div>
        <div>
          <div style="font-size:13px;font-weight:600;color:#111">Marcus Chen</div>
          <div style="font-size:12px;color:#999">Head of Platform Engineering, Axiom</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- CTA FINAL -->
<section style="background:#0f172a;padding:80px 48px;text-align:center">
  <div class="page">
    <h2 style="font-family:'{hf}',sans-serif;font-size:2.5rem;font-weight:700;color:#e2e8f0;margin-bottom:16px;letter-spacing:-.02em">Start building today</h2>
    <p style="font-size:15px;color:#94a3b8;max-width:440px;margin:0 auto 36px;line-height:1.7">Free tier includes 1M events/month, 3 environments, and full observability. No credit card required.</p>
    <div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap">
      <button style="background:{p};color:#fff;border:none;padding:16px 36px;border-radius:5px;font-size:15px;font-weight:700;cursor:pointer">Start for free →</button>
      <button style="background:transparent;color:#94a3b8;border:1px solid #334155;padding:16px 32px;border-radius:5px;font-size:15px;cursor:pointer">Schedule a demo</button>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer style="background:#0f172a;border-top:1px solid #1e293b;padding:40px 48px">
  <div class="page" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">
    <span style="font-family:'{hf}',sans-serif;font-size:.9rem;font-weight:700;color:#475569">{ctx['name'].upper()}</span>
    <div style="display:flex;gap:28px">
      {''.join(f'<a style="font-size:12px;color:#475569">{link}</a>' for link in ["Product", "Docs", "Changelog", "Status", "Privacy"])}
    </div>
    <span style="font-size:12px;color:#334155">© 2026 {ctx['name']}</span>
  </div>
</footer>

</body>
</html>"""


def generate_landing_page(
    project_name: str,
    brief_text: str,
    dna,
    exploration,
    preset: dict | None,
    css: str | None,
) -> str:
    """
    Generate a complete branded landing page for the project.
    Picks the best creative direction and renders a full standalone HTML page.
    """
    direction = _select_direction(exploration, brief_text)
    archetype = getattr(direction, "style_archetype", "startup_clean") if direction else "startup_clean"
    ctx       = _ctx(project_name, brief_text, dna, preset)

    EDITORIAL_ARCHETYPES = {"editorial_magazine", "luxury_minimal", "premium_craft"}
    PLAYFUL_ARCHETYPES   = {"playful_brand", "warm_human", "organic_natural", "creative_studio"}

    if archetype in EDITORIAL_ARCHETYPES:
        return _lp_editorial_page(ctx, css or "")
    if archetype in PLAYFUL_ARCHETYPES:
        return _lp_playful_page(ctx, css or "")
    return _lp_saas_page(ctx, css or "")


# ── Pipeline runner ───────────────────────────────────────────────────────────

def run_pipeline(project_name: str, brief_text: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {project_name}")
    print(f"{'─' * 60}")

    slug    = project_name.lower().replace(" ", "_")
    out_dir = OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline_ok: dict[str, bool | None] = {}

    # ── Step 1: Design DNA ────────────────────────────────────────────────────
    print("  [1/5] design_dna_resolver …")
    dna = step_dna(brief_text, project_name)
    pipeline_ok["dna"] = dna is not None

    # ── Step 2: Color psychology ──────────────────────────────────────────────
    print("  [2/5] color_psychology_engine …")
    rec = step_psychology(dna)
    pipeline_ok["rec"] = rec is not None

    # ── Step 3: Palette ───────────────────────────────────────────────────────
    print("  [3/5] palette_generator …")
    palette_output = step_palette(dna, rec)
    pipeline_ok["palette"] = palette_output is not None

    # ── Step 4: Creative directions ───────────────────────────────────────────
    print("  [4/5] design_exploration_engine …")
    exploration = step_explore(dna)
    pipeline_ok["explore"] = exploration is not None

    # ── Step 5: Theme ─────────────────────────────────────────────────────────
    print("  [5/5] theme_generator …")
    style_dna = step_build_style_dna(dna, palette_output, rec)
    preset, css = step_theme(style_dna)
    pipeline_ok["theme"] = preset is not None

    # ── Save artifacts ────────────────────────────────────────────────────────
    def _save_json(name: str, data: object) -> None:
        try:
            (out_dir / name).write_text(
                json.dumps(data, indent=2, default=str), encoding="utf-8"
            )
        except Exception as e:
            print(f"    ⚠️  Could not save {name}: {e}")

    _save_json("style_dna.json", asdict(style_dna) if style_dna else {})

    if palette_output:
        try:
            _save_json("palette.json", asdict(palette_output.palette_set))
        except Exception:
            _save_json("palette.json", {"error": "serialization failed"})

    if exploration:
        try:
            _save_json("creative_directions.json", asdict(exploration))
        except Exception:
            _save_json("creative_directions.json", {"error": "serialization failed"})

    if preset:
        _save_json("theme_preset.json", preset)

    if css:
        (out_dir / "theme.css").write_text(css, encoding="utf-8")

    # ── Generate HTML ─────────────────────────────────────────────────────────
    html_content = generate_html(
        project_name=project_name,
        brief_text=brief_text,
        dna=dna,
        rec=rec,
        palette_output=palette_output,
        exploration=exploration,
        style_dna=style_dna,
        preset=preset,
        css=css,
        pipeline_ok=pipeline_ok,
    )
    html_path = out_dir / "brand_charter.html"
    html_path.write_text(html_content, encoding="utf-8")

    # ── Landing page ──────────────────────────────────────────────────────────
    lp_content = generate_landing_page(
        project_name=project_name,
        brief_text=brief_text,
        dna=dna,
        exploration=exploration,
        preset=preset,
        css=css,
    )
    lp_path = out_dir / "landing_page.html"
    lp_path.write_text(lp_content, encoding="utf-8")

    ok_count = sum(1 for v in pipeline_ok.values() if v is True)
    tot = len(pipeline_ok)
    print(f"  ✅ {ok_count}/{tot} steps OK → {html_path}")

# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="EURKAI pipeline test — generates HTML brand charters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python generate_brand_charter.py
          python generate_brand_charter.py --project vectorstack
          python generate_brand_charter.py --brief "A wellness app..." --name "ZenApp"
        """),
    )
    parser.add_argument("--project", metavar="NAME",
                        help="Run a specific test brief (vectorstack | ateliernocturne | candlespark)")
    parser.add_argument("--brief",   metavar="TEXT",
                        help="Run a custom brief (requires --name)")
    parser.add_argument("--name",    metavar="NAME", default="Custom",
                        help="Project name for --brief mode")
    args = parser.parse_args()

    if _import_errors:
        print("⚠️  Import errors (pipeline steps will be skipped):")
        for err in _import_errors:
            print(f"   • {err}")

    if args.brief:
        run_pipeline(args.name, args.brief)
        return

    projects = TEST_BRIEFS
    if args.project:
        slug = args.project.lower().replace(" ", "").replace("_", "")
        projects = [
            p for p in TEST_BRIEFS
            if p[0].lower().replace(" ", "").replace("_", "") == slug
        ]
        if not projects:
            print(f"Unknown project '{args.project}'. Available: vectorstack, ateliernocturne, candlespark")
            sys.exit(1)

    print(f"\n{'═' * 60}")
    print("  EURKAI · Brand Charter Generator · pipeline-validator")
    print(f"  {len(projects)} project(s) to process")
    print(f"{'═' * 60}")

    for name, brief in projects:
        run_pipeline(name, brief)

    print(f"\n{'═' * 60}")
    print(f"  Done. Charters saved in: {OUTPUT_DIR}/")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
