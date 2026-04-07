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
import base64
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

try:
    from visual_coherence_engine import compute_image_adjustments as _coherence_adjustments
    _coherence_ok = True
except ImportError:
    _coherence_ok = False
    def _coherence_adjustments(palette: dict, dark_mode: bool) -> dict:  # type: ignore
        op = "0.60" if dark_mode else "0.42"
        return {"duotone": True, "overlay_color": palette.get("primary", "#4A7CFF"),
                "overlay_opacity": float(op), "filter": "grayscale(1) contrast(1.1)",
                "blend_mode": "color"}

try:
    from pictogram_system import generate_pictogram_set as _gen_pictograms
    _pictogram_ok = True
except ImportError:
    _pictogram_ok = False
    _gen_pictograms = None  # type: ignore

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
    import re as _re
    h = h.strip()
    # Handle rgb(...) / rgba(...)
    if h.startswith("rgb"):
        nums = _re.findall(r"[\d.]+", h)
        if len(nums) >= 3:
            r, g, b = float(nums[0])/255, float(nums[1])/255, float(nums[2])/255
            def lc(c: float) -> float:
                return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
            return 0.2126 * lc(r) + 0.7152 * lc(g) + 0.0722 * lc(b)
        return 0.0
    h = h.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    if len(h) < 6:
        return 0.0
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    def lc(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lc(r) + 0.7152 * lc(g) + 0.0722 * lc(b)


def text_on(bg_hex: str) -> str:
    """Return '#fff' or '#111' depending on bg luminance. Accepts hex or rgb(...)."""
    return "#fff" if hex_luminance(bg_hex) < 0.35 else "#111"


def _parse_color(color: str) -> tuple[float, float, float]:
    """Parse hex or rgb(...) to (r,g,b) floats. Returns (0,0,0) on failure."""
    import re as _re
    color = color.strip()
    if color.startswith("rgb"):
        nums = _re.findall(r"[\d.]+", color)
        if len(nums) >= 3:
            return float(nums[0]), float(nums[1]), float(nums[2])
    if color.startswith("#"):
        h = color.lstrip("#")
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        if len(h) == 6:
            return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return 0.0, 0.0, 0.0


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
    _it      = _text_on(p)                                        # "#fff" ou "#111"
    _dark_bg = (_it == "#fff")                                    # fond sombre → texte blanc
    _muted   = "rgba(255,255,255,.80)" if _dark_bg else "rgba(0,0,0,.60)"
    _btn_bg  = "rgba(255,255,255,.15)" if _dark_bg else "rgba(0,0,0,.10)"
    _btn_brd = "rgba(255,255,255,.45)" if _dark_bg else "rgba(0,0,0,.25)"
    return f"""<div style="background:{p};padding:52px 32px;text-align:center;border-radius:{r}">
  <h1 style="font-family:'{hf}',sans-serif;color:{_it};font-size:2.4rem;font-weight:700;margin-bottom:12px;line-height:1.1">Build something meaningful</h1>
  <p style="font-family:'{bf}',sans-serif;color:{_muted};max-width:480px;margin:0 auto 24px;font-size:15px;line-height:1.65">A platform built for people who care about craft, clarity, and impact.</p>
  <div style="display:flex;gap:12px;justify-content:center">
    <button style="background:{_it};color:{p};border:none;padding:12px 24px;border-radius:{r};font-size:14px;font-weight:600;cursor:pointer">Get started</button>
    <button style="background:{_btn_bg};color:{_it};border:1px solid {_btn_brd};padding:12px 24px;border-radius:{r};font-size:14px;cursor:pointer">Learn more</button>
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

def _demo_copy(project_name: str, brief_text: str, archetype: str) -> dict:
    """Generate realistic page copy tuned to archetype and brief."""
    n = html_lib.escape(project_name)
    brief_l = brief_text.lower()

    # Taglines per archetype
    _taglines = {
        "corporate_pro":       [f"Infrastructure that scales with you.", "Built for engineering teams who demand precision.", "Reliable by design. Trusted by teams."],
        "editorial_magazine":  [f"Slow down. Think deeper.", "A space for ideas that last.", "Beauty in thought."],
        "luxury_minimal":      [f"Crafted for those who notice the difference.", "Less, but better.", "Precision. Elegance. Presence."],
        "tech_futurist":       [f"The future of data, today.", "Push the limits of what's possible.", "Build beyond boundaries."],
        "creative_studio":     [f"Make something that matters.", "Where ideas become form.", "Design without compromise."],
        "startup_clean":       [f"Simpler. Faster. Smarter.", "Everything your team needs.", "Ship with confidence."],
        "bold_challenger":     [f"Break the default.", "For those who refuse ordinary.", "The platform that fights back."],
        "playful_brand":       [f"Built with joy, made for people.", "Work should feel good.", "Because good tools make great days."],
        "warm_human":          [f"People first, always.", "Technology with a human touch.", "Built around the people who use it."],
        "premium_craft":       [f"Every detail, considered.", "Craftsmanship at every layer.", "Excellence is the only option."],
    }

    # Feature names per archetype
    _features = {
        "corporate_pro":       [("Reliability", "99.99% uptime SLA backed by enterprise infrastructure."), ("Precision", "Deterministic pipelines with full audit trails and versioning."), ("Control", "Granular permissions and compliance-ready from day one."), ("Insight", "Real-time observability across every layer of your stack.")],
        "editorial_magazine":  [("Curation", "Every piece is selected for depth, not volume."), ("Rhythm", "Long-form layouts designed to be read, not scanned."), ("Voice", "Writing that earns its place on the page."), ("Silence", "White space is not empty — it is the work breathing.")],
        "luxury_minimal":      [("Exclusivity", "Access reserved for those who understand the difference."), ("Materials", "Every surface, texture, and transition considered."), ("Restraint", "When less is the most powerful choice you can make."), ("Heritage", "Built on craft, refined over time.")],
        "tech_futurist":       [("Edge Computing", "Process at the source, reduce latency to zero."), ("AI-Native", "Intelligence embedded at every layer of your stack."), ("Real-Time", "From data to action in under 100ms."), ("Autonomy", "Self-healing infrastructure that adapts automatically.")],
        "creative_studio":     [("Expression", "Tools that amplify your voice, not replace it."), ("Iteration", "From concept to output in hours, not days."), ("Collaboration", "Creative work is never solo. We built for that."), ("Boldness", "Design systems that reward experimentation.")],
        "startup_clean":       [("Speed", "Deploy in minutes, iterate in seconds."), ("Simplicity", "One integration, everything connected."), ("Automation", "Let the platform do the repetitive work."), ("Visibility", "See everything. Know everything. Act fast.")],
    }

    # KPI stats per archetype
    _stats = {
        "corporate_pro":   [("99.99%", "Uptime SLA"), ("< 50ms", "P99 Latency"), ("10,000+", "Active Teams"), ("SOC 2", "Certified")],
        "editorial_magazine": [("240+", "Published pieces"), ("18 min", "Avg. read time"), ("94%", "Reader retention"), ("12 years", "In print and digital")],
        "luxury_minimal":  [("Since 1997", "Heritage"), ("87", "Selected clients"), ("100%", "Handcrafted"), ("0", "Compromises made")],
        "tech_futurist":   [("1B+", "Events/day"), ("< 10ms", "Edge latency"), ("200+", "Integrations"), ("∞", "Scalability")],
        "creative_studio": [("5,000+", "Projects shipped"), ("48h", "Avg. turnaround"), ("120", "Studio members"), ("32", "Countries")],
        "startup_clean":   [("3 min", "Setup time"), ("98%", "Customer satisfaction"), ("500+", "Integrations"), ("24/7", "Support")],
    }

    taglines = _taglines.get(archetype, _taglines["startup_clean"])
    feats    = _features.get(archetype, _features["startup_clean"])
    stats    = _stats.get(archetype, _stats["startup_clean"])

    # Quote per archetype
    _quotes = {
        "corporate_pro": ("The moment we standardized on it, our deployment confidence jumped overnight.", "Sarah K., Platform Lead"),
        "editorial_magazine": ("Reading here feels different. There's no hurry. The page respects your time.", "Thomas L., subscriber"),
        "luxury_minimal": ("I've never seen this level of finish from a digital product. It sets a standard.", "C. Ferrara, Creative Director"),
        "tech_futurist": ("It doesn't just process data. It thinks ahead of you.", "Yuki M., Head of Engineering"),
        "creative_studio": ("We went from 'this could work' to 'this is the one' in a single session.", "Marco V., Art Director"),
        "startup_clean": ("We cut our onboarding time in half. The team barely needed documentation.", "Jordan P., CTO"),
    }
    quote, quote_author = _quotes.get(archetype, _quotes["startup_clean"])

    body_lorem = "Consistent, observable, and built for teams that can't afford surprises. Every decision was made with long-term reliability in mind, from the way data flows through the system to how errors surface and resolve without manual intervention."

    if "editorial" in archetype or "luxury" in archetype:
        body_lorem = "There is a particular satisfaction in things made with care. Not optimized, not A/B tested — considered. Laid out with the confidence of something that knows exactly what it is and does not need to apologize for it."
    elif "futurist" in archetype or "creative" in archetype:
        body_lorem = "The system doesn't ask for permission. It moves. It adapts. Built for those who already know where they're going and need the infrastructure to keep up, not slow them down."

    return {
        "name": n, "taglines": taglines, "tagline": taglines[0],
        "tagline2": taglines[1] if len(taglines) > 1 else taglines[0],
        "tagline3": taglines[2] if len(taglines) > 2 else taglines[0],
        "body": body_lorem, "features": feats, "stats": stats,
        "quote": html_lib.escape(quote), "quote_author": html_lib.escape(quote_author),
        "cta_primary": "Get started" if "startup" in archetype else ("Request access" if "luxury" in archetype or "corporate" in archetype else "Explore now"),
        "cta_secondary": "Read the docs" if "corporate" in archetype else ("Learn more" if "editorial" in archetype else "See examples"),
    }


def _archetype_signature(archetype: str, primary: str, accent: str, neutral: str) -> dict:
    """
    Visual identity signature layer — archetype-specific.
    Returns: css, hero_overlay, hero_pat, sep, card_sig
    """
    try:
        ar, ag, ab = _parse_color(accent)
        ar, ag, ab = int(ar), int(ag), int(ab)
    except Exception:
        ar, ag, ab = 200, 160, 60

    def _b64(svg: str) -> str:
        return base64.b64encode(svg.encode()).decode()

    if archetype in ("luxury_minimal", "editorial_magazine", "premium_craft"):
        pat = _b64(
            '<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60">'
            '<line x1="0" y1="60" x2="60" y2="0" stroke="rgba(255,255,255,.04)" stroke-width="1"/>'
            '</svg>'
        )
        return dict(
            css=f".euk-card-sig{{border-top:2px solid {accent}!important}}",
            hero_overlay=f"linear-gradient(160deg,rgba(0,0,0,.72) 0%,rgba(0,0,0,.3) 100%)",
            hero_pat=f"background-image:url('data:image/svg+xml;base64,{pat}');background-size:60px 60px;",
            sep=f'<div style="width:32px;height:1px;background:{accent};margin:0 auto 40px"></div>',
            card_sig=f"border-top:2px solid {accent};",
        )

    elif archetype in ("corporate_pro", "startup_clean"):
        pat = _b64(
            '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32">'
            '<path d="M 32 0 L 0 0 L 0 32" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="1"/>'
            '</svg>'
        )
        sep_html = (
            f'<div style="display:flex;align-items:center;gap:8px;justify-content:center;margin-bottom:40px">'
            f'<div style="width:24px;height:1px;background:{accent}"></div>'
            f'<div style="width:5px;height:5px;background:{accent};transform:rotate(45deg)"></div>'
            f'<div style="width:24px;height:1px;background:{accent}"></div>'
            f'</div>'
        )
        return dict(
            css=f".euk-card-sig{{border-left:3px solid {accent}!important;padding-left:21px!important}}",
            hero_overlay="linear-gradient(180deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,.15) 70%)",
            hero_pat=f"background-image:url('data:image/svg+xml;base64,{pat}');background-size:32px 32px;",
            sep=sep_html,
            card_sig=f"border-left:3px solid {accent};padding-left:21px;",
        )

    elif archetype in ("tech_futurist", "bold_challenger", "creative_studio"):
        pat = _b64(
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">'
            '<circle cx="12" cy="12" r="1.2" fill="rgba(255,255,255,.12)"/>'
            '</svg>'
        )
        return dict(
            css=(
                f".euk-card:hover{{box-shadow:0 0 40px rgba({ar},{ag},{ab},.2),"
                f"0 16px 40px rgba(0,0,0,.15)!important;transform:translateY(-6px)!important}}"
                f".euk-btn-primary:hover{{box-shadow:0 0 28px rgba({ar},{ag},{ab},.45),"
                f"0 8px 20px rgba(0,0,0,.2)!important}}"
            ),
            hero_overlay="linear-gradient(135deg,rgba(0,0,0,.65) 0%,rgba(0,0,0,.2) 100%)",
            hero_pat=f"background-image:url('data:image/svg+xml;base64,{pat}');background-size:24px 24px;",
            sep=f'<div style="width:100%;height:1px;background:linear-gradient(90deg,transparent,{accent},transparent);margin-bottom:40px"></div>',
            card_sig=f"border:1px solid rgba({ar},{ag},{ab},.35);",
        )

    else:  # playful_brand, warm_human, organic_natural, brutalist, fallback
        pat = _b64(
            '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48">'
            '<circle cx="8" cy="8" r="2" fill="rgba(255,255,255,.08)"/>'
            '<circle cx="40" cy="32" r="3" fill="rgba(255,255,255,.06)"/>'
            '<circle cx="22" cy="44" r="1.5" fill="rgba(255,255,255,.1)"/>'
            '</svg>'
        )
        sep_html = (
            f'<div style="display:flex;justify-content:center;gap:6px;margin-bottom:40px">'
            f'<span style="display:block;width:6px;height:6px;border-radius:50%;background:{accent};opacity:.5"></span>'
            f'<span style="display:block;width:8px;height:8px;border-radius:50%;background:{accent}"></span>'
            f'<span style="display:block;width:6px;height:6px;border-radius:50%;background:{accent};opacity:.5"></span>'
            f'</div>'
        )
        return dict(
            css="",
            hero_overlay="linear-gradient(145deg,rgba(0,0,0,.5) 0%,rgba(0,0,0,.1) 100%)",
            hero_pat=f"background-image:url('data:image/svg+xml;base64,{pat}');background-size:48px 48px;",
            sep=sep_html,
            card_sig="",
        )


# ── Pictogram System section ──────────────────────────────────────────────────

def _build_pict_section(
    archetype: str,
    primary: str,
    accent: str,
    neutral: str,
    txt_on_primary: str,
    radius_md: str,
    h_font: str,
    b_font: str,
) -> str:
    """
    Renders the Pictogram System section for the brand charter.
    Shows all 18 pictograms in 3 categories, in 3 color variants.
    Falls back to an empty string if the module is unavailable.
    """
    if not _pictogram_ok or _gen_pictograms is None:
        return ""

    # Generate three color variants using the same stroke rules
    pict_main   = _gen_pictograms(archetype, color=primary)
    pict_inv    = _gen_pictograms(archetype, color=txt_on_primary)   # on primary bg
    pict_accent = _gen_pictograms(archetype, color=accent)

    p = pict_main.params
    param_badge = (
        f"<code style='font-family:monospace;font-size:11px;background:rgba(0,0,0,.06);"
        f"border-radius:4px;padding:2px 8px;color:#555'>"
        f"stroke {p.stroke_width}px &nbsp;·&nbsp; "
        f"linecap: {p.linecap} &nbsp;·&nbsp; "
        f"linejoin: {p.linejoin} &nbsp;·&nbsp; "
        f"corner: {p.corner_radius}px"
        f"</code>"
    )

    def _icon_cell(svg: str, name: str, size: int, display: int) -> str:
        scale = display / size
        label = name.replace("_", " ")
        return (
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:8px">'
            f'<div style="width:{display}px;height:{display}px;display:flex;'
            f'align-items:center;justify-content:center">'
            f'<div style="transform:scale({scale:.2f});transform-origin:center">{svg}</div>'
            f'</div>'
            f'<span style="font-family:monospace;font-size:9px;color:rgba(0,0,0,.35);'
            f'text-transform:uppercase;letter-spacing:.08em">{label}</span>'
            f'</div>'
        )

    def _category_block(title: str, items: dict[str, str], size: int, display: int,
                        bg: str = "#fff", border: str = "#e8e8e8") -> str:
        cells = "".join(
            _icon_cell(svg, name, size, display)
            for name, svg in items.items()
        )
        return (
            f'<div style="margin-bottom:32px">'
            f'<h4 style="font-family:monospace;font-size:10px;letter-spacing:.12em;'
            f'text-transform:uppercase;color:rgba(0,0,0,.35);margin:0 0 16px">{title}</h4>'
            f'<div style="background:{bg};border:1px solid {border};border-radius:{radius_md};'
            f'padding:28px 24px;display:flex;flex-wrap:wrap;gap:28px;align-items:flex-end">'
            f'{cells}</div></div>'
        )

    functional_block  = _category_block(
        "Functional icons — 24 px grid", pict_main.functional,  24, 48)
    feature_block     = _category_block(
        "Feature pictograms — 48 px grid", pict_main.feature,   48, 80)
    markers_block     = _category_block(
        "Visual markers — 16 px grid", pict_main.markers,       16, 32)

    # Color variants strip
    def _variant_row(label: str, pset, bg: str, border: str) -> str:
        icons = {k: v for k, v in list(pset.functional.items())[:6]}
        cells = "".join(_icon_cell(svg, name, 24, 36) for name, svg in icons.items())
        return (
            f'<div style="display:flex;align-items:center;gap:24px;'
            f'background:{bg};border:1px solid {border};'
            f'border-radius:{radius_md};padding:20px 24px;margin-bottom:12px">'
            f'<span style="font-family:monospace;font-size:9px;letter-spacing:.1em;'
            f'text-transform:uppercase;color:rgba(0,0,0,.3);white-space:nowrap;min-width:80px">'
            f'{label}</span>'
            f'<div style="display:flex;flex-wrap:wrap;gap:20px;align-items:center">{cells}</div>'
            f'</div>'
        )

    variants = (
        _variant_row("on light",   pict_main,   "#fff",    "#e8e8e8") +
        _variant_row("on primary", pict_inv,    primary,   "transparent") +
        _variant_row("accent",     pict_accent, "#fff",    "#e8e8e8")
    )

    return f"""
<section style="padding:80px 0;background:{neutral}">
  <div style="max-width:1100px;margin:0 auto;padding:0 40px">
    <div style="font-family:monospace;font-size:10px;letter-spacing:.15em;color:rgba(0,0,0,.3);
                text-transform:uppercase;margin-bottom:32px;padding-bottom:12px;
                border-bottom:1px solid rgba(0,0,0,.06)">Pictogram System</div>

    <div style="display:flex;align-items:baseline;justify-content:space-between;
                flex-wrap:wrap;gap:16px;margin-bottom:40px">
      <h2 style="font-family:'{h_font}',sans-serif;font-size:1.6rem;font-weight:700;
                 color:#111;margin:0">Visual Glyph System</h2>
      {param_badge}
    </div>

    <p style="font-family:'{b_font}',sans-serif;font-size:.9rem;color:rgba(0,0,0,.5);
              max-width:560px;margin:0 0 40px;line-height:1.7">
      Parametric SVG pictograms — no external assets. All strokes, corners and proportions
      are derived from the brand's StyleDNA. Every pictogram follows the same grid,
      the same stroke rules, the same corner language.
    </p>

    {functional_block}
    {feature_block}
    {markers_block}

    <div>
      <h4 style="font-family:monospace;font-size:10px;letter-spacing:.12em;
                 text-transform:uppercase;color:rgba(0,0,0,.35);margin:0 0 16px">
        Color variants</h4>
      {variants}
    </div>

  </div>
</section>"""


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
    """Client-facing visual brand demo — immersive, archetype-specific."""

    # ── Extract tokens ────────────────────────────────────────────────────────
    cs        = (preset or {}).get("color_system", {})
    primary   = cs.get("primary",   {}).get("base",  "#2563eb")
    prim_lt   = cs.get("primary",   {}).get("light", "#93b4f0")
    prim_dk   = cs.get("primary",   {}).get("dark",  "#1a3a6b")
    secondary = cs.get("secondary", {}).get("base",  "#7c3aed")

    pp = getattr(style_dna, "palette_profile", None) if style_dna else None
    accent  = (pp.accent[0]  if pp and pp.accent  else "#f97316")
    neutral = (pp.neutral[0] if pp and pp.neutral else "#f4f5f5")

    h_font = (preset or {}).get("font_family_headings", "system-ui")
    b_font = (preset or {}).get("font_family_body",     "system-ui")
    gf_url = (preset or {}).get("font_google_url",      "")

    gp = getattr(style_dna, "geometry_profile", None) if style_dna else None
    lp = getattr(style_dna, "layout_profile",   None) if style_dna else None

    radius_sm  = "3px"   if gp and gp.border_radius == "none"   else ("4px"  if gp and gp.border_radius == "small" else ("8px" if gp and gp.border_radius == "medium" else "12px"))
    radius_md  = "5px"   if gp and gp.border_radius == "none"   else ("6px"  if gp and gp.border_radius == "small" else ("12px" if gp and gp.border_radius == "medium" else "20px"))
    radius_lg  = "6px"   if gp and gp.border_radius == "none"   else ("8px"  if gp and gp.border_radius == "small" else ("16px" if gp and gp.border_radius == "medium" else "28px"))
    radius_pill= "4px"   if gp and gp.border_radius == "none"   else "100px"

    archetype = (getattr(style_dna, "aesthetic_tags", ["startup_clean"]) or ["startup_clean"])[0]
    tone      = getattr(style_dna, "emotional_tone", "calm")

    txt_on_primary   = text_on(primary)
    txt_on_secondary = text_on(secondary)
    txt_on_accent    = text_on(accent)
    txt_on_neutral   = text_on(neutral)

    # Precomputed RGB tuples (avoid nested f-string issues)
    on_prim_rgb = ','.join(str(int(x)) for x in _parse_color(txt_on_primary))
    on_sec_rgb  = ','.join(str(int(x)) for x in _parse_color(txt_on_secondary))
    on_acc_rgb  = ','.join(str(int(x)) for x in _parse_color(txt_on_accent))
    on_neu_rgb  = ','.join(str(int(x)) for x in _parse_color(txt_on_neutral))
    prim_rgb    = ','.join(str(int(x)) for x in _parse_color(primary))

    # Deterministic image seed (picsum)
    slug = project_name.lower().replace(' ', '-').replace('_', '-')

    # Archetype signature layer
    _sig     = _archetype_signature(archetype, primary, accent, neutral)
    sig_css      = _sig['css']
    sig_overlay  = _sig['hero_overlay']
    sig_hero_pat = _sig['hero_pat']
    sig_sep      = _sig['sep']
    sig_card_sig = _sig['card_sig']

    # Pictogram system section
    pict_section = _build_pict_section(
        archetype=archetype,
        primary=primary,
        accent=accent,
        neutral=neutral,
        txt_on_primary=txt_on_primary,
        radius_md=radius_md,
        h_font=h_font,
        b_font=b_font,
    )

    c = _demo_copy(project_name, brief_text, archetype)
    pn = html_lib.escape(project_name)
    gf_import = f'<link rel="stylesheet" href="{html_lib.escape(gf_url)}">' if gf_url else ""

    # Section label style (small uppercase tag, unobtrusive)
    def demo_label(txt: str) -> str:
        return f'<div style="font-family:monospace;font-size:10px;letter-spacing:.15em;color:rgba(0,0,0,.3);text-transform:uppercase;margin-bottom:32px;padding-bottom:12px;border-bottom:1px solid rgba(0,0,0,.06)">{txt}</div>'

    def demo_label_light(txt: str) -> str:
        return f'<div style="font-family:monospace;font-size:10px;letter-spacing:.15em;color:rgba(255,255,255,.35);text-transform:uppercase;margin-bottom:32px;padding-bottom:12px;border-bottom:1px solid rgba(255,255,255,.1)">{txt}</div>'

    # ── Color contrast helpers ────────────────────────────────────────────────
    def contrast_row(bg: str, label: str, role: str) -> str:
        fg = text_on(bg)
        fg_muted = "rgba(255,255,255,.55)" if fg == "#ffffff" else "rgba(0,0,0,.45)"
        return f"""
<div style="background:{bg};padding:28px 24px;border-radius:{radius_md};flex:1;min-width:160px">
  <div style="font-family:'{h_font}',sans-serif;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:{fg_muted};margin-bottom:8px">{html_lib.escape(role)}</div>
  <div style="font-family:'{h_font}',sans-serif;font-size:1.2rem;font-weight:700;color:{fg};margin-bottom:4px">{html_lib.escape(label)}</div>
  <div style="font-family:'{b_font}',sans-serif;font-size:12px;color:{fg_muted}">{bg}</div>
  <div style="margin-top:16px;display:flex;gap:6px;align-items:center">
    <div style="background:{fg};height:1px;flex:1;opacity:.2"></div>
    <div style="font-size:11px;color:{fg};opacity:.5">Aa</div>
  </div>
</div>"""

    # ── Sections ─────────────────────────────────────────────────────────────

    # 1. Sticky nav (brand colors + hover class)
    nav = f"""
<nav style="position:sticky;top:0;z-index:100;background:{primary};padding:0 40px;
            font-family:'{h_font}',sans-serif;display:flex;align-items:center;
            justify-content:space-between;height:60px;box-shadow:0 1px 3px rgba(0,0,0,.2)">
  <div style="font-size:1rem;font-weight:700;color:{txt_on_primary};letter-spacing:-.01em">{pn}</div>
  <div style="display:flex;gap:28px;font-size:13px">
    <a href="#" class="euk-nav-link" style="color:rgba({on_prim_rgb},.65);text-decoration:none">Product</a>
    <a href="#" class="euk-nav-link" style="color:rgba({on_prim_rgb},.65);text-decoration:none">Docs</a>
    <a href="#" class="euk-nav-link" style="color:rgba({on_prim_rgb},.65);text-decoration:none">Pricing</a>
    <a href="#" class="euk-nav-link" style="color:rgba({on_prim_rgb},.65);text-decoration:none">Blog</a>
  </div>
  <div style="display:flex;gap:10px">
    <a href="#" class="euk-nav-link" style="font-size:13px;color:rgba({on_prim_rgb},.65);text-decoration:none">Sign in</a>
    <a href="#" class="euk-btn euk-btn-primary"
       style="font-size:13px;background:rgba({on_prim_rgb},.15);color:{txt_on_primary};
       padding:6px 16px;border-radius:{radius_pill};text-decoration:none;font-weight:500">{html_lib.escape(c['cta_primary'])}</a>
  </div>
</nav>"""

    # 2. Hero — layered: picsum bg + color overlay + archetype pattern + content
    hero = f"""
<section style="position:relative;overflow:hidden;min-height:520px">
  <div style="position:absolute;inset:0;background-image:url('https://picsum.photos/seed/{slug}/1400/700');background-size:cover;background-position:center"></div>
  <div style="position:absolute;inset:0;background:{primary};opacity:.84"></div>
  <div style="position:absolute;inset:0;{sig_hero_pat}"></div>
  <div style="position:absolute;inset:0;background:{sig_overlay}"></div>
  <div style="position:relative;z-index:1;padding:110px 0 90px">
    <div style="max-width:1100px;margin:0 auto;padding:0 40px">
      {demo_label_light("01 · Hero")}
      <div style="max-width:680px">
        <div style="font-family:'{h_font}',sans-serif;font-size:clamp(2.5rem,5vw,4rem);font-weight:900;
                    color:{txt_on_primary};line-height:1.1;letter-spacing:-.02em;margin-bottom:20px">
          {html_lib.escape(c['tagline'])}
        </div>
        <div style="font-family:'{h_font}',sans-serif;font-size:1.2rem;font-weight:400;
                    color:rgba({on_prim_rgb},.65);line-height:1.6;margin-bottom:36px;max-width:520px">
          {html_lib.escape(c['tagline2'])}
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
          <a href="#" class="euk-btn euk-btn-primary"
             style="display:inline-block;background:{txt_on_primary};color:{primary};
             font-family:'{b_font}',sans-serif;font-size:15px;font-weight:600;
             padding:14px 28px;border-radius:{radius_pill};text-decoration:none">{html_lib.escape(c['cta_primary'])}</a>
          <a href="#" class="euk-btn"
             style="display:inline-block;background:transparent;color:rgba({on_prim_rgb},.85);
             font-family:'{b_font}',sans-serif;font-size:15px;padding:14px 28px;
             border-radius:{radius_pill};text-decoration:none;border:1px solid rgba({on_prim_rgb},.3)">{html_lib.escape(c['cta_secondary'])}</a>
        </div>
      </div>
    </div>
  </div>
</section>"""

    # 3. Color system — immersive large swatches
    _color_strip = "".join(
        f'<div style="flex:1;height:28px;background:{col};border-radius:3px" title="{col}"></div>'
        for col in [prim_dk, primary, prim_lt, neutral, "#ffffff"]
    )
    color_section = f"""
<section style="background:#fff;padding:72px 0">
  <div style="max-width:1100px;margin:0 auto;padding:0 40px">
    {demo_label("02 · Color System")}
    <!-- Immersive large swatches -->
    <div style="display:grid;grid-template-columns:2fr 1fr 1fr;gap:0;border-radius:{radius_lg};overflow:hidden;margin-bottom:16px">
      <div style="background:{primary};height:220px;display:flex;flex-direction:column;justify-content:flex-end;padding:24px;position:relative">
        <div style="position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,.28) 0%,transparent 55%)"></div>
        <div style="position:relative;z-index:1">
          <div style="font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:rgba({on_prim_rgb},.55);font-family:monospace;margin-bottom:4px">Primary</div>
          <div style="font-size:1.15rem;font-weight:700;color:{txt_on_primary};font-family:'{h_font}',sans-serif">{primary}</div>
        </div>
      </div>
      <div style="background:{secondary};height:220px;display:flex;flex-direction:column;justify-content:flex-end;padding:20px;position:relative">
        <div style="position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,.25) 0%,transparent 55%)"></div>
        <div style="position:relative;z-index:1">
          <div style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:rgba({on_sec_rgb},.55);font-family:monospace;margin-bottom:4px">Secondary</div>
          <div style="font-size:.9rem;font-weight:600;color:{txt_on_secondary};font-family:'{h_font}',sans-serif">{secondary}</div>
        </div>
      </div>
      <div style="background:{accent};height:220px;display:flex;flex-direction:column;justify-content:flex-end;padding:20px;position:relative">
        <div style="position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,.25) 0%,transparent 55%)"></div>
        <div style="position:relative;z-index:1">
          <div style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:rgba({on_acc_rgb},.55);font-family:monospace;margin-bottom:4px">Accent</div>
          <div style="font-size:.9rem;font-weight:600;color:{txt_on_accent};font-family:'{h_font}',sans-serif">{accent}</div>
        </div>
      </div>
    </div>
    <!-- Scale strip -->
    <div style="display:flex;gap:4px;margin-bottom:24px">{_color_strip}</div>
    <!-- Contrast previews -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="border:1px solid #e5e5e5;border-radius:{radius_lg};padding:24px;background:#fafafa">
        <div style="font-family:'{h_font}',sans-serif;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#999;margin-bottom:12px">Text on primary</div>
        <div style="background:{primary};padding:20px;border-radius:{radius_sm}">
          <div style="font-family:'{h_font}',sans-serif;font-size:1.1rem;font-weight:700;color:{txt_on_primary};margin-bottom:4px">Heading reads clearly</div>
          <div style="font-family:'{b_font}',sans-serif;font-size:13px;color:rgba({on_prim_rgb},.65)">Body text at reduced opacity for hierarchy</div>
        </div>
      </div>
      <div style="border:1px solid #e5e5e5;border-radius:{radius_lg};padding:24px;background:#fafafa">
        <div style="font-family:'{h_font}',sans-serif;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#999;margin-bottom:12px">Text on surface</div>
        <div style="background:{neutral};padding:20px;border-radius:{radius_sm}">
          <div style="font-family:'{h_font}',sans-serif;font-size:1.1rem;font-weight:700;color:{txt_on_neutral};margin-bottom:4px">Heading reads clearly</div>
          <div style="font-family:'{b_font}',sans-serif;font-size:13px;color:rgba({on_neu_rgb},.6)">Body text at reduced opacity for hierarchy</div>
        </div>
      </div>
    </div>
  </div>
</section>"""

    # 4. Typography
    typo_section = f"""
<section style="background:#f8f8f8;padding:72px 0;border-top:1px solid #eee;border-bottom:1px solid #eee">
  <div style="max-width:1100px;margin:0 auto;padding:0 40px">
    {demo_label("03 · Typography")}
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:start">
      <div>
        <div style="font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#aaa;margin-bottom:20px;font-family:monospace">Display · {html_lib.escape(h_font)}</div>
        <div style="font-family:'{h_font}',sans-serif;font-size:3rem;font-weight:900;line-height:1.05;color:#0a0a0a;letter-spacing:-.02em;margin-bottom:12px">{html_lib.escape(c['tagline3'])}</div>
        <div style="font-family:'{h_font}',sans-serif;font-size:1.75rem;font-weight:700;line-height:1.2;color:#111;margin-bottom:8px">Section heading, clear hierarchy</div>
        <div style="font-family:'{h_font}',sans-serif;font-size:1.25rem;font-weight:600;line-height:1.3;color:#222;margin-bottom:8px">Subsection or card title</div>
        <div style="font-family:'{h_font}',sans-serif;font-size:1rem;font-weight:500;line-height:1.4;color:#333;margin-bottom:6px">Label or navigation item</div>
        <div style="font-family:monospace;font-size:11px;color:#aaa;letter-spacing:.08em;text-transform:uppercase">CAPTION · UI LABEL · METADATA</div>
      </div>
      <div>
        <div style="font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#aaa;margin-bottom:20px;font-family:monospace">Body · {html_lib.escape(b_font)}</div>
        <div style="font-family:'{b_font}',sans-serif;font-size:1.05rem;line-height:1.7;color:#333;margin-bottom:20px">{html_lib.escape(c['body'])}</div>
        <div style="font-family:'{b_font}',sans-serif;font-size:.9rem;line-height:1.65;color:#555;margin-bottom:16px">Secondary body at smaller size. Used for supporting content, footnotes, and instructional text that accompanies primary content.</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px">
          <span style="background:{primary};color:{txt_on_primary};font-family:'{b_font}',sans-serif;font-size:11px;font-weight:600;padding:4px 10px;border-radius:{radius_pill};letter-spacing:.02em">Primary tag</span>
          <span style="background:#f0f0f0;color:#444;font-family:'{b_font}',sans-serif;font-size:11px;padding:4px 10px;border-radius:{radius_pill}">Neutral tag</span>
          <span style="border:1px solid {primary};color:{primary};font-family:'{b_font}',sans-serif;font-size:11px;padding:4px 10px;border-radius:{radius_pill}">Outlined</span>
        </div>
      </div>
    </div>
  </div>
</section>"""

    # 5. UI Components
    ui_section = f"""
<section style="background:#fff;padding:72px 0">
  <div style="max-width:1100px;margin:0 auto;padding:0 40px">
    {demo_label("04 · UI Components")}

    <!-- Buttons — with micro-interaction class -->
    <div style="margin-bottom:48px">
      <div style="font-size:11px;letter-spacing:.08em;color:#999;text-transform:uppercase;margin-bottom:16px;font-family:monospace">Buttons</div>
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
        <button class="euk-btn euk-btn-primary" style="background:{primary};color:{txt_on_primary};font-family:'{b_font}',sans-serif;font-size:14px;font-weight:600;padding:12px 24px;border-radius:{radius_pill};border:none;cursor:pointer">{html_lib.escape(c['cta_primary'])}</button>
        <button class="euk-btn" style="background:transparent;color:{primary};font-family:'{b_font}',sans-serif;font-size:14px;font-weight:500;padding:11px 24px;border-radius:{radius_pill};border:1.5px solid {primary};cursor:pointer">{html_lib.escape(c['cta_secondary'])}</button>
        <button class="euk-btn" style="background:#f5f5f5;color:#333;font-family:'{b_font}',sans-serif;font-size:14px;padding:12px 24px;border-radius:{radius_pill};border:none;cursor:pointer">Cancel</button>
        <button class="euk-btn" style="background:transparent;color:{primary};font-family:'{b_font}',sans-serif;font-size:14px;text-decoration:underline;border:none;cursor:pointer;padding:12px 4px">Learn more →</button>
        <button style="background:#f0f0f0;color:#aaa;font-family:'{b_font}',sans-serif;font-size:14px;padding:12px 24px;border-radius:{radius_pill};border:none;cursor:not-allowed" disabled>Disabled</button>
      </div>
    </div>

    <!-- Cards — with hover lift class + archetype sig -->
    <div style="margin-bottom:48px">
      <div style="font-size:11px;letter-spacing:.08em;color:#999;text-transform:uppercase;margin-bottom:16px;font-family:monospace">Cards</div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">
        <div class="euk-card" style="border:1px solid #e5e5e5;border-radius:{radius_lg};padding:28px;background:#fff;{sig_card_sig}">
          <div style="width:36px;height:36px;background:{primary};border-radius:{radius_sm};margin-bottom:16px"></div>
          <div style="font-family:'{h_font}',sans-serif;font-size:1rem;font-weight:700;color:#0a0a0a;margin-bottom:8px">{html_lib.escape(c['features'][0][0])}</div>
          <div style="font-family:'{b_font}',sans-serif;font-size:13px;color:#666;line-height:1.6">{html_lib.escape(c['features'][0][1])}</div>
        </div>
        <div class="euk-card" style="border-radius:{radius_lg};padding:28px;background:{primary}">
          <div style="width:36px;height:36px;background:rgba({on_prim_rgb},.15);border-radius:{radius_sm};margin-bottom:16px"></div>
          <div style="font-family:'{h_font}',sans-serif;font-size:1rem;font-weight:700;color:{txt_on_primary};margin-bottom:8px">{html_lib.escape(c['features'][1][0])}</div>
          <div style="font-family:'{b_font}',sans-serif;font-size:13px;color:rgba({on_prim_rgb},.65);line-height:1.6">{html_lib.escape(c['features'][1][1])}</div>
        </div>
        <div class="euk-card" style="border-radius:{radius_lg};padding:28px;background:#f8f8f8">
          <div style="width:36px;height:36px;background:#e5e5e5;border-radius:{radius_sm};margin-bottom:16px"></div>
          <div style="font-family:'{h_font}',sans-serif;font-size:1rem;font-weight:700;color:#0a0a0a;margin-bottom:8px">{html_lib.escape(c['features'][2][0])}</div>
          <div style="font-family:'{b_font}',sans-serif;font-size:13px;color:#666;line-height:1.6">{html_lib.escape(c['features'][2][1])}</div>
        </div>
      </div>
    </div>

    <!-- Form -->
    <div style="margin-bottom:48px">
      <div style="font-size:11px;letter-spacing:.08em;color:#999;text-transform:uppercase;margin-bottom:16px;font-family:monospace">Form elements</div>
      <div style="max-width:480px;display:flex;flex-direction:column;gap:16px">
        <div>
          <label style="display:block;font-family:'{b_font}',sans-serif;font-size:13px;font-weight:500;color:#333;margin-bottom:6px">Email address</label>
          <input type="email" placeholder="you@company.com" style="width:100%;padding:10px 14px;font-family:'{b_font}',sans-serif;font-size:14px;border:1.5px solid #ddd;border-radius:{radius_md};outline:none;color:#111;background:#fff">
        </div>
        <div>
          <label style="display:block;font-family:'{b_font}',sans-serif;font-size:13px;font-weight:500;color:#333;margin-bottom:6px">Team name</label>
          <input type="text" placeholder="Acme Corp" style="width:100%;padding:10px 14px;font-family:'{b_font}',sans-serif;font-size:14px;border:1.5px solid {primary};border-radius:{radius_md};outline:none;color:#111;background:#fff;box-shadow:0 0 0 3px rgba({prim_rgb},.08)">
          <div style="font-size:11px;color:#888;margin-top:5px;font-family:'{b_font}',sans-serif">Focused state — border uses primary color</div>
        </div>
        <button class="euk-btn euk-btn-primary" style="background:{primary};color:{txt_on_primary};font-family:'{b_font}',sans-serif;font-size:14px;font-weight:600;padding:12px;border-radius:{radius_md};border:none;cursor:pointer;width:100%">{html_lib.escape(c['cta_primary'])}</button>
      </div>
    </div>

    <!-- Stats row -->
    <div>
      <div style="font-size:11px;letter-spacing:.08em;color:#999;text-transform:uppercase;margin-bottom:16px;font-family:monospace">Stats / KPI blocks</div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#e5e5e5;border-radius:{radius_lg};overflow:hidden">
        {"".join(f'<div style="background:#fff;padding:28px 24px"><div style="font-family:\'{h_font}\',sans-serif;font-size:2rem;font-weight:900;color:{primary};letter-spacing:-.02em;margin-bottom:4px">{html_lib.escape(v)}</div><div style="font-family:\'{b_font}\',sans-serif;font-size:13px;color:#888">{html_lib.escape(l)}</div></div>' for v,l in c['stats'])}
      </div>
    </div>

  </div>
</section>"""

    # 6. Features grid
    features_section = f"""
<section style="background:#f8f8f8;padding:80px 0;border-top:1px solid #eee">
  <div style="max-width:1100px;margin:0 auto;padding:0 40px">
    {demo_label("05 · Feature Section")}
    <div style="text-align:center;max-width:560px;margin:0 auto 56px">
      <div style="font-family:'{h_font}',sans-serif;font-size:2.25rem;font-weight:800;color:#0a0a0a;line-height:1.15;letter-spacing:-.015em;margin-bottom:16px">{html_lib.escape(c['tagline2'])}</div>
      <div style="font-family:'{b_font}',sans-serif;font-size:1rem;color:#666;line-height:1.65">Everything your team needs to move fast without breaking things.</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:2px;background:#e0e0e0;border-radius:{radius_lg};overflow:hidden">
      {"".join(f'<div class="euk-card" style="background:#fff;padding:40px;{sig_card_sig}"><div style="width:40px;height:4px;background:{primary};margin-bottom:20px;border-radius:2px"></div><div style="font-family:\'{h_font}\',sans-serif;font-size:1.15rem;font-weight:700;color:#0a0a0a;margin-bottom:10px">{html_lib.escape(feat[0])}</div><div style="font-family:\'{b_font}\',sans-serif;font-size:14px;color:#666;line-height:1.65">{html_lib.escape(feat[1])}</div></div>' for feat in c['features'])}
    </div>
  </div>
</section>"""

    # 7. Split section — real picsum image
    split_section = f"""
<section style="background:#fff;padding:80px 0">
  <div style="max-width:1100px;margin:0 auto;padding:0 40px">
    {demo_label("06 · Split Section")}
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:64px;align-items:center">
      <div>
        <div style="font-family:monospace;font-size:10px;letter-spacing:.12em;color:{primary};text-transform:uppercase;margin-bottom:12px">Why it matters</div>
        <div style="font-family:'{h_font}',sans-serif;font-size:2rem;font-weight:800;color:#0a0a0a;line-height:1.15;letter-spacing:-.01em;margin-bottom:20px">{html_lib.escape(c['features'][3][0] if len(c['features'])>3 else "Built for what comes next")}</div>
        <div style="font-family:'{b_font}',sans-serif;font-size:1rem;color:#555;line-height:1.7;margin-bottom:28px">{html_lib.escape(c['body'])}</div>
        <a href="#" class="euk-btn" style="display:inline-flex;align-items:center;gap:8px;font-family:'{b_font}',sans-serif;font-size:14px;font-weight:600;color:{primary};text-decoration:none">{html_lib.escape(c['cta_secondary'])} <span>→</span></a>
      </div>
      <div style="border-radius:{radius_lg};height:420px;overflow:hidden;position:relative">
        <img src="https://picsum.photos/seed/{slug}2/800/600" alt="Visual illustration"
             style="width:100%;height:100%;object-fit:cover;display:block">
        <div style="position:absolute;inset:0;background:{primary};opacity:.1;pointer-events:none"></div>
      </div>
    </div>
  </div>
</section>"""

    # 8. Testimonial — with archetype pattern overlay
    testimonial_section = f"""
<section style="background:{primary};padding:80px 0;position:relative;overflow:hidden">
  <div style="position:absolute;inset:0;{sig_hero_pat}opacity:.35;pointer-events:none"></div>
  <div style="position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:0 40px">
    {demo_label_light("07 · Testimonial")}
    <div style="max-width:680px;margin:0 auto;text-align:center">
      <div style="font-family:'{h_font}',sans-serif;font-size:1.75rem;font-weight:700;
                  color:{txt_on_primary};line-height:1.4;letter-spacing:-.01em;margin-bottom:28px">
        &ldquo;{c['quote']}&rdquo;
      </div>
      <div style="display:flex;align-items:center;justify-content:center;gap:12px">
        <div style="width:36px;height:36px;background:rgba({on_prim_rgb},.2);border-radius:50%"></div>
        <div style="font-family:'{b_font}',sans-serif;font-size:13px;color:rgba({on_prim_rgb},.65)">{c['quote_author']}</div>
      </div>
    </div>
  </div>
</section>"""

    # 9. Style properties visualized
    style_viz = f"""
<section style="background:#fafafa;padding:72px 0;border-top:1px solid #eee">
  <div style="max-width:1100px;margin:0 auto;padding:0 40px">
    {demo_label("08 · Style Properties")}
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:40px">

      <!-- Radius -->
      <div>
        <div style="font-size:11px;letter-spacing:.08em;color:#aaa;text-transform:uppercase;margin-bottom:20px;font-family:monospace">Border Radius</div>
        <div style="display:flex;flex-direction:column;gap:12px">
          {"".join(f"""<div style="display:flex;align-items:center;gap:16px">
            <div style="width:64px;height:32px;background:{primary};border-radius:{r};flex-shrink:0"></div>
            <div style="font-family:monospace;font-size:11px;color:#999">{lbl} — {r}</div>
          </div>""" for r, lbl in [("0px","none"),  (radius_sm,"sm"), (radius_md,"md"), (radius_lg,"lg"), (radius_pill,"pill")])}
        </div>
      </div>

      <!-- Shadows -->
      <div>
        <div style="font-size:11px;letter-spacing:.08em;color:#aaa;text-transform:uppercase;margin-bottom:20px;font-family:monospace">Shadows</div>
        <div style="display:flex;flex-direction:column;gap:16px">
          {"".join(f"""<div style="display:flex;align-items:center;gap:16px">
            <div style="width:64px;height:32px;background:#fff;border-radius:{radius_md};border:1px solid #f0f0f0;box-shadow:{shad};flex-shrink:0"></div>
            <div style="font-family:monospace;font-size:11px;color:#999">{lbl}</div>
          </div>""" for shad, lbl in [("0 1px 2px rgba(0,0,0,.06)","sm"), ("0 4px 8px rgba(0,0,0,.1)","md"), ("0 10px 24px rgba(0,0,0,.12)","lg"), ("0 20px 40px rgba(0,0,0,.15)","xl")])}
        </div>
      </div>

      <!-- Spacing -->
      <div>
        <div style="font-size:11px;letter-spacing:.08em;color:#aaa;text-transform:uppercase;margin-bottom:20px;font-family:monospace">Spacing</div>
        <div style="display:flex;flex-direction:column;gap:10px">
          {"".join(f"""<div style="display:flex;align-items:center;gap:16px">
            <div style="height:16px;width:{px};background:{primary};opacity:.7;border-radius:2px;flex-shrink:0"></div>
            <div style="font-family:monospace;font-size:11px;color:#999">{lbl} — {px}</div>
          </div>""" for px, lbl in [("4px","xs"), ("8px","sm"), ("16px","md"), ("24px","lg"), ("32px","xl"), ("48px","2xl"), ("64px","3xl")])}
        </div>
      </div>

    </div>
  </div>
</section>"""

    # 10. CTA
    cta_section = f"""
<section style="background:#fff;padding:80px 0;border-top:1px solid #eee">
  <div style="max-width:1100px;margin:0 auto;padding:0 40px;text-align:center">
    {demo_label("09 · CTA Section")}
    {sig_sep}
    <div style="font-family:'{h_font}',sans-serif;font-size:2.5rem;font-weight:900;color:#0a0a0a;
                line-height:1.1;letter-spacing:-.02em;margin-bottom:16px;max-width:560px;margin-inline:auto">
      Ready to get started?
    </div>
    <div style="font-family:'{b_font}',sans-serif;font-size:1.05rem;color:#666;margin-bottom:36px;max-width:440px;margin-inline:auto">
      Join thousands of teams who already trust {pn} to deliver.
    </div>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
      <a href="#" class="euk-btn euk-btn-primary" style="display:inline-block;background:{primary};color:{txt_on_primary};font-family:'{b_font}',sans-serif;font-size:15px;font-weight:600;padding:14px 32px;border-radius:{radius_pill};text-decoration:none">{html_lib.escape(c['cta_primary'])}</a>
      <a href="#" class="euk-btn" style="display:inline-block;background:#f5f5f5;color:#333;font-family:'{b_font}',sans-serif;font-size:15px;padding:14px 32px;border-radius:{radius_pill};text-decoration:none">{html_lib.escape(c['cta_secondary'])}</a>
    </div>
  </div>
</section>"""

    # 11. Collapsible technical data
    tech_data = f"""
<section style="background:#f4f4f4;padding:48px 0;border-top:2px solid #e5e5e5">
  <div style="max-width:1100px;margin:0 auto;padding:0 40px">
    <div style="font-family:monospace;font-size:10px;letter-spacing:.15em;color:#aaa;text-transform:uppercase;margin-bottom:24px">Technical reference</div>
    <details style="border:1px solid #e0e0e0;border-radius:6px;margin-bottom:12px;background:#fff">
      <summary style="padding:14px 20px;cursor:pointer;font-family:monospace;font-size:12px;font-weight:600;color:#555;user-select:none;list-style:none">▶ &nbsp;Design Tokens (CSS variables)</summary>
      <div style="padding:0 20px 20px">{render_tokens(css, preset)}</div>
    </details>
    <details style="border:1px solid #e0e0e0;border-radius:6px;background:#fff">
      <summary style="padding:14px 20px;cursor:pointer;font-family:monospace;font-size:12px;font-weight:600;color:#555;user-select:none;list-style:none">▶ &nbsp;Raw JSON data</summary>
      <div style="padding:0 20px 20px">{render_raw_json(style_dna, palette_output, preset)}</div>
    </details>
  </div>
</section>"""

    # Footer
    footer = f"""
<footer style="background:{primary};padding:32px 40px">
  <div style="max-width:1100px;margin:0 auto;display:flex;justify-content:space-between;align-items:center">
    <div style="font-family:'{h_font}',sans-serif;font-size:.9rem;font-weight:700;color:{txt_on_primary}">{pn}</div>
    <div style="font-family:monospace;font-size:10px;color:rgba({on_prim_rgb},.4);letter-spacing:.08em">BRAND PREVIEW · EURKAI · {datetime.now().strftime("%Y-%m-%d")}</div>
  </div>
</footer>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{pn} — Brand Preview</title>
  {gf_import}
  <style>
    :root {{
      --c-primary:   {primary};
      --c-secondary: {secondary};
      --c-accent:    {accent};
      --c-neutral:   {neutral};
      --f-heading:   '{h_font}', sans-serif;
      --f-body:      '{b_font}', sans-serif;
      --r-sm:   {radius_sm};
      --r-md:   {radius_md};
      --r-lg:   {radius_lg};
      --r-pill: {radius_pill};
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}
    body {{ background: #f2f2f2; -webkit-font-smoothing: antialiased; }}
    img {{ max-width: 100%; }}

    /* ── Micro-interactions ─────────────────────────────────── */
    .euk-btn {{
      display: inline-block;
      text-decoration: none;
      cursor: pointer;
      transition: transform .18s ease, box-shadow .18s ease;
      will-change: transform;
    }}
    .euk-btn:hover  {{ transform: translateY(-2px); }}
    .euk-btn:active {{ transform: translateY(0) !important; box-shadow: none !important; }}
    .euk-btn-primary:hover {{ box-shadow: 0 8px 24px rgba(0,0,0,.18); }}

    .euk-card {{
      transition: transform .22s ease, box-shadow .22s ease;
    }}
    .euk-card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 12px 32px rgba(0,0,0,.1);
    }}

    .euk-nav-link {{ transition: opacity .15s; }}
    .euk-nav-link:hover {{ opacity: 1 !important; }}

    /* ── Archetype signature ────────────────────────────────── */
    {sig_css}

    /* ── Tech ref ───────────────────────────────────────────── */
    .tokens-table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    .tokens-table th {{ text-align:left;padding:6px 10px;background:#f9f9f9;color:#666;font-size:10px;text-transform:uppercase;border-bottom:1px solid #eee; }}
    .tokens-table td {{ padding:5px 10px;border-bottom:1px solid #f5f5f5;color:#333; }}
    .tokens-table td:first-child {{ font-family:monospace;color:#555; }}
    .tokens-table td .color-dot {{ display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:6px;vertical-align:middle;border:1px solid rgba(0,0,0,.1); }}
    .token-section-header {{ background:#f4f4f4; }}
    .token-section-header td {{ font-size:10px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:.05em;padding:8px 10px; }}
    details summary::-webkit-details-marker {{ display:none; }}
    pre.json-block {{ background:#1e1e1e;color:#d4d4d4;font-family:monospace;font-size:11px;padding:16px 20px;overflow-x:auto;border-radius:0 0 6px 6px;line-height:1.5;max-height:400px;overflow-y:auto; }}
    details {{ margin-bottom:8px; }}
  </style>
</head>
<body>
{nav}
{hero}
{color_section}
{typo_section}
{ui_section}
{features_section}
{split_section}
{testimonial_section}
{pict_section}
{style_viz}
{cta_section}
{tech_data}
{footer}
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
    """Return (section_bg_css, accent_strip_html, section_fg, sec_bg_hex) for a section.
    section_fg and sec_bg_hex are always contrast-checked against the actual section background.
    Use sec_bg_hex to derive section-local secondary colors with _enforce_contrast()."""
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

    def _safe(text, solid_bg):
        return _enforce_contrast(text, solid_bg, 4.5)

    if opts == "accent_bg":
        # fond très légèrement teinté — fond effectif ≈ bg
        return f"background:{p}12;border-top:1px solid {p}33", "", _safe(fg, bg), bg
    elif opts == "full_color":
        txt = _safe(rc["inv"], p)
        return f"background:{p}", f'<div style="height:3px;background:{s}"></div>', txt, p
    elif opts == "alt_bg":
        return f"background:{bg2}", "", _safe(fg, bg2), bg2
    elif opts == "stripe_top":
        return f"background:{bg}", f'<div style="height:3px;background:{p}"></div>', _safe(fg, bg), bg
    elif opts == "stark_border":
        return f"background:{bg};border-top:4px solid {fg}", "", _safe(fg, bg), bg
    elif opts == "hairline":
        return f"background:{bg};border-top:1px solid {bdr}", "", _safe(fg, bg), bg
    elif opts == "grid_bg":
        return (f"background-color:{bg};"
                f"background-image:repeating-linear-gradient(90deg,{p}0d 0,{p}0d 1px,transparent 1px,transparent 48px),"
                f"repeating-linear-gradient(0deg,{p}0d 0,{p}0d 1px,transparent 1px,transparent 48px)"), "", _safe(fg, bg), bg
    else:
        return f"background:{bg}", "", _safe(fg, bg), bg


def _sec_colors(rc, sec_bg):
    """Dérive les couleurs section-locales, toutes contrastées contre sec_bg.
    Utiliser ces valeurs à la place de rc['fg2'], rc['p'], etc. dans les HTML de sections.
    Pour h3_css/label_css (couleur baked-in), ajouter ;color:{sc['fg']} après en CSS cascade."""
    return {
        "fg":  _enforce_contrast(rc["fg"],  sec_bg, 4.5),
        "fg2": _enforce_contrast(rc["fg2"], sec_bg, 3.0),
        "p":   _enforce_contrast(rc["p"],   sec_bg, 4.5),
        "s":   _enforce_contrast(rc["s"],   sec_bg, 4.5),
        "acc": _enforce_contrast(rc["acc"], sec_bg, 4.5),
        "bdr": _enforce_contrast(rc["bdr"], sec_bg, 1.5),
    }


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
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)
    lbl  = _cp("label", rc, rng)
    n    = rng.choice([4,6])  # vary item count

    # Pictogrammes SVG (pictogram_system) si disponibles, sinon fallback unicode
    _pict_set = rc.get("pictograms")
    if _pict_set is not None:
        _svg_pool = list((_pict_set.functional or {}).values()) + list((_pict_set.feature or {}).values())
        _use_svg  = bool(_svg_pool)
    else:
        _use_svg  = False
        _svg_pool = []

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
        def _icon_html(i, fallback_unicode):
            if _use_svg and _svg_pool:
                svg = _svg_pool[i % len(_svg_pool)]
                ic  = rng.choice([sc["p"], sc["s"], sc["acc"]])
                # Coloriser le SVG en remplaçant stroke/fill courant
                svg_colored = svg.replace('currentColor', ic).replace('stroke="#000"', f'stroke="{ic}"')
                return f'<div style="width:40px;height:40px;margin-bottom:14px">{svg_colored}</div>'
            return f'<div style="font-size:1.4rem;color:{rng.choice([sc["p"],sc["s"],sc["acc"]])};margin-bottom:12px">{fallback_unicode}</div>'

        cards_html = "".join(
            f'<div style="padding:28px 0;border-top:1px solid {sc["bdr"]}">'
            f'{_icon_html(i, icon)}'
            f'<h3 style="{rc["h3_css"]};color:{sfg};margin-bottom:8px">{t}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]};line-height:1.7">{d}</p>'
            f'</div>'
            for i,(icon,t,d) in enumerate(items)
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
            f'<div style="display:flex;gap:32px;align-items:baseline;padding:24px 0;border-bottom:1px solid {sc["bdr"]}">'
            f'<span style="{rc["label_css"]};color:{sc["p"]};min-width:32px">{n:02d}</span>'
            f'<h3 style="{rc["h3_css"]};color:{sfg};flex:1">{t}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]};max-width:300px;text-align:right;line-height:1.7">{d}</p>'
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
            f'<div style="display:grid;grid-template-columns:120px 1fr;gap:24px;padding:32px 0;border-bottom:1px solid {sc["bdr"]}">'
            f'<div style="font-family:\'{rc["hf"]}\',serif;font-size:4rem;font-weight:900;color:{sc["p"]}44;line-height:1">{n:02d}</div>'
            f'<div><h3 style="{rc["h3_css"]};color:{sfg};margin-bottom:8px">{t}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]};line-height:1.7">{d}</p></div>'
            f'</div>'
            for n,t,d,_ in items
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">{rows_html}</div></section>'
        )

    else:
        # Scattered cards with color accents
        border_colors = [sc["p"], sc["s"], sc["acc"], sc["p"], sc["s"], sc["acc"]]
        items = [(kw[i%len(kw)].capitalize(), _cp("body", rc, rng, i), border_colors[i%6]) for i in range(n)]
        cards_html = "".join(
            f'<div style="padding:24px;border-left:3px solid {col};background:{col}18">'
            f'<h3 style="{rc["h3_css"]};color:{sfg};margin-bottom:8px">{t}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]};line-height:1.7">{d}</p>'
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
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)
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
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;padding:28px 0;border-bottom:1px solid {sc["bdr"]}">'
            f'<span style="{rc["label_css"]};color:{sc["p"]}">{i+1:02d}</span>'
            f'<h3 style="{rc["h2_css"]};color:{sfg};font-size:clamp(1.4rem,3vw,2rem);flex:1;text-align:center">{vals[i].capitalize()}</h3>'
            f'<span style="{rc["body_css"]};font-size:11px;color:{sc["fg2"]};max-width:180px;text-align:right">{rng.choice(desc_pool)}</span>'
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
        # Colored cards grid — fond de chaque carte = couleur brand, inv est toujours correct
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
            f'<div style="display:flex;gap:24px;align-items:center;padding:20px 0;border-bottom:1px solid {sc["bdr"]}">'
            f'<div style="width:3px;height:40px;background:{rng.choice([sc["p"],sc["s"],sc["acc"]])};flex-shrink:0"></div>'
            f'<div style="font-family:\'{rc["hf"]}\',serif;font-size:clamp(2rem,5vw,3.5rem);font-weight:700;color:{sfg};letter-spacing:-.03em;line-height:1">{vals[i].capitalize()}</div>'
            f'<span style="{rc["body_css"]};font-size:10px;color:{sc["fg2"]};margin-left:auto;text-align:right;max-width:140px">{rng.choice(desc_pool)}</span>'
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
            f'<div style="padding:16px 0;border-bottom:1px solid {sc["bdr"]}">'
            f'<span style="{rc["label_css"]};color:{rng.choice([sc["p"],sc["s"],sc["acc"]])}">{vals[i].capitalize()}</span>'
            f'</div>'
            for i in range(n_vals)
        )
        stmt = _cp("h_sec", rc, rng, 0)
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center">'
            f'<div>{rc["section_label"](lbl)}<div style="margin-top:24px">{list_html}</div></div>'
            f'<div style="{rc["h2_css"]};color:{sfg};line-height:1.1;white-space:pre-line">{stmt}</div>'
            f'</div></div></section>'
        )


def _sec_manifesto(rc):
    rng  = rc["_rng"]
    vals = rc["vals"] or ["authenticité","rigueur","vision","engagement"]
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)
    att  = rc["ad"]["attitude"]
    n_lines = rng.choice([3,4,5])
    lines = [_cp("manifesto_line", rc, rng, i) for i in range(n_lines)]

    variant = rng.randint(0, 3)

    if variant == 0:
        # Numbered manifesto with dividers
        rows = "".join(
            f'<div style="padding:24px 0;border-bottom:1px solid {sc["bdr"]};display:flex;gap:36px;align-items:baseline">'
            f'<span style="{rc["label_css"]};color:{sc["p"]}">{i+1:02d}.</span>'
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
            f'font-weight:{rng.choice(["300","700"])};color:{rng.choice([sfg,sc["p"],sc["s"]])};'
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
            f'border-bottom:1px solid {sc["bdr"]};line-height:1.6">{line}</p>'
            for line in lines
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:start">'
            f'<div style="{rc["h2_css"]};color:{sfg};line-height:1.1;white-space:pre-line;position:sticky;top:80px">{lbl}</div>'
            f'<div>{lines_html}</div>'
            f'</div></div></section>'
        )

    else:
        # Full-width typographic wall
        bg_override = f"background:{p}" if att=="brutalist" else bg_css
        txt_color   = rc["inv"] if att=="brutalist" else sfg
        sc_wall = _sec_colors(rc, p) if att=="brutalist" else sc
        wall = " ".join(
            f'<span style="font-family:\'{rc["hf"]}\';font-size:clamp(1.2rem,3vw,2rem);'
            f'font-weight:{rng.choice(["900","300","700"])};'
            f'color:{rng.choice([txt_color,sc_wall["s"],sc_wall["acc"]])};'
            f'opacity:{rng.choice([1,0.6,0.8,0.4,1])};margin:0 12px">{line}</span>'
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
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    # Couleurs section-aware : toujours contrastées contre le fond réel de la section
    sfg2   = _enforce_contrast(fg2, sec_bg, 3.0)
    sec_p  = _enforce_contrast(p,   sec_bg, 4.5)
    sec_s  = _enforce_contrast(s,   sec_bg, 4.5)
    sec_acc= _enforce_contrast(acc, sec_bg, 4.5)
    sec_bdr= _enforce_contrast(rc["bdr"], sec_bg, 1.5)  # juste visible
    n_stats = rng.choice([3,4])
    stats = [(_cp("stat_n", rc, rng, i), _cp("stat_l", rc, rng, i)) for i in range(n_stats)]

    variant = rng.randint(0, 3)

    # Palette cyclique stats contrastée contre le fond de section
    _stat_colors = [sec_acc, sec_p, sec_s, sec_p]

    if variant == 0:
        # Horizontal grid
        items = "".join(
            f'<div style="text-align:center;padding:0 24px;{("border-left:1px solid "+sec_bdr) if i>0 else ""}">'
            f'<div style="font-family:\'{rc["hf"]}\',serif;font-size:clamp(3rem,7vw,5rem);font-weight:900;color:{_stat_colors[i%4]};line-height:1;letter-spacing:-.04em">{n}</div>'
            f'<div style="{rc["label_css"]};font-size:8px;margin-top:8px;color:{sfg2}">{l}</div>'
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
            f'<div style="display:flex;align-items:baseline;gap:32px;padding:24px 0;border-bottom:1px solid {sec_bdr}">'
            f'<div style="{rc["label_css"]};min-width:160px;color:{sfg2}">{l}</div>'
            f'<div style="font-family:\'{rc["hf"]}\';font-size:clamp(2rem,5vw,4rem);font-weight:900;color:{_stat_colors[i%4]};letter-spacing:-.04em">{n}</div>'
            f'</div>'
            for i,(n,l) in enumerate(stats)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">{items}</div></section>'
        )

    elif variant == 2:
        # Colored blocks — chaque bloc a sa propre couleur de fond, inv est correct
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
            f'<div style="font-family:\'{rc["hf"]}\';font-size:2rem;font-weight:900;color:{_stat_colors[(i+1)%4]}">{n}</div>'
            f'<div style="{rc["label_css"]};font-size:8px;color:{sfg2};margin-top:4px">{l}</div>'
            f'</div>'
            for i,(n,l) in enumerate(stats[1:])
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="font-family:\'{rc["hf"]}\';font-size:clamp(6rem,16vw,14rem);font-weight:900;color:{sec_acc};line-height:.85;letter-spacing:-.06em;margin-bottom:40px">{main_n}</div>'
            f'<div style="{rc["body_css"]};font-size:11px;color:{sfg2};text-transform:uppercase;letter-spacing:.2em;margin-bottom:48px">{main_l}</div>'
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
        bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng, "alt_bg")
        sc = _sec_colors(rc, sec_bg)
        return (
            f'<section style="padding:{sp} 48px;{bg_css}">{strip}'
            f'<div style="max-width:720px;margin:0 auto;text-align:center">'
            f'<div style="font-size:4rem;color:{sc["p"]};line-height:1;margin-bottom:-16px;font-family:\'{rc["hf"]}\'">"</div>'
            f'<p style="font-family:\'{rc["hf"]}\',Georgia,serif;font-size:clamp(1.3rem,3vw,2rem);font-style:italic;font-weight:300;color:{sfg};line-height:1.5;margin-bottom:24px">{quote[2:-2]}</p>'
            f'<div style="{rc["label_css"]};color:{sc["p"]}">{rc["name"].upper()}</div>'
            f'</div></section>'
        )

    elif variant == 1:
        # Full-color background — inv est correct sur fond p
        return (
            f'<section style="padding:{sp} 0;background:{p}">'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<p style="font-family:\'{rc["hf"]}\';font-size:clamp(1.8rem,4vw,3rem);font-weight:300;font-style:italic;color:{rc["inv"]};line-height:1.3">{quote}</p>'
            f'</div></section>'
        )

    elif variant == 2:
        # Left-rule quote
        bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
        sc = _sec_colors(rc, sec_bg)
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:flex;gap:40px;align-items:stretch">'
            f'<div style="width:4px;background:{sc["acc"]};flex-shrink:0"></div>'
            f'<p style="font-family:\'{rc["hf"]}\';font-size:clamp(1.4rem,3.5vw,2.5rem);font-weight:300;font-style:italic;color:{sfg};line-height:1.4">{quote}</p>'
            f'</div></div></section>'
        )

    else:
        # Split: quote left | visual right
        bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
        panel = _visual_panel(rc, rng)
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
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)
    lbl  = _cp("label", rc, rng)
    steps = min(len(kw), rng.choice([3,4]))
    step_colors = [sc["p"], sc["s"], sc["acc"], sc["p"]]

    variant = rng.randint(0, 2)

    if variant == 0:
        # Horizontal steps with connector
        items = "".join(
            f'<div style="flex:1;position:relative">'
            f'<div style="width:40px;height:40px;border-radius:50%;background:{step_colors[i%4]};display:flex;align-items:center;justify-content:center;margin-bottom:20px">'
            f'<span style="{rc["body_css"]};font-size:11px;font-weight:700;color:{rc["inv"]}">{i+1}</span>'
            f'</div>'
            f'<h3 style="{rc["h3_css"]};color:{sfg};margin-bottom:8px">{kw[i].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]};line-height:1.6">{_cp("body", rc, rng, i)}</p>'
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
            f'<div style="display:grid;grid-template-columns:80px 1fr;gap:24px;padding:32px 0;border-bottom:1px solid {sc["bdr"]}">'
            f'<div style="font-family:\'{rc["hf"]}\';font-size:3rem;font-weight:900;color:{step_colors[i%4]};line-height:1">{i+1}</div>'
            f'<div><h3 style="{rc["h3_css"]};color:{sfg};margin-bottom:8px">{kw[i].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:13px;color:{sc["fg2"]};line-height:1.7">{_cp("body", rc, rng, i)}</p></div>'
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
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]};margin-top:4px">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(steps)
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:start">'
            f'<div style="{rc["h2_css"]};color:{sfg};line-height:1.1;white-space:pre-line;position:sticky;top:80px">{intro}</div>'
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
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)
    lbl  = _cp("label", rc, rng)
    n    = rng.choice([4,5,6])

    variant = rng.randint(0, 2)

    if variant == 0:
        rows = "".join(
            f'<div style="display:flex;gap:20px;align-items:baseline;padding:20px 0;border-bottom:1px solid {sc["bdr"]}">'
            f'<span style="{rc["label_css"]};color:{rng.choice([sc["p"],sc["s"]])};min-width:28px">{i+1:02d}</span>'
            f'<h3 style="{rc["h3_css"]};color:{sfg};flex:1">{kw[i%len(kw)].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]};max-width:320px;text-align:right">{_cp("body", rc, rng, i)}</p>'
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
            f'<div style="padding:16px 0;border-bottom:1px solid {sc["bdr"]}">'
            f'<div style="{rc["label_css"]};color:{sc["p"]};margin-bottom:4px">{kw[i%len(kw)].capitalize()}</div>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]}">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(half)
        )
        col2 = "".join(
            f'<div style="padding:16px 0;border-bottom:1px solid {sc["bdr"]}">'
            f'<div style="{rc["label_css"]};color:{sc["s"]};margin-bottom:4px">{kw[(half+i)%len(kw)].capitalize()}</div>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]}">{_cp("body", rc, rng, half+i)}</p>'
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
            f'<span style="{rc["label_css"]};color:{sfg};background:{rng.choice([p,s,rc["acc"]])}22;padding:6px 16px;border-radius:100px;margin:4px;display:inline-block">{kw[i%len(kw)].capitalize()}</span>'
            for i in range(n)
        )
        desc = _cp("body", rc, rng, 0)
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:32px">{rc["section_label"](lbl)}</div>'
            f'<div style="margin-bottom:32px">{tags}</div>'
            f'<p style="{rc["body_css"]};font-size:14px;color:{sc["fg2"]};max-width:600px;line-height:1.8">{desc}</p>'
            f'</div></section>'
        )


def _sec_values_grid(rc):
    rng  = rc["_rng"]
    vals = rc["vals"] or ["authenticité","excellence","engagement","vision","rigueur","impact"]
    p, s, acc = rc["p"], rc["s"], rc["acc"]
    fg, fg2 = rc["fg"], rc["fg2"]
    w    = rc["width_px"]
    sp   = rc["spacing_v"]
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)
    n    = min(len(vals), rng.choice([3,4,6]))
    cols = f"repeat({rng.choice([2,3])},1fr)"

    variant = rng.randint(0, 2)

    if variant == 0:
        sc_colors = [sc["p"], sc["s"], sc["acc"], sc["p"], sc["s"]]
        cards = "".join(
            f'<div style="padding:32px;border:1px solid {sc["bdr"]}">'
            f'<div style="width:32px;height:3px;background:{sc_colors[i%5]};margin-bottom:20px"></div>'
            f'<h3 style="{rc["h3_css"]};color:{sfg};margin-bottom:10px">{vals[i].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]};line-height:1.6">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(n)
        )
    elif variant == 1:
        sc_colors3 = [sc["p"], sc["s"], sc["acc"]]
        cards = "".join(
            f'<div style="padding:28px;border-top:2px solid {sc_colors3[i%3]}">'
            f'<div style="{rc["label_css"]};color:{sc_colors3[i%3]};margin-bottom:16px">0{i+1}</div>'
            f'<h3 style="{rc["h3_css"]};color:{sfg};font-size:1.3rem;margin-bottom:0">{vals[i].capitalize()}</h3>'
            f'</div>'
            for i in range(n)
        )
    else:
        # Fond plein de chaque carte = couleur brand — inv est correct pour le texte sur fond coloré
        cards = "".join(
            f'<div style="background:{[p,s,acc][i%3]};padding:32px">'
            f'<h3 style="font-family:\'{rc["hf"]}\';font-size:1.2rem;font-weight:700;color:{rc["inv"]};margin-bottom:8px">{vals[i].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:11px;color:{rc["inv"]}bb;line-height:1.6">{_cp("body", rc, rng, i)}</p>'
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
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)
    n    = rng.choice([3,4])
    sc_colors = [sc["p"], sc["s"], sc["acc"], sc["p"]]

    variant = rng.randint(0, 2)
    if variant == 0:
        rot = [f"rotate({rng.choice([-1.5,-1,-.5,0,.5,1,1.5])}deg)" for _ in range(n)]
        # Cartes légèrement teintées : fond ≈ section bg, donc sfg est OK pour le texte
        cards = "".join(
            f'<div style="background:{sc_colors[i%4]}18;border-radius:{rc["border_radius"]};padding:28px;transform:{rot[i]};border:1px solid {sc_colors[i%4]}33">'
            f'<div style="{rc["label_css"]};color:{sc_colors[i%4]};margin-bottom:16px">0{i+1}</div>'
            f'<h3 style="{rc["h3_css"]};color:{sfg};margin-bottom:8px">{kw[i%len(kw)].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]}">{_cp("body", rc, rng, i)}</p>'
            f'</div>'
            for i in range(n)
        )
    else:
        # Fond plein = couleur brand, inv est correct
        colors = [p, s, acc, p]
        cards = "".join(
            f'<div style="background:{colors[i%4]};padding:32px">'
            f'<h3 style="font-family:\'{rc["hf"]}\';font-size:1.1rem;font-weight:700;color:{rc["inv"]};margin-bottom:8px">{kw[i%len(kw)].capitalize()}</h3>'
            f'<p style="{rc["body_css"]};font-size:11px;color:{rc["inv"]}bb;line-height:1.6">{_cp("body", rc, rng, i)}</p>'
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
# SECTION BUILDERS — EXTENDED (site family–specific)
# ─────────────────────────────────────────────────────────────────────────────

def _sec_articles_grid(rc):
    """Editorial/Magazine — article cards: image + category + title + date."""
    rng  = rc["_rng"]
    acc  = rc["acc"]; fg = rc["fg"]; fg2 = rc["fg2"]
    w = rc["width_px"]; sp = rc["spacing_v"]
    att  = rc["ad"]["attitude"]
    kw   = rc["kw"] or ["design", "culture", "forme", "vision", "identité"]
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)

    CATS = {
        "editorial":    ["DESIGN", "ART DE VIVRE", "CULTURE", "PORTRAIT", "FOCUS"],
        "brutalist":    ["CRITIQUE", "MANIFESTE", "ANALYSE", "CONTRE-PIED", "RAW"],
        "experimental": ["RECHERCHE", "PROCESSUS", "PROTOTYPE", "LAB", "SYSTÈMES"],
        "playful":      ["TENDANCES", "INSPIRATIONS", "DÉCOUVERTE", "SÉLECTION", "À LA UNE"],
        "product":      ["ACTUALITÉS", "RESSOURCES", "GUIDES", "TENDANCES", "EXPERTISE"],
    }
    cats = CATS.get(att, CATS["product"])
    titles = [
        f"L'art de {kw[0].lower()} dans un monde saturé",
        f"{kw[0].capitalize()} — une question de posture",
        f"Vers une nouvelle {kw[-1].lower()}",
        f"Ce que {kw[0].lower()} nous dit de notre époque",
        f"Repenser {kw[0].lower()} par l'essentiel",
    ]
    dates  = ["14 mars 2026", "7 mars 2026", "28 fév. 2026"]
    _IMGS  = [10, 20, 60, 80, 110, 140]
    articles = [(rng.choice(cats), titles[i%len(titles)], dates[i%3], _IMGS[(i+rng.randint(0,4))%len(_IMGS)]) for i in range(3)]

    cards = "".join(
        f'<article style="display:flex;flex-direction:column">'
        f'<div style="aspect-ratio:16/9;overflow:hidden;margin-bottom:20px;'
        f'background:url(https://picsum.photos/seed/art{img}/600/340) center/cover"></div>'
        f'<span style="{rc["label_css"]};font-size:8px;color:{sc["acc"]};margin-bottom:8px;display:block">{cat}</span>'
        f'<h3 style="{rc["h3_css"]};font-size:1.1rem;line-height:1.35;color:{sfg};margin-bottom:10px">{title}</h3>'
        f'<span style="{rc["label_css"]};font-size:8px;color:{sc["fg2"]}">{date}</span>'
        f'</article>'
        for cat, title, date, img in articles
    )
    return (
        f'<section style="padding:{sp} 0;{bg_css}">{strip}'
        f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
        f'<div style="margin-bottom:40px">{rc["section_label"]("DERNIERS ARTICLES")}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:40px">{cards}</div>'
        f'</div></section>'
    )


def _sec_work_grid(rc):
    """Studio/Portfolio — project gallery: image overlay + tag + title."""
    rng = rc["_rng"]
    acc = rc["acc"]; w = rc["width_px"]; sp = rc["spacing_v"]
    att = rc["ad"]["attitude"]
    kw  = rc["kw"] or ["branding", "web", "identité", "print"]
    name = rc["name"]
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng, "alt_bg")

    TAGS = {
        "brutalist":    ["SYSTÈME", "IDENTITÉ", "TYPE", "MANIFESTE"],
        "editorial":    ["DIRECTION ARTISTIQUE", "IDENTITÉ VISUELLE", "PRINT", "WEB"],
        "experimental": ["GÉNÉRATIF", "INTERACTIF", "INSTALLATION", "PROTOTYPE"],
        "playful":      ["BRANDING", "PACKAGING", "MOTION", "SOCIAL"],
        "product":      ["UI/UX", "WEB", "APP", "SYSTÈME DE DESIGN"],
    }
    tags = TAGS.get(att, TAGS["product"])
    proj_names = [
        f"Campagne {kw[0].capitalize()} 2026",
        f"Identité {name}",
        f"Système {kw[-1].capitalize()}",
        f"Collection {kw[0].capitalize()}",
    ]
    _IMGS = [15, 25, 35, 45, 55, 65]
    projects = [(proj_names[i%len(proj_names)], rng.choice(tags), _IMGS[i%len(_IMGS)]) for i in range(4)]

    variant = rng.randint(0, 1)
    if variant == 0:
        cards = "".join(
            f'<div style="position:relative;aspect-ratio:4/3;overflow:hidden;cursor:pointer">'
            f'<div style="position:absolute;inset:0;background:url(https://picsum.photos/seed/wrk{img}/800/600) center/cover"></div>'
            f'<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.72) 0%,transparent 55%)"></div>'
            f'<div style="position:absolute;bottom:0;left:0;right:0;padding:24px">'
            f'<span style="{rc["label_css"]};font-size:8px;color:{acc};display:block;margin-bottom:6px">{tag}</span>'
            f'<h3 style="{rc["h3_css"]};color:#fff;font-size:1rem">{title}</h3>'
            f'</div></div>'
            for title, tag, img in projects
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:40px">{rc["section_label"]("TRAVAUX")}</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">{cards}</div>'
            f'</div></section>'
        )
    else:
        big = projects[0]; smalls = projects[1:3]
        big_c = (
            f'<div style="position:relative;aspect-ratio:16/10;overflow:hidden">'
            f'<div style="position:absolute;inset:0;background:url(https://picsum.photos/seed/wrk{big[2]}/1200/750) center/cover"></div>'
            f'<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.75) 0%,transparent 55%)"></div>'
            f'<div style="position:absolute;bottom:0;left:0;right:0;padding:32px">'
            f'<span style="{rc["label_css"]};font-size:8px;color:{acc};display:block;margin-bottom:6px">{big[1]}</span>'
            f'<h3 style="{rc["h3_css"]};color:#fff;font-size:1.3rem">{big[0]}</h3>'
            f'</div></div>'
        )
        small_c = "".join(
            f'<div style="position:relative;aspect-ratio:16/9;overflow:hidden">'
            f'<div style="position:absolute;inset:0;background:url(https://picsum.photos/seed/wrk{p[2]}/600/338) center/cover"></div>'
            f'<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.7) 0%,transparent 55%)"></div>'
            f'<div style="position:absolute;bottom:0;left:0;right:0;padding:20px">'
            f'<span style="{rc["label_css"]};font-size:8px;color:{acc};display:block;margin-bottom:4px">{p[1]}</span>'
            f'<h3 style="{rc["h3_css"]};color:#fff;font-size:.95rem">{p[0]}</h3>'
            f'</div></div>'
            for p in smalls
        )
        return (
            f'<section style="padding:{sp} 0;{bg_css}">{strip}'
            f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
            f'<div style="margin-bottom:40px">{rc["section_label"]("TRAVAUX")}</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">'
            f'<div>{big_c}</div>'
            f'<div style="display:flex;flex-direction:column;gap:24px">{small_c}</div>'
            f'</div></div></section>'
        )


def _sec_product_grid(rc):
    """E-commerce/Catalog — product cards: image + name + category + price."""
    rng = rc["_rng"]
    p, acc = rc["p"], rc["acc"]; inv = rc["inv"]
    fg2 = rc["fg2"]; br = rc["border_radius"]
    w = rc["width_px"]; sp = rc["spacing_v"]
    name = rc["name"]; kw = rc["kw"] or ["produit", "collection", "série"]
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)

    PRODUCTS = [
        (f"{name} — Édition I",    "€189", kw[0].capitalize()),
        (f"{name} — Édition II",   "€249", kw[-1].capitalize()),
        (f"{name} — Format S",     "€89",  kw[0].capitalize()),
        (f"Collection {kw[0].capitalize()}", "€350", "Série limitée"),
    ]
    _IMGS = [20, 30, 40, 50, 60, 70]
    n     = rng.choice([3, 4])
    prods = PRODUCTS[:n]

    cards = "".join(
        f'<div style="display:flex;flex-direction:column">'
        f'<div style="aspect-ratio:3/4;overflow:hidden;background:url(https://picsum.photos/seed/prd{_IMGS[(i+2)%len(_IMGS)]}/400/533) center/cover;'
        f'border-radius:{br};margin-bottom:16px"></div>'
        f'<h3 style="{rc["h3_css"]};font-size:1rem;color:{sfg};margin-bottom:6px">{prod[0]}</h3>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px">'
        f'<span style="{rc["label_css"]};font-size:8px;color:{sc["fg2"]}">{prod[2]}</span>'
        f'<span style="{rc["h3_css"]};font-size:1.1rem;color:{sc["acc"]};font-weight:700">{prod[1]}</span>'
        f'</div>'
        f'<button style="margin-top:14px;background:{p};color:{inv};border:none;padding:10px 24px;'
        f'border-radius:{br};{rc["body_css"]};font-size:11px;font-weight:700;cursor:pointer">Ajouter au panier</button>'
        f'</div>'
        for i, prod in enumerate(prods)
    )
    return (
        f'<section style="padding:{sp} 0;{bg_css}">{strip}'
        f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
        f'<div style="margin-bottom:40px">{rc["section_label"]("COLLECTION")}</div>'
        f'<div style="display:grid;grid-template-columns:repeat({n},1fr);gap:32px">{cards}</div>'
        f'</div></section>'
    )


