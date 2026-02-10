"""
EURKAI_COCKPIT — E2E Smoke Tests (C08)
Version: 1.0.0

End-to-end validation tests that verify:
- Full user journey: project → brief → run
- API integration
- CLI integration (if available)
- Database persistence

These tests are designed to validate a fresh installation.

Run: pytest tests/test_e2e_smoke.py -v
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def e2e_env():
    """Setup E2E test environment with isolated database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "e2e_test.db"
        
        # Set environment
        os.environ["EURKAI_DB_PATH"] = str(db_path)
        os.environ["EURKAI_MASTER_PASSWORD"] = "e2e_test_password_123"
        os.environ["EURKAI_TOKEN"] = ""  # Disable auth
        
        # Clear cached storage if any
        try:
            from backend.api.deps import get_storage
            get_storage.cache_clear()
        except ImportError:
            pass
        
        yield {
            "db_path": db_path,
            "tmpdir": tmpdir
        }
        
        # Cleanup
        try:
            from backend.api.deps import get_storage
            get_storage.cache_clear()
        except ImportError:
            pass


@pytest.fixture
def api_client(e2e_env):
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient
    from backend.app import app
    return TestClient(app)


# =============================================================================
# E2E TEST: FULL USER JOURNEY
# =============================================================================

class TestE2EUserJourney:
    """
    Complete user journey test:
    1. Create project
    2. Create brief in project
    3. Trigger run
    4. Check run status
    5. Cleanup
    """
    
    def test_full_journey(self, api_client):
        """Test complete workflow: project → brief → run."""
        
        # Step 1: Create Project
        response = api_client.post("/api/projects", json={
            "name": "E2E Test Project",
            "description": "Created by E2E smoke test"
        })
        assert response.status_code == 201, f"Project creation failed: {response.text}"
        
        project_data = response.json()
        assert project_data["success"] is True
        project_id = project_data["data"]["id"]
        assert project_id is not None
        
        # Step 2: Verify project exists
        response = api_client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "E2E Test Project"
        
        # Step 3: Create Brief
        response = api_client.post("/api/briefs", json={
            "project_id": project_id,
            "title": "E2E Test Brief",
            "user_prompt": "This is a test prompt for E2E validation",
            "tags": ["e2e", "smoke-test"]
        })
        assert response.status_code == 201, f"Brief creation failed: {response.text}"
        
        brief_data = response.json()
        brief_id = brief_data["data"]["id"]
        assert brief_id is not None
        
        # Step 4: List briefs for project
        response = api_client.get(f"/api/briefs?project_id={project_id}")
        assert response.status_code == 200
        briefs = response.json()["data"]
        assert len(briefs) >= 1
        assert any(b["id"] == brief_id for b in briefs)
        
        # Step 5: Trigger Run
        response = api_client.post(f"/api/briefs/{brief_id}/run")
        assert response.status_code == 202, f"Run trigger failed: {response.text}"
        
        run_data = response.json()
        run_id = run_data["data"]["run_id"]
        assert run_id is not None
        
        # Step 6: Check Run Status
        response = api_client.get(f"/api/runs/{run_id}")
        assert response.status_code == 200
        
        run = response.json()["data"]
        assert run["status"] in ["pending", "running", "success", "failed"]
        assert run["brief_id"] == brief_id
        
        # Step 7: List runs for brief
        response = api_client.get(f"/api/briefs/{brief_id}/runs")
        assert response.status_code == 200
        runs = response.json()["data"]
        assert len(runs) >= 1
        
        # Step 8: Cleanup - Delete run
        response = api_client.delete(f"/api/runs/{run_id}")
        assert response.status_code == 204
        
        # Step 9: Cleanup - Delete brief
        response = api_client.delete(f"/api/briefs/{brief_id}")
        assert response.status_code == 204
        
        # Step 10: Cleanup - Delete project
        response = api_client.delete(f"/api/projects/{project_id}")
        assert response.status_code == 204
        
        # Verify cleanup
        response = api_client.get(f"/api/projects/{project_id}")
        assert response.status_code == 404


# =============================================================================
# E2E TEST: API HEALTH
# =============================================================================

