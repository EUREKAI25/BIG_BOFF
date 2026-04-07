"""Routes: /warmup-strategies"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import db_create_warmup, db_get_warmup, db_list_warmups, get_db
from ...models import EurkaiOutput, WarmupStrategyCreate

router = APIRouter(prefix="/warmup-strategies", tags=["Warmup"])


@router.post("", response_model=EurkaiOutput)
def create_warmup(payload: WarmupStrategyCreate, db: Session = Depends(get_db)):
    obj = db_create_warmup(db, payload.model_dump())
    return EurkaiOutput(success=True, result={"id": obj.id, "name": obj.name}, message="Warmup strategy created")


@router.get("", response_model=EurkaiOutput)
def list_warmups(db: Session = Depends(get_db)):
    rows = db_list_warmups(db)
    return EurkaiOutput(success=True, result=[{"id": r.id, "name": r.name, "max_daily_volume": r.max_daily_volume} for r in rows], message="OK")


@router.get("/{warmup_id}", response_model=EurkaiOutput)
def get_warmup(warmup_id: str, db: Session = Depends(get_db)):
    obj = db_get_warmup(db, warmup_id)
    if not obj:
        raise HTTPException(404, "Warmup strategy not found")
    return EurkaiOutput(success=True, result={
        "id": obj.id, "name": obj.name,
        "ramp_schedule": obj.ramp_schedule,
        "max_daily_volume": obj.max_daily_volume,
        "reply_simulation": obj.reply_simulation,
        "auto_pause_on_issue": obj.auto_pause_on_issue,
        "health_rules": obj.health_rules,
    }, message="OK")
