"""FastAPI main application."""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import os

# Import routes
from .routes import audit, payment, export
from ..database.session import get_db
from ..services.audit_service import AuditService

app = FastAPI(
    title="AI SEO Audit API",
    description="API for AI-powered SEO visibility audits",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="src/templates")


@app.get("/")
async def landing_page(request: Request):
    """Landing page with audit form."""
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/results/{audit_id}")
async def results_page(request: Request, audit_id: str, db: AsyncSession = Depends(get_db)):
    """Results page showing audit results."""
    try:
        audit = await AuditService.get_audit(db, audit_id)
        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found")

        # Convert to dict for template
        audit_data = {
            "audit_id": str(audit.id),
            "company_name": audit.company_name,
            "sector": audit.sector,
            "plan": audit.plan,
            "status": audit.status,
            "current_step": audit.current_step,
            "progress": audit.progress,
            "error_message": audit.error_message,
            "queries_count": len(audit.queries) if audit.queries else 0,
            "results": audit.results or {},
        }

        return templates.TemplateResponse("results.html", {
            "request": request,
            "audit": audit_data
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/success")
async def success_page(request: Request, audit_id: str = None):
    """Payment success page."""
    return templates.TemplateResponse("success.html", {
        "request": request,
        "audit_id": audit_id
    })


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-seo-audit-api",
        "version": "1.0.0",
        "phase": "setup"
    }


# Include API routes
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(payment.router, prefix="/api/payment", tags=["Payment"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
