"""AuditOrchestrator - Coordinates the complete audit process."""
from typing import Dict, Any
from ..core.object import Object, TestResult
from ..core.domain.audit_session import AuditSession
from ..core.interface.ai_provider import AIProvider
from ..core.config.sector_template import SectorTemplate
from .agents.audit_agent import AuditAgent
from .agents.analyze_agent import AnalyzeAgent
from .agents.generate_agent import GenerateAgent
from .validator import Validator, ValidationResult


class AuditOrchestrator(Object):
    """
    Audit Orchestrator - Main coordinator.

    Extends: Object → flow.orchestrator.Orchestrator

    Responsibilities:
    - Coordinate 3 agents (Audit → Analyze → Generate)
    - Manage data flow between agents
    - Validate each step via Validator
    - Does NOT perform business logic itself

    Architecture:
        Input: AuditSession (pending)
          ↓
        1. AuditAgent → queries AI, extracts results
          ↓
        2. Validator → validates results
          ↓
        3. AnalyzeAgent → calculates score, identifies gaps
          ↓
        4. Validator → validates analysis
          ↓
        5. GenerateAgent → creates recommendations
          ↓
        6. Validator → validates recommendations
          ↓
        Output: AuditSession (completed)
    """

    def __init__(
        self,
        provider: AIProvider,
        sector_template: SectorTemplate,
        strict_validation: bool = False,
        language: str = "fr",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.provider = provider
        self.sector_template = sector_template
        self.validator = Validator(strict=strict_validation)
        self.language = language

        # Initialize agents with language parameter
        self.audit_agent = AuditAgent(provider=provider, language=language)
        self.analyze_agent = AnalyzeAgent(language=language)
        self.generate_agent = GenerateAgent(language=language)

    def validate(self) -> bool:
        """Validate orchestrator configuration."""
        if not self.provider.validate():
            return False
        if not self.sector_template.validate():
            return False
        if not self.validator.validate():
            return False
        return True

    def test(self) -> TestResult:
        """Test orchestrator functionality."""
        if not self.validate():
            return TestResult(False, "Invalid configuration")

        # Test that all agents are operational
        agents = [self.audit_agent, self.analyze_agent, self.generate_agent, self.validator]
        for agent in agents:
            result = agent.test()
            if not result.success:
                return TestResult(False, f"{agent.__class__.__name__} test failed: {result.message}")

        return TestResult(True, "Orchestrator is operational")

    def execute(self, audit_session: AuditSession) -> AuditSession:
        """
        Execute complete audit process.

        Args:
            audit_session: AuditSession in 'pending' status

        Returns:
            AuditSession in 'completed' or 'failed' status

        Raises:
            ValueError: If audit session is invalid or already completed
        """
        # Validate input
        if not audit_session.validate():
            audit_session.status = "failed"
            return audit_session

        if audit_session.status != "pending":
            raise ValueError(f"Audit session must be pending, got {audit_session.status}")

        try:
            # Update status
            audit_session.status = "running"
            audit_session.touch()

            # Step 1: Generate queries if not provided
            if not audit_session.queries:
                audit_session.queries = self._generate_queries(audit_session)

            # Step 2: Run AuditAgent
            print(f"[Orchestrator] Step 1: Querying AI with {len(audit_session.queries)} queries...")
            results = self.run_agent(
                self.audit_agent,
                {
                    "queries": audit_session.queries,
                    "target_company": audit_session.company_name
                }
            )
            audit_session.results = results

            # Validate results
            if not self.validate_step("audit_results", {"results": results}):
                raise ValueError("Audit results validation failed")

            # Step 3: Run AnalyzeAgent
            print(f"[Orchestrator] Step 2: Analyzing {len(results)} results...")
            analysis = self.run_agent(
                self.analyze_agent,
                {
                    "results": results,
                    "target_company": audit_session.company_name
                }
            )

            # Calculate and set visibility score
            audit_session.visibility_score = self.analyze_agent.calculate_visibility_score(results)

            # Validate analysis
            if not self.validate_step("analysis", {"analysis": analysis}):
                raise ValueError("Analysis validation failed")

            # Step 4: Run GenerateAgent
            print(f"[Orchestrator] Step 3: Generating {len(analysis.visibility_gaps)} recommendations...")
            recommendations = self.run_agent(
                self.generate_agent,
                {"analysis": analysis}
            )

            # Store analysis and recommendations in metadata
            audit_session.metadata["analysis"] = analysis.to_dict()
            audit_session.metadata["recommendations"] = [r.to_dict() for r in recommendations]

            # Validate recommendations
            if not self.validate_step("recommendations", {"recommendations": recommendations}):
                raise ValueError("Recommendations validation failed")

            # Mark as completed
            audit_session.status = "completed"
            audit_session.touch()

            print(f"[Orchestrator] ✅ Audit completed successfully!")
            print(f"  - Visibility score: {audit_session.visibility_score:.1f}/100")
            print(f"  - Competitors identified: {len(analysis.competitors)}")
            print(f"  - Recommendations: {len(recommendations)}")

            return audit_session

        except Exception as e:
            print(f"[Orchestrator] ❌ Error: {e}")
            audit_session.status = "failed"
            audit_session.metadata["error"] = str(e)
            audit_session.touch()
            return audit_session

    def run_agent(self, agent, input_data: Dict[str, Any]) -> Any:
        """
        Run an agent with input data.

        Generic method that calls agent.execute() with appropriate arguments.
        """
        if isinstance(agent, AuditAgent):
            return agent.execute(
                queries=input_data["queries"],
                target_company=input_data["target_company"]
            )
        elif isinstance(agent, AnalyzeAgent):
            return agent.execute(
                results=input_data["results"],
                target_company=input_data["target_company"]
            )
        elif isinstance(agent, GenerateAgent):
            return agent.execute(
                analysis=input_data["analysis"]
            )
        else:
            raise ValueError(f"Unknown agent type: {type(agent)}")

    def validate_step(self, step: str, data: Dict[str, Any]) -> bool:
        """
        Validate a step using Validator.

        Args:
            step: Step name (audit_results, analysis, recommendations)
            data: Data to validate

        Returns:
            True if validation passed, False otherwise
        """
        result: ValidationResult = None

        if step == "audit_results":
            result = self.validator.validate_audit_results(data["results"])
        elif step == "analysis":
            result = self.validator.validate_analysis(data["analysis"])
        elif step == "recommendations":
            result = self.validator.validate_recommendations(data["recommendations"])
        else:
            raise ValueError(f"Unknown validation step: {step}")

        if not result.ok:
            print(f"[Validator] ❌ Validation failed for {step}:")
            for error in result.errors:
                print(f"  - ERROR: {error}")
            for warning in result.warnings:
                print(f"  - WARNING: {warning}")

        return result.ok

    def _generate_queries(self, audit_session: AuditSession) -> list:
        """Generate queries based on sector template and plan."""
        # Determine number of queries based on plan
        query_counts = {
            "freemium": 3,
            "starter": 10,
            "pro": 20,
        }
        count = query_counts.get(audit_session.plan, 3)

        # Generate queries from template
        queries = self.sector_template.generate_queries(
            count=count,
            company=audit_session.company_name,
            location=audit_session.location
        )

        return queries
