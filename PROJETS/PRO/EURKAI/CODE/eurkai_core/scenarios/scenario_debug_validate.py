"""
scenario_debug_validate
Valide tous les objets du catalog contre leurs schémas.
S'exécute via la MRG — history loggée automatiquement.
Peut être appelé manuellement ou via hook after.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from catalog.load_catalog import load_catalog
from core.mrg import mrg


def run(object_ident=None, verbose=True):
    """
    Lance scenario_debug_validate sur un objet ou sur tout le catalog.
    """
    catalog = load_catalog()
    storage = catalog["_storage"]

    targets = (
        {object_ident: storage.get("object", object_ident)}
        if object_ident
        else {
            t: obj
            for type_name in storage.list_types()
            for t, obj in storage.get_all(type_name).items()
        }
    )

    if verbose:
        print("=" * 60)
        print(f"scenario_debug_validate — {len(targets)} objet(s)")
        print("=" * 60)

    all_history = []
    passed = total = 0

    for ident, obj in targets.items():
        if obj is None:
            continue
        total += 1

        context = {
            "object_ident":        ident,
            "payload":             obj,
            "history_trigger":     "scenario_debug_validate",
            "history_justification": f"Validation de conformité — {ident}",
            "history_agent":       "scenario_debug_validate",
        }

        result = mrg("scenario_debug_validate", context, catalog)

        if result.get("validate_result", {}).get("success", True):
            passed += 1

        all_history.extend(result.get("history_list", []))

    summary = {
        "total":  total,
        "passed": passed,
        "failed": total - passed,
        "score":  round(100 * passed / total) if total else 0,
    }

    if verbose:
        print(f"\nRÉSULTAT : {passed}/{total} — score global {summary['score']}%")
        print("=" * 60)

    # Persister le rapport + history
    output_path = Path(__file__).parent.parent / "output" / "validation_report.json"
    with open(output_path, "w") as f:
        json.dump({"summary": summary, "history_list": all_history}, f, indent=2, ensure_ascii=False)

    return summary


if __name__ == "__main__":
    obj = sys.argv[1] if len(sys.argv) > 1 else None
    result = run(object_ident=obj)
    sys.exit(0 if result["score"] == 100 else 1)
