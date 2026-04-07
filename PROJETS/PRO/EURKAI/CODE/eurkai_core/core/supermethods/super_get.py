"""
SuperGet — résout what et how.
Cherche l'objet cible depuis le catalog via le scenario.
Met what.object_how à status=ready.
"""


def super_get(context, catalog):
    storage        = context["_storage"]
    scenario_ident = context["scenario_ident"]
    scenario       = storage.get("scenario", scenario_ident)

    if scenario is None:
        raise ValueError(f"scenario_not_found:{scenario_ident}")

    context["scenario"] = scenario

    # Résoudre what : l'objet cible du scénario
    what_def = scenario.get("scenario_what", {})
    what     = _resolve_what(what_def, storage, context)

    # Mettre how à ready
    how_ident = scenario.get("scenario_how")
    if what is not None:
        what["object_how"] = {"how_ident": how_ident, "how_status": "ready"}

    context["what"]        = what
    context["how_ident"]   = how_ident
    context["object_ident"] = (what or {}).get("object_ident") or context.get("object_ident")

    return context


def _resolve_what(what_def, storage, context):
    """
    Résolution en 3 niveaux :
    1. Par object_ident explicite dans le context
    2. Par object_lineage dans what_def
    3. Wildcard * → retourne le context lui-même comme what
    """
    # Niveau 1 — ident explicite dans le context
    obj_ident = context.get("object_ident")
    if obj_ident:
        obj = storage.get("object", obj_ident)
        if obj:
            return dict(obj)

    # Niveau 2 — lineage dans what_def
    lineage = what_def.get("object_lineage")
    if lineage and lineage != "*":
        obj = storage.get("object", lineage)
        if obj:
            return dict(obj)

    # Niveau 3 — wildcard ou payload direct dans le context
    payload = context.get("payload")
    if payload and isinstance(payload, dict):
        return payload

    # Fallback — retourne un objet minimal depuis le context
    return {"object_ident": context.get("object_ident"), "object_lineage": "Object"}
