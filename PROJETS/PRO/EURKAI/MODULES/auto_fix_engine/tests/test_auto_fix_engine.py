"""
Tests unitaires — auto_fix_engine.
Aucun appel réseau ni API. Teste :
- classification des issues
- calcul des patches (compute_fix)
- génération CSS
- application HTML
- boucle de correction complète avec mocks
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vision_audit" / "src"))

from auto_fix_engine import (
    AutoFixEngine, FixType, ZonePatch, FullPatch, CorrectionEntry, LoopResult,
    classify_issue, compute_fix, patch_to_css, full_patch_to_css,
    apply_css_patch, run_correction_loop, _zone_priority, _opacity_to_hex,
    DEFAULT_MAX_ITERATIONS, DEFAULT_TARGET_SCORE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_audit_result(zone, readability_pass, global_score, issues):
    """Construit un AuditResult mock sans importer vision_audit."""
    from types import SimpleNamespace
    iss_objs = [
        SimpleNamespace(
            zone=zone,
            problem=iss["problem"],
            severity=iss["severity"],
            confidence=iss.get("confidence", 0.9),
            suggested_fix=iss.get("suggested_fix", ""),
        )
        for iss in issues
    ]
    return SimpleNamespace(
        readability_pass=readability_pass,
        global_score=global_score,
        zone=zone,
        issues=iss_objs,
        ok=True,
        error=None,
    )


_HERO_AUDIT_FAIL = _make_audit_result("hero", False, 48, [
    {"problem": "text contrast insufficient against background image", "severity": "high"},
    {"problem": "background too detailed and competes with text",      "severity": "medium"},
])

_NAV_AUDIT_FAIL = _make_audit_result("nav", False, 62, [
    {"problem": "CTA button not identifiable from surrounding elements", "severity": "medium"},
])

_HERO_AUDIT_PASS = _make_audit_result("hero", True, 88, [])
_NAV_AUDIT_PASS  = _make_audit_result("nav",  True, 85, [])


# ─────────────────────────────────────────────────────────────────────────────
# Tests — classify_issue
# ─────────────────────────────────────────────────────────────────────────────

def test_classify_text_contrast():
    assert classify_issue("text contrast insufficient against background") == FixType.TEXT_CONTRAST
    assert classify_issue("low contrast text barely readable")             == FixType.TEXT_CONTRAST
    assert classify_issue("insufficient text legibility")                  == FixType.TEXT_CONTRAST
    print("✓ classify text_contrast OK")


def test_classify_overlay():
    assert classify_issue("increase overlay opacity behind text")    == FixType.OVERLAY_INCREASE
    assert classify_issue("add gradient behind text block")          == FixType.OVERLAY_INCREASE
    assert classify_issue("scrim too transparent")                   == FixType.OVERLAY_INCREASE
    print("✓ classify overlay_increase OK")


def test_classify_background():
    assert classify_issue("background too busy reduces readability") == FixType.BACKGROUND_SIMPLIFY
    assert classify_issue("image competes with text legibility")     == FixType.BACKGROUND_SIMPLIFY
    assert classify_issue("background too detailed")                 == FixType.BACKGROUND_SIMPLIFY
    print("✓ classify background_simplify OK")


def test_classify_cta():
    assert classify_issue("CTA not visible on this background")          == FixType.CTA_EMPHASIS
    assert classify_issue("button not identifiable from background")     == FixType.CTA_EMPHASIS
    print("✓ classify cta_emphasis OK")


def test_classify_typography():
    assert classify_issue("font weight too thin at this size")  == FixType.TYPOGRAPHY_SAFETY
    assert classify_issue("font size too small for legibility") == FixType.TYPOGRAPHY_SAFETY
    print("✓ classify typography_safety OK")


def test_classify_text_plate():
    assert classify_issue("add text background plate behind heading") == FixType.TEXT_PLATE
    print("✓ classify text_plate OK")


def test_classify_unknown():
    assert classify_issue("the colors look a bit off")  == FixType.UNKNOWN
    assert classify_issue("general visual imbalance")   == FixType.UNKNOWN
    print("✓ classify unknown OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — compute_fix
# ─────────────────────────────────────────────────────────────────────────────

def test_compute_text_contrast_high():
    patch = compute_fix(FixType.TEXT_CONTRAST, "high", "hero")
    assert patch.text_color  == "#ffffff"
    assert patch.text_shadow is not None
    print("✓ compute_fix text_contrast high OK")


def test_compute_text_contrast_medium():
    patch = compute_fix(FixType.TEXT_CONTRAST, "medium", "hero")
    assert patch.text_color  is None      # medium ne force pas la couleur
    assert patch.text_shadow is not None
    print("✓ compute_fix text_contrast medium OK")


def test_compute_overlay_incremental():
    # Première passe : overlay 0 → +0.35 (high)
    cur   = ZonePatch(zone="hero")
    patch = compute_fix(FixType.OVERLAY_INCREASE, "high", "hero", current=cur)
    assert patch.overlay_opacity == pytest_approx(0.35, abs=0.01)

    # Deuxième passe (overlay existant 0.35 → +0.35 = 0.70 → capped 0.75)
    cur2  = ZonePatch(zone="hero", overlay_opacity=0.35)
    patch2 = compute_fix(FixType.OVERLAY_INCREASE, "high", "hero", current=cur2)
    assert patch2.overlay_opacity <= 0.75
    print("✓ compute_fix overlay_increase incremental OK")


def test_compute_background_simplify():
    patch = compute_fix(FixType.BACKGROUND_SIMPLIFY, "high", "hero")
    assert patch.blur_px         >= 4
    assert patch.overlay_opacity is not None
    print("✓ compute_fix background_simplify OK")


def test_compute_cta_emphasis():
    patch = compute_fix(FixType.CTA_EMPHASIS, "high", "hero")
    assert patch.cta_font_weight == 800
    print("✓ compute_fix cta_emphasis OK")


def test_compute_typography_safety():
    cur   = ZonePatch(zone="nav", font_weight=400)
    patch = compute_fix(FixType.TYPOGRAPHY_SAFETY, "high", "nav", current=cur)
    assert patch.font_weight is not None
    assert patch.font_weight > 400
    assert patch.font_size_scale is not None
    print("✓ compute_fix typography_safety OK")


def test_compute_text_plate():
    patch = compute_fix(FixType.TEXT_PLATE, "high", "hero")
    assert patch.text_plate_bg     is not None
    assert patch.text_plate_radius is not None
    print("✓ compute_fix text_plate OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — ZonePatch / FullPatch
# ─────────────────────────────────────────────────────────────────────────────

def test_zone_patch_empty():
    p = ZonePatch(zone="hero")
    assert p.is_empty()
    p.text_color = "#fff"
    assert not p.is_empty()
    print("✓ ZonePatch.is_empty OK")


def test_zone_patch_merge():
    a = ZonePatch(zone="hero", text_color="#fff", overlay_opacity=0.3)
    b = ZonePatch(zone="hero", overlay_opacity=0.5, text_shadow="0 1px 4px rgba(0,0,0,0.5)")
    merged = a.merge(b)
    assert merged.text_color      == "#fff"       # from a (b has None)
    assert merged.overlay_opacity == 0.5          # b wins
    assert merged.text_shadow     is not None
    print("✓ ZonePatch.merge OK")


def test_full_patch_set_merge():
    fp = FullPatch()
    p1 = ZonePatch(zone="hero", text_color="#fff")
    p2 = ZonePatch(zone="hero", overlay_opacity=0.4)
    fp.set("hero", p1)
    fp.set("hero", p2)
    # Les deux doivent être mergés
    assert fp.zones["hero"].text_color      == "#fff"
    assert fp.zones["hero"].overlay_opacity == 0.4
    print("✓ FullPatch.set merge OK")


def test_full_patch_is_empty():
    fp = FullPatch()
    assert fp.is_empty()
    fp.set("hero", ZonePatch(zone="hero", text_color="#fff"))
    assert not fp.is_empty()
    print("✓ FullPatch.is_empty OK")


def test_full_patch_to_dict():
    fp = FullPatch()
    fp.set("hero", ZonePatch(zone="hero", text_color="#fff", overlay_opacity=0.4))
    d = fp.to_dict()
    assert "hero" in d
    assert d["hero"]["text_color"]      == "#fff"
    assert d["hero"]["overlay_opacity"] == 0.4
    print("✓ FullPatch.to_dict OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — CSS generation
# ─────────────────────────────────────────────────────────────────────────────

def test_patch_to_css_text_color():
    patch = ZonePatch(zone="hero", text_color="#ffffff", text_shadow="0 2px 8px rgba(0,0,0,0.8)")
    css = patch_to_css(patch)
    assert '[data-audit="hero"]' in css
    assert "#ffffff"             in css
    assert "text-shadow"         in css
    assert "!important"          in css
    print("✓ patch_to_css text_color OK")


def test_patch_to_css_overlay():
    patch = ZonePatch(zone="hero", overlay_opacity=0.5, overlay_color="#000000")
    css = patch_to_css(patch)
    assert "::before"       in css
    assert "position:absolute" in css
    assert "z-index:0"      in css
    print("✓ patch_to_css overlay OK")


def test_patch_to_css_blur():
    patch = ZonePatch(zone="hero", blur_px=8)
    css = patch_to_css(patch)
    assert "blur(8px)"  in css
    assert "filter"     in css
    print("✓ patch_to_css blur OK")


def test_patch_to_css_cta():
    patch = ZonePatch(zone="hero", cta_bg="#ff5500", cta_color="#ffffff", cta_font_weight=800)
    css = patch_to_css(patch)
    assert "button"     in css
    assert "#ff5500"    in css
    assert "800"        in css
    print("✓ patch_to_css cta OK")


def test_patch_to_css_text_plate():
    patch = ZonePatch(zone="hero", text_plate_bg="rgba(0,0,0,0.6)", text_plate_radius="6px")
    css = patch_to_css(patch)
    assert "rgba(0,0,0,0.6)" in css
    assert "6px"              in css
    print("✓ patch_to_css text_plate OK")


def test_full_patch_to_css_empty():
    fp  = FullPatch()
    css = full_patch_to_css(fp)
    assert css == ""
    print("✓ full_patch_to_css empty OK")


def test_full_patch_to_css_multi_zone():
    fp = FullPatch()
    fp.set("hero", ZonePatch(zone="hero", text_color="#fff"))
    fp.set("nav",  ZonePatch(zone="nav",  cta_font_weight=700))
    css = full_patch_to_css(fp)
    assert 'data-audit="hero"' in css
    assert 'data-audit="nav"'  in css
    print("✓ full_patch_to_css multi_zone OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — apply_css_patch (HTML injection)
# ─────────────────────────────────────────────────────────────────────────────

_BASE_HTML = """<!doctype html><html><head><title>Test</title></head>
<body><nav data-audit="nav">Nav</nav>
<section data-audit="hero"><h1>Hello</h1></section>
</body></html>"""


def test_apply_css_patch_injects_style():
    fp = FullPatch()
    fp.set("hero", ZonePatch(zone="hero", text_color="#ffffff"))
    result = apply_css_patch(_BASE_HTML, fp)
    assert '<style id="auto-fix-engine">' in result
    assert '#ffffff'                      in result
    assert '</head>'                      in result
    print("✓ apply_css_patch injects style OK")


def test_apply_css_patch_idempotent():
    """Appliquer deux fois ne duplique pas le bloc style."""
    fp = FullPatch()
    fp.set("hero", ZonePatch(zone="hero", text_color="#ffffff"))
    html1 = apply_css_patch(_BASE_HTML, fp)
    html2 = apply_css_patch(html1, fp)
    assert html2.count('<style id="auto-fix-engine">') == 1
    print("✓ apply_css_patch idempotent OK")


def test_apply_css_patch_empty_no_change():
    fp     = FullPatch()
    result = apply_css_patch(_BASE_HTML, fp)
    assert result == _BASE_HTML
    print("✓ apply_css_patch empty no_change OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — AutoFixEngine.compute_patch
# ─────────────────────────────────────────────────────────────────────────────

def test_compute_patch_basic():
    engine = AutoFixEngine()
    patch, log = engine.compute_patch([_HERO_AUDIT_FAIL], iteration=1)
    assert not patch.is_empty()
    assert "hero" in patch.zones
    assert len(log) >= 1
    assert log[0].zone      == "hero"
    assert log[0].iteration == 1
    print("✓ compute_patch basic OK")


def test_compute_patch_skip_passing():
    engine = AutoFixEngine()
    patch, log = engine.compute_patch([_HERO_AUDIT_PASS], iteration=1)
    assert patch.is_empty()
    assert len(log) == 0
    print("✓ compute_patch skip_passing OK")


def test_compute_patch_zone_priority():
    """hero doit être patchée avant nav."""
    engine = AutoFixEngine()
    patch, log = engine.compute_patch([_NAV_AUDIT_FAIL, _HERO_AUDIT_FAIL], iteration=1)
    zones_in_log = [e.zone for e in log]
    if "hero" in zones_in_log and "nav" in zones_in_log:
        assert zones_in_log.index("hero") < zones_in_log.index("nav")
    print("✓ compute_patch zone_priority OK")


def test_compute_patch_incremental():
    """Deux passes : le patch s'accumule sans réinitialiser."""
    engine = AutoFixEngine()
    patch1, _ = engine.compute_patch([_HERO_AUDIT_FAIL], current_patch=None, iteration=1)
    # Simuler que le hero est toujours KO (pas amélioré)
    patch2, _ = engine.compute_patch([_HERO_AUDIT_FAIL], current_patch=patch1, iteration=2)
    # L'overlay doit être plus élevé qu'à l'itération 1
    op1 = patch1.zones.get("hero", ZonePatch("hero")).overlay_opacity or 0
    op2 = patch2.zones.get("hero", ZonePatch("hero")).overlay_opacity or 0
    # op2 >= op1 (on n'a pas reculé)
    assert op2 >= op1
    print(f"✓ compute_patch incremental OK (overlay {op1:.2f} → {op2:.2f})")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — run_correction_loop (mock capture/audit)
