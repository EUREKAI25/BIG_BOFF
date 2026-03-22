"""
Tests pour design_catalog (explore + catalog JSON).
Run : python -m pytest MODULES/design_catalog/tests/ -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[4]))
sys.path.insert(0, str(Path(__file__).parents[3]))

from design_catalog.design_explore import explore

CATALOG_PATH = Path(__file__).parents[1] / "design_catalog.json"


# ── Catalog JSON ─────────────────────────────────────────────────────────────

def test_catalog_json_valid():
    assert CATALOG_PATH.exists(), "design_catalog.json manquant"
    with open(CATALOG_PATH) as f:
        data = json.load(f)
    assert "entries" in data
    assert "version" in data


def test_catalog_has_8_endpoints():
    with open(CATALOG_PATH) as f:
        data = json.load(f)
    endpoints = [e for e in data["entries"] if e["type"] == "endpoint"]
    assert len(endpoints) == 12, f"Attendu 12 endpoints, trouvé {len(endpoints)}"


def test_catalog_has_6_scenarios():
    with open(CATALOG_PATH) as f:
        data = json.load(f)
    scenarios = [e for e in data["entries"] if e["type"] == "scenario"]
    assert len(scenarios) == 8, f"Attendu 8 scenarios, trouvé {len(scenarios)}"


def test_catalog_entry_schema():
    """Chaque entrée respecte le schéma requis."""
    with open(CATALOG_PATH) as f:
        data = json.load(f)
    required_keys = {"name", "category", "type", "goal", "mission", "inputs", "outputs",
                     "dependencies", "test_function", "example"}
    for entry in data["entries"]:
        missing = required_keys - set(entry.keys())
        assert not missing, f"Entry '{entry.get('name')}' manque : {missing}"


def test_catalog_naming_convention():
    """Tous les noms suivent <category>.<object>.<action>."""
    with open(CATALOG_PATH) as f:
        data = json.load(f)
    for entry in data["entries"]:
        name = entry["name"]
        parts = name.split(".")
        assert len(parts) == 3, f"Nom invalide (doit avoir 3 parties): {name}"
        assert parts[0] == "design", f"Catégorie invalide: {name}"


def test_catalog_all_categories_design():
    with open(CATALOG_PATH) as f:
        data = json.load(f)
    for entry in data["entries"]:
        assert entry["category"] == "design", f"Catégorie inattendue: {entry['name']}"


def test_catalog_all_inputs_have_type():
    with open(CATALOG_PATH) as f:
        data = json.load(f)
    for entry in data["entries"]:
        for inp_name, inp in entry.get("inputs", {}).items():
            assert "type" in inp, f"Input '{inp_name}' dans '{entry['name']}' sans 'type'"
            assert "required" in inp, f"Input '{inp_name}' dans '{entry['name']}' sans 'required'"


def test_catalog_endpoint_names():
    expected = {
        "design.visual_intent.generate",
        "design.palette.generate",
        "design.coherence.apply",
        "design.plan.generate",
        "design.render.page",
        "design.capture.page",
        "design.audit.page",
        "design.fix.page",
        "design.brand.generate",
        "design.logo.generate",
        "design.icons.generate",
        "design.typography.generate",
    }
    with open(CATALOG_PATH) as f:
        data = json.load(f)
    actual = {e["name"] for e in data["entries"] if e["type"] == "endpoint"}
    assert actual == expected


def test_catalog_scenario_names():
    expected = {
        "design.page.generate_basic",
        "design.page.generate_from_image",
        "design.page.generate_from_mockup",
        "design.page.generate_full",
        "design.page.audit",
        "design.page.fix",
        "design.brand.generate_full",
        "design.brand.generate_from_reference",
    }
    with open(CATALOG_PATH) as f:
        data = json.load(f)
    actual = {e["name"] for e in data["entries"] if e["type"] == "scenario"}
    assert actual == expected


# ── design.explore() ─────────────────────────────────────────────────────────

def test_explore_returns_structure():
    result = explore(category="design")
    for key in ("version", "category", "endpoints", "scenarios",
                "endpoint_count", "scenario_count", "all_inputs", "all_outputs", "dependencies_map"):
        assert key in result, f"Clé manquante: {key}"


def test_explore_endpoint_count():
    result = explore(category="design")
    assert result["endpoint_count"] == 12
    assert len(result["endpoints"]) == 12


def test_explore_scenario_count():
    result = explore(category="design")
    assert result["scenario_count"] == 8
    assert len(result["scenarios"]) == 8


def test_explore_filter_type_endpoint():
    result = explore(category="design", type="endpoint")
    assert result["endpoint_count"] == 12
    assert result["scenario_count"] == 0


def test_explore_filter_type_scenario():
    result = explore(category="design", type="scenario")
    assert result["scenario_count"] == 8
    assert result["endpoint_count"] == 0


def test_explore_by_name_found():
    result = explore(name="design.visual_intent.generate")
    assert result["found"] is True
    assert result["entry"]["name"] == "design.visual_intent.generate"
    assert result["entry"]["type"] == "endpoint"


def test_explore_by_name_not_found():
    result = explore(name="design.nonexistent.thing")
    assert result["found"] is False
    assert result["entry"] is None


def test_explore_all_inputs_populated():
    result = explore(category="design")
    for name, inputs in result["all_inputs"].items():
        assert isinstance(inputs, dict), f"Inputs vides pour {name}"


def test_explore_all_outputs_populated():
    result = explore(category="design")
    for name, outputs in result["all_outputs"].items():
        assert isinstance(outputs, dict), f"Outputs vides pour {name}"


def test_explore_dependencies_map():
    result = explore(category="design")
    dm = result["dependencies_map"]
    # visual_intent endpoint dépend de visual_intent_engine
    assert "visual_intent_engine" in dm.get("design.visual_intent.generate", [])
    # generate_basic scenario dépend de render endpoint
    assert "design.render.page" in dm.get("design.page.generate_basic", [])


def test_explore_endpoint_has_inputs_outputs():
    result = explore(category="design")
    for ep in result["endpoints"]:
        assert "inputs"  in ep, f"Endpoint sans inputs: {ep['name']}"
        assert "outputs" in ep, f"Endpoint sans outputs: {ep['name']}"
        assert "goal"    in ep, f"Endpoint sans goal: {ep['name']}"


def test_explore_scenario_has_steps():
    result = explore(category="design")
    for sc in result["scenarios"]:
        assert "steps" in sc, f"Scenario sans steps: {sc['name']}"
        assert len(sc["steps"]) > 0, f"Steps vides pour: {sc['name']}"
