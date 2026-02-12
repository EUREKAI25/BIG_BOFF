"""AuditAgent - Queries AI providers and extracts results."""
from typing import List, Dict, Any
from ...core.object import Object, TestResult
from ...core.domain.audit_session import AuditResult
from ...core.interface.ai_provider import AIProvider, AIResponse


class AuditAgent(Object):
    """
    Audit Agent - Phase 1 of audit process.

    Extends: Object → flow.agent.Agent

    Responsibilities:
    - Query AI provider with generated prompts
    - Parse AI responses
    - Extract company mentions and positions
    - Identify competitors mentioned
    """

    def __init__(self, provider: AIProvider, language: str = "fr", **kwargs):
        super().__init__(**kwargs)
        self.provider = provider
        self.language = language

    def validate(self) -> bool:
        """Validate agent configuration."""
        return self.provider.validate()

    def test(self) -> TestResult:
        """Test agent functionality."""
        if not self.validate():
            return TestResult(False, "Invalid provider configuration")

        # Test that we can create a mock query
        try:
            result = self.query_ai("Test query: best restaurant in Paris")
            if not result:
                return TestResult(False, "Query returned None")
        except Exception as e:
            return TestResult(False, f"Query failed: {e}")

        return TestResult(True, "Audit agent is operational")

    def execute(self, queries: List[str], target_company: str) -> List[AuditResult]:
        """
        Execute audit queries.

        Args:
            queries: List of queries to test
            target_company: Name of company to look for

        Returns:
            List of AuditResult objects
        """
        results = []

        for query in queries:
            # Query the AI
            ai_response = self.query_ai(query)

            # Extract mentions
            mentions = self.extract_companies(ai_response.raw_text)

            # Check if target company is mentioned
            company_mentioned = self._is_company_mentioned(target_company, mentions)

            # Find position of target company
            position = None
            if company_mentioned:
                position = self._find_position(target_company, mentions)

            # Identify competitors (other companies mentioned)
            competitors = [m for m in mentions if not self._is_same_company(m, target_company)]

            # Create result
            result = AuditResult(
                query=query,
                ai_provider=self.provider.name,
                company_mentioned=company_mentioned,
                position=position,
                competitors=competitors[:10],  # Top 10 competitors
                raw_response=ai_response.raw_text
            )

            results.append(result)
            self.touch()

        return results

    def query_ai(self, query: str) -> AIResponse:
        """
        Query the AI provider.

        Constructs appropriate prompt and calls provider.
        """
        # Import prompts module
        from ...core.config.prompts import format_user_prompt

        # Format prompt in the requested language
        prompt = format_user_prompt(query, self.language)

        # Call provider with language parameter
        response = self.provider.query(prompt, language=self.language)
        return response

    def extract_companies(self, response: str) -> List[str]:
        """
        Extract company/brand names from AI response.

        Uses the provider's extraction method.
        """
        return self.provider.extract_mentions(response)

    def _is_company_mentioned(self, target: str, mentions: List[str]) -> bool:
        """Check if target company is in mentions (case-insensitive, partial match)."""
        target_lower = target.lower()
        for mention in mentions:
            if target_lower in mention.lower() or mention.lower() in target_lower:
                return True
        return False

    def _find_position(self, target: str, mentions: List[str]) -> int:
        """Find position of target company in mentions list."""
        target_lower = target.lower()
        for i, mention in enumerate(mentions, 1):
            if target_lower in mention.lower() or mention.lower() in target_lower:
                return i
        return None

    def _is_same_company(self, mention: str, target: str) -> bool:
        """Check if mention refers to the same company as target."""
        mention_lower = mention.lower()
        target_lower = target.lower()
        return mention_lower in target_lower or target_lower in mention_lower
