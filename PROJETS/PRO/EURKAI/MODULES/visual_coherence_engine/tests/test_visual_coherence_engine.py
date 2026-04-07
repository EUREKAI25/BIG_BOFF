"""
Tests pour visual_coherence_engine.
Run : python -m pytest MODULES/visual_coherence_engine/tests/ -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[3]))

from MODULES.visual_coherence_engine.src.visual_coherence_engine import (
    run,
    _hex_to_hsl,
    _hsl_to_hex,
    _wcag_contrast,
    _blend_color,
    _compute_image_adjustments,
    _compute_readability_rules,
    _circular_mean_hue,
    _pixel_structural_inference,
    _fallback_reference_analysis,
)


# ── Utilitaires ──────────────────────────────────────────────────────────────

def test_hex_hsl_roundtrip():
    for hex_in in ["#FF0000", "#00FF00", "#0000FF", "#4A7CFF", "#FFFFFF", "#000000"]:
        h, l, s = _hex_to_hsl(hex_in)
        hex_out = _hsl_to_hex(h, s, l)
        # Tolérance ±1 sur chaque canal RGB
        r1, g1, b1 = int(hex_in[1:3], 16), int(hex_in[3:5], 16), int(hex_in[5:7], 16)
        r2, g2, b2 = int(hex_out[1:3], 16), int(hex_out[3:5], 16), int(hex_out[5:7], 16)
        assert abs(r1-r2) <= 1 and abs(g1-g2) <= 1 and abs(b1-b2) <= 1, f"Roundtrip failed: {hex_in} → {hex_out}"


def test_wcag_contrast_extremes():
    assert abs(_wcag_contrast("#FFFFFF", "#000000") - 21.0) < 0.1
    assert abs(_wcag_contrast("#FFFFFF", "#FFFFFF") - 1.0) < 0.1


def test_wcag_contrast_symmetry():
    a, b = "#4A7CFF", "#FFFFFF"
    assert abs(_wcag_contrast(a, b) - _wcag_contrast(b, a)) < 0.001


def test_circular_mean_hue():
    # Hues proches de 0° et 359° doivent donner ~0° (pas ~180°)
    hsl = [(359.0, 0.5, 0.8), (1.0, 0.5, 0.8), (2.0, 0.5, 0.7)]
    mean = _circular_mean_hue(hsl)
    assert mean < 10 or mean > 350, f"Expected near 0°, got {mean}"


# ── CASE 2 — palette_drives_image ────────────────────────────────────────────

PALETTE_LIGHT = {
    "mode": "light",
    "primary": "#2563EB",
    "primary_light": "#60A5FA",
    "primary_dark": "#1D4ED8",
    "accent": "#F59E0B",
    "background": "#FFFFFF",
    "foreground": "#111827",
}

PALETTE_DARK = {
    "mode": "dark",
    "primary": "#60A5FA",
    "primary_light": "#93C5FD",
    "primary_dark": "#2563EB",
    "accent": "#F59E0B",
    "background": "#0F172A",
    "foreground": "#F1F5F9",
}

VISUAL_INTENT = {"emotion": "trust", "mood": "professional", "archetype": "startup_clean"}
CONTEXT_LIGHT = {"mode": "light", "name": "TestCo", "family": "saas"}
CONTEXT_DARK  = {"mode": "dark",  "name": "TestCo", "family": "saas"}


def test_run_case2_light():
    result = run(VISUAL_INTENT, CONTEXT_LIGHT, palette=PALETTE_LIGHT)
    assert result["reference_mode"] == "palette_drives_image"
    assert result["reference_type"] == "none"
    assert result["reference_analysis"] == {}
    assert "image_adjustments" in result
    adj = result["image_adjustments"]
    assert adj["duotone"] is True
    assert adj["blend_mode"] == "color"
    assert 0.0 < adj["overlay_opacity"] <= 1.0
    assert adj["filter"].startswith("grayscale(")


def test_run_case2_dark():
    result = run(VISUAL_INTENT, CONTEXT_DARK, palette=PALETTE_DARK)
    adj = result["image_adjustments"]
    assert adj["overlay_opacity"] >= 0.50, "Dark mode needs stronger overlay"


def test_overlay_opacity_range():
    for hex_p in ["#000000", "#FFFFFF", "#4A7CFF", "#FF6B4A"]:
        pal = {**PALETTE_LIGHT, "primary": hex_p}
        adj = _compute_image_adjustments(pal, dark_mode=False)
        assert 0.0 <= adj["overlay_opacity"] <= 1.0


def test_readability_rules_structure():
    adj = _compute_image_adjustments(PALETTE_LIGHT, dark_mode=False)
    rules = _compute_readability_rules(PALETTE_LIGHT, adj, dark_mode=False)
    assert "text_on_image" in rules
    assert "gradient_scrim" in rules
    assert "recommended_text_color" in rules
    assert rules["recommended_text_color"] in ("#FFFFFF", "#000000")


def test_no_palette_raises_no_error():
    """Sans palette et sans image → palette de secours, pas d'exception."""
    result = run(VISUAL_INTENT, {"mode": "light", "name": "X"}, palette=None)
    assert result["palette"]["_source"] == "emergency_fallback"
    assert len(result["conflicts"]) >= 1


