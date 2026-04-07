"""Routes API — Sections (ordre, activation, bg_color)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db, SectionDB

router = APIRouter(prefix="/sections", tags=["sections"])


class SectionToggle(BaseModel):
    enabled: bool


class SectionUpdate(BaseModel):
    bg_color:    str | None = None
    layout_type: str | None = None
    anchor_id:   str | None = None


class ReorderItem(BaseModel):
    id:          str
    order_index: int


@router.put("/{section_id}/toggle")
def toggle_section(section_id: str, body: SectionToggle, db: Session = Depends(get_db)):
    sec = db.query(SectionDB).filter_by(id=section_id).first()
    if not sec:
        raise HTTPException(404, "Section introuvable")
    sec.enabled = body.enabled
    db.commit()
    return {"ok": True, "enabled": sec.enabled}


@router.put("/{section_id}")
def update_section(section_id: str, body: SectionUpdate, db: Session = Depends(get_db)):
    sec = db.query(SectionDB).filter_by(id=section_id).first()
    if not sec:
        raise HTTPException(404, "Section introuvable")
    if body.bg_color    is not None: sec.bg_color    = body.bg_color or None
    if body.layout_type is not None: sec.layout_type = body.layout_type or None
    if body.anchor_id   is not None: sec.anchor_id   = body.anchor_id or None
    db.commit()
    return {"ok": True}


@router.post("/reorder")
def reorder_sections(items: list[ReorderItem], db: Session = Depends(get_db)):
    for item in items:
        sec = db.query(SectionDB).filter_by(id=item.id).first()
        if sec:
            sec.order_index = item.order_index
    db.commit()
    return {"ok": True}
