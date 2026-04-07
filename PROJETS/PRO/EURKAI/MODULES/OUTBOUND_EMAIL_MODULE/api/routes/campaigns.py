"""Routes: /campaigns"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import (
    db_campaign_stats, db_create_campaign, db_get_campaign,
    db_list_campaigns, db_update_campaign, get_db,
)
from ...models import (
    CampaignCreate, CampaignOut, CampaignStatus, EurkaiOutput,
)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("", response_model=EurkaiOutput)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    obj = db_create_campaign(db, payload.model_dump())
    return EurkaiOutput(success=True, result=CampaignOut.model_validate(obj).model_dump(), message="Campaign created")


@router.get("", response_model=EurkaiOutput)
def list_campaigns(project_id: str = None, db: Session = Depends(get_db)):
    rows = db_list_campaigns(db, project_id=project_id)
    return EurkaiOutput(success=True, result=[CampaignOut.model_validate(r).model_dump() for r in rows], message="OK")


@router.get("/{campaign_id}", response_model=EurkaiOutput)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    obj = db_get_campaign(db, campaign_id)
    if not obj:
        raise HTTPException(404, "Campaign not found")
    return EurkaiOutput(success=True, result=CampaignOut.model_validate(obj).model_dump(), message="OK")


@router.patch("/{campaign_id}", response_model=EurkaiOutput)
def update_campaign(campaign_id: str, updates: dict, db: Session = Depends(get_db)):
    obj = db_update_campaign(db, campaign_id, updates)
    if not obj:
        raise HTTPException(404, "Campaign not found")
    return EurkaiOutput(success=True, result=CampaignOut.model_validate(obj).model_dump(), message="Updated")


@router.post("/{campaign_id}/activate", response_model=EurkaiOutput)
def activate_campaign(campaign_id: str, db: Session = Depends(get_db)):
    obj = db_update_campaign(db, campaign_id, {"status": CampaignStatus.active})
    if not obj:
        raise HTTPException(404, "Campaign not found")
    return EurkaiOutput(success=True, result={"status": obj.status}, message="Campaign activated")


@router.post("/{campaign_id}/pause", response_model=EurkaiOutput)
def pause_campaign(campaign_id: str, db: Session = Depends(get_db)):
    obj = db_update_campaign(db, campaign_id, {"status": CampaignStatus.paused})
    if not obj:
        raise HTTPException(404, "Campaign not found")
    return EurkaiOutput(success=True, result={"status": obj.status}, message="Campaign paused")


@router.post("/{campaign_id}/stop", response_model=EurkaiOutput)
def stop_campaign(campaign_id: str, db: Session = Depends(get_db)):
    obj = db_update_campaign(db, campaign_id, {"status": CampaignStatus.stopped})
    if not obj:
        raise HTTPException(404, "Campaign not found")
    return EurkaiOutput(success=True, result={"status": obj.status}, message="Campaign stopped")


@router.get("/{campaign_id}/stats", response_model=EurkaiOutput)
def campaign_stats(campaign_id: str, db: Session = Depends(get_db)):
    if not db_get_campaign(db, campaign_id):
        raise HTTPException(404, "Campaign not found")
    stats = db_campaign_stats(db, campaign_id)
    return EurkaiOutput(success=True, result=stats, message="OK")
