"""
EMAIL_WARMING_MODULE — Database
Fonctions CRUD pour pools, senders, receivers, sessions.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from .models import Base, WarmingPoolDB, WarmingSenderDB, WarmingReceiverDB, WarmingSessionDB


def get_engine(db_url: str = None):
    url = db_url or os.getenv("WARMING_DB_URL", "sqlite:///./warming.db")
    return create_engine(url, connect_args={"check_same_thread": False})


def init_db(db_url: str = None):
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    return engine


def make_session(db_url: str = None):
    engine = get_engine(db_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Pools ──────────────────────────────────────────────────────────────────

def db_create_pool(db: Session, project_id: str, name: str, **kwargs) -> WarmingPoolDB:
    pool = WarmingPoolDB(project_id=project_id, name=name, **kwargs)
    db.add(pool); db.commit(); db.refresh(pool)
    return pool


def db_get_pool(db: Session, pool_id: str) -> WarmingPoolDB | None:
    return db.get(WarmingPoolDB, pool_id)


def db_list_pools(db: Session, project_id: str = None) -> list[WarmingPoolDB]:
    q = db.query(WarmingPoolDB)
    if project_id:
        q = q.filter_by(project_id=project_id)
    return q.order_by(WarmingPoolDB.created_at.desc()).all()


def db_update_pool(db: Session, pool_id: str, data: dict) -> WarmingPoolDB | None:
    pool = db.get(WarmingPoolDB, pool_id)
    if not pool:
        return None
    for k, v in data.items():
        if hasattr(pool, k):
            setattr(pool, k, v)
    db.commit(); db.refresh(pool)
    return pool


# ── Senders ────────────────────────────────────────────────────────────────

def db_add_sender(db: Session, pool_id: str, email: str,
                  display_name: str = None, provider: str = "brevo") -> WarmingSenderDB:
    s = WarmingSenderDB(pool_id=pool_id, email=email,
                        display_name=display_name, provider=provider)
    db.add(s); db.commit(); db.refresh(s)
    return s


def db_list_senders(db: Session, pool_id: str, active_only: bool = True) -> list[WarmingSenderDB]:
    q = db.query(WarmingSenderDB).filter_by(pool_id=pool_id)
    if active_only:
        q = q.filter_by(active=True)
    return q.all()


# ── Receivers ──────────────────────────────────────────────────────────────

def db_add_receiver(db: Session, pool_id: str, email: str, imap_host: str,
                    imap_password: str, imap_port: int = 993,
                    display_name: str = None, auto_reply: bool = True) -> WarmingReceiverDB:
    r = WarmingReceiverDB(pool_id=pool_id, email=email, imap_host=imap_host,
                          imap_port=imap_port, imap_password=imap_password,
                          display_name=display_name, auto_reply=auto_reply)
    db.add(r); db.commit(); db.refresh(r)
    return r


def db_list_receivers(db: Session, pool_id: str, active_only: bool = True) -> list[WarmingReceiverDB]:
    q = db.query(WarmingReceiverDB).filter_by(pool_id=pool_id)
    if active_only:
        q = q.filter_by(active=True)
    return q.all()


# ── Sessions ───────────────────────────────────────────────────────────────

def db_log_session(db: Session, pool_id: str, warming_day: int,
                   sent: int, received: int, replied: int, errors: int) -> WarmingSessionDB:
    s = WarmingSessionDB(pool_id=pool_id, warming_day=warming_day,
                         sent=sent, received=received, replied=replied, errors=errors)
    db.add(s); db.commit(); db.refresh(s)
    return s


def db_session_stats(db: Session, pool_id: str) -> dict:
    sessions = db.query(WarmingSessionDB).filter_by(pool_id=pool_id).all()
    return {
        "total_sessions": len(sessions),
        "total_sent":     sum(s.sent for s in sessions),
        "total_received": sum(s.received for s in sessions),
        "total_replied":  sum(s.replied for s in sessions),
        "last_session":   sessions[-1].ran_at.isoformat() if sessions else None,
    }
