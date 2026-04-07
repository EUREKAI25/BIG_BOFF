"""
OUTBOUND_EMAIL_MODULE — Models
SQLAlchemy ORM + Pydantic schemas.
Aucune donnée métier codée en dur.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, field_validator
from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import DeclarativeBase, relationship


def _uid() -> str:
    return str(uuid.uuid4())

def _now() -> datetime:
    return datetime.utcnow()


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────────

class DomainRole(str, Enum):
    sending = "sending"
    landing = "landing"
    mixed   = "mixed"

class DnsStatus(str, Enum):
    unknown   = "unknown"
    valid     = "valid"
    invalid   = "invalid"
    pending   = "pending"

class WarmupStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed   = "completed"
    paused      = "paused"
    failed      = "failed"

class ReputationStatus(str, Enum):
    unknown   = "unknown"
    healthy   = "healthy"
    degraded  = "degraded"
    at_risk   = "at_risk"
    blacklisted = "blacklisted"

class AuthMode(str, Enum):
    plain      = "plain"
    oauth2     = "oauth2"
    api_key    = "api_key"

class RotationAlgorithm(str, Enum):
    round_robin     = "round_robin"
    weighted        = "weighted"
    least_used      = "least_used"
    random          = "random"
    health_priority = "health_priority"

class CampaignStatus(str, Enum):
    draft    = "draft"
    active   = "active"
    paused   = "paused"
    stopped  = "stopped"
    archived = "archived"

class DeliveryStatus(str, Enum):
    pending   = "pending"
    sent      = "sent"
    failed    = "failed"
    bounced   = "bounced"
    deferred  = "deferred"

class ReplyStatus(str, Enum):
    none      = "none"
    positive  = "positive"
    negative  = "negative"
    neutral   = "neutral"
    ooo       = "ooo"

class BounceType(str, Enum):
    none      = "none"
    soft      = "soft"
    hard      = "hard"

class ComplianceScope(str, Enum):
    mailbox  = "mailbox"
    domain   = "domain"
    campaign = "campaign"
    global_  = "global"

class ComplianceAction(str, Enum):
    alert        = "alert"
    pause_mailbox = "pause_mailbox"
    pause_domain  = "pause_domain"
    stop_campaign = "stop_campaign"

class Channel(str, Enum):
    email    = "email"
    sms      = "sms"
    whatsapp = "whatsapp"
    linkedin = "linkedin"


# ── ORM Models ─────────────────────────────────────────────────────────────────

class SendingDomainDB(Base):
    __tablename__ = "sending_domains"

    id                = Column(String, primary_key=True, default=_uid)
    name              = Column(String, nullable=False, unique=True)
    role              = Column(String, default=DomainRole.sending)
    provider          = Column(String, nullable=True)        # brevo, ses, mailgun…
    provider_domain_id = Column(String, nullable=True)
    spf_status        = Column(String, default=DnsStatus.unknown)
    dkim_status       = Column(String, default=DnsStatus.unknown)
    dmarc_status      = Column(String, default=DnsStatus.unknown)
    dns_checked_at    = Column(DateTime, nullable=True)
    warmup_status     = Column(String, default=WarmupStatus.not_started)
    reputation_status = Column(String, default=ReputationStatus.unknown)
    is_active         = Column(Boolean, default=True)
    meta              = Column(JSON, default=dict)
    created_at        = Column(DateTime, default=_now)
    updated_at        = Column(DateTime, default=_now, onupdate=_now)

    mailboxes         = relationship("SendingMailboxDB", back_populates="domain", cascade="all, delete-orphan")


class SendingMailboxDB(Base):
    __tablename__ = "sending_mailboxes"

    id                = Column(String, primary_key=True, default=_uid)
    domain_id         = Column(String, ForeignKey("sending_domains.id"), nullable=False)
    local_part        = Column(String, nullable=False)
    email             = Column(String, nullable=False, unique=True)
    smtp_host         = Column(String, nullable=True)
    smtp_port         = Column(Integer, default=587)
    imap_host         = Column(String, nullable=True)
    imap_port         = Column(Integer, default=993)
    username          = Column(String, nullable=True)
    password_enc      = Column(String, nullable=True)          # chiffré at rest
    auth_mode         = Column(String, default=AuthMode.plain)
    api_key_enc       = Column(String, nullable=True)          # si auth_mode=api_key
    daily_limit       = Column(Integer, default=50)
    hourly_limit      = Column(Integer, default=10)
    sent_today        = Column(Integer, default=0)
    sent_this_hour    = Column(Integer, default=0)
    warmup_status     = Column(String, default=WarmupStatus.not_started)
    warmup_day        = Column(Integer, default=0)
    reputation_status = Column(String, default=ReputationStatus.unknown)
    last_send_at      = Column(DateTime, nullable=True)
    is_active         = Column(Boolean, default=True)
    meta              = Column(JSON, default=dict)
    created_at        = Column(DateTime, default=_now)
    updated_at        = Column(DateTime, default=_now, onupdate=_now)

    domain            = relationship("SendingDomainDB", back_populates="mailboxes")
    deliveries        = relationship("ProspectDeliveryDB", back_populates="mailbox")


class WarmupStrategyDB(Base):
    __tablename__ = "warmup_strategies"

    id                      = Column(String, primary_key=True, default=_uid)
    name                    = Column(String, nullable=False)
    ramp_schedule           = Column(JSON, default=list)   # [{day:1,volume:5},{day:2,volume:10}…]
    max_daily_volume        = Column(Integer, default=50)
    reply_simulation        = Column(Boolean, default=False)
    auto_pause_on_issue     = Column(Boolean, default=True)
    health_rules            = Column(JSON, default=dict)
    meta                    = Column(JSON, default=dict)
    created_at              = Column(DateTime, default=_now)


class RotationStrategyDB(Base):
    __tablename__ = "rotation_strategies"

    id                   = Column(String, primary_key=True, default=_uid)
    name                 = Column(String, nullable=False)
    algorithm            = Column(String, default=RotationAlgorithm.round_robin)
    per_mailbox_daily_cap = Column(Integer, default=50)
    per_domain_daily_cap  = Column(Integer, default=200)
    cooldown_hours        = Column(Integer, default=0)
    failure_rules         = Column(JSON, default=dict)
    meta                  = Column(JSON, default=dict)
    created_at            = Column(DateTime, default=_now)

    campaigns             = relationship("CampaignDB", back_populates="rotation_strategy")


class CampaignDB(Base):
    __tablename__ = "campaigns"

    id                  = Column(String, primary_key=True, default=_uid)
    project_id          = Column(String, nullable=False)       # identifiant projet consommateur
    name                = Column(String, nullable=False)
    channel             = Column(String, default=Channel.email)
    target_segment      = Column(JSON, default=dict)           # filtres prospects
    landing_domain_id   = Column(String, ForeignKey("sending_domains.id"), nullable=True)
    rotation_strategy_id = Column(String, ForeignKey("rotation_strategies.id"), nullable=True)
    status              = Column(String, default=CampaignStatus.draft)
    daily_send_limit    = Column(Integer, default=100)
    track_opens         = Column(Boolean, default=True)
    track_clicks        = Column(Boolean, default=True)
    meta                = Column(JSON, default=dict)
    created_at          = Column(DateTime, default=_now)
    updated_at          = Column(DateTime, default=_now, onupdate=_now)

    landing_domain      = relationship("SendingDomainDB", foreign_keys=[landing_domain_id])
    rotation_strategy   = relationship("RotationStrategyDB", back_populates="campaigns")
    sequences           = relationship("CampaignSequenceDB", back_populates="campaign", cascade="all, delete-orphan")
    deliveries          = relationship("ProspectDeliveryDB", back_populates="campaign")


class CampaignSequenceDB(Base):
    __tablename__ = "campaign_sequences"

    id              = Column(String, primary_key=True, default=_uid)
    campaign_id     = Column(String, ForeignKey("campaigns.id"), nullable=False)
    name            = Column(String, nullable=False)
    stop_on_reply   = Column(Boolean, default=True)
    meta            = Column(JSON, default=dict)
    created_at      = Column(DateTime, default=_now)

    campaign        = relationship("CampaignDB", back_populates="sequences")
    steps           = relationship("CampaignSequenceStepDB", back_populates="sequence",
                                   order_by="CampaignSequenceStepDB.step_order",
                                   cascade="all, delete-orphan")


class CampaignSequenceStepDB(Base):
    __tablename__ = "campaign_sequence_steps"

    id               = Column(String, primary_key=True, default=_uid)
    sequence_id      = Column(String, ForeignKey("campaign_sequences.id"), nullable=False)
    step_order       = Column(Integer, nullable=False)
    delay_days       = Column(Integer, default=0)
    subject_template = Column(Text, nullable=False)
    body_template    = Column(Text, nullable=False)
    channel          = Column(String, default=Channel.email)
    trigger_rules    = Column(JSON, default=dict)
    meta             = Column(JSON, default=dict)
    created_at       = Column(DateTime, default=_now)

    sequence         = relationship("CampaignSequenceDB", back_populates="steps")


class ProspectDeliveryDB(Base):
    __tablename__ = "prospect_deliveries"

    id                  = Column(String, primary_key=True, default=_uid)
    campaign_id         = Column(String, ForeignKey("campaigns.id"), nullable=False)
    prospect_id         = Column(String, nullable=False)        # ID externe (projet consommateur)
    mailbox_id          = Column(String, ForeignKey("sending_mailboxes.id"), nullable=True)
    sequence_step_id    = Column(String, ForeignKey("campaign_sequence_steps.id"), nullable=True)
    scheduled_at        = Column(DateTime, nullable=True)
    sent_at             = Column(DateTime, nullable=True)
    delivery_status     = Column(String, default=DeliveryStatus.pending)
    reply_status        = Column(String, default=ReplyStatus.none)
    bounce_type         = Column(String, default=BounceType.none)
    opened_at           = Column(DateTime, nullable=True)
    clicked_at          = Column(DateTime, nullable=True)
    provider_message_id = Column(String, nullable=True)
    error_message       = Column(Text, nullable=True)
    meta                = Column(JSON, default=dict)
    created_at          = Column(DateTime, default=_now)
    updated_at          = Column(DateTime, default=_now, onupdate=_now)

    campaign            = relationship("CampaignDB", back_populates="deliveries")
    mailbox             = relationship("SendingMailboxDB", back_populates="deliveries")


class ComplianceRuleDB(Base):
    __tablename__ = "compliance_rules"

    id                = Column(String, primary_key=True, default=_uid)
    name              = Column(String, nullable=False)
    scope             = Column(String, default=ComplianceScope.mailbox)
    rule_type         = Column(String, nullable=False)   # bounce_rate, smtp_failure, daily_volume…
    threshold         = Column(Float, nullable=False)
    window_hours      = Column(Integer, default=24)
    action_on_trigger = Column(String, default=ComplianceAction.alert)
    is_active         = Column(Boolean, default=True)
    meta              = Column(JSON, default=dict)
    created_at        = Column(DateTime, default=_now)


# ── Pydantic Schemas ───────────────────────────────────────────────────────────

class SendingDomainCreate(BaseModel):
    name: str
    role: DomainRole = DomainRole.sending
    provider: Optional[str] = None
    provider_domain_id: Optional[str] = None
    meta: dict = {}

class SendingDomainOut(BaseModel):
    id: str
    name: str
    role: str
    provider: Optional[str]
    spf_status: str
    dkim_status: str
    dmarc_status: str
    warmup_status: str
    reputation_status: str
    is_active: bool
    created_at: datetime
    class Config: from_attributes = True


class SendingMailboxCreate(BaseModel):
    domain_id: str
    local_part: str
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    imap_host: Optional[str] = None
    imap_port: int = 993
    username: Optional[str] = None
    password: Optional[str] = None
    auth_mode: AuthMode = AuthMode.plain
    api_key: Optional[str] = None
    daily_limit: int = 50
    hourly_limit: int = 10
    meta: dict = {}

class SendingMailboxOut(BaseModel):
    id: str
    domain_id: str
    email: str
    local_part: str
    daily_limit: int
    hourly_limit: int
    sent_today: int
    warmup_status: str
    warmup_day: int
    reputation_status: str
    is_active: bool
    last_send_at: Optional[datetime]
    created_at: datetime
    class Config: from_attributes = True


class WarmupStrategyCreate(BaseModel):
    name: str
    ramp_schedule: list = []
    max_daily_volume: int = 50
    reply_simulation: bool = False
    auto_pause_on_issue: bool = True
    health_rules: dict = {}
    meta: dict = {}

class RotationStrategyCreate(BaseModel):
    name: str
    algorithm: RotationAlgorithm = RotationAlgorithm.round_robin
    per_mailbox_daily_cap: int = 50
    per_domain_daily_cap: int = 200
    cooldown_hours: int = 0
    failure_rules: dict = {}
    meta: dict = {}

class CampaignCreate(BaseModel):
    project_id: str
    name: str
    channel: Channel = Channel.email
    target_segment: dict = {}
    landing_domain_id: Optional[str] = None
    rotation_strategy_id: Optional[str] = None
    daily_send_limit: int = 100
    track_opens: bool = True
    track_clicks: bool = True
    meta: dict = {}

class CampaignOut(BaseModel):
    id: str
    project_id: str
    name: str
    channel: str
    status: str
    daily_send_limit: int
    created_at: datetime
    class Config: from_attributes = True

class SequenceCreate(BaseModel):
    campaign_id: str
    name: str
    stop_on_reply: bool = True
    meta: dict = {}

class SequenceStepCreate(BaseModel):
    sequence_id: str
    step_order: int
    delay_days: int = 0
    subject_template: str
    body_template: str
    channel: Channel = Channel.email
    trigger_rules: dict = {}
    meta: dict = {}

class DeliveryResultInput(BaseModel):
    delivery_id: str
    status: DeliveryStatus
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None

class BounceInput(BaseModel):
    delivery_id: str
    bounce_type: BounceType
    error_message: Optional[str] = None

class ReplyInput(BaseModel):
    delivery_id: str
    reply_status: ReplyStatus

class ComplianceRuleCreate(BaseModel):
    name: str
    scope: ComplianceScope = ComplianceScope.mailbox
    rule_type: str
    threshold: float
    window_hours: int = 24
    action_on_trigger: ComplianceAction = ComplianceAction.alert
    meta: dict = {}

class ScheduleSendInput(BaseModel):
    campaign_id: str
    prospect_ids: list[str]
    sequence_step_id: str
    scheduled_at: Optional[datetime] = None

class EurkaiOutput(BaseModel):
    success: bool
    result: Any
    message: str
    error: Optional[dict] = None
