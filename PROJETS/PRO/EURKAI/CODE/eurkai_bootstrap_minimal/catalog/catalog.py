import json
from pathlib import Path
from config.settings import CATALOG_PATH

def load_catalog():
    path = Path(CATALOG_PATH)
    return json.loads(path.read_text(encoding="utf-8"))
