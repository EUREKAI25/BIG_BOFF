"""
design_endpoints — EURKAI Design Endpoint Layer
v1.1.0

12 endpoints atomiques wrappant les modules design EURKAI.
Convention de nommage : <category>.<object>.<action>

Endpoints disponibles :
    design.visual_intent.generate
    design.palette.generate
    design.coherence.apply
    design.plan.generate
    design.render.page
    design.capture.page
    design.audit.page
    design.fix.page
    design.brand.generate
    design.logo.generate
    design.icons.generate
    design.typography.generate
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).parent

ENDPOINTS: list[str] = [
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
]

VERSION = "1.1.0"


def load(name: str):
    """Charge un endpoint par nom et retourne son module."""
    path = _HERE / f"{name}.py"
    if not path.exists():
        raise FileNotFoundError(f"Endpoint not found: {name}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
