"""
SuperValidate — valide what contre son schema.
Déclenche on_success ou on_failure selon le résultat.
Intègre scenario_debug_validate automatiquement.
"""

from core.functions.validate_object_vs_schema import validate_object_vs_schema
from core.hooks.log_hooks import log_success, log_failure


def super_validate(context, catalog):
    storage  = context["_storage"]
    what     = context.get("what", {})
    scenario = context.get("scenario", {})

    # Résoudre le schema depuis object_schema ou scenario
    schema_ident = (
        what.get("object_schema")
        or scenario.get("scenario_attending_result", {}).get("schema_ident")
        or "ObjectSchema"
    )
    schema = storage.get("schema", schema_ident)

    if schema is None:
        context["validate_result"] = {
            "success": False, "score": 0, "tested": 0,
            "failure_count": 1, "warning_count": 0,
            "failures": [{"field": "schema", "detail": f"schema_not_found:{schema_ident}", "type": "required"}],
            "warnings": [],
        }
    else:
        context["validate_result"] = validate_object_vs_schema(what, schema)

    context["validate_result"]["schema_ident"]  = schema_ident
    context["validate_result"]["object_ident"]  = what.get("object_ident") or context.get("object_ident")

    # Hooks conditionnels — log immédiat
    if context["validate_result"]["success"]:
        log_success(context, catalog)
    else:
        log_failure(context, catalog)

    return context
