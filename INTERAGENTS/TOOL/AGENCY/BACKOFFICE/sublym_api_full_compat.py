from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter()
BASE = Path("EXCHANGE/LIBRARY")

def load(name):
    p = BASE / f"{name}.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())

def save(name, data):
    p = BASE / f"{name}.json"
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

@router.post("/api/remove-from-list")
async def remove_from_list(payload: dict):
    owner, list_id = payload["list"].split(":", 1)
    element = payload["element"]
    obj = load(owner)
    if list_id in obj and element in obj[list_id]:
        obj[list_id].remove(element)
    save(owner, obj)
    return {"ok": True}

@router.get("/api/schemas")
async def list_schemas():
    p = BASE / "RULES/SCHEMAS"
    p.mkdir(parents=True, exist_ok=True)
    return {"schemas":[f.stem for f in p.glob("*.json")]}

@router.get("/api/schemas/{name}")
async def get_schema(name: str):
    p = BASE / "RULES/SCHEMAS" / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else {}

@router.put("/api/schemas/{name}")
async def save_schema(name: str, payload: dict):
    p = BASE / "RULES/SCHEMAS"
    p.mkdir(parents=True, exist_ok=True)
    (p / f"{name}.json").write_text(json.dumps(payload, indent=2))
    return {"ok": True}

@router.post("/api/console")
async def console(payload: dict):
    return {"ok": True}
