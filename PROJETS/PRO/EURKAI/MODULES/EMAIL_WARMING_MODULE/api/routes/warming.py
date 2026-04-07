"""
EMAIL_WARMING_MODULE — API Routes
CRUD pools, senders, receivers + trigger manuel + stats.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...database import (
    db_create_pool, db_list_pools, db_get_pool, db_update_pool,
    db_add_sender, db_list_senders,
    db_add_receiver, db_list_receivers,
    db_session_stats,
)
from ...models import WarmingStatus

log    = logging.getLogger("warming.api")
router = APIRouter(prefix="/warming", tags=["Email Warming"])


# ── Pools ──────────────────────────────────────────────────────────────────

@router.get("/pools")
def list_pools(project_id: str = None, db: Session = Depends()):
    pools = db_list_pools(db, project_id)
    return [{"id": p.id, "name": p.name, "status": p.status,
             "day": _day(p), "total_sent": p.total_sent,
             "total_replied": p.total_replied,
             "last_session": p.last_session_at.isoformat() if p.last_session_at else None}
            for p in pools]


@router.post("/pools")
async def create_pool(body: dict, db: Session = Depends()):
    pool = db_create_pool(db,
        project_id=body["project_id"],
        name=body["name"],
        ramp_schedule=body.get("ramp_schedule", ''),
        session_interval_hours=body.get("session_interval_hours", 4),
    )
    return {"id": pool.id, "name": pool.name}


@router.patch("/pools/{pool_id}")
async def update_pool(pool_id: str, body: dict, db: Session = Depends()):
    pool = db_update_pool(db, pool_id, body)
    if not pool:
        raise HTTPException(404, "Pool introuvable")
    return {"ok": True}


@router.get("/pools/{pool_id}/stats")
def pool_stats(pool_id: str, db: Session = Depends()):
    pool = db_get_pool(db, pool_id)
    if not pool:
        raise HTTPException(404)
    stats = db_session_stats(db, pool_id)
    stats["day"] = _day(pool)
    stats["status"] = pool.status
    return stats


# ── Senders ────────────────────────────────────────────────────────────────

@router.get("/pools/{pool_id}/senders")
def list_senders(pool_id: str, db: Session = Depends()):
    return [{"id": s.id, "email": s.email, "provider": s.provider,
             "active": s.active, "sent_total": s.sent_total}
            for s in db_list_senders(db, pool_id, active_only=False)]


@router.post("/pools/{pool_id}/senders")
async def add_sender(pool_id: str, body: dict, db: Session = Depends()):
    s = db_add_sender(db, pool_id,
        email=body["email"],
        display_name=body.get("display_name"),
        provider=body.get("provider", "brevo"),
    )
    return {"id": s.id, "email": s.email}


# ── Receivers ──────────────────────────────────────────────────────────────

@router.get("/pools/{pool_id}/receivers")
def list_receivers(pool_id: str, db: Session = Depends()):
    return [{"id": r.id, "email": r.email, "auto_reply": r.auto_reply,
             "active": r.active, "received_total": r.received_total,
             "replied_total": r.replied_total}
            for r in db_list_receivers(db, pool_id, active_only=False)]


@router.post("/pools/{pool_id}/receivers")
async def add_receiver(pool_id: str, body: dict, db: Session = Depends()):
    r = db_add_receiver(db, pool_id,
        email=body["email"],
        imap_host=body["imap_host"],
        imap_password=body["imap_password"],
        imap_port=body.get("imap_port", 993),
        display_name=body.get("display_name"),
        auto_reply=body.get("auto_reply", True),
    )
    return {"id": r.id, "email": r.email}


# ── Trigger manuel ─────────────────────────────────────────────────────────

@router.post("/pools/{pool_id}/run")
def run_pool(pool_id: str, db: Session = Depends(),
             brevo_api_key: str = ""):
    from ...module import WarmingEngine
    engine = WarmingEngine(db, brevo_api_key=brevo_api_key)
    result = engine.run_session(pool_id)
    if not result.get("ok"):
        raise HTTPException(400, result.get("reason", "Erreur"))
    return result


# ── Helpers ────────────────────────────────────────────────────────────────

def _day(pool) -> int:
    from datetime import datetime
    if not pool.start_date:
        return 0
    return (datetime.utcnow().date() - pool.start_date.date()).days + 1
