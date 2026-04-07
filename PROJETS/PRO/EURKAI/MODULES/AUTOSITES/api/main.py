"""
AUTOSITES Admin — FastAPI app.

Démarrage :
    uvicorn api.main:app --reload --port 8010

Accès admin :
    http://localhost:8010/admin
"""
import json
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

HERE        = Path(__file__).parent
MODULES_DIR = HERE.parent.parent  # EURKAI/MODULES/
MANIFESTS   = HERE.parent / "manifests"
OUTPUT_DIR  = HERE.parent / "output"

# page_builder sur le path
sys.path.insert(0, str(MODULES_DIR / "page_builder"))
sys.path.insert(0, str(MODULES_DIR / "theme_generator"))

from .database import init_db, import_manifest_json, SessionLocal
from .routes   import pages, sections, blocks, generate, admin_ui

app = FastAPI(title="AUTOSITES Admin", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup():
    init_db()
    _seed_from_manifests()


def _seed_from_manifests():
    """
    Au démarrage : importe tous les manifests JSON du dossier manifests/
    qui n'ont pas encore de page correspondante en DB.
    Projet slug = nom du dossier parent (ici 'autosites').
    """
    if not MANIFESTS.exists():
        return
    db = SessionLocal()
    try:
        for manifest_path in sorted(MANIFESTS.glob("*.json")):
            try:
                import_manifest_json(db, "autosites", "AUTOSITES", manifest_path)
                print(f"[seed] importé : {manifest_path.name}")
            except Exception as e:
                print(f"[seed] erreur {manifest_path.name} : {e}")
    finally:
        db.close()


# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(admin_ui.router)   # HTML admin
app.include_router(pages.router,    prefix="/api")
app.include_router(sections.router, prefix="/api")
app.include_router(blocks.router,   prefix="/api")
app.include_router(generate.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "autosites"}
