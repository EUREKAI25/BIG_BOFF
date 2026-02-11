"""Unit tests for EURKAI core objects."""
import pytest
from src.core.object import Object, TestResult
from src.core.domain.audit_session import AuditSession, AuditResult
from src.core.interface.ai_provider import AIProvider
from src.core.domain.competitor_analysis import CompetitorAnalysis, Competitor, Gap
from src.core.domain.optimization_recommendation import OptimizationRecommendation
from src.core.config.sector_template import SectorTemplate


def test_audit_session_validation():
    """Test AuditSession validation."""
    # Valid audit
    audit = AuditSession(
        company_name="Restaurant Le Bon Goût",
        sector="restaurant",
        location="Paris",
        language="fr",
        plan="freemium"
    )
    assert audit.validate() is True
    assert audit.test().success is True

    # Invalid plan
    invalid_audit = AuditSession(
        company_name="Test",
        sector="restaurant",
        plan="invalid_plan"
    )
    assert invalid_audit.validate() is False


def test_audit_session_score_calculation():
    """Test visibility score calculation."""
    audit = AuditSession(
        company_name="Test Co",
        sector="restaurant",
        plan="freemium"
    )

    # Add mock results
    audit.results = [
        AuditResult("query1", "chatgpt", True, position=1),  # 100 points
        AuditResult("query2", "chatgpt", True, position=4),  # 75 points
        AuditResult("query3", "chatgpt", False),              # 0 points
    ]

    score = audit.generate_score()
    assert score == pytest.approx(58.33, rel=0.01)  # (100+75+0)/3
    assert audit.visibility_score == score


def test_audit_session_serialization():
    """Test to_dict and from_dict."""
    audit = AuditSession(
        company_name="Test Co",
        sector="restaurant",
        location="Paris"
    )
    audit.queries = ["query1", "query2"]

    # Serialize
    data = audit.to_dict()
    assert data["company_name"] == "Test Co"
    assert data["sector"] == "restaurant"
    assert len(data["queries"]) == 2

    # Deserialize
    restored = AuditSession.from_dict(data)
    assert restored.company_name == audit.company_name
    assert restored.sector == audit.sector


def test_ai_provider_validation():
    """Test AIProvider validation."""
    # Valid provider
    provider = AIProvider(
        name="chatgpt",
        api_endpoint="https://api.openai.com/v1/chat/completions",
        model="gpt-4o-mini",
        api_key="sk-test"
    )
    assert provider.validate() is True

    # Invalid name
    invalid = AIProvider(
        name="invalid",
        api_endpoint="https://api.test.com",
        model="test"
    )
    assert invalid.validate() is False


def test_ai_provider_extract_mentions():
    """Test mention extraction."""
    provider = AIProvider(
        name="chatgpt",
        api_endpoint="https://api.openai.com",
        model="gpt-4o-mini"
    )

    text = "Restaurant Le Bon Goût and Café de Paris are great places. Also try Pizza Roma."
    mentions = provider.extract_mentions(text)

    assert "Restaurant Le Bon Goût" in mentions or "Restaurant" in mentions
    assert "Café" in mentions or "Paris" in mentions
    assert len(mentions) > 0


def test_competitor_analysis():
    """Test CompetitorAnalysis."""
    analysis = CompetitorAnalysis(
        target_company="My Restaurant"
    )

    # Add competitors
    analysis.competitors = [
        Competitor("Competitor A", mention_count=5, avg_position=2.0),
        Competitor("Competitor B", mention_count=3, avg_position=4.0),
    ]

    assert analysis.validate() is True

    # Identify gaps
    gaps = analysis.identify_gaps()
    assert len(gaps) > 0
    assert any(g.type == "authority" for g in gaps)

    # Rank competitors
    ranked = analysis.rank_competitors()
    assert ranked[0].name == "Competitor A"  # Most mentions


def test_optimization_recommendation():
    """Test OptimizationRecommendation."""
    rec = OptimizationRecommendation(
        type="structured_data",
        title="Add Schema.org markup",
        description="Improve structured data",
        priority=1,
        content={"test": "data"},
        integration_guide="Insert in <head>",
        estimated_impact="high"
    )

    assert rec.validate() is True
    assert rec.test().success is True

    # Generate content
    rec_generated = rec.generate({"company_name": "Test Co"})
    assert rec_generated.content is not None
    assert "@context" in str(rec_generated.content)

    # Export
    html = rec.export("html")
    assert "Schema.org" in html


def test_sector_template():
    """Test SectorTemplate."""
    template = SectorTemplate.get_restaurant_template()

    assert template.validate() is True
    assert template.test().success is True
    assert template.sector_id == "restaurant"

    # Generate queries
    queries = template.generate_queries(5, company="Le Bon Goût", location="Paris")
    assert len(queries) == 5
    assert any("Paris" in q for q in queries)
    assert any("Le Bon Goût" in q for q in queries)

    # Customize
    custom = template.customize("My Restaurant", "Lyon")
    assert any("My Restaurant" in q for q in custom)
    assert any("Lyon" in q for q in custom)


def test_all_objects_inherit_from_object():
    """Test that all objects properly inherit from Object base class."""
    audit = AuditSession("Test", "restaurant")
    provider = AIProvider("chatgpt", "https://api.test.com", "gpt-4o")
    analysis = CompetitorAnalysis("Test Co")
    rec = OptimizationRecommendation("content", "Test", priority=1)
    template = SectorTemplate("test", {"fr": "Test"}, ["q1"], ["s1"], ["k1"])

    for obj in [audit, provider, analysis, rec, template]:
        assert isinstance(obj, Object)
        assert hasattr(obj, 'ident')
        assert hasattr(obj, 'created_at')
        assert hasattr(obj, 'validate')
        assert hasattr(obj, 'test')
        assert hasattr(obj, 'to_dict')
        assert callable(obj.validate)
        assert callable(obj.test)
