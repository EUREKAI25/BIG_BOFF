"""Payment API routes (Stripe integration)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import stripe
import os

from ...database.session import get_db
from ...database.models import Payment as PaymentModel, Audit as AuditModel
from ...services.audit_service import AuditService
from ..schemas import PaymentCreateRequest, PaymentCreateResponse

router = APIRouter()

# Initialize Stripe (in production, get from settings)
stripe.api_key = os.getenv("STRIPE_API_KEY", "")


@router.post("/create-checkout", response_model=PaymentCreateResponse)
async def create_checkout_session(
    request: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create Stripe Checkout session for audit payment.

    Returns checkout URL to redirect user to Stripe.
    """
    from uuid import UUID

    try:
        # Verify audit exists
        audit = await AuditService.get_audit(db, UUID(request.audit_id))
        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")

        # Check if already paid
        if audit.plan in ["starter", "pro"] and audit.status == "completed":
            # Already paid, don't charge again
            raise HTTPException(status_code=400, detail="Audit already paid")

        # Determine price based on plan
        prices = {
            "starter": 4900,  # 49 EUR in cents
            "pro": 14900,     # 149 EUR in cents
        }
        amount = prices.get(request.plan)

        if not amount:
            raise HTTPException(status_code=400, detail="Invalid plan")

        # For MVP, skip actual Stripe integration
        # In production, create real Stripe session:
        # session = stripe.checkout.Session.create(...)

        # Mock checkout session
        mock_session_id = f"cs_test_{request.audit_id[:8]}"
        mock_checkout_url = f"https://checkout.stripe.com/pay/{mock_session_id}"

        # Create payment record
        payment = PaymentModel(
            user_id=audit.user_id,
            audit_id=audit.id,
            stripe_checkout_id=mock_session_id,
            plan=request.plan,
            amount=amount,
            status="pending",
        )
        db.add(payment)
        await db.commit()

        return PaymentCreateResponse(
            checkout_url=mock_checkout_url,
            session_id=mock_session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Stripe webhook events.

    Validates webhook signature and processes events.
    """
    # Get raw body for signature verification
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        # In production, verify signature:
        # event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

        # For MVP, parse payload directly
        import json
        event_dict = json.loads(payload)
        event_type = event_dict.get("type")

        if event_type == "checkout.session.completed":
            session = event_dict.get("data", {}).get("object", {})
            session_id = session.get("id")

            # Find payment by session ID
            from sqlalchemy import select
            result = await db.execute(
                select(PaymentModel).where(
                    PaymentModel.stripe_checkout_id == session_id
                )
            )
            payment = result.scalar_one_or_none()

            if payment:
                # Update payment status
                payment.status = "completed"
                from datetime import datetime
                payment.paid_at = datetime.utcnow()

                # Update audit to paid plan
                audit = await AuditService.get_audit(db, payment.audit_id)
                if audit:
                    audit.plan = payment.plan

                await db.commit()

        elif event_type == "charge.refunded":
            # Handle refund
            charge = event_dict.get("data", {}).get("object", {})
            # Find and update payment...
            pass

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