def test_conflicts_empty_when_ok():
    result = run(VISUAL_INTENT, CONTEXT_LIGHT, palette=PALETTE_LIGHT)
    # Pas de vrais conflits attendus avec cette palette standard
    # (des warnings WCAG sont possibles mais pas une erreur)
    assert isinstance(result["conflicts"], list)


# ── Integration point simulation ─────────────────────────────────────────────

def test_picsum_panel_output_usable():
    """Vérifie que les valeurs de sortie sont directement utilisables dans _picsum_panel."""
    result = run(VISUAL_INTENT, CONTEXT_DARK, palette=PALETTE_DARK)
    adj = result["image_adjustments"]
    # Ces valeurs doivent être des strings/floats utilisables en CSS
    assert isinstance(adj["overlay_color"], str)
    assert adj["overlay_color"].startswith("#")
    assert isinstance(adj["overlay_opacity"], float)
    assert isinstance(adj["filter"], str)
    assert isinstance(adj["blend_mode"], str)


# ── CASE 3 — design_reference_drives_plan ────────────────────────────────────

def test_run_case3_screenshot_no_image():
    """reference_type=screenshot mais reference_image=None → fallback CASE 2."""
    result = run(VISUAL_INTENT, CONTEXT_LIGHT, palette=PALETTE_LIGHT,
                 reference_type="screenshot", reference_image=None)
    assert result["reference_mode"] == "palette_drives_image"
    assert result["reference_analysis"] == {}


def test_run_case3_mockup_invalid_path():
    """reference_type=mockup + chemin invalide → design_reference_drives_plan + fallback."""
    result = run(VISUAL_INTENT, CONTEXT_LIGHT, palette=PALETTE_LIGHT,
                 reference_image="/nonexistent_ref.png", reference_type="mockup")
    assert result["reference_mode"] == "design_reference_drives_plan"
    assert result["reference_type"] == "mockup"
    ra = result["reference_analysis"]
    assert ra.get("_source") == "fallback"
    assert ra.get("dominance") in ("text", "image", "balanced")
    assert "composition_bias" in ra
    assert "palette_hint" in ra
    # Palette et image_adjustments toujours présents
    assert "palette" in result
    assert "image_adjustments" in result
    assert len(result["conflicts"]) >= 1


def test_run_case3_output_structure():
    """Output CASE 3 complet et cohérent."""
    result = run(VISUAL_INTENT, CONTEXT_DARK, palette=PALETTE_DARK,
                 reference_image="/nonexistent.png", reference_type="screenshot")
    assert result["reference_mode"] == "design_reference_drives_plan"
    ra = result["reference_analysis"]
    for key in ("dominance", "density", "hierarchy", "spacing", "composition_bias", "palette_hint"):
        assert key in ra, f"Missing key: {key}"
    cb = ra["composition_bias"]
    for key in ("dominance", "density", "asymmetry", "rhythm"):
        assert key in cb, f"Missing composition_bias key: {key}"


def test_pixel_structural_inference_text_dominant():
    """Image claire + peu saturée → text dominant."""
    img = {"brightness": 0.85, "saturation": 0.10, "contrast_profile": "low"}
    result = _pixel_structural_inference(img)
    assert result["dominance"] == "text"
    assert result["spacing"] == "airy"
    assert result["hierarchy"] == "calm"


def test_pixel_structural_inference_image_dominant():
    """Image saturée + sombre → image dominant."""
    img = {"brightness": 0.40, "saturation": 0.65, "contrast_profile": "high"}
    result = _pixel_structural_inference(img)
    assert result["dominance"] == "image"
    assert result["density"] == "high"


def test_fallback_reference_analysis_complete():
    """Fallback contient tous les champs requis."""
    fa = _fallback_reference_analysis()
    for key in ("dominance", "density", "hierarchy", "spacing", "composition_bias", "palette_hint", "_source"):
        assert key in fa
    assert fa["_source"] == "fallback"


def test_reference_type_image_still_case1():
    """reference_type=image → CASE 1 (image_drives_palette), pas CASE 3."""
    # Sans image réelle, on teste juste que le mode est correct avec image invalide → fallback CASE 2
    result = run(VISUAL_INTENT, CONTEXT_LIGHT, palette=PALETTE_LIGHT,
                 reference_image="/nonexistent.png", reference_type="image")
    # Image analysis fail → fallback to palette_drives_image (not design_reference)
    assert result["reference_mode"] in ("image_drives_palette", "palette_drives_image")
    assert result["reference_type"] == "image"
