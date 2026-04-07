"""
EMAIL_WARMING_MODULE — EURKAI
Module de warming email bidirectionnel (Brevo/SMTP + IMAP).
Project-agnostic, pluggable dans tout projet EURKAI.

Usage minimal :
    from email_warming_module import WarmingEngine, init_db
    from email_warming_module.configs.seed_loader import load_seed

    engine = init_db()
    db     = make_session()()
    pool   = load_seed("presence_ia", db)
    WarmingEngine(db, brevo_api_key="...").run_session(pool.id)

Intégration APScheduler :
    scheduler.add_job(
        WarmingEngine.scheduler_job,
        "interval", hours=4,
        args=[pool_id, db_url, brevo_api_key]
    )
"""

from .module   import WarmingEngine
from .database import init_db, make_session, db_create_pool, db_list_pools, db_session_stats
from .models   import WarmingPoolDB, WarmingSenderDB, WarmingReceiverDB, WarmingSessionDB, WarmingStatus

__all__ = [
    # Core
    "WarmingEngine",
    # DB helpers
    "init_db", "make_session",
    "db_create_pool", "db_list_pools", "db_session_stats",
    # Models / enums
    "WarmingPoolDB", "WarmingSenderDB", "WarmingReceiverDB",
    "WarmingSessionDB", "WarmingStatus",
]