class TestE2EHealth:
    """Verify API is healthy and responsive."""
    
    def test_root_endpoint(self, api_client):
        """Root endpoint returns success."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "EURKAI_COCKPIT"
    
    def test_health_endpoint(self, api_client):
        """Health check returns OK."""
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_docs_available(self, api_client):
        """OpenAPI docs are accessible."""
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        openapi = response.json()
        assert "paths" in openapi
        assert "/api/projects" in openapi["paths"]


# =============================================================================
# E2E TEST: CONFIG
# =============================================================================

class TestE2EConfig:
    """Test configuration management."""
    
    def test_config_crud(self, api_client):
        """Config set and get works."""
        # Set config
        response = api_client.put("/api/config/e2e_test_key", json={
            "value": "e2e_test_value"
        })
        assert response.status_code == 200
        
        # List config
        response = api_client.get("/api/config")
        assert response.status_code == 200
        configs = response.json()["data"]
        assert any(c["key"] == "e2e_test_key" for c in configs)


# =============================================================================
# E2E TEST: SECRETS (GATED)
# =============================================================================

class TestE2ESecrets:
    """Test secrets with gated copy."""
    
    def test_secret_workflow(self, api_client):
        """Full secrets workflow: create → list (no value) → unlock → copy."""
        
        # Create secret
        response = api_client.post("/api/secrets", json={
            "key": "E2E_API_KEY",
            "value": "super_secret_e2e_value"
        })
        assert response.status_code == 201
        secret = response.json()["data"]
        secret_id = secret["id"]
        
        # Verify value not in response
        assert "value" not in secret
        assert "value_encrypted" not in secret
        
        # List secrets - no values exposed
        response = api_client.get("/api/secrets")
        assert response.status_code == 200
        secrets = response.json()["data"]
        for s in secrets:
            assert "value" not in s
            assert "value_encrypted" not in s
        
        # Try copy without session - should fail
        response = api_client.get(f"/api/secrets/{secret_id}/copy")
        assert response.status_code == 401
        
        # Unlock with master password
        response = api_client.post("/api/secrets/unlock", json={
            "master_password": "e2e_test_password_123"
        })
        assert response.status_code == 200
        session_token = response.json()["data"]["session_token"]
        
        # Copy with session - should succeed
        response = api_client.get(
            f"/api/secrets/{secret_id}/copy",
            headers={"X-Session-Token": session_token}
        )
        assert response.status_code == 200
        assert response.json()["data"]["value"] == "super_secret_e2e_value"
        
        # Cleanup
        response = api_client.delete(f"/api/secrets/{secret_id}")
        assert response.status_code == 204


# =============================================================================
# E2E TEST: MODULES REGISTRY
# =============================================================================

class TestE2EModules:
    """Test module registry."""
    
    def test_module_registration(self, api_client):
        """Register and query module."""
        
        # Register module
        response = api_client.post("/api/modules", json={
            "name": "e2e-test-module",
            "version": "1.0.0",
            "description": "E2E test module",
            "inputs": [
                {"name": "input_text", "type": "string", "required": True}
            ],
            "outputs": [
                {"name": "result", "type": "object"}
            ],
            "tags": ["e2e", "test"]
        })
        assert response.status_code == 201
        module = response.json()["data"]
        module_id = module["id"]
        
        # List modules
        response = api_client.get("/api/modules")
        assert response.status_code == 200
        modules = response.json()["data"]
        assert any(m["name"] == "e2e-test-module" for m in modules)
        
        # Get by name
        response = api_client.get("/api/modules/name/e2e-test-module")
        assert response.status_code == 200
        
        # Cleanup
        response = api_client.delete(f"/api/modules/{module_id}")
        assert response.status_code == 204


# =============================================================================
# E2E TEST: BACKUP DRY-RUN
# =============================================================================

class TestE2EBackup:
    """Test backup functionality."""
    
    def test_backup_dry_run(self, api_client):
        """Backup dry-run creates local files."""
        response = api_client.post("/api/backups/dry-run")
        assert response.status_code == 200
        
        data = response.json()["data"]
        assert data["status"] == "dry_run"
        assert "files" in data
    
    def test_backup_list(self, api_client):
        """Can list backups."""
        response = api_client.get("/api/backups")
        assert response.status_code == 200
        # May be empty, just verify endpoint works


# =============================================================================
# E2E TEST: RESPONSE CONTRACT
# =============================================================================

class TestE2EResponseContract:
    """Verify all responses follow C01 contract."""
    
    def test_success_response_format(self, api_client):
        """Success responses have correct structure."""
        response = api_client.get("/api/projects")
        data = response.json()
        
        # Required fields
        assert "success" in data
        assert "data" in data
        assert "meta" in data
        
        # Meta structure
        assert "timestamp" in data["meta"]
        assert "version" in data["meta"]
    
    def test_error_response_format(self, api_client):
        """Error responses have correct structure."""
        response = api_client.get("/api/projects/nonexistent-id-12345")
        assert response.status_code == 404
        
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "meta" in data


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
