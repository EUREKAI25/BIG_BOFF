"""
design.page.generate_full
Scénario : brief → visual_intent → palette → coherence → plan → render → capture → audit

Pipeline complet incluant capture Playwright et audit vision.
Option generate_charter : après le render, lance le pipeline charte de marque
(design_dna → psychology → palette → exploration → theme) et sauvegarde les fichiers
dans output/<slug>/charter/.
"""
from __future__ import annotations

import http.server
import json
import sys
import tempfile
import threading
from dataclasses import asdict
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from design_scenarios._ep_loader import load_endpoint

_ep_vi        = load_endpoint("design.visual_intent.generate")
_ep_palette   = load_endpoint("design.palette.generate")
_ep_coherence = load_endpoint("design.coherence.apply")
_ep_plan      = load_endpoint("design.plan.generate")
_ep_render    = load_endpoint("design.render.page")
_ep_capture   = load_endpoint("design.capture.page")
_ep_audit     = load_endpoint("design.audit.page")

NAME     = "design.page.generate_full"
CATEGORY = "design"
OBJECT   = "page"
ACTION   = "generate_full"
VERSION  = "1.0.0"

STEPS = [
    {"order": 1, "endpoint": "design.visual_intent.generate"},
    {"order": 2, "endpoint": "design.palette.generate"},
    {"order": 3, "endpoint": "design.coherence.apply"},
    {"order": 4, "endpoint": "design.plan.generate"},
    {"order": 5, "endpoint": "design.render.page"},
    {"order": 6, "endpoint": "design.capture.page",  "note": "Requiert Playwright"},
    {"order": 7, "endpoint": "design.audit.page",    "note": "Requiert API Anthropic"},
]

INPUTS = {
    "brief":             {"type": "str",      "required": True,  "description": "Brand/project description"},
    "project_name":      {"type": "str",      "required": True,  "description": "Brand/project name"},
    "seed":              {"type": "int",      "required": False, "description": "Seed de rendu (default: 42)"},
    "site_family":       {"type": "str",      "required": False, "description": "Famille de template"},
    "reference_image":   {"type": "str|None", "required": False, "description": "Image/mockup de référence (optionnel)"},
    "reference_type":    {"type": "str",      "required": False, "description": "none | image | screenshot | mockup"},
    "output_root":       {"type": "str",      "required": False, "description": "Répertoire output captures"},
    "api_key":           {"type": "str|None", "required": False, "description": "Clé API Anthropic pour audit"},
    "capture_port":      {"type": "int",      "required": False, "description": "Port serveur HTTP local (default: 18765)"},
    "generate_charter":  {"type": "bool",     "required": False, "description": "Générer la charte de marque complète (default: False)"},
}

OUTPUTS = {
    "html":          {"type": "str",       "description": "HTML rendu final"},
    "visual_intent": {"type": "dict",      "description": "Visual intent"},
    "palette":       {"type": "dict",      "description": "Palette couleurs"},
    "coherence":     {"type": "dict",      "description": "Résultat cohérence"},
    "plan":          {"type": "dict",      "description": "Design plan"},
    "captures":      {"type": "list",      "description": "Captures screenshots"},
    "audit":         {"type": "dict",      "description": "Résultat audit: results, summary, pass, score"},
    "charter":       {"type": "dict|None", "description": "Charte de marque (si generate_charter=True) : paths des fichiers générés"},
    "trace":         {"type": "list",      "description": "Trace d'exécution complète"},
}


