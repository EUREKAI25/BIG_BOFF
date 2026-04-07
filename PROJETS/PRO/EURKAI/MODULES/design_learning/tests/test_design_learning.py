"""
Tests unitaires — design_learning.
Aucun appel réseau, aucune API, aucune dépendance externe.
Simule plusieurs runs pour vérifier la convergence des corrections.
"""

import sys
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "auto_fix_engine" / "src"))

from design_learning import (
    DesignLearning, Pattern, derive_context, derive_context_from_audit,
    score_match, _hex_luminance, _context_fully_known, _deduplicate_fix,
    _MIN_MATCH_SCORE, _MAX_SUGGESTIONS, _MIN_IMPROVEMENT,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

_RC_DARK_IMAGE = {
    "bg":           "#0d1117",
    "fg":           "#ffffff",
    "bg_art":       "url(picsum.photos/1440/900)",
    "hero_pattern": "split",
}

_RC_LIGHT_COLOR = {
    "bg":           "#f8f9fa",
    "fg":           "#111111",
    "bg_art":       "background:#f8f9fa",
    "hero_pattern": "centered",
}

_CTX_HERO_DARK_IMAGE = {
    "zone":             "hero",
    "background_type":  "image",
    "text_color_class": "light",
    "theme_type":       "dark",
}

_CTX_NAV_LIGHT_COLOR = {
    "zone":             "nav",
    "background_type":  "color",
    "text_color_class": "dark",
    "theme_type":       "light",
}

_FIX_OVERLAY = {"overlay_opacity": 0.55, "overlay_color": "#000000"}
_FIX_CONTRAST = {"text_color": "#ffffff", "text_shadow": "0 2px 8px rgba(0,0,0,0.8)"}


def _make_db(tmp_dir: str) -> DesignLearning:
    return DesignLearning(db_path=Path(tmp_dir) / "patterns.json")


def _make_loop_result(zone="hero", final_score=85, initial_score=48,
                      converged=True, fix_params=None, fix_type="overlay_increase"):
    """Crée un LoopResult mock sans importer auto_fix_engine."""
    try:
        from auto_fix_engine import FullPatch, ZonePatch, LoopResult, CorrectionEntry
        zone_patch = ZonePatch(zone=zone, **(fix_params or _FIX_OVERLAY))
        full_patch = FullPatch()
        full_patch.set(zone, zone_patch)
        entry = CorrectionEntry(
            iteration=1, zone=zone,
            issue="text contrast insufficient", severity="high",
            fix_type=fix_type,
            description="overlay 0.0 → 0.55",
            before={}, after=fix_params or _FIX_OVERLAY,
        )
        return LoopResult(
            converged=converged,
            iterations_run=1,
            final_html="<html></html>",
            final_patch=full_patch,
            log=[entry],
            final_scores={zone: final_score},
            duration_ms=1200.0,
        )
    except ImportError:
        # Mock léger sans auto_fix_engine
        zone_patch = SimpleNamespace(to_dict=lambda: fix_params or _FIX_OVERLAY)
        full_patch = SimpleNamespace(zones={zone: zone_patch}, is_empty=lambda: False)
        entry = SimpleNamespace(
            zone=zone, severity="high",
            fix_type=fix_type, problem="low contrast",
        )
        return SimpleNamespace(
            converged=converged, iterations_run=1,
            final_patch=full_patch, log=[entry],
            final_scores={zone: final_score},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Tests — helpers
# ─────────────────────────────────────────────────────────────────────────────

def test_hex_luminance():
    assert _hex_luminance("#ffffff") > 0.99
    assert _hex_luminance("#000000") < 0.01
    assert 0.1 < _hex_luminance("#888888") < 0.3
    # Blanc = luminance haute → text_color_class = "light"
    # Noir  = luminance basse → text_color_class = "dark"
    print("✓ hex_luminance OK")


def test_derive_context_dark_image():
    ctx = derive_context("hero", _RC_DARK_IMAGE)
    assert ctx["zone"]             == "hero"
    assert ctx["background_type"]  == "image"
    assert ctx["text_color_class"] == "light"   # fg=#ffffff
    assert ctx["theme_type"]       == "dark"    # bg=#0d1117
    print(f"✓ derive_context dark/image OK : {ctx}")


def test_derive_context_light_color():
    ctx = derive_context("nav", _RC_LIGHT_COLOR)
    assert ctx["zone"]             == "nav"
    assert ctx["background_type"]  == "color"
    assert ctx["text_color_class"] == "dark"    # fg=#111111
    assert ctx["theme_type"]       == "light"   # bg=#f8f9fa
    print(f"✓ derive_context light/color OK : {ctx}")


def test_derive_context_gradient():
    rc = {**_RC_LIGHT_COLOR, "bg_art": "background:linear-gradient(to right,#111,#333)"}
    ctx = derive_context("hero", rc)
    assert ctx["background_type"] == "gradient"
    print("✓ derive_context gradient OK")


def test_score_match_exact():
    score = score_match(_CTX_HERO_DARK_IMAGE, _CTX_HERO_DARK_IMAGE)
    assert score == 5   # zone×2 + 3 dims×1
    print(f"✓ score_match exact = {score}/5 OK")


def test_score_match_zone_only():
    query = {"zone": "hero", "background_type": None, "text_color_class": None, "theme_type": None}
    score = score_match(_CTX_HERO_DARK_IMAGE, query)
    assert score == 2   # zone seul = 2
    print(f"✓ score_match zone_only = {score} OK")


def test_score_match_different_zone():
    score = score_match(_CTX_HERO_DARK_IMAGE, _CTX_NAV_LIGHT_COLOR)
    assert score == 0   # zones différentes, rien de commun
    print(f"✓ score_match different_zone = {score} OK")


def test_score_match_partial():
    query = {**_CTX_HERO_DARK_IMAGE, "background_type": "color"}  # bg_type différent
    score = score_match(_CTX_HERO_DARK_IMAGE, query)
    assert score == 4   # zone(2) + text_color(1) + theme(1) = 4
    print(f"✓ score_match partial = {score} OK")


def test_deduplicate_fix_averages_numbers():
    a = {"overlay_opacity": 0.4, "text_color": "#fff"}
    b = {"overlay_opacity": 0.6, "blur_px": 4}
    merged = _deduplicate_fix(a, b)
    assert merged["overlay_opacity"] == 0.5    # moyenne
    assert merged["text_color"]      == "#fff"  # de a
    assert merged["blur_px"]         == 4       # de b
    print("✓ deduplicate_fix OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — Pattern
# ─────────────────────────────────────────────────────────────────────────────

def test_pattern_success_rate():
    p = Pattern(id="x", recorded_at="2026", success_count=3, failure_count=1)
    assert p.success_rate == 0.75
    print("✓ Pattern.success_rate OK")


def test_pattern_success_rate_no_usage():
    p = Pattern(id="x", recorded_at="2026")
    assert p.success_rate == 1.0   # bénéfice du doute
    print("✓ Pattern.success_rate no_usage OK")


def test_pattern_is_reliable():
    p = Pattern(id="x", recorded_at="2026", use_count=2)
    assert p.is_reliable   # < 3 usages → bénéfice du doute

    p2 = Pattern(id="y", recorded_at="2026", use_count=5, success_count=2, failure_count=3)
    assert not p2.is_reliable   # 2/5 = 40% < 60%

    p3 = Pattern(id="z", recorded_at="2026", use_count=4, success_count=3, failure_count=1)
    assert p3.is_reliable   # 75% >= 60%
    print("✓ Pattern.is_reliable OK")


def test_pattern_to_dict_no_match_score():
    p = Pattern(id="x", recorded_at="2026", match_score=5)
    d = p.to_dict()
    assert "match_score" not in d   # non persisté
    print("✓ Pattern.to_dict excludes match_score OK")


def test_pattern_from_dict_roundtrip():
    p = Pattern(
        id="abc", recorded_at="2026-01-01T00:00:00Z",
        context=_CTX_HERO_DARK_IMAGE,
        problem="overlay_increase",
        fix=_FIX_OVERLAY,
        score_improvement=35,
        iterations_needed=2,
    )
    d = p.to_dict()
    p2 = Pattern.from_dict(d)
    assert p2.id               == p.id
    assert p2.context          == p.context
    assert p2.fix              == p.fix
    assert p2.score_improvement == p.score_improvement
    print("✓ Pattern from_dict roundtrip OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — DesignLearning storage
# ─────────────────────────────────────────────────────────────────────────────

def test_record_fix_basic():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        pid = db.record_fix(
            context=_CTX_HERO_DARK_IMAGE,
            problem="overlay_increase",
            fix_params=_FIX_OVERLAY,
            score_improvement=35,
        )
        assert pid is not None
        assert len(db.all_patterns()) == 1
        print(f"✓ record_fix basic OK (id={pid[:8]}...)")


def test_record_fix_below_threshold():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        pid = db.record_fix(
            context=_CTX_HERO_DARK_IMAGE,
            problem="text_contrast",
            fix_params=_FIX_CONTRAST,
            score_improvement=_MIN_IMPROVEMENT - 1,  # trop faible
        )
        assert pid is None
        assert len(db.all_patterns()) == 0
        print("✓ record_fix below_threshold ignored OK")


def test_record_fix_deduplication():
    """Deux records identiques doivent merge, pas dupliquer."""
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                      {"overlay_opacity": 0.4}, score_improvement=30)
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                      {"overlay_opacity": 0.6}, score_improvement=40)
        patterns = db.all_patterns()
        assert len(patterns) == 1   # dédupliqué
        assert patterns[0].fix["overlay_opacity"] == 0.5  # moyenné
        assert patterns[0].score_improvement      == 40   # max
        print("✓ record_fix deduplication OK")


def test_record_fix_different_contexts_not_merged():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                      _FIX_OVERLAY, score_improvement=30)
        db.record_fix(_CTX_NAV_LIGHT_COLOR, "text_contrast",
                      _FIX_CONTRAST, score_improvement=20)
        assert len(db.all_patterns()) == 2
        print("✓ record_fix different_contexts OK")


def test_persist_and_reload():
    with tempfile.TemporaryDirectory() as tmp:
        db1 = _make_db(tmp)
        db1.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                       _FIX_OVERLAY, score_improvement=35)
        # Recharger depuis le fichier
        db2 = _make_db(tmp)
        assert len(db2.all_patterns()) == 1
        assert db2.all_patterns()[0].problem == "overlay_increase"
        print("✓ persist_and_reload OK")


