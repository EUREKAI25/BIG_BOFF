"""
EURKAI_COCKPIT — Backend API Server
Version: 1.0.0

Local-first server exposing REST API for:
- Projects, Briefs, Runs
- Config, Secrets (encrypted)
- Modules registry
- Backups

Usage:
    # Development
    uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
    
    # Production
    uvicorn backend.app:app --host 127.0.0.1 --port 8000

Environment variables:
    EURKAI_DB_PATH         - Database path (default: ~/.eurkai_cockpit/cockpit.db)
    EURKAI_TOKEN           - API token (optional, empty = no auth)
    EURKAI_MASTER_PASSWORD - Master password for secrets encryption
    EURKAI_BACKUP_DIR      - Backup directory (default: ~/.eurkai_cockpit/backups)
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .api import (
    projects_router,
    briefs_router,
    runs_router,
    config_router,
    secrets_router,
    modules_router,
    backups_router,
)
from .storage import init_db, get_db_path


# =============================================================================
# LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    db_path = get_db_path()
    
    # Ensure database exists
    init_db(str(db_path))
    
    print(f"[EURKAI] Database: {db_path}")
    print(f"[EURKAI] Auth: {'enabled' if os.environ.get('EURKAI_TOKEN') else 'disabled'}")
    print(f"[EURKAI] Secrets: {'configured' if os.environ.get('EURKAI_MASTER_PASSWORD') else 'NOT configured'}")
    
    yield
    
    # Cleanup if needed
    pass


# =============================================================================
# APP
# =============================================================================

app = FastAPI(
    title="EURKAI_COCKPIT API",
    description="Local-first cockpit for AI orchestration",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# =============================================================================
# CORS (localhost only by default)
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    # Convert errors to JSON-serializable format
    errors = []
    for err in exc.errors():
        error_dict = {
            "type": err.get("type"),
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg")
        }
        # Don't include ctx as it may contain non-serializable objects
        errors.append(error_dict)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "ERR_VALIDATION",
                "message": "Validation error",
                "details": errors
            },
            "meta": {
                "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0"
            }
        }
    )


from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Wrap HTTP exceptions in standard response format."""
    detail = exc.detail
    
    # Extract code and message from detail
    if isinstance(detail, dict):
        code = detail.get("code", f"ERR_{exc.status_code}")
        message = detail.get("message", str(detail))
        details = detail.get("details")
    else:
        code = f"ERR_{exc.status_code}"
        message = str(detail)
        details = None
    
    content = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
        "meta": {
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0"
        }
    }
    
    if details:
        content["error"]["details"] = details
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    # Log to stdout
    print(f"[EURKAI ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "ERR_INTERNAL",
                "message": "Internal server error",
                "details": {"type": type(exc).__name__}
            },
            "meta": {
                "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0"
            }
        }
    )


# =============================================================================
# ROUTES
# =============================================================================

app.include_router(projects_router)
app.include_router(briefs_router)
app.include_router(runs_router)
app.include_router(config_router)
app.include_router(secrets_router)
app.include_router(modules_router)
app.include_router(backups_router)


@app.get("/")
async def root():
    """Health check / welcome."""
    return {
        "success": True,
        "data": {
            "name": "EURKAI_COCKPIT",
            "version": "1.0.0",
            "status": "running"
        },
        "meta": {
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("EURKAI_HOST", "127.0.0.1")
    port = int(os.environ.get("EURKAI_PORT", "8000"))
    
    print(f"[EURKAI] Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
