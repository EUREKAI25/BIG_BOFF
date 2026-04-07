"""
MRG — Machine Récursive Générique
Cycle canonique : SuperGet → SuperExecute → SuperValidate → SuperRender → after

Règles :
- 4 supermethods, rien de plus dans mrg()
- after est TOUJOURS exécuté (history_update + how_reset)
- scenario_debug_validate est intégré dans SuperValidate (automatique)
"""

from core.supermethods.super_get     import super_get
from core.supermethods.super_execute import super_execute
from core.supermethods.super_validate import super_validate
from core.supermethods.super_render  import super_render
from core.hooks.history_update       import history_update
from core.storage.catalog_storage    import get_storage


def mrg(scenario_ident, context, catalog):
    # Injecter le storage dans le context (disponible pour toutes les supermethods)
    context["_storage"]      = get_storage(catalog)
    context["scenario_ident"] = scenario_ident

    context = super_get(context, catalog)
    context = super_execute(context, catalog)
    context = super_validate(context, catalog)
    context = super_render(context, catalog)

    # after — toujours, quoi qu'il arrive
    context = history_update(context, catalog)

    # Réinitialiser how après exécution (règle : how.execute.after = value.reset)
    if context.get("what") and isinstance(context["what"], dict):
        context["what"]["object_how"] = None

    return context