def _sec_logo_wall(rc):
    """Brand/Institution — press mentions or client logos."""
    rng = rc["_rng"]
    w = rc["width_px"]; sp = rc["spacing_v"]
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng, "alt_bg")

    _ALL_LOGOS = [
        "Le Monde", "Libération", "L'Obs", "Télérama", "Le Figaro",
        "Forbes", "Wired", "Dezeen", "Monocle", "Wallpaper*",
        "LVMH", "Hermès", "Chanel", "L'Oréal", "Kering",
    ]
    n     = rng.choice([6, 8])
    logos = rng.sample(_ALL_LOGOS, min(n, len(_ALL_LOGOS)))
    col   = 4 if n >= 6 else 3

    items = "".join(
        f'<div style="display:flex;align-items:center;justify-content:center;padding:20px 24px;opacity:.42">'
        f'<span style="{rc["h3_css"]};font-size:1rem;font-weight:700;color:{sfg};letter-spacing:-.02em">{logo}</span>'
        f'</div>'
        for logo in logos
    )
    return (
        f'<section style="padding:{sp} 0;{bg_css}">{strip}'
        f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
        f'<div style="text-align:center;margin-bottom:40px">{rc["section_label"]("ILS NOUS FONT CONFIANCE")}</div>'
        f'<div style="display:grid;grid-template-columns:repeat({col},1fr);gap:0">{items}</div>'
        f'</div></section>'
    )


