from core.utils.resolve_how import resolve_how
from storage.get_storage import get_storage

def SuperGet(context, catalog):
    storage = get_storage(catalog)
    scenario_ident = context["scenario_ident"]
    scenario = storage.get_scenario(scenario_ident)
    if scenario is None:
        raise ValueError(f"Unknown scenario: {scenario_ident}")

    what = storage.get_first_object_by_filter(scenario["what"]["filter"])
    if what is None:
        raise ValueError(f"No object found for filter: {scenario['what']['filter']}")

    how = resolve_how(scenario, what, catalog)

    what["how"] = {
        "value": scenario.get("how"),
        "status": "ready",
    }

    context["scenario"] = scenario
    context["what"] = what
    context["how"] = how
    return context
