"""Routes API — Pages."""
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db, PageDB, ProjectDB

router = APIRouter(prefix="/pages", tags=["pages"])


class PageUpdate(BaseModel):
    title:               str | None = None
    description:         str | None = None
    placeholder_context: dict | None = None
    enabled:             bool | None = None


@router.get("/")
def list_pages(db: Session = Depends(get_db)):
    pages = db.query(PageDB).all()
    return [
        {
            "id":        p.id,
            "slug":      p.slug,
            "page_type": p.page_type,
            "title":     p.title,
            "enabled":   p.enabled,
            "project":   p.project.name if p.project else None,
            "sections_count": len(p.sections),
        }
        for p in pages
    ]


@router.get("/{page_id}")
def get_page(page_id: str, db: Session = Depends(get_db)):
    page = db.query(PageDB).filter_by(id=page_id).first()
    if not page:
        raise HTTPException(404, "Page introuvable")
    return {
        "id":                   page.id,
        "slug":                 page.slug,
        "page_type":            page.page_type,
        "lang":                 page.lang,
        "title":                page.title,
        "description":          page.description,
        "placeholder_context":  json.loads(page.placeholder_context or "{}"),
        "enabled":              page.enabled,
        "sections": [
            {
                "id":          s.id,
                "key":         s.key,
                "order_index": s.order_index,
                "enabled":     s.enabled,
                "bg_color":    s.bg_color,
                "blocks":      [{"id": b.id, "block_type": b.block_type} for b in s.blocks],
            }
            for s in page.sections
        ],
    }


@router.put("/{page_id}")
def update_page(page_id: str, body: PageUpdate, db: Session = Depends(get_db)):
    page = db.query(PageDB).filter_by(id=page_id).first()
    if not page:
        raise HTTPException(404, "Page introuvable")
    if body.title               is not None: page.title = body.title
    if body.description         is not None: page.description = body.description
    if body.enabled             is not None: page.enabled = body.enabled
    if body.placeholder_context is not None:
        page.placeholder_context = json.dumps(body.placeholder_context)
    db.commit()
    return {"ok": True}