def _sec_speakers(rc):
    """Event/Campaign — speaker cards with avatar + name + role."""
    rng = rc["_rng"]
    acc = rc["acc"]; fg2 = rc["fg2"]
    w = rc["width_px"]; sp = rc["spacing_v"]
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)

    _SPEAKERS = [
        ("Alice Moreau",    "Directrice Créative, Studio Lumière"),
        ("Jonas Berg",      "Cofondateur, Minimal Works"),
        ("Yasmin Okafor",   "Chercheuse, Lab for Design Futures"),
        ("Pierre Cassagne", "Designer & Auteur"),
    ]
    _SEEDS = [10, 20, 30, 40]
    n       = rng.choice([3, 4])
    speakers = _SPEAKERS[:n]

    cards = "".join(
        f'<div style="text-align:center">'
        f'<div style="width:80px;height:80px;border-radius:50%;overflow:hidden;margin:0 auto 16px;'
        f'background:url(https://picsum.photos/seed/face{_SEEDS[i]}/80/80) center/cover;'
        f'border:2px solid {sc["acc"]}"></div>'
        f'<h3 style="{rc["h3_css"]};font-size:1rem;color:{sfg};margin-bottom:4px">{spk[0]}</h3>'
        f'<span style="{rc["label_css"]};font-size:8px;color:{sc["fg2"]};display:block">{spk[1]}</span>'
        f'</div>'
        for i, spk in enumerate(speakers)
    )
    return (
        f'<section style="padding:{sp} 0;{bg_css}">{strip}'
        f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
        f'<div style="margin-bottom:48px">{rc["section_label"]("INTERVENANTS")}</div>'
        f'<div style="display:grid;grid-template-columns:repeat({n},1fr);gap:32px">{cards}</div>'
        f'</div></section>'
    )


def _sec_schedule(rc):
    """Event/Campaign — program / time schedule."""
    rng  = rc["_rng"]
    p, acc = rc["p"], rc["acc"]
    fg2 = rc["fg2"]; w = rc["width_px"]; sp = rc["spacing_v"]
    kw   = rc["kw"]   or ["ouverture", "conférence", "atelier", "table ronde"]
    vals = rc["vals"] or ["échange", "inspiration", "création"]
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng, "alt_bg")
    sc = _sec_colors(rc, sec_bg)

    _TIMES  = ["09h00", "10h30", "12h00", "14h00", "15h30", "17h00", "18h30"]
    _EVENTS = [
        f"Ouverture — {vals[0].capitalize()}",
        f"Conférence : {kw[0].capitalize()}",
        f"Atelier {kw[-1].capitalize()}",
        f"Table ronde — {vals[1%len(vals)].capitalize()}",
        f"Keynote : l'avenir de {kw[0].lower()}",
    ]
    n    = rng.choice([4, 5])
    rows = "".join(
        f'<div style="display:grid;grid-template-columns:80px 1fr;gap:24px;'
        f'padding:20px 0;border-bottom:1px solid {sc["bdr"]}">'
        f'<span style="{rc["h3_css"]};font-size:1.1rem;font-weight:700;color:{sc["acc"] if i==0 else sc["p"]}">{_TIMES[i]}</span>'
        f'<span style="{rc["body_css"]};font-size:14px;color:{sfg};line-height:1.5">{_EVENTS[i%len(_EVENTS)]}</span>'
        f'</div>'
        for i in range(n)
    )
    return (
        f'<section style="padding:{sp} 0;{bg_css}">{strip}'
        f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
        f'<div style="margin-bottom:40px">{rc["section_label"]("PROGRAMME")}</div>'
        f'{rows}'
        f'</div></section>'
    )