# ─────────────────────────────────────────────────────────────────────────────

def _make_mock_capture_fn(html_store: list):
    """capture_fn qui stocke le HTML passé et retourne une capture mock."""
    from types import SimpleNamespace

    def capture_fn(html: str):
        html_store.append(html)
        return [SimpleNamespace(ok=True, path="/tmp/hero.png", zone="hero",
                                viewport="desktop", page="landing")]
    return capture_fn


def _make_mock_audit_fn(results_per_call: list[list]):
    """audit_fn qui retourne des résultats différents à chaque appel."""
    call_count = [0]

    def audit_fn(captures):
        idx = min(call_count[0], len(results_per_call) - 1)
        call_count[0] += 1
        return results_per_call[idx]

    return audit_fn


def test_loop_converges():
    """La boucle converge si audit passe à l'itération 2."""
    html_store = []
    # Itération 1 : fail. Itération 2 : pass.
    audit_fn = _make_mock_audit_fn([
        [_HERO_AUDIT_FAIL],
        [_HERO_AUDIT_PASS],
    ])
    capture_fn = _make_mock_capture_fn(html_store)
    engine = AutoFixEngine(max_iterations=3, target_score=70)
    result = engine.run_correction_loop(
        initial_html=_BASE_HTML,
        capture_fn=capture_fn,
        audit_fn=audit_fn,
    )
    assert result.converged      is True
    assert result.iterations_run == 2
    assert len(result.log)       >= 1
    assert not result.final_patch.is_empty()
    print(f"✓ loop converges OK (iter={result.iterations_run})")


