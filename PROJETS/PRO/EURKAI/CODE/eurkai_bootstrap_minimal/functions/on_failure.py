from core.hooks.execute_named_hook import execute_named_hook

def on_failure(context, catalog):
    return execute_named_hook("on_failure", context, catalog)
