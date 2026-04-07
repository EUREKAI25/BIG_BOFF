from .campaigns import router as campaigns_router
from .compliance import router as compliance_router
from .domains import router as domains_router
from .mailboxes import router as mailboxes_router
from .reporting import router as reporting_router
from .rotation import router as rotation_router
from .send import router as send_router
from .sequences import router as sequences_router
from .warmup import router as warmup_router

__all__ = [
    "domains_router", "mailboxes_router", "warmup_router", "rotation_router",
    "campaigns_router", "sequences_router", "send_router", "reporting_router",
    "compliance_router",
]
