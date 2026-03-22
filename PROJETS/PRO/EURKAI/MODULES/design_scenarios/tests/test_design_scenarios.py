"""
Tests pour design_scenarios.
Run : python -m pytest MODULES/design_scenarios/tests/ -v

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

_SC_DIR = Path(__file__).parents[1]  # MODULES/design_scenarios/


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _SC_DIR / f"{name}.py")
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Fixtures ────────────────────────────────────────────────────────────────

BRIEF   = "Agence design minimaliste, Berlin, premium"
PROJECT = "Forma Studio"

MOCK_AUDIT_PASS = {
    "results": [{"zone": "hero", "global_score": 88, "readability_pass": True, "issues": [], "quick_fixes": [], "viewport": "desktop", "image_path": ""}],
    "summary": {"pass": 1, "fail": 0, "avg_score": 88, "total": 1},
    "pass": True, "score": 88,
}

MOCK_AUDIT_FAIL = {
    "results": [{"zone": "hero", "global_score": 55, "readability_pass": False,
                 "issues": [{"zone": "hero", "problem": "low contrast", "severity": "high", "confidence": 0.9, "suggested_fix": "darken"}],
                 "quick_fixes": ["darken overlay"], "viewport": "desktop", "image_path": ""}],
    "summary": {"pass": 0, "fail": 1, "avg_score": 55, "total": 1},
    "pass": False, "score": 55,
}


# ── design.page.generate_basic ───────────────────────────────────────────────

def test_scenario_page_generate_basic_structure():
    sc = _load("design.page.generate_basic")
    result = sc.run(brief=BRIEF, project_name=PROJECT, seed=42)
    for key in ("html", "visual_intent", "palette", "plan", "trace"):
        assert key in result, f"Missing key: {key}"


def test_scenario_page_generate_basic_html():
    sc = _load("design.page.generate_basic")
    result = sc.run(brief=BRIEF, project_name=PROJECT)
    assert len(result["html"]) > 100
    assert "<!doctype" in result["html"].lower() or "<html" in result["html"].lower()


def test_scenario_page_generate_basic_trace():
    sc = _load("design.page.generate_basic")
    result = sc.run(brief=BRIEF, project_name=PROJECT, seed=42)
    trace = result["trace"]
    assert len(trace) == 4
    for i, step in enumerate(trace, 1):
        assert step["step"] == i
        assert step["ok"] is True


def test_scenario_page_generate_basic_steps():
    sc = _load("design.page.generate_basic")
    assert sc.NAME == "design.page.generate_basic"
    assert len(sc.STEPS) == 4
    endpoints = [s["endpoint"] for s in sc.STEPS]
    assert "design.visual_intent.generate" in endpoints
    assert "design.render.page" in endpoints


def test_scenario_page_generate_basic_site_families():
    sc = _load("design.page.generate_basic")
    for family in ["product_saas", "ecommerce_catalog", ""]:
        result = sc.run(brief=BRIEF, project_name=PROJECT, site_family=family)
        assert len(result["html"]) > 100


def test_scenario_page_generate_basic_deterministic():
    sc = _load("design.page.generate_basic")
    r1 = sc.run(brief=BRIEF, project_name=PROJECT, seed=77)
    r2 = sc.run(brief=BRIEF, project_name=PROJECT, seed=77)
    # Même seed → mêmes plans
    assert r1["plan"].get("seed") == r2["plan"].get("seed")


# ── design.page.generate_from_image ──────────────────────────────────────────

def test_scenario_page_generate_from_image_no_image():
    """Image invalide → fallback palette_drives_image, pas d'erreur."""
    sc = _load("design.page.generate_from_image")
    result = sc.run(brief=BRIEF, project_name=PROJECT, reference_image="/nonexistent.jpg")
    for key in ("html", "visual_intent", "coherence", "plan", "trace"):
        assert key in result
    # Mode peut être image_drives_palette ou palette_drives_image selon fallback
    assert result["coherence"]["reference_mode"] in ("image_drives_palette", "palette_drives_image")


def test_scenario_page_generate_from_image_trace_steps():
    sc = _load("design.page.generate_from_image")
    result = sc.run(brief=BRIEF, project_name=PROJECT, reference_image="/nonexistent.png")
    assert len(result["trace"]) == 4
    endpoints = [s["endpoint"] for s in result["trace"]]
    assert "design.coherence.apply" in endpoints


def test_scenario_page_generate_from_image_metadata():
    sc = _load("design.page.generate_from_image")
    assert sc.NAME == "design.page.generate_from_image"
    assert sc.INPUTS["reference_image"]["required"] is True


# ── design.page.generate_from_mockup ─────────────────────────────────────────

def test_scenario_page_generate_from_mockup_fallback():
    """Mockup invalide → reference_analysis._source=fallback, pipeline continue."""
    sc = _load("design.page.generate_from_mockup")
    result = sc.run(brief=BRIEF, project_name=PROJECT, reference_image="/nonexistent.png")
    for key in ("html", "visual_intent", "palette", "coherence", "reference_analysis", "plan", "trace"):
        assert key in result
    assert result["coherence"]["reference_mode"] == "design_reference_drives_plan"
    assert result["reference_analysis"].get("_source") == "fallback"


