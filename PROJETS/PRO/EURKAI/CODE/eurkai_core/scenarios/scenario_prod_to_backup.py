"""
scenario_prod_to_backup
Scénario de sauvegarde : prod → backup.

Usage :
    from scenarios.scenario_prod_to_backup import run
    result = run({"prod_env": {...}})

Futur usage via convert() :
    prod.convert("backup")

Étapes :
  1. validate_input       — vérifie présence et structure minimale de prod_env
  2. verify_prod_state    — vérifie checks, artifacts via manifest, état exploitable
  3. prepare_backup_config — backup_path, backup_manifest, restore_plan
  4. simulate_backup      — archivage simulé (pas de stockage externe réel)
  5. normalize_output     — garantit champs minimums, évite valeurs manquantes
  6. assemble_result      — retour standardisé {from/to/data/meta}

Sortie data.backup_env :
  {
    "deliverable_type":    "code" | "page" | "document" | "content" | "media",
    "backup_path":         "backup/<slug>_<version>/",
    "backup_manifest":     {version, deliverable_type, source_prod,
                            archived_artifacts, ready_for_github, restorable},
    "archived_artifacts":  [...],
    "restore_plan":        {mode, steps},
    "checks":              {artifacts_ok, prod_ready, restorable}
  }

Note :
  Ce scénario prépare un backup propre et restaurable.
  GitHub viendra dans le scénario suivant.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

_VALID_TYPES = {"code", "page", "document", "content", "media"}


# ── Entry point ───────────────────────────────────────────────────────────────

def run(input_data, verbose=True, agent_ident="scenario_prod_to_backup"):
    """
    Prépare un backup structuré depuis un environnement prod.

    input_data : {
        "prod_env": {
            "deliverable_type":    str,
            "prod_path":           str,
            "release_manifest":    dict,
            "deployment_plan":     dict,
            "publication_targets": list,
            "checks":              dict
        }
    }

    Retourne {status, from, to, data: {backup_env}, meta}.
    """
    meta = {"steps": [], "errors": []}

    # ── Étape 1 — Validation input ────────────────────────────────────────────
    val = _validate_input(input_data)
    meta["steps"].append(_step_record("validate_input", val["ok"], val.get("error")))

    if not val["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — validate_input : {val['error']}")
        meta["errors"].append(val["error"])
        return _assemble_result("failure", None, meta)

    prod    = val["prod_env"]
    dtype   = val["deliverable_type"]

    if verbose:
        print(f"  [agent]   {agent_ident} — type:{dtype}")

    # ── Étape 2 — Vérification état prod ──────────────────────────────────────
    verify = _verify_prod_state(prod)
    meta["steps"].append(_step_record("verify_prod_state",
                                       verify["ok"], verify.get("warning")))
    meta["prod_ready"] = verify["prod_ready"]

    if verbose:
        flag = "OK" if verify["prod_ready"] else "WARN"
        print(f"  [{flag}]   {agent_ident} — prod ready:{verify['prod_ready']}")

    # ── Étape 3 — Configuration backup ───────────────────────────────────────
    config = _prepare_backup_config(dtype, prod, verify)
    meta["steps"].append(_step_record("prepare_backup_config",
                                       config["ok"], config.get("error")))

    if not config["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — prepare_backup_config : {config['error']}")
        meta["errors"].append(config["error"])
        return _assemble_result("failure", None, meta)

    # ── Étape 4 — Simulation backup ───────────────────────────────────────────
    sim = _simulate_backup(dtype, prod, config)
    meta["steps"].append(_step_record("simulate_backup",
                                       sim["ok"], sim.get("error") if not sim["ok"] else None))
    meta["archived_count"] = sim.get("archived_count", 0)

    if verbose:
        flag = "OK" if sim["ok"] else "WARN"
        print(f"  [{flag}]   {agent_ident} — backup simulé : {sim.get('archived_count', 0)} artifact(s)")

    # ── Étape 5 — Normalisation output ───────────────────────────────────────
    backup_env = _normalize_output(dtype, prod, config, sim, verify)
    meta["steps"].append(_step_record("normalize_output", True))

    # ── Étape 6 — Assemblage ──────────────────────────────────────────────────
    meta["steps"].append(_step_record("assemble_result", True))

    restorable = backup_env["checks"]["restorable"]
    status = "success" if restorable else "partial"
    return _assemble_result(status, backup_env, meta)


# ── Étapes ────────────────────────────────────────────────────────────────────

def _validate_input(input_data):
    if not isinstance(input_data, dict):
        return {"ok": False, "error": "input_not_a_dict"}

    prod = input_data.get("prod_env")
    if not prod:
        return {"ok": False, "error": "prod_env_missing"}
    if not isinstance(prod, dict):
        return {"ok": False, "error": "prod_env_not_a_dict"}

    dtype = prod.get("deliverable_type")
    if not dtype:
        return {"ok": False, "error": "deliverable_type_missing_in_prod"}

    return {
        "ok":               True,
        "prod_env":         prod,
        "deliverable_type": _normalize_type(dtype),
    }


def _verify_prod_state(prod):
    """
    Vérifie que le prod est exploitable pour un backup.
    Non-bloquant : retourne ok=True même si partiel.
    """
    warnings = []

    # Checks explicites depuis prod_env
    checks = prod.get("checks", {})
    prod_ready = checks.get("ready", False)
    if not prod_ready:
        warnings.append("prod_ready_false")

    # Artifacts implicites via release_manifest
    manifest  = prod.get("release_manifest", {})
    artifacts = manifest.get("artifacts", [])
    artifacts_ok = bool(artifacts)
    if not artifacts_ok:
        warnings.append("no_artifacts_in_manifest")

    # Vérification version présente
    version = manifest.get("version", "")
    if not version:
        warnings.append("version_missing_in_manifest")

    return {
        "ok":           True,   # non-bloquant
        "prod_ready":   prod_ready,
        "artifacts_ok": artifacts_ok,
        "artifacts":    artifacts,
        "version":      version or "0.1.0",
        "warnings":     warnings,
        "warning":      ", ".join(warnings) if warnings else None,
    }


def _prepare_backup_config(dtype, prod, verify):
    """Construit backup_path, backup_manifest, restore_plan."""
    try:
        prod_path = prod.get("prod_path", "prod/unknown")
        slug      = _slug_from_path(prod_path)
        version   = verify.get("version", "0.1.0")

        backup_path = f"backup/{slug}_{version.replace('.', '_')}"

        artifacts = verify.get("artifacts", [])
        manifest  = prod.get("release_manifest", {})

        backup_manifest = {
            "version":             version,
            "deliverable_type":    dtype,
            "source_prod":         prod_path,
            "archived_artifacts":  artifacts,
            "ready_for_github":    manifest.get("ready_for_github", False),
            "restorable":          bool(artifacts),
        }

        restore_plan = _build_restore_plan(dtype, artifacts)

        return {
            "ok":               True,
            "backup_path":      backup_path,
            "version":          version,
            "backup_manifest":  backup_manifest,
            "restore_plan":     restore_plan,
        }
    except Exception as e:
        return {"ok": False, "error": f"backup_config_error:{e}"}


def _simulate_backup(dtype, prod, config):
    """Simule l'archivage des artifacts (pas de stockage réel)."""
    artifacts = config["backup_manifest"].get("archived_artifacts", [])
    steps_done = []

    if artifacts:
        steps_done.append(f"archive_artifacts ({len(artifacts)} file(s))")
    else:
        steps_done.append("archive_artifacts (0 — skipped)")

    steps_done.append("write_backup_manifest")

    type_step = _type_backup_step(dtype)
    if type_step:
        steps_done.append(type_step)

    steps_done.append("verify_backup_integrity")

    return {
        "ok":             True,
        "steps_done":     steps_done,
        "archived_count": len(artifacts),
    }