def _serve_html_local(html: str, port: int) -> threading.Thread:
    """Lance un serveur HTTP local pour servir la page HTML."""
    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    tmp.write(html)
    tmp.close()
    tmp_dir  = Path(tmp.name).parent
    tmp_name = Path(tmp.name).name

    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(tmp_dir), **kw)
        def log_message(self, *a): pass  # silence

    server = http.server.HTTPServer(("127.0.0.1", port), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, t, f"http://127.0.0.1:{port}/{tmp_name}"


def _run_charter(brief: str, project_name: str, out_dir: Path) -> dict:
    """Lance le pipeline charte de marque et écrit les fichiers dans out_dir/charter/."""
    try:
        import generate_brand_charter as _gbc
    except ImportError as e:
        return {"error": f"generate_brand_charter introuvable : {e}"}

    charter_dir = out_dir / "charter"
    charter_dir.mkdir(parents=True, exist_ok=True)

    dna           = _gbc.step_dna(brief, project_name)
    rec           = _gbc.step_psychology(dna)
    palette_out   = _gbc.step_palette(dna, rec)
    exploration   = _gbc.step_explore(dna)
    style_dna     = _gbc.step_build_style_dna(dna, palette_out, rec)
    preset, css   = _gbc.step_theme(style_dna)

    def _save(name: str, data: object) -> Path:
        p = charter_dir / name
        p.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return p

    files: dict[str, str] = {}

    files["style_dna"]    = str(_save("style_dna.json",   asdict(style_dna) if style_dna else {}))
    if palette_out:
        try:    files["palette"] = str(_save("palette.json", asdict(palette_out.palette_set)))
        except: files["palette"] = str(_save("palette.json", {"error": "serialization failed"}))
    if exploration:
        try:    files["creative_directions"] = str(_save("creative_directions.json", asdict(exploration)))
        except: files["creative_directions"] = str(_save("creative_directions.json", {"error": "serialization failed"}))
    if preset:
        files["theme_preset"] = str(_save("theme_preset.json", preset))
    if css:
        p = charter_dir / "theme.css"
        p.write_text(css, encoding="utf-8")
        files["theme_css"] = str(p)
    if preset or style_dna:
        scss = _gbc.generate_scss(project_name, style_dna, preset)
        if scss:
            p = charter_dir / "theme.scss"
            p.write_text(scss, encoding="utf-8")
            files["theme_scss"] = str(p)

    pipeline_ok = {
        "dna":     dna       is not None,
        "rec":     rec       is not None,
        "palette": palette_out is not None,
        "explore": exploration is not None,
        "theme":   preset    is not None,
    }
    charter_html = _gbc.generate_html(
        project_name=project_name, brief_text=brief,
        dna=dna, rec=rec, palette_output=palette_out,
        exploration=exploration, style_dna=style_dna,
        preset=preset, css=css, pipeline_ok=pipeline_ok,
    )
    p = charter_dir / "brand_charter.html"
    p.write_text(charter_html, encoding="utf-8")
    files["brand_charter"] = str(p)

    return {"files": files, "pipeline_ok": pipeline_ok, "dir": str(charter_dir)}


def run(
    brief: str,
    project_name: str,
    seed: int = 42,
    site_family: str = "",
    reference_image: str | None = None,
    reference_type: str = "none",
    output_root: str = "output/captures",
    api_key: str | None = None,
    capture_port: int = 18765,
    generate_charter: bool = False,
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS

    Étapes 6–7 (capture + audit) nécessitent Playwright et une clé Anthropic.
    Si capture échoue, le scénario retourne quand même le HTML + trace partielle.
    """
    trace   = []
    context = {"mode": "light", "name": project_name}
    slug    = project_name.lower().replace(" ", "_")[:20]

    # Étape 1 — visual_intent
    vi = _ep_vi.run(brief=brief, reference_image=reference_image, reference_type=reference_type or None)
    trace.append({"step": 1, "endpoint": "design.visual_intent.generate", "ok": True})

    # Étape 2 — palette
    palette = _ep_palette.run(visual_intent=vi, context=context)
    trace.append({"step": 2, "endpoint": "design.palette.generate", "ok": True})

    # Étape 3 — coherence
    coherence = _ep_coherence.run(
        visual_intent=vi,
        context=context,
        palette=palette,
        reference_image=reference_image,
        reference_type=reference_type,
    )
    trace.append({
        "step": 3, "endpoint": "design.coherence.apply", "ok": True,
        "reference_mode": coherence.get("reference_mode"),
    })

    # Étape 4 — plan
    ref_analysis = coherence.get("reference_analysis") or None
    plan = _ep_plan.run(brief=brief, seed=seed, visual_intent=vi, reference_analysis=ref_analysis)
    trace.append({"step": 4, "endpoint": "design.plan.generate", "ok": True})

    # Étape 5 — render (Eurkai DOM Library)
    render = _ep_render.run(
        project_name=project_name,
        brief_text=brief,
        site_family=site_family,
        seed=seed,
        cp_palette=coherence.get("palette"),
        visual_intent=vi,
        plan=plan,
    )
    html = render["html"]
    trace.append({"step": 5, "endpoint": "design.render.page", "ok": True})

    # Étape 6 — capture (optionnel, nécessite Playwright)
    captures_result = {"captures": [], "ok_count": 0, "fail_count": 0}
    server = None
    try:
        server, _, url = _serve_html_local(html, capture_port)
        captures_result = _ep_capture.run(
            url=url, site=slug, page="full",
            output_root=output_root, viewport="desktop",
        )
        trace.append({"step": 6, "endpoint": "design.capture.page", "ok": True,
                      "captures": captures_result["ok_count"]})
    except Exception as e:
        trace.append({"step": 6, "endpoint": "design.capture.page", "ok": False, "error": str(e)})
    finally:
        if server:
            try: server.shutdown()
            except: pass

    # Étape 7 — audit (optionnel, nécessite API key)
    audit_result = {"results": [], "summary": {}, "pass": None, "score": 0}
    if captures_result["captures"]:
        try:
            audit_result = _ep_audit.run(
                captures=captures_result["captures"],
                api_key=api_key,
            )
            trace.append({"step": 7, "endpoint": "design.audit.page", "ok": True,
                          "score": audit_result["score"], "pass": audit_result["pass"]})
        except Exception as e:
            trace.append({"step": 7, "endpoint": "design.audit.page", "ok": False, "error": str(e)})

    # Étape 8 — charte de marque (optionnel)
    charter_result = None
    if generate_charter:
        out_dir = _ROOT / output_root / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            charter_result = _run_charter(brief, project_name, out_dir)
            ok_count = sum(1 for v in charter_result.get("pipeline_ok", {}).values() if v)
            trace.append({"step": 8, "endpoint": "generate_brand_charter", "ok": True,
                          "steps_ok": ok_count, "dir": charter_result.get("dir")})
        except Exception as e:
            charter_result = {"error": str(e)}
            trace.append({"step": 8, "endpoint": "generate_brand_charter", "ok": False, "error": str(e)})

    return {
        "html":          html,
        "visual_intent": vi,
        "palette":       coherence.get("palette"),
        "coherence":     coherence,
        "plan":          plan,
        "captures":      captures_result["captures"],
        "audit":         audit_result,
        "charter":       charter_result,
        "trace":         trace,
    }
