"""Routes: /rotation-strategies"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import db_create_rotation, db_get_rotation, db_list_rotations, get_db
from ...models import EurkaiOutput, RotationStrategyCreate

router = APIRouter(prefix="/rotation-strategies", tags=["Rotation"])


@router.post("", response_model=EurkaiOutput)
def create_rotation(payload: RotationStrategyCreate, db: Session = Depends(get_db)):
    obj = db_create_rotation(db, payload.model_dump())
    return EurkaiOutput(success=True, result={"id": obj.id, "name": obj.name, "algorithm": obj.algorithm}, message="Rotation strategy created")


@router.get("", response_model=EurkaiOutput)
def list_rotations(db: Session = Depends(get_db)):
    rows = db_list_rotations(db)
    return EurkaiOutput(success=True, result=[
        {"id": r.id, "name": r.name, "algorithm": r.algorithm,
         "per_mailbox_daily_cap": r.per_mailbox_daily_cap,
         "per_domain_daily_cap": r.per_domain_daily_cap}
        for r in rows
    ], message="OK")


@router.get("/{rotation_id}", response_model=EurkaiOutput)
def get_rotation(rotation_id: str, db: Session = Depends(get_db)):
    obj = db_get_rotation(db, rotation_id)
    if not obj:
        raise HTTPException(404, "Rotation strategy not found")
    return EurkaiOutput(success=True, result={
        "id": obj.id, "name": obj.name, "algorithm": obj.algorithm,
        "per_mailbox_daily_cap": obj.per_mailbox_daily_cap,
        "per_domain_daily_cap": obj.per_domain_daily_cap,
        "cooldown_hours": obj.cooldown_hours,
        "failure_rules": obj.failure_rules,
    }, message="OK")
