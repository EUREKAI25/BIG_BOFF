"""Routes: /domains"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import (
    db_create_domain, db_get_domain, db_get_domain_by_name,
    db_list_domains, db_update_domain, get_db,
)
from ...models import EurkaiOutput, SendingDomainCreate, SendingDomainOut

router = APIRouter(prefix="/domains", tags=["Domains"])


@router.post("", response_model=EurkaiOutput)
def create_domain(payload: SendingDomainCreate, db: Session = Depends(get_db)):
    if db_get_domain_by_name(db, payload.name):
        raise HTTPException(409, f"Domain {payload.name} already exists")
    obj = db_create_domain(db, payload.model_dump())
    return EurkaiOutput(success=True, result=SendingDomainOut.model_validate(obj).model_dump(), message="Domain created")


@router.get("", response_model=EurkaiOutput)
def list_domains(active_only: bool = False, db: Session = Depends(get_db)):
    rows = db_list_domains(db, active_only=active_only)
    return EurkaiOutput(success=True, result=[SendingDomainOut.model_validate(r).model_dump() for r in rows], message="OK")


@router.get("/{domain_id}", response_model=EurkaiOutput)
def get_domain(domain_id: str, db: Session = Depends(get_db)):
    obj = db_get_domain(db, domain_id)
    if not obj:
        raise HTTPException(404, "Domain not found")
    return EurkaiOutput(success=True, result=SendingDomainOut.model_validate(obj).model_dump(), message="OK")


@router.patch("/{domain_id}", response_model=EurkaiOutput)
def update_domain(domain_id: str, updates: dict, db: Session = Depends(get_db)):
    obj = db_update_domain(db, domain_id, updates)
    if not obj:
        raise HTTPException(404, "Domain not found")
    return EurkaiOutput(success=True, result=SendingDomainOut.model_validate(obj).model_dump(), message="Updated")


@router.post("/{domain_id}/validate", response_model=EurkaiOutput)
def validate_domain(domain_id: str, db: Session = Depends(get_db)):
    """Trigger DNS verification via configured provider."""
    from ...database import db_get_domain
    from ...providers.brevo import BrevoProvider
    obj = db_get_domain(db, domain_id)
    if not obj:
        raise HTTPException(404, "Domain not found")
    try:
        provider = BrevoProvider()
        result = provider.validate_domain(obj.name)
        if result.get("success"):
            db_update_domain(db, domain_id, {
                "spf_status": result["spf"],
                "dkim_status": result["dkim"],
                "dmarc_status": result["dmarc"],
            })
        return EurkaiOutput(success=result.get("success", False), result=result, message="Validation done")
    except Exception as e:
        raise HTTPException(500, str(e))