def _sec_material_story(rc):
    """Craft/Artisan — materials + process story."""
    rng  = rc["_rng"]
    acc  = rc["acc"]; fg = rc["fg"]; fg2 = rc["fg2"]
    w = rc["width_px"]; sp = rc["spacing_v"]
    kw   = rc["kw"]   or ["acier", "bois", "argile", "cuir"]
    vals = rc["vals"] or ["authenticité", "durabilité", "savoir-faire"]
    brief_txt = rc.get("brief_txt", "")
    bg_css, strip, sfg, sec_bg = _sec_vt(rc, rng)
    sc = _sec_colors(rc, sec_bg)

    _MAT_MAP = {
        "forge":    ["Acier Damascus",    "Fer forgé",         "Bronze patiné"],
        "couteaux": ["Acier inoxydable",  "Bois d'Olivier",    "Corne naturelle"],
        "céramique":["Grès chamotté",     "Porcelaine blanche","Faïence émaillée"],
        "bois":     ["Noyer américain",   "Chêne massif",      "Hêtre naturel"],
    }
    mat_list = next((v for k, v in _MAT_MAP.items() if k in brief_txt), None) \
               or [kw[0].capitalize(), kw[1].capitalize() if len(kw) > 1 else "Matière naturelle"]

    _IMGS = [12, 24, 36, 48]
    n     = rng.choice([2, 3])
    items = [(mat_list[i%len(mat_list)], _IMGS[i%len(_IMGS)]) for i in range(n)]

    cards = "".join(
        f'<div style="display:flex;flex-direction:column;gap:12px">'
        f'<div style="aspect-ratio:4/3;background:url(https://picsum.photos/seed/mat{img}/600/450) center/cover;'
        f'border-radius:{rc["border_radius"]}"></div>'
        f'<h3 style="{rc["h3_css"]};font-size:1rem;color:{sfg}">{mat}</h3>'
        f'<p style="{rc["body_css"]};font-size:12px;color:{sc["fg2"]};line-height:1.7">'
        f'{vals[i%len(vals)].capitalize()}. Choisie pour son caractère et sa durabilité.</p>'
        f'</div>'
        for i, (mat, img) in enumerate(items)
    )
    return (
        f'<section style="padding:{sp} 0;{bg_css}">{strip}'
        f'<div style="max-width:{w};margin:0 auto;padding:0 48px">'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:64px;align-items:start">'
        f'<div>'
        f'{rc["section_label"]("MATIÈRES ET SAVOIR-FAIRE")}'
        f'<p style="{rc["body_css"]};font-size:15px;color:{sfg};line-height:1.85;margin-top:16px">'
        f'Chaque pièce commence par le choix d\'une matière. {vals[0].capitalize()}, '
        f'{vals[1%len(vals)].lower()} — des exigences qui guident chaque geste.</p>'
        f'<div style="width:40px;height:3px;background:{sc["acc"]};margin-top:24px"></div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:{"1fr "*n};gap:16px">{cards}</div>'
        f'</div></div></section>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# SITE TYPE SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

_SITE_SIGNALS = {
    "product_saas":          ["saas", "api ", "plateforme", "logiciel", "appli", "dashboard", "b2b", "software", "abonnement", "subscription", "outil numérique"],
    "editorial_magazine":    ["magazine", "revue", "publication", "articles", "édito", "editorial", "journal", "newsletter", "médias", "rédaction", "presse"],
    "studio_portfolio":      ["studio", "portfolio", "créations", "travaux", "projets", "photographe", "photographie", "architecte", "illustrateur", "freelance design"],
    "craft_artisan":         ["artisanal", "artisan", "forge", "céramique", "couture", "bois", "main", "fabricat", "savoir-faire", "couteaux", "poterie", "luthier", "broderie"],
    "ecommerce_catalog":     ["boutique", "collection", "achat", "commander", "panier", "livraison", "e-commerce", "shop", "catalogue", "gamme de produits"],
    "event_campaign":        ["festival", "événement", "conférence", "lancement", "campagne", "concert", "exposition", "inscription", "programme", "billet"],
    "institution_manifesto": ["association", "fondation", "manifeste", "cause", "collectif", "ong", "institution", "mouvement", "engagement", "culturel"],
    "brand_landing":         ["agence", "startup", "services", "brand", "identité", "marketing", "consulting", "cabinet", "laboratoire"],
}

def site_type_resolver(brief_text: str, dna=None) -> str:
    """Analyzes brief signals → returns site family key (one of 8)."""
    txt    = brief_text.lower()
    scores = {k: sum(1 for s in v if s in txt) for k, v in _SITE_SIGNALS.items()}
    if dna:
        industry = (getattr(dna, "industry", "") or "").lower()
        for fam, sigs in _SITE_SIGNALS.items():
            if any(s in industry for s in sigs):
                scores[fam] = scores.get(fam, 0) + 2
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "brand_landing"


PAGE_FAMILIES = {
    "brand_landing": {
        "label": "Brand / Landing",
        "cta_band": True,
        "home_blueprints": [
            {"hero": "split",      "sections": ["stats", "features_grid", "pull_quote", "process", "logo_wall"]},
            {"hero": "centered",   "sections": ["features_cards", "stats", "values_list", "pull_quote"]},
            {"hero": "full-bleed", "sections": ["pull_quote", "features_grid", "process", "stats"]},
        ],
        "page_blueprints": {
            "about":   {"hero": "centered",   "sections": ["manifesto", "values_list", "process", "pull_quote"]},
            "product": {"hero": "split",       "sections": ["stats", "features_grid", "features_cards", "process"]},
            "minimal": {"hero": "centered",   "sections": ["manifesto", "pull_quote"]},
        },
    },
    "editorial_magazine": {
        "label": "Édito / Magazine",
        "cta_band": False,
        "home_blueprints": [
            {"hero": "layered",    "sections": ["articles_grid", "manifesto", "pull_quote", "stats"]},
            {"hero": "asymmetric", "sections": ["manifesto", "articles_grid", "pull_quote", "values_list"]},
            {"hero": "centered",   "sections": ["articles_grid", "pull_quote", "manifesto"]},
        ],
        "page_blueprints": {
            "about":   {"hero": "layered",    "sections": ["manifesto", "values_list", "pull_quote", "stats"]},
            "product": {"hero": "asymmetric", "sections": ["articles_grid", "manifesto", "pull_quote"]},
            "minimal": {"hero": "centered",   "sections": ["pull_quote", "manifesto"]},
        },
    },
    "studio_portfolio": {
        "label": "Studio / Portfolio",
        "cta_band": False,
        "home_blueprints": [
            {"hero": "full-bleed", "sections": ["work_grid", "stats", "pull_quote", "process"]},
            {"hero": "asymmetric", "sections": ["work_grid", "manifesto", "stats", "pull_quote"]},
            {"hero": "layered",    "sections": ["work_grid", "process", "pull_quote", "values_list"]},
        ],
        "page_blueprints": {
            "about":   {"hero": "centered",   "sections": ["manifesto", "process", "values_list", "stats"]},
            "product": {"hero": "full-bleed", "sections": ["work_grid", "process", "pull_quote"]},
            "minimal": {"hero": "centered",   "sections": ["work_grid", "pull_quote"]},
        },
    },
    "product_saas": {
        "label": "Produit / SaaS",
        "cta_band": True,
        "home_blueprints": [
            {"hero": "centered",   "sections": ["features_grid", "stats", "process", "pull_quote", "features_cards"]},
            {"hero": "split",      "sections": ["stats", "features_cards", "process", "features_grid"]},
            {"hero": "asymmetric", "sections": ["features_grid", "stats", "features_cards", "pull_quote"]},
        ],
        "page_blueprints": {
            "about":   {"hero": "centered",  "sections": ["values_list", "stats", "process", "pull_quote"]},
            "product": {"hero": "split",     "sections": ["features_grid", "features_cards", "stats", "process"]},
            "minimal": {"hero": "centered",  "sections": ["features_grid", "pull_quote"]},
        },
    },
    "craft_artisan": {
        "label": "Craft / Artisan",
        "cta_band": False,
        "home_blueprints": [
            {"hero": "split",   "sections": ["material_story", "process", "pull_quote", "stats"]},
            {"hero": "layered", "sections": ["material_story", "values_list", "pull_quote", "process"]},
            {"hero": "split",   "sections": ["process", "material_story", "pull_quote", "values_list"]},
        ],
        "page_blueprints": {
            "about":   {"hero": "layered",  "sections": ["manifesto", "process", "material_story", "pull_quote"]},
            "product": {"hero": "split",    "sections": ["material_story", "process", "stats", "pull_quote"]},
            "minimal": {"hero": "centered", "sections": ["material_story", "pull_quote"]},
        },
    },
    "ecommerce_catalog": {
        "label": "E-commerce",
        "cta_band": False,
        "home_blueprints": [
            {"hero": "centered", "sections": ["product_grid", "stats", "features_list", "pull_quote"]},
            {"hero": "split",    "sections": ["product_grid", "features_list", "pull_quote", "stats"]},
            {"hero": "centered", "sections": ["product_grid", "pull_quote", "features_list"]},
        ],
        "page_blueprints": {
            "about":   {"hero": "centered", "sections": ["manifesto", "values_list", "pull_quote"]},
            "product": {"hero": "split",    "sections": ["product_grid", "features_list", "stats"]},
            "minimal": {"hero": "centered", "sections": ["product_grid", "pull_quote"]},
        },
    },
    "event_campaign": {
        "label": "Événement",
        "cta_band": True,
        "home_blueprints": [
            {"hero": "full-bleed", "sections": ["schedule", "speakers", "stats", "pull_quote"]},
            {"hero": "centered",   "sections": ["speakers", "schedule", "pull_quote", "stats"]},
            {"hero": "full-bleed", "sections": ["stats", "speakers", "schedule", "pull_quote"]},
        ],
        "page_blueprints": {
            "about":   {"hero": "centered",   "sections": ["manifesto", "speakers", "values_list"]},
            "product": {"hero": "full-bleed", "sections": ["schedule", "speakers", "stats"]},
            "minimal": {"hero": "centered",   "sections": ["schedule", "pull_quote"]},
        },
    },
    "institution_manifesto": {
        "label": "Institution",
        "cta_band": False,
        "home_blueprints": [
            {"hero": "full-bleed", "sections": ["manifesto", "values_list", "stats", "pull_quote", "logo_wall"]},
            {"hero": "centered",   "sections": ["manifesto", "stats", "values_list", "pull_quote"]},
            {"hero": "layered",    "sections": ["manifesto", "pull_quote", "values_list", "stats", "logo_wall"]},
        ],
        "page_blueprints": {
            "about":   {"hero": "full-bleed", "sections": ["manifesto", "values_list", "stats", "pull_quote"]},
            "product": {"hero": "centered",   "sections": ["manifesto", "values_list", "logo_wall"]},
            "minimal": {"hero": "centered",   "sections": ["manifesto", "pull_quote"]},
        },
    },
}

_ALL_SECTION_KEYS = {
    "features_grid", "features_list", "features_cards",
    "values_list", "values_grid", "manifesto", "stats", "pull_quote", "process",
    "articles_grid", "work_grid", "product_grid", "logo_wall",
    "speakers", "schedule", "material_story",
}


def layout_blueprint_generator(site_family: str, page_type: str, rng,
                               variant_index: int = -1) -> dict:
    """
    Returns structural blueprint: {hero, sections, no_cta_band}.
    site_family drives WHAT — art direction drives HOW.

    variant_index >= 0 → deterministic indexed selection from home_blueprints,
    guaranteeing that each variant uses a distinct blueprint (different hero + sections).
    variant_index == -1 → random selection (single-variant / legacy path).
    """
    fam = PAGE_FAMILIES.get(site_family, PAGE_FAMILIES["brand_landing"])
    if page_type == "landing" or page_type not in fam.get("page_blueprints", {}):
        bps = fam["home_blueprints"]
        if variant_index >= 0:
            bp = bps[variant_index % len(bps)]
        else:
            bp = rng.choice(bps)
    else:
        bp = fam["page_blueprints"][page_type]
    no_cta = page_type == "minimal" or not fam.get("cta_band", True)
    return {
        "hero":        bp["hero"],
        "sections":    [s for s in bp["sections"] if s in _ALL_SECTION_KEYS],
        "no_cta_band": no_cta,
    }


# ─────────────────────────────────────────────────────────────────────────────
# HERO BUILDERS v2 — no defaults, all from rc
# ─────────────────────────────────────────────────────────────────────────────

def _hero_centered_v2(rc, rng):
    p=rc["p"]; inv=rc["inv"]; br=rc["button_radius"]
    bh=rc["button_hierarchy"]; body=rc["body_css"]
    s2 = (f'<button style="background:transparent;color:{rc["acc"]};'
          f'border:1.5px solid {rc["acc"]};padding:15px 32px;border-radius:{br};'
          f'{body};cursor:pointer">{rc["cta_s"]}</button>') if bh=="dual" and rc["cta_s"] else ""
    return (
        f'<section style="padding:{rc["spacing_v"]} 0;text-align:center;{rc["bg_art"]}">'
        f'<div style="position:relative;z-index:1;max-width:{rc["width_px"]};margin:0 auto;padding:0 48px">'
        f'{rc["industry_badge"]}'
        f'{rc.get("_accent_mark","")}'
        f'<h1 style="{rc["h1_css"]};margin:0 auto 28px;white-space:pre-line;max-width:800px;overflow-wrap:break-word;word-break:break-word">{rc["h1"]}</h1>'
        f'<p style="{body};font-size:1rem;color:{rc["fg2"]};max-width:480px;margin:0 auto 44px;line-height:{rc["body_lh"]}">{rc["sub"]}</p>'
        f'<div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap">'
        f'<button style="background:{p};color:{inv};border:none;padding:16px 44px;border-radius:{br};{body};font-weight:700;cursor:pointer">{rc["cta_p"]}</button>'
        f'{s2}'
        f'</div></div></section>'
    )


def _hero_split_v2(rc, rng):
    p=rc["p"]; inv=rc["inv"]; br=rc["button_radius"]
    bh=rc["button_hierarchy"]; body=rc["body_css"]
    panel = _visual_panel(rc, rng)
    s2 = (f'<button style="background:transparent;color:{rc["acc"]};'
          f'border:1.5px solid {rc["acc"]};padding:15px 28px;border-radius:{br};'
          f'{body};cursor:pointer">{rc["cta_s"]}</button>') if bh=="dual" and rc["cta_s"] else ""
    return (
        f'<section style="padding:0;min-height:560px;display:grid;grid-template-columns:55% 45%">'
        f'<div style="padding:100px 60px 80px;{rc["bg_art"]};display:flex;flex-direction:column;justify-content:center">'
        f'{rc["industry_badge"]}'
        f'{rc.get("_accent_mark","")}'
        f'<h1 style="{rc["h1_css"]};margin:20px 0 28px;white-space:pre-line;overflow-wrap:break-word;word-break:break-word">{rc["h1"]}</h1>'
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
    panel = _visual_panel(rc, rng)
    s2 = (f'<button style="background:transparent;color:{rc["acc"]};'
          f'border:1px solid {rc["acc"]};padding:14px 28px;border-radius:{br};'
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
        f'{rc.get("_accent_mark","")}'
        f'<h1 style="{rc["h1_css"]};margin:20px 0 32px;white-space:pre-line;overflow-wrap:break-word;word-break:break-word">{rc["h1"]}</h1>'
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
    panel = _visual_panel(rc, rng)
    kw = rc["kw"] or ["IMPACT"]
    h1_raw = rc["h1"] or kw[0]
    h2_raw = kw[1].upper() if len(kw)>1 else rc["name"]
    s2 = (f'<button style="background:transparent;color:{rc["acc"]};border:1px solid {rc["acc"]};'
          f'padding:14px 24px;{rc["label_css"]};font-size:10px;text-transform:uppercase;cursor:pointer">{rc["cta_s"]}</button>'
          ) if bh=="dual" and rc["cta_s"] else ""
    # Fullbleed = image + dark scrim → texte toujours blanc, indépendamment de la palette
    return (
        f'<section style="padding:0;min-height:640px;position:relative;display:flex;flex-direction:column;justify-content:flex-end">'
        f'{panel}'
        f'<div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0.1) 0%,rgba(0,0,0,0.72) 65%,rgba(0,0,0,0.82) 100%);z-index:0"></div>'
        f'<div style="position:relative;z-index:1;max-width:{rc["width_px"]};margin:0 auto;padding:0 48px 64px;width:100%">'
        f'<div style="{rc["h1_css"]};color:#f5f5f5;font-size:clamp(2.5rem,6vw,4.5rem);margin-bottom:32px;white-space:pre-line;overflow-wrap:break-word;overflow:hidden;max-width:100%">{h1_raw}</div>'
        f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:24px">'
        f'<p style="{body};font-size:13px;color:rgba(255,255,255,0.78);max-width:360px;line-height:1.75">{rc["sub"]}</p>'
        f'<div style="display:flex;gap:12px">'
        f'<button style="background:{p};color:{inv};border:none;padding:14px 32px;border-radius:{br};{body};font-weight:700;cursor:pointer">{rc["cta_p"]}</button>'
        f'{s2}'
        f'</div></div></div></section>'
    )


def _hero_asymmetric_v2(rc, rng):
    p=rc["p"]; inv=rc["inv"]; br=rc["button_radius"]
    bh=rc["button_hierarchy"]; body=rc["body_css"]
    panel = _visual_panel(rc, rng)
    col_a = rng.choice(["60%","65%","70%"])
    col_b = f"calc(100% - {col_a})"
    s2 = (f'<button style="background:transparent;color:{rc["acc"]};border:1.5px solid {rc["acc"]};'
          f'padding:15px 28px;border-radius:{br};{body};cursor:pointer">{rc["cta_s"]}</button>'
          ) if bh=="dual" and rc["cta_s"] else ""
    shift = rng.choice(["40px","60px","80px"])
    return (
        f'<section style="padding:0;min-height:580px;display:grid;grid-template-columns:{col_a} {col_b};align-items:stretch">'
        f'<div style="padding:100px 64px 80px;{rc["bg_art"]};display:flex;flex-direction:column;justify-content:center;position:relative">'
        f'{rc["industry_badge"]}'
        f'{rc.get("_accent_mark","")}'
        f'<h1 style="{rc["h1_css"]};margin:20px 0 28px;white-space:pre-line;padding-left:{shift};overflow-wrap:break-word;word-break:break-word">{rc["h1"]}</h1>'
        f'<p style="{body};font-size:1rem;color:{rc["fg2"]};max-width:420px;margin-bottom:44px;line-height:{rc["body_lh"]};padding-left:{shift}">{rc["sub"]}</p>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap;padding-left:{shift}">'
        f'<button style="background:{p};color:{inv};border:none;padding:16px 36px;border-radius:{br};{body};font-weight:700;cursor:pointer">{rc["cta_p"]}</button>'
        f'{s2}'
        f'</div></div>'
        f'<div style="position:relative;overflow:hidden">{panel}</div>'
        f'</section>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE TYPE OVERRIDES
# ─────────────────────────────────────────────────────────────────────────────

def _apply_page_type_overrides(rc: dict, page_type: str, rng) -> None:
    """
    Modifie le RenderingContract en fonction du type de page.
    Appelé après _build_rendering_contract — surcharge hero_pattern + sections.
    page_type: "landing" (default) | "about" | "product" | "minimal"
    """
    if page_type == "about":
        # Page à propos : narratif, valeurs + histoire + process
        # Hero plus introspectif (centered ou layered)
        rc["hero_pattern"] = rng.choice(["centered", "layered"])
        # Sections orientées story-telling
        _pool = ["manifesto", "values_list", "process", "pull_quote", "stats", "features_list"]
        rc["sections"] = ["manifesto", "values_list", "process", "pull_quote"]
        # On garde stats si l'archetype est "product" (data-driven)
        if rc.get("page_structure") == "product":
            rc["sections"] = ["stats", "values_list", "process", "pull_quote"]
        # CTA plus doux
        rc["cta_p"] = f"Travailler avec {rc['name']}"
        rc["cta_s"] = ""
        # Headline plus narratif si pas de tagline
        if rc["h1"] == rc["name"] or not rc["h1"]:
            vals = rc.get("vals") or []
            rc["h1"] = f"{vals[0].capitalize()} et {vals[1]}." if len(vals) >= 2 else f"Notre approche"
        rc["sub"] = f"Ce qui nous définit, ce qui nous guide, ce qui nous différencie."

    elif page_type == "product":
        # Page produit : features, proof, conversion
        rc["hero_pattern"] = rng.choice(["split", "full-bleed", "asymmetric"])
        rc["sections"] = ["stats", "features_grid", "process", "features_cards", "pull_quote"]
        # CTA orienté conversion
        brief_txt = rc.get("brief_txt", "")
        if any(x in brief_txt for x in ["saas", "api", "b2b", "logiciel", "plateforme"]):
            rc["cta_p"] = "Essayer gratuitement"
            rc["cta_s"] = ""
        elif any(x in brief_txt for x in ["boutique", "e-commerce", "produit", "collection"]):
            rc["cta_p"] = "Voir la collection"
            rc["cta_s"] = ""
        else:
            rc["cta_p"] = f"Découvrir {rc['name']}"
            rc["cta_s"] = ""

    elif page_type == "minimal":
        # Page épurée : un hero propre, 2 sections max, pas de CTA band
        rc["hero_pattern"] = "centered"
        _pool_m = ["pull_quote", "values_list", "features_list", "manifesto"]
        # Choisir 2 sections dans le pool
        _available = [s for s in _pool_m if s in ["pull_quote", "values_list", "features_list", "manifesto"]]
        rc["sections"] = rng.sample(_available, min(2, len(_available)))
        # Pas de CTA band (géré dans _lp_dynamic_page)
        rc["_no_cta_band"] = True
        # Espacement plus généreux
        rc["spacing_v"] = "120px"

    # "landing" = aucune surcharge (comportement existant)


# ─────────────────────────────────────────────────────────────────────────────
# FAMILY RENDERERS — structure HTML distincte par famille de site
# ─────────────────────────────────────────────────────────────────────────────

def _render_editorial_page(rc, rng, gf, reset, css_str, responsive):
    """Magazine / revue — masthead + article vedette + grille articles. Pas de hero CTA."""
    p,s,acc,bg,bg2,fg,fg2,bdr = rc["p"],rc["s"],rc["acc"],rc["bg"],rc["bg2"],rc["fg"],rc["fg2"],rc["bdr"]
    name = rc["name"]; kw = rc["kw"] or []; body = rc["body_css"]; hf = rc["hf"]; inv = rc["inv"]
    h1wt = "300" if rc.get("ad",{}).get("attitude")=="editorial" else "700"

    issue_n = rng.randint(1, 52)
    months = ["Jan.","Fév.","Mar.","Avr.","Mai","Jun.","Jul.","Aoû.","Sep.","Oct.","Nov.","Déc."]
    month_fr = rng.choice(months)
    rubrics = (kw[:5] or ["Design","Art","Vie","Essais","Agenda"])

    rubric_links = "".join(
        f'<a style="{body};font-size:11px;font-weight:600;color:{fg if i>0 else p};'
        f'letter-spacing:.08em;text-transform:uppercase;padding:10px 0;'
        f'border-bottom:2px solid {p if i==0 else "transparent"};cursor:pointer;white-space:nowrap">'
        f'{r.capitalize()}</a>'
        for i, r in enumerate(rubrics)
    )

    masthead = (
        f'<header style="background:{bg};border-bottom:2px solid {fg}">'
        f'<div style="border-bottom:1px solid {bdr};padding:5px 48px;display:flex;justify-content:space-between;align-items:center">'
        f'<span style="{body};font-size:9px;color:{fg2};letter-spacing:.18em;text-transform:uppercase">N°{issue_n} — {month_fr} 2026</span>'
        f'<span style="{body};font-size:9px;color:{p};letter-spacing:.12em;text-transform:uppercase;cursor:pointer">S\'abonner</span>'
        f'</div>'
        f'<div style="text-align:center;padding:32px 48px 24px">'
        f'<div style="font-family:\'{hf}\',serif;font-size:clamp(2.8rem,7vw,5.5rem);'
        f'font-weight:{h1wt};letter-spacing:-.03em;color:{fg};line-height:.95">{name.upper()}</div>'
        f'<div style="display:flex;align-items:center;justify-content:center;gap:12px;margin-top:12px">'
        f'<div style="height:1px;width:40px;background:{bdr}"></div>'
        f'<span style="{body};font-size:10px;color:{fg2};letter-spacing:.14em;text-transform:uppercase">Revue indépendante</span>'
        f'<div style="height:1px;width:40px;background:{bdr}"></div>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;gap:32px;padding:0 48px;border-top:1px solid {bdr};overflow-x:auto">'
        f'{rubric_links}'
        f'</div>'
        f'</header>'
    )

    img_seed = rng.randint(10, 990)
    category = (kw[0] if kw else "Dossier").upper()
    feature = (
        f'<section style="display:grid;grid-template-columns:58% 42%;border-bottom:2px solid {fg};min-height:500px">'
        f'<div style="position:relative;overflow:hidden">'
        f'<img src="https://picsum.photos/seed/{img_seed}/900/600" '
        f'style="width:100%;height:100%;object-fit:cover;filter:grayscale(.12)" loading="lazy"/>'
        f'<div style="position:absolute;inset:0;background:{p};mix-blend-mode:color;opacity:.22"></div>'
        f'</div>'
        f'<div style="padding:48px;display:flex;flex-direction:column;justify-content:space-between;background:{bg}">'
        f'<div>'
        f'<div style="{body};font-size:9px;font-weight:700;color:{acc};letter-spacing:.22em;'
        f'text-transform:uppercase;border-bottom:2px solid {acc};display:inline-block;padding-bottom:4px;margin-bottom:20px">'
        f'{category} — À LA UNE</div>'
        f'<h2 style="font-family:\'{hf}\',serif;font-size:clamp(1.5rem,2.8vw,2.2rem);'
        f'font-weight:{h1wt};font-style:italic;color:{fg};line-height:1.2;margin-bottom:20px">{rc["h1"]}</h2>'
        f'<p style="{body};font-size:13px;color:{fg2};line-height:1.9">{rc["sub"]}</p>'
        f'</div>'
        f'<div style="border-top:1px solid {bdr};padding-top:16px;display:flex;align-items:center;justify-content:space-between">'
        f'<span style="{body};font-size:10px;color:{fg2};letter-spacing:.06em">Par la Rédaction</span>'
        f'<a style="{body};font-size:10px;font-weight:700;color:{p};cursor:pointer;letter-spacing:.05em">Lire l\'article →</a>'
        f'</div>'
        f'</div>'
        f'</section>'
    )

    rc["_rng"] = rng
    articles = _sec_articles_grid(rc) if "articles_grid" in (rc.get("sections") or []) else ""
    _sec_map = {"pull_quote": _sec_pull_quote, "manifesto": _sec_manifesto,
                "stats": _sec_stats, "values_list": _sec_values_list}
    other = "".join(_sec_map[sk](rc) for sk in (rc.get("sections") or [])
                    if sk in _sec_map and sk != "articles_grid")

    footer = (
        f'<footer style="padding:36px 48px;background:{fg};display:flex;'
        f'justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">'
        f'<div style="font-family:\'{hf}\',serif;font-size:1.3rem;font-weight:{h1wt};'
        f'font-style:italic;color:{inv}">{name.upper()}</div>'
        f'<div style="display:flex;align-items:center;gap:16px">'
        f'<span style="{body};font-size:10px;color:{inv}66">N°{issue_n} — {month_fr} 2026</span>'
        f'<button style="background:{p};color:{_text_on(p)};border:none;padding:9px 22px;'
        f'{body};font-size:11px;font-weight:700;cursor:pointer;letter-spacing:.05em">Abonnement →</button>'
        f'</div>'
        f'</footer>'
    )
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>'
            f'{gf}<style>{reset}{css_str or ""}{responsive}</style></head><body>'
            f'{masthead}{feature}{articles}{other}{footer}</body></html>')


def _nav_logo_mark(name: str, p: str, inv: str, size: int = 28) -> str:
    """
    Logo mark visuel pour le nav : carré coloré avec initiale(s) de la marque.
    Garantit un identifiant visuel fort même sans fichier image.
    """
    parts = name.split()
    if len(parts) >= 2:
        initials = parts[0][0].upper() + parts[1][0].upper()
    else:
        initials = name[:2].upper() if len(name) >= 2 else name[0].upper()
    fs = max(10, size // 2)
    return (
        f'<div style="width:{size}px;height:{size}px;background:{p};'
        f'border-radius:5px;flex-shrink:0;display:flex;align-items:center;'
        f'justify-content:center">'
        f'<span style="font-family:system-ui,sans-serif;font-size:{fs}px;'
        f'font-weight:900;color:{inv};line-height:1;letter-spacing:-.03em">'
        f'{initials}</span>'
        f'</div>'
    )


def _render_studio_page(rc, rng, gf, reset, css_str, responsive):
    """Studio / portfolio — nav minimaliste, ouverture projet plein-écran, pas de CTA startup."""
    p,s,acc,bg,bg2,fg,fg2,bdr = rc["p"],rc["s"],rc["acc"],rc["bg"],rc["bg2"],rc["fg"],rc["fg2"],rc["bdr"]
    name = rc["name"]; kw = rc["kw"] or []; body = rc["body_css"]; hf = rc["hf"]; inv = rc["inv"]

    nav = (
        f'<nav style="position:fixed;top:0;left:0;right:0;z-index:100;height:52px;'
        f'background:{bg};border-bottom:1px solid {bdr};display:flex;align-items:center;'
        f'justify-content:space-between;padding:0 48px">'
        f'<div style="display:flex;align-items:center;gap:10px">'
        f'{_nav_logo_mark(name, p, inv, 28)}'
        f'<span style="font-family:\'{hf}\',serif;font-size:.95rem;font-weight:700;color:{fg}">{name}</span>'
        f'</div>'
        f'<div style="display:flex;gap:32px;align-items:center">'
        f'<a style="{body};font-size:11px;color:{fg2};cursor:pointer">Travaux</a>'
        f'<a style="{body};font-size:11px;color:{fg2};cursor:pointer">Studio</a>'
        f'<a style="{body};font-size:11px;font-weight:700;color:{p};cursor:pointer">Contact →</a>'
        f'</div></nav>'
    )

    cats = ["Identité","Digital","Espace","Motion","Édition","Direction artistique"]
    rng.shuffle(cats)
    img1, img2, img3 = rng.randint(10,490), rng.randint(491,750), rng.randint(751,990)
    p1 = kw[0].capitalize() if kw else "Projet I"
    p2 = kw[1].capitalize() if len(kw)>1 else "Projet II"
    p3 = kw[2].capitalize() if len(kw)>2 else "Projet III"

    showcase = (
        f'<section style="margin-top:52px;display:grid;grid-template-columns:62% 38%;min-height:88vh">'
        f'<div style="position:relative;overflow:hidden;cursor:pointer">'
        f'<img src="https://picsum.photos/seed/{img1}/1000/800" '
        f'style="width:100%;height:100%;object-fit:cover;filter:grayscale(.06)" loading="lazy"/>'
        f'<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.72) 0%,transparent 45%)"></div>'
        f'<div style="position:absolute;bottom:40px;left:40px">'
        f'<div style="{body};font-size:9px;font-weight:700;color:{acc};letter-spacing:.24em;text-transform:uppercase;margin-bottom:8px">01 — {cats[0].upper()}</div>'
        f'<div style="font-family:\'{hf}\',serif;font-size:clamp(1.4rem,3vw,2.2rem);font-weight:700;color:#f2f2f2;line-height:1.1">{p1}</div>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;flex-direction:column">'
        f'<div style="position:relative;overflow:hidden;flex:1;cursor:pointer;border-bottom:1px solid {bdr}">'
        f'<img src="https://picsum.photos/seed/{img2}/600/450" '
        f'style="width:100%;height:100%;object-fit:cover;filter:grayscale(.06)" loading="lazy"/>'
        f'<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.68) 0%,transparent 50%)"></div>'
        f'<div style="position:absolute;bottom:24px;left:24px">'
        f'<div style="{body};font-size:9px;font-weight:700;color:{acc};letter-spacing:.2em;text-transform:uppercase;margin-bottom:6px">02 — {cats[1].upper()}</div>'
        f'<div style="font-family:\'{hf}\',serif;font-size:1.1rem;font-weight:700;color:#f2f2f2">{p2}</div>'
        f'</div>'
        f'</div>'
        f'<div style="padding:28px 24px;background:{bg2};border-left:3px solid {p}">'
        f'<p style="{body};font-size:12px;color:{fg2};line-height:1.85;margin-bottom:14px">{rc.get("sub","")}</p>'
        f'<a style="{body};font-size:11px;font-weight:700;color:{p};cursor:pointer">Tous les projets →</a>'
        f'</div>'
        f'</div>'
        f'</section>'
    )

    rc["_rng"] = rng
    work = _sec_work_grid(rc) if "work_grid" in (rc.get("sections") or []) else ""
    _sec_map = {"stats": _sec_stats, "pull_quote": _sec_pull_quote,
                "process": _sec_process, "values_list": _sec_values_list}
    other = "".join(_sec_map[sk](rc) for sk in (rc.get("sections") or [])
                    if sk in _sec_map and sk != "work_grid")

    footer = (
        f'<footer style="padding:64px 48px;background:{fg};display:flex;'
        f'justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:32px">'
        f'<div>'
        f'<div style="font-family:\'{hf}\',serif;font-size:2.2rem;font-weight:700;color:{inv};margin-bottom:6px">{name}</div>'
        f'<div style="{body};font-size:11px;color:{inv}55;letter-spacing:.1em;text-transform:uppercase">{cats[0]} &amp; {cats[1]}</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div style="{body};font-size:10px;color:{inv}55;margin-bottom:5px;letter-spacing:.1em;text-transform:uppercase">Contact</div>'
        f'<div style="font-family:\'{hf}\',serif;font-size:1rem;color:{inv}">studio@{name.lower().replace(" ","")}.com</div>'
        f'</div>'
        f'</footer>'
    )
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>'
            f'{gf}<style>{reset}{css_str or ""}{responsive}</style></head><body>'
            f'{nav}{showcase}{work}{other}{footer}</body></html>')


def _render_event_page(rc, rng, gf, reset, css_str, responsive):
    """Événement / festival — nav sombre avec date, poster typographique, programme."""
    p,s,acc,bg,bg2,fg,fg2,bdr = rc["p"],rc["s"],rc["acc"],rc["bg"],rc["bg2"],rc["fg"],rc["fg2"],rc["bdr"]
    name = rc["name"]; kw = rc["kw"] or []; body = rc["body_css"]; hf = rc["hf"]; inv = rc["inv"]

    day   = rng.randint(1, 28)
    months_fr = ["JANVIER","FÉVRIER","MARS","AVRIL","MAI","JUIN",
                 "JUILLET","AOÛT","SEPTEMBRE","OCTOBRE","NOVEMBRE","DÉCEMBRE"]
    month = rng.choice(months_fr)
    city  = rng.choice(["PARIS","LYON","BORDEAUX","MARSEILLE","NANTES","STRASBOURG"])
    venue = rng.choice(["Grande Halle","Palais des Arts","Cité Numérique","Forum","Zénith"])
    ev_p  = _text_on(p)

    nav = (
        f'<nav style="position:sticky;top:0;z-index:100;background:{fg};'
        f'border-bottom:1px solid {fg2}33;height:56px;display:flex;align-items:center;'
        f'justify-content:space-between;padding:0 48px">'
        f'<div style="display:flex;align-items:center;gap:12px">'
        f'{_nav_logo_mark(name, p, ev_p, 28)}'
        f'<span style="font-family:\'{hf}\',serif;font-size:1rem;font-weight:700;color:{inv}">{name.upper()}</span>'
        f'<span style="{body};font-size:10px;color:{inv}55;letter-spacing:.12em">{day} {month} 2026</span>'
        f'</div>'
        f'<div style="display:flex;gap:20px;align-items:center">'
        f'<a style="{body};font-size:10px;color:{inv}77;cursor:pointer;letter-spacing:.06em">PROGRAMME</a>'
        f'<a style="{body};font-size:10px;color:{inv}77;cursor:pointer;letter-spacing:.06em">INTERVENANTS</a>'
        f'<a style="{body};font-size:10px;color:{inv}77;cursor:pointer;letter-spacing:.06em">ACCÈS</a>'
        f'<button style="background:{p};color:{ev_p};border:none;padding:8px 20px;'
        f'{body};font-size:11px;font-weight:700;cursor:pointer;letter-spacing:.06em">RÉSERVER</button>'
        f'</div></nav>'
    )

    img_seed = rng.randint(10, 990)
    poster = (
        f'<section style="position:relative;min-height:85vh;display:flex;flex-direction:column;'
        f'justify-content:flex-end;overflow:hidden;background:{fg}">'
        f'<img src="https://picsum.photos/seed/{img_seed}/1400/900" '
        f'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;'
        f'opacity:.28;filter:grayscale(.4)" loading="lazy"/>'
        f'<div style="position:absolute;top:-10px;left:40px;font-family:\'{hf}\',serif;'
        f'font-size:clamp(8rem,22vw,18rem);font-weight:900;color:{p}15;'
        f'line-height:.85;letter-spacing:-.06em;pointer-events:none;user-select:none">'
        f'{str(day).zfill(2)}</div>'
        f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;'
        f'background:linear-gradient(to bottom,transparent 20%,rgba(0,0,0,.78) 80%)"></div>'
        f'<div style="position:relative;z-index:1;padding:0 48px 72px">'
        f'<div style="{body};font-size:10px;font-weight:700;color:{acc};letter-spacing:.28em;'
        f'text-transform:uppercase;margin-bottom:14px">{city} — {venue}</div>'
        f'<h1 style="font-family:\'{hf}\',serif;font-size:clamp(2.5rem,8vw,6rem);'
        f'font-weight:900;color:#f4f4f4;line-height:.92;letter-spacing:-.04em;margin-bottom:8px">{rc["h1"]}</h1>'
        f'<div style="display:flex;align-items:center;gap:32px;margin-top:36px;flex-wrap:wrap">'
        f'<div style="font-family:\'{hf}\',serif;font-size:1.5rem;font-weight:300;'
        f'color:{inv}77;letter-spacing:.06em">{day} {month} 2026</div>'
        f'<button style="background:{p};color:{ev_p};border:none;padding:15px 40px;'
        f'{body};font-size:13px;font-weight:700;cursor:pointer;letter-spacing:.08em;text-transform:uppercase">'
        f'RÉSERVER MA PLACE</button>'
        f'</div>'
        f'</div>'
        f'</section>'
    )

    rc["_rng"] = rng
    _sec_map = {"schedule": _sec_schedule, "speakers": _sec_speakers,
                "stats": _sec_stats, "pull_quote": _sec_pull_quote}
    sections_html = "".join(_sec_map[sk](rc) for sk in (rc.get("sections") or []) if sk in _sec_map)

    footer = (
        f'<footer style="padding:36px 48px;background:{fg};border-top:1px solid {fg2}33;'
        f'display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">'
        f'<div>'
        f'<div style="font-family:\'{hf}\',serif;font-size:1.1rem;font-weight:700;color:{inv}">{name}</div>'
        f'<div style="{body};font-size:10px;color:{inv}55">{day} {month} 2026 — {city}</div>'
        f'</div>'
        f'<button style="background:{p};color:{ev_p};border:none;padding:12px 28px;'
        f'{body};font-size:12px;font-weight:700;cursor:pointer">Réserver →</button>'
        f'</footer>'
    )
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>'
            f'{gf}<style>{reset}{css_str or ""}{responsive}</style></head><body>'
            f'{nav}{poster}{sections_html}{footer}</body></html>')


def _render_ecommerce_page(rc, rng, gf, reset, css_str, responsive):
    """E-commerce / catalogue — structure authentique : nav catégories, annonce promo, hero produit,
    spotlight catégories, grille produits, newsletter, footer multi-colonnes."""
    p,s,acc,bg,bg2,fg,fg2,bdr = rc["p"],rc["s"],rc["acc"],rc["bg"],rc["bg2"],rc["fg"],rc["fg2"],rc["bdr"]
    name = rc["name"]; kw = rc["kw"] or []; vals = rc["vals"] or []; body = rc["body_css"]
    hf = rc["hf"]; inv = rc["inv"]; br = rc["button_radius"]

    # CTAs e-commerce — indépendants du DNA de la marque
    shop_cta  = rng.choice(["Voir la collection", "Découvrir maintenant", "Acheter maintenant", "Explorer la boutique"])
    browse_cta = rng.choice(["Parcourir le catalogue", "Toute la sélection", "Voir tout"])

    # ── Top bar : offre promotionnelle ─────────────────────────────────────────
    promo_msg = rng.choice([
        f"Livraison gratuite dès 75€ — Code : {name[:3].upper()}25",
        "Nouvelle collection disponible — Livraison 48h",
        f"Édition limitée {name} — Stocks limités",
        "Retours gratuits sous 30 jours",
    ])
    top_bar = (
        f'<div style="background:{p};padding:8px 48px;text-align:center">'
        f'<span style="{body};font-size:11px;color:{inv};font-weight:600">{promo_msg}</span>'
        f'</div>'
    )

    # ── Nav : logo | liens catégories | icônes ─────────────────────────────────
    main_cats = (kw[:4] or ["Nouveautés","Collections","Bestsellers","Éditions"])
    nav = (
        f'<nav style="background:{bg};border-bottom:2px solid {bdr};position:sticky;top:0;z-index:100">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;padding:0 48px;height:56px">'
        f'<div style="display:flex;align-items:center;gap:10px">'
        f'{_nav_logo_mark(name, p, inv, 30)}'
        f'<span style="font-family:\'{hf}\',serif;font-size:1.1rem;font-weight:700;color:{fg}">{name}</span>'
        f'</div>'
        f'<div style="display:flex;gap:28px;align-items:center">'
        + "".join(f'<a style="{body};font-size:12px;color:{fg};cursor:pointer;font-weight:500">{c.capitalize()}</a>' for c in main_cats)
        + f'</div>'
        f'<div style="display:flex;gap:16px;align-items:center">'
        f'<span style="{body};font-size:11px;color:{fg2};cursor:pointer">🔍</span>'
        f'<span style="{body};font-size:11px;color:{fg2};cursor:pointer">♡</span>'
        f'<span style="{body};font-size:11px;font-weight:700;color:{p};cursor:pointer">Panier (0)</span>'
        f'</div>'
        f'</div>'
        f'</nav>'
    )

    # ── Hero : grand format promotionnel 60/40 ─────────────────────────────────
    img_seed = rng.randint(10, 990)
    promo_label = rng.choice(["Nouvelle Collection","Édition Limitée","Sélection Printemps","Exclusivité Web"])
    hero_title = rc["h1"]  # titre court de la marque = tagline produit
    hero = (
        f'<section style="display:grid;grid-template-columns:58% 42%;min-height:480px">'
        f'<div style="position:relative;overflow:hidden">'
        f'<img src="https://picsum.photos/seed/{img_seed}/900/600" '
        f'style="width:100%;height:100%;object-fit:cover" loading="lazy"/>'
        f'<div style="position:absolute;inset:0;background:{p};mix-blend-mode:multiply;opacity:.12"></div>'
        f'</div>'
        f'<div style="padding:56px 48px;background:{bg};display:flex;flex-direction:column;justify-content:center;'
        f'border-left:4px solid {p}">'
        f'<div style="{body};font-size:9px;font-weight:700;color:{p};letter-spacing:.22em;'
        f'text-transform:uppercase;margin-bottom:14px">{promo_label}</div>'
        f'<h1 style="font-family:\'{hf}\',serif;font-size:clamp(1.8rem,3.5vw,2.8rem);'
        f'font-weight:700;color:{fg};line-height:1.1;letter-spacing:-.02em;margin-bottom:14px">{hero_title}</h1>'
        f'<p style="{body};font-size:13px;color:{fg2};line-height:1.75;margin-bottom:28px;max-width:340px">{rc.get("sub","")}</p>'
        f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">'
        f'<a style="background:{p};color:{inv};padding:13px 32px;border-radius:{br};'
        f'{body};font-size:12px;font-weight:700;cursor:pointer;display:inline-block">{shop_cta} →</a>'
        f'<a style="{body};font-size:11px;color:{fg2};text-decoration:underline;cursor:pointer">{browse_cta}</a>'
        f'</div>'
        f'<div style="display:flex;gap:24px;margin-top:32px;padding-top:24px;border-top:1px solid {bdr}">'
        f'<div style="text-align:center"><div style="font-family:\'{hf}\',serif;font-size:1.4rem;font-weight:700;color:{fg}">48h</div>'
        f'<div style="{body};font-size:9px;color:{fg2};text-transform:uppercase;letter-spacing:.1em">Livraison</div></div>'
        f'<div style="text-align:center"><div style="font-family:\'{hf}\',serif;font-size:1.4rem;font-weight:700;color:{fg}">30j</div>'
        f'<div style="{body};font-size:9px;color:{fg2};text-transform:uppercase;letter-spacing:.1em">Retours</div></div>'
        f'<div style="text-align:center"><div style="font-family:\'{hf}\',serif;font-size:1.4rem;font-weight:700;color:{fg}">4.8★</div>'
        f'<div style="{body};font-size:9px;color:{fg2};text-transform:uppercase;letter-spacing:.1em">Avis clients</div></div>'
        f'</div>'
        f'</div>'
        f'</section>'
    )

    # ── Spotlight catégories ───────────────────────────────────────────────────
    spot_cats = (kw + ["Nouveautés","Archives","Éditions","Capsule"])[:4]
    spot_seeds = [img_seed+10, img_seed+20, img_seed+30, img_seed+40]
    spots = "".join(
        f'<div style="position:relative;aspect-ratio:3/4;overflow:hidden;cursor:pointer">'
        f'<img src="https://picsum.photos/seed/{spot_seeds[i%4]}/400/533" '
        f'style="width:100%;height:100%;object-fit:cover;transition:transform .4s" loading="lazy"/>'
        f'<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.55) 0%,transparent 50%)"></div>'
        f'<div style="position:absolute;bottom:0;left:0;right:0;padding:20px">'
        f'<div style="{body};font-size:11px;font-weight:700;color:#fff;text-transform:uppercase;'
        f'letter-spacing:.1em;margin-bottom:4px">{spot_cats[i%len(spot_cats)].capitalize()}</div>'
        f'<a style="{body};font-size:10px;color:rgba(255,255,255,.72);text-decoration:underline;cursor:pointer">Voir →</a>'
        f'</div>'
        f'</div>'
        for i in range(4)
    )
    category_spotlight = (
        f'<section style="padding:48px;background:{bg2}">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:24px">'
        f'<h2 style="font-family:\'{hf}\',serif;font-size:1.2rem;font-weight:700;color:{fg}">Nos catégories</h2>'
        f'<a style="{body};font-size:11px;color:{p};cursor:pointer;font-weight:600">Tout voir →</a>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px">{spots}</div>'
        f'</section>'
    )

    # ── Grille produits (toujours présente pour un e-commerce) ─────────────────
    rc["_rng"] = rng
    # Générer les produits inline (sans passer par _sec_product_grid qui est conditionnel)
    _br = rc["border_radius"]
    _PRODUCTS = [
        (f"{name} — Édition I",             f"€{rng.choice([129,189,229])}", kw[0].capitalize() if kw else "Sélection"),
        (f"{name} — Collection II",         f"€{rng.choice([89,149,199])}",  kw[-1].capitalize() if kw else "Bestseller"),
        (f"Série {vals[0].capitalize() if vals else 'Signature'}", f"€{rng.choice([59,79,99])}", "Nouveauté"),
        (f"{name} — Format Premium",        f"€{rng.choice([249,299,349])}", "Édition Limitée"),
    ]
    n_prods = rng.choice([3, 4])
    prod_cards = "".join(
        f'<div style="display:flex;flex-direction:column;cursor:pointer">'
        f'<div style="position:relative;aspect-ratio:3/4;overflow:hidden;background:{bg2};'
        f'border-radius:{_br};margin-bottom:14px">'
        f'<img src="https://picsum.photos/seed/prd{img_seed+i*7}/400/533" '
        f'style="width:100%;height:100%;object-fit:cover" loading="lazy"/>'
        f'{"<div style=\\'position:absolute;top:12px;left:12px;background:"+p+";color:"+inv+";padding:3px 10px;font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase\\'>NOUVEAU</div>" if i==0 else ""}'
        f'</div>'
        f'<div style="font-family:\'{hf}\',serif;font-size:.95rem;font-weight:600;color:{fg};margin-bottom:4px">{_PRODUCTS[i][0]}</div>'
        f'<div style="{body};font-size:10px;color:{fg2};text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">{_PRODUCTS[i][2]}</div>'
        f'<div style="display:flex;align-items:center;justify-content:space-between">'
        f'<span style="font-family:\'{hf}\',serif;font-size:1.05rem;font-weight:700;color:{fg}">{_PRODUCTS[i][1]}</span>'
        f'<button style="background:{p};color:{inv};border:none;padding:7px 16px;border-radius:{_br};'
        f'{body};font-size:10px;font-weight:700;cursor:pointer">+ Panier</button>'
        f'</div>'
        f'</div>'
        for i in range(n_prods)
    )
    product_section = (
        f'<section style="padding:56px 48px;background:{bg}">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:32px">'
        f'<h2 style="font-family:\'{hf}\',serif;font-size:1.4rem;font-weight:700;color:{fg}">Bestsellers</h2>'
        f'<a style="{body};font-size:11px;color:{p};font-weight:600;cursor:pointer">Voir toute la boutique →</a>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:repeat({n_prods},1fr);gap:28px">{prod_cards}</div>'
        f'</section>'
    )

    # ── Bande newsletter ───────────────────────────────────────────────────────
    newsletter = (
        f'<section style="padding:48px;background:{p};text-align:center">'
        f'<h2 style="font-family:\'{hf}\',serif;font-size:1.6rem;font-weight:700;color:{inv};margin-bottom:8px">'
        f'Rejoignez la communauté {name}</h2>'
        f'<p style="{body};font-size:12px;color:{inv}cc;margin-bottom:24px">'
        f'Accès exclusif aux nouvelles collections, offres membres et avant-premières.</p>'
        f'<div style="display:flex;gap:0;max-width:420px;margin:0 auto">'
        f'<input style="flex:1;padding:12px 18px;border:none;{body};font-size:12px;'
        f'border-radius:{br} 0 0 {br};outline:none" placeholder="Votre email" type="email"/>'
        f'<button style="background:{fg};color:{bg};border:none;padding:12px 24px;'
        f'border-radius:0 {br} {br} 0;{body};font-size:12px;font-weight:700;cursor:pointer">S\'inscrire</button>'
        f'</div>'
        f'</section>'
    )

    # ── Footer multi-colonnes ──────────────────────────────────────────────────
    footer_cols = [
        ("Boutique",     main_cats[:4]),
        ("Service",      ["Livraison","Retours","Mon compte","FAQ"]),
        ("La marque",    ["Notre histoire","Engagement","Presse","Contact"]),
    ]
    cols_html = "".join(
        f'<div>'
        f'<div style="{body};font-size:9px;font-weight:700;color:{fg};letter-spacing:.15em;text-transform:uppercase;margin-bottom:16px">{col_title}</div>'
        + "".join(f'<div style="margin-bottom:8px"><a style="{body};font-size:11px;color:{fg2};cursor:pointer">{lk}</a></div>' for lk in links)
        + f'</div>'
        for col_title, links in footer_cols
    )
    footer = (
        f'<footer style="padding:48px;background:{bg2};border-top:1px solid {bdr}">'
        f'<div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:48px;margin-bottom:40px">'
        f'<div>'
        f'<div style="font-family:\'{hf}\',serif;font-size:1.3rem;font-weight:700;color:{fg};margin-bottom:12px">{name}</div>'
        f'<p style="{body};font-size:11px;color:{fg2};line-height:1.7;max-width:220px">{rc.get("sub","")[:80]}</p>'
        f'</div>'
        f'{cols_html}'
        f'</div>'
        f'<div style="padding-top:24px;border-top:1px solid {bdr};display:flex;justify-content:space-between;align-items:center">'
        f'<span style="{body};font-size:10px;color:{fg2}">© 2026 {name}. Tous droits réservés.</span>'
        f'<div style="display:flex;gap:16px">'
        f'<a style="{body};font-size:10px;color:{fg2};cursor:pointer">Mentions légales</a>'
        f'<a style="{body};font-size:10px;color:{fg2};cursor:pointer">CGV</a>'
        f'<a style="{body};font-size:10px;color:{fg2};cursor:pointer">Confidentialité</a>'
        f'</div>'
        f'</div>'
        f'</footer>'
    )

    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{name} — Boutique</title>'
            f'{gf}<style>{reset}{css_str or ""}{responsive}</style></head><body>'
            f'{top_bar}{nav}{hero}{category_spotlight}{product_section}{newsletter}{footer}</body></html>')


def _render_brand_landing_page(rc, rng, gf, reset, css_str, responsive):
    """Brand / Landing — hero fort + sections conviction + CTA band. Structure startup/agence."""
    p,s,acc,bg,bg2,fg,fg2,bdr = rc["p"],rc["s"],rc["acc"],rc["bg"],rc["bg2"],rc["fg"],rc["fg2"],rc["bdr"]
    name = rc["name"]; kw = rc["kw"] or []; vals = rc["vals"] or []; body = rc["body_css"]
    hf = rc["hf"]; inv = rc["inv"]; br = rc["button_radius"]

    # Nav avec badge catégorie + CTA principal
    industry = (rc.get("industry") or "").upper()
    nav = (
        f'<nav style="position:sticky;top:0;z-index:100;height:60px;background:{bg};'
        f'border-bottom:2px solid {acc};backdrop-filter:blur(12px);'
        f'display:flex;align-items:center;justify-content:space-between;padding:0 48px">'
        f'<div style="display:flex;align-items:center;gap:12px">'
        f'{_nav_logo_mark(name, p, inv, 28)}'
        f'<span style="font-family:\'{hf}\',serif;font-size:1.05rem;font-weight:700;color:{fg}">{name}</span>'
        f'{"<span style='"+body+";font-size:9px;font-weight:700;color:"+acc+";border:1px solid "+acc+";padding:2px 8px;letter-spacing:.12em;text-transform:uppercase'>" + industry + "</span>" if industry else ""}'
        f'</div>'
        f'<div style="display:flex;gap:20px;align-items:center">'
        + "".join(f'<a style="{body};font-size:11px;color:{fg2};cursor:pointer">{k.capitalize()}</a>' for k in kw[:3])
        + f'<button style="background:{p};color:{inv};border:none;padding:9px 22px;border-radius:{br};'
        f'{body};font-size:12px;font-weight:700;cursor:pointer">{rc.get("cta_p","Commencer").split()[0]}</button>'
        f'</div></nav>'
    )

    # Hero : centré avec bg_art + grande headline + double CTA
    cta_s = rc.get("cta_s","")
    s2 = (f'<button style="background:transparent;color:{acc};border:1.5px solid {acc};'
          f'padding:14px 28px;border-radius:{br};{body};cursor:pointer">{cta_s}</button>') if cta_s else ""
    hero_p = rc.get("hero_pattern","centered")
    # Force centered pour brand_landing (le split/asymm est pour les familles avec image)
    hero = (
        f'<section style="padding:{rc.get("spacing_v","88px")} 0;text-align:center;{rc.get("bg_art","background:"+bg)}">'
        f'<div style="position:relative;z-index:1;max-width:{rc.get("width_px","1060px")};margin:0 auto;padding:0 48px">'
        f'{rc.get("industry_badge","")}'
        f'{rc.get("_accent_mark","")}'
        f'<h1 style="{rc.get("h1_css","")};margin:0 auto 28px;white-space:pre-line;overflow-wrap:break-word;word-break:break-word">{rc["h1"]}</h1>'
        f'<p style="{body};font-size:1.05rem;color:{fg2};max-width:520px;margin:0 auto 48px;line-height:{rc.get("body_lh","1.75")}">{rc.get("sub","")}</p>'
        f'<div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap">'
        f'<button style="background:{p};color:{inv};border:none;padding:17px 48px;border-radius:{br};{body};font-size:15px;font-weight:700;cursor:pointer">{rc.get("cta_p","Commencer")}</button>'
        f'{s2}'
        f'</div>'
        f'</div>'
        f'</section>'
    )

    rc["_rng"] = rng
    _sec_map = {k: v for k,v in {
        "features_grid": _sec_features_grid, "features_list": _sec_features_list,
        "features_cards": _sec_features_cards, "values_list": _sec_values_list,
        "values_grid": _sec_values_grid, "manifesto": _sec_manifesto,
        "stats": _sec_stats, "pull_quote": _sec_pull_quote, "process": _sec_process,
        "logo_wall": _sec_logo_wall,
    }.items()}
    sections_html = "".join(_sec_map[sk](rc) for sk in (rc.get("sections") or []) if sk in _sec_map)

    inv_rgba = "255,255,255" if inv=="#fff" else "0,0,0"
    cta_band = (
        f'<section style="padding:{rc.get("spacing_v","88px")} 0;background:{p};text-align:center">'
        f'<div style="max-width:{rc.get("width_px","1060px")};margin:0 auto;padding:0 48px">'
        f'<h2 style="font-family:\'{hf}\',serif;font-size:2rem;font-weight:700;color:{inv};margin-bottom:14px">{name}</h2>'
        f'<p style="{body};font-size:14px;color:rgba({inv_rgba},.72);max-width:400px;margin:0 auto 36px;line-height:1.8">{rc.get("sub","")}</p>'
        f'<button style="background:{inv};color:{p};border:none;padding:18px 52px;'
        f'border-radius:{br};{body};font-size:14px;font-weight:700;cursor:pointer">{rc.get("cta_p","Commencer")}</button>'
        f'</div></section>'
    )

    footer = (
        f'<footer style="padding:40px 48px;background:{bg2};border-top:1px solid {bdr};'
        f'display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">'
        f'<span style="font-family:\'{hf}\',serif;font-size:.95rem;font-weight:700;color:{fg}">{name}</span>'
        f'<div style="display:flex;gap:24px">'
        + "".join(f'<a style="{body};font-size:11px;color:{fg2};cursor:pointer">{k.capitalize()}</a>' for k in kw[:4])
        + f'</div><span style="{body};font-size:11px;color:{fg2}">© 2026 {name}</span></footer>'
    )
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>'
            f'{gf}<style>{reset}{css_str or ""}{responsive}</style></head><body>'
            f'{nav}{hero}{sections_html}{cta_band}{footer}</body></html>')


