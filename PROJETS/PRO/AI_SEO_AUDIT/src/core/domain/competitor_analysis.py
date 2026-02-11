"""CompetitorAnalysis - Analysis of competitors visibility."""
from typing import List, Dict, Any, Optional
from ..object import Object, TestResult


class Competitor:
    """Competitor information."""
    def __init__(self, name: str, mention_count: int = 0, avg_position: Optional[float] = None):
        self.name = name
        self.mention_count = mention_count
        self.avg_position = avg_position

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "mention_count": self.mention_count,
            "avg_position": self.avg_position,
        }


class Gap:
    """Visibility gap identified."""
    def __init__(
        self,
        type: str,
        description: str,
        severity: str = "medium",
        affected_queries: Optional[List[str]] = None
    ):
        self.type = type  # content/structured_data/editorial/authority
        self.description = description
        self.severity = severity  # low/medium/high
        self.affected_queries = affected_queries or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "description": self.description,
            "severity": self.severity,
            "affected_queries": self.affected_queries,
        }


class CompetitorAnalysis(Object):
    """
    Competitor analysis object.

    Extends: Object → domain.service.Analysis

    Analyzes visibility gaps between target company and competitors.
    """

    def __init__(
        self,
        target_company: str,
        competitors: Optional[List[Competitor]] = None,
        visibility_gaps: Optional[List[Gap]] = None,
        recommendations_priority: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.target_company = target_company
        self.competitors = competitors or []
        self.visibility_gaps = visibility_gaps or []
        self.recommendations_priority = recommendations_priority or []

    def validate(self) -> bool:
        """Validate analysis."""
        if not self.target_company:
            return False
        return True

    def test(self) -> TestResult:
        """Test analysis functionality."""
        if not self.validate():
            return TestResult(False, "Invalid target company")

        if self.competitors and not self.visibility_gaps:
            return TestResult(False, "Competitors found but no gaps identified")

        return TestResult(True, "Analysis is valid")

    def identify_gaps(self) -> List[Gap]:
        """
        Identify visibility gaps.

        Analyzes why competitors are more visible than target.
        """
        gaps = []

        # Check if target has low visibility compared to competitors
        if len(self.competitors) > 0:
            gaps.append(Gap(
                type="authority",
                description=f"{len(self.competitors)} competitors have better visibility",
                severity="high" if len(self.competitors) > 5 else "medium"
            ))

        # Check for content gaps (will be enhanced in Phase 3)
        gaps.append(Gap(
            type="content",
            description="Target company lacks AI-optimized content",
            severity="medium"
        ))

        # Check for structured data gaps
        gaps.append(Gap(
            type="structured_data",
            description="Missing or incomplete structured data (Schema.org)",
            severity="medium"
        ))

        self.visibility_gaps = gaps
        self.touch()
        return gaps

    def rank_competitors(self) -> List[Competitor]:
        """
        Rank competitors by visibility.

        Sorts by mention count and average position.
        """
        self.competitors.sort(
            key=lambda c: (c.mention_count, -(c.avg_position or 999)),
            reverse=True
        )
        return self.competitors

    def suggest_queries(self, count: int = 5) -> List[str]:
        """
        Suggest additional queries to test.

        Based on sector and competitor patterns.
        """
        # Placeholder - will be enhanced with sector templates in Phase 3
        suggestions = [
            f"meilleur {self.target_company}",
            f"{self.target_company} avis",
            f"{self.target_company} vs concurrent",
            f"alternative {self.target_company}",
            f"{self.target_company} recommandation",
        ]
        return suggestions[:count]

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "target_company": self.target_company,
            "competitors": [c.to_dict() for c in self.competitors],
            "visibility_gaps": [g.to_dict() for g in self.visibility_gaps],
            "recommendations_priority": self.recommendations_priority,
        })
        return base
