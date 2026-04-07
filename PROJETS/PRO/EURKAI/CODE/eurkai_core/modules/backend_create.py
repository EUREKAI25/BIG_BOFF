"""
backend_create
Génère les modules backend et shared depuis les composants d'une spec.
Un module Python par composant de layer backend/shared.

Usage :
    from modules.backend_create import run
    result = run({"components": [...], "architecture": {...}})
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

MANIFEST = {
    "name":        "backend_create",
    "version":     "1.0.0",
    "type":        "module",
    "layer":       "creation",
    "inputs":      ["components", "architecture"],
    "outputs":     ["modules"],
    "description": "Génère un module Python par composant backend/shared.",
}


def run(input_data):
    """
    input_data : {
        "components":   [ {name, layer, feature, priority, type} ]
        "architecture": {pattern, stack_notes, layers}
    }

    Retourne : {
        "status":  "success" | "empty" | "error",
        "modules": [ {name, filename, code, layer, priority, validation, debug_applied?} ]
    }

    Chaîne de qualification par module :
        agent_generate_code → agent_debug_fix (si SyntaxError) → agent_validator
    """
    components = input_data.get("components") or []
    arch       = input_data.get("architecture") or {}
    pattern    = arch.get("pattern", "")

    try:
        from agents.agent_generate_code import run as gen_code
    except ImportError as e:
        return {"status": "error", "error": str(e), "modules": []}

    try:
        from agents.agent_debug_fix import run as debug_fix
        _has_debug_fix = True
    except ImportError:
        _has_debug_fix = False

    try:
        from agents.agent_validator import run as validator
        _has_validator = True
    except ImportError:
        _has_validator = False

    catalog = {"_storage": None}
    results = []

    for comp in components:
        if comp.get("layer") not in ("backend", "shared"):
            continue
        name    = comp["name"]
        feature = comp.get("feature", name)
        goal    = f"{feature}. Pattern : {pattern}." if pattern else feature

        # ── 1. Génération ────────────────────────────────────────────────────
        r = gen_code(
            _to_snake(name),
            {"object_type": "module", "object_goal": goal},
            catalog,
            verbose=False,
        )
        if r.get("status") not in ("ok", "partial"):
            continue

        code          = r["code"]
        filename      = r["filename"]
        debug_applied = None

        # ── 2. Debug fix si syntaxe invalide ─────────────────────────────────
        if _has_debug_fix:
            try:
                import ast as _ast
                _ast.parse(code)
            except SyntaxError as e:
                fix_result = debug_fix(code, str(e),
                                       context={"name": name, "goal": goal},
                                       verbose=False)
                if fix_result.get("status") == "success":
                    code          = fix_result["fixed_code"]
                    debug_applied = fix_result.get("fix_applied", "unknown")

        # ── 3. Validation ────────────────────────────────────────────────────
        validation = {"score": 0, "issues": [], "warnings": []}
        if _has_validator:
            obj_for_val = {
                "type":        "module",
                "ident":       _to_snake(name),
                "object_goal": goal,
                "object_type": "module",
            }
            val_result = validator(obj_for_val, code, verbose=False)
            validation = {
                "score":    val_result.get("score", 0),
                "issues":   val_result.get("issues", []),
                "warnings": val_result.get("warnings", []),
            }

        entry = {
            "name":       name,
            "filename":   filename,
            "code":       code,
            "layer":      comp.get("layer", "backend"),
            "priority":   comp.get("priority", "P2"),
            "validation": validation,
        }
        if debug_applied is not None:
            entry["debug_applied"] = debug_applied

        results.append(entry)

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
            {"name": "InvoiceModule",  "layer": "backend",  "feature": "Invoice management",  "priority": "P1"},
            {"name": "PaymentService", "layer": "backend",  "feature": "Payment tracking",    "priority": "P1"},
            {"name": "AuthModule",     "layer": "shared",   "feature": "Authentication",      "priority": "P1"},
            {"name": "DashboardView",  "layer": "frontend", "feature": "Dashboard",           "priority": "P2"},
        ],
        "architecture": {"pattern": "REST API — versioned"},
    }
    r = run(_input)
    print(f"status  : {r['status']}")
    print(f"modules : {[m['name'] for m in r['modules']]}")
    for m in r["modules"]:
        print(f"  [{m['layer']}/{m['priority']}] {m['filename']}")
