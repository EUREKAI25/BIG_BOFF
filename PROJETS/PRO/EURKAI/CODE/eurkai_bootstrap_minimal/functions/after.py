from core.hooks.execute_named_hook import execute_named_hook

def after(context, catalog):
    return execute_named_hook("after", context, catalog)