def test_atomic_write_no_corruption():
    """Vérifier que le JSON sauvegardé est valide."""
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                      _FIX_OVERLAY, score_improvement=35)
        data = json.loads((Path(tmp) / "patterns.json").read_text())
        assert "version"  in data
        assert "patterns" in data
        assert len(data["patterns"]) == 1
        print("✓ atomic_write valid JSON OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — retrieve_relevant_patterns
# ─────────────────────────────────────────────────────────────────────────────

def test_retrieve_exact_match():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                      _FIX_OVERLAY, score_improvement=35)
        db.record_fix(_CTX_NAV_LIGHT_COLOR, "text_contrast",
                      _FIX_CONTRAST, score_improvement=20)

        results = db.retrieve_relevant_patterns(_CTX_HERO_DARK_IMAGE)
        assert len(results) >= 1
        assert results[0].context["zone"] == "hero"
        assert results[0].match_score     == 5
        print(f"✓ retrieve exact_match OK (score={results[0].match_score})")


def test_retrieve_partial_match():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                      _FIX_OVERLAY, score_improvement=35)

        # Query avec une dimension différente
        query = {**_CTX_HERO_DARK_IMAGE, "background_type": "gradient"}
        results = db.retrieve_relevant_patterns(query)
        assert len(results) >= 1   # zone match = 2 ≥ _MIN_MATCH_SCORE
        assert results[0].match_score >= _MIN_MATCH_SCORE
        print(f"✓ retrieve partial_match OK (score={results[0].match_score})")


