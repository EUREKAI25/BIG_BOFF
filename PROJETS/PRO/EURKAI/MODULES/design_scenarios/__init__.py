"""
design_scenarios — EURKAI Design Scenario Layer
v1.1.0

8 scénarios orchestrant les endpoints design EURKAI.
Convention de nommage : <category>.<object>.<action>

Un scénario = séquence d'endpoints + trace d'exécution.

Scénarios disponibles :
    design.page.generate_basic
    design.page.generate_from_image
    design.page.generate_from_mockup
    design.page.generate_full
    design.page.audit
    design.page.fix
    design.brand.generate_full
    design.brand.generate_from_reference
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).parent

SCENARIOS: list[str] = [
    "design.page.generate_basic",
    "design.page.generate_from_image",
    "design.page.generate_from_mockup",
    "design.page.generate_full",
    "design.page.audit",
    "design.page.fix",
    "design.brand.generate_full",
    "design.brand.generate_from_reference",
]

VERSION = "1.1.0"


def load(name: str):
    """Charge un scénario par nom et retourne son module."""
    path = _HERE / f"{name}.py"
    if not path.exists():
        raise FileNotFoundError(f"Scenario not found: {name}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
