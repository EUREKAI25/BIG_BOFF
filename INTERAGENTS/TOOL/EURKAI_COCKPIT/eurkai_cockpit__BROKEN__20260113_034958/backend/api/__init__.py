"""
EURKAI_COCKPIT API Routes
"""

from .routes_projects import router as projects_router
from .routes_briefs import router as briefs_router
from .routes_runs import router as runs_router
from .routes_config import router as config_router
from .routes_secrets import router as secrets_router
from .routes_modules import router as modules_router
from .routes_backups import router as backups_router

__all__ = [
    "projects_router",
    "briefs_router", 
    "runs_router",
    "config_router",
    "secrets_router",
    "modules_router",
    "backups_router",
]
