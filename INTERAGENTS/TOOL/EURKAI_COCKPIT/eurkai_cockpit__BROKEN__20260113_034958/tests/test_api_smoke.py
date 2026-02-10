"""
EURKAI_COCKPIT — API Smoke Tests
Version: 1.0.0

Quick validation that all endpoints are functional.
Run: pytest tests/test_api_smoke.py -v
"""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# Set test environment before imports
@pytest.fixture(scope="module", autouse=True)
def setup_test_env():
    """Setup test environment with temp database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_cockpit.db"
        os.environ["EURKAI_DB_PATH"] = str(db_path)
        os.environ["EURKAI_MASTER_PASSWORD"] = "test_master_password_123"
        os.environ["EURKAI_TOKEN"] = ""  # Disable auth for tests
        
        # Clear cached storage
        from backend.api.deps import get_storage
        get_storage.cache_clear()
        
        yield
        
        get_storage.cache_clear()


@pytest.fixture
def client(setup_test_env):
    """Create test client."""
    from backend.app import app
    return TestClient(app)


class TestHealth:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["success"] is True
    
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200


class TestProjects:
    def test_create_and_list(self, client):
        # Create
        r = client.post("/api/projects", json={"name": "Test Project", "description": "Test"})
        assert r.status_code == 201
        project = r.json()["data"]
        assert project["name"] == "Test Project"
        project_id = project["id"]
        
        # Get
        r = client.get(f"/api/projects/{project_id}")
        assert r.status_code == 200
        
        # Update
        r = client.put(f"/api/projects/{project_id}", json={"name": "Updated"})
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "Updated"
        
        # List
        r = client.get("/api/projects")
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 1
        
        # Delete
        r = client.delete(f"/api/projects/{project_id}")
        assert r.status_code == 204
    
    def test_not_found(self, client):
        r = client.get("/api/projects/nonexistent")
        assert r.status_code == 404
    
    def test_validation_error(self, client):
        r = client.post("/api/projects", json={})
        assert r.status_code == 422


class TestBriefs:
    def test_crud(self, client):
        # Create project first
        r = client.post("/api/projects", json={"name": "Brief Test Project"})
        project_id = r.json()["data"]["id"]
        
        # Create brief
        r = client.post("/api/briefs", json={
            "project_id": project_id,
            "title": "Test Brief",
            "user_prompt": "Do something",
            "tags": ["test"]
        })
        assert r.status_code == 201
        brief = r.json()["data"]
        brief_id = brief["id"]
        assert brief["title"] == "Test Brief"
        assert brief["tags"] == ["test"]
        
        # List with filter
        r = client.get(f"/api/briefs?project_id={project_id}")
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 1
        
        # Update
        r = client.put(f"/api/briefs/{brief_id}", json={"title": "Updated Brief"})
        assert r.status_code == 200
        
        # Trigger run
        r = client.post(f"/api/briefs/{brief_id}/run")
        assert r.status_code == 202
        run_id = r.json()["data"]["run_id"]
        
        # List runs
        r = client.get(f"/api/briefs/{brief_id}/runs")
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 1
        
        # Get run
        r = client.get(f"/api/runs/{run_id}")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "pending"
        
        # Delete run
        r = client.delete(f"/api/runs/{run_id}")
        assert r.status_code == 204
        
        # Delete brief
        r = client.delete(f"/api/briefs/{brief_id}")
        assert r.status_code == 204
        
        # Cleanup
        client.delete(f"/api/projects/{project_id}")
    
    def test_invalid_project(self, client):
        r = client.post("/api/briefs", json={
            "project_id": "nonexistent",
            "title": "Test",
            "user_prompt": "Test"
        })
        assert r.status_code == 400


class TestConfig:
    def test_crud(self, client):
        # Set config
        r = client.put("/api/config/test_key", json={"value": "test_value"})
        assert r.status_code == 200
        
        # List
        r = client.get("/api/config")
        assert r.status_code == 200
        configs = r.json()["data"]
        assert any(c["key"] == "test_key" for c in configs)


class TestSecrets:
    def test_crud_and_unlock(self, client):
        # Create secret
        r = client.post("/api/secrets", json={
            "key": "API_KEY",
            "value": "super_secret_123"
        })
        assert r.status_code == 201
        secret = r.json()["data"]
        secret_id = secret["id"]
        assert "value" not in secret  # Never exposed
        
        # List (no values)
        r = client.get("/api/secrets")
        assert r.status_code == 200
        secrets = r.json()["data"]
        assert all("value_encrypted" not in s for s in secrets)
        
        # Copy without session = 401
        r = client.get(f"/api/secrets/{secret_id}/copy")
        assert r.status_code == 401
        
        # Unlock
        r = client.post("/api/secrets/unlock", json={
            "master_password": "test_master_password_123"
        })
        assert r.status_code == 200
        session_token = r.json()["data"]["session_token"]
        
        # Copy with session
        r = client.get(
            f"/api/secrets/{secret_id}/copy",
            headers={"X-Session-Token": session_token}
        )
        assert r.status_code == 200
        assert r.json()["data"]["value"] == "super_secret_123"
        
        # Update
        r = client.put(f"/api/secrets/{secret_id}", json={"value": "new_secret"})
        assert r.status_code == 200
        
        # Delete
        r = client.delete(f"/api/secrets/{secret_id}")
        assert r.status_code == 204
    
    def test_wrong_password(self, client):
        r = client.post("/api/secrets/unlock", json={
            "master_password": "wrong_password"
        })
        assert r.status_code == 400


class TestModules:
    def test_crud_and_compatibility(self, client):
        # Register module A
        r = client.post("/api/modules", json={
            "name": "text-processor",
            "version": "1.0.0",
            "description": "Processes text",
            "inputs": [
                {"name": "text", "type": "string", "required": True}
            ],
            "outputs": [
                {"name": "result", "type": "object"}
            ],
            "tags": ["nlp"]
        })
        assert r.status_code == 201
        module_a = r.json()["data"]
        
        # Register module B
        r = client.post("/api/modules", json={
            "name": "report-builder",
            "version": "1.0.0",
            "inputs": [
                {"name": "data", "type": "object", "required": True}
            ],
            "outputs": [
                {"name": "report", "type": "file"}
            ]
        })
        assert r.status_code == 201
        module_b = r.json()["data"]
        
        # Check compatibility
        r = client.get("/api/modules/compatible?from=text-processor&to=report-builder")
        assert r.status_code == 200
        compat = r.json()["data"]
        assert compat["compatible"] is True
        assert len(compat["mappings"]) == 1
        
        # Update module (version bump)
        r = client.post("/api/modules", json={
            "name": "text-processor",
            "version": "1.1.0",
            "description": "Updated"
        })
        assert r.status_code == 201
        
        # Same version = conflict
        r = client.post("/api/modules", json={
            "name": "text-processor",
            "version": "1.1.0"
        })
        assert r.status_code == 409
        
        # Delete
        client.delete(f"/api/modules/{module_a['id']}")
        client.delete(f"/api/modules/{module_b['id']}")
    
    def test_validation(self, client):
        # Invalid name
        r = client.post("/api/modules", json={
            "name": "INVALID",
            "version": "1.0.0"
        })
        assert r.status_code == 422
        
        # Invalid version
        r = client.post("/api/modules", json={
            "name": "valid-name",
            "version": "not-semver"
        })
        assert r.status_code == 422


class TestBackups:
    def test_dry_run(self, client):
        r = client.post("/api/backups/dry-run")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["status"] == "dry_run"
        assert "files" in data
    
    def test_list(self, client):
        r = client.get("/api/backups")
        assert r.status_code == 200


class TestResponseContract:
    """Verify C01 response contract compliance."""
    
    def test_success_format(self, client):
        r = client.get("/api/projects")
        data = r.json()
        assert "success" in data
        assert "data" in data
        assert "meta" in data
        assert "timestamp" in data["meta"]
        assert "version" in data["meta"]
    
    def test_error_format(self, client):
        r = client.get("/api/projects/nonexistent-id")
        data = r.json()
        assert data["success"] is False
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "meta" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
