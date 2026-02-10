"""
EURKAI_COCKPIT — Backup Tests (C07)
Version: 1.0.0

Tests for backup module:
- Dry-run mode
- SQLite copy
- JSON export
- Git configuration detection
"""

import base64
import json
import os
import sqlite3
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from backend.backup.backup import (
    BackupConfig,
    BackupResult,
    run_backup,
    export_json,
    copy_sqlite,
    is_git_configured,
    get_db_path,
    get_backup_dir,
    TABLES_TO_EXPORT,
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        
        # Create minimal schema
        conn.executescript("""
            CREATE TABLE projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                root_path TEXT,
                tags TEXT DEFAULT '[]',
                created_at TEXT,
                updated_at TEXT
            );
            
            CREATE TABLE briefs (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                title TEXT NOT NULL,
                goal TEXT,
                system_prompt TEXT,
                user_prompt TEXT NOT NULL,
                variables_json TEXT DEFAULT '{}',
                expected_output TEXT,
                tags TEXT DEFAULT '[]',
                policy TEXT DEFAULT '{}',
                created_at TEXT,
                updated_at TEXT
            );
            
            CREATE TABLE runs (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                brief_id TEXT,
                status TEXT DEFAULT 'pending',
                result_json TEXT,
                logs_json TEXT DEFAULT '[]',
                error TEXT,
                model TEXT,
                duration_ms INTEGER,
                started_at TEXT,
                finished_at TEXT,
                created_at TEXT
            );
            
            CREATE TABLE config (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL UNIQUE,
                value_json TEXT NOT NULL,
                updated_at TEXT
            );
            
            CREATE TABLE secrets (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL,
                encrypted_value BLOB NOT NULL,
                nonce BLOB NOT NULL,
                scope TEXT DEFAULT 'global',
                project_id TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            
            CREATE TABLE modules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                version TEXT NOT NULL,
                description TEXT,
                manifest_json TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            );
            
            CREATE TABLE backups (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                commit_sha TEXT,
                status TEXT NOT NULL,
                notes TEXT,
                created_at TEXT
            );
        """)
        
        # Insert test data
        conn.execute(
            "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "Test Project", "A test project", "2026-01-12T10:00:00Z", "2026-01-12T10:00:00Z")
        )
        
        conn.execute(
            "INSERT INTO config (id, key, value_json, updated_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), "theme", '"dark"', "2026-01-12T10:00:00Z")
        )
        
        conn.execute(
            "INSERT INTO modules (id, name, version, description, manifest_json, enabled, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "test-module", "1.0.0", "Test module", '{"inputs": [], "outputs": []}', 1, "2026-01-12T10:00:00Z", "2026-01-12T10:00:00Z")
        )
        
        # Insert secret with binary data
        conn.execute(
            "INSERT INTO secrets (id, key, encrypted_value, nonce, scope, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "api_key", b"encrypted_data_here", b"nonce_value_16b!", "global", "2026-01-12T10:00:00Z", "2026-01-12T10:00:00Z")
        )
        
        conn.commit()
        conn.close()
        
        yield db_path


@pytest.fixture
def backup_dir():
    """Create a temporary backup directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "backup"


# ============================================
# UNIT TESTS
# ============================================

class TestGetDbPath:
    """Tests for get_db_path()."""
    
    def test_default_path(self):
        """Without env var, returns default."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove EURKAI_DB_PATH if present
            os.environ.pop("EURKAI_DB_PATH", None)
            path = get_db_path()
            assert path == Path("data/cockpit.db")
    
    def test_env_override(self):
        """With env var, returns custom path."""
        with patch.dict(os.environ, {"EURKAI_DB_PATH": "/custom/path.db"}):
            path = get_db_path()
            assert path == Path("/custom/path.db")


class TestGetBackupDir:
    """Tests for get_backup_dir()."""
    
    def test_default_with_timestamp(self):
        """Without env var, returns default + timestamp."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("EURKAI_BACKUP_DIR", None)
            path = get_backup_dir("20260112_100000")
            assert path == Path("data/backups/20260112_100000")
    
    def test_env_override(self):
        """With env var, returns custom path."""
        with patch.dict(os.environ, {"EURKAI_BACKUP_DIR": "/custom/backups"}):
            path = get_backup_dir("20260112_100000")
            assert path == Path("/custom/backups")


class TestCopySqlite:
    """Tests for copy_sqlite()."""
    
    def test_copy_success(self, temp_db, backup_dir):
        """Copies database file successfully."""
        dest = copy_sqlite(temp_db, backup_dir)
        
        assert dest.exists()
        assert dest.name == temp_db.name
        assert dest.stat().st_size == temp_db.stat().st_size
    
    def test_creates_directory(self, temp_db):
        """Creates backup directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "a" / "b" / "c"
            dest = copy_sqlite(temp_db, nested)
            
            assert nested.exists()
            assert dest.exists()
    
    def test_missing_db_raises(self, backup_dir):
        """Raises FileNotFoundError for missing database."""
        with pytest.raises(FileNotFoundError):
            copy_sqlite(Path("/nonexistent/db.sqlite"), backup_dir)


class TestExportJson:
    """Tests for export_json()."""
    
    def test_exports_all_tables(self, temp_db, backup_dir):
        """Exports all configured tables."""
        exported = export_json(temp_db, backup_dir)
        
        # Should export all tables that exist
        assert "projects" in exported
        assert "config" in exported
        assert "modules" in exported
        assert "secrets" in exported
    
    def test_json_files_created(self, temp_db, backup_dir):
        """Creates JSON files for each table."""
        export_json(temp_db, backup_dir)
        
        assert (backup_dir / "projects.json").exists()
        assert (backup_dir / "config.json").exists()
        assert (backup_dir / "modules.json").exists()
    
    def test_json_content_valid(self, temp_db, backup_dir):
        """JSON files contain valid data."""
        export_json(temp_db, backup_dir)
        
        with open(backup_dir / "projects.json") as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["name"] == "Test Project"
    
    def test_binary_encoded_as_base64(self, temp_db, backup_dir):
        """Binary fields are base64 encoded."""
        export_json(temp_db, backup_dir)
        
        with open(backup_dir / "secrets.json") as f:
            data = json.load(f)
            assert len(data) == 1
            # encrypted_value should be base64
            enc = data[0]["encrypted_value"]
            decoded = base64.b64decode(enc)
            assert decoded == b"encrypted_data_here"
    
    def test_missing_db_raises(self, backup_dir):
        """Raises FileNotFoundError for missing database."""
        with pytest.raises(FileNotFoundError):
            export_json(Path("/nonexistent/db.sqlite"), backup_dir)
    
    def test_missing_table_skipped(self, backup_dir):
        """Missing tables are skipped without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "empty.db"
            conn = sqlite3.connect(str(db_path))
            # Only create projects table
            conn.execute("CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT)")
            conn.close()
            
            exported = export_json(db_path, backup_dir)
            assert "projects" in exported
            assert "briefs" not in exported


class TestIsGitConfigured:
    """Tests for is_git_configured()."""
    
    def test_no_git_command(self):
        """Returns False if git command not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert is_git_configured() is False
    
    def test_not_git_repo(self):
        """Returns False if not in git repository."""
        mock_result = MagicMock()
        mock_result.returncode = 128  # Not a git repo
        
        with patch("subprocess.run", return_value=mock_result):
            assert is_git_configured() is False
    
    def test_no_remote(self):
        """Returns False if remote doesn't exist."""
        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "rev-parse" in cmd:
                result.returncode = 0  # Is a git repo
            else:
                result.returncode = 1  # Remote not found
            return result
        
        with patch("subprocess.run", side_effect=mock_run):
            assert is_git_configured("nonexistent") is False
    
    def test_configured(self):
        """Returns True if git and remote configured."""
        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stdout = "true\n"
            return result
        
        with patch("subprocess.run", side_effect=mock_run):
            assert is_git_configured() is True


# ============================================
# INTEGRATION TESTS
# ============================================

class TestRunBackupDryRun:
    """Tests for run_backup() in dry-run mode."""
    
    def test_dryrun_creates_files(self, temp_db, backup_dir):
        """Dry-run creates SQLite copy and JSON exports."""
        config = BackupConfig(
            db_path=temp_db,
            backup_dir=backup_dir,
            dry_run=True
        )
        
        result = run_backup(config)
        
        assert result.success is True
        assert result.status == "dry_run"
        assert result.sqlite_copied is True
        assert len(result.json_exported) > 0
        assert result.commit_sha is None
        assert result.git_pushed is False
    
    def test_dryrun_no_git_operations(self, temp_db, backup_dir):
        """Dry-run skips all Git operations."""
        config = BackupConfig(
            db_path=temp_db,
            backup_dir=backup_dir,
            dry_run=True
        )
        
        with patch("backend.backup.backup.git_commit_push") as mock_git:
            result = run_backup(config)
            mock_git.assert_not_called()
        
        assert result.success is True
        assert "Dry-run" in result.notes or "dry" in result.notes.lower()


class TestRunBackupNoGit:
    """Tests for run_backup() without Git configured."""
    
    def test_no_git_falls_back_to_dryrun(self, temp_db, backup_dir):
        """Without Git, behaves like dry-run."""
        config = BackupConfig(
            db_path=temp_db,
            backup_dir=backup_dir,
            dry_run=False
        )
        
        with patch("backend.backup.backup.is_git_configured", return_value=False):
            result = run_backup(config)
        
        assert result.success is True
        assert result.status == "dry_run"
        assert result.sqlite_copied is True
        assert "Git not configured" in result.notes


class TestRunBackupWithGit:
    """Tests for run_backup() with Git configured."""
    
    def test_with_git_commits_and_pushes(self, temp_db, backup_dir):
        """With Git configured, commits and pushes."""
        config = BackupConfig(
            db_path=temp_db,
            backup_dir=backup_dir,
            dry_run=False
        )
        
        with patch("backend.backup.backup.is_git_configured", return_value=True):
            with patch("backend.backup.backup.git_commit_push", return_value=(True, "abc123def")):
                result = run_backup(config)
        
        assert result.success is True
        assert result.status == "success"
        assert result.commit_sha == "abc123def"
        assert result.git_pushed is True
    
    def test_git_failure_handled(self, temp_db, backup_dir):
        """Git failure doesn't crash, marks as failed."""
        config = BackupConfig(
            db_path=temp_db,
            backup_dir=backup_dir,
            dry_run=False
        )
        
        with patch("backend.backup.backup.is_git_configured", return_value=True):
            with patch("backend.backup.backup.git_commit_push", return_value=(False, None)):
                result = run_backup(config)
        
        assert result.success is False
        assert result.status == "failed"
        assert "Git commit/push failed" in result.error


class TestBackupResult:
    """Tests for BackupResult dataclass."""
    
    def test_to_dict(self):
        """to_dict() returns serializable dict."""
        result = BackupResult(
            success=True,
            status="success",
            timestamp="2026-01-12T10:00:00Z",
            backup_dir="/path/to/backup",
            sqlite_copied=True,
            json_exported=["projects", "config"],
            commit_sha="abc123",
            git_pushed=True,
            notes="All good"
        )
        
        d = result.to_dict()
        
        assert d["success"] is True
        assert d["status"] == "success"
        assert d["commit_sha"] == "abc123"
        assert "projects" in d["json_exported"]
        
        # Should be JSON serializable
        json.dumps(d)


class TestBackupMissingDb:
    """Tests for backup with missing database."""
    
    def test_missing_db_fails(self, backup_dir):
        """Missing database results in failed status."""
        config = BackupConfig(
            db_path=Path("/nonexistent/db.sqlite"),
            backup_dir=backup_dir,
            dry_run=True
        )
        
        result = run_backup(config)
        
        assert result.success is False
        assert result.status == "failed"
        assert "not found" in result.error.lower()


# ============================================
# CLI TESTS
# ============================================

class TestCli:
    """Tests for CLI entry point."""
    
    def test_cli_dryrun(self, temp_db, backup_dir):
        """CLI with --dry-run works."""
        from backend.backup.backup import main
        import sys
        
        with patch.object(sys, "argv", [
            "backup.py",
            "--dry-run",
            "--db-path", str(temp_db),
            "--backup-dir", str(backup_dir)
        ]):
            exit_code = main()
        
        assert exit_code == 0
        assert (backup_dir / temp_db.name).exists()
    
    def test_cli_missing_db_exits_1(self, backup_dir):
        """CLI with missing DB exits with code 1."""
        from backend.backup.backup import main
        import sys
        
        with patch.object(sys, "argv", [
            "backup.py",
            "--dry-run",
            "--db-path", "/nonexistent/db.sqlite",
            "--backup-dir", str(backup_dir)
        ]):
            exit_code = main()
        
        assert exit_code == 1
