"""
EMAIL_WARMING_MODULE — Models
SQLAlchemy models pour la gestion du warming email inter-comptes.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WarmingStatus(str, Enum):
    active    = "active"
    paused    = "paused"
    completed = "completed"


class WarmingPoolDB(Base):
    """Pool de warming : ensemble de senders + receivers pour un projet."""
    __tablename__ = "warming_pools"

    id          : Mapped[str]  = mapped_column(sa.String, primary_key=True,
                                               default=lambda: str(uuid.uuid4()))
    project_id  : Mapped[str]  = mapped_column(sa.String, nullable=False, index=True)
    name        : Mapped[str]  = mapped_column(sa.String, nullable=False)
    status      : Mapped[str]  = mapped_column(sa.String, default=WarmingStatus.active)

    # Ramp-up schedule (JSON list of {"day": N, "emails_per_session": X})
    ramp_schedule   : Mapped[str]  = mapped_column(sa.Text,
        default='[{"day":1,"eps":4},{"day":4,"eps":8},{"day":8,"eps":12},'
                '{"day":15,"eps":16},{"day":22,"eps":20}]')
    session_interval_hours : Mapped[int]  = mapped_column(sa.Integer, default=4)
    start_date      : Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    last_session_at : Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)
    total_sent      : Mapped[int]  = mapped_column(sa.Integer, default=0)
    total_replied   : Mapped[int]  = mapped_column(sa.Integer, default=0)
    created_at      : Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.utcnow)


class WarmingSenderDB(Base):
    """Adresse email expéditrice (envoi via Brevo ou SMTP)."""
    __tablename__ = "warming_senders"

    id          : Mapped[str]  = mapped_column(sa.String, primary_key=True,
                                               default=lambda: str(uuid.uuid4()))
    pool_id     : Mapped[str]  = mapped_column(sa.String, nullable=False, index=True)
    email       : Mapped[str]  = mapped_column(sa.String, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(sa.String, nullable=True)
    # Provider: brevo | smtp
    provider    : Mapped[str]  = mapped_column(sa.String, default="brevo")
    active      : Mapped[bool] = mapped_column(sa.Boolean, default=True)
    sent_total  : Mapped[int]  = mapped_column(sa.Integer, default=0)
    created_at  : Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.utcnow)


class WarmingReceiverDB(Base):
    """Boîte IMAP réceptrice : reçoit les emails de warming + envoie les réponses auto."""
    __tablename__ = "warming_receivers"

    id          : Mapped[str]  = mapped_column(sa.String, primary_key=True,
                                               default=lambda: str(uuid.uuid4()))
    pool_id     : Mapped[str]  = mapped_column(sa.String, nullable=False, index=True)
    email       : Mapped[str]  = mapped_column(sa.String, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(sa.String, nullable=True)
    imap_host   : Mapped[str]  = mapped_column(sa.String, nullable=False)
    imap_port   : Mapped[int]  = mapped_column(sa.Integer, default=993)
    imap_password: Mapped[str] = mapped_column(sa.String, nullable=False)
    auto_reply  : Mapped[bool] = mapped_column(sa.Boolean, default=True)
    active      : Mapped[bool] = mapped_column(sa.Boolean, default=True)
    received_total : Mapped[int] = mapped_column(sa.Integer, default=0)
    replied_total  : Mapped[int] = mapped_column(sa.Integer, default=0)
    created_at  : Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.utcnow)


class WarmingSessionDB(Base):
    """Log d'une session de warming (audit + stats)."""
    __tablename__ = "warming_sessions"

    id          : Mapped[str]  = mapped_column(sa.String, primary_key=True,
                                               default=lambda: str(uuid.uuid4()))
    pool_id     : Mapped[str]  = mapped_column(sa.String, nullable=False, index=True)
    warming_day : Mapped[int]  = mapped_column(sa.Integer, default=1)
    sent        : Mapped[int]  = mapped_column(sa.Integer, default=0)
    received    : Mapped[int]  = mapped_column(sa.Integer, default=0)
    replied     : Mapped[int]  = mapped_column(sa.Integer, default=0)
    errors      : Mapped[int]  = mapped_column(sa.Integer, default=0)
    ran_at      : Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.utcnow)