def test_scenario_page_generate_from_mockup_trace_steps():
    sc = _load("design.page.generate_from_mockup")
    result = sc.run(brief=BRIEF, project_name=PROJECT, reference_image="/nonexistent.png")
    assert len(result["trace"]) == 5
    step3 = result["trace"][2]
    assert step3["endpoint"] == "design.coherence.apply"
    assert step3["reference_mode"] == "design_reference_drives_plan"


def test_scenario_page_generate_from_mockup_screenshot_type():
    sc = _load("design.page.generate_from_mockup")
    result = sc.run(brief=BRIEF, project_name=PROJECT,
                    reference_image="/nonexistent.png", reference_type="screenshot")
    assert result["coherence"]["reference_type"] == "screenshot"


def test_scenario_page_generate_from_mockup_metadata():
    sc = _load("design.page.generate_from_mockup")
    assert sc.NAME == "design.page.generate_from_mockup"
    assert len(sc.STEPS) == 5


# ── design.page.generate_full (mock capture+audit) ───────────────────────────

def test_scenario_page_generate_full_without_capture():
    """Sans Playwright disponible → capture retourne 0 résultats, audit skippé, HTML retourné."""
    import types
    sc = _load("design.page.generate_full")
    # Remplacer _ep_capture par un mock qui retourne 0 captures
    sc._ep_capture = types.SimpleNamespace(
        run=lambda **kw: {"captures": [], "ok_count": 0, "fail_count": 0}
    )
    # Remplacer _serve_html_local pour ne pas démarrer de vrai serveur
    sc._serve_html_local = lambda html, port: (None, None, "http://127.0.0.1/mock.html")

    result = sc.run(brief=BRIEF, project_name=PROJECT, seed=42)
    assert "html" in result
    assert len(result["html"]) > 100
    # captures vides → audit non appelé
    assert result["captures"] == []
    assert result["audit"]["results"] == []


def test_scenario_page_generate_full_structure():
    sc = _load("design.page.generate_full")
    with patch("screenshot_capture.src.screenshot_capture.ScreenshotCapture",
               side_effect=Exception("no playwright")):
        result = sc.run(brief=BRIEF, project_name=PROJECT)
    for key in ("html", "visual_intent", "palette", "coherence", "plan", "captures", "audit", "trace"):
        assert key in result


def test_scenario_page_generate_full_metadata():
    sc = _load("design.page.generate_full")
    assert sc.NAME == "design.page.generate_full"
    assert len(sc.STEPS) == 7
    assert sc.INPUTS["brief"]["required"] is True


# ── design.page.audit (mock) ─────────────────────────────────────────────────

def test_scenario_page_audit_mock():
    import types
    sc = _load("design.page.audit")

    mock_capture_dict = {
        "ok": True, "path": "hero.png", "zone": "hero",
        "site": "test", "page": "audit", "viewport": "desktop",
        "error": None, "duration_ms": 100.0,
    }
    # Patcher _ep_capture directement dans le module chargé
    sc._ep_capture = types.SimpleNamespace(
        run=lambda **kw: {"captures": [mock_capture_dict], "ok_count": 1, "fail_count": 0}
    )
    sc._ep_audit = types.SimpleNamespace(
        run=lambda **kw: {"results": [], "summary": {"pass": 1, "fail": 0, "avg_score": 90, "total": 1}, "pass": True, "score": 90}
    )

    result = sc.run(url="http://localhost/test.html", site="test")
    assert "captures" in result
    assert "audit" in result
    assert "trace" in result
    assert len(result["trace"]) == 2


def test_scenario_page_audit_metadata():
    sc = _load("design.page.audit")
    assert sc.NAME == "design.page.audit"
    assert len(sc.STEPS) == 2
    assert sc.INPUTS["url"]["required"] is True


# ── design.page.fix ───────────────────────────────────────────────────────────

def test_scenario_page_fix_converged():
    sc = _load("design.page.fix")
    passing = [{"zone": "hero", "global_score": 88, "readability_pass": True,
                "issues": [], "quick_fixes": [], "viewport": "desktop", "image_path": ""}]
    result = sc.run(html="<html><body>OK</body></html>", audit_results=passing)
    assert result["converged"] is True
    assert result["iterations_run"] == 1


def test_scenario_page_fix_applies_iterations():
    sc = _load("design.page.fix")
    failing = [{
        "zone": "hero", "global_score": 45, "readability_pass": False,
        "issues": [{"zone": "hero", "problem": "contrast", "severity": "high",
                    "confidence": 0.9, "suggested_fix": "darken"}],
        "quick_fixes": ["darken"], "viewport": "desktop", "image_path": "hero.png",
    }]
    html   = "<html><body><div data-audit='hero'><h1 style='color:#fff'>Test</h1></div></body></html>"
    result = sc.run(html=html, audit_results=failing, max_iterations=3)
    assert isinstance(result["html"], str)
    assert result["iterations_run"] >= 1
    assert "hero" in result["final_scores"]


