"""Routes: /send — batch send, webhooks (bounce/reply/open/click)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import (
    BounceInput, DeliveryResultInput, EurkaiOutput,
    ReplyInput, ScheduleSendInput,
)
from ...module import (
    execute_send_batch, handle_bounce, handle_click, handle_open, handle_reply,
)

router = APIRouter(prefix="/send", tags=["Send"])


def _get_provider():
    """Instantiate provider from env. Override this for other providers."""
    import os
    from ...providers.brevo import BrevoProvider
    return BrevoProvider(api_key=os.getenv("BREVO_API_KEY"))


@router.post("/batch", response_model=EurkaiOutput)
def send_batch(payload: ScheduleSendInput, dry_run: bool = False, db: Session = Depends(get_db)):
    """
    Schedule and send emails for a list of prospects.
    The caller is responsible for providing rendered subject/body via the provider's
    send() method (extend BrevoProvider or implement custom AbstractEmailProvider).

    dry_run=True creates delivery records but does not send.
    """
    try:
        provider = _get_provider()
    except Exception as e:
        raise HTTPException(500, f"Provider init failed: {e}")

    result = execute_send_batch(
        db=db,
        campaign_id=payload.campaign_id,
        prospect_ids=payload.prospect_ids,
        sequence_step_id=payload.sequence_step_id,
        provider=provider,
        scheduled_at=payload.scheduled_at,
        dry_run=dry_run,
    )
    return result


@router.post("/webhook/delivery", response_model=EurkaiOutput)
def webhook_delivery(payload: DeliveryResultInput, db: Session = Depends(get_db)):
    """Update delivery status from provider webhook."""
    from ...database import db_update_delivery
    from ...models import DeliveryStatus
    updates = {
        "delivery_status": payload.status,
        "provider_message_id": payload.provider_message_id,
        "error_message": payload.error_message,
    }
    if payload.status == DeliveryStatus.sent:
        from datetime import datetime
        updates["sent_at"] = datetime.utcnow()
    obj = db_update_delivery(db, payload.delivery_id, updates)
    if not obj:
        raise HTTPException(404, "Delivery not found")
    return EurkaiOutput(success=True, result={"delivery_id": payload.delivery_id}, message="Delivery updated")


@router.post("/webhook/bounce", response_model=EurkaiOutput)
def webhook_bounce(payload: BounceInput, db: Session = Depends(get_db)):
    return handle_bounce(db, payload.delivery_id, payload.bounce_type, payload.error_message or "")


@router.post("/webhook/reply", response_model=EurkaiOutput)
def webhook_reply(payload: ReplyInput, db: Session = Depends(get_db)):
    return handle_reply(db, payload.delivery_id, payload.reply_status)


@router.get("/webhook/open/{delivery_id}", response_model=EurkaiOutput)
def webhook_open(delivery_id: str, db: Session = Depends(get_db)):
    return handle_open(db, delivery_id)


@router.get("/webhook/click/{delivery_id}", response_model=EurkaiOutput)
def webhook_click(delivery_id: str, db: Session = Depends(get_db)):
    return handle_click(db, delivery_id)
