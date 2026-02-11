"""Pydantic schemas for API requests/responses."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Audit schemas
class AuditCreateRequest(BaseModel):
    """Request to create new audit."""
    company_name: str = Field(..., min_length=2, max_length=255)
    sector: str = Field(..., min_length=2, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    plan: str = Field("freemium", pattern="^(freemium|starter|pro)$")
    language: str = Field("fr", pattern="^(fr|en|es|de|it)$")


class AuditStatusResponse(BaseModel):
    """Response for audit status."""
    audit_id: str
    status: str  # pending/running/completed/failed
    progress: int  # 0-100
    current_step: Optional[str] = None
    estimated_completion: Optional[datetime] = None


class CompetitorInfo(BaseModel):
    """Competitor information."""
    name: str
    mention_count: int
    avg_position: Optional[float] = None


class GapInfo(BaseModel):
    """Visibility gap information."""
    type: str
    description: str
    severity: str
    affected_queries: List[str] = []


class RecommendationInfo(BaseModel):
    """Recommendation information."""
    id: str
    type: str
    title: str
    description: str
    priority: int
    estimated_impact: str
    content: Dict[str, Any]
    integration_guide: str


class AuditResultsResponse(BaseModel):
    """Response for completed audit results."""
    audit_id: str
    company_name: str
    sector: str
    location: Optional[str]
    visibility_score: float
    status: str
    queries_tested: int
    competitors: List[CompetitorInfo]
    gaps: List[GapInfo]
    recommendations: List[RecommendationInfo]
    created_at: datetime
    completed_at: Optional[datetime]


# Payment schemas
class PaymentCreateRequest(BaseModel):
    """Request to create Stripe checkout session."""
    audit_id: str
    plan: str = Field(..., pattern="^(starter|pro)$")
    success_url: str
    cancel_url: str


class PaymentCreateResponse(BaseModel):
    """Response with Stripe checkout URL."""
    checkout_url: str
    session_id: str


class StripeWebhookEvent(BaseModel):
    """Stripe webhook event (simplified)."""
    type: str
    data: Dict[str, Any]


# Export schemas
class ExportRequest(BaseModel):
    """Request parameters for export."""
    format: str = Field("pdf", pattern="^(pdf|json|html)$")


# Health check
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    phase: str
    timestamp: datetime


# Error response
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