def _render_product_saas_page(rc, rng, gf, reset, css_str, responsive):
    """Produit / SaaS — nav avec login, hero dashboard, features table, social proof, pricing."""
    p,s,acc,bg,bg2,fg,fg2,bdr = rc["p"],rc["s"],rc["acc"],rc["bg"],rc["bg2"],rc["fg"],rc["fg2"],rc["bdr"]
    name = rc["name"]; kw = rc["kw"] or []; body = rc["body_css"]; hf = rc["hf"]; inv = rc["inv"]; br = rc["button_radius"]

    nav = (
        f'<nav style="position:sticky;top:0;z-index:100;height:56px;background:{bg};'
        f'border-bottom:1px solid {bdr};backdrop-filter:blur(12px);'
        f'display:flex;align-items:center;justify-content:space-between;padding:0 48px">'
        f'<div style="display:flex;align-items:center;gap:10px">'
        f'{_nav_logo_mark(name, p, inv, 28)}'
        f'<span style="font-family:\'{hf}\',serif;font-size:1rem;font-weight:700;color:{p}">{name}</span>'
        f'</div>'
        f'<div style="display:flex;gap:24px;align-items:center">'
        + "".join(f'<a style="{body};font-size:12px;color:{fg2};cursor:pointer">{k.capitalize()}</a>' for k in kw[:3])
        + f'<a style="{body};font-size:12px;color:{fg2};cursor:pointer">Connexion</a>'
        f'<button style="background:{p};color:{inv};border:none;padding:8px 20px;border-radius:{br};'
        f'{body};font-size:12px;font-weight:700;cursor:pointer">Essayer gratuitement</button>'
        f'</div></nav>'
    )

    # Hero : texte gauche + dashboard CSS droite
    dashboard_rows = "".join(
        f'<div style="background:{bg2};border-radius:4px;height:{h}px;margin-bottom:6px;'
        f'background:linear-gradient(90deg,{p}22 0%,{s}11 100%)"></div>'
        for h in [18, 12, 18, 12, 8, 18, 12]
    )
    dashboard = (
        f'<div style="background:{bg2};border-radius:8px;padding:20px;border:1px solid {bdr};'
        f'box-shadow:0 20px 60px rgba(0,0,0,.12)">'
        f'<div style="display:flex;gap:6px;margin-bottom:14px">'
        f'<div style="width:10px;height:10px;border-radius:50%;background:#ff5f57"></div>'
        f'<div style="width:10px;height:10px;border-radius:50%;background:#ffbd2e"></div>'
        f'<div style="width:10px;height:10px;border-radius:50%;background:#28c840"></div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px">'
        + "".join(f'<div style="background:{p}{("22" if i>0 else "")};border-radius:4px;padding:10px;text-align:center"><div style="{body};font-size:14px;font-weight:700;color:{p if i==0 else fg}">{["↑ 48%","3.2k","99.9%"][i]}</div><div style="{body};font-size:9px;color:{fg2};text-transform:uppercase;letter-spacing:.1em">{["Conversion","Utilisateurs","Uptime"][i]}</div></div>' for i in range(3))
        + f'</div>{dashboard_rows}</div>'
    )

    hero = (
        f'<section style="padding:80px 0;background:{bg}">'
        f'<div style="max-width:1100px;margin:0 auto;padding:0 48px;'
        f'display:grid;grid-template-columns:52% 48%;gap:64px;align-items:center">'
        f'<div>'
        f'{rc.get("industry_badge","")}'
        f'{rc.get("_accent_mark","")}'
        f'<h1 style="{rc.get("h1_css","")};margin-bottom:24px;overflow-wrap:break-word;word-break:break-word">{rc["h1"]}</h1>'
        f'<p style="{body};font-size:1rem;color:{fg2};max-width:440px;margin-bottom:40px;line-height:{rc.get("body_lh","1.75")}">{rc.get("sub","")}</p>'
        f'<div style="display:flex;gap:12px;flex-wrap:wrap">'
        f'<button style="background:{p};color:{inv};border:none;padding:15px 36px;border-radius:{br};{body};font-size:14px;font-weight:700;cursor:pointer">Commencer gratuitement</button>'
        f'<button style="background:transparent;color:{fg};border:1px solid {bdr};padding:15px 24px;border-radius:{br};{body};font-size:14px;cursor:pointer">Voir la démo →</button>'
        f'</div>'
        f'<p style="{body};font-size:11px;color:{fg2};margin-top:14px">✓ Sans carte bancaire · ✓ 14 jours offerts · ✓ Annulation libre</p>'
        f'</div>'
        f'<div>{dashboard}</div>'
        f'</div>'
        f'</section>'
    )

    rc["_rng"] = rng
    _sec_map = {
        "features_grid": _sec_features_grid, "features_cards": _sec_features_cards,
        "features_list": _sec_features_list, "stats": _sec_stats,
        "pull_quote": _sec_pull_quote, "process": _sec_process, "logo_wall": _sec_logo_wall,
    }
    sections_html = "".join(_sec_map[sk](rc) for sk in (rc.get("sections") or []) if sk in _sec_map)

    # Pricing hint
    pricing = (
        f'<section style="padding:64px 0;background:{bg2};text-align:center;border-top:1px solid {bdr}">'
        f'<div style="max-width:760px;margin:0 auto;padding:0 48px">'
        f'<div style="{body};font-size:10px;font-weight:700;color:{acc};letter-spacing:.18em;text-transform:uppercase;margin-bottom:12px">Tarifs simples</div>'
        f'<h2 style="font-family:\'{hf}\',serif;font-size:1.8rem;font-weight:700;color:{fg};margin-bottom:12px">Gratuit pour commencer, puissant pour scaler</h2>'
        f'<p style="{body};font-size:13px;color:{fg2};margin-bottom:28px;line-height:1.8">Démarrez gratuitement. Passez au plan Pro quand vous êtes prêt.</p>'
        f'<button style="background:{p};color:{inv};border:none;padding:15px 36px;border-radius:{br};{body};font-size:14px;font-weight:700;cursor:pointer">Voir les tarifs →</button>'
        f'</div></section>'
    )

    footer = (
        f'<footer style="padding:40px 48px;background:{fg};display:flex;'
        f'justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">'
        f'<span style="font-family:\'{hf}\',serif;font-size:.9rem;font-weight:700;color:{inv}">{name}</span>'
        f'<div style="display:flex;gap:24px">'
        + "".join(f'<a style="{body};font-size:11px;color:{inv}66;cursor:pointer">{k.capitalize()}</a>' for k in kw[:4])
        + f'</div><span style="{body};font-size:11px;color:{inv}44">© 2026 {name}</span></footer>'
    )
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>'
            f'{gf}<style>{reset}{css_str or ""}{responsive}</style></head><body>'
            f'{nav}{hero}{sections_html}{pricing}{footer}</body></html>')


def _render_craft_artisan_page(rc, rng, gf, reset, css_str, responsive):
    """Craft / Artisan — nav centrée, héro immersif matière, pas de pression CTA."""
    p,s,acc,bg,bg2,fg,fg2,bdr = rc["p"],rc["s"],rc["acc"],rc["bg"],rc["bg2"],rc["fg"],rc["fg2"],rc["bdr"]
    name = rc["name"]; kw = rc["kw"] or []; vals = rc["vals"] or []; body = rc["body_css"]
    hf = rc["hf"]; inv = rc["inv"]; br = rc["button_radius"]

    # Nav centrée, logo dominant
    nav_kw = "  ·  ".join(k.capitalize() for k in kw[:4])
    nav = (
        f'<nav style="padding:20px 48px;background:{bg};border-bottom:1px solid {bdr};'
        f'text-align:center">'
        f'<div style="display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:6px">'
        f'{_nav_logo_mark(name, p, inv, 24)}'
        f'<div style="font-family:\'{hf}\',serif;font-size:1.5rem;font-weight:700;'
        f'letter-spacing:-.02em;color:{fg}">{name}</div>'
        f'</div>'
        f'<div style="{body};font-size:10px;color:{fg2};letter-spacing:.18em;text-transform:uppercase">{nav_kw}</div>'
        f'</nav>'
    )

    # Hero plein-largeur immersif (image + overlay doux)
    img_seed = rng.randint(10, 990)
    hero = (
        f'<section style="position:relative;min-height:640px;display:flex;align-items:flex-end;overflow:hidden">'
        f'<img src="https://picsum.photos/seed/{img_seed}/1400/900" '
        f'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;'
        f'filter:grayscale(.05) contrast(1.05)" loading="lazy"/>'
        f'<div style="position:absolute;inset:0;background:{p};mix-blend-mode:color;opacity:.12"></div>'
        f'<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.55) 0%,transparent 55%)"></div>'
        f'<div style="position:relative;z-index:1;max-width:900px;padding:0 64px 72px">'
        f'<div style="{body};font-size:9px;font-weight:700;color:{acc};letter-spacing:.25em;'
        f'text-transform:uppercase;margin-bottom:14px">{(vals[0] if vals else "Fait main").upper()} — Depuis 1987</div>'
        f'<h1 style="font-family:\'{hf}\',serif;font-size:clamp(2.2rem,5vw,4rem);'
        f'font-weight:700;color:#f4f0ea;line-height:1.05;margin-bottom:28px;overflow-wrap:break-word">{rc["h1"]}</h1>'
        f'<a style="{body};font-size:12px;font-weight:700;color:#f4f0ea;letter-spacing:.12em;'
        f'text-transform:uppercase;border-bottom:1px solid #f4f0ea88;padding-bottom:3px;cursor:pointer">'
        f'Découvrir le travail →</a>'
        f'</div>'
        f'</section>'
    )

    rc["_rng"] = rng
    _sec_map = {
        "material_story": _sec_material_story, "process": _sec_process,
        "pull_quote": _sec_pull_quote, "stats": _sec_stats,
        "values_list": _sec_values_list, "manifesto": _sec_manifesto,
    }
    sections_html = "".join(_sec_map[sk](rc) for sk in (rc.get("sections") or []) if sk in _sec_map)

    # Contact section (pas de CTA agressif — prise de contact douce)
    contact = (
        f'<section style="padding:80px 48px;background:{bg2};border-top:1px solid {bdr};text-align:center">'
        f'<div style="{body};font-size:9px;font-weight:700;color:{acc};letter-spacing:.2em;'
        f'text-transform:uppercase;margin-bottom:16px">Atelier & commandes</div>'
        f'<h2 style="font-family:\'{hf}\',serif;font-size:1.6rem;font-weight:700;'
        f'color:{fg};margin-bottom:12px">Une question ? Un projet ?</h2>'
        f'<p style="{body};font-size:13px;color:{fg2};max-width:440px;margin:0 auto 28px;line-height:1.85">'
        f'Nous répondons à chaque message. Les commandes personnalisées sont les bienvenues.</p>'
        f'<a style="display:inline-block;{body};font-size:12px;font-weight:700;color:{p};'
        f'letter-spacing:.1em;text-transform:uppercase;border-bottom:2px solid {p};padding-bottom:3px;cursor:pointer">'
        f'Écrire à l\'atelier →</a>'
        f'</section>'
    )

    footer = (
        f'<footer style="padding:36px 48px;background:{fg};display:flex;'
        f'justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">'
        f'<div style="font-family:\'{hf}\',serif;font-size:1rem;font-weight:700;color:{inv}">{name}</div>'
        f'<div style="{body};font-size:10px;color:{inv}55;letter-spacing:.12em;text-transform:uppercase">'
        f'{" · ".join(k.capitalize() for k in kw[:3])}'
        f'</div>'
        f'<span style="{body};font-size:10px;color:{inv}44">© 2026</span>'
        f'</footer>'
    )
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>'
            f'{gf}<style>{reset}{css_str or ""}{responsive}</style></head><body>'
            f'{nav}{hero}{sections_html}{contact}{footer}</body></html>')


def _render_institution_page(rc, rng, gf, reset, css_str, responsive):
    """Institution / Manifeste — header institutionnel, texte long-form, impact, pas de CTA startup."""
    p,s,acc,bg,bg2,fg,fg2,bdr = rc["p"],rc["s"],rc["acc"],rc["bg"],rc["bg2"],rc["fg"],rc["fg2"],rc["bdr"]
    name = rc["name"]; kw = rc["kw"] or []; vals = rc["vals"] or []; body = rc["body_css"]
    hf = rc["hf"]; inv = rc["inv"]

    year = 2026 - rng.randint(2, 30)
    domain = rng.choice(["Culture","Éducation","Environnement","Société","Recherche","Patrimoine"])

    header = (
        f'<header style="background:{fg};border-bottom:3px solid {p}">'
        f'<div style="padding:12px 48px;border-bottom:1px solid {fg2}33;'
        f'display:flex;justify-content:space-between;align-items:center">'
        f'<span style="{body};font-size:9px;color:{inv}55;letter-spacing:.15em;text-transform:uppercase">'
        f'Fondée en {year} · {domain}</span>'
        f'<div style="display:flex;gap:20px">'
        f'<a style="{body};font-size:9px;color:{inv}55;cursor:pointer;letter-spacing:.1em;text-transform:uppercase">Presse</a>'
        f'<a style="{body};font-size:9px;color:{inv}55;cursor:pointer;letter-spacing:.1em;text-transform:uppercase">Partenaires</a>'
        f'<a style="{body};font-size:9px;color:{acc};cursor:pointer;letter-spacing:.1em;text-transform:uppercase">Nous rejoindre</a>'
        f'</div>'
        f'</div>'
        f'<div style="padding:32px 48px;display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:16px">'
        f'<div>'
        f'<div style="font-family:\'{hf}\',serif;font-size:clamp(1.8rem,4vw,3rem);'
        f'font-weight:700;color:{inv};line-height:1.1;margin-bottom:8px">{name}</div>'
        f'<div style="{body};font-size:12px;color:{inv}66;max-width:480px;line-height:1.6">{rc.get("sub","")}</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div style="{body};font-size:9px;color:{inv}44;text-transform:uppercase;letter-spacing:.12em;margin-bottom:4px">Notre mission</div>'
        f'<div style="font-family:\'{hf}\',serif;font-size:1rem;color:{acc}">{(vals[0] if vals else domain).capitalize()}</div>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;gap:28px;padding:0 48px;border-top:1px solid {fg2}22">'
        + "".join(f'<a style="{body};font-size:10px;color:{inv}66;padding:10px 0;'
                  f'border-bottom:2px solid {""+acc if i==0 else "transparent"};cursor:pointer;letter-spacing:.06em">'
                  f'{k.capitalize()}</a>' for i,k in enumerate(kw[:5]))
        + f'</div></header>'
    )

    # Manifeste (grande déclaration, long-form)
    manifesto_text = rc["h1"]
    manifesto = (
        f'<section style="padding:80px 0;background:{bg}'
        f';border-bottom:1px solid {bdr}">'
        f'<div style="max-width:760px;margin:0 auto;padding:0 48px">'
        f'<div style="width:32px;height:3px;background:{p};margin-bottom:28px"></div>'
        f'<h2 style="font-family:\'{hf}\',serif;font-size:clamp(1.8rem,4vw,3rem);'
        f'font-weight:300;font-style:italic;color:{fg};line-height:1.3;margin-bottom:32px">'
        f'"{manifesto_text}"</h2>'
        f'<p style="{body};font-size:14px;color:{fg2};line-height:2;max-width:640px">'
        f'{rc.get("sub","")} {(" ".join(vals[:2]) + "." if vals else "")}'
        f'</p>'
        f'</div>'
        f'</section>'
    )

    rc["_rng"] = rng
    _sec_map = {
        "stats": _sec_stats, "values_list": _sec_values_list, "pull_quote": _sec_pull_quote,
        "manifesto": _sec_manifesto, "logo_wall": _sec_logo_wall, "process": _sec_process,
    }
    sections_html = "".join(_sec_map[sk](rc) for sk in (rc.get("sections") or [])
                            if sk in _sec_map and sk != "manifesto")  # pas de doublon

    # Section presse / contact institutionnel
    press = (
        f'<section style="padding:64px 48px;background:{bg2};border-top:1px solid {bdr}">'
        f'<div style="max-width:960px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:64px;align-items:start">'
        f'<div>'
        f'<div style="{body};font-size:9px;font-weight:700;color:{acc};letter-spacing:.2em;text-transform:uppercase;margin-bottom:12px">Contact presse</div>'
        f'<p style="{body};font-size:13px;color:{fg2};line-height:1.85;margin-bottom:16px">'
        f'Pour toute demande d\'interview, de partenariat ou de dossier de presse.</p>'
        f'<a style="{body};font-size:12px;font-weight:700;color:{p};cursor:pointer">presse@{name.lower().replace(" ","")}.org →</a>'
        f'</div>'
        f'<div>'
        f'<div style="{body};font-size:9px;font-weight:700;color:{acc};letter-spacing:.2em;text-transform:uppercase;margin-bottom:12px">Nous soutenir</div>'
        f'<p style="{body};font-size:13px;color:{fg2};line-height:1.85;margin-bottom:16px">'
        f'Votre soutien est essentiel à notre indépendance et à la poursuite de notre mission.</p>'
        f'<a style="{body};font-size:12px;font-weight:700;color:{p};cursor:pointer">Faire un don →</a>'
        f'</div>'
        f'</div>'
        f'</section>'
    )

    footer = (
        f'<footer style="padding:36px 48px;background:{fg};border-top:3px solid {p};'
        f'display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">'
        f'<div>'
        f'<div style="font-family:\'{hf}\',serif;font-size:1rem;font-weight:700;color:{inv}">{name}</div>'
        f'<div style="{body};font-size:10px;color:{inv}44">Fondée en {year} · {domain}</div>'
        f'</div>'
        f'<div style="display:flex;gap:20px">'
        + "".join(f'<a style="{body};font-size:10px;color:{inv}55;cursor:pointer">{k.capitalize()}</a>' for k in kw[:4])
        + f'</div>'
        f'<span style="{body};font-size:10px;color:{inv}33">© 2026 {name} — Tous droits réservés</span>'
        f'</footer>'
    )
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>'
            f'{gf}<style>{reset}{css_str or ""}{responsive}</style></head><body>'
            f'{header}{manifesto}{sections_html}{press}{footer}</body></html>')


def _inject_audit_tags(html: str) -> str:
    """Injecte data-audit sur les zones clés après rendu (nav, hero, sections, final_cta).
    Approche post-processing : ne touche pas aux renderers individuels.
    """
    body_start = html.find("<body>")
    if body_start == -1:
        return html

    # nav → data-audit="nav" sur le premier <nav
    nav_pos = html.find("<nav ", body_start)
    if nav_pos != -1:
        html = html[:nav_pos] + '<nav data-audit="nav" ' + html[nav_pos + 5:]
        # recalibrer body_start après insertion
        body_start = html.find("<body>")

    # Trouver toutes les <section dans le body
    sections = []
    search_from = html.find("<body>")
    while True:
        pos = html.find("<section ", search_from)
        if pos == -1:
            break
        sections.append(pos)
        search_from = pos + 1

    if sections:
        # hero = première section
        pos = sections[0]
        html = html[:pos] + '<section data-audit="hero" ' + html[pos + 9:]
        # Recalculer les positions (décalage +18 pour 'data-audit="hero" ')
        offset = len('data-audit="hero" ')
        sections = [s + offset if s > pos else s for s in sections]

        # first_section = deuxième section (première après hero)
        if len(sections) >= 2:
            pos = sections[1]
            html = html[:pos] + '<section data-audit="first_section" ' + html[pos + 9:]
            offset = len('data-audit="first_section" ')
            sections = [s + offset if s > pos else s for s in sections]

        # final_cta = dernière section (si différente du hero) — à taguer EN PREMIER
        # pour qu'elle ne reçoive pas de tag section-N
        last_idx = len(sections) - 1
        if last_idx >= 1:
            pos = sections[last_idx]
            html = html[:pos] + '<section data-audit="final_cta" ' + html[pos + 9:]
            offset = len('data-audit="final_cta" ')
            sections = [s + offset if s > pos else s for s in sections]

        # section-1/2/3 sur les sections 2, 3, 4 (hors dernière déjà taguée final_cta)
        for idx, label in enumerate(["section-1", "section-2", "section-3"], start=2):
            if idx < last_idx:  # exclure la dernière (final_cta)
                pos = sections[idx]
                attr = f'data-audit="{label}" '
                html = html[:pos] + f'<section {attr}' + html[pos + 9:]
                offset = len(f'<section {attr}') - 9
                sections = [s + offset if s > pos else s for s in sections]

    return html


# ─────────────────────────────────────────────────────────────────────────────
# TOOL PAGE RENDERER — ToolPage RenderContract v1
# Zones: header_zone / input_zone (sidebar) / execution_zone (tabs) / output_zone
# Renderer = pure translator. No decisions. Exception si RC invalide.
# ─────────────────────────────────────────────────────────────────────────────

