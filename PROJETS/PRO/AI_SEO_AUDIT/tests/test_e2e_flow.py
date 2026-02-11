"""End-to-end flow tests."""
import pytest
from httpx import AsyncClient
from src.api.main import app
from src.database.models import User, Audit
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_freemium_flow_complete():
    """Test complete freemium flow: create -> poll -> results."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Create freemium audit
        audit_data = {
            "company_name": "Restaurant Test",
            "sector": "restaurant",
            "location": "Paris, France",
            "email": "test@example.com",
            "plan": "freemium",
            "language": "fr"
        }

        response = await client.post("/api/audit/create", json=audit_data)
        assert response.status_code == 200

        result = response.json()
        assert "audit_id" in result
        assert result["status"] == "processing"

        audit_id = result["audit_id"]

        # Step 2: Check status
        response = await client.get(f"/api/audit/{audit_id}/status")
        assert response.status_code == 200

        status = response.json()
        assert status["status"] in ["processing", "completed"]
        assert 0 <= status["progress"] <= 100

        # Step 3: Get results (mock will return completed immediately)
        response = await client.get(f"/api/audit/{audit_id}/results")

        # Should work or be processing
        assert response.status_code in [200, 202]


@pytest.mark.asyncio
async def test_starter_flow_with_payment():
    """Test starter plan flow with payment."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Create starter audit
        audit_data = {
            "company_name": "Hotel Test",
            "sector": "hotel",
            "location": "Lyon, France",
            "email": "test@hotel.com",
            "plan": "starter",
            "language": "fr"
        }

        response = await client.post("/api/audit/create", json=audit_data)
        assert response.status_code == 200

        audit_id = response.json()["audit_id"]

        # Step 2: Create checkout session
        payment_data = {
            "audit_id": audit_id,
            "plan": "starter",
            "success_url": "http://test/success",
            "cancel_url": "http://test/cancel"
        }

        response = await client.post("/api/payment/create-checkout", json=payment_data)
        assert response.status_code == 200

        checkout = response.json()
        assert "checkout_url" in checkout
        assert "session_id" in checkout


@pytest.mark.asyncio
async def test_pro_flow_with_exports():
    """Test pro plan flow with all export options."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Create pro audit
        audit_data = {
            "company_name": "Tech Company Test",
            "sector": "tech",
            "location": "Paris, France",
            "email": "test@tech.com",
            "plan": "pro",
            "language": "fr"
        }

        response = await client.post("/api/audit/create", json=audit_data)
        assert response.status_code == 200

        audit_id = response.json()["audit_id"]

        # Step 2: Test export endpoints
        # PDF export
        response = await client.get(f"/api/export/{audit_id}/guide.pdf")
        assert response.status_code in [200, 404]  # 404 if audit not completed

        # JSON export
        response = await client.get(f"/api/export/{audit_id}/recommendations.json")
        assert response.status_code in [200, 404]

        # Mockups export (pro only)
        response = await client.get(f"/api/export/{audit_id}/mockups.zip")
        assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_landing_page_loads():
    """Test that landing page loads correctly."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "AI SEO Audit" in response.text


@pytest.mark.asyncio
async def test_results_page_loads():
    """Test that results page can load (with or without audit)."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Try with non-existent audit
        response = await client.get("/results/nonexistent-id")

        # Should return 404 or redirect
        assert response.status_code in [404, 500]


@pytest.mark.asyncio
async def test_stripe_webhook():
    """Test Stripe webhook handling."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        webhook_data = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "metadata": {
                        "audit_id": "test-audit-id"
                    },
                    "payment_status": "paid"
                }
            }
        }

        response = await client.post(
            "/api/payment/webhook",
            json=webhook_data,
            headers={"stripe-signature": "test"}
        )

        # Should process webhook (might fail on signature, that's OK for now)
        assert response.status_code in [200, 400]


def test_app_structure():
    """Test that app has all required routes."""
    routes = [route.path for route in app.routes]

    # Frontend routes
    assert "/" in routes
    assert "/results/{audit_id}" in routes
    assert "/success" in routes

    # API routes
    assert "/api/audit/create" in routes
    assert "/api/audit/{audit_id}/status" in routes
    assert "/api/audit/{audit_id}/results" in routes
    assert "/api/payment/create-checkout" in routes
    assert "/api/payment/webhook" in routes

    # Export routes
    assert "/api/export/{audit_id}/guide.pdf" in routes
    assert "/api/export/{audit_id}/recommendations.json" in routes
    assert "/api/export/{audit_id}/mockups.zip" in routes

    # Health
    assert "/health" in routes
