"""AuditSession - Main audit domain object."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..object import Object, TestResult


class AuditResult:
    """Single query result."""
    def __init__(
        self,
        query: str,
        ai_provider: str,
        company_mentioned: bool,
        position: Optional[int] = None,
        competitors: Optional[List[str]] = None,
        raw_response: Optional[str] = None,
    ):
        self.query = query
        self.ai_provider = ai_provider
        self.company_mentioned = company_mentioned
        self.position = position
        self.competitors = competitors or []
        self.raw_response = raw_response

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "ai_provider": self.ai_provider,
            "company_mentioned": self.company_mentioned,
            "position": self.position,
            "competitors": self.competitors,
        }


class AuditSession(Object):
    """
    Main audit session object.

    Extends: Object → domain.service.Audit

    Represents a complete audit session for a company, including
    all queries tested, results, and visibility score.
    """

    def __init__(
        self,
        company_name: str,
        sector: str,
        location: str = "",
        language: str = "fr",
        plan: str = "freemium",
        queries: Optional[List[str]] = None,
        results: Optional[List[AuditResult]] = None,
        visibility_score: Optional[float] = None,
        status: str = "pending",
        user_email: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.company_name = company_name
        self.sector = sector
        self.location = location
        self.language = language
        self.plan = plan
        self.queries = queries or []
        self.results = results or []
        self.visibility_score = visibility_score
        self.status = status
        self.user_email = user_email

    def validate(self) -> bool:
        """Validate audit session."""
        if not self.company_name or len(self.company_name) < 2:
            return False
        if not self.sector:
            return False
        if self.plan not in ["freemium", "starter", "pro"]:
            return False
        if self.language not in ["fr", "en", "es", "de", "it"]:
            return False
        if self.status not in ["pending", "running", "completed", "failed"]:
            return False
        if self.visibility_score is not None and not (0 <= self.visibility_score <= 100):
            return False
        return True

    def test(self) -> TestResult:
        """Test audit session functionality."""
        if not self.validate():
            return TestResult(False, "Validation failed")

        # Test that queries and results are consistent
        if self.status == "completed" and not self.results:
            return TestResult(False, "Completed audit must have results")

        if self.status == "completed" and self.visibility_score is None:
            return TestResult(False, "Completed audit must have visibility score")

        return TestResult(True, "Audit session is valid")

    def execute(self) -> "AuditSession":
        """
        Execute the complete audit.

        This method will be implemented by the AuditOrchestrator in Phase 3.
        For now, it just returns self.
        """
        self.status = "running"
        self.touch()
        return self

    def generate_score(self) -> float:
        """
        Calculate visibility score based on results.

        Score calculation:
        - Company mentioned and position 1-3: 100 points
        - Company mentioned and position 4-5: 75 points
        - Company mentioned and position 6+: 50 points
        - Company not mentioned: 0 points

        Final score is average across all queries.
        """
        if not self.results:
            return 0.0

        total_score = 0
        for result in self.results:
            if not result.company_mentioned:
                score = 0
            elif result.position is not None:
                if result.position <= 3:
                    score = 100
                elif result.position <= 5:
                    score = 75
                else:
                    score = 50
            else:
                score = 0

            total_score += score

        self.visibility_score = total_score / len(self.results)
        self.touch()
        return self.visibility_score

    def export(self, format: str = "json") -> bytes:
        """
        Export audit results.

        Formats: json, pdf, html
        Will be implemented in Phase 4 (Export service).
        """
        # Placeholder for now
        if format == "json":
            import json
            return json.dumps(self.to_dict(), indent=2).encode()
        raise NotImplementedError(f"Export format '{format}' not implemented yet")

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "company_name": self.company_name,
            "sector": self.sector,
            "location": self.location,
            "language": self.language,
            "plan": self.plan,
            "queries": self.queries,
            "results": [r.to_dict() for r in self.results],
            "visibility_score": self.visibility_score,
            "status": self.status,
            "user_email": self.user_email,
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditSession":
        # Reconstruct results
        results = []
        for r in data.get("results", []):
            results.append(AuditResult(
                query=r["query"],
                ai_provider=r["ai_provider"],
                company_mentioned=r["company_mentioned"],
                position=r.get("position"),
                competitors=r.get("competitors", []),
            ))

        return cls(
            ident=data.get("ident"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            version=data.get("version", "1.0.0"),
            parent=data.get("parent"),
            metadata=data.get("metadata", {}),
            company_name=data["company_name"],
            sector=data["sector"],
            location=data.get("location", ""),
            language=data.get("language", "fr"),
            plan=data.get("plan", "freemium"),
            queries=data.get("queries", []),
            results=results,
            visibility_score=data.get("visibility_score"),
            status=data.get("status", "pending"),
            user_email=data.get("user_email"),
        )
