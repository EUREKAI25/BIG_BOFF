"""
history_update — hook after de toute MRG.
Enregistre 100% des actions. Toute entrée doit être justifiée.
"""

from datetime import datetime, timezone


def history_update(context, catalog):
    """
    Appelé systématiquement dans le hook after de la MRG.
    Produit une entrée History et l'ajoute au context.
    """
    now = datetime.now(timezone.utc)

    scenario_ident  = context.get("scenario_ident", "unknown")
    object_ident    = context.get("object_ident") or _resolve_object_ident(context)
    validate_result = context.get("validate_result", {})
    execute_result  = context.get("execute_result", {})

    success = validate_result.get("success", True) if validate_result else True
    status  = "success" if success else "failure"

    entry = {
        "history_ident":         f"history_{now.strftime('%Y%m%d%H%M%S%f')}",
        "history_action":        f"mrg:{scenario_ident}",
        "history_trigger":       context.get("history_trigger", "mrg_execution"),
        "history_result":        _summarise_result(validate_result, execute_result),
        "history_justification": context.get("history_justification", f"Exécution du scénario {scenario_ident}"),
        "history_timestamp":     now.isoformat(),
        "history_agent":         context.get("history_agent", "mrg"),
        "history_scenario":      scenario_ident,
        "history_object_ident":  object_ident,
        "history_status":        status,
    }

    # Accumule dans le context (sera persisté par le storage en itération suivante)
    if "history_list" not in context:
        context["history_list"] = []
    context["history_list"].append(entry)
    context["how_reset"] = True  # signale que how doit être réinitialisé

    return context


def _resolve_object_ident(context):
    what = context.get("what")
    if isinstance(what, dict):
        return what.get("object_ident") or what.get("schema_ident") or what.get("rule_ident")
    return None


def _summarise_result(validate_result, execute_result):
    if validate_result:
        score = validate_result.get("score", "?")
        fail  = validate_result.get("failure_count", 0)
        return f"score={score}% failures={fail}"
    if execute_result:
        return f"execute_result={str(execute_result)[:80]}"
    return "no_result"
