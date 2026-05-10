"""
Tests — ProjectExecutionContext integration

4 tests :
  1. rules/resources reçus par le pipeline (via meta["context"])
  2. context transmis au validator (_execution_context dans résultat validate)
  3. mode="skeleton" propagé jusqu'au meta final
  4. backward compat — tous les scénarios fonctionnent sans context
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context import ProjectExecutionContext
from scenarios.scenario_idea_to_brief import run as run_idea_to_brief


# ── Fixtures minimales ────────────────────────────────────────────────────────

_VALID_IDEA_INPUT = {"idea": "a SaaS platform to track freelance invoices and payments"}

_VALID_BRIEF_INPUT = {
    "brief": {
        "project_name":  "FreelanceTrack",
        "project_type":  "saas",
        "description":   "Track invoices and payments for freelancers",
        "target_users":  "freelancers",
        "core_features": ["invoice creation", "payment tracking"],
        "constraints":   {"tech": [], "ux": []},
        "monetization":  "freemium",
        "priority":      "high",
    }
}


# ── Test 1 — rules/resources reçus par le pipeline ───────────────────────────

def test_rules_resources_received_by_pipeline():
    ctx = ProjectExecutionContext(
        rules={"max_retries": 3, "timeout_seconds": 60},
        resources={"budget": "low", "provider": "anthropic"},
        mode="real",
        validation_level="core",
    )
    result = run_idea_to_brief(_VALID_IDEA_INPUT, verbose=False, context=ctx)

    assert result["status"] == "success", f"Expected success, got: {result}"
    assert "context" in result["meta"], "meta should contain 'context' key"

    ctx_in_meta = result["meta"]["context"]
    assert ctx_in_meta["rules"] == {"max_retries": 3, "timeout_seconds": 60}
    assert ctx_in_meta["resources"] == {"budget": "low", "provider": "anthropic"}
    assert ctx_in_meta["mode"] == "real"
    assert ctx_in_meta["validation_level"] == "core"

    print("  [PASS] test_rules_resources_received_by_pipeline")


# ── Test 2 — context transmis au validator ────────────────────────────────────

def test_context_transmitted_to_validator():
    from agents.agent_validator import run as validate

    ctx_dict = {
        "rules":            {"strict": True},
        "resources":        {},
        "mode":             "real",
        "validation_level": "full",
        "meta":             {},
        "_execution_context": {
            "rules":            {"strict": True},
            "resources":        {},
            "mode":             "real",
            "validation_level": "full",
            "meta":             {},
        },
    }

    obj  = {"type": "function", "ident": "compute_invoice_total", "inputs": {}, "outputs": {}}
    code = "def compute_invoice_total(items):\n    return sum(i['amount'] for i in items)\n"

    result = validate(obj, code, context=ctx_dict, verbose=False)

    assert "_execution_context" in result, "validator should expose _execution_context from context"
    assert result["_execution_context"]["rules"] == {"strict": True}

    print("  [PASS] test_context_transmitted_to_validator")


# ── Test 3 — mode="skeleton" propagé ─────────────────────────────────────────

def test_mode_skeleton_propagates():
    ctx = ProjectExecutionContext(mode="skeleton")
    result = run_idea_to_brief(_VALID_IDEA_INPUT, verbose=False, context=ctx)

    assert result["status"] == "success", f"Expected success, got: {result}"
    assert result["meta"]["context"]["mode"] == "skeleton"

    print("  [PASS] test_mode_skeleton_propagates")


# ── Test 4 — backward compat sans context ────────────────────────────────────

def test_backward_compat_no_context():
    from scenarios.scenario_brief_to_cdc      import run as run_brief_to_cdc
    from scenarios.scenario_cdc_to_specs      import run as run_cdc_to_specs
    from scenarios.scenario_specs_to_deliverable import run as run_specs_to_deliverable

    # scenario_idea_to_brief
    r1 = run_idea_to_brief(_VALID_IDEA_INPUT, verbose=False)
    assert r1["status"] == "success"
    assert "context" not in r1["meta"], "meta should NOT contain 'context' key when context=None"

    # scenario_brief_to_cdc
    r2 = run_brief_to_cdc(_VALID_BRIEF_INPUT, verbose=False)
    assert r2["status"] == "success"
    assert "context" not in r2["meta"]

    # scenario_cdc_to_specs (needs a valid cdc)
    cdc_input = {"cdc": r2["data"]["cdc"]}
    r3 = run_cdc_to_specs(cdc_input, verbose=False)
    assert r3["status"] == "success"
    assert "context" not in r3["meta"]

    # scenario_specs_to_deliverable (needs valid specs)
    specs_input = {"specs": r3["data"]["specs"]}
    r4 = run_specs_to_deliverable(specs_input, verbose=False)
    assert r4["status"] == "success"
    assert "context" not in r4["meta"]

    print("  [PASS] test_backward_compat_no_context")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_rules_resources_received_by_pipeline,
        test_context_transmitted_to_validator,
        test_mode_skeleton_propagates,
        test_backward_compat_no_context,
    ]

    print("=" * 65)
    print("  test_project_execution_context")
    print("=" * 65)

    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {t.__name__} : {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {t.__name__} : {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'=' * 65}")
    print(f"  {passed}/{passed + failed} passed")
    print("=" * 65)
