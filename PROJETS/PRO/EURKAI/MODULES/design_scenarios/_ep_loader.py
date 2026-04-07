"""
_ep_loader.py — utilitaire interne : charge un endpoint depuis design_endpoints.
Import interne uniquement. Ne pas utiliser directement.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_EP_DIR = Path(__file__).parents[1] / "design_endpoints"


def load_endpoint(name: str):
    """Charge et retourne le module d'un endpoint par son nom."""
    path = _EP_DIR / f"{name}.py"
    if not path.exists():
        raise FileNotFoundError(f"Endpoint not found: {name}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
