"""Tests: Rotation engine — choose_next_mailbox"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from outbound_email_module.models import Base, CampaignStatus, DomainRole, RotationAlgorithm, WarmupStatus
from outbound_email_module.database import (
    db_create_campaign, db_create_domain, db_create_mailbox,
    db_create_rotation, db_increment_sent, db_update_mailbox,
)
from outbound_email_module.module import choose_next_mailbox


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _setup_campaign(db, algorithm=RotationAlgorithm.round_robin, n_mailboxes=3):
    dom = db_create_domain(db, {"name": "rot.example.com", "role": DomainRole.sending})
    rotation = db_create_rotation(db, {
        "name": "Test Rotation",
        "algorithm": algorithm,
        "per_mailbox_daily_cap": 50,
        "per_domain_daily_cap": 200,
    })
    campaign = db_create_campaign(db, {
        "project_id": "test",
        "name": "Test Camp",
        "rotation_strategy_id": rotation.id,
        "status": CampaignStatus.active,
    })
    mailboxes = []
    for i in range(n_mailboxes):
        mb = db_create_mailbox(db, {
            "domain_id": dom.id,
            "local_part": f"mb{i}",
            "email": f"mb{i}@rot.example.com",
            "daily_limit": 50,
            "hourly_limit": 20,
        })
        mailboxes.append(mb)
    return campaign, mailboxes


def test_choose_next_mailbox_basic(db):
    campaign, mailboxes = _setup_campaign(db)
    mb = choose_next_mailbox(db, campaign.id)
    assert mb is not None
    assert mb.email.endswith("@rot.example.com")


def test_choose_next_mailbox_respects_daily_limit(db):
    campaign, mailboxes = _setup_campaign(db, n_mailboxes=1)
    mb = mailboxes[0]
    # Fill up daily limit
    db_update_mailbox(db, mb.id, {"sent_today": 50})
    result = choose_next_mailbox(db, campaign.id)
    assert result is None


def test_choose_next_mailbox_round_robin(db):
    campaign, mailboxes = _setup_campaign(db, algorithm=RotationAlgorithm.round_robin)
    # After incrementing mb0, next should be mb1 (least recently used)
    db_increment_sent(db, mailboxes[0].id)
    mb = choose_next_mailbox(db, campaign.id)
    # mb1 or mb2 should be chosen (they have last_send_at=None, mb0 has a timestamp)
    assert mb.id != mailboxes[0].id


def test_choose_next_mailbox_least_used(db):
    campaign, mailboxes = _setup_campaign(db, algorithm=RotationAlgorithm.least_used)
    db_update_mailbox(db, mailboxes[0].id, {"sent_today": 10})
    db_update_mailbox(db, mailboxes[1].id, {"sent_today": 5})
    db_update_mailbox(db, mailboxes[2].id, {"sent_today": 1})
    mb = choose_next_mailbox(db, campaign.id)
    assert mb.id == mailboxes[2].id


def test_choose_next_mailbox_skip_inactive(db):
    campaign, mailboxes = _setup_campaign(db, n_mailboxes=2)
    db_update_mailbox(db, mailboxes[0].id, {"is_active": False})
    mb = choose_next_mailbox(db, campaign.id)
    assert mb.id == mailboxes[1].id
