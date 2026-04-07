"""
frontend_create
Génère les composants frontend depuis les composants d'une spec.
Une classe Python par composant de layer frontend.

Usage :
    from modules.frontend_create import run
    result = run({"components": [...]})
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

MANIFEST = {
    "name":        "frontend_create",
    "version":     "1.0.0",
    "type":        "module",
    "layer":       "creation",
    "inputs":      ["components"],
    "outputs":     ["modules"],
    "description": "Génère une classe Python par composant frontend.",
}


def run(input_data):
    """
    input_data : {
        "components": [ {name, layer, feature, priority, type} ]
    }

    Retourne : {
        "status":  "success" | "empty",
        "modules": [ {name, filename, code, layer} ]
    }
    """
    components = input_data.get("components") or []

    try:
        from agents.agent_generate_code import run as gen_code
    except ImportError as e:
        return {"status": "error", "error": str(e), "modules": []}

    catalog = {"_storage": None}
    results = []

    for comp in components:
        if comp.get("layer") != "frontend":
            continue
        name = comp["name"]
        r = gen_code(
            _to_snake(name),
            {"object_type": "class", "object_goal": comp.get("feature", name)},
            catalog,
            verbose=False,
        )
        if r.get("status") in ("ok", "partial"):
            results.append({
                "name":     name,
                "filename": r["filename"],
                "code":     r["code"],
                "layer":    "frontend",
            })

    status = "success" if results else "empty"
    return {"status": status, "modules": results}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_snake(s):
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", str(s))
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# ── Smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _input = {
        "components": [
            {"name": "DashboardView", "layer": "frontend", "feature": "Dashboard UI",   "priority": "P1"},
            {"name": "InvoiceForm",   "layer": "frontend", "feature": "Invoice form",   "priority": "P1"},
            {"name": "ApiClient",     "layer": "frontend", "feature": "API calls",      "priority": "P1"},
            {"name": "AuthModule",    "layer": "shared",   "feature": "Authentication", "priority": "P1"},
        ],
    }
    r = run(_input)
    print(f"status  : {r['status']}")
    print(f"modules : {[m['name'] for m in r['modules']]}")
    for m in r["modules"]:
        print(f"  [{m['layer']}] {m['filename']}")