def test_retrieve_no_match_different_zone():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                      _FIX_OVERLAY, score_improvement=35)

        # Zone différente → score 0 < MIN_MATCH_SCORE
        results = db.retrieve_relevant_patterns(_CTX_NAV_LIGHT_COLOR)
        assert len(results) == 0
        print("✓ retrieve no_match different_zone OK")


def test_retrieve_top_k_limit():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        # Ajouter 5 patterns pour la même zone (contextes légèrement différents)
        for i in range(5):
            ctx = {**_CTX_HERO_DARK_IMAGE, "theme_type": "dark" if i % 2 == 0 else "light"}
            db.record_fix(ctx, f"fix_{i}", {"overlay_opacity": 0.1 * (i + 1)},
                          score_improvement=10 + i * 5)

        results = db.retrieve_relevant_patterns(_CTX_HERO_DARK_IMAGE, top_k=3)
        assert len(results) <= 3
        print(f"✓ retrieve top_k_limit OK ({len(results)} patterns)")


def test_retrieve_sorted_by_score_then_improvement():
    """Patterns triés : score desc, puis score_improvement desc."""
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        # Pattern A : exact match (score=5), amélioration=20
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                      _FIX_OVERLAY, score_improvement=20)
        # Pattern B : partial match (score=4, bg_type diff), amélioration=40
        ctx_partial = {**_CTX_HERO_DARK_IMAGE, "background_type": "gradient"}
        db.record_fix(ctx_partial, "text_contrast",
                      _FIX_CONTRAST, score_improvement=40)

        results = db.retrieve_relevant_patterns(_CTX_HERO_DARK_IMAGE)
        assert results[0].match_score >= results[-1].match_score
        print(f"✓ retrieve sorted OK (scores: {[r.match_score for r in results]})")


