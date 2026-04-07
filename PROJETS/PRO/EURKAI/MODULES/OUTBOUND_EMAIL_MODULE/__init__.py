"""
OUTBOUND_EMAIL_MODULE
Generic outbound email strategy engine for EURKAI.
No hardcoded business data — all config via DB or seed JSON.

Usage (as sub-app):
    from outbound_email_module.api.main import app as oem_app
    parent_app.mount("/oem", oem_app)

Usage (core engine only):
    from outbound_email_module.module import choose_next_mailbox, execute_send_batch
    from outbound_email_module.database import SessionLocal, init_db
    from outbound_email_module.providers.brevo import BrevoProvider
"""
from .database import SessionLocal, get_db, init_db
from .models import EurkaiOutput
from .module import (
    apply_warmup_step, check_compliance, choose_next_mailbox,
    enforce_compliance, execute_send_batch, handle_bounce,
    handle_click, handle_open, handle_reply,
)
from .providers import AbstractEmailProvider, BrevoProvider

__version__ = "1.0.0"

__all__ = [
    "init_db", "SessionLocal", "get_db",
    "EurkaiOutput",
    "choose_next_mailbox", "execute_send_batch",
    "check_compliance", "enforce_compliance", "apply_warmup_step",
    "handle_bounce", "handle_reply", "handle_open", "handle_click",
    "AbstractEmailProvider", "BrevoProvider",
]
