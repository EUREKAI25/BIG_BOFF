"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

# Import routes (will be created in Phase 4)
# from .routes import audit, payment, export

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


@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page (will be templated in Phase 5)."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI SEO Audit</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                   margin: 0; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .container { background: white; padding: 60px; border-radius: 12px; max-width: 600px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center; }
            h1 { color: #1a202c; margin-bottom: 20px; }
            p { color: #4a5568; font-size: 18px; line-height: 1.6; }
            .status { background: #f0fff4; border: 2px solid #9ae6b4; padding: 20px; border-radius: 8px;
                     margin-top: 30px; }
            .status h3 { color: #2f855a; margin: 0 0 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 AI SEO Audit</h1>
            <p>API backend is running!</p>
            <div class="status">
                <h3>✅ Status: Operational</h3>
                <p>Phase 1 (Setup) in progress</p>
            </div>
            <p style="margin-top: 30px; font-size: 14px; color: #718096;">
                Docs: <a href="/docs" style="color: #667eea;">/docs</a> |
                ReDoc: <a href="/redoc" style="color: #667eea;">/redoc</a>
            </p>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-seo-audit-api",
        "version": "1.0.0",
        "phase": "setup"
    }


# Routes will be added in Phase 4
# app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
# app.include_router(payment.router, prefix="/api/payment", tags=["Payment"])
# app.include_router(export.router, prefix="/api/export", tags=["Export"])
