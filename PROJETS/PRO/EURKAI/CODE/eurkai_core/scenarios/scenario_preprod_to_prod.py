"""
scenario_preprod_to_prod
Scénario de promotion : preprod → prod.

Usage :
    from scenarios.scenario_preprod_to_prod import run
    result = run({"preprod_env": {...}})

Futur usage via convert() :
    preprod.convert("prod")

Étapes :
  1. validate_input        — vérifie présence et structure minimale de preprod_env
  2. verify_preprod_state  — vérifie artifacts, checks, état exploitable
  3. prepare_prod_config   — prod_path, release_manifest, deployment_plan, publication_targets
  4. simulate_promotion    — passage simulé preprod → prod (pas de déploiement réel)
  5. normalize_output      — garantit champs minimums, évite valeurs manquantes
  6. assemble_result       — retour standardisé {from/to/data/meta}

Sortie data.prod_env :
  {
    "deliverable_type":    "code" | "page" | "document" | "content" | "media",
    "prod_path":           "/…/prod/<slug>_<version>/",
    "release_manifest":    {version, deliverable_type, artifacts, source_preprod,
                            ready_for_backup, ready_for_github},
    "deployment_plan":     {mode, steps},
    "publication_targets": [...],
    "checks":              {artifacts_ok, run_ok, ready}
  }

Note :
  Ce scénario prépare un état prod propre.
  Backup et GitHub viendront dans les scénarios suivants.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Types reconnus
_VALID_TYPES = {"code", "page", "document", "content", "media"}

# Champs minimums requis dans preprod_env
_PREPROD_REQUIRED_FIELDS = {"type", "path", "files", "run_result", "ready"}


# ── Entry point ───────────────────────────────────────────────────────────────

def run(input_data, verbose=True, agent_ident="scenario_preprod_to_prod"):
    """
    Promeut un environnement preprod vers un état prod structuré.

    input_data : {
        "preprod_env": {
            "type":       "code" | "page" | "document" | "content" | "media",
            "path":       str,
            "files":      [{name, path, size}],
            "run_result": {status, output},
            "ready":      bool,
            "note":       str  (optionnel)
        }
    }

    Retourne {status, from, to, data: {prod_env}, meta}.
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

    preprod = val["preprod_env"]
    dtype   = val["deliverable_type"]

    if verbose:
        print(f"  [agent]   {agent_ident} — type:{dtype}")

    # ── Étape 2 — Vérification état preprod ───────────────────────────────────
    verify = _verify_preprod_state(preprod)
    meta["steps"].append(_step_record("verify_preprod_state",
                                       verify["ok"], verify.get("warning")))
    meta["preprod_ready"] = verify["ready"]

    if verbose:
        if verify["ok"]:
            print(f"  [OK]      {agent_ident} — preprod ready:{verify['ready']}")
        else:
            print(f"  [WARN]    {agent_ident} — preprod partiel : {verify.get('warning')}")

    # ── Étape 3 — Configuration prod ──────────────────────────────────────────
    config = _prepare_prod_config(dtype, preprod, verify)
    meta["steps"].append(_step_record("prepare_prod_config", config["ok"], config.get("error")))

    if not config["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — prepare_prod_config : {config['error']}")
        meta["errors"].append(config["error"])
        return _assemble_result("failure", None, meta)

    # ── Étape 4 — Simulation promotion ───────────────────────────────────────
    promo = _simulate_promotion(dtype, preprod, config)
    meta["steps"].append(_step_record("simulate_promotion",
                                       promo["ok"], promo.get("error") if not promo["ok"] else None))
    meta["promotion_steps"] = promo.get("steps_done", [])

    if verbose:
        status_str = "OK" if promo["ok"] else "WARN"
        print(f"  [{status_str}]   {agent_ident} — promotion simulée : {len(promo.get('steps_done', []))} step(s)")

    # ── Étape 5 — Normalisation output ───────────────────────────────────────
    prod_env = _normalize_output(dtype, preprod, config, promo, verify)
    meta["steps"].append(_step_record("normalize_output", True))

    # ── Étape 6 — Assemblage ──────────────────────────────────────────────────
    meta["steps"].append(_step_record("assemble_result", True))

    overall_ready = prod_env["checks"]["ready"]
    status = "success" if overall_ready else "partial"
    return _assemble_result(status, prod_env, meta)


# ── Étapes ────────────────────────────────────────────────────────────────────

def _validate_input(input_data):
    if not isinstance(input_data, dict):
        return {"ok": False, "error": "input_not_a_dict"}

    preprod = input_data.get("preprod_env")
    if not preprod:
        return {"ok": False, "error": "preprod_env_missing"}
    if not isinstance(preprod, dict):
        return {"ok": False, "error": "preprod_env_not_a_dict"}

    # Type obligatoire
    dtype = preprod.get("type") or preprod.get("deliverable_type")
    if not dtype:
        return {"ok": False, "error": "deliverable_type_missing_in_preprod"}

    dtype_norm = _normalize_type(dtype)

    return {
        "ok":               True,
        "preprod_env":      preprod,
        "deliverable_type": dtype_norm,
    }


