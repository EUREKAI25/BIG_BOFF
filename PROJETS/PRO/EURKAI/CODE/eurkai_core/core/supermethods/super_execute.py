"""
SuperExecute — exécute how sur what via scan_and_do.
"""

from core.functions.scan_and_do import scan_and_do


def super_execute(context, catalog):
    what      = context.get("what", {})
    how_ident = context.get("how_ident")

    context["execute_result"] = scan_and_do(what, how_ident, catalog)
    return context
