from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid

from interagents.orchestrator import Orchestrator
from interagents.storage import Storage

router = APIRouter(prefix="/api/interagents", tags=["interagents"])

BASE = Path(__file__).resolve().parents[2]
WORKSPACE = BASE / "EURKAI_COCKPIT" / "workspace"

def get_orchestrator() -> Orchestrator:
    storage = Storage(workspace_dir=str(WORKSPACE))
    return Orchestrator(storage=storage)

@router.get("/health")
def health():
    return {"status": "ok", "workspace": str(WORKSPACE)}

@router.post("/run")
def run(payload: dict):
    prompt = payload.get("prompt") or payload.get("text") or ""
    if not prompt.strip():
        return JSONResponse({"error": "missing_prompt"}, status_code=400)

    orch = get_orchestrator()
    run_id = str(uuid.uuid4())

    if hasattr(orch, "run_text"):
        result = orch.run_text(prompt, run_id=run_id)
    elif hasattr(orch, "run"):
        result = orch.run(prompt, run_id=run_id)
    else:
        orch.storage.save_run({
            "id": run_id,
            "status": "queued",
            "input": {"prompt": prompt}
        })
        result = {"id": run_id, "status": "queued"}

    return {"ok": True, "run_id": run_id, "result": result}

@router.get("/runs")
def list_runs():
    orch = get_orchestrator()
    return {"runs": orch.storage.list_runs()}

@router.get("/runs/{run_id}")
def get_run(run_id: str):
    orch = get_orchestrator()
    data = orch.storage.load_run(run_id)
    if not data:
        return JSONResponse({"error": "not_found"}, status_code=404)
    return data

@router.get("/outputs/{run_id}")
def get_outputs(run_id: str):
    orch = get_orchestrator()
    return {"run_id": run_id, "outputs": orch.storage.load_outputs(run_id)}
