"""
scan_and_do.stub
─────────────────
Scénario minimal d'exemple — affiche chaque objet.

Usage :
    python -m scan_and_do.stub
"""

from __future__ import annotations
from typing import Any, Dict

from .engine import Scenario, scan_and_do


class PrintScenario(Scenario):
    """Scénario stub : imprime chaque entrée du dictionnaire."""

    def execute(self, key: str, obj: Dict[str, Any]) -> None:
        print(f"{key}: {obj}")


if __name__ == "__main__":
    objects = {
        "a": {"x": 1},
        "b": {"x": 2},
    }
    scan_and_do(objects, PrintScenario())
