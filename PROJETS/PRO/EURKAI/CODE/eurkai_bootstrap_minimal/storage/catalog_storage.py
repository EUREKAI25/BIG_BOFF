from core.registry.function_registry import FUNCTION_REGISTRY

class CatalogStorage:
    def __init__(self, catalog):
        self.catalog = catalog

    def get_scenario(self, ident):
        return self.catalog["scenario_list"].get(ident)

    def get_schema(self, ident):
        return self.catalog["schema_list"].get(ident)

    def get_filter(self, ident):
        entry = self.catalog["filter_list"].get(ident)
        if not entry:
            return None
        return FUNCTION_REGISTRY.get(entry["function"])

    def get_function(self, ident):
        entry = self.catalog["function_list"].get(ident)
        if not entry:
            return None
        return FUNCTION_REGISTRY.get(entry["function"])

    def get_first_object_by_filter(self, filter_name):
        filter_fn = self.get_filter(filter_name)
        if filter_fn is None:
            raise ValueError(f"Unknown filter: {filter_name}")
        for obj in self.catalog["object_list"].values():
            if filter_fn(obj):
                return obj
        return None
