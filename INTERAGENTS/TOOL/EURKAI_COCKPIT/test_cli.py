"""
EURKAI_COCKPIT — CLI Tests
Version: 1.0.0
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.cli import app
from backend.storage.storage import Storage


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield str(db_path)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def initialized_db(temp_db, runner):
    result = runner.invoke(app, ["--db-path", temp_db, "init"])
    assert result.exit_code == 0
    return temp_db


class TestInit:
    def test_init_creates_db(self, temp_db, runner):
        result = runner.invoke(app, ["--db-path", temp_db, "init"])
        assert result.exit_code == 0
        assert "Database created" in result.output
        assert Path(temp_db).exists()
    
    def test_init_idempotent(self, temp_db, runner):
        result1 = runner.invoke(app, ["--db-path", temp_db, "init"])
        assert result1.exit_code == 0
        assert "created" in result1.output
        
        result2 = runner.invoke(app, ["--db-path", temp_db, "init"])
        assert result2.exit_code == 0
        assert "already initialized" in result2.output
    
    def test_init_sets_config(self, temp_db, runner):
        runner.invoke(app, ["--db-path", temp_db, "init"])
        storage = Storage(db_path=temp_db, auto_init=False)
        version = storage.get_config("cockpit.version")
        assert version is not None
        assert version["value"] == "1.0.0"


class TestProject:
    def test_project_add(self, initialized_db, runner):
        result = runner.invoke(app, [
            "--db-path", initialized_db,
            "project", "add", "TestProject", "--desc", "A test project"
        ])
        assert result.exit_code == 0
        assert "Project created" in result.output
        assert "TestProject" in result.output
    
    def test_project_add_json(self, initialized_db, runner):
        result = runner.invoke(app, [
            "--db-path", initialized_db,
            "project", "add", "JSONProject", "--json"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "JSONProject"
        assert "id" in data
    
    def test_project_list_empty(self, initialized_db, runner):
        result = runner.invoke(app, ["--db-path", initialized_db, "project", "list"])
        assert result.exit_code == 0
        assert "No projects found" in result.output
    
    def test_project_add_then_list(self, initialized_db, runner):
        runner.invoke(app, ["--db-path", initialized_db, "project", "add", "ListTest"])
        result = runner.invoke(app, ["--db-path", initialized_db, "project", "list"])
        assert result.exit_code == 0
        assert "ListTest" in result.output
    
    def test_project_list_json(self, initialized_db, runner):
        runner.invoke(app, ["--db-path", initialized_db, "project", "add", "JSONListTest"])
        result = runner.invoke(app, ["--db-path", initialized_db, "project", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["name"] == "JSONListTest"


class TestBrief:
    def test_brief_add_requires_project(self, initialized_db, runner):
        result = runner.invoke(app, [
            "--db-path", initialized_db,
            "brief", "add", "invalid-project-id", "TestBrief", "--user-prompt", "Test prompt"
        ])
        assert result.exit_code == 1
        assert "Project not found" in result.output
    
    def test_brief_add_success(self, initialized_db, runner):
        proj_result = runner.invoke(app, [
            "--db-path", initialized_db, "project", "add", "BriefProject", "--json"
        ])
        project_id = json.loads(proj_result.output)["id"]
        
        result = runner.invoke(app, [
            "--db-path", initialized_db,
            "brief", "add", project_id, "TestBrief",
            "--user-prompt", "Generate code", "--goal", "Create working code"
        ])
        assert result.exit_code == 0
        assert "Brief created" in result.output
    
    def test_brief_list_filtered(self, initialized_db, runner):
        proj_result = runner.invoke(app, [
            "--db-path", initialized_db, "project", "add", "FilterProject", "--json"
        ])
        project_id = json.loads(proj_result.output)["id"]
        
        runner.invoke(app, [
            "--db-path", initialized_db, "brief", "add", project_id, "FilteredBrief", "--user-prompt", "Test"
        ])
        
        result = runner.invoke(app, [
            "--db-path", initialized_db, "brief", "list", "--project-id", project_id
        ])
        assert result.exit_code == 0
        assert "FilteredBrief" in result.output


class TestRun:
    def test_run_start_requires_brief(self, initialized_db, runner):
        result = runner.invoke(app, ["--db-path", initialized_db, "run", "start", "invalid-brief-id"])
        assert result.exit_code == 1
        assert "Brief not found" in result.output
    
    def test_run_start_creates_pending(self, initialized_db, runner):
        proj_result = runner.invoke(app, ["--db-path", initialized_db, "project", "add", "RunProject", "--json"])
        project_id = json.loads(proj_result.output)["id"]
        
        brief_result = runner.invoke(app, [
            "--db-path", initialized_db, "brief", "add", project_id, "RunBrief", "--user-prompt", "Test", "--json"
        ])
        brief_id = json.loads(brief_result.output)["id"]
        
        result = runner.invoke(app, ["--db-path", initialized_db, "run", "start", brief_id])
        assert result.exit_code == 0
        assert "Run created" in result.output
        assert "pending" in result.output
    
    def test_run_start_json(self, initialized_db, runner):
        proj_result = runner.invoke(app, ["--db-path", initialized_db, "project", "add", "JSONRunProject", "--json"])
        project_id = json.loads(proj_result.output)["id"]
        
        brief_result = runner.invoke(app, [
            "--db-path", initialized_db, "brief", "add", project_id, "JSONRunBrief", "--user-prompt", "Test", "--json"
        ])
        brief_id = json.loads(brief_result.output)["id"]
        
        result = runner.invoke(app, ["--db-path", initialized_db, "run", "start", brief_id, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "pending"
        assert data["brief_id"] == brief_id
        assert "run_id" in data
    
    def test_run_list(self, initialized_db, runner):
        proj_result = runner.invoke(app, ["--db-path", initialized_db, "project", "add", "ListRunProject", "--json"])
        project_id = json.loads(proj_result.output)["id"]
        
        brief_result = runner.invoke(app, [
            "--db-path", initialized_db, "brief", "add", project_id, "ListRunBrief", "--user-prompt", "Test", "--json"
        ])
        brief_id = json.loads(brief_result.output)["id"]
        
        runner.invoke(app, ["--db-path", initialized_db, "run", "start", brief_id])
        result = runner.invoke(app, ["--db-path", initialized_db, "run", "list"])
        assert result.exit_code == 0
        assert "pending" in result.output


class TestExport:
    def test_export_creates_files(self, initialized_db, runner):
        with tempfile.TemporaryDirectory() as export_dir:
            result = runner.invoke(app, ["--db-path", initialized_db, "export", "--output", export_dir])
            assert result.exit_code == 0
            assert "Export completed" in result.output
            assert len(list(Path(export_dir).glob("eurkai_*.db"))) == 1
            assert len(list(Path(export_dir).glob("eurkai_*.json"))) == 1
    
    def test_export_contains_data(self, initialized_db, runner):
        runner.invoke(app, ["--db-path", initialized_db, "project", "add", "ExportProject"])
        
        with tempfile.TemporaryDirectory() as export_dir:
            runner.invoke(app, ["--db-path", initialized_db, "export", "--output", export_dir])
            json_file = list(Path(export_dir).glob("eurkai_*.json"))[0]
            with open(json_file) as f:
                data = json.load(f)
            assert len(data["data"]["projects"]) == 1
            assert data["data"]["projects"][0]["name"] == "ExportProject"
    
    def test_export_json_output(self, initialized_db, runner):
        with tempfile.TemporaryDirectory() as export_dir:
            result = runner.invoke(app, ["--db-path", initialized_db, "export", "--output", export_dir, "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["status"] == "success"
            assert "counts" in data


class TestImport:
    def test_import_restores_data(self, initialized_db, runner):
        runner.invoke(app, ["--db-path", initialized_db, "project", "add", "ImportProject"])
        
        with tempfile.TemporaryDirectory() as export_dir:
            runner.invoke(app, ["--db-path", initialized_db, "export", "--output", export_dir])
            json_file = list(Path(export_dir).glob("eurkai_*.json"))[0]
            
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
                new_db = tmp.name
            
            try:
                runner.invoke(app, ["--db-path", new_db, "init"])
                result = runner.invoke(app, ["--db-path", new_db, "import", str(json_file)])
                assert result.exit_code == 0
                assert "Import completed" in result.output
                
                list_result = runner.invoke(app, ["--db-path", new_db, "project", "list", "--json"])
                projects = json.loads(list_result.output)
                assert len(projects) == 1
                assert projects[0]["name"] == "ImportProject"
            finally:
                os.unlink(new_db)
    
    def test_import_skips_existing(self, initialized_db, runner):
        runner.invoke(app, ["--db-path", initialized_db, "project", "add", "DuplicateProject", "--json"])
        
        with tempfile.TemporaryDirectory() as export_dir:
            runner.invoke(app, ["--db-path", initialized_db, "export", "--output", export_dir])
            json_file = list(Path(export_dir).glob("eurkai_*.json"))[0]
            
            result = runner.invoke(app, ["--db-path", initialized_db, "import", str(json_file), "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["imported"]["projects"] == 0
            assert data["imported"]["skipped"] >= 1


class TestErrors:
    def test_commands_require_init(self, temp_db, runner):
        result = runner.invoke(app, ["--db-path", temp_db, "project", "list"])
        assert result.exit_code == 1
        assert "Database not found" in result.output
        assert "init" in result.output


class TestIntegration:
    def test_full_workflow(self, temp_db, runner):
        result = runner.invoke(app, ["--db-path", temp_db, "init"])
        assert result.exit_code == 0
        
        result = runner.invoke(app, [
            "--db-path", temp_db, "project", "add", "IntegrationProject",
            "--desc", "Full workflow test", "--json"
        ])
        assert result.exit_code == 0
        project = json.loads(result.output)
        
        result = runner.invoke(app, [
            "--db-path", temp_db, "brief", "add", project["id"], "IntegrationBrief",
            "--user-prompt", "Create a test", "--goal", "Test the system", "--json"
        ])
        assert result.exit_code == 0
        brief = json.loads(result.output)
        
        result = runner.invoke(app, ["--db-path", temp_db, "run", "start", brief["id"], "--json"])
        assert result.exit_code == 0
        run = json.loads(result.output)
        assert run["status"] == "pending"
        
        with tempfile.TemporaryDirectory() as export_dir:
            result = runner.invoke(app, ["--db-path", temp_db, "export", "--output", export_dir, "--json"])
            assert result.exit_code == 0
            export_result = json.loads(result.output)
            assert export_result["counts"]["projects"] == 1
            assert export_result["counts"]["briefs"] == 1
            assert export_result["counts"]["runs"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
