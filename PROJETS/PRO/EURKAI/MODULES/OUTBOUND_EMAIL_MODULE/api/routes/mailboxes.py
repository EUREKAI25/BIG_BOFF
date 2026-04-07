"""Routes: /mailboxes"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import (
    db_create_mailbox, db_get_domain, db_get_mailbox,
    db_list_mailboxes, db_mailbox_stats, db_reset_daily_counters,
    db_update_mailbox, get_db,
)
from ...models import (
    EurkaiOutput, SendingMailboxCreate, SendingMailboxOut,
)

router = APIRouter(prefix="/mailboxes", tags=["Mailboxes"])


@router.post("", response_model=EurkaiOutput)
def create_mailbox(payload: SendingMailboxCreate, db: Session = Depends(get_db)):
    domain = db_get_domain(db, payload.domain_id)
    if not domain:
        raise HTTPException(404, "Domain not found")

    data = payload.model_dump()
    # Build email from local_part + domain name
    data["email"] = f"{payload.local_part}@{domain.name}"
    # Move plaintext password to password_enc (consumer encrypts if needed)
    if "password" in data:
        data["password_enc"] = data.pop("password")
    if "api_key" in data:
        data["api_key_enc"] = data.pop("api_key")

    obj = db_create_mailbox(db, data)
    return EurkaiOutput(success=True, result=SendingMailboxOut.model_validate(obj).model_dump(), message="Mailbox created")


@router.get("", response_model=EurkaiOutput)
def list_mailboxes(domain_id: Optional[str] = None, active_only: bool = False, db: Session = Depends(get_db)):
    rows = db_list_mailboxes(db, domain_id=domain_id, active_only=active_only)
    return EurkaiOutput(success=True, result=[SendingMailboxOut.model_validate(r).model_dump() for r in rows], message="OK")


@router.get("/{mailbox_id}", response_model=EurkaiOutput)
def get_mailbox(mailbox_id: str, db: Session = Depends(get_db)):
    obj = db_get_mailbox(db, mailbox_id)
    if not obj:
        raise HTTPException(404, "Mailbox not found")
    return EurkaiOutput(success=True, result=SendingMailboxOut.model_validate(obj).model_dump(), message="OK")


@router.patch("/{mailbox_id}", response_model=EurkaiOutput)
def update_mailbox(mailbox_id: str, updates: dict, db: Session = Depends(get_db)):
    obj = db_update_mailbox(db, mailbox_id, updates)
    if not obj:
        raise HTTPException(404, "Mailbox not found")
    return EurkaiOutput(success=True, result=SendingMailboxOut.model_validate(obj).model_dump(), message="Updated")


@router.get("/{mailbox_id}/stats", response_model=EurkaiOutput)
def mailbox_stats(mailbox_id: str, window_hours: int = 24, db: Session = Depends(get_db)):
    if not db_get_mailbox(db, mailbox_id):
        raise HTTPException(404, "Mailbox not found")
    stats = db_mailbox_stats(db, mailbox_id, window_hours=window_hours)
    return EurkaiOutput(success=True, result=stats, message="OK")


@router.post("/reset-daily-counters", response_model=EurkaiOutput)
def reset_daily_counters(db: Session = Depends(get_db)):
    """Reset sent_today and sent_this_hour for all mailboxes (run via cron at midnight)."""
    db_reset_daily_counters(db)
    return EurkaiOutput(success=True, result=None, message="Daily counters reset")
