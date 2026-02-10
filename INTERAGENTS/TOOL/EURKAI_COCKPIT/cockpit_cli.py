#!/usr/bin/env python3
"""
EURKAI_COCKPIT — CLI d'intégration
Version: 1.0.0
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import click

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.storage.storage import Storage
from backend.storage.migrations import init_db, get_db_path

VERSION = "1.0.0"
DEFAULT_CONFIG = {
    "version": VERSION,
    "created_at": None,
    "default_policy": {"passes_in_a_row": 2, "max_iters": 8},
}

def get_storage(db_path: Optional[str] = None) -> Storage:
    return Storage(db_path=db_path, auto_init=False)

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def output_json(data: dict | list, pretty: bool = True) -> None:
    indent = 2 if pretty else None
    click.echo(json.dumps(data, indent=indent, ensure_ascii=False, default=str))

def output_table(headers: list[str], rows: list[list], max_width: int = 40) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell is not None else ""
            if len(cell_str) > max_width:
                cell_str = cell_str[:max_width-3] + "..."
            widths[i] = max(widths[i], len(cell_str))
    
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    click.echo(header_line)
    click.echo("-" * len(header_line))
    
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell is not None else ""
            if len(cell_str) > max_width:
                cell_str = cell_str[:max_width-3] + "..."
            cells.append(cell_str.ljust(widths[i]))
        click.echo(" | ".join(cells))

def ensure_db_exists(ctx: click.Context) -> Storage:
    db_path = ctx.obj.get("db_path") if ctx.obj else None
    resolved_path = get_db_path(db_path)
    
    if not resolved_path.exists():
        click.echo(f"Error: Database not found at {resolved_path}", err=True)
        click.echo("Run 'cockpit init' first.", err=True)
        ctx.exit(1)
    
    return get_storage(db_path)

@click.group()
@click.option("--db-path", envvar="EURKAI_DB_PATH", help="Path to database file")
@click.version_option(VERSION, prog_name="cockpit")
@click.pass_context
def app(ctx: click.Context, db_path: Optional[str]) -> None:
    """EURKAI_COCKPIT — CLI d'intégration inter-agents."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db_path

@app.command()
@click.option("--db-path", help="Override default database path")
@click.pass_context
def init(ctx: click.Context, db_path: Optional[str]) -> None:
    """Initialize database and default config (idempotent)."""
    path = db_path or ctx.obj.get("db_path")
    resolved_path = get_db_path(path)
    already_exists = resolved_path.exists()
    
    init_db(path)
    
    storage = Storage(db_path=path, auto_init=False)
    existing = storage.get_config("cockpit.version")
    if not existing:
        config = DEFAULT_CONFIG.copy()
        config["created_at"] = utc_now()
        # set_config expects string, so serialize
        storage.set_config("cockpit.version", VERSION)
        storage.set_config("cockpit.config", json.dumps(config))
    
    if already_exists:
        click.echo(f"✓ Database already initialized at {resolved_path}")
    else:
        click.echo(f"✓ Database created at {resolved_path}")
    click.echo(f"✓ Config version: {VERSION}")

@app.group()
def project() -> None:
    """Manage projects."""
    pass

@project.command("add")
@click.argument("name")
@click.option("--desc", "-d", help="Project description")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def project_add(ctx: click.Context, name: str, desc: Optional[str], as_json: bool) -> None:
    """Add a new project."""
    storage = ensure_db_exists(ctx)
    project = storage.create_project(name=name, description=desc)
    
    if as_json:
        output_json(project)
    else:
        click.echo(f"✓ Project created: {project['name']} ({project['id']})")

@project.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def project_list(ctx: click.Context, as_json: bool) -> None:
    """List all projects."""
    storage = ensure_db_exists(ctx)
    projects = storage.list_projects()
    
    if as_json:
        output_json(projects)
    else:
        if not projects:
            click.echo("No projects found.")
            return
        output_table(
            headers=["ID", "Name", "Description", "Created"],
            rows=[[p["id"][:8], p["name"], p.get("description") or "-", p["created_at"][:10]] for p in projects]
        )

@app.group()
def brief() -> None:
    """Manage briefs."""
    pass

