"""Audit API routes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from ...database.session import get_db
from ...services.audit_service import AuditService
from ...core.utils.language_detector import get_browser_language_from_header, normalize_language_code
from ..schemas import (
    AuditCreateRequest,
    AuditStatusResponse,
    AuditResultsResponse,
    CompetitorInfo,
    GapInfo,
    RecommendationInfo,
    ErrorResponse,
)

router = APIRouter()


@router.post("/create", response_model=AuditStatusResponse)
async def create_audit(
    audit_request: AuditCreateRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create new audit and start processing.

    Returns audit ID and initial status.
    Audit processing happens in background.

    Language detection:
    - Uses explicit language from request if provided
    - Falls back to browser Accept-Language header
    - Defaults to French if no preference detected
    """
    try:
        # Detect language from browser if not explicitly provided or default
        language = audit_request.language
        if language == "fr":  # Default value, try to detect better
            accept_language = http_request.headers.get("accept-language")
            if accept_language:
                detected_lang = get_browser_language_from_header(accept_language)
                if detected_lang != "fr":
                    language = detected_lang

        # Normalize language code just in case
        language = normalize_language_code(language)

        # Create audit in DB
        audit = await AuditService.create_audit(
            db=db,
            company_name=audit_request.company_name,
            sector=audit_request.sector,
            location=audit_request.location or "",
            email=audit_request.email,
            plan=audit_request.plan,
            language=language,
        )

        # Start audit processing in background
        background_tasks.add_task(
            AuditService.run_audit,
            db=db,
            audit_id=audit.id
        )

        return AuditStatusResponse(
            audit_id=str(audit.id),
            status=audit.status,
            progress=0,
            current_step="Initializing audit...",
            estimated_completion=None,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{audit_id}/status", response_model=AuditStatusResponse)
async def get_audit_status(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current status of audit.

    Use for polling while audit is running.
    """
    audit = await AuditService.get_audit(db, audit_id)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Calculate progress
    progress_map = {
        "pending": 0,
        "running": 50,
        "completed": 100,
        "failed": 0,
    }
    progress = progress_map.get(audit.status, 0)

    # Determine current step
    step_map = {
        "pending": "Waiting to start...",
        "running": "Analyzing visibility...",
        "completed": "Audit complete!",
        "failed": "Audit failed",
    }
    current_step = step_map.get(audit.status)

    return AuditStatusResponse(
        audit_id=str(audit.id),
        status=audit.status,
        progress=progress,
        current_step=current_step,
        estimated_completion=audit.completed_at,
    )


@router.get("/{audit_id}/results", response_model=AuditResultsResponse)
async def get_audit_results(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get complete audit results.

    Only available when audit status is 'completed'.
    """
    audit = await AuditService.get_audit(db, audit_id)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    if audit.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Audit not completed yet (status: {audit.status})"
        )

    # Extract data from results JSON
    results_data = audit.results or {}
    analysis = results_data.get("analysis", {})
    recommendations_data = results_data.get("recommendations", [])

    # Parse competitors
    competitors = [
        CompetitorInfo(
            name=comp["name"],
            mention_count=comp["mention_count"],
            avg_position=comp.get("avg_position"),
        )
        for comp in analysis.get("competitors", [])
    ]

    # Parse gaps
    gaps = [
        GapInfo(
            type=gap["type"],
            description=gap["description"],
            severity=gap["severity"],
            affected_queries=gap.get("affected_queries", []),
        )
        for gap in analysis.get("visibility_gaps", [])
    ]

    # Parse recommendations
    recommendations = [
        RecommendationInfo(
            id=rec.get("ident", ""),
            type=rec["type"],
            title=rec["title"],
            description=rec.get("description", ""),
            priority=rec.get("priority", 5),
            estimated_impact=rec.get("estimated_impact", "medium"),
            content=rec.get("content", {}),
            integration_guide=rec.get("integration_guide", ""),
        )
        for rec in recommendations_data
    ]

    return AuditResultsResponse(
        audit_id=str(audit.id),
        company_name=audit.company_name,
        sector=audit.sector,
        location=audit.location,
        visibility_score=audit.visibility_score or 0,
        status=audit.status,
        queries_tested=len(results_data.get("queries", [])),
        competitors=competitors,
        gaps=gaps,
        recommendations=recommendations,
        created_at=audit.created_at,
        completed_at=audit.completed_at,
    )
