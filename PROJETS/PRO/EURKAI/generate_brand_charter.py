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
    "geometric_sans":    "bold_condensed_geometric",
    "humanist_sans":     "neutral_sans",
    "editorial_serif":   "thin_elegant_serif",
    "editorial_sans":    "neutral_sans",
    "tech_mono":         "neutral_sans",
    "brutalist_display": "bold_condensed_geometric",
    "organic_serif":     "thin_elegant_serif",
    "playful_display":   "bold_condensed_geometric",
    "corporate_sans":    "neutral_sans",
    "craft_serif":       "thin_elegant_serif",
    "bold_condensed":    "bold_condensed_geometric",
    "warm_rounded":      "neutral_sans",
}

LAYOUT_TO_RADIUS: dict[str, str] = {
    "geometric_grid":  "small",
    "editorial_grid":  "none",
    "fluid_organic":   "large",
    "brutalist_grid":  "none",
    "compact_grid":    "small",
    "asymmetric":      "none",
    "playful_layout":  "large",
    "corporate_grid":  "small",
    "craft_layout":    "medium",
    "card_based":      "medium",
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
    radius = LAYOUT_TO_RADIUS.get(
        getattr(dna, "layout_style", None) or "", "medium"
    )
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
        layout_profile=LayoutProfile(),
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


def render_preview(preset: dict | None, css: str | None) -> str:
    if preset is None or css is None:
        return "<p style='color:#999'>Preview unavailable — theme generation failed.</p>"

    h_font = preset.get("font_family_headings", "sans-serif")
    b_font = preset.get("font_family_body", "sans-serif")
    gf_url = preset.get("font_google_url", "")

    font_import = f'@import url("{gf_url}");' if gf_url else ""

    preview_html = f"""
<div id="preview-root" style="font-family:var(--font-family-body,'{b_font}',sans-serif)">

  <!-- Hero -->
  <div class="preview-frame">
    <div class="preview-label">Hero section</div>
    <div class="preview-body" style="background:var(--color-primary,#2563eb);padding:48px 32px;text-align:center">
      <h1 style="font-family:var(--font-family-headings,'{h_font}',sans-serif);color:#fff;font-size:2.2rem;font-weight:700;margin-bottom:12px">
        Build something meaningful
      </h1>
      <p style="color:rgba(255,255,255,0.8);max-width:500px;margin:0 auto 24px">
        A platform built for people who care about craft, clarity, and impact.
      </p>
      <button class="btn btn-primary" style="margin-right:8px">Get started</button>
      <button class="btn" style="background:rgba(255,255,255,0.15);color:#fff;border:1px solid rgba(255,255,255,0.4)">Learn more</button>
    </div>
  </div>

  <!-- Buttons -->
  <div class="preview-frame" style="margin-top:16px">
    <div class="preview-label">Buttons</div>
    <div class="preview-body" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
      <button class="btn btn-primary">Primary</button>
      <button class="btn btn-secondary">Secondary</button>
      <button class="btn" style="background:transparent;color:var(--color-primary,#2563eb);border:1px solid var(--color-primary,#2563eb)">Outline</button>
      <button class="btn" style="background:transparent;color:#666;border:1px solid #ddd">Ghost</button>
    </div>
  </div>

  <!-- Cards -->
  <div class="preview-frame" style="margin-top:16px">
    <div class="preview-label">Cards</div>
    <div class="preview-body" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div class="card">
        <h3 style="font-family:var(--font-family-headings,'{h_font}',sans-serif);font-size:1.1rem;margin-bottom:8px">Feature title</h3>
        <p style="font-size:13px;color:#666;line-height:1.6">A short description of what this feature does and why it matters to your workflow.</p>
      </div>
      <div class="card">
        <h3 style="font-family:var(--font-family-headings,'{h_font}',sans-serif);font-size:1.1rem;margin-bottom:8px">Another feature</h3>
        <p style="font-size:13px;color:#666;line-height:1.6">Each card shares the same radius, shadow, and spacing tokens from the generated theme.</p>
      </div>
    </div>
  </div>

  <!-- Text block -->
  <div class="preview-frame" style="margin-top:16px">
    <div class="preview-label">Text block</div>
    <div class="preview-body">
      <h2 style="font-family:var(--font-family-headings,'{h_font}',sans-serif);font-size:1.6rem;margin-bottom:12px">
        Typography in context
      </h2>
      <p style="color:#444;line-height:1.7;margin-bottom:10px">
        This paragraph uses the generated body font at regular weight. The spacing, rhythm
        and font pairing reflect the <em>style preset</em> derived from the brief analysis.
      </p>
      <p style="color:#666;font-size:13px;line-height:1.7">
        Secondary text appears slightly smaller and lighter, maintaining the contrast
        hierarchy defined by the accessibility tokens.
      </p>
    </div>
  </div>
</div>"""

    # Scope the theme CSS inside #preview-root to avoid bleeding into the charter chrome
    scoped_css = css.replace(":root", "#preview-root")
    style_block = f"<style>{font_import}\n{scoped_css}</style>"

    return style_block + preview_html


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
                 render_preview(preset, css)),
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
