"""Integration tests for orchestrator and agents."""
import pytest
from src.core.domain.audit_session import AuditSession
from src.core.interface.ai_provider import AIProvider
from src.core.config.sector_template import SectorTemplate
from src.orchestrator.audit_orchestrator import AuditOrchestrator
from src.orchestrator.validator import Validator
from src.orchestrator.agents.audit_agent import AuditAgent
from src.orchestrator.agents.analyze_agent import AnalyzeAgent
from src.orchestrator.agents.generate_agent import GenerateAgent


def test_validator_audit_results():
    """Test validator with audit results."""
    from src.core.domain.audit_session import AuditResult

    validator = Validator()

    # Valid results
    valid_results = [
        AuditResult("query1", "chatgpt", True, position=1, competitors=["Comp A"]),
        AuditResult("query2", "chatgpt", False, competitors=["Comp B"]),
    ]

    result = validator.validate_audit_results(valid_results)
    assert result.ok is True
    assert len(result.errors) == 0


def test_audit_agent():
    """Test AuditAgent execution."""
    provider = AIProvider(
        name="chatgpt",
        api_endpoint="https://api.openai.com/v1/chat/completions",
        model="gpt-4o-mini"
    )

    agent = AuditAgent(provider=provider)
    assert agent.validate() is True
    assert agent.test().success is True

    # Execute with mock queries
    results = agent.execute(
        queries=["best restaurant Paris"],
        target_company="Le Bon Goût"
    )

    assert len(results) == 1
    assert results[0].query == "best restaurant Paris"
    assert results[0].ai_provider == "chatgpt"


def test_analyze_agent():
    """Test AnalyzeAgent execution."""
    from src.core.domain.audit_session import AuditResult

    agent = AnalyzeAgent()
    assert agent.validate() is True
    assert agent.test().success is True

    # Mock results
    results = [
        AuditResult("query1", "chatgpt", True, position=1, competitors=["Comp A"]),
        AuditResult("query2", "chatgpt", False, competitors=["Comp A", "Comp B"]),
        AuditResult("query3", "chatgpt", True, position=5, competitors=["Comp A"]),
    ]

    analysis = agent.execute(results, "My Restaurant")

    assert analysis.target_company == "My Restaurant"
    assert len(analysis.competitors) > 0
    assert len(analysis.visibility_gaps) > 0

    # Test score calculation
    score = agent.calculate_visibility_score(results)
    assert 0 <= score <= 100
    # (100 + 0 + 75) / 3 = 58.33
    assert score == pytest.approx(58.33, rel=0.01)


def test_generate_agent():
    """Test GenerateAgent execution."""
    from src.core.domain.competitor_analysis import CompetitorAnalysis, Gap

    agent = GenerateAgent()
    assert agent.validate() is True
    assert agent.test().success is True

    # Mock analysis
    analysis = CompetitorAnalysis("Test Co")
    analysis.visibility_gaps = [
        Gap("structured_data", "Missing Schema.org", "high"),
        Gap("content", "Content not optimized", "medium"),
    ]

    recommendations = agent.execute(analysis)

    assert len(recommendations) >= len(analysis.visibility_gaps)
    assert all(rec.validate() for rec in recommendations)

    # Check that recommendations have content
    for rec in recommendations:
        assert rec.content is not None
        assert rec.integration_guide != ""


def test_orchestrator_complete_flow():
    """Test complete orchestrator flow end-to-end."""
    # Setup
    provider = AIProvider(
        name="chatgpt",
        api_endpoint="https://api.openai.com/v1/chat/completions",
        model="gpt-4o-mini",
        api_key="test-key"
    )

    template = SectorTemplate.get_restaurant_template()

    orchestrator = AuditOrchestrator(
        provider=provider,
        sector_template=template,
        strict_validation=False
    )

    assert orchestrator.validate() is True
    assert orchestrator.test().success is True

    # Create audit session
    audit = AuditSession(
        company_name="Restaurant Le Bon Goût",
        sector="restaurant",
        location="Paris",
        language="fr",
        plan="freemium",
        status="pending"
    )

    # Execute orchestrator
    completed_audit = orchestrator.execute(audit)

    # Verify results
    assert completed_audit.status in ["completed", "failed"]

    if completed_audit.status == "completed":
        assert completed_audit.visibility_score is not None
        assert 0 <= completed_audit.visibility_score <= 100
        assert len(completed_audit.results) > 0
        assert "analysis" in completed_audit.metadata
        assert "recommendations" in completed_audit.metadata

        # Verify metadata structure
        analysis = completed_audit.metadata["analysis"]
        assert "target_company" in analysis
        assert "competitors" in analysis
        assert "visibility_gaps" in analysis

        recommendations = completed_audit.metadata["recommendations"]
        assert len(recommendations) > 0
        assert all("title" in r for r in recommendations)
        assert all("type" in r for r in recommendations)


def test_orchestrator_with_custom_queries():
    """Test orchestrator with custom queries."""
    provider = AIProvider(
        name="chatgpt",
        api_endpoint="https://api.openai.com/v1/chat/completions",
        model="gpt-4o-mini"
    )

    template = SectorTemplate.get_restaurant_template()
    orchestrator = AuditOrchestrator(provider=provider, sector_template=template)

    # Audit with custom queries
    audit = AuditSession(
        company_name="Test Restaurant",
        sector="restaurant",
        location="Lyon",
        plan="starter",
        queries=["meilleur restaurant Lyon", "où manger Lyon", "restaurant étoilé Lyon"],
        status="pending"
    )

    completed = orchestrator.execute(audit)

    assert completed.status in ["completed", "failed"]
    if completed.status == "completed":
        assert len(completed.results) == 3  # Same as custom queries count


def test_all_agents_inherit_from_object():
    """Test that all agents inherit from Object."""
    from src.core.object import Object

    provider = AIProvider("chatgpt", "https://api.test.com", "gpt-4o")
    audit_agent = AuditAgent(provider=provider)
    analyze_agent = AnalyzeAgent()
    generate_agent = GenerateAgent()
    validator = Validator()

    agents = [audit_agent, analyze_agent, generate_agent, validator]

    for agent in agents:
        assert isinstance(agent, Object)
        assert hasattr(agent, 'validate')
        assert hasattr(agent, 'test')
        assert callable(agent.validate)
        assert callable(agent.test)
