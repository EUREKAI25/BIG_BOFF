"""Routes: /sequences and /sequences/{id}/steps"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import (
    db_create_sequence, db_create_step, db_get_sequence,
    db_list_sequences, db_list_steps, get_db,
)
from ...models import EurkaiOutput, SequenceCreate, SequenceStepCreate

router = APIRouter(prefix="/sequences", tags=["Sequences"])


@router.post("", response_model=EurkaiOutput)
def create_sequence(payload: SequenceCreate, db: Session = Depends(get_db)):
    obj = db_create_sequence(db, payload.model_dump())
    return EurkaiOutput(success=True, result={"id": obj.id, "name": obj.name, "campaign_id": obj.campaign_id}, message="Sequence created")


@router.get("", response_model=EurkaiOutput)
def list_sequences(campaign_id: str, db: Session = Depends(get_db)):
    rows = db_list_sequences(db, campaign_id)
    return EurkaiOutput(success=True, result=[{"id": r.id, "name": r.name, "stop_on_reply": r.stop_on_reply} for r in rows], message="OK")


@router.get("/{sequence_id}", response_model=EurkaiOutput)
def get_sequence(sequence_id: str, db: Session = Depends(get_db)):
    obj = db_get_sequence(db, sequence_id)
    if not obj:
        raise HTTPException(404, "Sequence not found")
    steps = db_list_steps(db, sequence_id)
    return EurkaiOutput(success=True, result={
        "id": obj.id, "name": obj.name, "campaign_id": obj.campaign_id,
        "stop_on_reply": obj.stop_on_reply,
        "steps": [
            {
                "id": s.id, "step_order": s.step_order,
                "delay_days": s.delay_days, "channel": s.channel,
                "subject_template": s.subject_template,
            }
            for s in steps
        ],
    }, message="OK")


@router.post("/{sequence_id}/steps", response_model=EurkaiOutput)
def add_step(sequence_id: str, payload: SequenceStepCreate, db: Session = Depends(get_db)):
    if not db_get_sequence(db, sequence_id):
        raise HTTPException(404, "Sequence not found")
    data = payload.model_dump()
    data["sequence_id"] = sequence_id
    obj = db_create_step(db, data)
    return EurkaiOutput(success=True, result={"id": obj.id, "step_order": obj.step_order}, message="Step added")


@router.get("/{sequence_id}/steps", response_model=EurkaiOutput)
def list_steps(sequence_id: str, db: Session = Depends(get_db)):
    if not db_get_sequence(db, sequence_id):
        raise HTTPException(404, "Sequence not found")
    steps = db_list_steps(db, sequence_id)
    return EurkaiOutput(success=True, result=[
        {
            "id": s.id, "step_order": s.step_order, "delay_days": s.delay_days,
            "channel": s.channel, "subject_template": s.subject_template,
            "body_template": s.body_template, "trigger_rules": s.trigger_rules,
        }
        for s in steps
    ], message="OK")
