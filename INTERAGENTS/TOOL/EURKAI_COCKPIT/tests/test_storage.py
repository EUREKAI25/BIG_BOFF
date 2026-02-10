"""
EURKAI_COCKPIT — Storage Tests
Version: 1.0.0

Comprehensive tests for storage layer:
- CRUD operations for all entities
- Encryption/decryption
- Idempotent initialization
- Cascade deletes
- JSON validation
"""

import json
import os
import pytest
import tempfile
from pathlib import Path

# Set encryption key before imports
TEST_ENCRYPTION_KEY = "dGVzdC1rZXktMzItYnl0ZXMtbG9uZy1mb3ItdGVzdGluZw=="  # Base64 32-byte key
os.environ["EURKAI_SECRET_KEY"] = "8B8vXQ3qZ2xq2z5x5Y9kL3mN6pR9sT2w4A7cF0hJ1kL="  # Valid Fernet key

from backend.storage import (
    Storage,
    Project,
    Brief,
    Run,
    Config,
    Secret,
    ModuleManifest,
    Module,
    Backup,
    SecretEncryption,
    generate_uuid,
    utc_now,
    init_database,
    get_schema_version,
    SCHEMA_VERSION,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def temp_db():
    """Create temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def storage(temp_db):
    """Create initialized storage instance."""
    s = Storage(temp_db)
    s.init_db()
    return s


@pytest.fixture
def project(storage):
    """Create test project."""
    return storage.create_project(
        name="Test Project",
        description="A test project",
        root_path="/tmp/test",
        tags=["test", "demo"]
    )


@pytest.fixture
def brief(storage, project):
    """Create test brief."""
    return storage.create_brief(
        project_id=project.id,
        title="Test Brief",
        user_prompt="Test the system",
        goal="Verify functionality",
        system_prompt="You are a tester",
        tags=["test"]
    )


# ============================================
# INITIALIZATION TESTS
# ============================================

class TestInitialization:
    """Test database initialization."""
    
    def test_init_creates_database(self, temp_db):
        """Database file created on init."""
        storage = Storage(temp_db)
        storage.init_db()
        assert temp_db.exists()
    
    def test_init_idempotent(self, temp_db):
        """Multiple init calls don't error."""
        storage = Storage(temp_db)
        storage.init_db()
        storage.init_db()  # Second call should work
        storage.init_db()  # Third call should work
        assert temp_db.exists()
    
    def test_init_database_function(self, temp_db):
        """init_database() helper works."""
        storage = init_database(temp_db)
        version = get_schema_version(temp_db)
        assert version == SCHEMA_VERSION
    
    def test_schema_version_stored(self, temp_db):
        """Schema version stored in config."""
        init_database(temp_db)
        version = get_schema_version(temp_db)
        assert version == SCHEMA_VERSION


# ============================================
# PROJECT TESTS
# ============================================

class TestProjects:
    """Test project CRUD operations."""
    
    def test_create_project(self, storage):
        """Create project with all fields."""
        project = storage.create_project(
            name="My Project",
            description="Description",
            root_path="/path/to/project",
            tags=["tag1", "tag2"]
        )
        
        assert project.id is not None
        assert len(project.id) == 36  # UUID format
        assert project.name == "My Project"
        assert project.description == "Description"
        assert project.root_path == "/path/to/project"
        assert project.tags == ["tag1", "tag2"]
        assert project.created_at is not None
        assert project.updated_at is not None
    
    def test_get_project(self, storage, project):
        """Retrieve project by ID."""
        retrieved = storage.get_project(project.id)
        assert retrieved is not None
        assert retrieved.id == project.id
        assert retrieved.name == project.name
    
    def test_get_nonexistent_project(self, storage):
        """Get returns None for missing project."""
        assert storage.get_project("nonexistent") is None
    
    def test_list_projects(self, storage):
        """List all projects."""
        storage.create_project(name="Project 1")
        storage.create_project(name="Project 2")
        
        projects = storage.list_projects()
        assert len(projects) == 2
    
    def test_update_project(self, storage, project):
        """Update project fields."""
        updated = storage.update_project(
            project.id,
            name="Updated Name",
            tags=["new", "tags"]
        )
        
        assert updated.name == "Updated Name"
        assert updated.tags == ["new", "tags"]
        # Verify update persisted
        refetched = storage.get_project(project.id)
        assert refetched.name == "Updated Name"
        assert refetched.tags == ["new", "tags"]
    
    def test_delete_project(self, storage, project):
        """Delete project."""
        assert storage.delete_project(project.id) is True
        assert storage.get_project(project.id) is None
    
    def test_delete_nonexistent_project(self, storage):
        """Delete returns False for missing project."""
        assert storage.delete_project("nonexistent") is False


# ============================================
# BRIEF TESTS
# ============================================

class TestBriefs:
    """Test brief CRUD operations."""
    
    def test_create_brief(self, storage, project):
        """Create brief with all fields."""
        brief = storage.create_brief(
            project_id=project.id,
            title="Test Brief",
            user_prompt="Do something",
            goal="Test goal",
            system_prompt="You are helpful",
            variables_json={"key": "value"},
            expected_output="Success",
            tags=["test"],
            policy={"passes_in_a_row": 3, "max_iters": 10}
        )
        
        assert brief.id is not None
        assert brief.project_id == project.id
        assert brief.title == "Test Brief"
        assert brief.user_prompt == "Do something"
        assert brief.goal == "Test goal"
        assert brief.variables_json == {"key": "value"}
        assert brief.policy == {"passes_in_a_row": 3, "max_iters": 10}
    
    def test_brief_requires_project_id(self, storage):
        """Brief creation requires valid project_id."""
        with pytest.raises(Exception):  # Foreign key constraint
            storage.create_brief(
                project_id="nonexistent",
                title="Test",
                user_prompt="Test"
            )
    
    def test_list_briefs_by_project(self, storage, project):
        """List briefs filtered by project."""
        storage.create_brief(project_id=project.id, title="Brief 1", user_prompt="Test")
        storage.create_brief(project_id=project.id, title="Brief 2", user_prompt="Test")
        
        briefs = storage.list_briefs(project_id=project.id)
        assert len(briefs) == 2
    
    def test_update_brief(self, storage, brief):
        """Update brief fields."""
        updated = storage.update_brief(
            brief.id,
            title="New Title",
            goal="New Goal"
        )
        
        assert updated.title == "New Title"
        assert updated.goal == "New Goal"
    
    def test_delete_brief(self, storage, brief):
        """Delete brief."""
        assert storage.delete_brief(brief.id) is True
        assert storage.get_brief(brief.id) is None
    
    def test_cascade_delete_briefs(self, storage, project, brief):
        """Deleting project cascades to briefs."""
        brief_id = brief.id
        storage.delete_project(project.id)
        assert storage.get_brief(brief_id) is None


# ============================================
# RUN TESTS
# ============================================

class TestRuns:
    """Test run CRUD operations."""
    
    def test_create_run(self, storage, brief):
        """Create run with all fields."""
        run = storage.create_run(
            brief_id=brief.id,
            run_id="custom-run-123",
            status="pending",
            model="claude-3"
        )
        
        assert run.id is not None
        assert run.run_id == "custom-run-123"
        assert run.brief_id == brief.id
        assert run.status == "pending"
        assert run.model == "claude-3"
    
    def test_create_run_auto_run_id(self, storage, brief):
        """Run ID generated if not provided."""
        run = storage.create_run(brief_id=brief.id)
        assert run.run_id is not None
        assert len(run.run_id) == 36
    
    def test_get_run_by_id_or_run_id(self, storage, brief):
        """Get run by primary ID or run_id."""
        run = storage.create_run(brief_id=brief.id, run_id="my-run")
        
        by_id = storage.get_run(run.id)
        by_run_id = storage.get_run("my-run")
        
        assert by_id.id == by_run_id.id
    
    def test_update_run_status(self, storage, brief):
        """Update run status and result."""
        run = storage.create_run(brief_id=brief.id)
        
        updated = storage.update_run(
            run.id,
            status="success",
            result_json={"output": "done"},
            duration_ms=1500,
            finished_at=utc_now()
        )
        
        assert updated.status == "success"
        assert updated.result_json == {"output": "done"}
        assert updated.duration_ms == 1500
    
    def test_list_runs_by_brief(self, storage, brief):
        """List runs filtered by brief."""
        storage.create_run(brief_id=brief.id, run_id="run-1")
        storage.create_run(brief_id=brief.id, run_id="run-2")
        
        runs = storage.list_runs(brief_id=brief.id)
        assert len(runs) == 2
    
    def test_cascade_delete_runs(self, storage, brief):
        """Deleting brief cascades to runs."""
        run = storage.create_run(brief_id=brief.id)
        run_id = run.id
        storage.delete_brief(brief.id)
        assert storage.get_run(run_id) is None


# ============================================
# CONFIG TESTS
# ============================================

class TestConfig:
    """Test config CRUD operations."""
    
    def test_set_config(self, storage):
        """Set config value."""
        config = storage.set_config("theme", "dark")
        
        assert config.key == "theme"
        assert config.value_json == "dark"
    
    def test_set_config_complex_value(self, storage):
        """Set config with complex JSON value."""
        value = {"nested": {"key": [1, 2, 3]}}
        config = storage.set_config("complex", value)
        
        assert config.value_json == value
    
    def test_get_config(self, storage):
        """Get config by key."""
        storage.set_config("mykey", "myvalue")
        
        config = storage.get_config("mykey")
        assert config.value_json == "myvalue"
    
    def test_upsert_config(self, storage):
        """Setting existing key updates value."""
        storage.set_config("key", "value1")
        storage.set_config("key", "value2")
        
        config = storage.get_config("key")
        assert config.value_json == "value2"
    
    def test_list_config(self, storage):
        """List all config entries."""
        storage.set_config("a", 1)
        storage.set_config("b", 2)
        
        configs = storage.list_config()
        keys = [c.key for c in configs]
        assert "a" in keys
        assert "b" in keys
    
    def test_delete_config(self, storage):
        """Delete config entry."""
        storage.set_config("key", "value")
        assert storage.delete_config("key") is True
        assert storage.get_config("key") is None


# ============================================
# SECRET TESTS
# ============================================

class TestSecrets:
    """Test secret CRUD operations with encryption."""
    
    def test_create_secret_global(self, storage):
        """Create global secret."""
        secret = storage.create_secret(
            key="API_KEY",
            plaintext="secret-value-123"
        )
        
        assert secret.id is not None
        assert secret.key == "API_KEY"
        assert secret.scope == "global"
        assert secret.encrypted_value != b"secret-value-123"
    
    def test_create_secret_project_scoped(self, storage, project):
        """Create project-scoped secret."""
        secret = storage.create_secret(
            key="PROJECT_API_KEY",
            plaintext="project-secret",
            scope="project",
            project_id=project.id
        )
        
        assert secret.scope == "project"
        assert secret.project_id == project.id
    
    def test_decrypt_secret(self, storage):
        """Decrypt secret value."""
        secret = storage.create_secret(
            key="DECRYPT_TEST",
            plaintext="my-secret-password"
        )
        
        decrypted = storage.decrypt_secret(secret)
        assert decrypted == "my-secret-password"
    
    def test_get_secret_by_key(self, storage):
        """Get secret by key and scope."""
        storage.create_secret(key="MYKEY", plaintext="value")
        
        secret = storage.get_secret_by_key("MYKEY")
        assert secret is not None
        assert secret.key == "MYKEY"
    
    def test_update_secret(self, storage):
        """Update secret value (re-encrypt)."""
        secret = storage.create_secret(key="UPDATE_TEST", plaintext="old-value")
        
        updated = storage.update_secret(secret.id, "new-value")
        decrypted = storage.decrypt_secret(updated)
        
        assert decrypted == "new-value"
        assert updated.encrypted_value != secret.encrypted_value
    
    def test_list_secrets(self, storage):
        """List secrets (encrypted, not decrypted)."""
        storage.create_secret(key="KEY1", plaintext="val1")
        storage.create_secret(key="KEY2", plaintext="val2")
        
        secrets = storage.list_secrets()
        keys = [s.key for s in secrets]
        
        assert "KEY1" in keys
        assert "KEY2" in keys
    
    def test_delete_secret(self, storage):
        """Delete secret."""
        secret = storage.create_secret(key="DELETE_ME", plaintext="value")
        assert storage.delete_secret(secret.id) is True
        assert storage.get_secret(secret.id) is None


# ============================================
# MODULE TESTS
# ============================================

class TestModules:
    """Test module CRUD operations."""
    
    def test_create_module(self, storage):
        """Create module from manifest."""
        manifest = ModuleManifest(
            name="test-module",
            version="1.0.0",
            description="A test module",
            inputs=[{"name": "prompt", "type": "string", "required": True}],
            outputs=[{"name": "result", "type": "string"}],
            constraints={"hard": ["max_tokens:1000"], "soft": []},
            tags=["test"],
            enabled=True
        )
        
        module = storage.create_module(manifest)
        
        assert module.id is not None
        assert module.name == "test-module"
        assert module.version == "1.0.0"
        assert module.manifest_json["inputs"][0]["name"] == "prompt"
    
    def test_get_module_by_name(self, storage):
        """Get module by name."""
        manifest = ModuleManifest(name="findme", version="1.0.0")
        storage.create_module(manifest)
        
        module = storage.get_module_by_name("findme")
        assert module is not None
        assert module.name == "findme"
    
    def test_list_modules_enabled_only(self, storage):
        """List only enabled modules."""
        manifest1 = ModuleManifest(name="enabled", version="1.0.0", enabled=True)
        manifest2 = ModuleManifest(name="disabled", version="1.0.0", enabled=False)
        
        storage.create_module(manifest1)
        m2 = storage.create_module(manifest2)
        storage.update_module(m2.id, enabled=False)
        
        all_modules = storage.list_modules()
        enabled_modules = storage.list_modules(enabled_only=True)
        
        assert len(all_modules) == 2
        assert len(enabled_modules) == 1
        assert enabled_modules[0].name == "enabled"
    
    def test_update_module_version(self, storage):
        """Update module version."""
        manifest = ModuleManifest(name="versioned", version="1.0.0")
        module = storage.create_module(manifest)
        
        updated = storage.update_module(module.id, version="1.1.0")
        assert updated.version == "1.1.0"
    
    def test_delete_module(self, storage):
        """Delete module from registry."""
        manifest = ModuleManifest(name="deleteme", version="1.0.0")
        module = storage.create_module(manifest)
        
        assert storage.delete_module(module.id) is True
        assert storage.get_module(module.id) is None


# ============================================
# BACKUP TESTS
# ============================================

class TestBackups:
    """Test backup history operations."""
    
    def test_create_backup_success(self, storage):
        """Record successful backup."""
        backup = storage.create_backup(
            status="success",
            commit_sha="abc123",
            notes="Auto backup"
        )
        
        assert backup.id is not None
        assert backup.status == "success"
        assert backup.commit_sha == "abc123"
    
    def test_create_backup_dry_run(self, storage):
        """Record dry run backup."""
        backup = storage.create_backup(
            status="dry_run",
            notes="Test only"
        )
        
        assert backup.status == "dry_run"
        assert backup.commit_sha is None
    
    def test_list_backups(self, storage):
        """List backup history."""
        storage.create_backup(status="success")
        storage.create_backup(status="failed")
        storage.create_backup(status="dry_run")
        
        backups = storage.list_backups()
        statuses = [b.status for b in backups]
        
        assert len(backups) == 3
        assert "success" in statuses
        assert "failed" in statuses
        assert "dry_run" in statuses


# ============================================
# UTILITY TESTS
# ============================================

class TestUtilities:
    """Test utility functions."""
    
    def test_generate_uuid(self):
        """UUID generation works."""
        uuid1 = generate_uuid()
        uuid2 = generate_uuid()
        
        assert len(uuid1) == 36
        assert uuid1 != uuid2
    
    def test_utc_now_format(self):
        """UTC timestamp in ISO format."""
        ts = utc_now()
        
        assert "T" in ts
        assert ts.endswith("Z")


# ============================================
# ENCRYPTION TESTS
# ============================================

class TestEncryption:
    """Test encryption functionality."""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Encryption roundtrip works."""
        enc = SecretEncryption()
        
        original = "super-secret-value"
        encrypted, nonce = enc.encrypt(original)
        decrypted = enc.decrypt(encrypted, nonce)
        
        assert decrypted == original
        assert encrypted != original.encode()
    
    def test_different_encryptions(self):
        """Same plaintext produces different ciphertext."""
        enc = SecretEncryption()
        
        encrypted1, _ = enc.encrypt("value")
        encrypted2, _ = enc.encrypt("value")
        
        # Fernet uses random IV, so ciphertexts differ
        assert encrypted1 != encrypted2


# ============================================
# EDGE CASES
# ============================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_tags(self, storage):
        """Empty tags array works."""
        project = storage.create_project(name="No Tags", tags=[])
        assert project.tags == []
    
    def test_unicode_content(self, storage, project):
        """Unicode content handled correctly."""
        brief = storage.create_brief(
            project_id=project.id,
            title="日本語タイトル",
            user_prompt="Émojis 🎉 and spëcial chârs"
        )
        
        retrieved = storage.get_brief(brief.id)
        assert retrieved.title == "日本語タイトル"
        assert "🎉" in retrieved.user_prompt
    
    def test_large_json(self, storage, project):
        """Large JSON objects work."""
        large_vars = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        
        brief = storage.create_brief(
            project_id=project.id,
            title="Large JSON",
            user_prompt="Test",
            variables_json=large_vars
        )
        
        retrieved = storage.get_brief(brief.id)
        assert len(retrieved.variables_json) == 100
    
    def test_no_categories_table(self, temp_db):
        """Verify no categories table exists (tags only)."""
        storage = Storage(temp_db)
        storage.init_db()
        
        with storage.connection() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t["name"] for t in tables]
        
        assert "categories" not in table_names
        assert "tags" not in table_names  # No separate tags table


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
