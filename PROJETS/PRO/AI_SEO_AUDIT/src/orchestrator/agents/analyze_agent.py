"""AnalyzeAgent - Analyzes audit results and identifies gaps."""
from typing import List, Dict, Any
from collections import Counter
from ...core.object import Object, TestResult
from ...core.domain.audit_session import AuditResult
from ...core.domain.competitor_analysis import CompetitorAnalysis, Competitor, Gap


class AnalyzeAgent(Object):
    """
    Analyze Agent - Phase 2 of audit process.

    Extends: Object → flow.agent.Agent

    Responsibilities:
    - Calculate visibility score
    - Identify competitors and their visibility
    - Detect visibility gaps
    - Prioritize recommendations
    """

    def __init__(self, language: str = "fr", **kwargs):
        super().__init__(**kwargs)
        self.language = language

    def validate(self) -> bool:
        """Validate agent configuration."""
        return True

    def test(self) -> TestResult:
        """Test agent functionality."""
        # Create mock results for testing
        mock_results = [
            AuditResult("query1", "chatgpt", True, position=1, competitors=["Competitor A"]),
            AuditResult("query2", "chatgpt", False, competitors=["Competitor A", "Competitor B"]),
        ]

        try:
            analysis = self.execute(mock_results, "Test Company")
            if not analysis:
                return TestResult(False, "Execute returned None")
            if analysis.target_company != "Test Company":
                return TestResult(False, "Target company not set correctly")
        except Exception as e:
            return TestResult(False, f"Execute failed: {e}")

        return TestResult(True, "Analyze agent is operational")

    def execute(self, results: List[AuditResult], target_company: str) -> CompetitorAnalysis:
        """
        Execute competitor analysis.

        Args:
            results: List of audit results
            target_company: Name of target company

        Returns:
            CompetitorAnalysis object
        """
        # Identify competitors
        competitors = self._identify_competitors(results)

        # Create analysis object
        analysis = CompetitorAnalysis(
            target_company=target_company,
            competitors=competitors
        )

        # Identify gaps
        gaps = self.identify_gaps(results, competitors)
        analysis.visibility_gaps = gaps

        # Prioritize recommendations
        priority = self._prioritize_recommendations(gaps)
        analysis.recommendations_priority = priority

        self.touch()
        return analysis

    def calculate_visibility_score(self, results: List[AuditResult]) -> float:
        """
        Calculate visibility score (0-100).

        Scoring:
        - Mentioned + position 1-3: 100 points
        - Mentioned + position 4-5: 75 points
        - Mentioned + position 6+: 50 points
        - Not mentioned: 0 points
        """
        if not results:
            return 0.0

        total_score = 0
        for result in results:
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

        return total_score / len(results)

    def identify_gaps(self, results: List[AuditResult], competitors: List[Competitor]) -> List[Gap]:
        """
        Identify visibility gaps.

        Analyzes why competitors are more visible.
        """
        from ...core.config.translations import get_gap_description

        gaps = []

        # Count mentions
        total_queries = len(results)
        mentioned_count = sum(1 for r in results if r.company_mentioned)
        mention_rate = mentioned_count / total_queries if total_queries > 0 else 0

        # Gap: Low mention rate
        if mention_rate < 0.3:
            description = get_gap_description(
                "low_mention_rate",
                self.language,
                mentioned=mentioned_count,
                total=total_queries,
                rate=int(mention_rate * 100)
            )
            gaps.append(Gap(
                type="authority",
                description=description,
                severity="high",
                affected_queries=[r.query for r in results if not r.company_mentioned]
            ))

        # Gap: Competitors more visible
        if len(competitors) > 0:
            top_competitors = sorted(competitors, key=lambda c: c.mention_count, reverse=True)[:3]
            competitor_names = [c.name for c in top_competitors]
            description = get_gap_description(
                "competitors_more_visible",
                self.language,
                competitors=", ".join(competitor_names)
            )
            gaps.append(Gap(
                type="authority",
                description=description,
                severity="high" if len(competitors) > 5 else "medium"
            ))

        # Gap: Poor positioning when mentioned
        poor_positions = [r for r in results if r.company_mentioned and r.position and r.position > 5]
        if len(poor_positions) > total_queries * 0.3:
            description = get_gap_description(
                "poor_positioning",
                self.language,
                count=len(poor_positions)
            )
            gaps.append(Gap(
                type="content",
                description=description,
                severity="medium",
                affected_queries=[r.query for r in poor_positions]
            ))

        # Gap: Structured data (always applicable)
        description = get_gap_description("missing_structured_data", self.language)
        gaps.append(Gap(
            type="structured_data",
            description=description,
            severity="medium"
        ))

        # Gap: Content optimization
        description = get_gap_description("content_not_optimized", self.language)
        gaps.append(Gap(
            type="content",
            description=description,
            severity="medium"
        ))

        return gaps

    def _identify_competitors(self, results: List[AuditResult]) -> List[Competitor]:
        """
        Identify competitors from results.

        Aggregates mentions across all queries.
        """
        # Count mentions per competitor
        all_competitors = []
        for result in results:
            all_competitors.extend(result.competitors)

        if not all_competitors:
            return []

        # Count occurrences
        competitor_counts = Counter(all_competitors)

        # Calculate average position for each competitor
        competitors = []
        for name, count in competitor_counts.items():
            # Find positions where this competitor appeared
            positions = []
            for result in results:
                if name in result.competitors:
                    # Find position in the competitors list
                    try:
                        pos = result.competitors.index(name) + 1
                        positions.append(pos)
                    except ValueError:
                        pass

            avg_position = sum(positions) / len(positions) if positions else None

            competitors.append(Competitor(
                name=name,
                mention_count=count,
                avg_position=avg_position
            ))

        # Sort by mention count
        competitors.sort(key=lambda c: c.mention_count, reverse=True)

        return competitors

    def _prioritize_recommendations(self, gaps: List[Gap]) -> List[str]:
        """
        Prioritize recommendations based on gaps.

        Returns list of recommendation types in priority order.
        """
        priority = []

        # High severity gaps first
        high_severity = [g for g in gaps if g.severity == "high"]
        for gap in high_severity:
            if gap.type not in priority:
                priority.append(gap.type)

        # Medium severity
        medium_severity = [g for g in gaps if g.severity == "medium"]
        for gap in medium_severity:
            if gap.type not in priority:
                priority.append(gap.type)

        # Low severity
        low_severity = [g for g in gaps if g.severity == "low"]
        for gap in low_severity:
            if gap.type not in priority:
                priority.append(gap.type)

        return priority