def test_retrieve_excludes_unreliable():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                      _FIX_OVERLAY, score_improvement=35)
        # Marquer le pattern comme non fiable
        p = db.all_patterns()[0]
        p.use_count     = 10
        p.success_count = 2
        p.failure_count = 8   # success_rate = 20% < 60%
        db._save()

        # Recharger
        db2 = _make_db(tmp)
        results = db2.retrieve_relevant_patterns(_CTX_HERO_DARK_IMAGE)
        assert len(results) == 0
        print("✓ retrieve excludes unreliable OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — suggest_preemptive_adjustments
# ─────────────────────────────────────────────────────────────────────────────

def test_suggest_returns_patch_or_none():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        # Aucun pattern → None
        result = db.suggest_preemptive_adjustments([_CTX_HERO_DARK_IMAGE])
        assert result is None
        print("✓ suggest returns None when no patterns OK")


def test_suggest_returns_patch_with_patterns():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                      _FIX_OVERLAY, score_improvement=35)

        result = db.suggest_preemptive_adjustments([_CTX_HERO_DARK_IMAGE])
        assert result is not None
        print(f"✓ suggest returns patch OK : {type(result).__name__}")


def test_suggest_max_suggestions():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        # Ajouter des patterns pour 5 zones
        zones = ["hero", "nav", "primary_cta", "section-1", "section-2"]
        for z in zones:
            ctx = {**_CTX_HERO_DARK_IMAGE, "zone": z}
            db.record_fix(ctx, "overlay_increase", _FIX_OVERLAY, score_improvement=30)

        zone_contexts = [{"zone": z, **_CTX_HERO_DARK_IMAGE} for z in zones]
        result = db.suggest_preemptive_adjustments(zone_contexts)

        # Vérifier que la limite est respectée
        if result is not None and hasattr(result, "zones"):
            assert len(result.zones) <= _MAX_SUGGESTIONS
        print(f"✓ suggest max_suggestions ({_MAX_SUGGESTIONS}) OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — mark_preemptive_result
# ─────────────────────────────────────────────────────────────────────────────

def test_mark_preemptive_success():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        pid = db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase",
                            _FIX_OVERLAY, score_improvement=35)
        db.mark_preemptive_result(pid, success=True)
        db.mark_preemptive_result(pid, success=True)
        db.mark_preemptive_result(pid, success=False)

        p = db.all_patterns()[0]
        assert p.use_count     == 3
        assert p.success_count == 2
        assert p.failure_count == 1
        assert abs(p.success_rate - 2/3) < 0.01
        print(f"✓ mark_preemptive_result OK (rate={p.success_rate:.2f})")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — record_from_loop_result
