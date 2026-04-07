"""Routes API — Blocks (lecture + édition du seed_json)."""
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db, BlockDB

router = APIRouter(prefix="/blocks", tags=["blocks"])


class SeedUpdate(BaseModel):
    seed: dict   # seed_json complet mis à jour


@router.get("/{block_id}")
def get_block(block_id: str, db: Session = Depends(get_db)):
    blk = db.query(BlockDB).filter_by(id=block_id).first()
    if not blk:
        raise HTTPException(404, "Bloc introuvable")
    return {
        "id":          blk.id,
        "block_type":  blk.block_type,
        "column_span": blk.column_span,
        "structure":   json.loads(blk.structure_json or "{}"),
        "seed":        json.loads(blk.seed_json or "{}"),
        "css_class":   blk.css_class,
        "html_id":     blk.html_id,
    }


@router.put("/{block_id}/seed")
def update_seed(block_id: str, body: SeedUpdate, db: Session = Depends(get_db)):
    blk = db.query(BlockDB).filter_by(id=block_id).first()
    if not blk:
        raise HTTPException(404, "Bloc introuvable")
    blk.seed_json = json.dumps(body.seed, ensure_ascii=False)
    db.commit()
    return {"ok": True}


@router.patch("/{block_id}/seed")
def patch_seed_field(block_id: str, body: dict, db: Session = Depends(get_db)):
    """Met à jour des champs individuels du seed (merge partiel)."""
    blk = db.query(BlockDB).filter_by(id=block_id).first()
    if not blk:
        raise HTTPException(404, "Bloc introuvable")
    seed = json.loads(blk.seed_json or "{}")
    seed.update(body)
    blk.seed_json = json.dumps(seed, ensure_ascii=False)
    db.commit()
    return {"ok": True, "seed": seed}