def _verify_preprod_state(preprod):
    """
    Vérifie que le preprod est exploitable.
    Retourne ok=True même si des éléments sont manquants (non-bloquant),
    mais signale via warning et ajuste ready.
    """
    warnings = []

    # Artifacts
    files = preprod.get("files", [])
    artifacts_ok = bool(files)
    if not artifacts_ok:
        warnings.append("no_files_in_preprod")

    # Run/preview
    run_result = preprod.get("run_result") or {}
    run_ok = run_result.get("status") == "ok"
    if not run_ok:
        warnings.append("run_result_not_ok")

    # Marqueur ready explicite
    explicit_ready = preprod.get("ready", None)
    if explicit_ready is False:
        warnings.append("preprod_ready_false")

    ready = artifacts_ok and run_ok and (explicit_ready is not False)

    return {
        "ok":           True,   # non-bloquant : on continue même si partiel
        "ready":        ready,
        "artifacts_ok": artifacts_ok,
        "run_ok":       run_ok,
        "warnings":     warnings,
        "warning":      ", ".join(warnings) if warnings else None,
    }


def _prepare_prod_config(dtype, preprod, verify):
    """Construit prod_path, release_manifest, deployment_plan, publication_targets."""
    try:
        source_path = preprod.get("path", "unknown")
        slug        = _slug_from_path(source_path)
        version     = _generate_version()

        prod_path = f"prod/{slug}_{version.replace('.', '_')}"

        artifacts = [f["name"] for f in preprod.get("files", [])]

        release_manifest = {
            "version":          version,
            "deliverable_type": dtype,
            "artifacts":        artifacts,
            "source_preprod":   source_path,
            "ready_for_backup": verify["ready"],
            "ready_for_github": verify["ready"] and dtype == "code",
        }

        deployment_plan = _build_deployment_plan(dtype, verify)
        publication_targets = _build_publication_targets(dtype)

        return {
            "ok":                  True,
            "prod_path":           prod_path,
            "version":             version,
            "release_manifest":    release_manifest,
            "deployment_plan":     deployment_plan,
            "publication_targets": publication_targets,
        }
    except Exception as e:
        return {"ok": False, "error": f"prod_config_error:{e}"}


def _simulate_promotion(dtype, preprod, config):
    """Simule le passage preprod → prod sans déploiement réel."""
    steps_done = []

    # Étape générique : promotion des artefacts
    files = preprod.get("files", [])
    if files:
        steps_done.append(f"promote_artifacts ({len(files)} file(s))")

    # Étape : application config prod
    steps_done.append("apply_prod_config")

    # Étape spécifique au type
    type_step = _type_promotion_step(dtype, preprod, config)
    if type_step:
        steps_done.append(type_step)

    # Étape finale : vérification manifest
    steps_done.append("verify_release_manifest")

    return {
        "ok":         True,
        "steps_done": steps_done,
        "mode":       "simulated",
    }


def _normalize_output(dtype, preprod, config, promo, verify):
    """Garantit tous les champs du prod_env, évite les None."""
    checks = {
        "artifacts_ok": verify.get("artifacts_ok", False),
        "run_ok":       verify.get("run_ok", False),
        "ready":        verify.get("ready", False),
    }

    return {
        "deliverable_type":    dtype,
        "prod_path":           config.get("prod_path", "prod/unknown"),
        "release_manifest":    config.get("release_manifest", {}),
        "deployment_plan":     config.get("deployment_plan", {"mode": "simulated", "steps": []}),
        "publication_targets": config.get("publication_targets", []),
        "checks":              checks,
    }


# ── Helpers par type ─────────────────────────────────────────────────────────

def _build_deployment_plan(dtype, verify):
    """Plan de déploiement simulé, adapté au type."""
    base_steps = ["promote_artifacts", "apply_prod_config", "verify_release_manifest"]

    type_steps = {
        "code": [
            "install_dependencies",
            "run_health_check",
            "set_env_variables",
            "start_service",
        ],
        "page": [
            "copy_static_assets",
            "set_base_url",
            "configure_cdn_headers",
        ],
        "document": [
            "copy_to_diffusion_folder",
            "generate_index",
            "tag_version",
        ],
        "content": [
            "package_editorial_content",
            "assign_publication_date",
            "notify_editor",
        ],
        "media": [
            "copy_assets_to_delivery_folder",
            "apply_metadata",
            "generate_asset_manifest",
        ],
    }

    steps = base_steps + type_steps.get(dtype, [])

    return {
        "mode":  "simulated",
        "steps": steps,
        "ready": verify.get("ready", False),
    }


def _build_publication_targets(dtype):
    """Cibles de publication simulées par type."""
    targets = {
        "code": [
            {"target": "github",      "type": "repository",    "status": "pending"},
            {"target": "vps",         "type": "server",        "status": "pending"},
            {"target": "backup",      "type": "archive",       "status": "pending"},
        ],
        "page": [
            {"target": "github_pages","type": "static_hosting","status": "pending"},
            {"target": "cdn",         "type": "edge_network",  "status": "pending"},
        ],
        "document": [
            {"target": "shared_drive","type": "file_storage",  "status": "pending"},
            {"target": "email",       "type": "distribution",  "status": "pending"},
        ],
        "content": [
            {"target": "cms",         "type": "content_system","status": "pending"},
            {"target": "newsletter",  "type": "email_blast",   "status": "pending"},
        ],
        "media": [
            {"target": "asset_library","type": "dam",          "status": "pending"},
            {"target": "delivery_cdn", "type": "edge_network", "status": "pending"},
        ],
    }
    return targets.get(dtype, [{"target": "generic", "type": "unknown", "status": "pending"}])