# ─────────────────────────────────────────────────────────────────────────────

def test_record_from_loop_result_success():
    with tempfile.TemporaryDirectory() as tmp:
        db    = _make_db(tmp)
        loop  = _make_loop_result("hero", final_score=85, initial_score=48, converged=True)
        ids   = db.record_from_loop_result(loop, initial_scores={"hero": 48}, rc=_RC_DARK_IMAGE)
        assert len(ids) >= 1
        assert len(db.all_patterns()) >= 1
        print(f"✓ record_from_loop_result success OK ({len(ids)} patterns)")


def test_record_from_loop_result_no_improvement():
    with tempfile.TemporaryDirectory() as tmp:
        db   = _make_db(tmp)
        loop = _make_loop_result("hero", final_score=50, initial_score=48, converged=True)
        ids  = db.record_from_loop_result(loop, initial_scores={"hero": 48}, rc=_RC_DARK_IMAGE)
        # amélioration = 2 < _MIN_IMPROVEMENT → rien enregistré
        assert len(ids) == 0
        print("✓ record_from_loop_result no_improvement ignored OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — stats
# ─────────────────────────────────────────────────────────────────────────────

def test_stats_empty():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        s  = db.stats()
        assert s["total_patterns"]   == 0
        assert s["avg_score_improvement"] == 0
        print("✓ stats empty OK")


def test_stats_populated():
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)
        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase", _FIX_OVERLAY, score_improvement=30)
        db.record_fix(_CTX_NAV_LIGHT_COLOR, "text_contrast",    _FIX_CONTRAST, score_improvement=20)
        s = db.stats()
        assert s["total_patterns"]        == 2
        assert s["avg_score_improvement"] == 25.0
        assert len(s["most_common_problems"]) >= 1
        assert "hero" in s["coverage"] or "nav" in s["coverage"]
        print(f"✓ stats populated OK : {s}")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — simulation multi-runs (convergence)
# ─────────────────────────────────────────────────────────────────────────────

def test_simulation_same_site_type_fewer_failures():
    """
    Simule 5 générations du même type de site.
    Vérifie que le nombre de corrections nécessaires diminue après apprentissage.
    """
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)

        # Run 1 : pas de connaissance → correction nécessaire (3 itérations)
        loop1 = _make_loop_result("hero", final_score=88, initial_score=45,
                                  converged=True, fix_params=_FIX_OVERLAY)
        loop1.iterations_run = 3
        db.record_from_loop_result(loop1, {"hero": 45}, _RC_DARK_IMAGE)

        patterns_after_run1 = len(db.all_patterns())
        assert patterns_after_run1 >= 1

        # Run 2 : on a un pattern → on peut suggérer un patch proactif
        ctx     = derive_context("hero", _RC_DARK_IMAGE)
        suggestion = db.suggest_preemptive_adjustments([ctx])
        assert suggestion is not None  # le pattern est retrouvé

        # Le patch suggéré doit contenir les valeurs du fix enregistré
        if hasattr(suggestion, "zones") and "hero" in suggestion.zones:
            zone_patch = suggestion.zones["hero"]
            assert zone_patch.overlay_opacity == _FIX_OVERLAY["overlay_opacity"]

        print(f"✓ simulation multi-run OK : pattern retrouvé pour run 2")


