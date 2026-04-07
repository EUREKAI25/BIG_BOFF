from core.hooks.execute_named_hook import execute_named_hook

def validate(context, catalog):
    return execute_named_hook("validate", context, catalog)
