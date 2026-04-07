"""Routes API — Génération HTML depuis DB."""
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db, PageDB, build_manifest_dict

HERE       = Path(__file__).parent.parent.parent  # AUTOSITES/
OUTPUT_DIR = HERE / "output"

router = APIRouter(prefix="/generate", tags=["generate"])


def _render_page_from_db(db: Session, page_id: str) -> str:
    from src.manifest.schema import ManifestPage
    from src.manifest.parser import parse_manifest
    from src.renderer.html   import render_page

    manifest_dict = build_manifest_dict(db, page_id)
    manifest      = ManifestPage(**manifest_dict)
    page          = parse_manifest(manifest)
    return render_page(page)


@router.post("/pages/{page_id}")
def generate_page(page_id: str, db: Session = Depends(get_db)):
    """Génère index.html dans output/<slug>/ depuis la DB."""
    page = db.query(PageDB).filter_by(id=page_id).first()
    if not page:
        raise HTTPException(404, "Page introuvable")

    try:
        html = _render_page_from_db(db, page_id)
    except Exception as e:
        raise HTTPException(500, f"Erreur de génération : {e}")

    out_dir  = OUTPUT_DIR / page.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(html, encoding="utf-8")

    return {
        "ok":       True,
        "file":     str(out_file),
        "size_kb":  round(out_file.stat().st_size / 1024, 1),
    }


@router.get("/pages/{page_id}/preview", response_class=HTMLResponse)
def preview_page(page_id: str, db: Session = Depends(get_db)):
    """Prévisualise une page sans écrire de fichier."""
    try:
        return _render_page_from_db(db, page_id)
    except Exception as e:
        raise HTTPException(500, str(e))
