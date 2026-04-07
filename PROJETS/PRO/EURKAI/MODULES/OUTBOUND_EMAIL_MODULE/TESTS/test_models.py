"""Tests: ORM models + Pydantic schemas"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from outbound_email_module.models import (
    Base, BounceType, CampaignStatus, Channel, DeliveryStatus,
    DomainRole, DnsStatus, ReplyStatus, ReputationStatus,
    RotationAlgorithm, WarmupStatus,
    SendingDomainCreate, SendingMailboxCreate, CampaignCreate,
)
from outbound_email_module.database import (
    db_create_domain, db_create_mailbox, db_create_campaign,
    db_get_domain, db_get_mailbox, db_get_campaign,
    db_list_domains, db_update_domain,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_domain(db):
    data = {"name": "test.example.com", "role": DomainRole.sending, "provider": "brevo"}
    obj = db_create_domain(db, data)
    assert obj.id
    assert obj.name == "test.example.com"
    assert obj.spf_status == DnsStatus.unknown
    assert obj.is_active is True


def test_create_mailbox(db):
    dom = db_create_domain(db, {"name": "mb.example.com", "role": DomainRole.sending})
    mb = db_create_mailbox(db, {
        "domain_id": dom.id,
        "local_part": "contact",
        "email": "contact@mb.example.com",
        "daily_limit": 100,
        "hourly_limit": 20,
    })
    assert mb.email == "contact@mb.example.com"
    assert mb.sent_today == 0
    assert mb.warmup_status == WarmupStatus.not_started


def test_create_campaign(db):
    c = db_create_campaign(db, {
        "project_id": "test-project",
        "name": "Test Campaign",
        "channel": Channel.email,
        "daily_send_limit": 50,
    })
    assert c.status == CampaignStatus.draft
    assert c.project_id == "test-project"


def test_update_domain(db):
    dom = db_create_domain(db, {"name": "upd.example.com"})
    updated = db_update_domain(db, dom.id, {"spf_status": DnsStatus.valid})
    assert updated.spf_status == DnsStatus.valid


def test_list_domains_active_only(db):
    db_create_domain(db, {"name": "active.example.com", "is_active": True})
    db_create_domain(db, {"name": "inactive.example.com", "is_active": False})
    all_domains = db_list_domains(db, active_only=False)
    active = db_list_domains(db, active_only=True)
    assert len(all_domains) == 2
    assert len(active) == 1


def test_pydantic_domain_create():
    d = SendingDomainCreate(name="pydantic.example.com")
    assert d.role == DomainRole.sending
    assert d.meta == {}


def test_pydantic_campaign_create():
    c = CampaignCreate(project_id="p1", name="Camp 1")
    assert c.channel == Channel.email
    assert c.track_opens is True
