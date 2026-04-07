"""
SuperRender — produit la sortie exploitable.
Formats : raw (toujours), summary, typed (selon context).
"""


def super_render(context, catalog):
    validate_result = context.get("validate_result", {})
    execute_result  = context.get("execute_result", {})
    what            = context.get("what", {})

    context["render_result"] = {
        "render_object_ident":   what.get("object_ident") or context.get("object_ident"),
        "render_scenario_ident": context.get("scenario_ident"),
        "render_success":        validate_result.get("success", True),
        "render_score":          validate_result.get("score", 100),
        "render_summary":        _build_summary(validate_result, execute_result),
        "render_raw":            {
            "what":           what,
            "execute_result": execute_result,
            "validate_result": validate_result,
        },
    }
    return context


def _build_summary(validate_result, execute_result):
    if not validate_result:
        return {"status": "no_validation"}
    return {
        "status":        "success" if validate_result.get("success") else "failure",
        "score":         validate_result.get("score", 0),
        "failure_count": validate_result.get("failure_count", 0),
        "warning_count": validate_result.get("warning_count", 0),
        "failures":      validate_result.get("failures", []),
        "warnings":      validate_result.get("warnings", []),
    }
