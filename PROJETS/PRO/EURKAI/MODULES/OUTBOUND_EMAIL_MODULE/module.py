"""
OUTBOUND_EMAIL_MODULE — Core Engine
Rotation, warmup, compliance, send orchestration.
No hardcoded business data.
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from .database import (
    db_campaign_stats, db_get_campaign, db_get_mailbox, db_get_rotation,
    db_get_warmup, db_increment_sent, db_list_mailboxes, db_list_rules,
    db_mailbox_stats, db_update_campaign, db_update_mailbox,
    db_create_delivery, db_update_delivery, db_prospect_already_contacted,
    db_prospect_replied,
)
from .models import (
    BounceType, CampaignStatus, ComplianceAction, DeliveryStatus,
    EurkaiOutput, ReputationStatus, RotationAlgorithm, SendingMailboxDB,
    WarmupStatus,
)

log = logging.getLogger("oem.engine")


# ── Rotation ───────────────────────────────────────────────────────────────────

def choose_next_mailbox(
    db: Session,
    campaign_id: str,
    domain_id: Optional[str] = None,
) -> Optional[SendingMailboxDB]:
    """
    Select the best mailbox to use next for a given campaign.
    Respects daily/hourly limits, warmup caps, and rotation algorithm.
    Returns None if no eligible mailbox is available.
    """
    campaign = db_get_campaign(db, campaign_id)
    if not campaign:
        log.warning("choose_next_mailbox: campaign %s not found", campaign_id)
        return None

    rotation = db_get_rotation(db, campaign.rotation_strategy_id) if campaign.rotation_strategy_id else None
    algorithm = RotationAlgorithm(rotation.algorithm) if rotation else RotationAlgorithm.round_robin
    per_mailbox_cap = rotation.per_mailbox_daily_cap if rotation else 50

    mailboxes = db_list_mailboxes(db, domain_id=domain_id, active_only=True)
    candidates = []

    for mb in mailboxes:
        # Hard daily limit (per mailbox config)
        if (mb.sent_today or 0) >= mb.daily_limit:
            continue
        # Hard hourly limit
        if (mb.sent_this_hour or 0) >= mb.hourly_limit:
            continue
        # Rotation strategy per-mailbox cap
        if (mb.sent_today or 0) >= per_mailbox_cap:
            continue
        # Skip degraded reputation
        if mb.reputation_status == ReputationStatus.blacklisted:
            continue
        # Warmup cap: if in warmup, check day volume
        if mb.warmup_status == WarmupStatus.in_progress:
            warmup = _get_active_warmup(db, mb)
            if warmup:
                day_cap = _warmup_day_cap(warmup, mb.warmup_day or 0)
                if (mb.sent_today or 0) >= day_cap:
                    continue
        candidates.append(mb)

    if not candidates:
        return None

    if algorithm == RotationAlgorithm.round_robin:
        # Least recently used
        candidates.sort(key=lambda m: m.last_send_at or datetime.min)
        return candidates[0]

    elif algorithm == RotationAlgorithm.weighted:
        # Weight by remaining capacity
        total = sum(mb.daily_limit - (mb.sent_today or 0) for mb in candidates)
        if total == 0:
            return candidates[0]
        r = random.uniform(0, total)
        acc = 0
        for mb in candidates:
            acc += mb.daily_limit - (mb.sent_today or 0)
            if r <= acc:
                return mb
        return candidates[-1]

    elif algorithm == RotationAlgorithm.least_used:
        candidates.sort(key=lambda m: m.sent_today or 0)
        return candidates[0]

    elif algorithm == RotationAlgorithm.random:
        return random.choice(candidates)

    elif algorithm == RotationAlgorithm.health_priority:
        def _health_score(mb: SendingMailboxDB) -> int:
            score = 0
            if mb.reputation_status == ReputationStatus.healthy:
                score += 3
            elif mb.reputation_status == ReputationStatus.unknown:
                score += 1
            if mb.warmup_status == WarmupStatus.completed:
                score += 2
            return score
        candidates.sort(key=_health_score, reverse=True)
        return candidates[0]

    return candidates[0]


def _get_active_warmup(db: Session, mb: SendingMailboxDB):
    """Retrieve warmup strategy linked to a campaign for this mailbox (via convention)."""
    # Warmup is assigned per domain/mailbox via meta["warmup_strategy_id"]
    warmup_id = (mb.meta or {}).get("warmup_strategy_id")
    if warmup_id:
        return db_get_warmup(db, warmup_id)
    return None


def _warmup_day_cap(warmup, day: int) -> int:
    """Return the max volume allowed on a given warmup day."""
    schedule = warmup.ramp_schedule or []
    # Schedule: [{day: 1, volume: 5}, {day: 2, volume: 10}, ...]
    cap = warmup.max_daily_volume
    for entry in schedule:
        if isinstance(entry, dict) and entry.get("day") == day:
            cap = entry.get("volume", cap)
            break
        elif isinstance(entry, dict) and entry.get("day", 0) <= day:
            cap = entry.get("volume", cap)
    return cap


# ── Warmup progression ─────────────────────────────────────────────────────────

def apply_warmup_step(db: Session, mailbox_id: str) -> EurkaiOutput:
    """
    Advance warmup day counter after a successful send.
    Auto-pauses if health rules trigger.
    """
    mb = db_get_mailbox(db, mailbox_id)
    if not mb:
        return EurkaiOutput(success=False, result=None, message="Mailbox not found")
    if mb.warmup_status != WarmupStatus.in_progress:
        return EurkaiOutput(success=True, result=None, message="Not in warmup")

    warmup = _get_active_warmup(db, mb)
    if not warmup:
        return EurkaiOutput(success=True, result=None, message="No warmup strategy linked")

    new_day = (mb.warmup_day or 0) + 1
    schedule_days = [e.get("day", 0) for e in (warmup.ramp_schedule or []) if isinstance(e, dict)]
    max_day = max(schedule_days) if schedule_days else 30

    updates = {"warmup_day": new_day}

    if new_day >= max_day:
        updates["warmup_status"] = WarmupStatus.completed
        log.info("Mailbox %s warmup completed on day %d", mailbox_id, new_day)

    # Auto-pause on high bounce rate
    if warmup.auto_pause_on_issue:
        stats = db_mailbox_stats(db, mailbox_id, window_hours=24)
        health_rules = warmup.health_rules or {}
        bounce_threshold = health_rules.get("max_bounce_rate", 0.05)
        if stats["bounce_rate"] > bounce_threshold:
            updates["warmup_status"] = WarmupStatus.paused
            updates["reputation_status"] = ReputationStatus.at_risk
            log.warning("Mailbox %s warmup paused: bounce_rate=%.2f%%", mailbox_id, stats["bounce_rate"] * 100)

    db_update_mailbox(db, mailbox_id, updates)
    return EurkaiOutput(success=True, result=updates, message="Warmup step applied")


# ── Compliance ─────────────────────────────────────────────────────────────────

def check_compliance(db: Session, mailbox_id: str, campaign_id: str) -> list[dict]:
    """
    Evaluate active compliance rules for a mailbox/campaign.
    Returns list of triggered rules with recommended actions.
    """
    triggered = []
    rules = db_list_rules(db)

    for rule in rules:
        if rule.scope == "mailbox":
            stats = db_mailbox_stats(db, mailbox_id, window_hours=rule.window_hours)
            value = stats.get(rule.rule_type, 0)
        elif rule.scope == "campaign":
            stats = db_campaign_stats(db, campaign_id)
            value = stats.get(rule.rule_type, 0)
        else:
            continue

        if value > rule.threshold:
            triggered.append({
                "rule_id": rule.id,
                "rule_name": rule.name,
                "rule_type": rule.rule_type,
                "value": value,
                "threshold": rule.threshold,
                "action": rule.action_on_trigger,
            })
            log.warning(
                "Compliance rule '%s' triggered: %s=%.4f > %.4f → %s",
                rule.name, rule.rule_type, value, rule.threshold, rule.action_on_trigger,
            )

    return triggered


def enforce_compliance(db: Session, triggered: list[dict], mailbox_id: str, campaign_id: str):
    """Apply compliance actions: pause mailbox, pause domain, stop campaign, alert."""
    for t in triggered:
        action = t["action"]
        if action == ComplianceAction.pause_mailbox:
            db_update_mailbox(db, mailbox_id, {"is_active": False})
        elif action == ComplianceAction.stop_campaign:
            db_update_campaign(db, campaign_id, {"status": CampaignStatus.stopped})
        elif action == ComplianceAction.alert:
            log.error("COMPLIANCE ALERT: %s", t)
        # pause_domain handled upstream if needed


# ── Send batch ─────────────────────────────────────────────────────────────────

def execute_send_batch(
    db: Session,
    campaign_id: str,
    prospect_ids: list[str],
    sequence_step_id: str,
    provider,  # AbstractEmailProvider instance
    scheduled_at: Optional[datetime] = None,
    dry_run: bool = False,
) -> EurkaiOutput:
    """
    Schedule + send emails for a list of prospects.
    - Skips already contacted prospects for this step
    - Skips prospects who replied (if stop_on_reply)
    - Picks best mailbox via choose_next_mailbox()
    - Delegates actual send to provider
    - Updates delivery records
    """
    campaign = db_get_campaign(db, campaign_id)
    if not campaign:
        return EurkaiOutput(success=False, result=None, message=f"Campaign {campaign_id} not found")
    if campaign.status not in (CampaignStatus.active,):
        return EurkaiOutput(success=False, result=None, message=f"Campaign status is {campaign.status}, not active")

    results = {"sent": 0, "skipped": 0, "failed": 0, "deliveries": []}

    for prospect_id in prospect_ids:
        # Skip already sent for this step
        if db_prospect_already_contacted(db, campaign_id, prospect_id, sequence_step_id):
            results["skipped"] += 1
            continue

        # Skip if replied (stop_on_reply check — sequence level)
        if db_prospect_replied(db, campaign_id, prospect_id):
            results["skipped"] += 1
            continue

        # Choose mailbox
        mailbox = choose_next_mailbox(db, campaign_id)
        if not mailbox:
            log.warning("No eligible mailbox for campaign %s", campaign_id)
            results["failed"] += 1
            continue

        # Compliance pre-flight
        triggered = check_compliance(db, mailbox.id, campaign_id)
        if triggered:
            enforce_compliance(db, triggered, mailbox.id, campaign_id)
            blocking = [t for t in triggered if t["action"] != ComplianceAction.alert]
            if blocking:
                results["failed"] += len(prospect_ids) - results["sent"] - results["skipped"] - results["failed"]
                break

        # Create delivery record
        delivery_data = {
            "campaign_id": campaign_id,
            "prospect_id": prospect_id,
            "mailbox_id": mailbox.id,
            "sequence_step_id": sequence_step_id,
            "scheduled_at": scheduled_at or datetime.utcnow(),
            "delivery_status": DeliveryStatus.pending,
        }
        delivery = db_create_delivery(db, delivery_data)

        if dry_run:
            results["sent"] += 1
            results["deliveries"].append({"delivery_id": delivery.id, "mailbox": mailbox.email, "dry_run": True})
            continue

        # Send via provider
        try:
            send_result = provider.send(
                mailbox=mailbox,
                delivery_id=delivery.id,
                prospect_id=prospect_id,
                sequence_step_id=sequence_step_id,
            )
            if send_result.get("success"):
                db_update_delivery(db, delivery.id, {
                    "delivery_status": DeliveryStatus.sent,
                    "sent_at": datetime.utcnow(),
                    "provider_message_id": send_result.get("message_id"),
                })
                db_increment_sent(db, mailbox.id)
                apply_warmup_step(db, mailbox.id)
                results["sent"] += 1
                results["deliveries"].append({"delivery_id": delivery.id, "mailbox": mailbox.email})
            else:
                db_update_delivery(db, delivery.id, {
                    "delivery_status": DeliveryStatus.failed,
                    "error_message": send_result.get("error", "Provider error"),
                })
                results["failed"] += 1
        except Exception as exc:
            log.exception("Send error for prospect %s: %s", prospect_id, exc)
            db_update_delivery(db, delivery.id, {
                "delivery_status": DeliveryStatus.failed,
                "error_message": str(exc),
            })
            results["failed"] += 1

    return EurkaiOutput(
        success=True,
        result=results,
        message=f"Batch done: {results['sent']} sent, {results['skipped']} skipped, {results['failed']} failed",
    )


# ── Bounce / Reply handlers ────────────────────────────────────────────────────

def handle_bounce(db: Session, delivery_id: str, bounce_type: str, error: str = "") -> EurkaiOutput:
    from .database import db_get_delivery
    from .models import BounceType as BT
    delivery = db_get_delivery(db, delivery_id)
    if not delivery:
        return EurkaiOutput(success=False, result=None, message="Delivery not found")

    db_update_delivery(db, delivery_id, {
        "bounce_type": bounce_type,
        "delivery_status": DeliveryStatus.bounced,
        "error_message": error,
    })

    # Hard bounce → flag mailbox reputation
    if bounce_type == BounceType.hard and delivery.mailbox_id:
        stats = db_mailbox_stats(db, delivery.mailbox_id, window_hours=24)
        if stats["bounce_rate"] > 0.10:
            db_update_mailbox(db, delivery.mailbox_id, {
                "reputation_status": ReputationStatus.at_risk,
            })

    return EurkaiOutput(success=True, result={"delivery_id": delivery_id}, message="Bounce recorded")


def handle_reply(db: Session, delivery_id: str, reply_status: str) -> EurkaiOutput:
    from .database import db_get_delivery
    delivery = db_get_delivery(db, delivery_id)
    if not delivery:
        return EurkaiOutput(success=False, result=None, message="Delivery not found")

    db_update_delivery(db, delivery_id, {"reply_status": reply_status})
    return EurkaiOutput(success=True, result={"delivery_id": delivery_id}, message="Reply recorded")


def handle_open(db: Session, delivery_id: str) -> EurkaiOutput:
    db_update_delivery(db, delivery_id, {"opened_at": datetime.utcnow()})
    return EurkaiOutput(success=True, result=None, message="Open recorded")


def handle_click(db: Session, delivery_id: str) -> EurkaiOutput:
    db_update_delivery(db, delivery_id, {"clicked_at": datetime.utcnow()})
    return EurkaiOutput(success=True, result=None, message="Click recorded")
