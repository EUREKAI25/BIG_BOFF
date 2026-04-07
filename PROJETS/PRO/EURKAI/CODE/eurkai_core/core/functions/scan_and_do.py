"""
scan_and_do — cœur de la MRG.
Parcourt what, applique how, retourne result.
Agnostique : ne porte aucune logique métier.

Règle : à chaque loop, how s'exécute sur tous les what dont object_how.status = ready.
"""

from core.functions.function_registry import get_function


def scan_and_do(what, how_ident, catalog):
    """
    Applique how_ident sur what.
    - Si what est un dict simple → applique directement
    - Si what contient une elementlist → parcourt récursivement
    """
    if how_ident is None:
        return {"scan_and_do_result": "no_how", "what": what}

    how_fn = get_function(how_ident)
    if how_fn is None:
        return {"scan_and_do_result": "how_not_found", "how_ident": how_ident}

    # Exécution sur what courant si status = ready
    how_status = (what.get("object_how") or {}).get("how_status")
    if how_status == "ready":
        return how_fn(what=what, catalog=catalog)

    # Parcours récursif de l'elementlist si présente
    elementlist = what.get("object_elementlist", {})
    if elementlist:
        results = {}
        for list_name, items in elementlist.items():
            if isinstance(items, dict):
                for item_key, item in items.items():
                    if isinstance(item, dict) and item.get("object_how", {}) and \
                       item["object_how"].get("how_status") == "ready":
                        results[item_key] = how_fn(what=item, catalog=catalog)
        return results if results else {"scan_and_do_result": "no_ready_items"}

    return {"scan_and_do_result": "executed", "what_ident": what.get("object_ident")}
