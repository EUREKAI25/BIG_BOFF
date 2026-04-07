def filter_has_schema(obj):
    return isinstance(obj, dict) and ("schema" in obj)
