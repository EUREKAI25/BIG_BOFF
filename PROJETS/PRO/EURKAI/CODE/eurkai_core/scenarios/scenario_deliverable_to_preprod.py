"""
scenario_deliverable_to_preprod
Scénario de delivery : deliverable → environnement de préproduction.

Usage direct :
    from scenarios.scenario_deliverable_to_preprod import run
    result = run({"deliverable_type": "code", "deliverable": {...}})

Futur usage via convert() :
    deliverable.convert("preprod")

Étapes :
  1. validate_input          — vérifie présence deliverable_type + deliverable
  2. detect_deliverable_type — normalise le type (code/page/document/content/media)
  3. prepare_environment     — crée le dossier preprod + structure de fichiers
  4. materialize_deliverable — écrit le contenu dans les fichiers
  5. simulate_preview_or_run — validation/preview simulée selon le type
  6. assemble_result         — retour standardisé {from/to/data/meta}

Note :
  Pas de déploiement réel. Simulation locale dans un dossier preprod.
  Le dossier est créé dans <base_path>/<slug>_<timestamp>/
  Par défaut : CODE/eurkai_core/preprod/

Sortie data.preprod_env :
  {
    "type":       "code",
    "path":       "/…/preprod/invoice_module_20260407_1234/",
    "files":      [{"name": "…", "path": "…", "size": int}],
    "run_result": {"status": "ok"|"error", "output": str},
    "ready":      bool,
    "note":       str,
  }
"""

import ast
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Dossier preprod par défaut (relatif au fichier courant → CODE/eurkai_core/preprod/)
_DEFAULT_BASE = Path(__file__).parent.parent / "preprod"

# Types reconnus
_VALID_TYPES = {"code", "page", "document", "content", "media"}


# ── Entry point ───────────────────────────────────────────────────────────────

def run(input_data, base_path=None, verbose=True,
        agent_ident="scenario_deliverable_to_preprod"):
    """
    Prépare un environnement de préproduction pour un deliverable.

    input_data : {
        "deliverable_type": "code" | "page" | "document" | "content" | "media",
        "deliverable":      {...}   (sortie de scenario_specs_to_deliverable)
    }
    base_path  : Path ou str — dossier racine preprod (défaut: eurkai_core/preprod/)

    Retourne {status, from, to, data: {preprod_env}, meta}.
    """
    meta      = {"steps": [], "errors": []}
    base_path = Path(base_path) if base_path else _DEFAULT_BASE

    # ── Étape 1 — Validation ──────────────────────────────────────────────────
    val = _validate_input(input_data)
    meta["steps"].append(_step_record("validate_input", val["ok"], val.get("error")))

    if not val["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — validate_input : {val['error']}")
        meta["errors"].append(val["error"])
        return _assemble_result("failure", None, meta)

    raw_type   = val["deliverable_type"]
    deliverable = val["deliverable"]

    # ── Étape 2 — Normalisation du type ──────────────────────────────────────
    dtype = _normalize_type(raw_type)
    meta["steps"].append(_step_record("detect_deliverable_type", True))
    meta["deliverable_type"] = dtype

    if verbose:
        print(f"  [agent]   {agent_ident} — type:{dtype}")

    # ── Étape 3 — Préparation de l'environnement ──────────────────────────────
    env = _prepare_environment(dtype, deliverable, base_path)
    meta["steps"].append(_step_record("prepare_environment", env["ok"], env.get("error")))

    if not env["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — prepare_environment : {env['error']}")
        meta["errors"].append(env["error"])
        return _assemble_result("failure", None, meta)

    preprod_path = env["path"]

    # ── Étape 4 — Matérialisation du livrable ─────────────────────────────────
    mat = _materialize_deliverable(dtype, deliverable, preprod_path)
    meta["steps"].append(_step_record("materialize_deliverable", mat["ok"], mat.get("error")))
    meta["files_written"] = len(mat.get("files", []))

    if not mat["ok"]:
        if verbose:
            print(f"  [WARN]    {agent_ident} — materialize : {mat.get('error')}")
        # Non bloquant : on continue avec les fichiers écrits

    # ── Étape 5 — Simulation preview / run ───────────────────────────────────
    sim = _simulate(dtype, deliverable, preprod_path, mat.get("files", []))
    meta["steps"].append(_step_record("simulate_preview_or_run",
                                       sim["ok"], sim.get("error") if not sim["ok"] else None))

    if verbose:
        status_str = "OK" if sim["ok"] else "WARN"
        print(f"  [{status_str}]   {agent_ident} — {dtype} preprod @ {preprod_path.name}")
        if sim.get("output"):
            print(f"  [SIM]     {sim['output'][:80]}")

    # ── Étape 6 — Assemblage ──────────────────────────────────────────────────
    meta["steps"].append(_step_record("assemble_result", True))

    preprod_env = {
        "type":        dtype,
        "path":        str(preprod_path),
        "files":       mat.get("files", []),
        "run_result":  {"status": "ok" if sim["ok"] else "error",
                        "output": sim.get("output", "")},
        "ready":       sim["ok"] and mat["ok"],
        "note":        sim.get("note", ""),
    }

    status = "success" if preprod_env["ready"] else "partial"
    return _assemble_result(status, preprod_env, meta)


