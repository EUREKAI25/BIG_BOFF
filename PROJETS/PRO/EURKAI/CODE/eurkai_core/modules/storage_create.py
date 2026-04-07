"""
storage_create
Génère les classes de modèles de données depuis les data_models d'une spec.
Une classe Python par data model (table de stockage).

Usage :
    from modules.storage_create import run
    result = run({"data_models": [...]})
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

MANIFEST = {
    "name":        "storage_create",
    "version":     "1.0.0",
    "type":        "module",
    "layer":       "creation",
    "inputs":      ["data_models"],
    "outputs":     ["modules"],
    "description": "Génère une classe Python par data model (table).",
}


def run(input_data):
    """
    input_data : {
        "data_models": [ {name, table, fields: [{name, type, notes}]} ]
    }

    Retourne : {
        "status":  "success" | "empty",
        "modules": [ {name, filename, code, table, layer} ]
    }
    """
    data_models = input_data.get("data_models") or []

    try:
        from agents.agent_generate_code import run as gen_code
    except ImportError as e:
        return {"status": "error", "error": str(e), "modules": []}

    catalog = {"_storage": None}
    results = []

    for model in data_models:
        name   = model["name"]
        table  = model.get("table", name.lower() + "s")
        fields = {f["name"]: f.get("type", "Any") for f in model.get("fields", [])}

        r = gen_code(
            _to_snake(name),
            {
                "object_type": "class",
                "object_goal": f"Data model — table {table}.",
                "attributes":  fields,
            },
            catalog,
            verbose=False,
        )
        if r.get("status") in ("ok", "partial"):
            results.append({
                "name":     name,
                "filename": r["filename"],
                "code":     r["code"],
                "table":    table,
                "layer":    "storage",
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
        "data_models": [
            {"name": "User",    "table": "users",    "fields": [
                {"name": "id",    "type": "uuid"},
                {"name": "email", "type": "string"},
            ]},
            {"name": "Invoice", "table": "invoices", "fields": [
                {"name": "id",     "type": "uuid"},
                {"name": "amount", "type": "decimal"},
                {"name": "status", "type": "enum"},
            ]},
        ],
    }
    r = run(_input)
    print(f"status  : {r['status']}")
    print(f"modules : {[m['name'] for m in r['modules']]}")
    for m in r["modules"]:
        print(f"  [{m['table']}] {m['filename']}")
        print(m["code"][:150])
