"""
load_catalog — charge catalog_core.json et injecte le storage.
Point d'entrée unique pour accéder au catalog.
"""

import json
from pathlib import Path
from core.storage.catalog_storage import get_storage

CATALOG_PATH = Path(__file__).parent / "catalog_core.json"


def load_catalog():
    with open(CATALOG_PATH) as f:
        catalog = json.load(f)
    catalog["_storage"] = get_storage(catalog)
    return catalog
