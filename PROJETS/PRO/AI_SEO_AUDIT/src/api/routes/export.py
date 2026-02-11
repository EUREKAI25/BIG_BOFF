"""Export API routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ...database.session import get_db
from ...services.audit_service import AuditService

router = APIRouter()


@router.get("/{audit_id}/guide.pdf")
async def export_guide_pdf(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Export audit guide as PDF.

    Only available for paid plans (starter, pro).
    """
    audit = await AuditService.get_audit(db, audit_id)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    if audit.status != "completed":
        raise HTTPException(status_code=400, detail="Audit not completed")

    if audit.plan == "freemium":
        raise HTTPException(
            status_code=403,
            detail="PDF export not available for freemium plan"
        )

    # Generate PDF from recommendations
    # In Phase 5, will use WeasyPrint to generate actual PDF
    # For now, return placeholder

    pdf_content = generate_pdf_placeholder(audit)

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=audit_{audit.company_name}_{audit.id}.pdf"
        }
    )


@router.get("/{audit_id}/recommendations.json")
async def export_recommendations_json(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Export recommendations as JSON (with JSON-LD structured data).

    Available for starter and pro plans.
    """
    audit = await AuditService.get_audit(db, audit_id)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    if audit.status != "completed":
        raise HTTPException(status_code=400, detail="Audit not completed")

    if audit.plan == "freemium":
        raise HTTPException(
            status_code=403,
            detail="JSON export not available for freemium plan"
        )

    # Extract recommendations from results
    results_data = audit.results or {}
    recommendations = results_data.get("recommendations", [])

    # Format for export
    export_data = {
        "audit_id": str(audit.id),
        "company_name": audit.company_name,
        "sector": audit.sector,
        "visibility_score": audit.visibility_score,
        "recommendations": recommendations,
        "exported_at": audit.completed_at.isoformat() if audit.completed_at else None,
    }

    return JSONResponse(content=export_data)


@router.get("/{audit_id}/mockups.zip")
async def export_mockups_zip(
    audit_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Export HTML mockups as ZIP file.

    Only available for pro plan.
    """
    audit = await AuditService.get_audit(db, audit_id)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    if audit.status != "completed":
        raise HTTPException(status_code=400, detail="Audit not completed")

    if audit.plan != "pro":
        raise HTTPException(
            status_code=403,
            detail="Mockups export only available for pro plan"
        )

    # Generate mockups ZIP
    # Will be implemented in Phase 5
    raise HTTPException(
        status_code=501,
        detail="Mockups generation not implemented yet (Phase 5)"
    )


def generate_pdf_placeholder(audit) -> bytes:
    """
    Generate PDF placeholder.

    Will be replaced with real PDF generation using WeasyPrint in Phase 5.
    """
    # Simple PDF header (placeholder)
    pdf_header = b"%PDF-1.4\n"
    pdf_body = f"""
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 100 >>
stream
BT
/F1 24 Tf
100 700 Td
(AI SEO Audit - {audit.company_name}) Tj
ET
endstream
endobj
xref
0 5
trailer
<< /Size 5 /Root 1 0 R >>
%%EOF
""".encode()

    return pdf_header + pdf_body
