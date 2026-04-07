"""Tests: execute_send_batch (dry_run mode)"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from outbound_email_module.models import Base, CampaignStatus, DeliveryStatus, DomainRole
from outbound_email_module.database import (
    db_create_campaign, db_create_domain, db_create_mailbox,
    db_create_sequence, db_create_step,
)
from outbound_email_module.module import execute_send_batch
from outbound_email_module.providers.base import AbstractEmailProvider
from outbound_email_module.models import SendingMailboxDB


class MockProvider(AbstractEmailProvider):
    def send(self, mailbox, delivery_id, prospect_id, sequence_step_id, **kwargs):
        return {"success": True, "message_id": f"mock-{delivery_id}"}

    def validate_domain(self, domain_name):
        return {"success": True, "spf": "valid", "dkim": "valid", "dmarc": "valid"}

    def get_sending_stats(self, mailbox_email, window_hours=24):
        return {"sent": 0, "bounced": 0, "opened": 0, "clicked": 0}


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _setup(db):
    dom = db_create_domain(db, {"name": "send.example.com", "role": DomainRole.sending})
    mb = db_create_mailbox(db, {
        "domain_id": dom.id, "local_part": "out",
        "email": "out@send.example.com", "daily_limit": 100, "hourly_limit": 50,
    })
    camp = db_create_campaign(db, {
        "project_id": "p1", "name": "Send Test", "status": CampaignStatus.active,
    })
    seq = db_create_sequence(db, {"campaign_id": camp.id, "name": "Seq1", "stop_on_reply": True})
    step = db_create_step(db, {
        "sequence_id": seq.id, "step_order": 1, "delay_days": 0,
        "subject_template": "Hello {{name}}", "body_template": "<p>Hi {{name}}</p>",
    })
    return camp, seq, step, mb


def test_send_batch_dry_run(db):
    camp, seq, step, mb = _setup(db)
    result = execute_send_batch(
        db=db,
        campaign_id=camp.id,
        prospect_ids=["prospect-1", "prospect-2", "prospect-3"],
        sequence_step_id=step.id,
        provider=MockProvider(),
        dry_run=True,
    )
    assert result.success is True
    assert result.result["sent"] == 3
    assert result.result["skipped"] == 0
    assert result.result["failed"] == 0


def test_send_batch_dedup(db):
    camp, seq, step, mb = _setup(db)
    # First batch
    execute_send_batch(
        db=db, campaign_id=camp.id,
        prospect_ids=["p1", "p2"],
        sequence_step_id=step.id,
        provider=MockProvider(), dry_run=True,
    )
    # Second batch with same prospects — should all be skipped
    result = execute_send_batch(
        db=db, campaign_id=camp.id,
        prospect_ids=["p1", "p2"],
        sequence_step_id=step.id,
        provider=MockProvider(), dry_run=True,
    )
    assert result.result["skipped"] == 2
    assert result.result["sent"] == 0


def test_send_batch_inactive_campaign(db):
    camp, seq, step, mb = _setup(db)
    from outbound_email_module.database import db_update_campaign
    db_update_campaign(db, camp.id, {"status": CampaignStatus.paused})
    result = execute_send_batch(
        db=db, campaign_id=camp.id,
        prospect_ids=["p1"],
        sequence_step_id=step.id,
        provider=MockProvider(),
    )
    assert result.success is False