def _type_promotion_step(dtype, preprod, config):
    """Étape de promotion spécifique au type (pour simulate_promotion)."""
    steps = {
        "code":     "validate_syntax_and_tests",
        "page":     "build_static_bundle",
        "document": "finalize_document_version",
        "content":  "package_content_bundle",
        "media":    "finalize_asset_delivery",
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
    """Extrait un slug depuis le chemin preprod (dernier segment sans timestamp)."""
    name = Path(str(path_str)).name
    # Retire le timestamp _YYYYMMDD_HHMMSS si présent
    name = re.sub(r"_\d{8}_\d{6}$", "", name)
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return name[:32] or "deliverable"


def _generate_version():
    """Version 0.1.0 par défaut pour la première release."""
    return "0.1.0"


def _assemble_result(status, prod_env, meta):
    return {
        "status": status,
        "from":   "preprod",
        "to":     "prod",
        "data":   {"prod_env": prod_env} if prod_env else {},
        "meta":   meta,
    }


def _step_record(name, ok, error=None):
    record = {"step": name, "status": "ok" if ok else "failure"}
    if error:
        record["error"] = error
    return record


# ── Smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    _PREPROD_CODE = {
        "preprod_env": {
            "type":       "code",
            "path":       "/tmp/eurkai_preprod/invoicemodule_20260407_012302",
            "files":      [
                {"name": "invoice_module.py", "path": "/tmp/eurkai_preprod/invoice_module.py", "size": 220},
                {"name": "requirements.txt",  "path": "/tmp/eurkai_preprod/requirements.txt",  "size": 60},
                {"name": "README.md",         "path": "/tmp/eurkai_preprod/README.md",         "size": 180},
            ],
            "run_result": {"status": "ok", "output": "Syntaxe Python : OK\nScore : 100/100"},
            "ready":      True,
            "note":       "Module principal généré.",
        }
    }

    _PREPROD_PAGE = {
        "preprod_env": {
            "type":       "page",
            "path":       "/tmp/eurkai_preprod/page_20260407_012302",
            "files":      [
                {"name": "preview.html", "path": "/tmp/eurkai_preprod/preview.html", "size": 2825},
            ],
            "run_result": {"status": "ok", "output": "Preview généré : preview.html (2825 bytes)"},
            "ready":      True,
            "note":       "Preview HTML local.",
        }
    }

    _PREPROD_PARTIAL = {
        "preprod_env": {
            "type":       "document",
            "path":       "/tmp/eurkai_preprod/document_20260407_012302",
            "files":      [],            # pas d'artifacts — state partiel
            "run_result": {"status": "error", "output": ""},
            "ready":      False,
        }
    }

    _PREPROD_CONTENT = {
        "preprod_env": {
            "type":       "content",
            "path":       "/tmp/eurkai_preprod/content_20260407_012302",
            "files":      [
                {"name": "content_brief.md", "path": "/tmp/eurkai_preprod/content_brief.md", "size": 340},
            ],
            "run_result": {"status": "ok", "output": "Brief éditorial : 4 pièces planifiées."},
            "ready":      True,
        }
    }

    cases = [
        {"label": "✓ Code     (ready)",    "input": _PREPROD_CODE},
        {"label": "✓ Page     (ready)",    "input": _PREPROD_PAGE},
        {"label": "~ Document (partiel)",  "input": _PREPROD_PARTIAL},
        {"label": "✓ Content  (ready)",    "input": _PREPROD_CONTENT},
        {"label": "✗ env manquant",        "input": {}},
        {"label": "✗ input invalide",      "input": "not a dict"},
    ]

    print("=" * 65)
    print("  scenario_preprod_to_prod — smoke test")
    print("=" * 65)

    passed = failed = 0
    for case in cases:
        r = run(case["input"], verbose=False)
        ok = r["status"] in ("success", "partial")
        print(f"\n{case['label']}")
        print(f"  status      : {r['status']}")
        print(f"  from→to     : {r['from']} → {r['to']}")
        print(f"  steps       : {[s['step'] + ':' + s['status'] for s in r['meta']['steps']]}")
        if r.get("data", {}).get("prod_env"):
            env = r["data"]["prod_env"]
            print(f"  dtype       : {env['deliverable_type']}")
            print(f"  prod_path   : {env['prod_path']}")
            print(f"  version     : {env['release_manifest'].get('version')}")
            print(f"  artifacts   : {env['release_manifest'].get('artifacts')}")
            print(f"  deploy_steps: {env['deployment_plan']['steps'][:3]}…")
            print(f"  pub_targets : {[t['target'] for t in env['publication_targets']]}")
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
