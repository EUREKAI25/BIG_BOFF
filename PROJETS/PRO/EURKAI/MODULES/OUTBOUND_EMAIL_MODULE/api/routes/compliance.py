"""Routes: /compliance"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database import db_create_rule, db_list_rules, get_db
from ...models import ComplianceRuleCreate, EurkaiOutput

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post("/rules", response_model=EurkaiOutput)
def create_rule(payload: ComplianceRuleCreate, db: Session = Depends(get_db)):
    obj = db_create_rule(db, payload.model_dump())
    return EurkaiOutput(success=True, result={"id": obj.id, "name": obj.name}, message="Rule created")


@router.get("/rules", response_model=EurkaiOutput)
def list_rules(scope: str = None, db: Session = Depends(get_db)):
    rows = db_list_rules(db, scope=scope)
    return EurkaiOutput(success=True, result=[
        {
            "id": r.id, "name": r.name, "scope": r.scope,
            "rule_type": r.rule_type, "threshold": r.threshold,
            "window_hours": r.window_hours, "action_on_trigger": r.action_on_trigger,
        }
        for r in rows
    ], message="OK")