# ── Étapes ────────────────────────────────────────────────────────────────────

def _validate_input(input_data):
    if not isinstance(input_data, dict):
        return {"ok": False, "error": "input_not_a_dict"}
    dtype = input_data.get("deliverable_type")
    if not dtype:
        return {"ok": False, "error": "deliverable_type_missing"}
    deliv = input_data.get("deliverable")
    if not deliv or not isinstance(deliv, dict):
        return {"ok": False, "error": "deliverable_missing_or_invalid"}
    return {"ok": True, "deliverable_type": dtype, "deliverable": deliv}


def _normalize_type(raw_type):
    t = str(raw_type).lower().strip()
    if t in _VALID_TYPES:
        return t
    # Tentative de mapping
    _aliases = {
        "html": "page", "landing": "page", "ui": "page",
        "python": "code", "script": "code", "module": "code",
        "doc": "document", "guide": "document", "report": "document",
        "copy": "content", "article": "content", "blog": "content",
        "asset": "media", "image": "media", "visual": "media",
    }
    return _aliases.get(t, "code")


def _prepare_environment(dtype, deliverable, base_path):
    """Crée le dossier preprod pour ce livrable."""
    # Slug depuis le nom du livrable
    slug = _deliverable_slug(deliverable)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    preprod_path = base_path / f"{slug}_{ts}"

    try:
        preprod_path.mkdir(parents=True, exist_ok=True)
        return {"ok": True, "path": preprod_path}
    except Exception as e:
        return {"ok": False, "error": f"mkdir_failed:{e}", "path": preprod_path}


def _materialize_deliverable(dtype, deliverable, preprod_path):
    """Écrit les fichiers du livrable dans le dossier preprod."""
    writers = {
        "code":     _write_code,
        "page":     _write_page,
        "document": _write_document,
        "content":  _write_content,
        "media":    _write_media,
    }
    writer = writers.get(dtype, _write_generic)
    return writer(deliverable, preprod_path)


def _simulate(dtype, deliverable, preprod_path, files):
    """Simulation de preview / run selon le type."""
    simulators = {
        "code":     _sim_code,
        "page":     _sim_page,
        "document": _sim_document,
        "content":  _sim_content,
        "media":    _sim_media,
    }
    sim = simulators.get(dtype, _sim_generic)
    return sim(deliverable, preprod_path, files)


# ── Writers (matérialisation) ─────────────────────────────────────────────────

def _write_code(deliverable, path):
    """Écrit le code Python dans un fichier .py."""
    files = []

    code     = deliverable.get("code", "")
    filename = deliverable.get("filename") or "main.py"
    if not filename.endswith(".py"):
        filename += ".py"

    # Fichier principal
    if code:
        fp = path / filename
        fp.write_text(code, encoding="utf-8")
        files.append({"name": filename, "path": str(fp), "size": len(code)})

    # requirements.txt minimal
    req = path / "requirements.txt"
    req.write_text("# Auto-generated by EURKAI preprod\n# Add your dependencies here\n",
                    encoding="utf-8")
    files.append({"name": "requirements.txt", "path": str(req), "size": req.stat().st_size})

    # README minimal
    entry  = deliverable.get("entry_point", filename)
    comps  = deliverable.get("components_all", [])
    readme = path / "README.md"
    readme.write_text(
        f"# Preprod — {entry}\n\n"
        f"Auto-generated by EURKAI pipeline.\n\n"
        f"## Entry point\n`{filename}`\n\n"
        f"## Components identified\n"
        + "\n".join(f"- {c}" for c in comps)
        + "\n\n## Run\n```bash\npython {filename}\n```\n",
        encoding="utf-8",
    )
    files.append({"name": "README.md", "path": str(readme), "size": readme.stat().st_size})

    return {"ok": True, "files": files}


