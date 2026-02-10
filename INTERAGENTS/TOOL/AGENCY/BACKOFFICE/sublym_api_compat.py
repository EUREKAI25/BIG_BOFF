from fastapi import APIRouter

router = APIRouter()

DATA = {
    "memberships": {},
    "declarations": {},
    "attributes": {},
}

@router.get("/api/tree")
async def tree():
    return {"root":"LIBRARY","nodes":[],"base_path":"LIBRARY"}

@router.get("/api/object/{oid}")
async def get_object(oid: str):
    return {
        "memberships": DATA.get("memberships", {}),
        "declarations": DATA.get("declarations", {}),
        "attributes": DATA.get("attributes", {}),
        "instances": [],
        "ObjectElementList": DATA.get("memberships", {}).get(oid, [])
    }

@router.post("/api/create")
async def create(payload: dict):
    name = payload.get("name","Object")
    DATA["memberships"].setdefault(name, [])
    return {"ok": True, "name": name}

@router.post("/api/delete")
async def delete(payload: dict):
    return {"ok": True}