def _render_tool_page(rc, rng, gf, reset_css, extra_css, responsive_css):
    """
    Renderer ToolPage — traduit le RenderContract en HTML.
    Signature identique aux family renderers.
    Sidebar blanche avec accordéon, logo en couleurs, header avec couleur primaire.
    Zones data-attributes conformes au RenderContract ToolPage v1.
    """
    import os as _os
    import re as _re

    # ── Design tokens depuis RC ───────────────────────────────────────────────
    primary   = rc.get("p",   "#527FB3")
    bg        = rc.get("bg",  "#f7f8fa")
    text_col  = rc.get("fg",  rc.get("text", "#1a2535"))
    bdr       = rc.get("bdr", "#dde2ea")
    hf        = rc.get("hf",  "Inter, system-ui, sans-serif")
    bf        = rc.get("bf",  "Inter, system-ui, sans-serif")
    name      = rc.get("name", "Outil")

    # Sidebar blanche, header couleur primaire
    sidebar_bg    = "#ffffff"
    sidebar_bdr   = bdr                          # bordure droite sidebar
    sidebar_text  = text_col                     # texte sombre sur blanc
    sidebar_muted = _enforce_contrast(           # texte secondaire lisible
        _hsl_to_hex(*(_hex_to_hsl(primary)[:2] + (0.48,))), sidebar_bg, 3.5
    )
    active_bg     = primary + "12"              # teinte très légère sur item actif
    active_text   = primary                     # texte coloré sur item actif
    header_bg     = primary
    on_header     = _enforce_contrast("#ffffff", header_bg)

    # KPI card
    card_surface  = "#ffffff"
    card_border   = bdr

    # ── Context data ─────────────────────────────────────────────────────────
    ctx_data      = rc.get("ctx", {})
    tool_sections = ctx_data.get("tool_sections") or []
    logo_path     = ctx_data.get("logo_path", "")
    home_url      = ctx_data.get("home_url", "")

    # ── Logo SVG inline — couleurs naturelles sur fond blanc ─────────────────
    logo_html = ""
    if logo_path and _os.path.exists(logo_path):
        try:
            with open(logo_path, "r", encoding="utf-8") as _f:
                _svg_raw = _f.read()
            _svg_raw = _re.sub(r'<\?xml[^?]*\?>', '', _svg_raw)
            _svg_raw = _re.sub(r'<!DOCTYPE[^>]*>', '', _svg_raw).strip()
            if 'preserveAspectRatio' not in _svg_raw:
                _svg_raw = _svg_raw.replace('<svg ', '<svg preserveAspectRatio="xMidYMid meet" ', 1)
            _svg_raw = _re.sub(r'\s*width="[^"]*"', '', _svg_raw, count=1)
            _svg_raw = _re.sub(r'\s*height="[^"]*"', '', _svg_raw, count=1)
            _svg_raw = _svg_raw.replace('<svg ', '<svg width="156" height="44" ', 1)
            _logo_inner = (
                f'<a href="{home_url}" title="Accéder au site" '
                f'style="display:block;line-height:0">{_svg_raw}</a>'
                if home_url else _svg_raw
            )
            logo_html = (
                f'<div data-zone="logo" style="padding:16px 16px 14px;'
                f'border-bottom:1px solid {bdr}">'
                f'{_logo_inner}'
                f'</div>'
            )
        except Exception:
            _fb = f'<a href="{home_url}" style="color:{primary};text-decoration:none">{name}</a>' if home_url else name
            logo_html = (
                f'<div data-zone="logo" style="padding:18px 16px 14px;'
                f'border-bottom:1px solid {bdr};font-family:{hf};'
                f'font-size:1rem;font-weight:700;color:{primary}">{_fb}</div>'
            )
    else:
        _fb = f'<a href="{home_url}" style="color:{primary};text-decoration:none">{name}</a>' if home_url else name
        logo_html = (
            f'<div data-zone="logo" style="padding:18px 16px 14px;'
            f'border-bottom:1px solid {bdr};font-family:{hf};'
            f'font-size:1rem;font-weight:700;color:{primary}">{_fb}</div>'
        )

    # ── Accordéon sidebar — sections + sous-pages ─────────────────────────────
    # Structure attendue dans tool_sections :
    # { id, label, icon, children: [{id, label, href?}], kpis, rows }
    # href présent → lien direct vers page externe (admin route)
    # href absent  → panel interne (rendered in cockpit)
    # Clic section header → ouvre accordéon + navigue vers premier enfant
    _first_panel = None
    nav_items_html = ""
    for _i, _sec in enumerate(tool_sections):
        _sid      = _sec.get("id", f"sec_{_i}")
        _slabel   = _sec.get("label", _sid)
        _sicon    = _sec.get("icon", "")
        _children = _sec.get("children", [])
        if not _children:
            _children = [{"id": _sid, "label": _slabel}]

        # Premier child interne (sans href) = panel cible du clic section
        _first_internal = next((c for c in _children if not c.get("href")), _children[0])
        _first_cid = _first_internal.get("id", _sid)
        if _first_panel is None:
            _first_panel = _first_cid

        # ── Accordéon header ─────────────────────────────────────────────────
        nav_items_html += (
            f'<div class="acc-section" data-acc="{_sid}">\n'
            f'  <button class="acc-header" '
            f'data-acc-toggle="{_sid}" data-acc-first="{_first_cid}" '
            f'style="width:100%;display:flex;align-items:center;gap:8px;'
            f'padding:10px 16px;border:none;background:none;cursor:pointer;'
            f'font-family:{bf};font-size:0.82rem;font-weight:600;color:{sidebar_text};'
            f'text-align:left;transition:color .15s">'
            f'  <span style="font-size:0.95rem;flex-shrink:0">{_sicon}</span>'
            f'  <span style="flex:1">{_slabel}</span>'
            f'  <span class="acc-caret" data-caret="{_sid}" '
            f'style="font-size:0.65rem;color:{sidebar_muted};transition:transform .2s;'
            f'display:inline-block;transform:rotate(0deg)'
            f'">▶</span>'
            f'  </button>\n'
        )

        # ── Sous-pages ────────────────────────────────────────────────────────
        _display = "none"  # tous fermés par défaut
        nav_items_html += f'  <div class="acc-body" data-acc-body="{_sid}" style="display:{_display}">\n'
        for _ci, _child in enumerate(_children):
            _cid    = _child.get("id", f"{_sid}_c{_ci}")
            _clabel = _child.get("label", _cid)
            _chref  = _child.get("href", "")
            _is_first = False  # aucun item actif au chargement
            _active_s = (
                f"background:{active_bg};color:{active_text};font-weight:600;"
                f"border-left:2px solid {primary}"
            ) if _is_first and not _chref else (
                f"color:{sidebar_muted};border-left:2px solid transparent"
            )
            if _chref:
                # Lien externe → ouvre la vraie page admin
                nav_items_html += (
                    f'    <a href="{_chref}" target="_top" '
                    f'style="display:block;padding:7px 16px 7px 38px;'
                    f'font-family:{bf};font-size:0.78rem;text-decoration:none;cursor:pointer;'
                    f'transition:background .12s,color .12s;{_active_s}">'
                    f'{_clabel} <span style="font-size:0.6rem;opacity:.5">↗</span>'
                    f'</a>\n'
                )
            else:
                nav_items_html += (
                    f'    <a href="#" data-tab="{_cid}" '
                    f'{"data-active=\"true\" " if _is_first else ""}'
                    f'style="display:block;padding:7px 16px 7px 38px;'
                    f'font-family:{bf};font-size:0.78rem;text-decoration:none;cursor:pointer;'
                    f'transition:background .12s,color .12s,border-left-color .12s;{_active_s}">'
                    f'{_clabel}'
                    f'</a>\n'
                )
        nav_items_html += '  </div>\n</div>\n'

    # ── Panels (output_zone) — un panel par child + un par section sans children ──
    panels_html = ""
    for _i, _sec in enumerate(tool_sections):
        _sid      = _sec.get("id", f"sec_{_i}")
        _kpis     = _sec.get("kpis", [])
        _rows     = _sec.get("rows", [])
        _children = _sec.get("children", [])

        # Panels enfants — partagent KPIs/rows de la section parente
        if not _children:
            _children = [{"id": _sid, "label": _sec.get("label", _sid)}]

        for _ci, _child in enumerate(_children):
            _cid    = _child.get("id", f"{_sid}_c{_ci}")
            _clabel = _child.get("label", _cid)
            _is_active = False  # aucun panel actif au chargement
            _hidden = "" if _is_active else ' style="display:none"'

            # KPIs — seulement sur le premier sous-panel de chaque section
            _kpi_html = ""
            if _ci == 0 and _kpis:
                for _kpi in _kpis:
                    _kval   = _kpi.get("value", "—")
                    _klabel = _kpi.get("label", "")
                    _kdelta = _kpi.get("delta", "")
                    _dc = "#16a34a" if str(_kdelta).startswith("+") else ("#dc2626" if str(_kdelta).startswith("-") else sidebar_muted)
                    _dhtml = (
                        f'<span style="font-size:0.71rem;color:{_dc};margin-top:3px;font-weight:500">'
                        f'{_kdelta}</span>'
                    ) if _kdelta else ""
                    _kpi_html += (
                        f'<div style="background:{card_surface};border:1px solid {card_border};'
                        f'border-radius:8px;padding:18px 16px;display:flex;flex-direction:column;gap:4px;'
                        f'border-top:3px solid {primary}">'
                        f'<span style="font-family:{bf};font-size:0.68rem;text-transform:uppercase;'
                        f'letter-spacing:.1em;color:{sidebar_muted};font-weight:600">{_klabel}</span>'
                        f'<span style="font-family:{hf};font-size:1.65rem;font-weight:700;'
                        f'color:{text_col};line-height:1.1">{_kval}</span>'
                        f'{_dhtml}'
                        f'</div>\n'
                    )
                _kpi_grid = (
                    f'<div data-zone="kpi_grid" '
                    f'style="display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));'
                    f'gap:12px;margin-bottom:28px">\n{_kpi_html}</div>'
                )
            else:
                _kpi_grid = ""

            # Table — seulement sur le premier sous-panel si rows fournis
            _table_html = ""
            if _ci == 0 and _rows:
                _headers = list(_rows[0].keys())
                _th_html = "".join(
                    f'<th style="padding:9px 14px;text-align:left;font-family:{bf};'
                    f'font-size:0.68rem;font-weight:600;text-transform:uppercase;'
                    f'letter-spacing:.07em;color:{sidebar_muted};'
                    f'border-bottom:1px solid {bdr};background:{bg}">'
                    f'{_hk.replace("_"," ").capitalize()}</th>'
                    for _hk in _headers
                )
                _tr_html = ""
                for _ri, _r in enumerate(_rows):
                    _row_bg = "background:#f9fafb" if _ri % 2 == 1 else ""
                    _td_html = "".join(
                        f'<td style="padding:9px 14px;font-family:{bf};font-size:0.82rem;'
                        f'color:{text_col};border-bottom:1px solid {bdr}55;{_row_bg}">'
                        f'{_r.get(_hk,"")}</td>'
                        for _hk in _headers
                    )
                    _tr_html += f'<tr>{_td_html}</tr>\n'
                _table_html = (
                    f'<div style="background:{card_surface};border:1px solid {card_border};'
                    f'border-radius:8px;overflow:hidden;margin-top:4px">'
                    f'<table style="width:100%;border-collapse:collapse">'
                    f'<thead><tr>{_th_html}</tr></thead>'
                    f'<tbody>{_tr_html}</tbody>'
                    f'</table></div>'
                )

            _breadcrumb = (
                f'<div style="font-family:{bf};font-size:0.72rem;color:{sidebar_muted};'
                f'margin-bottom:8px">'
                f'<span style="color:{primary};font-weight:500">{_sec.get("label","")}</span>'
                f' › {_clabel}</div>'
            )
            _section_title = (
                f'<h2 style="font-family:{hf};font-size:1.05rem;font-weight:700;'
                f'color:{text_col};margin-bottom:20px;padding-bottom:10px;'
                f'border-bottom:1px solid {bdr}">{_clabel}</h2>'
            )

            panels_html += (
                f'<div id="panel-{_cid}" data-panel="{_cid}"{_hidden} '
                f'style="padding:28px 32px;flex:1;overflow-y:auto;min-width:0" '
                f'data-zone="output_zone">\n'
                f'{_breadcrumb}\n{_section_title}\n{_kpi_grid}\n{_table_html}\n'
                f'</div>\n'
            )

    # ── JS — accordéon + navigation tabs ─────────────────────────────────────
    js = f"""
<script>
(function() {{
  var primary = '{primary}';
  var activeText = '{active_text}';
  var mutedText = '{sidebar_muted}';
  var activeBg = '{active_bg}';
  var sidebarText = '{sidebar_text}';
  var bdr = '{bdr}';

  // ── Accordéon — toggle : ferme si ouvert, ouvre + navigue si fermé ──────────
  document.querySelectorAll('[data-acc-toggle]').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      var sid      = btn.getAttribute('data-acc-toggle');
      var firstCid = btn.getAttribute('data-acc-first');
      var body     = document.querySelector('[data-acc-body="' + sid + '"]');
      var caret    = document.querySelector('[data-caret="' + sid + '"]');
      if (!body) return;
      var isOpen = body.style.display !== 'none';
      if (isOpen) {{
        // Fermer
        body.style.display = 'none';
        if (caret) caret.style.transform = 'rotate(0deg)';
      }} else {{
        // Ouvrir + naviguer vers premier panel interne
        body.style.display = 'block';
        if (caret) caret.style.transform = 'rotate(90deg)';
        if (firstCid) {{
          var target = document.querySelector('[data-tab="' + firstCid + '"]');
          if (target) target.click();
        }}
      }}
    }});
  }});

  // ── Navigation tabs ────────────────────────────────────────────────────────
  document.querySelectorAll('[data-tab]').forEach(function(tab) {{
    tab.addEventListener('click', function(e) {{
      e.preventDefault();
      var id = tab.getAttribute('data-tab');

      // Réinitialiser tous les onglets
      document.querySelectorAll('[data-tab]').forEach(function(t) {{
        var isActive = t.getAttribute('data-tab') === id;
        t.style.background = isActive ? activeBg : '';
        t.style.color = isActive ? activeText : mutedText;
        t.style.fontWeight = isActive ? '600' : '400';
        t.style.borderLeftColor = isActive ? primary : 'transparent';
        if (isActive) t.setAttribute('data-active', 'true');
        else t.removeAttribute('data-active');
      }});

      // Afficher le panel correspondant
      document.querySelectorAll('[data-panel]').forEach(function(p) {{
        p.style.display = p.getAttribute('data-panel') === id ? '' : 'none';
      }});

      // Mettre à jour le breadcrumb dans le header
      var headerLabel = document.getElementById('header-label');
      if (headerLabel) {{
        var activeLink = document.querySelector('[data-tab="' + id + '"]');
        if (activeLink) headerLabel.textContent = activeLink.textContent.trim();
      }}
    }});
  }});
}})();
</script>"""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} — Dashboard</title>
{gf}
<style>
{reset_css}
html,body{{height:100%;margin:0;padding:0;font-family:{bf}}}
*{{box-sizing:border-box}}
.acc-header:hover{{color:{primary}!important}}
[data-tab]:hover{{background:{active_bg}!important;color:{active_text}!important}}
{extra_css}
</style>
</head>
<body style="display:flex;height:100vh;overflow:hidden;background:{bg}" data-page-type="tool">

<!-- SIDEBAR — input_zone -->
<aside data-zone="input_zone"
  style="width:220px;min-width:220px;background:{sidebar_bg};
         border-right:1px solid {sidebar_bdr};
         display:flex;flex-direction:column;height:100vh;
         overflow-y:auto;overflow-x:hidden;flex-shrink:0">
  {logo_html}
  <nav data-zone="nav" style="padding:8px 0;flex:1">
    {nav_items_html}
  </nav>
  <div style="padding:10px 16px;border-top:1px solid {bdr};
              font-family:{bf};font-size:0.68rem;color:{sidebar_muted}">
    {name} — Admin
  </div>
</aside>

<!-- MAIN -->
<div style="flex:1;display:flex;flex-direction:column;min-width:0;height:100vh">

  <!-- HEADER — header_zone -->
  <header data-zone="header_zone"
    style="height:50px;background:{header_bg};
           display:flex;align-items:center;padding:0 24px;gap:12px;flex-shrink:0">
    <span id="header-label"
      style="font-family:{bf};font-size:0.8rem;font-weight:600;
             color:{on_header};letter-spacing:.03em">Dashboard</span>
    <span style="margin-left:auto;font-family:{bf};font-size:0.72rem;
                 color:{on_header};opacity:0.65">Administration</span>
  </header>

  <!-- CONTENT — execution_zone -->
  <div data-zone="execution_zone"
    style="flex:1;display:flex;overflow:hidden;background:{bg}">
    {panels_html}
  </div>

</div>

{js}
</body>
</html>"""

    return html


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR v2
# ─────────────────────────────────────────────────────────────────────────────

def _lp_dynamic_page(ctx: dict, css: str, palette_output=None, harmony: str = "complementary",
                     page_type: str = "landing", site_family: str = "",
                     cp_palette: dict | None = None,
                     variant_index: int = -1,
                     plan=None) -> str:
    import random as _rnd

    seed = ctx.get("render_seed", 42)
    rng  = _rnd.Random(seed)

    # ── Step 0: SITE TYPE RESOLUTION ─────────────────────────────────────────
    # Structure is determined BEFORE art direction styling
    _site_family = site_family or ctx.get("site_family") or site_type_resolver(
        ctx.get("brief_text", "")
    )

    # ── Step 1: ART DIRECTION ─────────────────────────────────────────────────
    ad = _build_art_direction(ctx, rng)

    # ── Step 2: PALETTE ───────────────────────────────────────────────────────
    # Priority: Color Palette Engine > palette_output > internal build
    if cp_palette is not None:
        pal = _pal_safe(_pal_from_color_palette_engine(cp_palette))
    elif palette_output is not None:
        pal = _pal_from_palette_output(ad, palette_output, harmony, rng)
    else:
        base_hex = ctx.get("primary", "#2563eb")
        pal = _build_palette(ad, base_hex, rng)

    # ── Step 3: TYPOGRAPHY ────────────────────────────────────────────────────
    typo = _build_typography(ad, pal, rng)

    # ── Step 4: RENDERING CONTRACT ────────────────────────────────────────────
    rc = _build_rendering_contract(ad, pal, typo, ctx, rng)

    # ── Step 4b: LAYOUT BLUEPRINT (site family → RC structure baseline) ──────
    blueprint = layout_blueprint_generator(_site_family, page_type, rng,
                                           variant_index=variant_index)
    rc["hero_pattern"] = blueprint["hero"]
    rc["sections"]     = blueprint["sections"]
    rc["_no_cta_band"] = blueprint["no_cta_band"]
    rc["_site_family"] = _site_family
    # CTA text overrides for non-landing page types
    if page_type == "about":
        rc["cta_p"] = f"Travailler avec {rc['name']}"
        rc["cta_s"] = ""

    # ── Step 4c: DESIGN PLAN ENFORCEMENT (écrase blueprint si plan fourni) ───
    # Le plan est la SOURCE DE VÉRITÉ. Blueprint = baseline seulement.
    if plan is not None:
        rc = plan.apply_to_rc(rc)

    # ── Step 5: COHERENCE VALIDATION ─────────────────────────────────────────
    assert rc.get("h1"),         "RC error: h1 missing"
    assert rc.get("hero_pattern"), "RC error: hero_pattern missing"
    assert rc.get("p"),          "RC error: primary color missing"
    assert rc.get("hf"),         "RC error: display font missing"
    assert rc.get("sections"),   "RC error: section list empty"

    # ── Step 6: RENDER ────────────────────────────────────────────────────────
    gf   = f'<link rel="stylesheet" href="{typo["gf_url"]}">' if typo.get("gf_url") else ""

    # CSS variables block — single source of truth for all palette tokens
    _css_vars = _build_css_vars(pal)

    # Reset uses CSS vars — no inline color literals
    _reset = (_css_vars
              + "*{box-sizing:border-box;margin:0;padding:0}"
              "body{background:var(--color-bg);color:var(--color-text);-webkit-font-smoothing:antialiased}"
              "img{max-width:100%}a{text-decoration:none}")
    _responsive = (
        "body{overflow-x:hidden}"
        "h1,h2,h3{overflow-wrap:break-word!important;max-width:100%!important}"
        "section,nav,footer,header{max-width:100vw;overflow:hidden}"
        "@media(max-width:900px){"
        "[style*='padding:0 48px']{padding-left:20px!important;padding-right:20px!important}"
        "[style*='padding:0 48px 64px']{padding-left:20px!important;padding-right:20px!important}"
        "[style*='grid-template-columns:1fr 1fr']{grid-template-columns:1fr!important}"
        "[style*='grid-template-columns:repeat(2,1fr)']{grid-template-columns:1fr!important}"
        "[style*='grid-template-columns:repeat(3,1fr)']{grid-template-columns:1fr!important}"
        "[style*='grid-template-columns:repeat(4,1fr)']{grid-template-columns:1fr!important}"
        "[style*='grid-template-columns:55% 45%']{grid-template-columns:1fr!important}"
        "[style*='grid-template-columns:58% 42%']{grid-template-columns:1fr!important}"
        "[style*='grid-template-columns:50% 50%']{grid-template-columns:1fr!important}"
        "[style*='grid-template-columns:60%']{grid-template-columns:1fr!important}"
        "[style*='grid-template-columns:62%']{grid-template-columns:1fr!important}"
        "[style*='grid-template-columns:65%']{grid-template-columns:1fr!important}"
        "[style*='grid-template-columns:70%']{grid-template-columns:1fr!important}"
        "[style*='min-height:560px']{min-height:320px!important}"
        "[style*='min-height:580px']{min-height:320px!important}"
        "[style*='min-height:640px']{min-height:380px!important}"
        "[style*='min-height:88vh']{min-height:60vh!important}"
        "[style*='min-height:85vh']{min-height:55vh!important}"
        "[style*='min-height:80vh']{min-height:55vh!important}"
        "nav [style*='display:flex;gap:28px']{display:none!important}"
        "nav [style*='display:flex;gap:20px']{display:none!important}"
        "nav [style*='display:flex;gap:32px']{display:none!important}"
        "[style*='padding-left:40px']{padding-left:0!important}"
        "[style*='padding-left:60px']{padding-left:0!important}"
        "[style*='padding-left:80px']{padding-left:0!important}"
        "[style*='padding:100px 60px']{padding:60px 20px!important}"
        "[style*='padding:100px 64px']{padding:60px 20px!important}"
        "[style*='padding:48px']{padding:28px 20px!important}"
        "[style*='padding:56px 48px']{padding:36px 20px!important}"
        "h1{font-size:clamp(1.7rem,8vw,2.6rem)!important;line-height:1.08!important}"
        "h2{font-size:clamp(1.1rem,4vw,1.6rem)!important;line-height:1.2!important}"
        "h3{font-size:1rem!important;line-height:1.35!important}"
        "p{font-size:0.875rem!important;line-height:1.65!important}"
        "section{padding-top:48px!important;padding-bottom:48px!important}"
        "[style*='font-size:2.2rem']{font-size:1.5rem!important}"
        "[style*='font-size:3rem']{font-size:2rem!important}"
        "[style*='font-size:4rem']{font-size:2.2rem!important}"
        "[style*='font-size:5rem']{font-size:2.5rem!important}"
        "}"
    )

    # DA enforcement layer — compute once, inject into every renderer
    _sp_rc       = _build_spacing_system(ad)
    _dec_rc      = rc.get("decorators") or _get_decorators_graceful(ad)
    _mono_rc     = rc.get("is_mono", False)
    _da_css      = _build_da_css(ad, pal, _sp_rc, _dec_rc, _mono_rc)

    # Accent enforcement CSS — hover states + utility classes (DNA-derived, not arbitrary)
    _acc_enf_css = _build_accent_enforcement_css(pal, rc)

    # Pictogrammes SVG — injectés dans rc pour les feature sections
    if _pictogram_ok and _gen_pictograms and not rc.get("pictograms"):
        try:
            _arch = ad.get("archetype", "startup_clean")
            _pict = _gen_pictograms(_arch, color=pal["p"])
            rc["pictograms"] = _pict
        except Exception:
            rc["pictograms"] = None

    # ── TOOL PAGE — intercept avant family dispatch ───────────────────────────
    # Note: _da_css / _acc_enf_css sont des décorateurs landing page —
    # non injectés ici (introduisent accent rouge + radial bg non souhaités).
    if page_type == "tool":
        html = _render_tool_page(rc, rng, gf, _reset, css or "", _responsive)
        _validation = _validate_page(html)
        html = _embed_page_meta(html, rc, ad, _validation)
        return html

    # Dispatch vers renderer famille-specific — TOUS les types sont ex nihilo
    _family_renderers = {
        "brand_landing":       _render_brand_landing_page,
        "editorial_magazine":  _render_editorial_page,
        "studio_portfolio":    _render_studio_page,
        "product_saas":        _render_product_saas_page,
        "craft_artisan":       _render_craft_artisan_page,
        "ecommerce_catalog":   _render_ecommerce_page,
        "event_campaign":      _render_event_page,
        "institution_manifesto": _render_institution_page,
    }
    renderer = _family_renderers.get(_site_family, _render_brand_landing_page)
    html = renderer(rc, rng, gf, _reset, (css or "") + _da_css + _acc_enf_css, _responsive)

    # ── HARD-FIX: Post-render visual signature enforcement ────────────────────
    # 1. Inject dividers between every section transition
    _div_html = _build_divider_html(_dec_rc, pal, ad.get("attitude", "product"))
    html = html.replace("</section><section", f"</section>{_div_html}<section")
    html = html.replace("</section>\n<section", f"</section>\n{_div_html}\n<section")

    # 2. Inject glyph strip in hero if no SVG present in first section
    _hero_end       = html.find("</section>")
    _has_svg_hero   = "<svg" in (html[:_hero_end] if _hero_end != -1 else html[:3000])
    if not _has_svg_hero:
        _glyph  = _build_glyph_strip(rc)
        _h1_pos = html.find("<h1 ")
        if _h1_pos != -1:
            html = html[:_h1_pos] + _glyph + html[_h1_pos:]

    # 3. Validate — warn if required elements still missing
    _validation = _validate_page(html)
    if _validation["warnings"]:
        print(f"[page_validate] ⚠ {_validation['warnings']}")

    # 4. Embed metadata comment for UI consumption
    html = _embed_page_meta(html, rc, ad, _validation)

    return _inject_audit_tags(html)

# ── Public API ────────────────────────────────────────────────────────────────

def generate_landing_page(
    project_name: str,
    brief_text: str,
    dna,
    exploration,
    preset: dict | None,
    css: str | None,
    render_seed: int = 42,
    palette_output=None,
    harmony: str = "complementary",
    page_type: str = "landing",
    site_family: str = "",
    cp_palette: dict | None = None,
    plan=None,
    tool_sections: list | None = None,
    logo_path: str = "",
    home_url: str = "",
) -> str:
    """
    Design Instantiation Engine — generates a fully unique page.
    brief → site_type_resolver → layout_blueprint → art_direction → render.

    page_type:   "landing" | "about" | "product" | "minimal"
    site_family: "brand_landing" | "editorial_magazine" | "studio_portfolio"
                 | "product_saas" | "craft_artisan" | "ecommerce_catalog"
                 | "event_campaign" | "institution_manifesto" | "" (auto-detect)
    cp_palette:  Color Palette Engine output dict (primary/secondary/accent/background/
                 surface/text_primary/text_secondary/border/states/contrast_score).
                 When provided, overrides palette_output and internal palette build.
                 All colors become fully traceable to this palette.
    plan:        DesignPlan — source de vérité structurelle. Quand fourni, son
                 layout_strategy / hero.type / section_types s'imposent au renderer.
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
    if tool_sections is not None:
        ctx["tool_sections"] = tool_sections
    if logo_path:
        ctx["logo_path"] = logo_path
    if home_url:
        ctx["home_url"] = home_url

    return _lp_dynamic_page(ctx, css or "", palette_output=palette_output, harmony=harmony,
                            page_type=page_type, site_family=site_family,
                            cp_palette=cp_palette, plan=plan)


# ── SCSS Generator ────────────────────────────────────────────────────────────

