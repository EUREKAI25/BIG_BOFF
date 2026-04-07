"""
scenario_validate
Valide un objet contre son schema via la MRG.
Scénario métier autonome — distinct de scenario_debug_validate (debug permanent).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from catalog.load_catalog import load_catalog
from core.mrg import mrg


def run(object_ident, verbose=True):
    catalog = load_catalog()
    storage = catalog["_storage"]

    obj = storage.get("object", object_ident)
    if obj is None:
        return {"success": False, "error": f"object_not_found:{object_ident}"}

    context = {
        "object_ident":           object_ident,
        "payload":                obj,
        "history_trigger":        "scenario_validate",
        "history_justification":  f"Validation — {object_ident}",
        "history_agent":          "scenario_validate",
    }

    result = mrg("scenario_validate", context, catalog)
    validate_result = result.get("validate_result", {})

    if verbose:
        status = "OK" if validate_result.get("success") else "FAIL"
        score  = validate_result.get("score", 0)
        print(f"  [{status}]   {object_ident} — score {score}%")
        if not validate_result.get("success"):
            for f in validate_result.get("failures", []):
                print(f"         ✗ {f.get('field')} : {f.get('detail')}")

    return validate_result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scenario_validate.py <object_ident>")
        sys.exit(1)
    result = run(sys.argv[1])
    sys.exit(0 if result.get("success") else 1)
