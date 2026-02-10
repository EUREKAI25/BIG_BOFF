from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter()
BASE = Path("EXCHANGE/LIBRARY")

BASE.mkdir(parents=True, exist_ok=True)

def load(name):
    p = BASE / f"{name}.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())

def save(name, data):
    p = BASE / f"{name}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))

@router.post("/api/add-to-list")
async def add_to_list(payload: dict):
    owner, list_id = payload["list"].split(":", 1)
    element = payload["element"]
    obj = load(owner)
    obj.setdefault(list_id, [])
    if element not in obj[list_id]:
        obj[list_id].append(element)
    save(owner, obj)
    return {"ok": True}
