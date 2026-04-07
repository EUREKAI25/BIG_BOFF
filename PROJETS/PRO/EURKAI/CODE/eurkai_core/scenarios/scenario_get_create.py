"""
scenario_get_create
Cherche un objet via SuperGet (3 niveaux).
  Niveau 1 : par object_ident exact
  Niveau 2 : par object_lineage
  Niveau 3 : agent_generate_object + triple validation
Si trouvé : valide via MRG.
Si généré : triple_validate selon scenario_execution_modality.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from catalog.load_catalog import load_catalog
from core.mrg import mrg
from agents.agent_generate_object import run as agent_generate
from core.functions.triple_validate import triple_validate


def run(object_ident, lineage=None, schema_ident=None,
        goal=None, modality="L1+L2+L3", verbose=True):
    catalog = load_catalog()
    storage = catalog["_storage"]

    # Niveau 1 — par ident exact
    obj = storage.get("object", object_ident)

    # Niveau 2 — par lineage
    if obj is None and lineage:
        matches = storage.get_all_by_filter("object", lambda o: o.get("object_lineage") == lineage)
        obj     = next(iter(matches.values()), None)

    # Niveau 3 — agent_generate_object + triple_validate
    if obj is None:
        target_schema = schema_ident or "ObjectSchema"
        schema        = storage.get("schema", target_schema)

        if schema is None:
            return {"success": False, "error": f"schema_not_found:{target_schema}"}

        params = {
            "object_lineage": lineage or f"Object:{object_ident}",
            "object_goal":    goal or f"Objet {object_ident}",
        }

        agent_result = agent_generate(target_schema, params, catalog, verbose=verbose)

        if not agent_result.get("success"):
            return {
                "success": False,
                "status":  "agent_failed",
                "error":   agent_result.get("error"),
                "stage":   agent_result.get("stage", "agent_generate"),
            }

        generated = agent_result["generated_object"]
        tv_result = triple_validate(generated, schema, params, modality)

        if verbose:
            status = "OK" if tv_result["success"] else "FAIL"
            print(f"  [{status}]   triple_validate — score {tv_result['score']}% ({modality})")

        return {
            "success":          tv_result["success"],
            "status":           "generated",
            "generated_object": generated,
            "triple_validate":  tv_result,
            "usage":            agent_result.get("usage", {}),
        }

    # Objet trouvé — valider via MRG
    context = {
        "object_ident":          object_ident,
        "payload":               obj,
        "history_trigger":       "scenario_get_create",
        "history_justification": f"Get — {object_ident}",
        "history_agent":         "scenario_get_create",
    }

    result        = mrg("scenario_get_create", context, catalog)
    validate_result = result.get("validate_result", {})

    if verbose:
        status = "OK" if validate_result.get("success") else "FAIL"
        score  = validate_result.get("score", 0)
        print(f"  [{status}]   {object_ident} — score {score}%")

    return {"success": validate_result.get("success"), "status": "found",
            "validate_result": validate_result}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scenario_get_create.py <object_ident> [lineage] [schema_ident] [goal]")
        sys.exit(1)
    obj_ident    = sys.argv[1]
    lineage_arg  = sys.argv[2] if len(sys.argv) > 2 else None
    schema_arg   = sys.argv[3] if len(sys.argv) > 3 else None
    goal_arg     = sys.argv[4] if len(sys.argv) > 4 else None
    result       = run(obj_ident, lineage_arg, schema_arg, goal_arg)
    print(json.dumps({k: v for k, v in result.items()
                      if k != "generated_object"}, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("success") else 1)
