"""
function_registry — registre des fonctions disponibles pour la MRG.
Les fonctions sont enregistrées ici, pas dans le catalog.
Pas de FUNCTION_REGISTRY global circulaire : imports locaux uniquement.
"""

_REGISTRY = {}


def register(name):
    """Décorateur d'enregistrement."""
    def decorator(fn):
        _REGISTRY[name] = fn
        return fn
    return decorator


def get_function(name):
    """Retourne la fonction par nom, None si absente."""
    if name not in _REGISTRY:
        _load_defaults()
    return _REGISTRY.get(name)


def _load_defaults():
    """Charge les fonctions par défaut (lazy, évite les imports circulaires)."""
    from core.functions.validate_object_vs_schema import validate_object_vs_schema

    def _validate_wrapper(what, catalog):
        storage      = catalog.get("_storage_ref") if isinstance(catalog, dict) else None
        schema_ident = what.get("object_schema", "ObjectSchema")
        schema       = storage.get("schema", schema_ident) if storage else None
        if schema is None:
            return {"success": False, "error": f"schema_not_found:{schema_ident}"}
        return validate_object_vs_schema(what, schema)

    from core.functions.placeholder_resolve import placeholder_resolve

    from core.functions.prompt_execute    import prompt_execute
    from core.functions.recursive_query   import recursive_query

    _REGISTRY.setdefault("validate_object_vs_schema", _validate_wrapper)
    _REGISTRY.setdefault("placeholder_resolve",        placeholder_resolve)
    _REGISTRY.setdefault("prompt_execute",             prompt_execute)
    _REGISTRY.setdefault("recursive_query",            recursive_query)
    _REGISTRY.setdefault("noop", lambda what, catalog: {"result": "noop", "what": what})
