"""
Tests pour design_endpoints.
Run : python -m pytest MODULES/design_endpoints/tests/ -v

Dépendances externes (Playwright, Anthropic API) sont mockées.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).parents[4]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

_EP_DIR = Path(__file__).parents[1]  # MODULES/design_endpoints/


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _EP_DIR / f"{name}.py")
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Fixtures ────────────────────────────────────────────────────────────────

BRIEF   = "SaaS analytics B2B, trust, professional"
PROJECT = "Synaptic"

MOCK_PALETTE = {
    "mode": "light", "primary": "#2563EB", "primary_light": "#60A5FA",
    "primary_dark": "#1D4ED8", "accent": "#F59E0B",
    "background": "#FFFFFF", "foreground": "#111827",
    "text_primary": "#111827", "body_text_grade": "AAA",
    "_source": "test",
}

MOCK_VISUAL_INTENT = {
    "emotion": "trust", "mood": "professional", "archetype": "startup_clean",
    "composition_bias": {"dominance": "text", "density": "low", "asymmetry": "medium", "rhythm": "regular"},
    "typography_strategy": {"hierarchy_strength": "high", "weight_contrast": "medium"},
    "color_strategy": {"contrast": "medium"},
    "mode": "palette",
}

MOCK_AUDIT_RESULTS = [
    {
        "zone": "hero", "viewport": "desktop", "image_path": "hero.png",
        "readability_pass": True, "global_score": 85,
        "issues": [], "quick_fixes": [],
    }
]


# ── design.visual_intent.generate ───────────────────────────────────────────

def test_endpoint_visual_intent_generate():
    ep = _load("design.visual_intent.generate")
    assert ep.NAME == "design.visual_intent.generate"
    assert ep.CATEGORY == "design"
    assert ep.ACTION == "generate"
    result = ep.run(brief=BRIEF)
    assert isinstance(result, dict)
    assert len(result) > 0


def test_endpoint_visual_intent_with_reference_analysis():
    ep = _load("design.visual_intent.generate")
    ra = {"dominance": "text", "density": "low", "hierarchy": "calm",
          "spacing": "airy", "composition_bias": {}, "palette_hint": {}, "_source": "test"}
    result = ep.run(brief=BRIEF, reference_analysis=ra)
    assert isinstance(result, dict)


def test_endpoint_visual_intent_metadata():
    ep = _load("design.visual_intent.generate")
    assert hasattr(ep, "INPUTS")
    assert hasattr(ep, "OUTPUTS")
    assert "brief" in ep.INPUTS
    assert ep.INPUTS["brief"]["required"] is True


# ── design.palette.generate ─────────────────────────────────────────────────

def test_endpoint_palette_generate():
    ep_vi  = _load("design.visual_intent.generate")
    ep_pal = _load("design.palette.generate")
    vi     = ep_vi.run(brief=BRIEF)
    result = ep_pal.run(visual_intent=vi)
    assert isinstance(result, dict)
    # Palette doit contenir les clés de base
    for key in ("primary", "background"):
        assert key in result, f"Missing key: {key}"


def test_endpoint_palette_with_context():
    ep_vi  = _load("design.visual_intent.generate")
    ep_pal = _load("design.palette.generate")
    vi     = ep_vi.run(brief=BRIEF)
    result = ep_pal.run(visual_intent=vi, context={"mode": "dark", "name": PROJECT})
    assert isinstance(result, dict)


def test_endpoint_palette_metadata():
    ep = _load("design.palette.generate")
    assert ep.NAME == "design.palette.generate"
    assert "visual_intent" in ep.INPUTS
    assert ep.INPUTS["visual_intent"]["required"] is True


# ── design.coherence.apply ───────────────────────────────────────────────────

def test_endpoint_coherence_apply_case2():
    ep_vi  = _load("design.visual_intent.generate")
    ep_pal = _load("design.palette.generate")
    ep_coh = _load("design.coherence.apply")
    vi      = ep_vi.run(brief=BRIEF)
    palette = ep_pal.run(visual_intent=vi)
    result  = ep_coh.run(visual_intent=vi, context={"mode": "light", "name": PROJECT}, palette=palette)
    assert result["reference_mode"] == "palette_drives_image"
    assert result["reference_type"] == "none"
    assert isinstance(result["conflicts"], list)
    assert "image_adjustments" in result
    assert "readability_rules" in result


def test_endpoint_coherence_apply_case3_fallback():
    ep_vi  = _load("design.visual_intent.generate")
    ep_pal = _load("design.palette.generate")
    ep_coh = _load("design.coherence.apply")
    vi      = ep_vi.run(brief=BRIEF)
    palette = ep_pal.run(visual_intent=vi)
    result  = ep_coh.run(
        visual_intent=vi, context={"mode": "light", "name": PROJECT},
        palette=palette, reference_image="/nonexistent.png", reference_type="mockup",
    )
    assert result["reference_mode"] == "design_reference_drives_plan"
    ra = result["reference_analysis"]
    assert ra.get("_source") == "fallback"
    for key in ("dominance", "density", "hierarchy", "spacing"):
        assert key in ra


def test_endpoint_coherence_metadata():
    ep = _load("design.coherence.apply")
    assert ep.NAME == "design.coherence.apply"
    assert ep.ACTION == "apply"
    assert "reference_mode" in ep.OUTPUTS


# ── design.plan.generate ────────────────────────────────────────────────────

def test_endpoint_plan_generate():
    ep_vi   = _load("design.visual_intent.generate")
    ep_plan = _load("design.plan.generate")
    vi      = ep_vi.run(brief=BRIEF)
    result  = ep_plan.run(brief=BRIEF, seed=42, visual_intent=vi)
    assert isinstance(result, dict)
    assert "layout_strategy" in result or "section_types" in result


def test_endpoint_plan_deterministic():
    ep_vi   = _load("design.visual_intent.generate")
    ep_plan = _load("design.plan.generate")
    vi      = ep_vi.run(brief=BRIEF)
    plan_a  = ep_plan.run(brief=BRIEF, seed=99, visual_intent=vi)
    plan_b  = ep_plan.run(brief=BRIEF, seed=99, visual_intent=vi)
    assert plan_a.get("seed") == plan_b.get("seed")


def test_endpoint_plan_with_reference_analysis():
    ep_plan = _load("design.plan.generate")
    ra = {
        "dominance": "image", "density": "high", "hierarchy": "aggressive",
        "spacing": "tight", "composition_bias": {"dominance": "image", "density": "high",
        "asymmetry": "high", "rhythm": "chaotic"}, "palette_hint": {}, "_source": "test",
    }
    result = ep_plan.run(brief=BRIEF, seed=42, reference_analysis=ra)
    assert isinstance(result, dict)


def test_endpoint_plan_metadata():
    ep = _load("design.plan.generate")
    assert ep.NAME == "design.plan.generate"
    assert ep.INPUTS["brief"]["required"] is True
    assert "plan" in ep.OUTPUTS


# ── design.render.page ───────────────────────────────────────────────────────

def test_endpoint_render_page_basic():
    ep = _load("design.render.page")
    result = ep.run(project_name=PROJECT, brief_text=BRIEF)
    assert isinstance(result["html"], str)
    assert len(result["html"]) > 100
    assert "<!doctype" in result["html"].lower() or "<html" in result["html"].lower()
    assert result["project_name"] == PROJECT
    assert result["seed"] == 42


def test_endpoint_render_page_with_palette():
    ep_vi   = _load("design.visual_intent.generate")
    ep_pal  = _load("design.palette.generate")
    ep_rend = _load("design.render.page")
    vi      = ep_vi.run(brief=BRIEF)
    palette = ep_pal.run(visual_intent=vi)
    result  = ep_rend.run(project_name=PROJECT, brief_text=BRIEF, cp_palette=palette)
    assert "<html" in result["html"].lower() or "<!doctype" in result["html"].lower()


def test_endpoint_render_page_site_families():
    ep = _load("design.render.page")
    for family in ["product_saas", "ecommerce_catalog", "event_campaign", "editorial_magazine"]:
        result = ep.run(project_name=PROJECT, brief_text=BRIEF, site_family=family, seed=42)
        assert len(result["html"]) > 100, f"Empty HTML for family: {family}"
        assert result["site_family"] == family


def test_endpoint_render_page_metadata():
    ep = _load("design.render.page")
    assert ep.NAME == "design.render.page"
    assert ep.INPUTS["project_name"]["required"] is True
    assert "html" in ep.OUTPUTS


# ── design.capture.page (mock Playwright) ───────────────────────────────────

def test_endpoint_capture_page_mock():
    ep = _load("design.capture.page")

    mock_result = MagicMock()
    mock_result.to_dict.return_value = {
        "ok": True, "path": "output/captures/synaptic/full/hero.png",
        "site": "synaptic", "page": "full", "viewport": "desktop",
        "zone": "hero", "error": None, "duration_ms": 120.0,
    }

    with patch("screenshot_capture.src.screenshot_capture.ScreenshotCapture") as MockCapture:
        mock_instance = MockCapture.return_value
        mock_instance.capture_all_zones.return_value = [mock_result]

        result = ep.run(url="http://localhost/test.html", site="synaptic", page="full")
        assert "captures" in result
        assert "ok_count" in result
        assert "fail_count" in result


def test_endpoint_capture_page_metadata():
    ep = _load("design.capture.page")
    assert ep.NAME == "design.capture.page"
    assert ep.INPUTS["url"]["required"] is True
    assert "captures" in ep.OUTPUTS


# ── design.audit.page (mock API) ────────────────────────────────────────────

def test_endpoint_audit_page_mock():
    ep = _load("design.audit.page")

    from vision_audit.src.vision_audit import AuditResult
    mock_ar = AuditResult(
        readability_pass=True, global_score=88,
        issues=[], quick_fixes=[], zone="hero", viewport="desktop",
    )

    with patch("vision_audit.src.vision_audit.VisionAudit") as MockVA:
        mock_instance = MockVA.return_value
        mock_instance.audit_page.return_value = [mock_ar]

        result = ep.run(captures=MOCK_AUDIT_RESULTS)
        assert "results" in result
        assert "summary" in result
        assert "pass" in result
        assert "score" in result


def test_endpoint_audit_page_metadata():
    ep = _load("design.audit.page")
    assert ep.NAME == "design.audit.page"
    assert ep.INPUTS["captures"]["required"] is True


# ── design.fix.page ──────────────────────────────────────────────────────────

def test_endpoint_fix_page_converged():
    """Toutes zones passent → retourne HTML inchangé, converged=True."""
    ep = _load("design.fix.page")
    passing_results = [{
        "zone": "hero", "global_score": 85, "readability_pass": True,
        "issues": [], "quick_fixes": [], "viewport": "desktop", "image_path": "",
    }]
    html   = "<html><body><h1>Test</h1></body></html>"
    result = ep.run(html=html, audit_results=passing_results)
    assert result["converged"] is True
    assert result["html"] == html
    assert result["patch_zones"] == []


def test_endpoint_fix_page_applies_patch():
    """Zone failing → patch appliqué, HTML modifié."""
    ep = _load("design.fix.page")
    html = """
    <!doctype html><html><body>
    <div data-audit="hero" style="background:#fff">
      <h1 style="color:#fff">Test heading</h1>
    </div>
    </body></html>
    """
    failing_results = [{
        "zone": "hero", "global_score": 45, "readability_pass": False,
        "issues": [{"zone": "hero", "problem": "low contrast",
                    "severity": "high", "confidence": 0.9, "suggested_fix": "increase text contrast"}],
        "quick_fixes": ["increase text contrast"],
        "viewport": "desktop", "image_path": "hero.png",
    }]
    result = ep.run(html=html, audit_results=failing_results)
    assert isinstance(result["html"], str)
    assert result["converged"] is False
    assert "hero" in result["final_scores"]


def test_endpoint_fix_page_output_structure():
    ep = _load("design.fix.page")
    result = ep.run(
        html="<html><body>Test</body></html>",
        audit_results=[{
            "zone": "nav", "global_score": 60, "readability_pass": False,
            "issues": [], "quick_fixes": [], "viewport": "desktop", "image_path": "",
        }],
    )
    for key in ("html", "converged", "iteration", "final_scores", "patch_zones"):
        assert key in result, f"Missing key: {key}"


def test_endpoint_fix_page_metadata():
    ep = _load("design.fix.page")
    assert ep.NAME == "design.fix.page"
    assert ep.INPUTS["html"]["required"] is True
    assert ep.INPUTS["audit_results"]["required"] is True


# ── design.brand.generate ─────────────────────────────────────────────────────

def test_endpoint_brand_generate_structure():
    ep_vi  = _load("design.visual_intent.generate")
    ep_pal = _load("design.palette.generate")
    ep_br  = _load("design.brand.generate")
    vi      = ep_vi.run(brief=BRIEF)
    palette = ep_pal.run(visual_intent=vi)
    result  = ep_br.run(brief=BRIEF, visual_intent=vi, palette=palette,
                        context={"name": PROJECT, "mode": "light", "family": "saas"})
    for key in ("brand_core", "logo", "icons", "typography", "visual_signature", "_meta"):
        assert key in result, f"Missing key: {key}"


def test_endpoint_brand_generate_logo_keys():
    ep_vi  = _load("design.visual_intent.generate")
    ep_pal = _load("design.palette.generate")
    ep_br  = _load("design.brand.generate")
    vi      = ep_vi.run(brief=BRIEF)
    palette = ep_pal.run(visual_intent=vi)
    result  = ep_br.run(brief=BRIEF, visual_intent=vi, palette=palette,
                        context={"name": PROJECT, "mode": "light"})
    logo = result["logo"]
    for key in ("type", "style", "construction", "variations", "generation_prompt", "svg_spec"):
        assert key in logo, f"Missing logo key: {key}"
    assert isinstance(logo["variations"], list)
    assert PROJECT in logo["generation_prompt"]


def test_endpoint_brand_generate_reference_mode():
    """Avec reference dict → _meta.context_key présent, overrides appliqués."""
    ep_vi  = _load("design.visual_intent.generate")
    ep_pal = _load("design.palette.generate")
    ep_br  = _load("design.brand.generate")
    vi      = ep_vi.run(brief=BRIEF)
    palette = ep_pal.run(visual_intent=vi)
    ref = {"dominance": "text", "density": "low", "hierarchy": "calm",
           "spacing": "airy", "composition_bias": {}, "palette_hint": {}, "_source": "test"}
    result = ep_br.run(brief=BRIEF, visual_intent=vi, palette=palette,
                       context={"name": PROJECT, "mode": "light"}, reference=ref)
    assert result["_meta"]["context_key"] != ""
    assert "minimal" in result["logo"]["style"].lower() or "logotype" in result["logo"]["type"]


def test_endpoint_brand_generate_metadata():
    ep = _load("design.brand.generate")
    assert ep.NAME == "design.brand.generate"
    assert ep.CATEGORY == "design"
    assert ep.INPUTS["brief"]["required"] is True
    assert ep.INPUTS["context"]["required"] is True
    assert "brand_core" in ep.OUTPUTS


# ── design.logo.generate ──────────────────────────────────────────────────────

def test_endpoint_logo_generate_returns_logo():
    ep_vi  = _load("design.visual_intent.generate")
    ep_pal = _load("design.palette.generate")
    ep_lg  = _load("design.logo.generate")
    vi      = ep_vi.run(brief=BRIEF)
    palette = ep_pal.run(visual_intent=vi)
    result  = ep_lg.run(brief=BRIEF, visual_intent=vi, palette=palette,
                        context={"name": PROJECT, "mode": "light"})
    for key in ("type", "style", "construction", "variations", "generation_prompt", "svg_spec"):
        assert key in result, f"Missing key: {key}"
    # Doit retourner le logo seulement, pas brand_core
    assert "brand_core" not in result


def test_endpoint_logo_generate_svg_spec():
    ep_vi  = _load("design.visual_intent.generate")
    ep_pal = _load("design.palette.generate")
    ep_lg  = _load("design.logo.generate")
    vi      = ep_vi.run(brief=BRIEF)
    palette = ep_pal.run(visual_intent=vi)
    result  = ep_lg.run(brief=BRIEF, visual_intent=vi, palette=MOCK_PALETTE,
                        context={"name": PROJECT, "mode": "light"})
    svg = result["svg_spec"]
    assert svg["primary_color"] == MOCK_PALETTE["primary"]
    assert svg["background"] == MOCK_PALETTE["background"]


def test_endpoint_logo_generate_metadata():
    ep = _load("design.logo.generate")
    assert ep.NAME == "design.logo.generate"
    assert ep.INPUTS["brief"]["required"] is True
    assert "type" in ep.OUTPUTS


# ── design.icons.generate ─────────────────────────────────────────────────────

def test_endpoint_icons_generate_returns_icons():
    ep_vi   = _load("design.visual_intent.generate")
    ep_pal  = _load("design.palette.generate")
    ep_ic   = _load("design.icons.generate")
    vi       = ep_vi.run(brief=BRIEF)
    palette  = ep_pal.run(visual_intent=vi)
    result   = ep_ic.run(brief=BRIEF, visual_intent=vi, palette=palette,
                         context={"name": PROJECT, "mode": "light"})
    for key in ("style", "stroke", "corner_style", "consistency_rules", "generation_prompt", "examples"):
        assert key in result, f"Missing key: {key}"
    assert isinstance(result["consistency_rules"], list)
    assert len(result["examples"]) >= 4


def test_endpoint_icons_generate_metadata():
    ep = _load("design.icons.generate")
    assert ep.NAME == "design.icons.generate"
    assert ep.INPUTS["visual_intent"]["required"] is True
    assert "style" in ep.OUTPUTS


# ── design.typography.generate ───────────────────────────────────────────────

def test_endpoint_typography_generate_returns_typography():
    ep_vi   = _load("design.visual_intent.generate")
    ep_pal  = _load("design.palette.generate")
    ep_ty   = _load("design.typography.generate")
    vi       = ep_vi.run(brief=BRIEF)
    palette  = ep_pal.run(visual_intent=vi)
    result   = ep_ty.run(brief=BRIEF, visual_intent=vi, palette=palette,
                         context={"name": PROJECT, "mode": "light"})
    for key in ("primary_font", "secondary_font", "fallbacks", "style", "pairing_logic", "custom_font_possible"):
        assert key in result, f"Missing key: {key}"
    assert result["primary_font"] != "Inter"


def test_endpoint_typography_generate_context_gaming():
    """Context gaming → Rajdhani."""
    ep_vi   = _load("design.visual_intent.generate")
    ep_pal  = _load("design.palette.generate")
    ep_ty   = _load("design.typography.generate")
    vi_gaming = {**MOCK_VISUAL_INTENT, "context": {"product_type": "gaming"}}
    palette   = ep_pal.run(visual_intent=vi_gaming)
    result    = ep_ty.run(brief="Esports platform", visual_intent=vi_gaming, palette=palette,
                          context={"name": "FrostByte", "mode": "dark", "family": "gaming"})
    assert result["primary_font"] == "Rajdhani"


def test_endpoint_typography_generate_metadata():
    ep = _load("design.typography.generate")
    assert ep.NAME == "design.typography.generate"
    assert ep.INPUTS["brief"]["required"] is True
    assert "primary_font" in ep.OUTPUTS
