from storage.get_storage import get_storage

def execute_named_hook(hook_name, context, catalog):
    scenario = context.get("scenario")
    if scenario is None:
        return context

    hook_ident = scenario.get("hooks", {}).get(hook_name)
    if not hook_ident:
        return context

    storage = get_storage(catalog)
    hook_fn = storage.get_function(hook_ident)
    if hook_fn is None:
        raise ValueError(f"Unknown {hook_name} hook: {hook_ident}")

    result = hook_fn(context=context, catalog=catalog)
    return context if result is None else result
