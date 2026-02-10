#!/usr/bin/env bash
set -e

ROOT="/Users/nathalie/Dropbox/____BIG_BOFF___/INTERAGENTS/TOOL"
ENGINE="$ROOT/INTERAGENTS_ENGINE"
API="$ROOT/AGENCY/BACKOFFICE/sublym_api_compat.py"
APP="$ROOT/AGENCY/BACKOFFICE/backoffice_app.py"

echo "=== [1] PATCH API COMPAT SUBLYM ==="

cat > "$API" <<'PY'
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/tree")
async def tree():
    return {
        "root": "LIBRARY",
        "nodes": [],
        "base_path": "LIBRARY"
    }

@router.get("/api/object/{oid}")
async def get_object(oid: str):
    return {
        "oid": oid,
        "memberships": {
            "ObjectElementList": []
        },
        "declarations": {},
        "attributes": {},
        "instances": []
    }

@router.post("/api/create")
async def create(payload: dict):
    return {
        "ok": True,
        "created": payload
    }

@router.post("/api/delete")
async def delete(payload: dict):
    return {"ok": True}

@router.post("/api/console")
async def console(payload: dict):
    return {"ok": True}

@router.put("/api/schemas/{name}")
async def save_schema(name: str, payload: dict):
    return {"ok": True}
PY

echo "OK: API compat écrite"

echo
echo "=== [2] PATCH BACKOFFICE (router include) ==="

python <<'PY'
from pathlib import Path

p = Path("AGENCY/BACKOFFICE/backoffice_app.py")
s = p.read_text(encoding="utf-8")

marker = "sublym_api_compat"

if marker not in s:
    s += "\nfrom AGENCY.BACKOFFICE.sublym_api_compat import router as sublym_router\n"
    s += "app.include_router(sublym_router)\n"
    p.write_text(s, encoding="utf-8")
    print("OK: router SUBLYM branché")
else:
    print("OK: router déjà présent")
PY

echo
echo "=== [3] RESTART SERVER ==="

pkill -f "uvicorn.*8899" >/dev/null 2>&1 || true

cd "$ENGINE"
source .venv/bin/activate

uvicorn "AGENCY.BACKOFFICE.backoffice_app:app" \
  --app-dir "$ROOT" \
  --reload \
  --port 8899
