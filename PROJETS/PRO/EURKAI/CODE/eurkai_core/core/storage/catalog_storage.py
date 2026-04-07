"""
catalog_storage — accès unifié au catalog.
Interface agnostique : get / get_all / get_all_by_filter.
Les listes sont auto-découvertes depuis les clés catalog_{type}_list.
Ne jamais accéder au catalog directement : toujours passer par ce module.
"""


class CatalogStorage:

    def __init__(self, catalog):
        self._catalog = catalog
        # Auto-découverte : catalog_{type}_list → type_name
        self._lists = {
            k[len("catalog_"):-len("_list")]: k
            for k in catalog
            if k.startswith("catalog_") and k.endswith("_list")
        }

    def get(self, type_name, ident):
        """Retourne un item par type et ident."""
        key = self._lists.get(type_name)
        if key is None:
            return None
        return self._catalog[key].get(ident)

    def get_all(self, type_name):
        """Retourne tous les items d'un type."""
        key = self._lists.get(type_name)
        if key is None:
            return {}
        return self._catalog[key]

    def get_all_by_filter(self, type_name, filter_fn):
        """Retourne les items d'un type filtrés par une fonction."""
        return {k: v for k, v in self.get_all(type_name).items() if filter_fn(v)}

    def list_types(self):
        """Retourne la liste des types disponibles dans ce catalog."""
        return list(self._lists.keys())


def get_storage(catalog):
    return CatalogStorage(catalog)