def test_loop_max_iterations():
    """La boucle s'arrête à max_iterations si jamais convergée."""
    html_store = []
    # Toujours fail
    audit_fn   = _make_mock_audit_fn([[_HERO_AUDIT_FAIL]] * 10)
    capture_fn = _make_mock_capture_fn(html_store)
    engine = AutoFixEngine(max_iterations=3, target_score=90)
    result = engine.run_correction_loop(
        initial_html=_BASE_HTML,
        capture_fn=capture_fn,
        audit_fn=audit_fn,
    )
    assert result.converged      is False
    assert result.iterations_run <= 3
    print(f"✓ loop max_iterations OK (ran {result.iterations_run} iterations)")


def test_loop_html_patched():
    """Le HTML final doit contenir le style injecté."""
    html_store = []
    audit_fn   = _make_mock_audit_fn([[_HERO_AUDIT_FAIL], [_HERO_AUDIT_PASS]])
    capture_fn = _make_mock_capture_fn(html_store)
    engine     = AutoFixEngine(max_iterations=3)
    result     = engine.run_correction_loop(
        initial_html=_BASE_HTML,
        capture_fn=capture_fn,
        audit_fn=audit_fn,
    )
    assert '<style id="auto-fix-engine">' in result.final_html
    print("✓ loop html_patched OK")


