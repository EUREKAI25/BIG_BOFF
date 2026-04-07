"""Tests: Compliance rules evaluation"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from outbound_email_module.models import (
    Base, BounceType, CampaignStatus, ComplianceAction, ComplianceScope,
    DeliveryStatus, DomainRole,
)
from outbound_email_module.database import (
    db_create_campaign, db_create_delivery, db_create_domain,
    db_create_mailbox, db_create_rule, db_update_delivery,
)
from outbound_email_module.module import check_compliance


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _setup(db):
    dom = db_create_domain(db, {"name": "comp.example.com", "role": DomainRole.sending})
    mb = db_create_mailbox(db, {
        "domain_id": dom.id, "local_part": "test",
        "email": "test@comp.example.com", "daily_limit": 100, "hourly_limit": 20,
    })
    camp = db_create_campaign(db, {
        "project_id": "p1", "name": "C1", "status": CampaignStatus.active,
    })
    return dom, mb, camp


def test_no_triggered_rules(db):
    _, mb, camp = _setup(db)
    db_create_rule(db, {
        "name": "Bounce > 5%", "scope": "mailbox", "rule_type": "bounce_rate",
        "threshold": 0.05, "window_hours": 24, "action_on_trigger": ComplianceAction.alert,
    })
    triggered = check_compliance(db, mb.id, camp.id)
    assert triggered == []


def test_bounce_rate_triggers(db):
    _, mb, camp = _setup(db)
    db_create_rule(db, {
        "name": "Bounce > 5%", "scope": "mailbox", "rule_type": "bounce_rate",
        "threshold": 0.05, "window_hours": 24, "action_on_trigger": ComplianceAction.pause_mailbox,
    })
    # Create 10 deliveries, 2 bounced → 20% bounce rate
    from datetime import datetime
    for i in range(8):
        d = db_create_delivery(db, {
            "campaign_id": camp.id, "prospect_id": f"p{i}", "mailbox_id": mb.id,
            "delivery_status": DeliveryStatus.sent, "sent_at": datetime.utcnow(),
        })
    for i in range(2):
        d = db_create_delivery(db, {
            "campaign_id": camp.id, "prospect_id": f"pb{i}", "mailbox_id": mb.id,
            "delivery_status": DeliveryStatus.bounced, "sent_at": datetime.utcnow(),
            "bounce_type": BounceType.hard,
        })

    triggered = check_compliance(db, mb.id, camp.id)
    assert len(triggered) == 1
    assert triggered[0]["action"] == ComplianceAction.pause_mailbox
