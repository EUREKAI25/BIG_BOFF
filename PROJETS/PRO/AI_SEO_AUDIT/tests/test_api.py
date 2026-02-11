"""API endpoint tests."""
import pytest
from httpx import AsyncClient
from src.api.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-seo-audit-api"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint returns HTML."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AI SEO Audit" in response.text


@pytest.mark.asyncio
async def test_api_docs():
    """Test API documentation is available."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/docs")

    assert response.status_code == 200


# Note: Full API tests require database setup
# These will be completed in Phase 6 (Tests & Deploy)
# For now, we verify that routes are registered correctly

def test_api_routes_registered():
    """Test that all API routes are registered."""
    routes = [route.path for route in app.routes]

    # Check audit routes
    assert "/api/audit/create" in routes
    assert "/api/audit/{audit_id}/status" in routes
    assert "/api/audit/{audit_id}/results" in routes

    # Check payment routes
    assert "/api/payment/create-checkout" in routes
    assert "/api/payment/webhook" in routes

    # Check export routes
    assert "/api/export/{audit_id}/guide.pdf" in routes
    assert "/api/export/{audit_id}/recommendations.json" in routes
    assert "/api/export/{audit_id}/mockups.zip" in routes