def test_loop_to_dict():
    html_store = []
    audit_fn   = _make_mock_audit_fn([[_HERO_AUDIT_FAIL], [_HERO_AUDIT_PASS]])
    capture_fn = _make_mock_capture_fn(html_store)
    engine     = AutoFixEngine(max_iterations=3)
    result     = engine.run_correction_loop(
        initial_html=_BASE_HTML,
        capture_fn=capture_fn,
        audit_fn=audit_fn,
    )
    d = result.to_dict()
    assert "converged"      in d
    assert "iterations_run" in d
    assert "log"            in d
    assert "final_scores"   in d
    assert "final_patch"    in d
    print("✓ loop to_dict OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — helpers
# ─────────────────────────────────────────────────────────────────────────────

def test_zone_priority():
    assert _zone_priority("hero") < _zone_priority("nav")
    assert _zone_priority("nav")  < _zone_priority("primary_cta")
    assert _zone_priority("unknown_zone") > _zone_priority("section-3")
    print("✓ zone_priority OK")


def test_opacity_to_hex():
    assert _opacity_to_hex(0.0)  == "00"
    assert _opacity_to_hex(1.0)  == "FF"
    assert _opacity_to_hex(0.5)  in ("80", "7F")  # ~127-128
    print("✓ opacity_to_hex OK")


def test_correction_entry_to_dict():
    entry = CorrectionEntry(
        iteration=1, zone="hero",
        issue="low contrast", severity="high",
        fix_type="text_contrast",
        description="forced text color to #ffffff",
        before={}, after={"text_color": "#ffffff"},
    )
    d = entry.to_dict()
    assert d["iteration"] == 1
    assert d["zone"]      == "hero"
    assert d["fix_type"]  == "text_contrast"
    print("✓ CorrectionEntry.to_dict OK")


# ─────────────────────────────────────────────────────────────────────────────
# pytest_approx compat (sans pytest)
# ─────────────────────────────────────────────────────────────────────────────

class pytest_approx:
    def __init__(self, val, abs=0.01):
        self.val = val
        self.abs = abs
    def __eq__(self, other):
        return abs(other - self.val) <= self.abs


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_classify_text_contrast,
        test_classify_overlay,
        test_classify_background,
        test_classify_cta,
        test_classify_typography,
        test_classify_text_plate,
        test_classify_unknown,
        test_compute_text_contrast_high,
        test_compute_text_contrast_medium,
        test_compute_overlay_incremental,
        test_compute_background_simplify,
        test_compute_cta_emphasis,
        test_compute_typography_safety,
        test_compute_text_plate,
        test_zone_patch_empty,
        test_zone_patch_merge,
        test_full_patch_set_merge,
        test_full_patch_is_empty,
        test_full_patch_to_dict,
        test_patch_to_css_text_color,
        test_patch_to_css_overlay,
        test_patch_to_css_blur,
        test_patch_to_css_cta,
        test_patch_to_css_text_plate,
        test_full_patch_to_css_empty,
        test_full_patch_to_css_multi_zone,
        test_apply_css_patch_injects_style,
        test_apply_css_patch_idempotent,
        test_apply_css_patch_empty_no_change,
        test_compute_patch_basic,
        test_compute_patch_skip_passing,
        test_compute_patch_zone_priority,
        test_compute_patch_incremental,
        test_loop_converges,
        test_loop_max_iterations,
        test_loop_html_patched,
        test_loop_to_dict,
        test_zone_priority,
        test_opacity_to_hex,
        test_correction_entry_to_dict,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"✗ {t.__name__} : {e}")
            import traceback; traceback.print_exc()
            failed += 1
    print(f"\n{'✅' if failed == 0 else '❌'} {len(tests) - failed}/{len(tests)} tests passent.")
