from core.hooks.execute_named_hook import execute_named_hook

def before(context, catalog):
    return execute_named_hook("before", context, catalog)