def _normalize_output(dtype, prod, config, sim, verify):
    """Garantit tous les champs du backup_env, évite les None."""
    artifacts = config["backup_manifest"].get("archived_artifacts", [])
    restorable = bool(artifacts) and verify.get("prod_ready", False)

    checks = {
        "artifacts_ok": verify.get("artifacts_ok", False),
        "prod_ready":   verify.get("prod_ready", False),
        "restorable":   restorable,
    }

    return {
        "deliverable_type":    dtype,
        "backup_path":         config.get("backup_path", "backup/unknown"),
        "backup_manifest":     config.get("backup_manifest", {}),
        "archived_artifacts":  artifacts,
        "restore_plan":        config.get("restore_plan", {"mode": "simulated", "steps": []}),
        "checks":              checks,
    }


# ── Helpers par type ──────────────────────────────────────────────────────────

def _build_restore_plan(dtype, artifacts):
    """Plan de restauration simulé, adapté au type."""
    base_steps = ["restore_artifacts", "restore_manifest", "verify_integrity"]

    type_steps = {
        "code": [
            "install_dependencies",
            "restore_env_variables",
            "run_smoke_test",
        ],
        "page": [
            "restore_static_assets",
            "reconfigure_base_url",
        ],
        "document": [
            "restore_document_index",
            "verify_document_versions",
        ],
        "content": [
            "restore_editorial_metadata",
            "reschedule_publication",
        ],
        "media": [
            "restore_asset_metadata",
            "rebuild_asset_manifest",
        ],
    }

    return {
        "mode":  "simulated",
        "steps": base_steps + type_steps.get(dtype, []),
    }