@brief.command("add")
@click.argument("project_id")
@click.argument("title")
@click.option("--goal", "-g", help="Brief goal")
@click.option("--system-prompt", "-s", help="System prompt")
@click.option("--user-prompt", "-u", required=True, help="User prompt (required)")
@click.option("--expected", "-e", help="Expected output description")
@click.option("--tags", "-t", help="Comma-separated tags")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def brief_add(ctx: click.Context, project_id: str, title: str, goal: Optional[str],
              system_prompt: Optional[str], user_prompt: str, expected: Optional[str],
              tags: Optional[str], as_json: bool) -> None:
    """Add a new brief to a project."""
    storage = ensure_db_exists(ctx)
    
    project = storage.get_project(project_id)
    if not project:
        click.echo(f"Error: Project not found: {project_id}", err=True)
        ctx.exit(1)
    
    tags_list = [t.strip() for t in tags.split(",")] if tags else None
    
    brief = storage.create_brief(
        project_id=project_id, title=title, user_prompt=user_prompt,
        goal=goal, system_prompt=system_prompt, expected_output=expected, tags=tags_list
    )
    
    if as_json:
        output_json(brief)
    else:
        click.echo(f"✓ Brief created: {brief['title']} ({brief['id']})")

@brief.command("list")
@click.option("--project-id", "-p", help="Filter by project ID")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def brief_list(ctx: click.Context, project_id: Optional[str], as_json: bool) -> None:
    """List briefs, optionally filtered by project."""
    storage = ensure_db_exists(ctx)
    briefs = storage.list_briefs(project_id=project_id)
    
    if as_json:
        output_json(briefs)
    else:
        if not briefs:
            click.echo("No briefs found.")
            return
        output_table(
            headers=["ID", "Project", "Title", "Goal", "Created"],
            rows=[[b["id"][:8], b["project_id"][:8], b["title"], b.get("goal") or "-", b["created_at"][:10]] for b in briefs]
        )

@app.group()
def run() -> None:
    """Manage runs."""
    pass