def generate_scss(project_name: str, style_dna, preset: dict | None) -> str:
    """
    Generates structured SCSS — primary developer deliverable.
    Output: design tokens as Sass variables + CSS custom properties + base components.
    Compile with: sass theme.scss theme.compiled.css
    """
    cs       = (preset or {}).get("color_system", {})
    primary  = cs.get("primary",   {}).get("base",  "#2563eb")
    prim_lt  = cs.get("primary",   {}).get("light", "#93b4f0")
    prim_dk  = cs.get("primary",   {}).get("dark",  "#1a3a6b")
    secondary= cs.get("secondary", {}).get("base",  "#7c3aed")

    pp      = getattr(style_dna, "palette_profile", None) if style_dna else None
    accent  = (pp.accent[0]  if pp and pp.accent  else "#f97316")
    neutral = (pp.neutral[0] if pp and pp.neutral else "#f4f5f5")

    h_font = (preset or {}).get("font_family_headings", "system-ui")
    b_font = (preset or {}).get("font_family_body",     "system-ui")

    gp = getattr(style_dna, "geometry_profile", None) if style_dna else None

    def _r(none_v, small_v, med_v, large_v):
        if not gp:                              return med_v
        if gp.border_radius == "none":          return none_v
        if gp.border_radius == "small":         return small_v
        if gp.border_radius == "medium":        return med_v
        return large_v

    r_sm   = _r("2px",  "4px",  "8px",  "12px")
    r_md   = _r("3px",  "6px",  "12px", "20px")
    r_lg   = _r("4px",  "8px",  "16px", "28px")
    r_pill = _r("4px",  "6px",  "100px","100px")

    txt_on_primary = text_on(primary)
    archetype = (getattr(style_dna, "aesthetic_tags", ["startup_clean"]) or ["startup_clean"])[0]

    return f"""// ══════════════════════════════════════════════════════════════════════
// {project_name} — Design System (EURKAI generated)
// Archetype: {archetype}
// Compile: sass theme.scss theme.compiled.css
// ══════════════════════════════════════════════════════════════════════


// ─── Colors ──────────────────────────────────────────────────────────
$color-primary:        {primary};
$color-primary-light:  {prim_lt};
$color-primary-dark:   {prim_dk};
$color-secondary:      {secondary};
$color-accent:         {accent};
$color-neutral:        {neutral};
$color-white:          #ffffff;
$color-surface:        #f8f8f8;
$color-border:         rgba(0, 0, 0, 0.08);

// On-color (auto-computed)
$color-on-primary:     {txt_on_primary};


// ─── Typography ──────────────────────────────────────────────────────
$font-heading: '{h_font}', sans-serif;
$font-body:    '{b_font}', sans-serif;
$font-mono:    'JetBrains Mono', 'Fira Code', monospace;

// Scale (Major Third — 1.250)
$type-xs:      0.640rem;  // ~10px
$type-sm:      0.800rem;  // ~13px
$type-base:    1.000rem;  // 16px
$type-lg:      1.250rem;  // 20px
$type-xl:      1.563rem;  // 25px
$type-2xl:     1.953rem;  // 31px
$type-3xl:     2.441rem;  // 39px
$type-4xl:     3.052rem;  // 49px
$type-display: 4.000rem;  // 64px

// Weights
$weight-light:   300;
$weight-regular: 400;
$weight-medium:  500;
$weight-semibold:600;
$weight-bold:    700;
$weight-black:   900;


// ─── Spacing ─────────────────────────────────────────────────────────
$space-1:  4px;
$space-2:  8px;
$space-3:  12px;
$space-4:  16px;
$space-5:  20px;
$space-6:  24px;
$space-8:  32px;
$space-10: 40px;
$space-12: 48px;
$space-16: 64px;
$space-20: 80px;
$space-24: 96px;


// ─── Geometry ────────────────────────────────────────────────────────
$radius-sm:   {r_sm};
$radius-md:   {r_md};
$radius-lg:   {r_lg};
$radius-pill: {r_pill};

$shadow-sm:  0 1px 2px rgba(0, 0, 0, 0.06);
$shadow-md:  0 4px 8px rgba(0, 0, 0, 0.10);
$shadow-lg:  0 10px 24px rgba(0, 0, 0, 0.12);
$shadow-xl:  0 20px 40px rgba(0, 0, 0, 0.15);


// ─── Transitions ─────────────────────────────────────────────────────
$transition-fast:   0.15s ease;
$transition-base:   0.22s ease;
$transition-slow:   0.35s ease;


// ─── Breakpoints ─────────────────────────────────────────────────────
$bp-sm:  640px;
$bp-md:  768px;
$bp-lg:  1024px;
$bp-xl:  1280px;
$bp-2xl: 1440px;


// ══════════════════════════════════════════════════════════════════════
// CSS Custom Properties (runtime tokens)
// ══════════════════════════════════════════════════════════════════════

:root {{
  // Colors
  --color-primary:        #{{$color-primary}};
  --color-primary-light:  #{{$color-primary-light}};
  --color-primary-dark:   #{{$color-primary-dark}};
  --color-secondary:      #{{$color-secondary}};
  --color-accent:         #{{$color-accent}};
  --color-neutral:        #{{$color-neutral}};
  --color-surface:        #{{$color-surface}};
  --color-border:         #{{$color-border}};
  --color-on-primary:     #{{$color-on-primary}};

  // Typography
  --font-heading: #{{$font-heading}};
  --font-body:    #{{$font-body}};
  --font-mono:    #{{$font-mono}};

  // Radii
  --radius-sm:   #{{$radius-sm}};
  --radius-md:   #{{$radius-md}};
  --radius-lg:   #{{$radius-lg}};
  --radius-pill: #{{$radius-pill}};

  // Shadows
  --shadow-sm: #{{$shadow-sm}};
  --shadow-md: #{{$shadow-md}};
  --shadow-lg: #{{$shadow-lg}};
  --shadow-xl: #{{$shadow-xl}};
}}


// ══════════════════════════════════════════════════════════════════════
// Base reset
// ══════════════════════════════════════════════════════════════════════

*,
*::before,
*::after {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

html {{
  font-size: 16px;
  scroll-behavior: smooth;
}}

body {{
  font-family: $font-body;
  font-size: $type-base;
  line-height: 1.6;
  color: #111;
  background: #fff;
  -webkit-font-smoothing: antialiased;
}}


// ══════════════════════════════════════════════════════════════════════
// Components
// ══════════════════════════════════════════════════════════════════════

// ─── Buttons ─────────────────────────────────────────────────────────
.btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: $font-body;
  font-size: $type-sm;
  font-weight: $weight-semibold;
  line-height: 1;
  cursor: pointer;
  border: none;
  text-decoration: none;
  border-radius: $radius-pill;
  padding: 12px 24px;
  transition: transform $transition-fast, box-shadow $transition-fast;
  will-change: transform;

  &:hover  {{ transform: translateY(-2px); }}
  &:active {{ transform: translateY(0); box-shadow: none; }}

  &--primary {{
    background: $color-primary;
    color: $color-on-primary;
    &:hover {{ box-shadow: $shadow-lg; }}
  }}

  &--outline {{
    background: transparent;
    color: $color-primary;
    border: 1.5px solid $color-primary;
    &:hover {{ background: rgba($color-primary, 0.05); }}
  }}

  &--ghost {{
    background: transparent;
    color: $color-primary;
    &:hover {{ background: rgba($color-primary, 0.08); }}
  }}

  &--neutral {{
    background: $color-neutral;
    color: #333;
    &:hover {{ background: darken($color-neutral, 4%); }}
  }}

  &--sm {{ padding: 8px 16px; font-size: $type-xs; }}
  &--lg {{ padding: 16px 32px; font-size: $type-base; }}
}}


// ─── Cards ───────────────────────────────────────────────────────────
.card {{
  border-radius: $radius-lg;
  transition: transform $transition-base, box-shadow $transition-base;

  &:hover {{
    transform: translateY(-4px);
    box-shadow: $shadow-lg;
  }}

  &--bordered {{
    border: 1px solid $color-border;
    background: #fff;
    padding: $space-6;
  }}

  &--filled {{
    background: $color-primary;
    color: $color-on-primary;
    padding: $space-6;
  }}

  &--surface {{
    background: $color-surface;
    padding: $space-6;
  }}
}}


// ─── Container ───────────────────────────────────────────────────────
.container {{
  max-width: 1100px;
  margin-inline: auto;
  padding-inline: $space-8;
}}


// ─── Typography helpers ───────────────────────────────────────────────
.heading-display {{ font-family: $font-heading; font-size: $type-display; font-weight: $weight-black; line-height: 1.05; letter-spacing: -0.02em; }}
.heading-1       {{ font-family: $font-heading; font-size: $type-4xl;    font-weight: $weight-bold;  line-height: 1.1;  letter-spacing: -0.015em; }}
.heading-2       {{ font-family: $font-heading; font-size: $type-3xl;    font-weight: $weight-bold;  line-height: 1.15; letter-spacing: -0.01em; }}
.heading-3       {{ font-family: $font-heading; font-size: $type-2xl;    font-weight: $weight-semibold; line-height: 1.2; }}
.body-lg         {{ font-family: $font-body;    font-size: $type-lg;     line-height: 1.7; color: #333; }}
.body-base       {{ font-family: $font-body;    font-size: $type-base;   line-height: 1.65; color: #444; }}
.body-sm         {{ font-family: $font-body;    font-size: $type-sm;     line-height: 1.6;  color: #555; }}
.label           {{ font-family: $font-mono;    font-size: $type-xs;     letter-spacing: 0.1em; text-transform: uppercase; color: rgba(0,0,0,.4); }}


// ─── Tag / Badge ─────────────────────────────────────────────────────
.tag {{
  display: inline-flex;
  align-items: center;
  font-family: $font-body;
  font-size: $type-xs;
  font-weight: $weight-semibold;
  padding: 4px 10px;
  border-radius: $radius-pill;
  letter-spacing: 0.02em;

  &--primary  {{ background: $color-primary;  color: $color-on-primary; }}
  &--neutral  {{ background: $color-neutral;  color: #444; }}
  &--outlined {{ background: transparent; color: $color-primary; border: 1px solid $color-primary; }}
}}
"""


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
    # SCSS — primary developer deliverable (structured design tokens)
    if preset or style_dna:
        scss = generate_scss(project_name, style_dna, preset)
        if scss:
            (out_dir / "theme.scss").write_text(scss, encoding="utf-8")

    import random as _r
    lp_content = generate_landing_page(
        project_name=project_name, brief_text=brief_text,
        dna=dna, exploration=exploration, preset=preset, css=css,
        render_seed=_r.randint(0, 999999),
    )
    lp_path = out_dir / "landing_page.html"
    lp_path.write_text(lp_content, encoding="utf-8")

    charter_content = generate_html(
        project_name=project_name, brief_text=brief_text,
        dna=dna, rec=rec, palette_output=palette_output,
        exploration=exploration, style_dna=style_dna,
        preset=preset, css=css, pipeline_ok=pipeline_ok,
    )
    charter_path = out_dir / "brand_charter.html"
    charter_path.write_text(charter_content, encoding="utf-8")

    ok_count = sum(1 for v in pipeline_ok.values() if v is True)
    print(f"  ✅ {ok_count}/{len(pipeline_ok)} steps OK → {lp_path}")
    print(f"  📋 Brand charter → {charter_path}")


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
    h = (h or "").lstrip("#").strip()
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    if len(h) != 6:
        return 0.0, 0.0, 0.5
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


def _luminance(hex_str: str) -> float:
    h = (hex_str or "").lstrip("#").strip()
    if not h:
        return 0.0
    if len(h) == 3:                        # expand #rgb → rrggbb
        h = h[0]*2 + h[1]*2 + h[2]*2
    if len(h) < 6:
        return 0.0
    h = h[:6]
    r,g,b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
    def lc(c): return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
    return 0.2126*lc(r) + 0.7152*lc(g) + 0.0722*lc(b)