def _write_page(deliverable, path):
    """Génère un aperçu HTML minimal pour le livrable page."""
    files  = []
    layout = deliverable.get("layout", {})
    comps  = deliverable.get("components", [])
    sections = layout.get("sections", ["header", "content", "footer"])

    sections_html = "\n".join(
        f'  <section id="{s}" style="padding:40px 32px;border-bottom:1px solid #e5e7eb">\n'
        f'    <h2 style="color:#1e3a5f;font-size:14px;text-transform:uppercase">{s.capitalize()}</h2>\n'
        f'    <p style="color:#6b7280;font-size:14px;margin-top:8px">[{s} — à implémenter]</p>\n'
        f'  </section>'
        for s in sections
    )
    comps_list = "".join(f"<li>{c}</li>" for c in comps)

    html = (
        "<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Preprod preview — {layout.get('pattern','Page')}</title>"
        "<style>*{box-sizing:border-box;margin:0;padding:0}"
        "body{font-family:system-ui,sans-serif;background:#f9fafb;color:#1a1a2e}"
        ".header{background:#1e3a5f;color:#fff;padding:24px 32px}"
        ".header h1{font-size:18px}.header .sub{font-size:12px;color:#93c5fd;margin-top:4px}"
        ".badge{display:inline-block;background:#f97316;color:#fff;font-size:11px;"
        "font-weight:700;padding:2px 10px;border-radius:12px;margin-left:8px}"
        ".sidebar{position:fixed;top:0;right:0;width:240px;height:100vh;background:#fff;"
        "border-left:1px solid #e5e7eb;padding:20px;overflow-y:auto}"
        ".sidebar h3{font-size:12px;color:#6b7280;text-transform:uppercase;margin-bottom:12px}"
        ".sidebar ul{list-style:none;font-size:12px;color:#374151;line-height:2}"
        ".main{margin-right:240px}"
        "</style></head><body>"
        "<div class='header'>"
        f"<h1>{layout.get('pattern','Page')} <span class='badge'>PREPROD</span></h1>"
        "<div class='sub'>Généré par EURKAI · preview local · non déployé</div>"
        "</div>"
        f"<div class='main'>{sections_html}</div>"
        "<div class='sidebar'>"
        f"<h3>Composants ({len(comps)})</h3><ul>{comps_list}</ul>"
        "</div></body></html>"
    )

    fp = path / "preview.html"
    fp.write_text(html, encoding="utf-8")
    files.append({"name": "preview.html", "path": str(fp), "size": len(html)})
    return {"ok": True, "files": files}


def _write_document(deliverable, path):
    """Génère un document Markdown depuis le stub."""
    files   = []
    outline = deliverable.get("outline", [])
    summary = deliverable.get("architecture_summary", "")
    secu    = deliverable.get("security_highlights", [])

    content = f"# Document technique\n\n"
    if summary:
        content += f"**Architecture** : {summary}\n\n"
    content += "## Plan\n\n"
    for section in outline:
        content += f"- {section}\n"
    if secu:
        content += "\n## Points de sécurité clés\n\n"
        for s in secu:
            content += f"- {s}\n"
    content += "\n\n---\n*Auto-généré par EURKAI preprod.*\n"

    fp = path / "document.md"
    fp.write_text(content, encoding="utf-8")
    files.append({"name": "document.md", "path": str(fp), "size": len(content)})
    return {"ok": True, "files": files}


