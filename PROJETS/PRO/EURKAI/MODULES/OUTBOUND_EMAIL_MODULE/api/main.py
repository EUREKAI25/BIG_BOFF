"""
OUTBOUND_EMAIL_MODULE — FastAPI app
Run standalone: uvicorn outbound_email_module.api.main:app --port 8010
Or mount as sub-app in a parent FastAPI instance.
"""
import os

from fastapi import FastAPI

from ..database import init_db
from .routes import (
    campaigns_router, compliance_router, domains_router,
    mailboxes_router, reporting_router, rotation_router,
    send_router, sequences_router, warmup_router,
)

app = FastAPI(
    title="Outbound Email Module — EURKAI",
    description="Generic reusable outbound email strategy engine.",
    version="1.0.0",
)

# Init DB on startup
@app.on_event("startup")
def startup():
    init_db()


# Mount all routers
_PREFIX = os.getenv("OEM_API_PREFIX", "/oem")

for _r in [
    domains_router, mailboxes_router, warmup_router, rotation_router,
    campaigns_router, sequences_router, send_router, reporting_router,
    compliance_router,
]:
    app.include_router(_r, prefix=_PREFIX)


@app.get(_PREFIX + "/health")
def health():
    return {"status": "ok", "module": "outbound_email_module"}
