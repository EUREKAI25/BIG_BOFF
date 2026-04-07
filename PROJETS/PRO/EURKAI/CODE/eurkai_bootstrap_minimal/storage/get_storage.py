from config.settings import CATALOG_BACKEND
from storage.catalog_storage import CatalogStorage
from storage.bdd_storage import BddStorage

def get_storage(catalog=None):
    if CATALOG_BACKEND == "json":
        return CatalogStorage(catalog)
    if CATALOG_BACKEND == "bdd":
        return BddStorage(catalog)
    raise ValueError(f"Unknown CATALOG_BACKEND: {CATALOG_BACKEND}")
