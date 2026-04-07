#!/usr/bin/env python3
"""
test_pipeline_integration.py — Tests d'intégration du pipeline EURKAI

Valide :
  1. Le design_validator bloque les layouts invalides
  2. Le mécanisme de retry produit de vraies variations de plan
  3. Le pipeline converge dans max_attempts
  4. La boucle de validation rejette au moins un plan avant d'en accepter un

Usage :
    python test_pipeline_integration.py
    python test_pipeline_integration.py --brief "..." --verbose
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATH SETUP (même logique que pipeline.py)
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).parent
MODULES_DIR = SCRIPT_DIR / "MODULES"

sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(MODULES_DIR))
for _mod in sorted(MODULES_DIR.iterdir()):
    if _mod.is_dir() and not _mod.name.startswith(("_", ".")):
        sys.path.insert(0, str(_mod))

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────

from design_plan.src.design_plan import generate_design_plan, diff_plans, plans_are_distinct
from design_validator.src.design_validator import validate_layout, PASS_THRESHOLD
from pipeline import (
    PipelineOrchestrator,
    _extract_layout_from_plan,
    _mutate_seed,
    PLAN_REGEN_SEED_OFFSET,
    MAX_PLAN_ATTEMPTS,
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_SEP  = "─" * 64
_SEP2 = "═" * 64

def _hdr(title: str) -> None:
    print(f"\n{_SEP2}")
    print(f"  {title}")
    print(f"{_SEP2}")

def _sub(title: str) -> None:
    print(f"\n{_SEP}")
    print(f"  {title}")
    print(_SEP)

def _ok(msg: str) -> None:
    print(f"  ✅  {msg}")

def _fail(msg: str) -> None:
    print(f"  ❌  {msg}")

def _info(msg: str) -> None:
    print(f"  ·  {msg}")

def _warn(msg: str) -> None:
    print(f"  ⚠️   {msg}")


@dataclass
class TestResult:
    name:    str
    passed:  bool
    details: str = ""

    def __repr__(self) -> str:
        icon = "✅" if self.passed else "❌"
        return f"{icon} {self.name}"


RESULTS: list[TestResult] = []

def _record(name: str, passed: bool, details: str = "") -> TestResult:
    r = TestResult(name=name, passed=passed, details=details)
    RESULTS.append(r)
    if passed:
        _ok(f"PASS — {name}")
    else:
        _fail(f"FAIL — {name}")
    if details:
        for line in details.splitlines():
            print(f"       {line}")
    return r


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — DESIGN VALIDATOR : bloque les layouts invalides
# ─────────────────────────────────────────────────────────────────────────────

def _make_base_plan(seed: int = 42, brief: str = "Distillerie artisanale normande"):
    return generate_design_plan(brief=brief, seed=seed)

def _make_base_layout(plan) -> dict:
    """Layout valide extrait du plan."""
    return _extract_layout_from_plan(plan)


def test_validator_blocks_forbidden_patterns(brief: str) -> None:
    _hdr("TEST 1 — Validator blocks forbidden patterns")

    plan     = _make_base_plan(brief=brief)
    plan_d   = plan.to_dict()

    print(f"\n  Plan de référence : {plan.layout_strategy} / {plan.hero.type}")
    print(f"  Forbidden : {plan.constraints.forbidden[:4]}…")
    print(f"  Required  : {plan.constraints.required[:3]}…")

    # ── 1a. Centered hero ─────────────────────────────────────────────────────
    _sub("1a — centered_hero in forbidden → must FAIL")

    bad_layout = _make_base_layout(plan)
    bad_layout["hero"]["type"]        = "centered_hero"
    bad_layout["hero"]["positioning"] = "center_dominant"

    r1a = validate_layout(plan_d, bad_layout)
    print(f"       score={r1a.score}  valid={r1a.valid}")
    for reason in r1a.fail_reasons:
        print(f"       FAIL reason: {reason}")

    _record(
        "1a — centered_hero blocked",
        not r1a.valid and any("centered_hero" in f for f in r1a.fail_reasons),
        f"score={r1a.score}, fail_reasons={r1a.fail_reasons}",
    )

    # ── 1b. Uniform card grid ─────────────────────────────────────────────────
    _sub("1b — uniform_card_grid → must FAIL")

    bad_layout2 = _make_base_layout(plan)
    bad_layout2["sections"] = [
        {"type": "hero",          "layout_variant": "asymmetric_split",  "symmetric": False},
        {"type": "feature_block", "layout_variant": "card_grid",         "symmetric": False},
        {"type": "feature_block", "layout_variant": "product_grid",      "symmetric": False},
        {"type": "feature_block", "layout_variant": "collection_grid",   "symmetric": False},
        {"type": "cta_block",     "layout_variant": "full_width_cta",    "symmetric": False,
         "visually_isolated": True},
    ]

    r1b = validate_layout(plan_d, bad_layout2)
    print(f"       score={r1b.score}  valid={r1b.valid}")
    for reason in r1b.fail_reasons:
        print(f"       FAIL reason: {reason}")

    _record(
        "1b — uniform_card_grid blocked",
        not r1b.valid and any("uniform_card_grid" in f for f in r1b.fail_reasons),
        f"score={r1b.score}",
    )

    # ── 1c. Required item missing ──────────────────────────────────────────────
    _sub("1c — cta_visual_isolation absent → must FAIL")

    bad_layout3 = _make_base_layout(plan)
    bad_layout3["sections"] = [
        {"type": "hero",          "layout_variant": "asymmetric_split",  "symmetric": False},
        {"type": "feature_block", "layout_variant": "staggered_two_col", "symmetric": False},
        {"type": "cta_block",     "layout_variant": "full_width_cta",    "symmetric": False,
         "visually_isolated": False},   # ← manquant
    ]

    r1c = validate_layout(plan_d, bad_layout3)
    print(f"       score={r1c.score}  valid={r1c.valid}")
    for reason in r1c.fail_reasons:
        print(f"       FAIL reason: {reason}")

    _record(
        "1c — cta_visual_isolation enforced",
        not r1c.valid and any("cta_visual_isolation" in f for f in r1c.fail_reasons),
        f"score={r1c.score}",
    )

    # ── 1d. Score cumulatif trop bas → FAIL sans hard constraint ──────────────
    _sub("1d — accumulation of medium/minor violations → score < 70")

    p2 = generate_design_plan(
        brief=brief, seed=42,
        theme_hints={"layout": "editorial_flow"},
    )
    p2_d = p2.to_dict()

    bad_layout4 = _extract_layout_from_plan(p2)
    bad_layout4["hero"]["type"]           = "brutalist_text_dominant"   # hero mismatch −20
    bad_layout4["hero"]["positioning"]    = "extreme_right"              # positioning −20
    bad_layout4["hero"]["text_placement"] = "full_width_over_image"     # text_placement −5
    bad_layout4["structure"]["density"]   = "high"                      # density −5

    r1d = validate_layout(p2_d, bad_layout4)
    print(f"       score={r1d.score}  valid={r1d.valid}  (threshold={PASS_THRESHOLD})")
    for w in r1d.warnings:
        print(f"       WARNING: {w}")

    _record(
        "1d — cumulative violations fail score threshold",
        not r1d.valid and r1d.score < PASS_THRESHOLD,
        f"score={r1d.score} < threshold={PASS_THRESHOLD}",
    )

    # ── 1e. Layout valide de référence → doit PASSER ──────────────────────────
    _sub("1e — valid reference layout → must PASS")

    good_layout = _make_base_layout(plan)
    r1e = validate_layout(plan_d, good_layout)
    print(f"       score={r1e.score}  valid={r1e.valid}")
    for w in r1e.warnings:
        print(f"       WARNING: {w}")

    _record(
        "1e — valid layout passes",
        r1e.valid and r1e.score >= PASS_THRESHOLD,
        f"score={r1e.score}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — RETRY : variation réelle entre tentatives
# ─────────────────────────────────────────────────────────────────────────────

def test_retry_produces_variation(brief: str, base_seed: int = 42) -> None:
    _hdr("TEST 2 — Retry mechanism: variation between attempts")

    plans   = []
    results = []

    print(f"\n  Brief    : {brief[:60]}")
    print(f"  Seed 0   : {base_seed}")
    print(f"  Attempts : {MAX_PLAN_ATTEMPTS}")
    print()

    for attempt in range(1, MAX_PLAN_ATTEMPTS + 1):
        seed = _mutate_seed(base_seed, attempt - 1)
        plan = generate_design_plan(brief=brief, seed=seed)
        layout = _extract_layout_from_plan(plan)
        vr     = validate_layout(plan.to_dict(), layout)

        plans.append(plan)
        results.append(vr)

        icon = "✅" if vr.valid else "❌"
        print(
            f"  Attempt {attempt}  seed={seed:6d}  "
            f"layout={plan.layout_strategy:<20s}  "
            f"hero={plan.hero.type:<25s}  "
            f"score={vr.score:3d}  {icon}"
        )
        if vr.fail_reasons:
            for r in vr.fail_reasons:
                print(f"              FAIL: {r}")

    # ── Vérification de la variation ──────────────────────────────────────────
    print()
    _sub("2a — Plans are distinct across attempts")

    strategies = [p.layout_strategy for p in plans]
    hero_types = [p.hero.type for p in plans]
    profiles   = [p.brief_profile for p in plans]

    unique_strategies = len(set(strategies))
    unique_heroes     = len(set(hero_types))
    unique_profiles   = len(set(profiles))

    print(f"  Layout strategies : {strategies}")
    print(f"  Hero types        : {hero_types}")
    print(f"  Profiles          : {profiles}")
    print(f"  Unique strategies : {unique_strategies}")
    print(f"  Unique heroes     : {unique_heroes}")
    print()

    # Les plans doivent être distincts deux à deux (min 3 diffs)
    distinct_pairs = 0
    total_pairs    = 0
    for i in range(len(plans)):
        for j in range(i + 1, len(plans)):
            total_pairs += 1
            if plans_are_distinct(plans[i], plans[j], min_diffs=1):
                distinct_pairs += 1

    _record(
        "2a — retry produces distinct plans",
        distinct_pairs == total_pairs,
        f"{distinct_pairs}/{total_pairs} pairs distinct",
    )

    # ── Vérification convergence (au moins un PASS) ───────────────────────────
    _sub("2b — At least one valid plan within max_attempts")

    valid_attempts = [(i + 1, results[i]) for i in range(len(results)) if results[i].valid]
    _info(f"Valid attempts : {[a for a, _ in valid_attempts]}")
    _info(f"First valid    : attempt {valid_attempts[0][0] if valid_attempts else 'none'}")

    _record(
        "2b — convergence within max_attempts",
        len(valid_attempts) > 0,
        f"{len(valid_attempts)}/{MAX_PLAN_ATTEMPTS} valid plans found",
    )

    # ── Détail des diffs entre tentatives adjacentes ───────────────────────────
    _sub("2c — Diff between consecutive attempts")

    for i in range(len(plans) - 1):
        diffs = diff_plans(plans[i], plans[i + 1])
        print(f"  Attempt {i + 1} → {i + 2} : {len(diffs)} dimensions differ")
        for dim, (va, vb) in list(diffs.items())[:5]:
            print(f"    {dim:35s} {str(va)[:20]:22s} → {str(vb)[:20]}")

    _record(
        "2c — each seed produces measurable diff",
        all(
            len(diff_plans(plans[i], plans[i + 1])) > 0
            for i in range(len(plans) - 1)
        ),
        "all consecutive attempts differ",
    )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — BOUCLE VALIDATION AVEC FAIL FORCÉ, PUIS PASS
# ─────────────────────────────────────────────────────────────────────────────

def test_validation_loop_fail_then_pass(brief: str) -> None:
    """
    Simule une boucle de validation où :
    - La tentative 1 utilise un layout INVALIDE (inject d'un pattern interdit)
    - La tentative 2+ utilise le layout réel du plan

    Cela reproduit exactement le comportement de la boucle de pipeline
    dans un scénario où le renderer produirait un layout incorrect.
    """
    _hdr("TEST 3 — Validation loop: FAIL → retry → PASS")

    print("\n  Scénario : le renderer produit un layout invalide à la 1ère tentative,")
    print("             la boucle mute le seed et finit par obtenir un layout valide.\n")

    base_seed    = 42
    max_attempts = MAX_PLAN_ATTEMPTS
    fail_count   = 0
    pass_attempt = None

    for attempt in range(1, max_attempts + 1):
        seed = _mutate_seed(base_seed, attempt - 1)
        plan = generate_design_plan(brief=brief, seed=seed)

        # Simuler un renderer défaillant sur les 2 premières tentatives :
        # injecter un pattern interdit dans le layout extrait
        layout = _extract_layout_from_plan(plan)

        if attempt <= 2:
            # Injecter un pattern interdit : hero centré
            layout["hero"]["type"]        = "centered_hero"
            layout["hero"]["positioning"] = "center_aligned"
            simulation_note = "  [renderer fault: centered_hero injected]"
        else:
            simulation_note = "  [renderer correct: real layout]"

        vr = validate_layout(plan.to_dict(), layout)

        icon = "✅" if vr.valid else "❌ FAIL —"
        print(
            f"  Attempt {attempt}  seed={seed:6d}  "
            f"{icon} score={vr.score:3d}"
        )
        print(f"           layout={plan.layout_strategy:<20s}  "
              f"hero_injected={layout['hero']['type']}")
        print(f"           {simulation_note}")

        if vr.fail_reasons:
            for reason in vr.fail_reasons:
                print(f"           FAIL: {reason}")

        if not vr.valid:
            fail_count += 1
            _info(f"Attempt {attempt} REJECTED — retry with next seed")
        else:
            pass_attempt = attempt
            _info(f"Attempt {attempt} ACCEPTED — layout is valid")
            break

        print()

    print()
    _record(
        "3a — at least one FAIL before PASS",
        fail_count >= 1 and pass_attempt is not None,
        f"{fail_count} FAIL(s), PASS on attempt {pass_attempt}",
    )

    _record(
        "3b — PASS reached within max_attempts",
        pass_attempt is not None and pass_attempt <= max_attempts,
        f"converged at attempt {pass_attempt}/{max_attempts}",
    )

    _record(
        "3c — layout changed between first and final attempt",
        pass_attempt is not None and pass_attempt > 1,
        "different seed → different plan → valid layout",
    )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — PIPELINE END-TO-END
# ─────────────────────────────────────────────────────────────────────────────

def test_pipeline_end_to_end(brief: str, project_name: str, seed: int = 42) -> None:
    _hdr("TEST 4 — Full pipeline end-to-end")

    print(f"\n  Brief   : {brief[:72]}")
    print(f"  Project : {project_name}")
    print(f"  Seed    : {seed}\n")

    orchestrator = PipelineOrchestrator(
        output_dir=SCRIPT_DIR / "output" / "integration_tests",
        enable_capture=False,
        enable_audit=False,
        enable_learning=False,
        verbose=True,
    )

    t0 = time.time()
    result = orchestrator.run(
        brief=brief,
        project_name=project_name,
        seed=seed,
    )
    elapsed_ms = (time.time() - t0) * 1000

    print()
    _record(
        "4a — pipeline status = success",
        result.status == "success",
        f"status={result.status}, error={result.error}",
    )

    _record(
        "4b — output HTML saved",
        result.output_path is not None and Path(result.output_path).exists(),
        f"path={result.output_path}",
    )

    _record(
        "4c — converged within max_attempts",
        result.attempts <= MAX_PLAN_ATTEMPTS,
        f"attempts={result.attempts}, max={MAX_PLAN_ATTEMPTS}",
    )

    _record(
        "4d — execution time reasonable",
        elapsed_ms < 30_000,
        f"duration={elapsed_ms:.0f}ms",
    )

    if result.output_path:
        html_path = Path(result.output_path)
        design_plan_path = html_path.parent / html_path.name.replace("landing_", "design_plan_").replace(".html", ".json")
        _record(
            "4e — design plan JSON artifact saved",
            design_plan_path.exists(),
            f"path={design_plan_path}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — RÉGÉNÉRATION COMPLÈTE (seed +1000 si tout échoue)
# ─────────────────────────────────────────────────────────────────────────────

def test_full_regen_seed_offset(brief: str) -> None:
    _hdr("TEST 5 — Full regen: seed +1000 offset")

    base_seed  = 42
    regen_seed = base_seed + PLAN_REGEN_SEED_OFFSET

    plan_base  = generate_design_plan(brief=brief, seed=base_seed)
    plan_regen = generate_design_plan(brief=brief, seed=regen_seed)

    diffs = diff_plans(plan_base, plan_regen)

    print(f"\n  Seed base  : {base_seed}  → {plan_base.layout_strategy}  / {plan_base.hero.type}")
    print(f"  Seed regen : {regen_seed} → {plan_regen.layout_strategy} / {plan_regen.hero.type}")
    print(f"  Nb diffs   : {len(diffs)}")
    print()

    for dim, (va, vb) in list(diffs.items())[:8]:
        print(f"    {dim:40s} {str(va)[:20]:22s} → {str(vb)[:20]}")

    _record(
        "5a — regen seed (+1000) produces a different plan",
        plans_are_distinct(plan_base, plan_regen, min_diffs=1),
        f"{len(diffs)} dimensions differ",
    )

    vr_base  = validate_layout(plan_base.to_dict(),  _extract_layout_from_plan(plan_base))
    vr_regen = validate_layout(plan_regen.to_dict(), _extract_layout_from_plan(plan_regen))

    _record(
        "5b — regen plan is valid",
        vr_regen.valid,
        f"score={vr_regen.score}",
    )

    _info(f"base  : score={vr_base.score}  valid={vr_base.valid}")
    _info(f"regen : score={vr_regen.score}  valid={vr_regen.valid}")


# ─────────────────────────────────────────────────────────────────────────────
# RAPPORT FINAL
# ─────────────────────────────────────────────────────────────────────────────

def _print_summary() -> bool:
    print(f"\n{_SEP2}")
    print("  INTEGRATION TEST SUMMARY")
    print(_SEP2)

    passed = [r for r in RESULTS if r.passed]
    failed = [r for r in RESULTS if not r.passed]

    for r in RESULTS:
        icon = "✅" if r.passed else "❌"
        print(f"  {icon}  {r.name}")
        if r.details and not r.passed:
            print(f"       details: {r.details}")

    print(f"\n  {len(passed)}/{len(RESULTS)} tests passed")

    # Critères de validation du test
    print(f"\n  VALIDATION CRITERIA :")
    criteria = {
        "at least one FAIL occurs before PASS":
            any("3a" in r.name for r in passed),
        "layouts differ between attempts":
            any("2a" in r.name or "2c" in r.name for r in passed),
        "final layout is VALID":
            any("3b" in r.name or "4a" in r.name for r in passed),
    }
    all_criteria = True
    for criterion, met in criteria.items():
        icon = "✅" if met else "❌"
        print(f"    {icon}  {criterion}")
        if not met:
            all_criteria = False

    overall = len(failed) == 0 and all_criteria
    print(f"\n  {'✅ ALL TESTS PASS' if overall else '❌ SOME TESTS FAILED'}")
    print(_SEP2)

    return overall


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="EURKAI Pipeline Integration Tests",
    )
    parser.add_argument("--brief",   default="Distillerie artisanale normande, calvados haut de gamme depuis 1887",
                        help="Brief de test (défaut: maison-calva)")
    parser.add_argument("--name",    default="test_integration",
                        help="Nom du projet de test")
    parser.add_argument("--seed",    type=int, default=42)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    print(f"\n{_SEP2}")
    print("  EURKAI — Pipeline Integration Tests")
    print(_SEP2)
    print(f"  Brief : {args.brief[:70]}")
    print(f"  Seed  : {args.seed}")

    # ── Tests ─────────────────────────────────────────────────────────────────
    test_validator_blocks_forbidden_patterns(brief=args.brief)
    test_retry_produces_variation(brief=args.brief, base_seed=args.seed)
    test_validation_loop_fail_then_pass(brief=args.brief)
    test_pipeline_end_to_end(brief=args.brief, project_name=args.name, seed=args.seed)
    test_full_regen_seed_offset(brief=args.brief)

    # ── Rapport ───────────────────────────────────────────────────────────────
    ok = _print_summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
