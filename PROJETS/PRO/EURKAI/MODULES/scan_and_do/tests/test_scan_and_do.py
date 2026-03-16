"""
Tests du module scan_and_do.

Lance avec : pytest tests/ -v
"""

import sys
from pathlib import Path
from typing import Any, Dict

MODULE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(MODULE_ROOT))

from scan_and_do import scan_and_do, Scenario


# ─── Scénarios de test ───────────────────────────────────────────────────────

class CollectScenario(Scenario):
    """Enregistre les appels pour vérification."""

    def __init__(self):
        self.calls: list[tuple[str, Any]] = []

    def execute(self, key: str, obj: Any) -> None:
        self.calls.append((key, obj))


class SideEffectScenario(Scenario):
    """Accumule une valeur depuis chaque objet."""

    def __init__(self):
        self.total = 0

    def execute(self, key: str, obj: Dict[str, Any]) -> None:
        self.total += obj.get("value", 0)


# ─── Tests ───────────────────────────────────────────────────────────────────

def test_iterates_all_entries():
    objects = {"a": {"x": 1}, "b": {"x": 2}, "c": {"x": 3}}
    scenario = CollectScenario()
    scan_and_do(objects, scenario)
    assert len(scenario.calls) == 3


def test_passes_correct_key_and_obj():
    objects = {"foo": {"val": 42}}
    scenario = CollectScenario()
    scan_and_do(objects, scenario)
    key, obj = scenario.calls[0]
    assert key == "foo"
    assert obj == {"val": 42}


def test_empty_dict_no_calls():
    scenario = CollectScenario()
    scan_and_do({}, scenario)
    assert scenario.calls == []


def test_scenario_can_produce_side_effects():
    objects = {"a": {"value": 10}, "b": {"value": 20}, "c": {"value": 5}}
    scenario = SideEffectScenario()
    scan_and_do(objects, scenario)
    assert scenario.total == 35


def test_engine_returns_none():
    scenario = CollectScenario()
    result = scan_and_do({"x": {}}, scenario)
    assert result is None


def test_objects_of_any_type():
    """Le moteur est agnostique — accepte tout type de valeur."""
    objects = {
        "str_val":  "hello",
        "int_val":  42,
        "list_val": [1, 2, 3],
        "none_val": None,
    }
    scenario = CollectScenario()
    scan_and_do(objects, scenario)
    assert len(scenario.calls) == 4


def test_stub_scenario_runs():
    """Vérifie que le stub du catalogue s'exécute sans erreur."""
    from scan_and_do.stub import PrintScenario
    objects = {"a": {"x": 1}, "b": {"x": 2}}
    scan_and_do(objects, PrintScenario())  # ne lève pas d'exception