def _write_content(deliverable, path):
    """Génère un brief éditorial depuis le stub."""
    files = []
    plan  = deliverable.get("editorial_plan", [])
    topics = deliverable.get("key_topics", [])
    tone  = deliverable.get("tone", "")

    lines = ["# Brief éditorial\n"]
    if tone:
        lines.append(f"**Ton** : {tone}\n")
    if topics:
        lines.append(f"**Sujets clés** : {', '.join(topics)}\n")
    lines.append("\n## Plan éditorial\n")
    for item in plan:
        status = item.get("status", "")
        lines.append(f"- [ ] **{item.get('format', '')}** — {status}\n")
    lines.append("\n---\n*Auto-généré par EURKAI preprod.*\n")

    fp = path / "content_brief.md"
    fp.write_text("".join(lines), encoding="utf-8")
    files.append({"name": "content_brief.md", "path": str(fp), "size": fp.stat().st_size})
    return {"ok": True, "files": files}


def _write_media(deliverable, path):
    """Génère un media spec file."""
    files  = []
    assets = deliverable.get("assets_required", [])
    screens = deliverable.get("screens", [])
    style  = deliverable.get("style_direction", "")

    lines = ["# Media Pack — Spec\n"]
    if style:
        lines.append(f"**Direction créative** : {style}\n")
    if screens:
        lines.append(f"**Écrans à capturer** : {', '.join(screens)}\n")
    lines.append("\n## Assets requis\n\n| Asset | Format | Statut |\n|---|---|---|\n")
    for a in assets:
        lines.append(f"| {a.get('name','')} | {a.get('format','')} | {a.get('status','')} |\n")
    lines.append("\n---\n*Auto-généré par EURKAI preprod.*\n")

    fp = path / "media_spec.md"
    fp.write_text("".join(lines), encoding="utf-8")
    files.append({"name": "media_spec.md", "path": str(fp), "size": fp.stat().st_size})
    return {"ok": True, "files": files}


def _write_generic(deliverable, path):
    fp = path / "deliverable.txt"
    fp.write_text(str(deliverable), encoding="utf-8")
    return {"ok": True, "files": [{"name": "deliverable.txt", "path": str(fp),
                                    "size": fp.stat().st_size}]}


# ── Simulateurs ───────────────────────────────────────────────────────────────

def _sim_code(deliverable, path, files):
    """Validation syntaxique Python simulée."""
    code = deliverable.get("code", "")
    if not code.strip():
        return {"ok": False, "error": "no_code",
                "output": "Code vide — rien à valider."}

    try:
        ast.parse(code)
        validation = deliverable.get("validation", {})
        score      = validation.get("score", "—")
        issues     = validation.get("issues", [])
        output = (
            f"Syntaxe Python : OK\n"
            f"Score validation : {score}/100\n"
            f"Issues : {len(issues)}\n"
            f"Fichiers écrits : {len(files)}"
        )
        note = (
            f"Module principal généré. "
            f"Pour tester : `python {deliverable.get('filename', 'main.py')}`"
        )
        return {"ok": True, "output": output, "note": note}
    except SyntaxError as e:
        return {"ok": False, "error": f"syntax_error:{e}",
                "output": f"SyntaxError : {e}"}


def _sim_page(deliverable, path, files):
    """Simulation preview page — vérifie que le fichier HTML existe."""
    html_files = [f for f in files if f["name"].endswith(".html")]
    if not html_files:
        return {"ok": False, "error": "no_html_file",
                "output": "Aucun fichier HTML généré."}
    f     = html_files[0]
    note  = f"Preview HTML local : {f['path']}\nOuvrir avec : open {f['path']}"
    return {
        "ok": True,
        "output": f"Preview généré : {f['name']} ({f['size']} bytes)",
        "note":   note,
    }


def _sim_document(deliverable, path, files):
    md_files = [f for f in files if f["name"].endswith(".md")]
    if not md_files:
        return {"ok": False, "error": "no_md_file"}
    f = md_files[0]
    return {
        "ok": True,
        "output": f"Document Markdown généré : {f['name']} ({f['size']} bytes)",
        "note":   f"Ouvrir : open {f['path']}",
    }


def _sim_content(deliverable, path, files):
    plan = deliverable.get("editorial_plan", [])
    return {
        "ok": True,
        "output": f"Brief éditorial : {len(plan)} pièces de contenu planifiées.",
        "note":   f"Fichier : {files[0]['path'] if files else '—'}",
    }