def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    la, lb = _luminance(hex_a), _luminance(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def _enforce_contrast(fg: str, bg: str, min_ratio: float = 4.5) -> str:
    """Ajuste fg vers blanc ou noir jusqu'à atteindre min_ratio sur bg."""
    if not fg or not bg:
        return fg or "#111111"  # fallback sûr sur vide/None
    if _contrast_ratio(fg, bg) >= min_ratio:
        return fg
    # Choisir la direction : noir ou blanc selon ce qui est le plus loin du bg
    target = "#ffffff" if _luminance(bg) < 0.5 else "#000000"
    # Interpoler fg → target en HSL lightness par pas de 5%
    hh, hs, hl = _hex_to_hsl(fg)
    tl = _hex_to_hsl(target)[2]
    step = 0.05 if tl > hl else -0.05
    for _ in range(20):
        hl = max(0.0, min(1.0, hl + step))
        candidate = _hsl_to_hex(hh, hs, hl)
        if _contrast_ratio(candidate, bg) >= min_ratio:
            return candidate
    return target  # fallback garanti

def _text_on(hex_str):
    return "#fff" if _luminance(hex_str) < 0.35 else "#111"


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

    # Surfaces tintées par hue — bg/fg2/bdr dérivés de la teinte de base
    # Donne des noirs bleutés, des blancs légèrement colorés, etc.
    surfaces = {
        "dark":  dict(
            bg  = _hsl_to_hex(h, 0.15, 0.04),
            bg2 = _hsl_to_hex(h, 0.10, 0.07),
            fg  = _hsl_to_hex(h, 0.05, 0.90),
            fg2 = "#666",
            bdr = _hsl_to_hex(h, 0.08, 0.14),
        ),
        "warm":  dict(
            bg  = _hsl_to_hex(h, 0.18, 0.965),   # warm cream — teinté hue
            bg2 = _hsl_to_hex(h, 0.22, 0.918),   # warm surface
            fg  = _hsl_to_hex(h, 0.42, 0.10),    # warm near-black
            fg2 = _hsl_to_hex(h, 0.20, 0.44),    # warm muted
            bdr = _hsl_to_hex(h, 0.20, 0.80),    # warm border
        ),
        "pale":  dict(
            bg  = _hsl_to_hex(h, 0.07, 0.975),
            bg2 = _hsl_to_hex(h, 0.08, 0.950),
            fg  = "#111111",
            fg2 = "#777",
            bdr = _hsl_to_hex(h, 0.06, 0.870),
        ),
        "light": dict(
            bg  = _hsl_to_hex(h, 0.04, 1.00),
            bg2 = _hsl_to_hex(h, 0.05, 0.96),
            fg  = "#111111",
            fg2 = "#666",
            bdr = _hsl_to_hex(h, 0.04, 0.90),
        ),
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
        else [40, 60, 80]    if ad["archetype"] in {"editorial_magazine","luxury_minimal","premium_craft"}
        else [30, 60, 150]
    )
    s_hex = _hsl_to_hex((p_h+s_shift)%360, p_s*0.72, min(0.78, lt+0.12))

    # Accent — vibrant contrast, saturation minimale garantie
    acc = _hsl_to_hex((p_h+90)%360, min(1.0, max(0.65, p_s*1.3)), min(0.65, max(0.48, lt*1.15)))

    inv = _text_on(p)

    return _pal_safe(dict(mode=mode, p=p, s=s_hex, acc=acc, inv=inv, **surfaces))


# ─────────────────────────────────────────────────────────────────────────────
# PALETTE FROM PALETTE_OUTPUT (palette_generator integration)
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_distinct_accent(acc: str, p: str, s: str, bg: str) -> str:
    """
    Garantit que acc est hue-distinct de p et s.
    Si acc est achromatique ou trop proche de p/s en teinte → génère une couleur
    véritablement différente (split-complement du primary, ou gold pour palettes grises).
    """
    def _hd(h1, h2):
        d = abs(h1 - h2); return min(d, 360 - d)

    a_h, a_s, a_l = _hex_to_hsl(acc)
    p_h, p_s, _   = _hex_to_hsl(p)
    s_h, s_s, _   = _hex_to_hsl(s)
    bg_l           = _hex_to_hsl(bg)[2]
    dark = bg_l < 0.3

    too_close = (
        a_s < 0.12                                       # achromatique
        or (p_s > 0.12 and _hd(a_h, p_h) < 25)          # trop proche de p
        or (s_s > 0.12 and _hd(a_h, s_h) < 25)          # trop proche de s
    )
    if not too_close:
        return acc

    # Trouver une teinte maximalement éloignée de p et s
    if p_s > 0.12:
        cand_h = (p_h + 150) % 360
        if s_s > 0.12 and _hd(cand_h, s_h) < 25:
            cand_h = (p_h + 210) % 360
    elif s_s > 0.12:
        cand_h = (s_h + 150) % 360
    else:
        cand_h = 40  # gold/ambre — classique pour palettes monochromes/éditoriales

    cand_l = 0.60 if dark else 0.44
    return _hsl_to_hex(cand_h, 0.80, cand_l)


def _pal_safe(d: dict) -> dict:
    """Enforce WCAG contrast on all text/bg pairs before rendering."""
    bg, bg2 = d["bg"], d["bg2"]
    d["fg"]  = _enforce_contrast(d["fg"],  bg,  4.5)
    d["fg2"] = _enforce_contrast(d["fg2"], bg,  3.0)
    d["p"]   = _enforce_contrast(d["p"],   bg,  3.0)   # brand color on bg
    d["s"]   = _enforce_contrast(d["s"],   bg,  3.0)
    d["acc"] = _ensure_distinct_accent(d["acc"], d["p"], d["s"], bg)  # hue-distinct d'abord
    d["acc"] = _enforce_contrast(d["acc"], bg,  3.0)                  # puis contrast OK
    d["fg"]  = _enforce_contrast(d["fg"],  bg2, 4.5)   # fg doit passer sur bg2 aussi
    d["inv"] = _text_on(d["p"])                         # recalculer après ajustement p
    return d

_HARMONY_ORDER = ["complementary", "analogous", "triadic", "monochromatic", "minimal"]


# ─────────────────────────────────────────────────────────────────────────────
# COLOR PALETTE ENGINE BRIDGE
# Maps Color Palette Engine output → internal pal dict (single source of truth)
# ─────────────────────────────────────────────────────────────────────────────

def _pal_from_color_palette_engine(cp: dict) -> dict:
    """
    Bridge: Color Palette Engine output → internal pal dict used by all renderers.

    Color Palette Engine schema  →  internal pal key
    ─────────────────────────────────────────────────
    primary        → p
    secondary      → s
    accent         → acc
    background     → bg
    surface        → bg2
    text_primary   → fg
    text_secondary → fg2
    border         → bdr
    (computed)     → inv   _text_on(primary)
    (computed)     → mode  dark if background luminance < 0.3

    All values are traceable to the Color Palette Engine output.
    States (success/warning/error) are preserved in pal["states"].
    """
    def _get(key: str, fallback: str = "#888888") -> str:
        v = cp.get(key, "")
        return v if (isinstance(v, str) and len(v.lstrip("#")) >= 6) else fallback

    p   = _get("primary",        "#2563eb")
    s   = _get("secondary",      "#7c3aed")
    acc = _get("accent",         "#f59e0b")
    bg  = _get("background",     "#ffffff")
    bg2 = _get("surface",        "#f4f4f4")
    fg  = _get("text_primary",   "#111111")
    fg2 = _get("text_secondary", "#555555")
    bdr = _get("border",         "#e2e2e2")
    inv = _text_on(p)
    mode = "dark" if _luminance(bg) < 0.3 else "light"

    states = cp.get("states", {})

    return dict(
        mode=mode, p=p, s=s, acc=acc, inv=inv,
        bg=bg, bg2=bg2, fg=fg, fg2=fg2, bdr=bdr,
        states=states,
    )

def _pal_from_palette_output(ad, palette_output, harmony, rng):
    """
    Convert palette_generator PaletteOutput → pal dict.
    Zero hardcoded brand colors. Surfaces from bw_variant.
    ad = art direction dict (pour déterminer le mode dark/warm/light/pale)
    """
    def _c(lst, idx, fallback="#888888"):
        val = lst[idx].hex if lst and len(lst) > idx else ""
        return val if val and len(val.lstrip("#")) >= 6 else fallback

    ps = getattr(palette_output, "palette_set", None) if palette_output else None
    bw = getattr(ps, "black_and_white_variant", None) if ps else None

    # Mode faux noir/blanc : toutes les couleurs brand depuis bw_variant
    if harmony in ("black_and_white", "bw_dark", "bw_light"):
        blacks_raw = (bw.false_blacks if bw else []) or []
        whites_raw = (bw.false_whites if bw else []) or []
        # Garantir que false_blacks sont vraiment sombres (L≤0.18) et false_whites clairs (L≥0.82)
        def _force_dark(h, max_l=0.18):
            hh,hs,hl = _hex_to_hsl(h); return _hsl_to_hex(hh, hs, min(hl, max_l))
        def _force_light(h, min_l=0.82):
            hh,hs,hl = _hex_to_hsl(h); return _hsl_to_hex(hh, hs, max(hl, min_l))
        class _FakeCol:
            def __init__(self, hx): self.hex = hx
        blacks = [_FakeCol(_force_dark(c.hex)) for c in blacks_raw] or [_FakeCol("#0d0d0d"),_FakeCol("#1a1a1a"),_FakeCol("#2a2a2a")]
        whites = [_FakeCol(_force_light(c.hex)) for c in whites_raw] or [_FakeCol("#f5f5f3"),_FakeCol("#ebebea"),_FakeCol("#e0e0de")]
        # Accent vif : prendre depuis la première harmonie couleur disponible
        _vivid_variant = None
        for _h in _HARMONY_ORDER:
            _vivid_variant = getattr(ps, _h, None) if ps else None
            if _vivid_variant: break
        _vivid_acc = _c(getattr(_vivid_variant, "accent", []) or [], 0, None) if _vivid_variant else None
        _vivid_s   = _c(getattr(_vivid_variant, "primary", []) or [], 0, None) if _vivid_variant else None
        is_dark = (harmony == "bw_dark") or (harmony == "black_and_white" and ad["_dark"])
        if is_dark:
            bg  = _c(blacks, 0, "#0d0d0d")
            bg2 = _c(blacks, 1, "#1a1a1a")
            fg  = _c(whites, 0, "#f0f0ee")
            fg2 = _c(whites, 1, "#aaaaaa")
            p   = _c(whites, 0, "#f0f0ee")
            s   = _vivid_s  or _c(whites, 1, "#cccccc")
            acc = _vivid_acc or _c(whites, 0, "#f0f0ee")
            bdr = _c(blacks, 2, "#333333")
        else:
            bg  = _c(whites, 0, "#fafafa")
            bg2 = _c(whites, 1, "#f0f0ee")
            fg  = _c(blacks, 0, "#111111")
            fg2 = _c(blacks, 1, "#555555")
            p   = _c(blacks, 0, "#111111")
            s   = _vivid_s  or _c(blacks, 1, "#444444")
            acc = _vivid_acc or _c(blacks, 0, "#111111")
            bdr = _c(whites, 2, "#dddddd")
        mode = "dark" if is_dark else "light"
        inv  = _text_on(p)
        return _pal_safe(dict(mode=mode, p=p, s=s, acc=acc, inv=inv,
                    bg=bg, bg2=bg2, fg=fg, fg2=fg2, bdr=bdr))

    # Choisir la variante harmonique — fallback en ordre si None
    variant = None
    for h in [harmony] + _HARMONY_ORDER:
        v = getattr(ps, h, None) if ps else None
        if v is not None:
            variant = v
            harmony = h
            break

    # Couleurs brand depuis la variante
    prim = getattr(variant, "primary",   []) or []
    sec  = getattr(variant, "secondary", []) or []
    acc_ = getattr(variant, "accent",    []) or []
    neu  = getattr(variant, "neutral",   []) or []

    p   = _c(prim, 0, "#2563eb")
    s   = _c(sec,  0, "#7c3aed")
    acc = _c(acc_, 0, "#f59e0b")
    inv = _text_on(p)

    # Neutrals (du module)
    fg   = _c(neu, 3, "#222222")   # neutral_dark
    fg2  = _c(neu, 2, "#888888")   # neutral_mid
    bdr  = _c(neu, 1, "#e2e2e2")   # neutral_light

    # Mode surface system (même logique que _build_palette)
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

    # Surfaces depuis bw_variant (zéro hardcoded)
    blacks = (bw.false_blacks if bw else []) or []
    whites = (bw.false_whites if bw else []) or []

    if mode == "dark":
        _ph = _hex_to_hsl(p)[0]
        bg  = _c(blacks, 0, _hsl_to_hex(_ph, 0.15, 0.04))
        bg2 = _c(blacks, 1, _hsl_to_hex(_ph, 0.10, 0.07))
        sfg = _c(whites, 0, "#f0f0f0")
        return _pal_safe(dict(mode=mode, p=p, s=s, acc=acc, inv=inv,
                    bg=bg, bg2=bg2, fg=sfg, fg2=fg2, bdr=bdr))
    elif mode == "warm":
        # Tonal scale la plus claire si dispo, sinon teinté chaud
        tones = {}
        if variant and getattr(variant, "tonal_scales", None):
            tones = variant.tonal_scales[0].shades
        bg  = tones.get(100, type("_",(),{"hex":"#f9f6f0"})()).hex
        bg2 = tones.get(200, type("_",(),{"hex":"#ede8df"})()).hex
        return _pal_safe(dict(mode=mode, p=p, s=s, acc=acc, inv=inv,
                    bg=bg, bg2=bg2, fg=fg, fg2=fg2, bdr=bdr))
    elif mode == "pale":
        bg  = _c(whites, 0, "#f9f9f7")
        bg2 = _c(whites, 1, "#f1f0ed")
        return _pal_safe(dict(mode=mode, p=p, s=s, acc=acc, inv=inv,
                    bg=bg, bg2=bg2, fg=fg, fg2=fg2, bdr=bdr))
    else:  # light
        bg  = _c(whites, 2, "#ffffff")
        bg2 = _c(whites, 1, "#f4f4f4")
        return _pal_safe(dict(mode=mode, p=p, s=s, acc=acc, inv=inv,
                    bg=bg, bg2=bg2, fg=fg, fg2=fg2, bdr=bdr))


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
        h1_sz="clamp(2.8rem,7vw,5rem)"; h1_wt="900"; h1_st="normal"; h1_tr="uppercase"
        h1_ls="-.06em"; h1_lh="0.88"; lls=".3em"; lh="1.65"
    elif att == "editorial" and font_cat == "serif":
        h1_sz="clamp(2.4rem,5vw,4rem)"; h1_wt="300"; h1_st="italic"; h1_tr="none"
        h1_ls="-.01em"; h1_lh="1.05"; lls=".22em"; lh="1.9"
    elif att == "editorial":
        h1_sz="clamp(2.4rem,5vw,4rem)"; h1_wt="700"; h1_st="normal"; h1_tr="none"
        h1_ls="-.04em"; h1_lh="1.05"; lls=".2em"; lh="1.8"
    elif att == "experimental":
        tr = rng.choice(["uppercase","none"])
        h1_sz="clamp(2.8rem,7vw,5rem)"; h1_wt="900"; h1_st="normal"; h1_tr=tr
        h1_ls="-.05em"; h1_lh="0.9"; lls=".25em"; lh="1.7"
    elif att == "playful":
        h1_sz="clamp(2rem,5vw,3.5rem)"; h1_wt="900"; h1_st="normal"; h1_tr="none"
        h1_ls="-.02em"; h1_lh="1.1"; lls=".1em"; lh="1.75"
    else:  # product
        sz  = "clamp(2.8rem,6vw,4.5rem)" if ad["energy"]=="high" else "clamp(2rem,4.5vw,3.2rem)"
        wt  = "800" if ad["energy"]=="high" else "700"
        h1_sz=sz; h1_wt=wt; h1_st="normal"; h1_tr="none"
        h1_ls="-.03em"; h1_lh="1.05"; lls=".18em"; lh="1.75"

    h3_wt = "600" if h1_wt in ("300","400") else "700"
    h3_st = "italic" if h1_st == "italic" else "normal"

    return dict(
        hf=hf, bf=bf, gf_url=gf_url,
        h1_css=(f"font-family:'{hf}',Georgia,serif;font-size:{h1_sz};"
                f"font-weight:{h1_wt};font-style:{h1_st};text-transform:{h1_tr};"
                f"letter-spacing:{h1_ls};line-height:{h1_lh};color:{fg}"),
        h2_css=(f"font-family:'{hf}',Georgia,serif;font-size:clamp(1.8rem,4vw,2.8rem);"
                f"font-weight:{h1_wt};font-style:{h1_st};color:{fg};letter-spacing:{h1_ls}"),
        h3_css=(f"font-family:'{hf}',Georgia,serif;font-size:1.1rem;"
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
    acc       = pal.get("acc", s)
    bg2       = pal.get("bg2", bg)
    ornament  = ad["ornament_level"]
    att       = ad["attitude"]

    if ornament == "none":
        return f"background:{bg}"

    v = rng.choice({
        "brutalist":    ["hard_grid","noise_heavy","stripe_bold","diagonal_bold"],
        "editorial":    ["gradient_deep","spotlight","hairline_grid","radial_soft"],
        "experimental": ["mesh_gradient","noise_heavy","spotlight","stripe_bold"],
        "playful":      ["dots_multi","radial_warm","diagonal_soft"],
        "product":      ["gradient_deep","spotlight","dots_mono","radial_soft"],
    }.get(att, ["gradient_deep","radial_soft"]))

    _pos = rng.choice(['70% 30%','20% 60%','80% 80%','50% 20%'])
    _ang = rng.choice([120, 135, 150, 45])
    _corner = rng.choice(["0% 0%", "100% 0%", "0% 100%", "100% 100%"])

    defs = {
        # ── Existing patterns — opacités renforcées ────────────────────────────
        "hard_grid":    (f"background-color:{bg};"
                         f"background-image:repeating-linear-gradient(0deg,{p}44 0,{p}44 1px,transparent 1px,transparent 40px),"
                         f"repeating-linear-gradient(90deg,{p}44 0,{p}44 1px,transparent 1px,transparent 40px)"),
        "noise_heavy":  (f"background-color:{bg};"
                         f"background-image:linear-gradient(45deg,{p}33 25%,transparent 25%),"
                         f"linear-gradient(-45deg,{p}28 25%,transparent 25%),"
                         f"linear-gradient(45deg,transparent 75%,{s}22 75%),"
                         f"linear-gradient(-45deg,transparent 75%,{s}1a 75%);"
                         f"background-size:6px 6px;background-position:0 0,0 3px,3px -3px,-3px 0"),
        "stripe_bold":  (f"background-color:{bg};"
                         f"background-image:repeating-linear-gradient(45deg,{p}40 0,{p}40 2px,transparent 2px,transparent 24px)"),
        "diagonal_bold":(f"background-color:{bg};"
                         f"background-image:repeating-linear-gradient(135deg,{p}44 0,{p}44 3px,transparent 3px,transparent 28px)"),
        "radial_soft":  f"background:radial-gradient(ellipse at {_pos},{p}44 0%,{bg} 65%)",
        "hairline_grid":(f"background-color:{bg};"
                         f"background-image:repeating-linear-gradient(0deg,{p}1a 0,{p}1a 1px,transparent 1px,transparent 64px),"
                         f"repeating-linear-gradient(90deg,{p}1a 0,{p}1a 1px,transparent 1px,transparent 64px)"),
        "dots_mono":    (f"background-image:radial-gradient(circle,{p}55 1.5px,transparent 1.5px);"
                         f"background-size:28px 28px;background-color:{bg}"),
        "dots_multi":   (f"background-image:radial-gradient(circle,{p}66 1.5px,transparent 1.5px),"
                         f"radial-gradient(circle,{s}55 1px,transparent 1px);"
                         f"background-size:36px 36px,20px 20px;background-position:0 0,10px 10px;background-color:{bg}"),
        "radial_warm":  f"background:radial-gradient(ellipse at 60% 40%,{p}55 0%,{s}28 40%,{bg} 70%)",
        "diagonal_soft":(f"background-color:{bg};"
                         f"background-image:repeating-linear-gradient(135deg,{p}28 0,{p}28 1px,transparent 1px,transparent 32px)"),
        "none":         f"background:{bg}",
        # ── New high-impact types ──────────────────────────────────────────────
        # Mesh gradient — 3 radial sources, sense of depth and warmth
        "mesh_gradient":(f"background-color:{bg};"
                         f"background-image:"
                         f"radial-gradient(ellipse at 10% 20%,{p}66 0%,transparent 50%),"
                         f"radial-gradient(ellipse at 85% 15%,{s}55 0%,transparent 45%),"
                         f"radial-gradient(ellipse at 55% 90%,{acc}44 0%,transparent 40%)"),
        # Spotlight — strong directional glow from one corner, theatrical
        "spotlight":    (f"background-color:{bg};"
                         f"background-image:radial-gradient(ellipse at {_corner},{p}77 0%,{p}22 35%,transparent 65%)"),
        # Gradient deep — 3-stop linear sweep, structured and bold
        "gradient_deep":(f"background:linear-gradient({_ang}deg,{bg} 0%,{p}33 45%,{s}22 100%)"),
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


# ─────────────────────────────────────────────────────────────────────────────
# CSS VARIABLES — single `:root` block, all tokens from pal
# ─────────────────────────────────────────────────────────────────────────────

def _build_css_vars(pal: dict) -> str:
    """
    Emit a CSS :root block from the pal dict.
    Every token is traceable to a palette key.

    Token map:
        --color-primary     ← pal['p']
        --color-secondary   ← pal['s']
        --color-accent      ← pal['acc']
        --color-bg          ← pal['bg']
        --color-surface     ← pal['bg2']
        --color-text        ← pal['fg']
        --color-text-muted  ← pal['fg2']
        --color-border      ← pal['bdr']
        --color-on-primary  ← pal['inv']
        --color-success     ← pal['states']['success']  (if present)
        --color-warning     ← pal['states']['warning']  (if present)
        --color-error       ← pal['states']['error']    (if present)
    """
    states = pal.get("states", {})
    lines = [
        f"--color-primary:{pal['p']}",
        f"--color-secondary:{pal['s']}",
        f"--color-accent:{pal['acc']}",
        f"--color-bg:{pal['bg']}",
        f"--color-surface:{pal['bg2']}",
        f"--color-text:{pal['fg']}",
        f"--color-text-muted:{pal['fg2']}",
        f"--color-border:{pal['bdr']}",
        f"--color-on-primary:{pal['inv']}",
    ]
    if states.get("success"): lines.append(f"--color-success:{states['success']}")
    if states.get("warning"): lines.append(f"--color-warning:{states['warning']}")
    if states.get("error"):   lines.append(f"--color-error:{states['error']}")
    return ":root{" + ";".join(lines) + "}"


# ─────────────────────────────────────────────────────────────────────────────
# PHOTO PANEL — Picsum avec palette-match overlay
# ─────────────────────────────────────────────────────────────────────────────

# Archetypes qui bénéficient de vraies photos plutôt que panels CSS abstraits
_PHOTO_ARCHETYPES = {
    "editorial_magazine", "luxury_minimal", "premium_craft",
    "organic_natural", "playful_brand", "warm_human",
    "startup_clean", "corporate_pro",
}


def _picsum_panel(rc, img_seed):
    """
    Picsum photo panel avec palette-match duotone.
    Technique : grayscale(1) + overlay mix-blend-mode:color → image prend la teinte brand.
    Paramètres d'overlay calculés par visual_coherence_engine (CASE 2 : palette_drives_image).
    """
    p    = rc["p"]
    mode = rc.get("mode", "light")
    palette = {"primary": p, "mode": mode}
    adj = _coherence_adjustments(palette, dark_mode=(mode == "dark"))
    overlay_color = adj["overlay_color"]
    overlay_op    = adj["overlay_opacity"]
    css_filter    = adj["filter"]
    blend_mode    = adj["blend_mode"]
    return (
        f'<div style="position:absolute;inset:0;overflow:hidden">'
        f'<img src="https://picsum.photos/seed/{img_seed}/900/700" '
        f'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;'
        f'filter:{css_filter}" loading="lazy" />'
        f'<div style="position:absolute;inset:0;background:{overlay_color};mix-blend-mode:{blend_mode};'
        f'opacity:{overlay_op}"></div>'
        f'</div>'
    )


def _visual_panel(rc, rng):
    """
    Route vers photo Picsum ou panel CSS selon archetype.
    Editorial/craft/lifestyle → photo. Tech/brutalist/experimental → CSS.
    """
    archetype = rc["ad"]["archetype"]
    if archetype in _PHOTO_ARCHETYPES:
        return _picsum_panel(rc, rng.randint(10, 990))
    if archetype == "creative_studio" and rng.random() < 0.5:
        return _picsum_panel(rc, rng.randint(10, 990))
    return _css_visual_panel(rc, rc["visual_system"], rng)


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


# ─────────────────────────────────────────────────────────────────────────────
# DA ENFORCEMENT LAYER — spacing, monochrome, decorators, CSS injection
# ─────────────────────────────────────────────────────────────────────────────

def _build_spacing_system(ad):
    """DA-driven spacing: density × energy matrix + attitude delta."""
    energy  = ad["energy"]
    density = ad["density"]
    att     = ad["attitude"]

    # Base section_pad from density
    _base_pad = {"minimal": 140, "balanced": 100, "dense": 72}[density]

    # Energy multiplier
    _e_mult = {"low": 1.25, "medium": 1.0, "high": 0.75}[energy]

    # Attitude delta: brutalist/experimental breathe more; product tighter
    _att_delta = {"brutalist": 16, "editorial": 8, "experimental": 12, "playful": 0, "product": -8}[att]

    section_pad = int(_base_pad * _e_mult) + _att_delta

    # Grid gap: density-driven, attitude nudge
    _grid_base = {"minimal": 40, "balanced": 32, "dense": 24}[density]
    _grid_att  = {"brutalist": 8, "editorial": 4, "experimental": 6, "playful": 2, "product": 0}[att]
    grid_gap = _grid_base + _grid_att

    # Content width: density-driven baseline
    content_w = {"minimal": "760px", "balanced": "1060px", "dense": "1200px"}[density]

    # Title gap: space between label/kicker and headline
    title_gap = {"low": 28, "medium": 20, "high": 14}[energy]

    # spacing_v: vertical rhythm between sections (legacy key kept for renderer compat)
    spacing_v = f"{section_pad}px"

    return dict(
        section_pad=f"{section_pad}px",
        spacing_v=spacing_v,
        grid_gap=f"{grid_gap}px",
        content_w=content_w,
        title_gap=f"{title_gap}px",
    )


def _detect_monochrome(pal):
    """Returns True if palette is essentially desaturated (avg saturation < 12%)."""
    import colorsys

    def _hex_sat(h):
        h = h.lstrip("#")
        if len(h) < 6:
            return 100
        r, g, b = int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255
        _, s, _ = colorsys.rgb_to_hsv(r, g, b)
        return s * 100

    try:
        avg_sat = (_hex_sat(pal.get("p", "#888")) + _hex_sat(pal.get("s", "#888"))) / 2
        return avg_sat < 12.0
    except Exception:
        return False


# Fallback decorators by attitude (when visual_decorators module unavailable)
_DECORATOR_FALLBACKS = {
    "brutalist":    {"border": "3px solid", "icon_style": "symbol", "motif": "rule", "divider": "heavy_rule"},
    "editorial":    {"border": "1px solid", "icon_style": "minimal", "motif": "hairline", "divider": "hairline"},
    "experimental": {"border": "1px dashed", "icon_style": "abstract", "motif": "noise", "divider": "dotted"},
    "playful":      {"border": "2px solid", "icon_style": "rounded", "motif": "dot", "divider": "wavy"},
    "product":      {"border": "1px solid", "icon_style": "outline", "motif": "grid", "divider": "thin_rule"},
}

# ── Mapping tables for visual_decorators module ───────────────────────────────
_ARCHETYPE_TO_STYLE_FAMILY = {
    "luxury_minimal":     "editorial_luxury",
    "editorial_magazine": "editorial_luxury",
    "premium_craft":      "premium_brand",
    "corporate_pro":      "premium_brand",
    "startup_clean":      "tech_minimal",
    "tech_futurist":      "tech_minimal",
    "bold_challenger":    "bold_marketing",
    "creative_studio":    "experimental_grid",
    "organic_natural":    "premium_brand",
    "playful_brand":      "bold_marketing",
    "warm_human":         "premium_brand",
    "brutalist":          "brutalist",
}

_ATTITUDE_TO_EMOTIONAL_GOAL = {
    "brutalist":    "authority",
    "editorial":    "desire",
    "experimental": "curiosity",
    "playful":      "excitement",
    "product":      "trust",
}


def _get_brand_positioning(att, energy):
    if att == "brutalist":    return "disruptive"
    if att == "editorial":    return "premium" if energy != "low" else "serious"
    if att == "experimental": return "disruptive"
    if att == "playful":      return "playful"
    return "accessible" if energy == "high" else "serious"


def _get_decorators_graceful(ad):
    """Try visual_decorators module with proper visual_intent; fall back to attitude-based defaults."""
    att      = ad.get("attitude", "product")
    energy   = ad.get("energy", "medium")
    archetype = ad.get("archetype", "startup_clean")
    try:
        import importlib.util as _ilu_dec
        import pathlib as _pl_dec
        _VD_PY = _pl_dec.Path(__file__).parent / "MODULES" / "visual_decorators" / "src" / "visual_decorators.py"
        if _VD_PY.exists():
            _spec = _ilu_dec.spec_from_file_location("_vd_da_layer", _VD_PY)
            _mod  = _ilu_dec.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            visual_intent = {
                "context": {
                    "emotional_goal":    _ATTITUDE_TO_EMOTIONAL_GOAL.get(att, "trust"),
                    "brand_positioning": _get_brand_positioning(att, energy),
                },
                "art_direction": {
                    "style_family": _ARCHETYPE_TO_STYLE_FAMILY.get(archetype, "tech_minimal"),
                    "intensity":    energy,
                },
                "composition_bias": {
                    "density": ad.get("density", "medium"),
                },
            }
            result = _mod.generate_visual_decorators(visual_intent)
            if result and isinstance(result, dict) and "borders" in result:
                # Normalize: add flat keys for backward compat
                b  = result.get("borders", {})
                th = {"thin": "1px", "medium": "2px", "thick": "3px"}.get(b.get("thickness", "thin"), "1px")
                result["border"]     = f"{th} {b.get('style', 'solid')}"
                result["icon_style"] = result.get("icons", {}).get("style", "line")
                result["motif"]      = result.get("motifs", {}).get("type", "none")
                result["divider"]    = "{}_{}".format(
                    result.get("dividers", {}).get("type", "line"),
                    result.get("dividers", {}).get("style", "minimal"),
                )
                return result
    except Exception:
        pass
    return _DECORATOR_FALLBACKS.get(att, _DECORATOR_FALLBACKS["product"])


def _build_da_css(ad, pal, spacing, decorators, is_mono):
    """DA enforcement CSS block injected after reset CSS. NO PAGE without decorators."""
    att      = ad["attitude"]
    energy   = ad["energy"]
    geometry = ad["geometry"]
    mood     = ad.get("mood", "neutral")

    lines = []

    # ── 1. Spacing vars ──────────────────────────────────────────────────────
    lines.append(
        f":root{{--da-section-pad:{spacing['section_pad']};--da-grid-gap:{spacing['grid_gap']};"
        f"--da-title-gap:{spacing['title_gap']};--da-content-w:{spacing['content_w']}}}"
    )

    # ── 2. Monochrome image treatment ────────────────────────────────────────
    if is_mono:
        lines.append(
            "img{filter:grayscale(100%) contrast(1.08) brightness(0.98)!important}"
        )
        lines.append(
            f"body{{background:{pal.get('bg','#f8f8f6')}!important;color:{pal.get('txt','#1a1a18')}!important}}"
        )

    # ── Palette shortcuts ─────────────────────────────────────────────────────
    bg2  = pal.get("bg2", pal.get("bg", "#f5f5f3"))
    acc  = pal.get("acc", "#000")
    p    = pal.get("p", "#111")
    bdr  = pal.get("bdr", p + "22")

    # ── Decorator field accessors (works for nested module output OR flat fallback) ──
    _brd         = decorators.get("borders", {})
    _brd_pattern = _brd.get("pattern", "frame")
    _brd_r_map   = {"none": "0", "small": "4px", "medium": "8px", "large": "16px", "full": "999px"}
    _brd_radius  = _brd_r_map.get(_brd.get("radius", "small"), "4px")
    border_val   = decorators.get("border", "1px solid")

    _div         = decorators.get("dividers", {})
    _div_type    = _div.get("type", "line")
    _div_style   = _div.get("style", "minimal")

    _motifs      = decorators.get("motifs")
    _motif_type  = _motifs.get("type", "none")  if _motifs else decorators.get("motif", "")
    _motif_usage = _motifs.get("usage", "none") if _motifs else ""

    _ov          = decorators.get("overlays", {})
    _ov_type     = _ov.get("type", "none")
    _ov_opacity  = {"subtle": "0.04", "medium": "0.08", "strong": "0.14"}.get(_ov.get("intensity", "subtle"), "0.04")

    icon_style   = decorators.get("icon_style", "line")

    # ── 3. Background / section alternation ──────────────────────────────────
    if att == "brutalist":
        lines.append(
            f".da-section-alt{{background:{bg2}!important}}"
            f"section{{border-bottom:3px solid {p}!important}}"
        )
    elif att == "editorial":
        lines.append(
            f".da-section-alt{{background:{bg2}!important}}"
            f"section+section{{border-top:1px solid {bdr}!important}}"
        )
    elif att == "experimental":
        noise_opacity = "0.04" if energy == "low" else "0.07"
        lines.append(
            f"body::after{{content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;"
            f"background-image:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E"
            f"%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4'/%3E%3C/filter%3E"
            f"%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='{noise_opacity}'/%3E%3C/svg%3E\");"
            f"opacity:{noise_opacity}}}"
        )
    elif att == "playful":
        lines.append(f".da-section-alt{{background:{bg2}!important}}")

    # ── 4. Border language consistency ───────────────────────────────────────
    if att == "brutalist":
        lines.append(
            f"[class*='card'],[class*='Card']{{border:{border_val} {p}!important;border-radius:0!important}}"
            f"button,[role='button']{{border:{border_val} {p}!important;border-radius:0!important}}"
        )
    elif att == "editorial":
        lines.append(
            f"[class*='card'],[class*='Card']{{border:{border_val} {bdr}!important;border-radius:{_brd_radius}!important}}"
        )
    elif att == "experimental":
        lines.append(
            f"[class*='card'],[class*='Card']{{border:1px dashed {acc}66!important;border-radius:{_brd_radius}!important}}"
        )
    else:
        lines.append(
            f"[class*='card'],[class*='Card']{{border:{border_val} {p}22!important;border-radius:{_brd_radius}!important}}"
        )

    # ── 5. Icon style enforcement ─────────────────────────────────────────────
    if icon_style in ("symbol", "filled") and att == "brutalist":
        lines.append(
            f".da-icon{{font-weight:900!important;font-variant-numeric:tabular-nums!important}}"
        )
    elif icon_style in ("line", "minimal") or att == "editorial":
        lines.append(f".da-icon{{opacity:0.7!important;font-weight:300!important}}")
    elif icon_style == "duotone":
        lines.append(f".da-icon{{color:{acc}!important;opacity:0.85!important}}")

    # ── 6. Typography attitude sharpening ────────────────────────────────────
    if att == "brutalist":
        lines.append(
            "h1,h2,h3{text-transform:uppercase!important;letter-spacing:-0.02em!important}"
            f"h1{{border-bottom:4px solid {p}!important;padding-bottom:12px!important}}"
        )
    elif att == "editorial":
        lines.append(
            "h1,h2{font-style:italic!important;letter-spacing:-0.03em!important}"
            "p{max-width:62ch!important}"
        )
    elif att == "experimental":
        lines.append(
            "h1{letter-spacing:-0.04em!important;line-height:0.95!important}"
        )
    elif att == "playful":
        lines.append(
            "h1,h2{letter-spacing:0.01em!important}"
        )

    # ── 7. Divider system ─────────────────────────────────────────────────────
    if _div_type == "gradient":
        lines.append(
            f"hr,.da-divider{{border:none!important;height:1px!important;"
            f"background:linear-gradient(90deg,transparent,{p}66,transparent)!important;margin:2rem 0!important}}"
        )
    elif _div_type == "line" and _div_style == "bold":
        lines.append(
            f"hr,.da-divider{{border:none!important;border-top:2px solid {p}!important;margin:2rem 0!important}}"
        )
    elif _div_type == "line" and _div_style == "decorative":
        lines.append(
            f"hr,.da-divider{{border:none!important;border-top:1px solid {p}22!important;margin:2rem 0!important}}"
            f"hr::after,.da-divider::after{{content:'◆';display:block;text-align:center;"
            f"color:{acc};font-size:0.5rem;margin-top:-0.4rem}}"
        )
    elif _div_type == "ornament":
        lines.append(
            f"hr,.da-divider{{border:none!important;text-align:center;margin:2rem 0!important}}"
            f"hr::before,.da-divider::before{{content:'— ◆ —';color:{p}66;font-size:0.75rem;letter-spacing:0.2em}}"
        )
    elif _div_type == "zigzag":
        lines.append(
            f"hr,.da-divider{{border:none!important;height:8px!important;margin:2rem 0!important;"
            f"background:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='8'%3E"
            f"%3Cpath d='M0,4 L5,0 L10,4 L15,0 L20,4' stroke='{p.replace('#','%23')}' fill='none' stroke-width='1.5'/%3E%3C/svg%3E\");"
            f"background-repeat:repeat-x}}"
        )
    elif _div_type == "space":
        lines.append(
            f"hr,.da-divider{{border:none!important;height:3rem!important;margin:0!important}}"
        )
    elif _div_type not in ("none", ""):
        lines.append(
            f"hr,.da-divider{{border:none!important;border-top:1px solid {p}22!important;margin:2rem 0!important}}"
        )

    # ── 8. Motif / decorative layer ───────────────────────────────────────────
    if _motif_type == "grid-fragment" or (_motif_type == "rule" and att == "brutalist"):
        lines.append(
            f"section::before{{content:'';display:block;height:4px;background:{p};"
            f"margin-bottom:var(--da-section-pad,80px)}}"
        )
    elif _motif_type == "dot-pattern" and _motif_usage in ("background", "none", ""):
        lines.append(
            f"body{{background-image:radial-gradient(circle,{p}18 1px,transparent 1px)!important;"
            f"background-size:24px 24px!important}}"
        )
    elif _motif_type == "diagonal-cut":
        lines.append(
            f"section:first-of-type{{clip-path:polygon(0 0,100% 0,100% 90%,0 100%)!important;"
            f"padding-bottom:calc(var(--da-section-pad,80px) + 60px)!important}}"
        )
    elif _motif_type == "wave":
        bg2_enc = bg2.replace("#", "%23")
        lines.append(
            f"section:nth-of-type(odd){{position:relative;overflow:hidden}}"
            f"section:nth-of-type(odd)::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:60px;"
            f"background:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 60'%3E"
            f"%3Cpath d='M0,30 C300,60 900,0 1200,30 L1200,60 L0,60 Z' fill='{bg2_enc}'/%3E%3C/svg%3E\");"
            f"background-size:cover;pointer-events:none}}"
        )
    elif _motif_type == "geometric" and _motif_usage == "corner":
        lines.append(
            f"section{{position:relative}}"
            f"section::before{{content:'';position:absolute;top:0;right:0;width:80px;height:80px;"
            f"background:linear-gradient(135deg,{acc}22 0%,transparent 60%);pointer-events:none}}"
        )
    elif _motif_type == "blob" and _motif_usage in ("background", "section-accent"):
        lines.append(
            f"section:nth-of-type(even){{position:relative;overflow:hidden}}"
            f"section:nth-of-type(even)::before{{content:'';position:absolute;top:-40%;right:-20%;"
            f"width:60%;height:120%;border-radius:30% 70% 70% 30%/30% 30% 70% 70%;"
            f"background:{acc}0a;pointer-events:none;z-index:0}}"
        )
    elif _motif_type == "dot":
        lines.append(
            f"section::before{{content:'●';display:block;color:{acc};font-size:0.5rem;"
            f"margin-bottom:12px;opacity:0.5}}"
        )

    # ── 9. Overlay system ─────────────────────────────────────────────────────
    if _ov_type == "gradient" and att not in ("brutalist", "experimental"):
        lines.append(
            f"section:nth-of-type(even){{background:linear-gradient(160deg,{bg2} 0%,{pal.get('bg','#fff')} 100%)!important}}"
        )
    elif _ov_type == "scanlines":
        lines.append(
            f"body::before{{content:'';position:fixed;inset:0;pointer-events:none;z-index:9998;"
            f"background:repeating-linear-gradient(0deg,transparent,transparent 2px,{p}0a 2px,{p}0a 4px);"
            f"opacity:{_ov_opacity}}}"
        )
    elif _ov_type == "vignette":
        lines.append(
            f"body::before{{content:'';position:fixed;inset:0;pointer-events:none;z-index:9998;"
            f"background:radial-gradient(ellipse at center,transparent 60%,{p}33 100%)}}"
        )

    # ── 10. Mandatory decorator utility classes ───────────────────────────────
    if _brd_pattern == "top-only":
        _dec_border_base = f"border-top:{border_val} {p}!important;border-radius:{_brd_radius}"
    elif _brd_pattern == "accent":
        _dec_border_base = f"border-left:{border_val} {acc}!important;border-radius:{_brd_radius}"
    elif _brd_pattern == "frame":
        _dec_border_base = f"border:{border_val} {p}!important;border-radius:{_brd_radius}"
    else:
        _dec_border_base = f"border:{border_val} {p}22!important;border-radius:{_brd_radius}"

    lines.append(
        f".decorator-border{{{_dec_border_base}}}"
        f".decorator-border--soft{{border-color:{p}22!important;border-radius:8px!important}}"
        f".decorator-border--sharp{{border-color:{p}!important;border-radius:0!important}}"
        f".decorator-border--glow{{box-shadow:0 0 0 2px {acc}44,0 0 12px {acc}22!important;border-radius:{_brd_radius}!important}}"
        f".decorator-border--minimal{{border:1px solid {p}11!important}}"
        f".decorator-border--bold{{border:3px solid {p}!important}}"
        f".decorator-accent{{color:{acc}!important}}"
        f".decorator-accent--soft{{color:{acc};opacity:0.7}}"
        f".decorator-accent--sharp{{color:{acc};font-weight:700!important}}"
        f".decorator-accent--glow{{color:{acc};text-shadow:0 0 8px {acc}66!important}}"
        f".decorator-accent--minimal{{color:{p};opacity:0.5}}"
        f".decorator-accent--bold{{color:{acc};font-weight:900!important;text-transform:uppercase!important}}"
        f".decorator-divider{{border:none!important;border-top:1px solid {p}22!important;margin:2rem 0!important}}"
        f".decorator-divider--soft{{border-top-color:{p}11!important}}"
        f".decorator-divider--sharp{{border-top:2px solid {p}!important}}"
        f".decorator-divider--glow{{border-top-color:{acc}66!important;box-shadow:0 -1px 8px {acc}33!important}}"
        f".decorator-divider--minimal{{border-top-style:dashed!important;opacity:0.4!important}}"
        f".decorator-divider--bold{{border-top:3px solid {p}!important}}"
        f".decorator-highlight{{background:{acc}1a!important;padding:0.1em 0.3em!important;border-radius:2px!important}}"
        f".decorator-highlight--soft{{background:{acc}0d!important}}"
        f".decorator-highlight--sharp{{background:{acc}!important;color:#fff!important}}"
        f".decorator-highlight--glow{{background:{acc}22!important;box-shadow:0 0 6px {acc}44!important}}"
        f".decorator-highlight--minimal{{background:transparent!important;border-bottom:1px solid {acc}!important;padding:0!important}}"
        f".decorator-highlight--bold{{background:{p}!important;color:{pal.get('bg','#fff')}!important;padding:0.2em 0.4em!important}}"
        f".decorator-frame{{border:{border_val} {p}22!important;border-radius:{_brd_radius}!important;padding:1rem!important}}"
        f".decorator-frame--soft{{border-color:{p}11!important;border-radius:12px!important}}"
        f".decorator-frame--sharp{{border-color:{p}!important;border-radius:0!important;border-width:2px!important}}"
        f".decorator-frame--glow{{border-color:{acc}55!important;box-shadow:inset 0 0 20px {acc}11,0 0 0 1px {acc}22!important}}"
        f".decorator-frame--minimal{{border-left:{border_val} {acc}!important;border-top:none!important;border-right:none!important;border-bottom:none!important}}"
        f".decorator-frame--bold{{border:3px solid {p}!important;border-radius:0!important}}"
    )

    return "\n".join(lines)


def _build_accent_enforcement_css(pal: dict, rc: dict) -> str:
    """
    CSS enforcement block — accent must be visible on every page.
    Rules:
      - Button hover/active states use accent outline (interaction state)
      - .euk-acc* utility classes for secondary accent elements
      - Nav link hover underline in accent color
      - Focus ring in accent color
    All values derived from pal['acc'] — never arbitrary.
    """
    acc = pal["acc"]
    inv = rc.get("inv", "#fff")
    br  = rc.get("button_radius", "6px")
    return (
        f"button{{transition:all .15s cubic-bezier(.4,0,.2,1)}}"
        f"button:hover{{opacity:.87;transform:translateY(-1px);"
        f"outline:2px solid {acc}55;outline-offset:2px}}"
        f"button:active{{opacity:.95;transform:translateY(0)}}"
        f".euk-acc{{color:{acc}!important}}"
        f".euk-acc-bg{{background:{acc}!important;color:{inv}!important}}"
        f".euk-acc-bdr{{border-color:{acc}!important}}"
        f"nav a:hover{{color:{acc}!important;"
        f"text-decoration:underline;text-decoration-color:{acc};"
        f"text-underline-offset:3px}}"
        f"button:focus-visible,a:focus-visible{{"
        f"outline:2px solid {acc};outline-offset:3px;border-radius:{br}}}"
    )


def _build_divider_html(dec_rc: dict, pal: dict, att: str) -> str:
    """Returns an inline-style HTML divider injected between sections.
    No CSS class dependency — all styles are inline. Style derived from att + decorators.
    """
    p       = pal.get("p",   "#2563eb")
    acc     = pal.get("acc", "#f97316")
    bdr     = pal.get("bdr", "#e5e7eb")
    div_type = str(dec_rc.get("divider", ""))

    if att == "brutalist" or "heavy" in div_type:
        return (f'<div aria-hidden="true" data-eurkai="divider"'
                f' style="width:100%;height:3px;background:{p};display:block"></div>')
    elif att == "experimental" or "dotted" in div_type:
        return (f'<div aria-hidden="true" data-eurkai="divider"'
                f' style="width:100%;text-align:center;padding:6px 0;color:{acc}88;'
                f'font-size:7px;letter-spacing:14px;line-height:1;display:block">'
                f'•••••••••••</div>')
    elif att == "playful" or "wavy" in div_type:
        return (f'<div aria-hidden="true" data-eurkai="divider"'
                f' style="width:100%;overflow:hidden;line-height:0;display:block">'
                f'<svg viewBox="0 0 1200 18" preserveAspectRatio="none"'
                f' style="width:100%;height:18px;display:block">'
                f'<path d="M0,9 C200,0 400,18 600,9 C800,0 1000,18 1200,9"'
                f' stroke="{acc}" stroke-width="1.5" fill="none"/></svg></div>')
    elif att == "editorial" or "hairline" in div_type:
        return (f'<div aria-hidden="true" data-eurkai="divider"'
                f' style="width:100%;height:1px;background:{bdr};display:block"></div>')
    else:
        return (f'<div aria-hidden="true" data-eurkai="divider"'
                f' style="width:100%;height:1px;background:{bdr};opacity:.5;display:block"></div>')


def _build_glyph_strip(rc: dict) -> str:
    """Returns a glyph/icon strip for hero injection when no SVG is present.
    Uses SVG pictograms if available, Unicode glyphs otherwise.
    """
    att = (rc.get("ad") or {}).get("attitude", "product")
    acc = rc.get("acc", "#f97316")

    # Try SVG pictograms first
    pict = rc.get("pictograms")
    if pict:
        try:
            icons = (getattr(pict, "nav",     None) or [])[:3]
            if not icons:
                icons = (getattr(pict, "feature", None) or [])[:3]
            svgs = [getattr(ic, "svg", None) for ic in icons if getattr(ic, "svg", None)]
            if svgs:
                inner = "".join(
                    f'<span style="display:inline-block;width:28px;height:28px;'
                    f'opacity:.7;flex-shrink:0">{s}</span>'
                    for s in svgs[:3]
                )
                return (f'<div data-eurkai="glyph-strip" aria-hidden="true"'
                        f' style="display:flex;gap:14px;align-items:center;'
                        f'margin-bottom:18px">{inner}</div>')
        except Exception:
            pass

    # Fallback: Unicode glyphs per attitude
    _GLYPHS: dict[str, list[tuple[str, float]]] = {
        "brutalist":    [("▮", 1.0), ("▮", 0.4), ("▮", 0.15)],
        "editorial":    [("—", 0.9), ("·", 0.5), ("—", 0.25)],
        "experimental": [("◆", 1.0), ("◇", 0.6), ("◆", 0.2)],
        "playful":      [("●", 1.0), ("◉", 0.7), ("○", 0.35)],
        "product":      [("→", 1.0), ("→", 0.5), ("→", 0.2)],
    }
    glyphs = _GLYPHS.get(att, _GLYPHS["product"])
    items = "".join(
        f'<span style="color:{acc};font-size:14px;opacity:{op};line-height:1">{g}</span>'
        for g, op in glyphs
    )
    return (f'<div data-eurkai="glyph-strip" aria-hidden="true"'
            f' style="display:flex;gap:10px;align-items:center;margin-bottom:18px">'
            f'{items}</div>')


def _validate_page(html: str) -> dict:
    """Validates page for required visual elements. Returns validation summary dict."""
    has_svg     = "<svg" in html
    has_divider = 'data-eurkai="divider"' in html
    has_glyph   = 'data-eurkai="glyph-strip"' in html or has_svg
    warnings: list[str] = []
    if not has_glyph:
        warnings.append("no_glyphs")
    if not has_divider:
        warnings.append("no_dividers")
    return {
        "has_svg":     has_svg,
        "has_divider": has_divider,
        "has_glyph":   has_glyph,
        "warnings":    warnings,
        "valid":       not warnings,
    }


def _embed_page_meta(html: str, rc: dict, ad: dict, validation: dict) -> str:
    """Embeds <!-- eurkai:meta {...} --> comment in <body> for UI/tooling consumption."""
    import json as _json_m
    dec_used: list[str] = []
    if validation.get("has_divider"):
        dec_used.append("divider")
    if rc.get("_accent_mark"):
        dec_used.append("accent_mark")
    if rc.get("industry_badge"):
        dec_used.append("industry_badge")
    _bg = rc.get("bg_art") or {}
    if isinstance(_bg, dict) and _bg.get("type") not in (None, "", "none"):
        dec_used.append("bg_art")

    meta = {
        "layout_strategy":    rc.get("page_structure", ""),
        "hero_type":          rc.get("hero_pattern",   ""),
        "typography_family":  rc.get("hf",             ""),
        "visual_density":     ad.get("density",        ""),
        "archetype":          ad.get("archetype",      ""),
        "attitude":           ad.get("attitude",       ""),
        "site_family":        rc.get("_site_family",   ""),
        "decorators_used":    dec_used,
        "glyphs_used":        (["svg_pictogram"] if validation.get("has_svg")
                               else ["glyph_strip"] if validation.get("has_glyph")
                               else []),
        "validation_warnings": validation.get("warnings", []),
        # Plan enforcement tracing (Task 7 — debug visibility)
        "plan_layout_strategy":  rc.get("_design_plan",    ""),
        "plan_hero_type":         rc.get("_plan_hero_type", ""),
        "rendered_sections":      rc.get("sections",        []),
        "plan_enforced":          bool(rc.get("_design_plan")),
    }
    comment = (f'<!-- eurkai:meta '
               f'{_json_m.dumps(meta, ensure_ascii=False, separators=(",", ":"))} -->')
    body_pos = html.find("<body>")
    if body_pos != -1:
        ins = body_pos + len("<body>")
        html = html[:ins] + "\n" + comment + "\n" + html[ins:]
    return html


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
        "playful":      ["centered","layered","split"],
        "product":      ["split","centered","asymmetric"],
    }
    hero_pattern = rng.choice(hero_options[att])

    section_flow = rng.choice({
        "editorial":    ["alternating","narrative"],
        "brutalist":    ["fragmented","linear"],
        "experimental": ["fragmented","narrative","alternating"],
        "playful":      ["narrative","alternating"],
        "product":      ["linear","alternating"],
    }[att])

    _sp       = _build_spacing_system(ad)
    width_px  = _sp["content_w"]
    spacing_v = _sp["spacing_v"]

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
    decorators = _get_decorators_graceful(ad)
    is_mono    = _detect_monochrome(pal)

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

    # Sections pool — 6-8 options par structure pour plus de variété
    # Mix cross-attitude : un pool éditorial peut avoir des stats, etc.
    _POOLS = {
        "editorial":    ["manifesto","values_list","features_list","pull_quote",
                         "stats","process"],
        "product":      ["features_grid","values_grid","stats","process",
                         "pull_quote","features_cards","features_list"],
        "narrative":    ["manifesto","features_cards","pull_quote","values_list",
                         "stats","features_grid","features_list"],
        "experimental": ["manifesto","pull_quote","stats","values_grid",
                         "features_list","features_cards","process"],
    }
    pool = _POOLS.get(page_structure, _POOLS["product"])
    n    = {"minimal":2,"balanced":3,"dense":4}[density]
    sections = rng.sample(pool, min(n, len(pool)))

    # Certains flows démarrent par une section impactante (stats ou pull_quote)
    if section_flow in {"narrative","fragmented"} and rng.random() < 0.35:
        _lead = next((s for s in ["stats","pull_quote","manifesto"] if s in sections), None)
        if _lead:
            sections = [_lead] + [s for s in sections if s != _lead]

    # Industry badge
    industry_badge = (
        f'<div style="display:inline-block;border-radius:100px;padding:4px 14px;'
        f'margin-bottom:20px;background:{pal["acc"]}22">'
        f'<span style="{typo["label_css"]};color:{pal["acc"]}">{industry.upper()}</span></div>'
    ) if industry else ""

    def section_label(text):
        # DA-aware kicker: attitude-driven visual signature
        lc = typo["label_css"].replace("font-size:9px;", "")
        _acc = pal["acc"]
        _p   = pal["p"]
        _bdr = pal.get("bdr", _p + "22")
        if att == "brutalist":
            # Heavy left bar, uppercase, primary color
            return (
                f'<div style="margin-bottom:{_sp["title_gap"]};padding-left:12px;'
                f'border-left:4px solid {_p}">'
                f'<h2 style="{lc};font-size:0.65rem;letter-spacing:.22em;text-transform:uppercase;'
                f'display:block;color:{_p};margin:0;font-weight:900">{text.upper()}</h2>'
                f'</div>'
            )
        elif att == "editorial":
            # Hairline bottom, italic, subdued
            return (
                f'<div style="margin-bottom:{_sp["title_gap"]};padding-bottom:8px;'
                f'border-bottom:1px solid {_bdr}">'
                f'<h2 style="{lc};font-size:0.7rem;letter-spacing:.12em;text-transform:uppercase;'
                f'display:block;color:{_acc};margin:0;font-style:italic">{text}</h2>'
                f'</div>'
            )
        elif att == "experimental":
            # Rotated diamond accent + spaced caps
            return (
                f'<div style="margin-bottom:{_sp["title_gap"]};display:flex;align-items:center;gap:10px">'
                f'<span style="display:inline-block;width:6px;height:6px;background:{_acc};'
                f'transform:rotate(45deg);flex-shrink:0"></span>'
                f'<h2 style="{lc};font-size:0.65rem;letter-spacing:.28em;text-transform:uppercase;'
                f'display:block;color:{_acc};margin:0">{text}</h2>'
                f'</div>'
            )
        elif att == "playful":
            # Pill badge
            return (
                f'<div style="margin-bottom:{_sp["title_gap"]}">'
                f'<span style="display:inline-block;background:{_acc}22;border-radius:100px;'
                f'padding:3px 12px">'
                f'<h2 style="{lc};font-size:0.65rem;letter-spacing:.14em;text-transform:uppercase;'
                f'display:inline;color:{_acc};margin:0;font-weight:700">{text}</h2>'
                f'</span></div>'
            )
        else:
            # product (default): accent bar 24×2px
            return (
                f'<div style="margin-bottom:{_sp["title_gap"]}">'
                f'<div style="width:24px;height:2px;background:{_acc};margin-bottom:10px"></div>'
                f'<h2 style="{lc};font-size:0.7rem;letter-spacing:.18em;text-transform:uppercase;'
                f'display:block;color:{_acc};margin:0">{text}</h2>'
                f'</div>'
            )

    # ── HEADING ADAPTATION ────────────────────────────────────────────────────
    # Rule: max 2 lines, no awkward breaks, font-size reduces dynamically.
    # All decisions driven by h1 length — no arbitrary values.
    import re as _re
    _h1_parts = [p.strip() for p in h1.split('\n') if p.strip()][:2]
    if not _h1_parts:
        _h1_parts = [name]
    # Truncate each part to 42 chars (≈ 2 lines at normal viewport)
    _h1_parts = [
        (p[:42].rsplit(' ', 1)[0] + '…') if len(p) > 42 else p
        for p in _h1_parts
    ]
    h1 = '\n'.join(_h1_parts)
    _h1_len = len(h1.replace('\n', ' '))
    # Adaptive font-size — scale down for longer headings
    _h1_adapted = typo["h1_css"]
    if _h1_len > 38:
        _h1_adapted = _re.sub(r'font-size:[^;]+;',
            'font-size:clamp(1.8rem,3.5vw,2.6rem);', _h1_adapted)
    elif _h1_len > 24:
        _h1_adapted = _re.sub(r'font-size:[^;]+;',
            'font-size:clamp(2.2rem,4.5vw,3.2rem);', _h1_adapted)
    # Overflow guard — always applied regardless of length
    _h1_adapted += ";overflow-wrap:break-word;word-break:break-word"
    # Mutate typo in-place so **typo unpacking uses the adapted version (no duplicate key)
    typo["h1_css"] = _h1_adapted

    # ── ACCENT SECONDARY ELEMENT ──────────────────────────────────────────────
    # Rule: accent must appear in hero even when no industry badge and single CTA.
    # Visual form is driven by att (art direction) — not arbitrary.
    _acc_color = pal["acc"]
    if not industry:
        if att == "brutalist":
            # Thick left-aligned bar
            _accent_mark = (
                f'<div style="width:48px;height:4px;background:{_acc_color};'
                f'margin-bottom:20px" aria-hidden="true"></div>'
            )
        elif att == "experimental":
            # Diamond glyph
            _accent_mark = (
                f'<div style="display:inline-flex;align-items:center;gap:8px;'
                f'margin-bottom:20px" aria-hidden="true">'
                f'<span style="display:inline-block;width:8px;height:8px;'
                f'background:{_acc_color};transform:rotate(45deg)"></span>'
                f'<span style="display:inline-block;width:8px;height:8px;'
                f'background:{_acc_color};opacity:.4;transform:rotate(45deg)"></span>'
                f'</div>'
            )
        elif att == "editorial":
            # Thin centered rule
            _accent_mark = (
                f'<div style="width:40px;height:1px;background:{_acc_color};'
                f'margin:0 auto 24px" aria-hidden="true"></div>'
            )
        else:
            # Default: short accent bar, centered
            _accent_mark = (
                f'<div style="width:36px;height:3px;background:{_acc_color};'
                f'margin:0 auto 20px;border-radius:2px" aria-hidden="true"></div>'
            )
    else:
        _accent_mark = ""   # industry badge already carries accent

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
        grid_gap=_sp["grid_gap"], title_gap=_sp["title_gap"],
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
        decorators=decorators, is_mono=is_mono,
        # copy
        headline_style=headline_style, cta_tone=cta_tone,
        h1=h1, sub=sub, cta_p=cta_p, cta_s=cta_s,
        sections=sections,
        # palette (flat)
        **pal,
        # typography (flat) — h1_css already replaced by adaptive version above
        **typo,
        # DesignDNA-derived additions (not in typo, no duplicate)
        _accent_mark=_accent_mark, # mandatory accent secondary element in hero
        # compat keys for section builders
        typo_att=att,
        visual_system=visual_system,
    )
    return rc


# ─────────────────────────────────────────────────────────────────────────────
# HERO BUILDERS v2 — no defaults, all from rc
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    main()
