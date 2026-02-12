"""Audit service - Business logic for audits."""
import asyncio
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Audit as AuditModel, User as UserModel, Query as QueryModel
from ..core.domain.audit_session import AuditSession
from ..core.interface.ai_provider import AIProvider
from ..core.config.sector_template import SectorTemplate
from ..orchestrator.audit_orchestrator import AuditOrchestrator


class AuditService:
    """Service for managing audits."""

    @staticmethod
    async def create_audit(
        db: AsyncSession,
        company_name: str,
        sector: str,
        location: str = "",
        email: Optional[str] = None,
        plan: str = "freemium",
        language: str = "fr",
    ) -> AuditModel:
        """
        Create new audit in database.

        Returns audit in 'pending' status.
        Actual execution happens asynchronously via run_audit().
        """
        # Create or get user if email provided
        user_id = None
        if email:
            user = await AuditService._get_or_create_user(db, email, company_name)
            user_id = user.id

        # Create audit record
        audit = AuditModel(
            user_id=user_id,
            company_name=company_name,
            sector=sector,
            location=location,
            language=language,
            plan=plan,
            status="pending",
        )

        db.add(audit)
        await db.commit()
        await db.refresh(audit)

        return audit

    @staticmethod
    async def get_audit(db: AsyncSession, audit_id: UUID) -> Optional[AuditModel]:
        """Get audit by ID."""
        result = await db.execute(
            select(AuditModel).where(AuditModel.id == audit_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def run_audit(db: AsyncSession, audit_id: UUID) -> AuditModel:
        """
        Execute audit asynchronously.

        This should be called in background task (Celery/Redis queue in production).
        For MVP, runs synchronously.
        """
        # Get audit from DB
        audit_model = await AuditService.get_audit(db, audit_id)
        if not audit_model:
            raise ValueError(f"Audit {audit_id} not found")

        if audit_model.status != "pending":
            raise ValueError(f"Audit {audit_id} is not pending (status: {audit_model.status})")

        # Create AuditSession object
        audit_session = AuditSession(
            ident=str(audit_model.id),
            company_name=audit_model.company_name,
            sector=audit_model.sector,
            location=audit_model.location or "",
            language=audit_model.language,
            plan=audit_model.plan,
            status="pending",
        )

        # Setup orchestrator
        provider = AIProvider(
            name="chatgpt",
            api_endpoint="https://api.openai.com/v1/chat/completions",
            model="gpt-4o-mini",
            # In production, get from settings/env
            api_key="",  # Will use mock for MVP
        )

        # Get sector template
        if audit_model.sector == "restaurant":
            template = SectorTemplate.get_restaurant_template()
        else:
            # Fallback to restaurant template for MVP
            template = SectorTemplate.get_restaurant_template()

        orchestrator = AuditOrchestrator(
            provider=provider,
            sector_template=template,
            strict_validation=False,
            language=audit_model.language
        )

        # Execute orchestrator
        completed_session = orchestrator.execute(audit_session)

        # Update database with results
        audit_model.status = completed_session.status
        audit_model.visibility_score = completed_session.visibility_score

        # Extract analysis data
        analysis = completed_session.metadata.get("analysis", {})

        # Structure results for template
        audit_model.results = {
            "score": completed_session.visibility_score,
            "total_mentions": analysis.get("total_mentions", 0),
            "avg_position": analysis.get("avg_position"),
            "competitors": analysis.get("competitors", []),
            "gaps": analysis.get("gaps", []),
            "recommendations": completed_session.metadata.get("recommendations", []),
        }

        if completed_session.status == "completed":
            from datetime import datetime
            audit_model.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(audit_model)

        # Save queries to database
        if completed_session.results:
            await AuditService._save_queries(db, audit_model.id, completed_session.results)

        return audit_model

    @staticmethod
    async def _get_or_create_user(
        db: AsyncSession, email: str, company_name: str
    ) -> UserModel:
        """Get existing user or create new one."""
        result = await db.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = UserModel(email=email, company_name=company_name)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user

    @staticmethod
    async def _save_queries(db: AsyncSession, audit_id: UUID, results):
        """Save query results to database."""
        for result in results:
            query = QueryModel(
                audit_id=audit_id,
                query_text=result.query,
                ai_provider=result.ai_provider,
                ai_response=result.raw_response,
                company_mentioned=result.company_mentioned,
                position=result.position,
                competitors_found=result.competitors,
            )
            db.add(query)

        await db.commit()