def test_scenario_page_fix_trace_structure():
    sc = _load("design.page.fix")
    passing = [{"zone": "nav", "global_score": 80, "readability_pass": True,
                "issues": [], "quick_fixes": [], "viewport": "desktop", "image_path": ""}]
    result = sc.run(html="<html><body>X</body></html>", audit_results=passing)
    trace = result["trace"]
    assert len(trace) >= 1
    assert trace[0]["endpoint"] == "design.fix.page"
    assert "final_scores" in trace[0]


def test_scenario_page_fix_metadata():
    sc = _load("design.page.fix")
    assert sc.NAME == "design.page.fix"
    assert len(sc.STEPS) == 1
    assert sc.INPUTS["html"]["required"] is True
    assert sc.INPUTS["audit_results"]["required"] is True


# ── design.brand.generate_full ────────────────────────────────────────────────

def test_scenario_brand_generate_full_structure():
    sc = _load("design.brand.generate_full")
    result = sc.run(brief=BRIEF, context={"name": PROJECT, "mode": "light", "family": "saas"})
    for key in ("brand_identity", "visual_intent", "palette", "trace"):
        assert key in result, f"Missing key: {key}"


def test_scenario_brand_generate_full_brand_identity_keys():
    sc = _load("design.brand.generate_full")
    result = sc.run(brief=BRIEF, context={"name": PROJECT, "mode": "light"})
    bi = result["brand_identity"]
    for key in ("brand_core", "logo", "icons", "typography", "visual_signature", "_meta"):
        assert key in bi, f"Missing brand_identity key: {key}"


def test_scenario_brand_generate_full_trace():
    sc = _load("design.brand.generate_full")
    result = sc.run(brief=BRIEF, context={"name": PROJECT, "mode": "light"})
    trace = result["trace"]
    assert len(trace) == 3
    endpoints = [s["endpoint"] for s in trace]
    assert "design.visual_intent.generate" in endpoints
    assert "design.palette.generate" in endpoints
    assert "design.brand.generate" in endpoints
    for step in trace:
        assert step["ok"] is True


def test_scenario_brand_generate_full_name_in_logo():
    sc = _load("design.brand.generate_full")
    result = sc.run(brief=BRIEF, context={"name": PROJECT, "mode": "light"})
    assert PROJECT in result["brand_identity"]["logo"]["generation_prompt"]


def test_scenario_brand_generate_full_metadata():
    sc = _load("design.brand.generate_full")
    assert sc.NAME == "design.brand.generate_full"
    assert len(sc.STEPS) == 3
    assert sc.INPUTS["brief"]["required"] is True
    assert sc.INPUTS["context"]["required"] is True


def test_scenario_brand_generate_full_site_family():
    sc = _load("design.brand.generate_full")
    result = sc.run(brief=BRIEF, context={"name": PROJECT, "mode": "light"}, site_family="product_saas")
    assert result["brand_identity"]["_meta"]["context_key"] != ""


# ── design.brand.generate_from_reference ──────────────────────────────────────

def test_scenario_brand_generate_from_reference_structure():
    sc = _load("design.brand.generate_from_reference")
    result = sc.run(brief=BRIEF, context={"name": PROJECT, "mode": "light"},
                    reference_image="/nonexistent.png")
    for key in ("brand_identity", "visual_intent", "palette", "coherence",
                "reference_analysis", "reference_mode", "trace"):
        assert key in result, f"Missing key: {key}"


def test_scenario_brand_generate_from_reference_mode():
    sc = _load("design.brand.generate_from_reference")
    result = sc.run(brief=BRIEF, context={"name": PROJECT, "mode": "light"},
                    reference_image="/nonexistent.png", reference_type="mockup")
    assert result["reference_mode"] == "design_reference_drives_plan"
    assert result["reference_analysis"].get("_source") == "fallback"


def test_scenario_brand_generate_from_reference_trace():
    sc = _load("design.brand.generate_from_reference")
    result = sc.run(brief=BRIEF, context={"name": PROJECT, "mode": "light"},
                    reference_image="/nonexistent.png")
    trace = result["trace"]
    assert len(trace) == 4
    endpoints = [s["endpoint"] for s in trace]
    assert "design.coherence.apply" in endpoints
    assert "design.brand.generate" in endpoints


def test_scenario_brand_generate_from_reference_identity_keys():
    sc = _load("design.brand.generate_from_reference")
    result = sc.run(brief=BRIEF, context={"name": PROJECT, "mode": "light"},
                    reference_image="/nonexistent.png")
    bi = result["brand_identity"]
    for key in ("brand_core", "logo", "icons", "typography", "visual_signature", "_meta"):
        assert key in bi, f"Missing brand_identity key: {key}"


def test_scenario_brand_generate_from_reference_metadata():
    sc = _load("design.brand.generate_from_reference")
    assert sc.NAME == "design.brand.generate_from_reference"
    assert len(sc.STEPS) == 4
    assert sc.INPUTS["reference_image"]["required"] is True
