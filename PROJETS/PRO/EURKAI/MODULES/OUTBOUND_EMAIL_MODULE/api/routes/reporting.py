"""Routes: /reporting"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import (
    db_campaign_stats, db_get_campaign, db_get_mailbox,
    db_list_campaigns, db_list_mailboxes, db_mailbox_stats, get_db,
)
from ...models import EurkaiOutput

router = APIRouter(prefix="/reporting", tags=["Reporting"])


@router.get("/campaigns/{campaign_id}", response_model=EurkaiOutput)
def report_campaign(campaign_id: str, db: Session = Depends(get_db)):
    if not db_get_campaign(db, campaign_id):
        raise HTTPException(404, "Campaign not found")
    stats = db_campaign_stats(db, campaign_id)
    return EurkaiOutput(success=True, result=stats, message="OK")


@router.get("/campaigns", response_model=EurkaiOutput)
def report_all_campaigns(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    campaigns = db_list_campaigns(db, project_id=project_id)
    results = []
    for c in campaigns:
        stats = db_campaign_stats(db, c.id)
        results.append({"campaign_id": c.id, "name": c.name, "status": c.status, **stats})
    return EurkaiOutput(success=True, result=results, message="OK")


@router.get("/mailboxes/{mailbox_id}", response_model=EurkaiOutput)
def report_mailbox(mailbox_id: str, window_hours: int = 24, db: Session = Depends(get_db)):
    if not db_get_mailbox(db, mailbox_id):
        raise HTTPException(404, "Mailbox not found")
    stats = db_mailbox_stats(db, mailbox_id, window_hours=window_hours)
    return EurkaiOutput(success=True, result=stats, message="OK")


@router.get("/mailboxes", response_model=EurkaiOutput)
def report_all_mailboxes(domain_id: Optional[str] = None, window_hours: int = 24, db: Session = Depends(get_db)):
    mailboxes = db_list_mailboxes(db, domain_id=domain_id, active_only=False)
    results = []
    for mb in mailboxes:
        stats = db_mailbox_stats(db, mb.id, window_hours=window_hours)
        results.append({
            "mailbox_id": mb.id, "email": mb.email,
            "warmup_status": mb.warmup_status, "reputation_status": mb.reputation_status,
            **stats,
        })
    return EurkaiOutput(success=True, result=results, message="OK")