def _type_backup_step(dtype):
    """Étape d'archivage spécifique au type."""
    steps = {
        "code":     "archive_executable_package",
        "page":     "archive_static_bundle",
        "document": "archive_document_index",
        "content":  "archive_editorial_package",
        "media":    "archive_asset_delivery_pack",
    }
    return steps.get(dtype)


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _normalize_type(raw_type):
    t = str(raw_type).lower().strip()
    if t in _VALID_TYPES:
        return t
    _aliases = {
        "html": "page", "landing": "page", "ui": "page",
        "python": "code", "script": "code", "module": "code",
        "doc": "document", "guide": "document", "report": "document",
        "copy": "content", "article": "content", "blog": "content",
        "asset": "media", "image": "media", "visual": "media",
    }
    return _aliases.get(t, "code")


def _slug_from_path(path_str):
    name = Path(str(path_str)).name
    name = re.sub(r"_\d{1,3}_\d{1,3}_\d{1,3}$", "", name)   # retire _0_1_0
    name = re.sub(r"_\d{8}_\d{6}$", "", name)                 # retire timestamp
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return name[:32] or "deliverable"


def _assemble_result(status, backup_env, meta):
    return {
        "status": status,
        "from":   "prod",
        "to":     "backup",
        "data":   {"backup_env": backup_env} if backup_env else {},
        "meta":   meta,
    }


def _step_record(name, ok, error=None):
    record = {"step": name, "status": "ok" if ok else "failure"}
    if error:
        record["error"] = error
    return record


# ── Smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    _PROD_CODE = {
        "prod_env": {
            "deliverable_type":    "code",
            "prod_path":           "prod/invoicemodule_0_1_0",
            "release_manifest":    {
                "version":          "0.1.0",
                "deliverable_type": "code",
                "artifacts":        ["invoice_module.py", "requirements.txt", "README.md"],
                "source_preprod":   "/tmp/preprod/invoicemodule_20260407",
                "ready_for_backup": True,
                "ready_for_github": True,
            },
            "deployment_plan":     {"mode": "simulated", "steps": ["promote_artifacts"]},
            "publication_targets": [{"target": "github"}, {"target": "vps"}],
            "checks":              {"artifacts_ok": True, "run_ok": True, "ready": True},
        }
    }

    _PROD_PAGE = {
        "prod_env": {
            "deliverable_type":    "page",
            "prod_path":           "prod/page_0_1_0",
            "release_manifest":    {
                "version":          "0.1.0",
                "deliverable_type": "page",
                "artifacts":        ["preview.html"],
                "source_preprod":   "/tmp/preprod/page_20260407",
                "ready_for_backup": True,
                "ready_for_github": False,
            },
            "deployment_plan":     {"mode": "simulated", "steps": ["copy_static_assets"]},
            "publication_targets": [{"target": "github_pages"}, {"target": "cdn"}],
            "checks":              {"artifacts_ok": True, "run_ok": True, "ready": True},
        }
    }

    _PROD_PARTIAL = {
        "prod_env": {
            "deliverable_type":    "document",
            "prod_path":           "prod/document_0_1_0",
            "release_manifest":    {
                "version":          "0.1.0",
                "deliverable_type": "document",
                "artifacts":        [],              # pas d'artifacts
                "source_preprod":   "/tmp/preprod/document_20260407",
                "ready_for_backup": False,
                "ready_for_github": False,
            },
            "deployment_plan":     {"mode": "simulated", "steps": []},
            "publication_targets": [],
            "checks":              {"artifacts_ok": False, "run_ok": False, "ready": False},
        }
    }

    _PROD_MEDIA = {
        "prod_env": {
            "deliverable_type":    "media",
            "prod_path":           "prod/media_0_1_0",
            "release_manifest":    {
                "version":          "0.1.0",
                "deliverable_type": "media",
                "artifacts":        ["logo.svg", "banner.png", "icon.png"],
                "source_preprod":   "/tmp/preprod/media_20260407",
                "ready_for_backup": True,
                "ready_for_github": False,
            },
            "deployment_plan":     {"mode": "simulated", "steps": ["copy_assets_to_delivery_folder"]},
            "publication_targets": [{"target": "asset_library"}, {"target": "delivery_cdn"}],
            "checks":              {"artifacts_ok": True, "run_ok": True, "ready": True},
        }
    }

    cases = [
        {"label": "✓ Code     (ready)",   "input": _PROD_CODE},
        {"label": "✓ Page     (ready)",   "input": _PROD_PAGE},
        {"label": "~ Document (partiel)", "input": _PROD_PARTIAL},
        {"label": "✓ Media    (ready)",   "input": _PROD_MEDIA},
        {"label": "✗ env manquant",       "input": {}},
        {"label": "✗ input invalide",     "input": "not a dict"},
    ]

    print("=" * 65)
    print("  scenario_prod_to_backup — smoke test")
    print("=" * 65)

    passed = failed = 0
    for case in cases:
        r = run(case["input"], verbose=False)
        ok = r["status"] in ("success", "partial")
        print(f"\n{case['label']}")
        print(f"  status      : {r['status']}")
        print(f"  from→to     : {r['from']} → {r['to']}")
        print(f"  steps       : {[s['step'] + ':' + s['status'] for s in r['meta']['steps']]}")
        if r.get("data", {}).get("backup_env"):
            env = r["data"]["backup_env"]
            print(f"  dtype       : {env['deliverable_type']}")
            print(f"  backup_path : {env['backup_path']}")
            print(f"  version     : {env['backup_manifest'].get('version')}")
            print(f"  artifacts   : {env['archived_artifacts']}")
            print(f"  restore     : {env['restore_plan']['steps'][:3]}…")
            print(f"  checks      : {env['checks']}")
        if r["meta"].get("errors"):
            print(f"  errors      : {r['meta']['errors']}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 65}")
    print(f"  {passed}/{passed + failed} passed ({failed} failures intentionnelles)")
    print("=" * 65)
