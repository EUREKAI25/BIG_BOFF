from core.hooks.execute_named_hook import execute_named_hook

def get(context, catalog):
    return execute_named_hook("get", context, catalog)