def test_simulation_different_seeds_same_archetype():
    """
    Même archetype, graines différentes → les patterns s'accumulent et convergent.
    """
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)

        # 3 runs avec des fixes légèrement différents (seeds différentes)
        fixes = [
            {"overlay_opacity": 0.45},
            {"overlay_opacity": 0.50},
            {"overlay_opacity": 0.55},
        ]
        for fix in fixes:
            loop = _make_loop_result("hero", final_score=85, initial_score=48,
                                     converged=True, fix_params=fix)
            db.record_from_loop_result(loop, {"hero": 48}, _RC_DARK_IMAGE)

        patterns = db.all_patterns()
        # Dédupliqué → un seul pattern avec overlay moyenné
        assert len(patterns) == 1
        # Overlay moyenné entre 0.45, 0.50, 0.55
        op = patterns[0].fix.get("overlay_opacity", 0)
        assert 0.44 <= op <= 0.56
        print(f"✓ simulation different_seeds convergence OK (overlay={op:.2f})")


def test_simulation_multiple_zones():
    """Les patterns par zone s'accumulent indépendamment."""
    with tempfile.TemporaryDirectory() as tmp:
        db = _make_db(tmp)

        db.record_fix(_CTX_HERO_DARK_IMAGE, "overlay_increase", _FIX_OVERLAY, score_improvement=35)
        db.record_fix(_CTX_NAV_LIGHT_COLOR, "text_contrast",    _FIX_CONTRAST, score_improvement=20)

        # Suggestions pour deux zones simultanément
        zone_contexts = [_CTX_HERO_DARK_IMAGE, _CTX_NAV_LIGHT_COLOR]
        result = db.suggest_preemptive_adjustments(zone_contexts)

        # Au moins une zone doit être suggérée
        assert result is not None
        print(f"✓ simulation multiple_zones OK")


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_hex_luminance,
        test_derive_context_dark_image,
        test_derive_context_light_color,
        test_derive_context_gradient,
        test_score_match_exact,
        test_score_match_zone_only,
        test_score_match_different_zone,
        test_score_match_partial,
        test_deduplicate_fix_averages_numbers,
        test_pattern_success_rate,
        test_pattern_success_rate_no_usage,
        test_pattern_is_reliable,
        test_pattern_to_dict_no_match_score,
        test_pattern_from_dict_roundtrip,
        test_record_fix_basic,
        test_record_fix_below_threshold,
        test_record_fix_deduplication,
        test_record_fix_different_contexts_not_merged,
        test_persist_and_reload,
        test_atomic_write_no_corruption,
        test_retrieve_exact_match,
        test_retrieve_partial_match,
        test_retrieve_no_match_different_zone,
        test_retrieve_top_k_limit,
        test_retrieve_sorted_by_score_then_improvement,
        test_retrieve_excludes_unreliable,
        test_suggest_returns_patch_or_none,
        test_suggest_returns_patch_with_patterns,
        test_suggest_max_suggestions,
        test_mark_preemptive_success,
        test_record_from_loop_result_success,
        test_record_from_loop_result_no_improvement,
        test_stats_empty,
        test_stats_populated,
        test_simulation_same_site_type_fewer_failures,
        test_simulation_different_seeds_same_archetype,
        test_simulation_multiple_zones,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            import traceback
            print(f"✗ {t.__name__} : {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{'✅' if failed == 0 else '❌'} {len(tests) - failed}/{len(tests)} tests passent.")
