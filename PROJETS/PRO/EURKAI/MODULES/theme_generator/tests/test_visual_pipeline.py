"""
Tests du pipeline visuel :
  StyleDNA JSON → ThemePreset → CSS

Lance avec : pytest tests/test_visual_pipeline.py -v
"""

import json
import sys
from pathlib import Path

# Résolution du package sans pip install
MODULE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MODULE_ROOT))

from theme_generator.style_dna import StyleDNA, style_dna_from_dict
from theme_generator.visual_analysis import VisualSource, JsonVisualAnalysis, MockVisualAnalysis, visual_analysis
from theme_generator.theme_translation import translate
from theme_generator.generator import ThemeGenerator

FIXTURES = Path(__file__).parent / "fixtures"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


# ─── Tests StyleDNA ──────────────────────────────────────────────────────────

def test_style_dna_from_dict_startup():
    data = load_fixture("style_dna_startup.json")
    dna = style_dna_from_dict(data)
    assert dna.emotional_tone == "calm"
    assert dna.complexity_level == "moderate"
    assert dna.palette_profile.dominant == ["#1a53ff", "#001f5c"]
    assert dna.typography_profile.display == "neutral_sans"
    assert dna.geometry_profile.border_radius == "small"


def test_style_dna_from_dict_luxury():
    data = load_fixture("style_dna_luxury.json")
    dna = style_dna_from_dict(data)
    assert dna.emotional_tone == "premium"
    assert dna.complexity_level == "minimal"
    assert dna.palette_profile.accent == ["#c9a84c"]


def test_style_dna_from_dict_brutalist():
    data = load_fixture("style_dna_brutalist.json")
    dna = style_dna_from_dict(data)
    assert dna.emotional_tone == "bold"
    assert dna.geometry_profile.border_radius == "none"
    assert "brutalist" in dna.aesthetic_tags


# ─── Tests visual_analysis adapters ──────────────────────────────────────────

def test_json_adapter_loads_from_file():
    adapter = JsonVisualAnalysis()
    source  = VisualSource(type="manual", path=FIXTURES / "style_dna_startup.json")
    dna = adapter.analyze(source)
    assert isinstance(dna, StyleDNA)
    assert dna.emotional_tone == "calm"


def test_json_adapter_loads_from_raw_json():
    data   = load_fixture("style_dna_luxury.json")
    source = VisualSource(type="manual", raw_json=data)
    dna    = visual_analysis(source, backend="json")
    assert isinstance(dna, StyleDNA)
    assert dna.emotional_tone == "premium"


def test_mock_adapter_returns_style_dna():
    adapter = MockVisualAnalysis()
    source  = VisualSource(type="manual")
    dna     = adapter.analyze(source)
    assert isinstance(dna, StyleDNA)
    assert dna.palette_profile.dominant


# ─── Tests theme_translation ─────────────────────────────────────────────────

def test_translate_produces_required_fields():
    data    = load_fixture("style_dna_startup.json")
    dna     = style_dna_from_dict(data)
    preset  = translate(dna)

    assert "color_system" in preset
    assert "primary" in preset["color_system"]
    assert "base" in preset["color_system"]["primary"]
    assert "style_preset_name" in preset
    assert "animation_style" in preset
    assert "font_family_headings" in preset
    assert "font_family_body" in preset
    assert "font_google_url" in preset


def test_translate_luxury_uses_minimal_preset():
    data   = load_fixture("style_dna_luxury.json")
    dna    = style_dna_from_dict(data)
    preset = translate(dna)
    assert preset["style_preset_name"] == "minimal"
    assert preset["animation_style"] == "subtle"


def test_translate_brutalist_uses_bold_preset():
    data   = load_fixture("style_dna_brutalist.json")
    dna    = style_dna_from_dict(data)
    preset = translate(dna)
    assert preset["style_preset_name"] == "bold"
    # border_radius "none" → style_overrides
    assert "style_overrides" in preset
    assert preset["style_overrides"]["radius"]["sm"] == "0px"


def test_translate_colors_are_rgb_strings():
    data   = load_fixture("style_dna_startup.json")
    dna    = style_dna_from_dict(data)
    preset = translate(dna)
    base   = preset["color_system"]["primary"]["base"]
    assert base.startswith("rgb("), f"Attendu rgb(...), obtenu : {base}"


def test_translate_google_fonts_url_is_valid():
    data   = load_fixture("style_dna_luxury.json")
    dna    = style_dna_from_dict(data)
    preset = translate(dna)
    url    = preset["font_google_url"]
    assert "fonts.googleapis.com" in url
    assert "display=swap" in url


# ─── Test roundtrip complet ───────────────────────────────────────────────────

def test_roundtrip_startup_json_to_css():
    """
    Roundtrip complet :
      style_dna.json → StyleDNA → ThemePreset → CSS
    """
    # 1. Charger le StyleDNA depuis JSON
    source = VisualSource(type="manual", path=FIXTURES / "style_dna_startup.json")
    dna    = visual_analysis(source, backend="json")
    assert isinstance(dna, StyleDNA)

    # 2. Traduire en ThemePreset
    preset = translate(dna)
    assert "color_system" in preset

    # 3. Générer le CSS
    generator = ThemeGenerator()
    css = generator.generate(preset)

    assert ":root {" in css
    assert "--color-primary:" in css
    assert "--font-family-headings:" in css
    assert "Inter" in css or "Manrope" in css  # neutral_sans → Inter ou Manrope
    assert "fonts.googleapis.com" in css


def test_roundtrip_luxury_json_to_css():
    source = VisualSource(type="manual", path=FIXTURES / "style_dna_luxury.json")
    dna    = visual_analysis(source, backend="json")
    preset = translate(dna)
    css    = ThemeGenerator().generate(preset)

    assert ":root {" in css
    # luxury → thin_elegant_serif → Playfair Display
    assert "Playfair Display" in css or "Cormorant" in css or "EB Garamond" in css


def test_roundtrip_does_not_break_existing_preset():
    """
    Vérifie que le ThemeGenerator fonctionne toujours avec un ThemePreset
    passé directement (rétrocompat v0.1.0).
    """
    legacy_preset = {
        "color_system": {
            "primary":   {"base": "rgb(102, 126, 234)", "light": "rgb(118, 142, 250)", "dark": "rgb(85, 104, 211)"},
            "secondary": {"base": "rgb(118, 75, 162)",  "light": "rgb(134, 91, 178)",  "dark": "rgb(102, 59, 146)"},
        },
        "style_preset_name":    "rounded",
        "animation_style":      "subtle",
        "font_family_headings": "Inter",
        "font_family_body":     "Inter",
        "font_weights":         {"normal": 400, "medium": 500, "bold": 700},
    }
    css = ThemeGenerator().generate(legacy_preset)
    assert ":root {" in css
    assert "--color-primary:" in css