def _sim_media(deliverable, path, files):
    assets = deliverable.get("assets_required", [])
    return {
        "ok": True,
        "output": f"Media spec : {len(assets)} assets définis.",
        "note":   f"Fichier : {files[0]['path'] if files else '—'}",
    }


def _sim_generic(deliverable, path, files):
    return {
        "ok": True,
        "output": f"{len(files)} fichier(s) écrit(s).",
        "note":   "",
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _deliverable_slug(deliverable):
    """Génère un slug depuis l'entry_point, filename, ou type du livrable."""
    name = (
        deliverable.get("entry_point")
        or deliverable.get("filename")
        or deliverable.get("type")
        or "deliverable"
    )
    # snake_case, cleaned
    name = re.sub(r"[^a-zA-Z0-9_]", "_", str(name))
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return name[:32]


def _assemble_result(status, preprod_env, meta):
    return {
        "status": status,
        "from":   "deliverable",
        "to":     "preprod",
        "data":   {"preprod_env": preprod_env} if preprod_env else {},
        "meta":   meta,
    }


def _step_record(name, ok, error=None):
    record = {"step": name, "status": "ok" if ok else "failure"}
    if error:
        record["error"] = error
    return record


# ── Smoke test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile, json

    _DELIV_CODE = {
        "deliverable_type": "code",
        "deliverable": {
            "type":          "code",
            "entry_point":   "InvoiceModule",
            "filename":      "invoice_module.py",
            "code":          (
                "def invoice_module(user_id, invoice_id):\n"
                "    \"\"\"\n"
                "    Invoice creation and management.\n"
                "    \"\"\"\n"
                "    # user_id: str\n"
                "    # invoice_id: str\n"
                "    return None\n"
            ),
            "validation":    {"score": 100, "issues": []},
            "components_all":["InvoiceModule", "PaymentService", "AuthModule", "BillingService"],
        },
    }

    _DELIV_PAGE = {
        "deliverable_type": "page",
        "deliverable": {
            "type":   "page",
            "status": "stub",
            "layout": {
                "pattern":  "landing page wireframe",
                "sections": ["header", "hero", "features", "pricing", "cta", "footer"],
            },
            "components":    ["HeroSection", "FeatureGrid", "PricingTable"],
            "ux_constraints":["CTA visible above fold", "Mobile first"],
        },
    }

    _DELIV_DOC = {
        "deliverable_type": "document",
        "deliverable": {
            "type":   "document",
            "status": "stub",
            "outline": [
                "1. Introduction et contexte",
                "2. Architecture technique",
                "3. Composants et modules",
                "4. API et intégrations",
            ],
            "architecture_summary": "Client-Server · REST API · SPA",
            "security_highlights":  ["JWT 15-min tokens", "bcrypt passwords"],
        },
    }

    cases = [
        {"label": "✓ Code",             "input": _DELIV_CODE},
        {"label": "✓ Page",             "input": _DELIV_PAGE},
        {"label": "✓ Document",         "input": _DELIV_DOC},
        {"label": "✗ type manquant",    "input": {"deliverable": {}}},
        {"label": "✗ input invalide",   "input": "not a dict"},
    ]

    print("=" * 65)
    print("  scenario_deliverable_to_preprod — smoke test")
    print("=" * 65)

    # Dossier temp pour les tests
    with tempfile.TemporaryDirectory(prefix="eurkai_preprod_test_") as tmpdir:
        passed = failed = 0
        for case in cases:
            r = run(case["input"], base_path=Path(tmpdir), verbose=False)
            ok = r["status"] in ("success", "partial")
            print(f"\n{case['label']}")
            print(f"  status   : {r['status']}")
            print(f"  from→to  : {r['from']} → {r['to']}")
            print(f"  steps    : {[s['step'] + ':' + s['status'] for s in r['meta']['steps']]}")
            if r.get("data", {}).get("preprod_env"):
                env = r["data"]["preprod_env"]
                print(f"  type     : {env['type']}")
                print(f"  path     : {Path(env['path']).name}")
                print(f"  files    : {[f['name'] for f in env['files']]}")
                print(f"  run      : {env['run_result']['status']} — {env['run_result']['output'][:60]}")
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
