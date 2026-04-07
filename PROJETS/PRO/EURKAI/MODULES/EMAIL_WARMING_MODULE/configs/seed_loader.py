"""
EMAIL_WARMING_MODULE — Seed Loader
Charge un fichier JSON de config projet (pool + senders + receivers)
et l'insère en base si le pool n'existe pas encore.

Usage :
    from email_warming_module.configs.seed_loader import load_seed
    pool = load_seed("presence_ia", db)   # charge configs/presence_ia_seed.json
"""
import json
import os
from pathlib import Path
from sqlalchemy.orm import Session

_CONFIGS_DIR = Path(__file__).parent


def load_seed(project_name: str, db: Session):
    """
    Charge le seed <project_name>_seed.json et initialise le pool + senders + receivers.
    Si le pool existe déjà (même project_id + name), retourne le pool existant.
    Retourne : WarmingPoolDB
    """
    from ..database import (
        db_create_pool, db_list_pools,
        db_add_sender, db_list_senders,
        db_add_receiver, db_list_receivers,
    )

    seed_file = _CONFIGS_DIR / f"{project_name}_seed.json"
    if not seed_file.exists():
        raise FileNotFoundError(f"Seed introuvable : {seed_file}")

    data = json.loads(seed_file.read_text(encoding="utf-8"))
    pool_cfg = data["pool"]

    # Chercher un pool existant pour ce projet
    existing = db_list_pools(db, project_id=pool_cfg["project_id"])
    pool = next((p for p in existing if p.name == pool_cfg["name"]), None)

    if not pool:
        import json as _json
        pool = db_create_pool(
            db,
            project_id=pool_cfg["project_id"],
            name=pool_cfg["name"],
            ramp_schedule=_json.dumps(pool_cfg.get("ramp_schedule", [])),
            session_interval_hours=pool_cfg.get("session_interval_hours", 4),
        )

    # Senders — n'ajouter que ceux qui n'existent pas encore
    existing_emails = {s.email for s in db_list_senders(db, pool.id, active_only=False)}
    for s in data.get("senders", []):
        if s["email"] not in existing_emails:
            db_add_sender(db, pool.id,
                email=s["email"],
                display_name=s.get("display_name"),
                provider=s.get("provider", "brevo"),
            )

    # Receivers — résoudre les variables d'environnement (ENV:VAR_NAME)
    existing_rcv = {r.email for r in db_list_receivers(db, pool.id, active_only=False)}
    for r in data.get("receivers", []):
        if r["email"] in existing_rcv:
            continue
        password = r.get("imap_password", "")
        if password.startswith("ENV:"):
            password = os.environ.get(password[4:], "")
        db_add_receiver(db, pool.id,
            email=r["email"],
            imap_host=r["imap_host"],
            imap_port=r.get("imap_port", 993),
            imap_password=password,
            display_name=r.get("display_name"),
            auto_reply=r.get("auto_reply", True),
        )

    return pool
