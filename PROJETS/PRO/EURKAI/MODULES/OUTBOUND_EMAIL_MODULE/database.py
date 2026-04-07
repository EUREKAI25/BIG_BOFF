"""
OUTBOUND_EMAIL_MODULE — Database layer
SQLite + SQLAlchemy. Path configurable via OEM_DB_PATH env var.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

from .models import (Base, BounceType, CampaignDB, CampaignSequenceDB,
                     CampaignSequenceStepDB, ComplianceRuleDB,
                     DeliveryStatus, ProspectDeliveryDB, ReputationStatus,
                     RotationStrategyDB, SendingDomainDB, SendingMailboxDB,
                     WarmupStrategyDB, WarmupStatus)

_DB_PATH = os.getenv("OEM_DB_PATH", "outbound_email.db")
_engine  = create_engine(f"sqlite:///{_DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def init_db():
    Base.metadata.create_all(bind=_engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── SendingDomain ──────────────────────────────────────────────────────────────

def db_create_domain(db: Session, data: dict) -> SendingDomainDB:
    obj = SendingDomainDB(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def db_list_domains(db: Session, active_only: bool = False) -> list[SendingDomainDB]:
    q = db.query(SendingDomainDB)
    if active_only:
        q = q.filter_by(is_active=True)
    return q.all()

def db_get_domain(db: Session, domain_id: str) -> Optional[SendingDomainDB]:
    return db.query(SendingDomainDB).filter_by(id=domain_id).first()

def db_get_domain_by_name(db: Session, name: str) -> Optional[SendingDomainDB]:
    return db.query(SendingDomainDB).filter_by(name=name).first()

def db_update_domain(db: Session, domain_id: str, updates: dict) -> Optional[SendingDomainDB]:
    obj = db_get_domain(db, domain_id)
    if not obj: return None
    for k, v in updates.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.utcnow()
    db.commit(); db.refresh(obj)
    return obj


# ── SendingMailbox ─────────────────────────────────────────────────────────────

def db_create_mailbox(db: Session, data: dict) -> SendingMailboxDB:
    obj = SendingMailboxDB(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def db_list_mailboxes(db: Session, domain_id: Optional[str] = None,
                      active_only: bool = False) -> list[SendingMailboxDB]:
    q = db.query(SendingMailboxDB)
    if domain_id:
        q = q.filter_by(domain_id=domain_id)
    if active_only:
        q = q.filter_by(is_active=True)
    return q.all()

def db_get_mailbox(db: Session, mailbox_id: str) -> Optional[SendingMailboxDB]:
    return db.query(SendingMailboxDB).filter_by(id=mailbox_id).first()

def db_update_mailbox(db: Session, mailbox_id: str, updates: dict) -> Optional[SendingMailboxDB]:
    obj = db_get_mailbox(db, mailbox_id)
    if not obj: return None
    for k, v in updates.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.utcnow()
    db.commit(); db.refresh(obj)
    return obj

def db_increment_sent(db: Session, mailbox_id: str):
    obj = db_get_mailbox(db, mailbox_id)
    if obj:
        obj.sent_today      = (obj.sent_today or 0) + 1
        obj.sent_this_hour  = (obj.sent_this_hour or 0) + 1
        obj.last_send_at    = datetime.utcnow()
        db.commit()

def db_reset_daily_counters(db: Session):
    db.query(SendingMailboxDB).update({"sent_today": 0, "sent_this_hour": 0})
    db.commit()


# ── WarmupStrategy ─────────────────────────────────────────────────────────────

def db_create_warmup(db: Session, data: dict) -> WarmupStrategyDB:
    obj = WarmupStrategyDB(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def db_list_warmups(db: Session) -> list[WarmupStrategyDB]:
    return db.query(WarmupStrategyDB).all()

def db_get_warmup(db: Session, warmup_id: str) -> Optional[WarmupStrategyDB]:
    return db.query(WarmupStrategyDB).filter_by(id=warmup_id).first()


# ── RotationStrategy ───────────────────────────────────────────────────────────

def db_create_rotation(db: Session, data: dict) -> RotationStrategyDB:
    obj = RotationStrategyDB(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def db_list_rotations(db: Session) -> list[RotationStrategyDB]:
    return db.query(RotationStrategyDB).all()

def db_get_rotation(db: Session, rotation_id: str) -> Optional[RotationStrategyDB]:
    return db.query(RotationStrategyDB).filter_by(id=rotation_id).first()


# ── Campaign ───────────────────────────────────────────────────────────────────

def db_create_campaign(db: Session, data: dict) -> CampaignDB:
    obj = CampaignDB(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def db_list_campaigns(db: Session, project_id: Optional[str] = None) -> list[CampaignDB]:
    q = db.query(CampaignDB)
    if project_id:
        q = q.filter_by(project_id=project_id)
    return q.all()

def db_get_campaign(db: Session, campaign_id: str) -> Optional[CampaignDB]:
    return db.query(CampaignDB).filter_by(id=campaign_id).first()

def db_update_campaign(db: Session, campaign_id: str, updates: dict) -> Optional[CampaignDB]:
    obj = db_get_campaign(db, campaign_id)
    if not obj: return None
    for k, v in updates.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.utcnow()
    db.commit(); db.refresh(obj)
    return obj


# ── Sequence ───────────────────────────────────────────────────────────────────

def db_create_sequence(db: Session, data: dict) -> CampaignSequenceDB:
    obj = CampaignSequenceDB(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def db_list_sequences(db: Session, campaign_id: str) -> list[CampaignSequenceDB]:
    return db.query(CampaignSequenceDB).filter_by(campaign_id=campaign_id).all()

def db_get_sequence(db: Session, sequence_id: str) -> Optional[CampaignSequenceDB]:
    return db.query(CampaignSequenceDB).filter_by(id=sequence_id).first()

def db_create_step(db: Session, data: dict) -> CampaignSequenceStepDB:
    obj = CampaignSequenceStepDB(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def db_list_steps(db: Session, sequence_id: str) -> list[CampaignSequenceStepDB]:
    return (db.query(CampaignSequenceStepDB)
            .filter_by(sequence_id=sequence_id)
            .order_by(CampaignSequenceStepDB.step_order)
            .all())


# ── ProspectDelivery ───────────────────────────────────────────────────────────

def db_create_delivery(db: Session, data: dict) -> ProspectDeliveryDB:
    obj = ProspectDeliveryDB(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def db_get_delivery(db: Session, delivery_id: str) -> Optional[ProspectDeliveryDB]:
    return db.query(ProspectDeliveryDB).filter_by(id=delivery_id).first()

def db_update_delivery(db: Session, delivery_id: str, updates: dict) -> Optional[ProspectDeliveryDB]:
    obj = db_get_delivery(db, delivery_id)
    if not obj: return None
    for k, v in updates.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.utcnow()
    db.commit(); db.refresh(obj)
    return obj

def db_prospect_already_contacted(db: Session, campaign_id: str, prospect_id: str,
                                   sequence_step_id: str) -> bool:
    return db.query(ProspectDeliveryDB).filter_by(
        campaign_id=campaign_id,
        prospect_id=prospect_id,
        sequence_step_id=sequence_step_id,
    ).first() is not None

def db_prospect_replied(db: Session, campaign_id: str, prospect_id: str) -> bool:
    from .models import ReplyStatus
    return db.query(ProspectDeliveryDB).filter(
        ProspectDeliveryDB.campaign_id == campaign_id,
        ProspectDeliveryDB.prospect_id == prospect_id,
        ProspectDeliveryDB.reply_status != ReplyStatus.none,
    ).first() is not None


# ── ComplianceRule ─────────────────────────────────────────────────────────────

def db_create_rule(db: Session, data: dict) -> ComplianceRuleDB:
    obj = ComplianceRuleDB(**data)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def db_list_rules(db: Session, scope: Optional[str] = None) -> list[ComplianceRuleDB]:
    q = db.query(ComplianceRuleDB).filter_by(is_active=True)
    if scope:
        q = q.filter_by(scope=scope)
    return q.all()


# ── Stats helpers ──────────────────────────────────────────────────────────────

def db_campaign_stats(db: Session, campaign_id: str) -> dict:
    rows = db.query(ProspectDeliveryDB).filter_by(campaign_id=campaign_id).all()
    total   = len(rows)
    sent    = sum(1 for r in rows if r.delivery_status == DeliveryStatus.sent)
    bounced = sum(1 for r in rows if r.bounce_type != BounceType.none)
    opened  = sum(1 for r in rows if r.opened_at)
    clicked = sum(1 for r in rows if r.clicked_at)
    from .models import ReplyStatus
    replied = sum(1 for r in rows if r.reply_status != ReplyStatus.none)
    return {
        "total": total, "sent": sent, "bounced": bounced,
        "opened": opened, "clicked": clicked, "replied": replied,
        "bounce_rate": round(bounced / sent, 4) if sent else 0,
        "open_rate":   round(opened  / sent, 4) if sent else 0,
        "reply_rate":  round(replied / sent, 4) if sent else 0,
    }

def db_mailbox_stats(db: Session, mailbox_id: str, window_hours: int = 24) -> dict:
    since = datetime.utcnow() - timedelta(hours=window_hours)
    rows  = db.query(ProspectDeliveryDB).filter(
        ProspectDeliveryDB.mailbox_id == mailbox_id,
        ProspectDeliveryDB.sent_at >= since,
    ).all()
    total   = len(rows)
    bounced = sum(1 for r in rows if r.bounce_type != BounceType.none)
    failed  = sum(1 for r in rows if r.delivery_status == DeliveryStatus.failed)
    return {
        "sent": total, "bounced": bounced, "failed": failed,
        "bounce_rate": round(bounced / total, 4) if total else 0,
        "failure_rate": round(failed / total, 4) if total else 0,
    }