@run.command("start")
@click.argument("brief_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def run_start(ctx: click.Context, brief_id: str, as_json: bool) -> None:
    """Start a new run for a brief (creates pending run, no execution)."""
    storage = ensure_db_exists(ctx)
    
    brief = storage.get_brief(brief_id)
    if not brief:
        click.echo(f"Error: Brief not found: {brief_id}", err=True)
        ctx.exit(1)
    
    # create_run only accepts brief_id and model
    run_obj = storage.create_run(brief_id=brief_id)
    
    # Update with initial log
    log_entry = json.dumps([{"timestamp": utc_now(), "level": "info", "message": "Run created by CLI (pending execution)"}])
    storage.update_run(run_obj["id"], logs=log_entry)
    run_obj = storage.get_run(run_obj["id"])
    
    # Add run_id alias for compatibility
    run_obj["run_id"] = run_obj["id"]
    
    if as_json:
        output_json(run_obj)
    else:
        click.echo(f"✓ Run created: {run_obj['id']}")
        click.echo(f"  Brief: {brief['title']}")
        click.echo(f"  Status: {run_obj['status']}")
        click.echo(f"  Note: Run is pending. Use a runner (C08+) to execute.")

@run.command("list")
@click.option("--brief-id", "-b", help="Filter by brief ID")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def run_list(ctx: click.Context, brief_id: Optional[str], as_json: bool) -> None:
    """List runs, optionally filtered by brief."""
    storage = ensure_db_exists(ctx)
    
    # C03 API requires brief_id, so we need to list all briefs first if not specified
    if brief_id:
        runs = storage.list_runs(brief_id=brief_id)
    else:
        # Get all runs by iterating through briefs
        runs = []
        for brief in storage.list_briefs():
            runs.extend(storage.list_runs(brief_id=brief["id"]))
        # Sort by created_at descending
        runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    
    # Add run_id alias for compatibility
    for r in runs:
        r["run_id"] = r["id"]
    
    if as_json:
        output_json(runs)
    else:
        if not runs:
            click.echo("No runs found.")
            return
        output_table(
            headers=["Run ID", "Brief", "Status", "Model", "Duration", "Created"],
            rows=[
                [r["id"][:8], r["brief_id"][:8], r["status"], 
                 r.get("model") or "-", f"{r['duration_ms']}ms" if r.get("duration_ms") else "-", r["created_at"][:10]]
                for r in runs
            ]
        )

@app.command()
@click.option("--output", "-o", default="export", help="Output directory")
@click.option("--json", "as_json", is_flag=True, help="Output result as JSON")
@click.pass_context
def export(ctx: click.Context, output: str, as_json: bool) -> None:
    """Export database (SQLite + JSON dump)."""
    storage = ensure_db_exists(ctx)
    
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    db_export_path = output_dir / f"eurkai_{timestamp}.db"
    shutil.copy2(storage.db_path, db_export_path)
    
    json_export_path = output_dir / f"eurkai_{timestamp}.json"
    
    # Collect all runs
    all_runs = []
    for brief in storage.list_briefs():
        all_runs.extend(storage.list_runs(brief_id=brief["id"]))
    
    export_data = {
        "version": VERSION,
        "exported_at": utc_now(),
        "source_db": str(storage.db_path),
        "data": {
            "projects": storage.list_projects(),
            "briefs": storage.list_briefs(),
            "runs": all_runs,
            "modules": storage.list_modules(),
            "config": storage.list_config(),
            "secrets": _export_secrets(storage)
        }
    }
    
    with open(json_export_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
    
    storage.create_backup(status="success", notes=f"CLI export to {output_dir}")
    
    result = {
        "status": "success", "db_file": str(db_export_path), "json_file": str(json_export_path),
        "counts": {
            "projects": len(export_data["data"]["projects"]),
            "briefs": len(export_data["data"]["briefs"]),
            "runs": len(export_data["data"]["runs"]),
            "modules": len(export_data["data"]["modules"]),
            "secrets": len(export_data["data"]["secrets"])
        }
    }
    
    if as_json:
        output_json(result)
    else:
        click.echo(f"✓ Export completed to {output_dir}/")
        click.echo(f"  Database: {db_export_path.name}")
        click.echo(f"  JSON: {json_export_path.name}")
        for k, v in result["counts"].items():
            suffix = " (encrypted)" if k == "secrets" else ""
            click.echo(f"  {k.capitalize()}: {v}{suffix}")

def _export_secrets(storage: Storage) -> list[dict]:
    """Export secrets (encrypted, hex-encoded)."""
    secrets = storage.list_secrets()
    for s in secrets:
        if s.get("value_encrypted"):
            s["value_encrypted"] = s["value_encrypted"].hex() if isinstance(s["value_encrypted"], bytes) else s["value_encrypted"]
        if s.get("nonce"):
            s["nonce"] = s["nonce"].hex() if isinstance(s["nonce"], bytes) else s["nonce"]
    return secrets

@app.command("import")
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="Output result as JSON")
@click.pass_context
def import_data(ctx: click.Context, file: str, as_json: bool) -> None:
    """Import data from JSON export (projects, briefs, modules, config)."""
    storage = ensure_db_exists(ctx)
    file_path = Path(file)
    
    with open(file_path, "r", encoding="utf-8") as f:
        import_data_content = json.load(f)
    
    if "data" not in import_data_content:
        click.echo("Error: Invalid import file format (missing 'data' key)", err=True)
        ctx.exit(1)
    
    data = import_data_content["data"]
    counts = {"projects": 0, "briefs": 0, "modules": 0, "config": 0, "skipped": 0}
    
    for p in data.get("projects", []):
        if storage.get_project(p["id"]):
            counts["skipped"] += 1
            continue
        with storage._conn() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (p["id"], p["name"], p.get("description"), p.get("created_at", utc_now()), p.get("updated_at", utc_now()))
            )
        counts["projects"] += 1
    
    for b in data.get("briefs", []):
        if storage.get_brief(b["id"]) or not storage.get_project(b["project_id"]):
            counts["skipped"] += 1
            continue
        with storage._conn() as conn:
            conn.execute(
                """INSERT INTO briefs (id, project_id, title, goal, system_prompt, user_prompt, 
                   variables, expected_output, tags, policy, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (b["id"], b["project_id"], b["title"], b.get("goal"), b.get("system_prompt"), b["user_prompt"],
                 json.dumps(b.get("variables", {})), b.get("expected_output"), json.dumps(b.get("tags", [])),
                 json.dumps(b.get("policy", {"passes_in_a_row": 2, "max_iters": 8})),
                 b.get("created_at", utc_now()), b.get("updated_at", utc_now()))
            )
        counts["briefs"] += 1
    
    for m in data.get("modules", []):
        if storage.get_module_by_name(m["name"]):
            counts["skipped"] += 1
            continue
        with storage._conn() as conn:
            conn.execute(
                """INSERT INTO module_manifests (id, name, version, description, inputs, outputs, constraints, tags, registered_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (m["id"], m["name"], m["version"], m.get("description"), json.dumps(m.get("inputs", [])),
                 json.dumps(m.get("outputs", [])), json.dumps(m.get("constraints", {})), json.dumps(m.get("tags", [])),
                 m.get("registered_at", utc_now()))
            )
        counts["modules"] += 1
    
    for c in data.get("config", []):
        key = c.get("key")
        if not key:
            continue
        if storage.get_config(key):
            counts["skipped"] += 1
            continue
        value = c.get("value", "")
        if not isinstance(value, str):
            value = json.dumps(value)
        storage.set_config(key, value)
        counts["config"] += 1
    
    result = {"status": "success", "source": str(file_path), "imported": counts, "note": "runs and secrets not imported (as per policy)"}
    
    if as_json:
        output_json(result)
    else:
        click.echo(f"✓ Import completed from {file_path.name}")
        for k, v in counts.items():
            click.echo(f"  {k.capitalize()}: {v}")
        click.echo(f"  Note: runs and secrets not imported")

def main() -> None:
    app()

if __name__ == "__main__":
    main()
