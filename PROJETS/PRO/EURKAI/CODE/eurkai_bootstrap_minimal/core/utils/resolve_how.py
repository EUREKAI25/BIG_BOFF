def resolve_how(scenario, what, catalog):
    from core.registry.function_registry import FUNCTION_REGISTRY

    how_ident = scenario.get("how")
    how_fn = FUNCTION_REGISTRY.get(how_ident)

    if how_fn is None:
        raise ValueError(f"Unknown how function: {how_ident}")

    return how_fn
