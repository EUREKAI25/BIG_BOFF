"""
product_create
Orchestrateur de création produit logiciel depuis des specs.

Compose :
  - backend_create  → modules backend/shared (1 module Python / composant)
  - frontend_create → composants frontend (1 classe Python / composant)
  - storage_create  → modèles de données (1 classe Python / data model)

Usage :
    from modules.product_create import run
    result = run({"specs": {...}})

Contrat de sortie :
    {
        "status":          "success" | "partial" | "error",
        "deliverable_type": "code",
        "deliverable": {
            "backend":  [ {name, filename, code, layer, priority} ],
            "frontend": [ {name, filename, code, layer} ],
            "storage":  [ {name, filename, code, table, layer} ],
        },
        "meta": {
            "note":     str,
            "steps":    [ {module, status, count} ],
            "errors":   []
        }
    }
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

MANIFEST = {
    "name":        "product_create",
    "version":     "1.0.0",
    "type":        "module",
    "layer":       "orchestration",
    "inputs":      ["specs"],
    "outputs":     ["deliverable"],
    "sub_modules": ["backend_create", "frontend_create", "storage_create"],
    "description": "Orchestre la création d'un produit logiciel depuis des specs.",
}


def run(input_data):
    """
    input_data : {"specs": {...}}

    Orchestre backend_create + frontend_create + storage_create
    selon les composants et data_models des specs.
    """
    meta   = {"steps": [], "errors": []}
    specs  = input_data.get("specs") if isinstance(input_data, dict) else None

    if not specs or not isinstance(specs, dict):
        return {"status": "error", "error": "specs_missing",
                "deliverable_type": "code", "deliverable": {}, "meta": meta}

    components  = specs.get("components") or []
    data_models = specs.get("data_models") or []
    arch        = specs.get("architecture") or {}

    # ── backend_create ────────────────────────────────────────────────────────
    try:
        from modules.backend_create import run as backend_create
        r_back = backend_create({"components": components, "architecture": arch})
        meta["steps"].append({
            "module": "backend_create",
            "status": r_back["status"],
            "count":  len(r_back.get("modules", [])),
        })
        if r_back["status"] == "error":
            meta["errors"].append(f"backend_create:{r_back.get('error')}")
    except ImportError as e:
        r_back = {"status": "error", "modules": []}
        meta["errors"].append(f"backend_create_import:{e}")

    # ── frontend_create ───────────────────────────────────────────────────────
    try:
        from modules.frontend_create import run as frontend_create
        r_front = frontend_create({"components": components})
        meta["steps"].append({
            "module": "frontend_create",
            "status": r_front["status"],
            "count":  len(r_front.get("modules", [])),
        })
        if r_front["status"] == "error":
            meta["errors"].append(f"frontend_create:{r_front.get('error')}")
    except ImportError as e:
        r_front = {"status": "error", "modules": []}
        meta["errors"].append(f"frontend_create_import:{e}")

    # ── storage_create ────────────────────────────────────────────────────────
    try:
        from modules.storage_create import run as storage_create
        r_stor = storage_create({"data_models": data_models})
        meta["steps"].append({
            "module": "storage_create",
            "status": r_stor["status"],
            "count":  len(r_stor.get("modules", [])),
        })
        if r_stor["status"] == "error":
            meta["errors"].append(f"storage_create:{r_stor.get('error')}")
    except ImportError as e:
        r_stor = {"status": "error", "modules": []}
        meta["errors"].append(f"storage_create_import:{e}")

    backend  = r_back.get("modules", [])
    frontend = r_front.get("modules", [])
    storage  = r_stor.get("modules", [])

    total = len(backend) + len(frontend) + len(storage)

    meta["note"] = (
        f"product_create — {len(backend)} backend, "
        f"{len(frontend)} frontend, {len(storage)} storage."
    )

    if total == 0:
        return {"status": "error", "error": "no_module_generated",
                "deliverable_type": "code",
                "deliverable": {"backend": [], "frontend": [], "storage": []},
                "meta": meta}

    status = "partial" if meta["errors"] else "success"

    return {
        "status":           status,
        "deliverable_type": "code",
        "deliverable": {
            "backend":  backend,
            "frontend": frontend,
            "storage":  storage,
        },
        "meta": meta,
    }


# ── Smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _specs = {
        "architecture": {
            "pattern":    "REST API — versioned · SPA frontend",
            "stack_notes": "Containerized. Deploy on Railway.",
        },
        "components": [
            {"name": "InvoiceModule",  "layer": "backend",  "feature": "Invoice management",  "priority": "P1"},
            {"name": "PaymentService", "layer": "backend",  "feature": "Payment tracking",    "priority": "P1"},
            {"name": "AuthModule",     "layer": "shared",   "feature": "Authentication",      "priority": "P1"},
            {"name": "DashboardView",  "layer": "frontend", "feature": "Dashboard UI",        "priority": "P2"},
            {"name": "ApiClient",      "layer": "frontend", "feature": "API client",          "priority": "P1"},
        ],
        "data_models": [
            {"name": "User",    "table": "users",    "fields": [{"name": "id", "type": "uuid"}, {"name": "email", "type": "string"}]},
            {"name": "Invoice", "table": "invoices", "fields": [{"name": "id", "type": "uuid"}, {"name": "amount", "type": "decimal"}]},
        ],
    }

    r = run({"specs": _specs})
    print(f"status           : {r['status']}")
    print(f"deliverable_type : {r['deliverable_type']}")
    print(f"note             : {r['meta']['note']}")
    print(f"steps            : {r['meta']['steps']}")
    print(f"backend          : {[m['name'] for m in r['deliverable']['backend']]}")
    print(f"frontend         : {[m['name'] for m in r['deliverable']['frontend']]}")
    print(f"storage          : {[m['name'] for m in r['deliverable']['storage']]}")
    if r["meta"]["errors"]:
        print(f"errors           : {r['meta']['errors']}")
