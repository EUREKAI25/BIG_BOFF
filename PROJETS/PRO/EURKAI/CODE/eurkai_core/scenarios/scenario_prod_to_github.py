"""
scenario_prod_to_github
Scénario de publication : prod → github (simulation).

Usage :
    from scenarios.scenario_prod_to_github import run
    result = run({"prod_env": {...}})

Futur usage via convert() :
    prod.convert("github")

Étapes :
  1. validate_input         — vérifie présence et structure de prod_env
  2. prepare_repo_config    — repo_name, branch, commit_message, files à publier
  3. simulate_git_operations — init → add → commit → push (simulé)
  4. normalize_output       — garantit champs minimums
  5. assemble_result        — retour standardisé {from/to/data/meta}

Sortie data.github_env :
  {
    "repo_name":      str,
    "repo_path":      str,
    "branch":         "main",
    "commit_message": str,
    "files":          [...],
    "manifest":       {repo_name, version, deliverable_type, artifacts,
                       commit_message, branch, simulated},
    "ready":          bool
  }

Note :
  Pas de vrai git, pas d'API GitHub, pas de réseau.
  Simulation structurée uniquement.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

_VALID_TYPES = {"code", "page", "document", "content", "media"}


# ── Entry point ───────────────────────────────────────────────────────────────

def run(input_data, verbose=True, agent_ident="scenario_prod_to_github"):
    """
    Prépare une publication GitHub simulée depuis un environnement prod.

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

    Retourne {status, from, to, data: {github_env}, meta}.
    """
    meta = {"steps": [], "errors": []}

    # ── Étape 1 — Validation ──────────────────────────────────────────────────
    val = _validate_input(input_data)
    meta["steps"].append(_step_record("validate_input", val["ok"], val.get("error")))

    if not val["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — validate_input : {val['error']}")
        meta["errors"].append(val["error"])
        return _assemble_result("failure", None, meta)

    prod  = val["prod_env"]
    dtype = val["deliverable_type"]

    if verbose:
        print(f"  [agent]   {agent_ident} — type:{dtype}")

    # ── Étape 2 — Configuration repo ──────────────────────────────────────────
    config = _prepare_repo_config(dtype, prod)
    meta["steps"].append(_step_record("prepare_repo_config",
                                       config["ok"], config.get("error")))

    if not config["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — prepare_repo_config : {config['error']}")
        meta["errors"].append(config["error"])
        return _assemble_result("failure", None, meta)

    if verbose:
        print(f"  [OK]      {agent_ident} — repo:{config['repo_name']} branch:{config['branch']}")

    # ── Étape 3 — Simulation opérations git ───────────────────────────────────
    git = _simulate_git_operations(config)
    meta["steps"].append(_step_record("simulate_git_operations",
                                       git["ok"], git.get("error") if not git["ok"] else None))
    meta["git_steps"] = git.get("steps_done", [])

    if verbose:
        flag = "OK" if git["ok"] else "WARN"
        print(f"  [{flag}]   {agent_ident} — git simulé : {len(git.get('steps_done', []))} step(s)")

    # ── Étape 4 — Normalisation output ───────────────────────────────────────
    github_env = _normalize_output(dtype, prod, config, git)
    meta["steps"].append(_step_record("normalize_output", True))

    # ── Étape 5 — Assemblage ──────────────────────────────────────────────────
    meta["steps"].append(_step_record("assemble_result", True))

    status = "success" if github_env["ready"] else "partial"
    return _assemble_result(status, github_env, meta)


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

    # Vérification checks : ready_for_github si présent dans manifest
    manifest = prod.get("release_manifest", {})
    ready_for_github = manifest.get("ready_for_github", True)
    if ready_for_github is False:
        return {"ok": False, "error": "manifest_not_ready_for_github"}

    return {
        "ok":               True,
        "prod_env":         prod,
        "deliverable_type": _normalize_type(dtype),
    }


def _prepare_repo_config(dtype, prod):
    """Construit repo_name, branch, commit_message, liste de fichiers à publier."""
    try:
        manifest  = prod.get("release_manifest", {})
        prod_path = prod.get("prod_path", "prod/unknown")
        version   = manifest.get("version", "0.1.0")
        artifacts = manifest.get("artifacts", [])

        repo_name      = _build_repo_name(prod_path, dtype)
        repo_path      = f"github/{repo_name}"
        branch         = "main"
        commit_message = _build_commit_message(dtype, version, artifacts)
        files          = _build_file_list(dtype, artifacts, prod_path)

        return {
            "ok":             True,
            "repo_name":      repo_name,
            "repo_path":      repo_path,
            "branch":         branch,
            "commit_message": commit_message,
            "files":          files,
            "version":        version,
            "artifacts":      artifacts,
        }
    except Exception as e:
        return {"ok": False, "error": f"repo_config_error:{e}"}


def _simulate_git_operations(config):
    """Simule init → add → commit → push."""
    steps_done = []
    files = config.get("files", [])

    steps_done.append(f"git init {config['repo_name']}")
    steps_done.append(f"git checkout -b {config['branch']}")

    if files:
        steps_done.append(f"git add {len(files)} file(s)")
    else:
        steps_done.append("git add (0 files — skipped)")

    steps_done.append(f"git commit -m \"{config['commit_message'][:60]}\"")
    steps_done.append(f"git push origin {config['branch']}  [SIMULATED]")

    return {
        "ok":         True,
        "steps_done": steps_done,
        "files_added": len(files),
    }


def _normalize_output(dtype, prod, config, git):
    """Garantit tous les champs du github_env."""
    manifest = prod.get("release_manifest", {})
    artifacts = config.get("artifacts", [])
    files_added = git.get("files_added", 0)
    ready = files_added > 0 and git["ok"]

    github_manifest = {
        "repo_name":       config.get("repo_name", "unknown"),
        "version":         config.get("version", "0.1.0"),
        "deliverable_type": dtype,
        "artifacts":       artifacts,
        "commit_message":  config.get("commit_message", ""),
        "branch":          config.get("branch", "main"),
        "simulated":       True,
    }

    return {
        "repo_name":      config.get("repo_name", "unknown"),
        "repo_path":      config.get("repo_path", "github/unknown"),
        "branch":         config.get("branch", "main"),
        "commit_message": config.get("commit_message", ""),
        "files":          config.get("files", []),
        "manifest":       github_manifest,
        "ready":          ready,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_repo_name(prod_path, dtype):
    """Génère un nom de repo depuis le prod_path."""
    name = Path(str(prod_path)).name
    # Retire version _0_1_0 ou timestamp
    name = re.sub(r"_\d{1,3}_\d{1,3}_\d{1,3}$", "", name)
    name = re.sub(r"_\d{8}_\d{6}$", "", name)
    name = re.sub(r"[^a-zA-Z0-9_-]", "-", name)
    name = re.sub(r"-+", "-", name).strip("-").lower()
    name = name[:40] or f"eurkai-{dtype}"
    # Préfixe eurkai- si absent
    if not name.startswith("eurkai-"):
        name = f"eurkai-{name}"
    return name


def _build_commit_message(dtype, version, artifacts):
    """Génère un message de commit lisible."""
    count = len(artifacts)
    type_labels = {
        "code":     "feat",
        "page":     "feat",
        "document": "docs",
        "content":  "content",
        "media":    "assets",
    }
    prefix = type_labels.get(dtype, "feat")
    return f"{prefix}({dtype}): release v{version} — {count} artifact(s)"


def _build_file_list(dtype, artifacts, prod_path):
    """Construit la liste des fichiers à publier."""
    files = []

    # Artifacts du manifest
    for name in artifacts:
        files.append({
            "name":   name,
            "source": f"{prod_path}/{name}",
            "dest":   name,
        })

    # Fichiers systématiques selon le type
    type_extras = {
        "code": [
            {"name": "README.md",      "source": f"{prod_path}/README.md",      "dest": "README.md"},
            {"name": ".gitignore",     "source": "generated",                    "dest": ".gitignore"},
        ],
        "page": [
            {"name": "index.html",     "source": f"{prod_path}/preview.html",   "dest": "index.html"},
        ],
        "document": [
            {"name": "README.md",      "source": f"{prod_path}/README.md",      "dest": "README.md"},
        ],
        "content": [
            {"name": "CONTENT.md",     "source": f"{prod_path}/content_brief.md", "dest": "CONTENT.md"},
        ],
        "media": [
            {"name": "MEDIA_SPEC.md",  "source": f"{prod_path}/media_spec.md",  "dest": "MEDIA_SPEC.md"},
        ],
    }

    extras = type_extras.get(dtype, [])
    # Évite les doublons (si README déjà dans artifacts)
    existing_names = {f["name"] for f in files}
    for extra in extras:
        if extra["name"] not in existing_names:
            files.append(extra)

    return files


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


def _assemble_result(status, github_env, meta):
    return {
        "status": status,
        "from":   "prod",
        "to":     "github",
        "data":   {"github_env": github_env} if github_env else {},
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
            "deployment_plan":     {"mode": "simulated", "steps": []},
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
                "ready_for_github": True,
            },
            "deployment_plan":     {"mode": "simulated", "steps": []},
            "publication_targets": [{"target": "github_pages"}],
            "checks":              {"artifacts_ok": True, "run_ok": True, "ready": True},
        }
    }

    _PROD_MEDIA = {
        "prod_env": {
            "deliverable_type":    "media",
            "prod_path":           "prod/media_0_1_0",
            "release_manifest":    {
                "version":          "0.1.0",
                "deliverable_type": "media",
                "artifacts":        ["logo.svg", "banner.png"],
                "source_preprod":   "/tmp/preprod/media_20260407",
                "ready_for_backup": True,
                "ready_for_github": True,
            },
            "deployment_plan":     {"mode": "simulated", "steps": []},
            "publication_targets": [{"target": "asset_library"}],
            "checks":              {"artifacts_ok": True, "run_ok": True, "ready": True},
        }
    }

    _PROD_NOT_READY = {
        "prod_env": {
            "deliverable_type":    "code",
            "prod_path":           "prod/draft_0_1_0",
            "release_manifest":    {
                "version":          "0.1.0",
                "deliverable_type": "code",
                "artifacts":        [],
                "ready_for_github": False,   # bloquant
            },
            "deployment_plan":     {},
            "publication_targets": [],
            "checks":              {"ready": False},
        }
    }

    cases = [
        {"label": "✓ Code  (ready)",       "input": _PROD_CODE},
        {"label": "✓ Page  (ready)",       "input": _PROD_PAGE},
        {"label": "✓ Media (ready)",       "input": _PROD_MEDIA},
        {"label": "✗ not ready_for_github","input": _PROD_NOT_READY},
        {"label": "✗ env manquant",        "input": {}},
        {"label": "✗ input invalide",      "input": "not a dict"},
    ]

    print("=" * 65)
    print("  scenario_prod_to_github — smoke test")
    print("=" * 65)

    passed = failed = 0
    for case in cases:
        r = run(case["input"], verbose=False)
        ok = r["status"] in ("success", "partial")
        print(f"\n{case['label']}")
        print(f"  status   : {r['status']}")
        print(f"  from→to  : {r['from']} → {r['to']}")
        print(f"  steps    : {[s['step'] + ':' + s['status'] for s in r['meta']['steps']]}")
        if r.get("data", {}).get("github_env"):
            env = r["data"]["github_env"]
            print(f"  repo     : {env['repo_name']}")
            print(f"  branch   : {env['branch']}")
            print(f"  commit   : {env['commit_message']}")
            print(f"  files    : {[f['name'] for f in env['files']]}")
            print(f"  ready    : {env['ready']}")
        if r["meta"].get("errors"):
            print(f"  errors   : {r['meta']['errors']}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 65}")
    print(f"  {passed}/{passed + failed} passed ({failed} failures intentionnelles)")
    print("=" * 65)
