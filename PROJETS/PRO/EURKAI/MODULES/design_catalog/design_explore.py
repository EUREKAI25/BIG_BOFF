"""
design.explore
Fonction d'exploration du système design EURKAI.

Usage :
    from design_catalog.design_explore import explore
    result = explore(category="design")
    result = explore(type="endpoint")
    result = explore(name="design.visual_intent.generate")
"""
from __future__ import annotations

import json
from pathlib import Path

_CATALOG_PATH = Path(__file__).parent / "design_catalog.json"

NAME     = "design.explore"
CATEGORY = "design"
VERSION  = "1.0.0"


def _load_catalog() -> dict:
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def explore(
    category: str | None = "design",
    type: str | None = None,
    name: str | None = None,
) -> dict:
    """
    Retourne la liste des endpoints/scénarios disponibles avec leurs schémas.

    Args:
        category : filtrer par catégorie (default: "design")
        type     : filtrer par type — "endpoint" | "scenario" | None (tous)
        name     : retourner l'entrée exacte par nom

    Returns:
        dict :
            version          : str
            category         : str
            endpoints        : list[dict]   — entrées de type "endpoint"
            scenarios        : list[dict]   — entrées de type "scenario"
            endpoint_count   : int
            scenario_count   : int
            all_inputs       : dict[name → inputs_schema]
            all_outputs      : dict[name → outputs_schema]
            dependencies_map : dict[name → list[str]]
    """
    catalog = _load_catalog()
    entries = catalog.get("entries", [])

    # Filtre category
    if category:
        entries = [e for e in entries if e.get("category") == category]

    # Filtre type
    if type:
        entries = [e for e in entries if e.get("type") == type]

    # Filtre name (entrée unique)
    if name:
        matches = [e for e in entries if e.get("name") == name]
        return {
            "version":          catalog.get("version"),
            "category":         category,
            "found":            len(matches) > 0,
            "entry":            matches[0] if matches else None,
        }

    endpoints = [e for e in entries if e.get("type") == "endpoint"]
    scenarios = [e for e in entries if e.get("type") == "scenario"]
    objects   = [e for e in entries if e.get("type") == "object"]

    all_inputs  = {e["name"]: e.get("inputs", {})  for e in entries}
    all_outputs = {e["name"]: e.get("outputs", {}) for e in entries}
    deps_map    = {e["name"]: e.get("dependencies", []) for e in entries}

    return {
        "version":          catalog.get("version"),
        "category":         category or "all",
        "endpoints":        [{"name": e["name"], "goal": e["goal"], "inputs": e.get("inputs", {}), "outputs": e.get("outputs", {})} for e in endpoints],
        "scenarios":        [{"name": e["name"], "goal": e["goal"], "steps": e.get("dependencies", []), "inputs": e.get("inputs", {}), "outputs": e.get("outputs", {})} for e in scenarios],
        "objects":          [{"name": e["name"], "goal": e["goal"], "class": e.get("class"), "module": e.get("module"), "methods": e.get("methods", []), "inputs": e.get("inputs", {}), "outputs": e.get("outputs", {})} for e in objects],
        "endpoint_count":   len(endpoints),
        "scenario_count":   len(scenarios),
        "object_count":     len(objects),
        "all_inputs":       all_inputs,
        "all_outputs":      all_outputs,
        "dependencies_map": deps_map,
    }
