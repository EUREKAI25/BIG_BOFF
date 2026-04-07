"""
generate_ui.py — EURKAI Generation Input Page
────────────────────────────────────────────────
UI layer on top of the existing pipeline.run_pipeline().
Does NOT modify the pipeline.

Usage:
    python generate_ui.py
    python generate_ui.py --port 8764

Open:
    http://localhost:8764
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# ─── Flask ────────────────────────────────────────────────────────────────────
try:
    from flask import Flask, jsonify, request, send_from_directory
except ImportError:
    print("Flask manquant : pip install flask", file=sys.stderr)
    sys.exit(1)

# ─── Pipeline import ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# Pipeline v2 (milestones stricts, no fallback) — prioritaire
try:
    sys.path.insert(0, str(SCRIPT_DIR / "MODULES"))
    from design_pipeline import run_pipeline_v2  # type: ignore
    from design_pipeline.pipeline_v2 import OUTPUT_DIR  # type: ignore
    _PIPELINE_V2_OK = True
except Exception as _e2:
    _PIPELINE_V2_OK = False
    _PIPELINE_V2_ERR = str(_e2)

# Pipeline v1 — fallback
try:
    from pipeline import run_pipeline, OUTPUT_DIR  # type: ignore
    _PIPELINE_OK = True
except ImportError as _e:
    _PIPELINE_OK = False
    _PIPELINE_ERR = str(_e)
    OUTPUT_DIR = SCRIPT_DIR / "output"


class _PipelineResult:
    """Adaptateur résultat pipeline — même interface pour v1 (objet) et v2 (dict)."""
    def __init__(self, data):
        if isinstance(data, dict):
            self.output_path   = str(data.get("output_path", "")) or None
            self.output_paths  = [str(p) for p in data.get("output_paths", []) if p]
            self.final_score   = data.get("final_score")
            self.error         = ("; ".join(data["errors"]) if data.get("errors") else None)
            self.html          = data.get("html", "")
            self.plan          = data.get("plan", {})
        else:
            # v1 objet — passe-plat
            self.output_path   = getattr(data, "output_path", None)
            self.output_paths  = getattr(data, "output_paths", [])
            self.final_score   = getattr(data, "final_score", None)
            self.error         = getattr(data, "error", None)
            self.html          = getattr(data, "html", "")
            self.plan          = getattr(data, "plan", {})


def _run_pipeline(brief, project_name, seed, palette=None, **kwargs):
    """Appelle pipeline_v2 si disponible, sinon pipeline v1. Retourne _PipelineResult."""
    if _PIPELINE_V2_OK:
        raw = run_pipeline_v2(
            brief=brief, project_name=project_name, seed=seed,
            palette=palette or {}, **kwargs,
        )
        return _PipelineResult(raw)
    raw = run_pipeline(
        brief=brief, project_name=project_name, seed=seed, **kwargs,
    )
    return _PipelineResult(raw)

PORT         = 8764
HISTORY_FILE = SCRIPT_DIR / "generation_history.json"
MAX_HISTORY  = 50

# URL prefix for reverse-proxy deployments (e.g. "/tools" → routes at /tools/...)
_PREFIX = os.environ.get("URL_PREFIX", "").rstrip("/")

# ─── Job registry ─────────────────────────────────────────────────────────────
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def _new_job(project_name: str, brief: str, params: dict) -> str:
    job_id = uuid.uuid4().hex[:10]
    with _jobs_lock:
        _jobs[job_id] = {
            "job_id":       job_id,
            "project_name": project_name,
            "brief_preview": brief[:120].replace("\n", " "),
            "params":       params,
            "status":       "running",
            "started_at":   datetime.now().isoformat(timespec="seconds"),
            "finished_at":  None,
            "duration_s":   None,
            "final_score":  None,
            "output_path":   None,
            "output_paths":  [],
            "charter_paths": [],
            "error":         None,
            "logs":         [],
        }
    return job_id


class _LogCapture(io.TextIOBase):
    """Wraps stdout — forwards to original + stores lines in job dict."""
    def __init__(self, job_id: str, original: Any) -> None:
        self.job_id   = job_id
        self.original = original
        self._buf     = ""

    def write(self, s: str) -> int:
        self.original.write(s)
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            stripped = line.strip()
            if stripped:
                with _jobs_lock:
                    if self.job_id in _jobs:
                        _jobs[self.job_id]["logs"].append(stripped)
        return len(s)

    def flush(self) -> None:
        self.original.flush()


def _gen_charter_file(
    brief: str,
    project_name: str,
    charter_dir: Path,
    charter_paths: list,
    dna=None,
) -> None:
    """Génère brand_charter.html dans charter_dir et ajoute le chemin à charter_paths."""
    try:
        import generate_brand_charter as _gbc
        charter_dir.mkdir(parents=True, exist_ok=True)
        if dna is None:
            dna = _gbc.step_dna(brief, project_name)
        rec       = _gbc.step_psychology(dna)
        palette   = _gbc.step_palette(dna, rec)
        style_dna = _gbc.step_build_style_dna(dna, palette, rec)
        preset, _ = _gbc.step_theme(style_dna)
        html      = _gbc.generate_html(
            project_name, brief,
            dna, rec, palette, _gbc.step_explore(dna), style_dna, preset,
            css=None, pipeline_ok={},
        )
        cp = charter_dir / "brand_charter.html"
        cp.write_text(html, encoding="utf-8")
        charter_paths.append(str(cp))
        print(f"[charter] ✓ {cp}")
    except Exception as _ce:
        print(f"[charter] ✗ {_ce}")


def _run_job(job_id: str, brief: str, project_name: str,
             seed: int, harmony: str, site_family: str,
             enable_capture: bool, enable_audit: bool,
             generate_charter: bool = False,
             nb_options: int = 1,
             charter_mode: str = "none",
             cp_palette: dict | None = None) -> None:
    t0      = time.time()
    orig    = sys.stdout
    capture = _LogCapture(job_id, orig)
    sys.stdout = capture

    output_paths:  list[str] = []
    charter_paths: list[str] = []
    final_scores:  list[float] = []
    variants_meta: list[dict] = []
    last_error: str | None = None

    try:
        if charter_mode == "only":
            # Charte uniquement — pas de page
            import generate_brand_charter as _gbc
            for i in range(nb_options):
                slug = project_name.lower().replace(" ", "_")
                suffix = f"_{i + 1}" if nb_options > 1 else ""
                charter_dir = OUTPUT_DIR / slug / f"charter{suffix}"
                charter_dir.mkdir(parents=True, exist_ok=True)
                print(f"[charte {i + 1}/{nb_options}] Génération…")
                try:
                    dna       = _gbc.step_dna(brief, project_name)
                    rec       = _gbc.step_psychology(dna)
                    palette   = _gbc.step_palette(dna, rec)
                    style_dna = _gbc.step_build_style_dna(dna, palette, rec)
                    preset, _ = _gbc.step_theme(style_dna)
                    html      = _gbc.generate_html(
                        dna, rec, palette, _gbc.step_explore(dna), style_dna, preset
                    )
                    out = charter_dir / "brand_charter.html"
                    out.write_text(html, encoding="utf-8")
                    output_paths.append(str(out))
                    charter_paths.append(str(out))
                    print(f"[charte {i + 1}/{nb_options}] ✓ {out}")
                except Exception as e:
                    last_error = f"{type(e).__name__}: {e}"
                    print(f"[charte {i + 1}/{nb_options}] ✗ {last_error}")

        else:
            if not _PIPELINE_V2_OK and not _PIPELINE_OK:
                raise RuntimeError(f"Pipeline non disponible : {_PIPELINE_V2_ERR if not _PIPELINE_V2_OK else _PIPELINE_ERR}")

            do_charter = (charter_mode == "also")

            if nb_options == 1 and not cp_palette:
                # ── Variante unique sans palette de référence — pipeline standard
                result = _run_pipeline(
                    brief=brief, project_name=project_name, seed=seed,
                    harmony=harmony, site_family=site_family,
                    enable_capture=enable_capture, enable_audit=enable_audit,
                    verbose=True,
                )
                if result.output_path:
                    output_paths.append(result.output_path)
                if result.final_score:
                    final_scores.append(result.final_score)
                if result.error:
                    last_error = result.error
                if do_charter and result.output_path:
                    _gen_charter_file(
                        brief, project_name,
                        Path(result.output_path).parent / "charter",
                        charter_paths,
                    )

            else:
                # ── Multi-variantes — archetypes forcés ───────────────────────
                # Chaque variante utilise un archétype ET un blueprint différents
                # → layout_strategy, hero_type, visual_density, typography_direction distincts
                import generate_brand_charter as _gbc
                from design_dna_resolver          import resolve as _rdna
                from design_dna_resolver.brief_parser      import parse_brief as _pbr
                from design_dna_resolver.archetype_inference import infer_archetype as _ia
                from design_dna_resolver.style_mapper        import get_style_profile as _gsp

                brief_input = _pbr(brief)
                _, _, scores = _ia(brief_input)
                ranked = sorted(scores, key=lambda k: scores[k], reverse=True)

                # Sélection diversifiée : exclure les archetypes trop similaires
                # Axes de diversité : hero_pattern, heading_alignment, layout_rhythm, radius_profile
                _ARCH_AXES = {
                    "editorial_magazine": ("editorial",  "left",   "editorial", "zero"),
                    "luxury_minimal":     ("luxury",     "center", "airy",      "zero"),
                    "playful_brand":      ("playful",    "center", "playful",   "pill"),
                    "warm_human":         ("warm_split", "left",   "airy",      "large"),
                    "startup_clean":      ("centered",   "center", "balanced",  "small"),
                    "corporate_pro":      ("corporate",  "left",   "balanced",  "small"),
                    "tech_futurist":      ("dark_tech",  "center", "dense",     "small"),
                    "brutalist":          ("raw_bold",   "left",   "dense",     "zero"),
                    "organic_natural":    ("warm_split", "left",   "airy",      "large"),
                    "premium_craft":      ("luxury",     "left",   "airy",      "small"),
                    "bold_challenger":    ("raw_bold",   "left",   "dense",     "zero"),
                    "creative_studio":    ("centered",   "center", "playful",   "large"),
                }
                def _pick_diverse(ranked_list, n):
                    """Greedy: pick n archetypes maximising diversity across all 4 axes."""
                    chosen, seen_axes = [], set()
                    # First pass: pick unique on all 4 axes
                    for arch in ranked_list:
                        axes = _ARCH_AXES.get(arch, (arch, "center", "balanced", "small"))
                        sig = (axes[0], axes[1], axes[2])  # hero + alignment + rhythm
                        if sig not in seen_axes:
                            chosen.append(arch)
                            seen_axes.add(sig)
                            if len(chosen) == n:
                                return chosen
                    # Second pass: relax to hero-only uniqueness
                    seen_hero = {_ARCH_AXES.get(a, (a,))[0] for a in chosen}
                    for arch in ranked_list:
                        if arch in chosen:
                            continue
                        hero = _ARCH_AXES.get(arch, (arch,))[0]
                        if hero not in seen_hero:
                            chosen.append(arch)
                            seen_hero.add(hero)
                            if len(chosen) == n:
                                return chosen
                    # Fill remaining with remaining ranked
                    for arch in ranked_list:
                        if arch not in chosen:
                            chosen.append(arch)
                            if len(chosen) == n:
                                return chosen
                    return (chosen * n)[:n]

                diverse_archs = _pick_diverse(ranked, nb_options)

                slug = project_name.lower().replace(" ", "_")
                ts   = datetime.now().strftime("%Y%m%d_%H%M%S")

                for i in range(nb_options):
                    current_seed = seed + i * 1009
                    arch = diverse_archs[i]
                    print(f"\n[variante {i + 1}/{nb_options}] archétype={arch} seed={current_seed}"
                          + (" [palette ref]" if cp_palette else ""))

                    try:
                        # DNA avec archétype forcé
                        dna = _rdna(brief)
                        dna.style_archetype = arch
                        prof = _gsp(arch)
                        dna.palette_bias     = prof.palette_bias
                        dna.typography_style = prof.typography_style
                        dna.layout_style     = getattr(prof, "layout_style", None)

                        rec        = _gbc.step_psychology(dna)
                        palette    = _gbc.step_palette(dna, rec)
                        style_dna  = _gbc.step_build_style_dna(dna, palette, rec)
                        preset, css= _gbc.step_theme(style_dna)

                        # Bypass generate_landing_page → _select_direction ignore
                        # notre archetype forcé. On appelle _lp_dynamic_page
                        # directement avec ctx["archetype"] = arch.
                        # variant_index garantit un blueprint distinct (hero + sections différents)
                        # cp_palette (visuel de référence) est prioritaire sur palette_output.
                        ctx = _gbc._ctx(project_name, brief, dna, preset)
                        ctx["archetype"]   = arch   # ← archétype forcé
                        ctx["render_seed"] = current_seed

                        html = _gbc._lp_dynamic_page(
                            ctx, css or "",
                            palette_output=palette,
                            harmony=harmony,
                            site_family=site_family,
                            cp_palette=cp_palette,  # None si pas de référence
                            variant_index=i,         # ← blueprint indexé, pas random
                        )

                        out_dir = OUTPUT_DIR / slug
                        out_dir.mkdir(parents=True, exist_ok=True)
                        out_path = out_dir / f"landing_v{i + 1}_{arch}_{ts}.html"
                        out_path.write_text(html, encoding="utf-8")
                        output_paths.append(str(out_path))

                        # Parse embedded metadata for UI display
                        _meta = _parse_page_meta(html)
                        variants_meta.append({"variant": i + 1, "archetype": arch, **_meta})
                        print(f"[variante {i + 1}/{nb_options}] ✓ {out_path.name}"
                              + (f" [{_meta.get('hero_type','')} / {_meta.get('visual_density','')}]"
                                 if _meta else ""))

                        if do_charter:
                            _gen_charter_file(
                                brief, project_name,
                                out_dir / f"charter_v{i + 1}",
                                charter_paths,
                                dna=dna,
                            )

                    except Exception as _ve:
                        last_error = f"variante {i + 1}: {_ve}"
                        print(f"[variante {i + 1}/{nb_options}] ✗ {_ve}")

        duration  = round(time.time() - t0, 1)
        success   = bool(output_paths)
        avg_score = round(sum(final_scores) / len(final_scores)) if final_scores else 0

        with _jobs_lock:
            _jobs[job_id].update({
                "status":        "success" if success else "error",
                "finished_at":   datetime.now().isoformat(timespec="seconds"),
                "duration_s":    duration,
                "final_score":   avg_score,
                "output_path":   output_paths[0] if output_paths else None,
                "output_paths":  output_paths,
                "charter_paths": charter_paths,
                "variants_meta": variants_meta,
                "error":         last_error if not success else None,
            })

        _append_history(_jobs[job_id])

    except Exception as exc:
        duration = round(time.time() - t0, 1)
        err_msg  = f"{type(exc).__name__}: {exc}"
        with _jobs_lock:
            _jobs[job_id].update({
                "status":      "error",
                "finished_at": datetime.now().isoformat(timespec="seconds"),
                "duration_s":  duration,
                "error":       err_msg,
                "logs":        _jobs[job_id]["logs"] + [traceback.format_exc().strip()],
            })
        _append_history(_jobs[job_id])
    finally:
        sys.stdout = orig


# ─── History persistence ──────────────────────────────────────────────────────
def _load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _append_history(job: dict) -> None:
    history = _load_history()
    # Remove previous entry for same project if any (keep latest)
    history = [h for h in history if h.get("job_id") != job["job_id"]]
    entry = {k: job[k] for k in (
        "job_id", "project_name", "brief_preview",
        "status", "started_at", "finished_at",
        "duration_s", "final_score", "output_path", "error",
    )}
    history.insert(0, entry)
    HISTORY_FILE.write_text(
        json.dumps(history[:MAX_HISTORY], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _parse_page_meta(html: str) -> dict:
    """Parse <!-- eurkai:meta {...} --> comment embedded in generated HTML."""
    m = re.search(r'<!-- eurkai:meta (\{.*?\}) -->', html)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return {}


# ─── Tools Hub — module scanner + HTML generator ─────────────────────────────

_HUB_CAT_META = {
    "ai":            {"label": "AI",            "color": "#818cf8"},
    "design":        {"label": "Design",        "color": "#34d399"},
    "document":      {"label": "Document",      "color": "#fb923c"},
    "capture":       {"label": "Capture",       "color": "#22d3ee"},
    "quality":       {"label": "Qualité",       "color": "#fbbf24"},
    "orchestration": {"label": "Orchestration", "color": "#a78bfa"},
    "utility":       {"label": "Utilitaire",    "color": "#6b7280"},
}

_HUB_CAT_RULES = [
    (["model_executor","ai_inquiry","conversational_brief","design_exploration",
      "visual_intent","vision_audit"],                                    "ai"),
    (["color_palette","color_psychology","visual_decorators","brand","logo",
      "palette","seed_builder","theme","pictogram","design_plan","design_dna",
      "design_learning"],                                                 "design"),
    (["document_objects","page_builder"],                                 "document"),
    (["screenshot_capture","scraper","scan_and_do"],                      "capture"),
    (["auto_fix","design_validator","pipeline_validator",
      "visual_coherence","visual_consistency"],                           "quality"),
    (["project_orchestration","design_endpoints",
      "design_scenarios","design_catalog"],                               "orchestration"),
]

_HUB_TAG_MAP = {
    "visual":   ["color","visual","design","palette","brand","logo","theme","pictogram"],
    "ai":       ["model","ai_inquiry","vision","intent","anthropic","openai","gemini"],
    "css":      ["css","html","render","page_builder","decorators","scss"],
    "audit":    ["audit","validator","coherence","fix","learning","score"],
    "capture":  ["screenshot","scraper","scan","capture"],
    "svg":      ["svg","pictogram","logo","glyph"],
    "pipeline": ["pipeline","orchestration","scenario","endpoint","batch"],
    "document": ["document","invoice","dashboard"],
    "seed":     ["seed","dna","brief","context"],
}

_HUB_TAG_COLORS = {
    "visual":   "#34d399", "ai":     "#818cf8", "css":      "#22d3ee",
    "audit":    "#fbbf24", "capture":"#22d3ee", "svg":      "#34d399",
    "pipeline": "#a78bfa", "document":"#fb923c","seed":     "#6b7280",
}

# Tool pages registry (name, url, description, tags)
_TOOL_PAGES = [
    {"name": "Générateur",    "url": "page_generate",
     "desc": "Lancer le pipeline complet depuis un brief",
     "tags": ["pipeline","ai"]},
]


def _hub_cat(name: str) -> str:
    n = name.lower()
    for keys, cat in _HUB_CAT_RULES:
        if any(k in n for k in keys):
            return cat
    return "utility"


def _hub_tags(name: str, raw: dict) -> list[str]:
    blob = (name + " " + json.dumps(raw)).lower()
    return [t for t, kws in _HUB_TAG_MAP.items() if any(k in blob for k in kws)]


def _scan_manifests() -> list[dict]:
    modules_dir = SCRIPT_DIR / "MODULES"
    result = []
    for mf in sorted(modules_dir.rglob("MANIFEST.json")):
        if mf.parent.parent != modules_dir:
            continue
        try:
            raw = json.loads(mf.read_text(encoding="utf-8"))
            fn  = raw.get("function", {})
            name = (raw.get("module") or raw.get("name")
                    or fn.get("name") or mf.parent.name).lower().replace("-","_")
            result.append({
                "name":        name,
                "dir":         mf.parent.name,
                "manifest":    mf,
                "version":     raw.get("version", ""),
                "description": raw.get("description", ""),
                "status":      raw.get("status", "stable"),
                "category":    _hub_cat(name),
                "tags":        _hub_tags(name, raw),
            })
        except Exception:
            pass
    return result


def _scan_endpoints() -> list[dict]:
    """Scan design_endpoints/*.py for module-level constants (NAME, CATEGORY, INPUTS, OUTPUTS…)."""
    import ast as _ast
    ep_dir = SCRIPT_DIR / "MODULES" / "design_endpoints"
    result = []
    if not ep_dir.exists():
        return result
    for py_file in sorted(ep_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            tree = _ast.parse(py_file.read_text(encoding="utf-8"))
            consts: dict = {}
            for node in tree.body:
                if isinstance(node, _ast.Assign):
                    for target in node.targets:
                        if isinstance(target, _ast.Name):
                            try:
                                consts[target.id] = _ast.literal_eval(node.value)
                            except Exception:
                                pass
            name = consts.get("NAME", py_file.stem)
            result.append({
                "slug":        name,
                "name":        name,
                "item_type":   "endpoint",
                "version":     str(consts.get("VERSION", "")),
                "description": str(consts.get("DESCRIPTION", "")),
                "status":      str(consts.get("STATUS", "stable")),
                "category":    str(consts.get("CATEGORY", _hub_cat(name))),
                "tags":        _hub_tags(name, consts),
                "inputs":      consts.get("INPUTS", {}),
                "outputs":     consts.get("OUTPUTS", {}),
                "_py_file":    str(py_file),
            })
        except Exception:
            pass
    return result


def _find_manifest_for(module_name: str) -> tuple[dict | None, Path | None]:
    """Return (raw_manifest_dict, module_dir_path) for a module slug, or (None, None)."""
    slug = module_name.lower().replace("-", "_")
    modules_dir = SCRIPT_DIR / "MODULES"
    for mf in modules_dir.rglob("MANIFEST.json"):
        if mf.parent.parent != modules_dir:
            continue
        try:
            raw = json.loads(mf.read_text(encoding="utf-8"))
            fn  = raw.get("function", {})
            name = (raw.get("module") or raw.get("name")
                    or fn.get("name") or mf.parent.name).lower().replace("-", "_")
            if name == slug:
                return raw, mf.parent
        except Exception:
            pass
    return None, None


def _find_endpoint_for(slug: str) -> tuple[dict | None, Path | None]:
    """Return (normalized_raw, ep_dir) for an endpoint slug, or (None, None)."""
    import ast as _ast
    ep_dir = SCRIPT_DIR / "MODULES" / "design_endpoints"
    if not ep_dir.exists():
        return None, None
    slug_norm = slug.lower().replace("-", "_")
    for py_file in sorted(ep_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            tree = _ast.parse(py_file.read_text(encoding="utf-8"))
            consts: dict = {}
            for node in tree.body:
                if isinstance(node, _ast.Assign):
                    for target in node.targets:
                        if isinstance(target, _ast.Name):
                            try:
                                consts[target.id] = _ast.literal_eval(node.value)
                            except Exception:
                                pass
            name = consts.get("NAME", py_file.stem)
            if name != slug and name.lower().replace(".", "_") != slug_norm:
                continue
            # Normalize INPUTS to manifest function.inputs format
            inputs_raw  = consts.get("INPUTS", {})
            outputs_raw = consts.get("OUTPUTS", {})
            fn_inputs = {
                k: ("{type} — {desc}{req}".format(
                    type=v.get("type", "str"),
                    desc=v.get("description", ""),
                    req=" [obligatoire]" if v.get("required") else " [optionnel]",
                ) if isinstance(v, dict) else str(v))
                for k, v in inputs_raw.items()
            } if isinstance(inputs_raw, dict) else {}
            fn_outputs = {
                k: ("{type} — {desc}".format(
                    type=v.get("type", "any"),
                    desc=v.get("description", ""),
                ) if isinstance(v, dict) else str(v))
                for k, v in outputs_raw.items()
            } if isinstance(outputs_raw, dict) else {}
            raw = {
                "name":        name,
                "module":      name,
                "version":     str(consts.get("VERSION", "")),
                "description": str(consts.get("DESCRIPTION", f"Endpoint {name}")),
                "status":      str(consts.get("STATUS", "stable")),
                "item_type":   "endpoint",
                "function":    {"name": "run", "inputs": fn_inputs, "output": fn_outputs},
                "_py_file":    str(py_file),
            }
            return raw, ep_dir
        except Exception:
            pass
    return None, None


def _module_main_py(raw: dict, mod_dir: Path) -> Path | None:
    """Find the main .py file for a module."""
    fn_name  = raw.get("function", {}).get("name", "")
    mod_name = (raw.get("module") or raw.get("name") or mod_dir.name).lower().replace("-","_")
    pkg_name = mod_dir.name  # e.g. "conversational_brief"
    candidates = [
        mod_dir / "src" / f"{mod_name}.py",
        mod_dir / f"{mod_name}.py",
        mod_dir / "src" / "__init__.py",
        # Package subdirectory with same name (e.g. module_dir/module_name/__init__.py)
        mod_dir / pkg_name / "__init__.py",
        mod_dir / mod_name / "__init__.py",
        mod_dir / "__init__.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Fallback: any .py in src/ that contains the function name
    src_dir = mod_dir / "src"
    if src_dir.exists() and fn_name:
        for py in src_dir.glob("*.py"):
            if fn_name in py.read_text(encoding="utf-8", errors="ignore"):
                return py
    return None


def _build_cli_hint(raw: dict, mod_dir: Path) -> str:
    """Return a terminal-ready CLI snippet for the module."""
    fn       = raw.get("function", {})
    fn_name  = fn.get("name", "")
    sig      = fn.get("signature", "")
    py       = _module_main_py(raw, mod_dir)

    # Try to read exported names from __init__ or main file
    exported = fn_name
    if not exported and py and py.name == "__init__.py":
        try:
            src = py.read_text(encoding="utf-8", errors="ignore")
            import re as _re
            # Look for __all__ or def <name>
            m = _re.search(r'__all__\s*=\s*\[([^\]]+)\]', src)
            if m:
                names = _re.findall(r'"([^"]+)"|\'([^\']+)\'', m.group(1))
                exported = next((a or b for a, b in names if a or b), "")
            if not exported:
                m2 = _re.search(r'^def\s+(\w+)', src, _re.MULTILINE)
                if m2:
                    exported = m2.group(1)
        except Exception:
            pass

    # Build import path relative to SCRIPT_DIR
    if py:
        try:
            rel      = py.relative_to(SCRIPT_DIR)
            # For __init__.py, use the package path (without /__init__)
            if py.name == "__init__.py":
                mod_path = ".".join(rel.parent.parts)
            else:
                mod_path = ".".join(rel.with_suffix("").parts)
        except ValueError:
            mod_path = mod_dir.name

        # Bash: cd to project root
        lines = [f"# depuis la racine du projet EURKAI"]
        lines.append(f"cd {SCRIPT_DIR}")
        lines.append("")

        if exported:
            lines.append(f"python3 -c \"")
            lines.append(f"from {mod_path} import {exported}")

            # Build call from inputs
            fn_inputs = fn.get("inputs", raw.get("input_datas", raw.get("inputs", {})))
            if isinstance(fn_inputs, list):
                args = ", ".join(f"{a}=..." for a in fn_inputs[:4])
            elif isinstance(fn_inputs, dict):
                args = ", ".join(f"{k}=..." for k in list(fn_inputs.keys())[:4])
            else:
                args = "..."

            lines.append(f"result = {exported}({args})")
            lines.append(f"\"")
        else:
            lines.append(f"python3 -c \"from {mod_path} import *\"")

        if sig:
            lines.append(f"\n# Signature : {sig}")
        return "\n".join(lines)

    return (f"# Module introuvable sur le disque\n"
            f"# Chercher dans : {mod_dir}")


def _build_input_example(raw: dict) -> dict:
    """Build a minimal example input dict from MANIFEST."""
    fn_inputs = raw.get("function", {}).get("inputs", {})
    if not fn_inputs:
        fn_inputs = raw.get("inputs", {})
    example: dict = {}
    for field, desc in fn_inputs.items():
        desc_str = str(desc).lower()
        if "str" in desc_str:
            if "brief" in field:
                example[field] = "Agence de design parisienne, premium, minimaliste"
            elif "obligatoire" in desc_str or "required" in desc_str:
                example[field] = f"<{field}>"
            else:
                example[field] = None
        elif "dict" in desc_str:
            example[field] = None
        elif "list" in desc_str:
            example[field] = []
        elif "int" in desc_str or "float" in desc_str:
            example[field] = 0
        elif "bool" in desc_str:
            example[field] = True
        else:
            example[field] = None
    return example


_HUB_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#070710;--bg-card:#0c0c18;--bg-mod:#0a0a14;
  --border:#1a1a2e;--border-hi:#262640;
  --text:#e2e2f0;--muted:#56566e;--accent:#7c6bf5;
  --font-sans:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --font-mono:"SF Mono","Fira Code",monospace;
  --radius:8px;
}
body{background:var(--bg);color:var(--text);font-family:var(--font-sans);
  min-height:100vh;padding-bottom:80px}
a{text-decoration:none;color:inherit}
.header{display:flex;align-items:center;gap:10px;padding:16px 28px;
  border-bottom:1px solid var(--border);position:sticky;top:0;
  background:var(--bg);z-index:10}
.logo-mark{width:28px;height:28px;background:var(--accent);border-radius:6px;
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:700;color:#fff;letter-spacing:.02em}
.logo-text{font-size:14px;font-weight:600;letter-spacing:.04em}
.header-sep{color:var(--muted);margin:0 2px}
.header-sub{font-size:14px;color:var(--muted)}
.header-sp{flex:1}
.total-badge{font-size:11px;color:var(--muted);
  border:1px solid var(--border);border-radius:20px;padding:3px 10px}
.layout{max-width:860px;margin:0 auto;padding:32px 24px 0}
.section-title{font-size:10px;font-weight:600;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);margin-bottom:10px}
/* Tool cards */
.tool-cards{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:32px}
.tool-card{display:flex;flex-direction:column;gap:5px;
  background:var(--bg-card);border:1px solid var(--border);
  border-left:3px solid var(--accent);border-radius:var(--radius);
  padding:12px 14px;flex:1;min-width:160px;max-width:240px;
  transition:border-color .15s,background .15s}
.tool-card:hover{border-color:var(--accent);background:#0f0f1e}
.tc-name{font-size:13px;font-weight:600;color:var(--accent)}
.tc-desc{font-size:11px;color:var(--muted);line-height:1.45}
.tc-tags{display:flex;gap:4px;flex-wrap:wrap;margin-top:2px}
/* Category accordion */
.modules-wrap{display:flex;flex-direction:column;gap:5px}
.cat-block{background:var(--bg-card);border:1px solid var(--border);
  border-radius:var(--radius);overflow:hidden}
.cat-block[open]{border-color:var(--border-hi)}
.cat-summary{display:flex;align-items:center;gap:9px;
  padding:11px 14px;cursor:pointer;user-select:none;list-style:none;
  transition:background .12s}
.cat-summary:hover{background:#0d0d1c}
.cat-summary::-webkit-details-marker{display:none}
.cat-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.cat-label{font-size:13px;font-weight:600;flex:1}
.cat-count{font-size:10px;color:var(--muted);
  background:var(--border);border-radius:20px;padding:2px 7px}
.cat-chev{font-size:16px;color:var(--muted);transition:transform .18s;line-height:1}
.cat-block[open] .cat-chev{transform:rotate(90deg)}
.cat-body{border-top:1px solid var(--border)}
/* Module nested accordion */
.mod-block{border-bottom:1px solid var(--border)}
.mod-block:last-child{border-bottom:none}
.mod-block[open]{background:var(--bg-mod)}
.mod-summary{display:flex;align-items:center;gap:8px;
  padding:8px 14px 8px 26px;cursor:pointer;user-select:none;list-style:none;
  transition:background .1s}
.mod-summary:hover{background:#0d0d1c}
.mod-summary::-webkit-details-marker{display:none}
.status-dot{width:5px;height:5px;border-radius:50%;flex-shrink:0}
.mod-name{font-size:12px;font-weight:600;font-family:var(--font-mono);
  color:var(--text);white-space:nowrap}
.mod-tags-inline{display:flex;gap:4px;flex-wrap:wrap;flex:1}
.mod-chev{font-size:14px;color:var(--muted);transition:transform .18s;
  line-height:1;flex-shrink:0}
.mod-block[open] .mod-chev{transform:rotate(90deg)}
/* Module body */
.mod-body{padding:8px 14px 10px 26px;border-top:1px solid var(--border)11}
.mod-ver{font-size:10px;color:var(--muted);font-family:var(--font-mono);
  margin-bottom:5px;display:flex;align-items:center;gap:6px}
.ver-badge{border:1px solid var(--border);border-radius:4px;
  padding:1px 5px;color:var(--muted)}
.mod-desc{font-size:11px;color:var(--muted);line-height:1.5;margin-bottom:8px}
.mod-open-link{font-size:11px;color:var(--accent);
  border:1px solid rgba(124,107,245,.3);border-radius:4px;
  padding:3px 8px;background:rgba(124,107,245,.08);display:inline-block;
  transition:background .12s}
.mod-open-link:hover{background:rgba(124,107,245,.18)}
/* shared tag chip */
.tag-chip{font-size:10px;font-weight:500;border:1px solid;
  border-radius:4px;padding:1px 5px;letter-spacing:.02em;white-space:nowrap}
/* item type badge */
.type-badge{font-size:9px;font-weight:600;border-radius:3px;padding:1px 5px;
  letter-spacing:.04em;flex-shrink:0;border:1px solid}
.type-badge.mod{background:#7c6bf520;color:#7c6bf5;border-color:#7c6bf540}
.type-badge.ep{background:#22d3ee20;color:#22d3ee;border-color:#22d3ee40}
"""


_HUB_JS = """
const TAG_COLORS={visual:"#34d399",ai:"#818cf8",css:"#22d3ee",audit:"#fbbf24",
  capture:"#22d3ee",svg:"#34d399",pipeline:"#a78bfa",document:"#fb923c",seed:"#6b7280"};
const CAT_META={
  ai:{label:"AI",color:"#818cf8"},
  design:{label:"Design",color:"#34d399"},
  document:{label:"Document",color:"#fb923c"},
  capture:{label:"Capture",color:"#22d3ee"},
  quality:{label:"Qualité",color:"#fbbf24"},
  orchestration:{label:"Orchestration",color:"#a78bfa"},
  utility:{label:"Utilitaire",color:"#6b7280"}
};
const CAT_ORDER=["ai","design","document","capture","quality","orchestration","utility"];
const TOOL_PAGES=[
  {name:"Générateur",url:"page_generate",desc:"Lancer le pipeline complet depuis un brief",tags:["pipeline","ai"]}
];
function _esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function tagChip(t){const c=TAG_COLORS[t]||"#6b7280";return `<span class="tag-chip" style="color:${c};border-color:${c}44;background:${c}14">${_esc(t)}</span>`;}
function statusColor(s){return {stable:"#34d399",beta:"#fbbf24",wip:"#f87171",experimental:"#818cf8"}[s]||"#6b7280";}
function buildItemAccordion(item){
  const tags=(item.tags||[]).map(tagChip).join("");
  const dotCol=item.item_type==="endpoint"?"#22d3ee":statusColor(item.status);
  const typeBadge=item.item_type==="endpoint"
    ?'<span class="type-badge ep">endpoint</span>'
    :'<span class="type-badge mod">module</span>';
  const slug=encodeURIComponent(item.slug||item.name);
  const url=API_BASE+"/"+slug;
  const desc=item.description?((_esc(item.description.slice(0,180)))+(item.description.length>180?"…":"")):"";
  return `<details class="mod-block"><summary class="mod-summary">
  <span class="status-dot" style="background:${dotCol}"></span>
  <span class="mod-name">${_esc(item.name)}</span>
  ${typeBadge}
  <div class="mod-tags-inline">${tags}</div>
  <span class="mod-chev">›</span>
</summary><div class="mod-body">
  <div class="mod-ver"><span class="ver-badge">${_esc(item.version||"")}</span>${_esc(item.status||"")}</div>
  ${desc?`<div class="mod-desc">${desc}</div>`:""}
  <a class="mod-open-link" href="${url}">Ouvrir →</a>
</div></details>`;
}
function buildCatAccordion(cat,items){
  const m=CAT_META[cat]||{label:cat,color:"#6b7280"};
  return `<details class="cat-block"><summary class="cat-summary">
  <span class="cat-dot" style="background:${m.color}"></span>
  <span class="cat-label">${m.label}</span>
  <span class="cat-count">${items.length}</span>
  <span class="cat-chev">›</span>
</summary><div class="cat-body">${items.map(buildItemAccordion).join("")}</div></details>`;
}
function renderToolCards(pages){
  return pages.map(p=>{
    const tags=(p.tags||[]).map(tagChip).join("");
    return `<a class="tool-card" href="${API_BASE}/${p.url}">
  <div class="tc-name">${_esc(p.name)}</div>
  <div class="tc-desc">${_esc(p.desc||"")}</div>
  <div class="tc-tags">${tags}</div></a>`;
  }).join("");
}
async function loadCatalog(){
  try{
    const res=await fetch(API_BASE+"/api/catalog");
    if(!res.ok) throw new Error("HTTP "+res.status);
    const data=await res.json();
    const {items,meta}=data;
    document.getElementById("toolCards").innerHTML=renderToolCards(TOOL_PAGES);
    document.getElementById("totalBadge").textContent=`${meta.count} items — ${meta.modules} modules, ${meta.endpoints} endpoints`;
    const bycat={};
    items.forEach(item=>{const c=item.category||"utility";(bycat[c]=bycat[c]||[]).push(item);});
    Object.values(bycat).forEach(arr=>arr.sort((a,b)=>(a.name||"").localeCompare(b.name||"")));
    const wrap=document.getElementById("modulesWrap");
    const orderedCats=[...CAT_ORDER,...Object.keys(bycat).filter(c=>!CAT_ORDER.includes(c))];
    wrap.innerHTML=orderedCats.filter(c=>bycat[c]&&bycat[c].length).map(c=>buildCatAccordion(c,bycat[c])).join("");
  }catch(e){
    document.getElementById("modulesWrap").innerHTML=`<div style="color:#f87171;font-size:12px;padding:20px 0">Erreur chargement : ${_esc(e.message)}</div>`;
  }
}
document.addEventListener("DOMContentLoaded",loadCatalog);
"""


def _build_hub_html() -> str:
    """Static shell — catalog data loaded client-side via GET /api/catalog."""
    return (
        '<!DOCTYPE html><html lang="fr"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '<title>EURKAI — Tools</title>'
        f'<style>{_HUB_CSS}</style>'
        '</head><body>'
        '<header class="header">'
        '<div class="logo-mark">EK</div>'
        '<span class="logo-text">EURKAI</span>'
        '<span class="header-sep">/</span>'
        '<span class="header-sub">Tools</span>'
        '<div class="header-sp"></div>'
        '<span class="total-badge" id="totalBadge">Chargement…</span>'
        '</header>'
        '<div class="layout">'
        '<div class="section-title">Outils</div>'
        '<div class="tool-cards" id="toolCards"></div>'
        '<div class="section-title" style="margin-bottom:10px">Modules &amp; Endpoints</div>'
        '<div class="modules-wrap" id="modulesWrap">'
        '<div style="color:var(--muted);font-size:12px;padding:20px 0">Chargement du catalogue…</div>'
        '</div>'
        '</div>'
        f'<script>const API_BASE="{_PREFIX}";</script>'
        f'<script>{_HUB_JS}</script>'
        '</body></html>'
    )


# ─── Module detail page ───────────────────────────────────────────────────────

_MOD_PAGE_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#070710;--bg-card:#0c0c18;--bg-input:#090914;
  --border:#1a1a2e;--border-hi:#2e2e50;
  --text:#e2e2f0;--muted:#56566e;--accent:#7c6bf5;
  --success:#34d399;--warn:#fbbf24;--error:#f87171;
  --font-sans:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --font-mono:"SF Mono","Fira Code",monospace;
  --radius:8px;
}
body{background:var(--bg);color:var(--text);font-family:var(--font-sans);
  min-height:100vh;padding-bottom:80px}
a{text-decoration:none;color:inherit}
/* Header */
.header{display:flex;align-items:center;gap:10px;padding:14px 28px;
  border-bottom:1px solid var(--border);position:sticky;top:0;
  background:var(--bg);z-index:10}
.back{font-size:12px;color:var(--muted);padding:4px 8px;
  border:1px solid var(--border);border-radius:4px;transition:color .12s,border-color .12s}
.back:hover{color:var(--text);border-color:var(--border-hi)}
.h-sep{color:var(--border);margin:0 4px}
.mod-title{font-size:14px;font-weight:600;font-family:var(--font-mono)}
.mod-ver-h{font-size:11px;color:var(--muted);
  border:1px solid var(--border);border-radius:4px;padding:2px 7px;
  font-family:var(--font-mono)}
.status-badge{font-size:10px;padding:2px 8px;border-radius:4px;font-weight:600}
.header-sp{flex:1}
.save-btn{font-size:12px;color:var(--accent);
  border:1px solid rgba(124,107,245,.4);border-radius:5px;padding:5px 14px;
  background:rgba(124,107,245,.1);cursor:pointer;transition:background .12s}
.save-btn:hover{background:rgba(124,107,245,.2)}
.save-btn:disabled{opacity:.4;cursor:default}
/* Layout */
.layout{max-width:1100px;margin:0 auto;padding:28px 24px 0;
  display:grid;grid-template-columns:1fr 420px;gap:24px}
@media(max-width:820px){.layout{grid-template-columns:1fr}}
/* Panels */
.panel{display:flex;flex-direction:column;gap:18px}
.block{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius)}
.block-title{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);padding:10px 14px;border-bottom:1px solid var(--border)}
.block-body{padding:14px}
/* Editable fields */
.desc-area{width:100%;min-height:80px;background:var(--bg-input);
  border:1px solid var(--border);border-radius:5px;padding:10px;
  color:var(--text);font-size:12px;line-height:1.6;resize:vertical;
  font-family:var(--font-sans)}
.desc-area:focus{outline:none;border-color:var(--border-hi)}
/* Tags editor */
.tags-wrap{display:flex;gap:6px;flex-wrap:wrap;align-items:center;min-height:30px}
.tag-chip{font-size:11px;font-weight:500;border:1px solid;
  border-radius:4px;padding:2px 7px;display:flex;align-items:center;gap:5px}
.tag-rm{cursor:pointer;opacity:.6;font-size:13px;line-height:1}
.tag-rm:hover{opacity:1}
.tag-add{font-size:11px;border:1px dashed var(--border);border-radius:4px;
  padding:2px 8px;background:transparent;color:var(--muted);cursor:pointer;
  font-family:var(--font-sans);transition:border-color .12s,color .12s}
.tag-add:hover{border-color:var(--accent);color:var(--accent)}
.tag-input{font-size:11px;background:var(--bg-input);border:1px solid var(--border-hi);
  border-radius:4px;padding:2px 7px;color:var(--text);outline:none;width:100px;
  font-family:var(--font-sans)}
/* CLI block */
.cli-pre{font-family:var(--font-mono);font-size:11px;line-height:1.65;
  color:#94a3b8;background:var(--bg-input);border-radius:5px;padding:12px;
  overflow-x:auto;white-space:pre}
.cli-copy{float:right;font-size:10px;color:var(--muted);
  border:1px solid var(--border);border-radius:3px;padding:1px 6px;
  cursor:pointer;margin-left:8px;background:var(--bg);transition:color .1s}
.cli-copy:hover{color:var(--text)}
/* Inputs table */
.inputs-table{width:100%;border-collapse:collapse;font-size:11px}
.inputs-table th{text-align:left;color:var(--muted);font-weight:600;
  padding:5px 8px;border-bottom:1px solid var(--border);white-space:nowrap}
.inputs-table td{padding:6px 8px;border-bottom:1px solid var(--border)14;
  vertical-align:top;line-height:1.4}
.inputs-table tr:last-child td{border-bottom:none}
.field-name{font-family:var(--font-mono);color:var(--accent);font-size:11px}
.field-req{font-size:9px;padding:1px 5px;border-radius:3px;font-weight:700;
  letter-spacing:.04em}
.req-yes{background:#f8717120;color:#f87171}
.req-opt{background:#34d39920;color:#34d399}
/* Test runner */
.test-area{width:100%;height:220px;background:var(--bg-input);
  border:1px solid var(--border);border-radius:5px;padding:10px;
  color:var(--text);font-size:11px;line-height:1.6;resize:vertical;
  font-family:var(--font-mono)}
.test-area:focus{outline:none;border-color:var(--border-hi)}
.run-btn{margin-top:8px;width:100%;padding:9px;background:var(--accent);
  border:none;border-radius:6px;color:#fff;font-size:13px;font-weight:600;
  cursor:pointer;transition:opacity .12s;display:flex;align-items:center;
  justify-content:center;gap:8px}
.run-btn:hover{opacity:.88}
.run-btn:disabled{opacity:.45;cursor:default}
.spin{width:14px;height:14px;border:2px solid rgba(255,255,255,.3);
  border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
/* Output */
.out-box{font-family:var(--font-mono);font-size:11px;line-height:1.6;
  min-height:80px;padding:12px;background:var(--bg-input);
  border:1px solid var(--border);border-radius:5px;
  color:#94a3b8;overflow-x:auto;white-space:pre;margin-top:10px}
.out-ok{border-color:#34d39930;color:#94a3b8}
.out-err{border-color:#f8717130;color:#f87171}
"""


def _build_module_page_html(module_name: str) -> tuple[str, int]:
    raw, mod_dir = _find_manifest_for(module_name)
    if raw is None:
        raw, mod_dir = _find_endpoint_for(module_name)
    if raw is None:
        return (f'<html><body style="background:#070710;color:#e2e2f0;'
                f'font-family:monospace;padding:40px">'
                f'<p>Item <b>{module_name}</b> introuvable dans les modules et endpoints.</p>'
                f'<p><a href="{_PREFIX}/" style="color:#7c6bf5">← Retour</a></p>'
                f'</body></html>'), 404

    fn      = raw.get("function", {})
    name    = (raw.get("module") or raw.get("name") or mod_dir.name)
    version = raw.get("version", "")
    status  = raw.get("status", "stable")
    desc    = raw.get("description", "")
    tags    = _hub_tags(module_name, raw)
    fn_inputs  = fn.get("inputs", raw.get("inputs", {})) or {}
    fn_outputs = fn.get("output", fn.get("outputs", raw.get("outputs", {}))) or {}
    # CLI hint — endpoint files have _py_file, modules use _build_cli_hint
    if raw.get("_py_file"):
        py_path = raw["_py_file"]
        try:
            rel     = Path(py_path).relative_to(SCRIPT_DIR)
            mod_path = ".".join(rel.with_suffix("").parts)
            ep_name  = raw.get("name", module_name)
            cli = (f"from {mod_path} import run\n\n"
                   f"# Appel\nresult = run(**inputs)  # → {ep_name}")
        except ValueError:
            cli = f"# Endpoint: {module_name}\nfrom ... import run"
    else:
        cli = _build_cli_hint(raw, mod_dir)
    example = _build_input_example(raw)

    def _esc(s: str) -> str:
        return (s.replace("&","&amp;").replace("<","&lt;")
                 .replace(">","&gt;").replace('"',"&quot;"))

    stat_col = {"stable":"#34d399","beta":"#fbbf24","wip":"#f87171",
                "experimental":"#818cf8"}.get(status,"#6b7280")

    def _tag_chip_edit(t: str) -> str:
        col = _HUB_TAG_COLORS.get(t, "#6b7280")
        return (f'<span class="tag-chip" data-tag="{_esc(t)}" style="'
                f'color:{col};border-color:{col}44;background:{col}14">'
                f'{_esc(t)}'
                f'<span class="tag-rm" onclick="removeTag(this)">×</span></span>')

    tags_chips = "".join(_tag_chip_edit(t) for t in tags)

    def _input_row(field: str, desc_v) -> str:
        desc_str = str(desc_v)
        is_req   = "obligatoire" in desc_str.lower() or (
            "none" not in desc_str.lower() and "|" not in desc_str
        )
        req_html = (f'<span class="field-req req-yes">req</span>' if is_req
                    else f'<span class="field-req req-opt">opt</span>')
        return (f'<tr><td><span class="field-name">{_esc(field)}</span></td>'
                f'<td>{req_html}</td>'
                f'<td style="color:var(--muted)">{_esc(desc_str[:120])}</td></tr>')

    inputs_rows = "".join(_input_row(f, d) for f, d in fn_inputs.items())

    # Output schema summary
    def _out_row(field: str, desc_v) -> str:
        return (f'<tr><td><span class="field-name">{_esc(field)}</span></td>'
                f'<td style="color:var(--muted)">{_esc(str(desc_v)[:120])}</td></tr>')

    if isinstance(fn_outputs, dict):
        out_rows = "".join(_out_row(f, d) for f, d in fn_outputs.items())
    else:
        out_rows = f'<tr><td colspan="2" style="color:var(--muted)">{_esc(str(fn_outputs))}</td></tr>'

    example_json = json.dumps(example, indent=2, ensure_ascii=False)
    cli_escaped  = _esc(cli)
    run_url      = f"{_PREFIX}/api/run/{module_name}"
    save_url     = f"{_PREFIX}/api/modules/{module_name}"

    js = r"""
function removeTag(el) {
  el.parentElement.remove();
  markDirty();
}
function addTag() {
  const inp = document.getElementById('tagInput');
  const v = inp.value.trim().toLowerCase().replace(/\s+/g,'_');
  if (!v) return;
  const wrap = document.getElementById('tagsWrap');
  const span = document.createElement('span');
  span.className = 'tag-chip';
  span.dataset.tag = v;
  span.style = 'color:#7c6bf5;border-color:#7c6bf544;background:#7c6bf514';
  span.innerHTML = v + '<span class="tag-rm" onclick="removeTag(this)">×</span>';
  wrap.insertBefore(span, wrap.querySelector('.tag-add'));
  inp.value = '';
  inp.style.display = 'none';
  markDirty();
}
document.getElementById('tagInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); addTag(); }
  if (e.key === 'Escape') {
    e.target.style.display = 'none'; e.target.value = '';
  }
});
document.querySelector('.tag-add').addEventListener('click', () => {
  const inp = document.getElementById('tagInput');
  inp.style.display = inp.style.display === 'none' ? 'inline-block' : 'none';
  if (inp.style.display !== 'none') inp.focus();
});
function markDirty() {
  document.getElementById('saveBtn').disabled = false;
}
document.getElementById('descArea').addEventListener('input', markDirty);

async function saveModule() {
  const btn  = document.getElementById('saveBtn');
  const desc = document.getElementById('descArea').value;
  const tags = [...document.querySelectorAll('#tagsWrap .tag-chip')]
    .map(el => el.dataset.tag).filter(Boolean);
  btn.disabled = true;
  btn.textContent = 'Sauvegarde…';
  try {
    const r = await fetch(SAVE_URL, {
      method:'PUT',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({description: desc, tags})
    });
    const d = await r.json();
    btn.textContent = d.ok ? '✓ Sauvegardé' : '✗ Erreur';
  } catch(e) {
    btn.textContent = '✗ Erreur réseau';
  }
  setTimeout(() => { btn.textContent = 'Sauvegarder'; }, 2000);
}

async function runModule() {
  const btn = document.getElementById('runBtn');
  const ta  = document.getElementById('testArea');
  const out = document.getElementById('outBox');
  let inputs;
  try { inputs = JSON.parse(ta.value); } catch(e) {
    out.className = 'out-box out-err';
    out.textContent = 'JSON invalide : ' + e.message; return;
  }
  btn.disabled = true;
  btn.innerHTML = '<div class="spin"></div> Exécution…';
  out.className = 'out-box';
  out.textContent = '…';
  try {
    const r = await fetch(RUN_URL, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({inputs})
    });
    const d = await r.json();
    if (d.ok) {
      out.className = 'out-box out-ok';
      out.textContent = JSON.stringify(d.output, null, 2);
    } else {
      out.className = 'out-box out-err';
      out.textContent = (d.error || 'Erreur') + '\n\n' + (d.traceback || '');
    }
  } catch(e) {
    out.className = 'out-box out-err';
    out.textContent = 'Erreur réseau : ' + e.message;
  }
  btn.disabled = false;
  btn.innerHTML = '&#9654; Exécuter';
}
"""

    html = (
        '<!DOCTYPE html><html lang="fr"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f'<title>EURKAI — {_esc(name)}</title>'
        f'<style>{_MOD_PAGE_CSS}</style>'
        '</head><body>'
        '<header class="header">'
        f'<a class="back" href="{_PREFIX}/">← Tools</a>'
        '<span class="h-sep">/</span>'
        f'<span class="mod-title">{_esc(name)}</span>'
        + (f'<span class="mod-ver-h">{_esc(version)}</span>' if version else "")
        + f'<span class="status-badge" style="background:{stat_col}22;color:{stat_col}">'
          f'{_esc(status)}</span>'
          '<div class="header-sp"></div>'
          '<button class="save-btn" id="saveBtn" onclick="saveModule()" disabled>Sauvegarder</button>'
          '</header>'
          '<div class="layout">'
          # Left column
          '<div class="panel">'
          # Description
          '<div class="block">'
          '<div class="block-title">Description</div>'
          '<div class="block-body">'
          f'<textarea class="desc-area" id="descArea">{_esc(desc)}</textarea>'
          '</div></div>'
          # Tags
          '<div class="block">'
          '<div class="block-title">Tags</div>'
          '<div class="block-body">'
          f'<div class="tags-wrap" id="tagsWrap">{tags_chips}'
          '<button class="tag-add">+ tag</button>'
          '<input class="tag-input" id="tagInput" placeholder="nom…" style="display:none">'
          '</div></div></div>'
          # CLI
          '<div class="block">'
          '<div class="block-title">CLI / Import</div>'
          '<div class="block-body">'
          f'<button class="cli-copy" onclick="navigator.clipboard.writeText(document.getElementById(\'cliPre\').textContent)">Copier</button>'
          f'<pre class="cli-pre" id="cliPre">{cli_escaped}</pre>'
          '</div></div>'
          # Inputs
          + ('<div class="block">'
             '<div class="block-title">Inputs</div>'
             '<div class="block-body">'
             '<table class="inputs-table">'
             '<thead><tr><th>Champ</th><th></th><th>Description</th></tr></thead>'
             f'<tbody>{inputs_rows}</tbody>'
             '</table></div></div>' if inputs_rows else "")
          # Outputs
          + ('<div class="block">'
             '<div class="block-title">Output</div>'
             '<div class="block-body">'
             '<table class="inputs-table">'
             '<thead><tr><th>Champ</th><th>Description</th></tr></thead>'
             f'<tbody>{out_rows}</tbody>'
             '</table></div></div>' if out_rows else "")
          + '</div>'
          # Right column — test runner
          '<div class="panel">'
          '<div class="block">'
          '<div class="block-title">Test</div>'
          '<div class="block-body">'
          f'<textarea class="test-area" id="testArea">{_esc(example_json)}</textarea>'
          '<button class="run-btn" id="runBtn" onclick="runModule()">&#9654; Exécuter</button>'
          '<div class="out-box" id="outBox" style="display:none"></div>'
          '</div></div>'
          '</div>'  # end right col
          '</div>'  # end layout
          f'<script>const RUN_URL="{run_url}";const SAVE_URL="{save_url}";{js}</script>'
          '</body></html>'
    )
    return html, 200



# ─── Output path → URL ───────────────────────────────────────────────────────
def _output_url(abs_path: str | None) -> str | None:
    if not abs_path:
        return None
    try:
        rel = Path(abs_path).relative_to(OUTPUT_DIR)
        return f"{_PREFIX}/output/{rel.as_posix()}"
    except ValueError:
        return None


# ─── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=None)
app.config["JSON_SORT_KEYS"] = False


@app.route(_PREFIX + "/")
def hub():
    return _build_hub_html()


@app.route(_PREFIX + "/page_generate")
def index():
    # Inject prefix so JS fetch() calls use the right base path
    injected = _HTML.replace(
        "const API_BASE = (document.currentScript && document.currentScript.dataset.prefix) || window.__API_BASE__ || '';",
        f"const API_BASE = '{_PREFIX}';",
        1,
    )
    return injected


@app.route(_PREFIX + "/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(force=True, silent=True) or {}

    brief        = (data.get("brief") or "").strip()
    project_name = (data.get("project_name") or "").strip()

    if not brief:
        return jsonify(error="Brief manquant"), 400
    if not project_name:
        import uuid as _uuid
        site_fam  = (data.get("site_family") or "projet").replace("_", "-")
        _harmony  = data.get("harmony") or "complementary"
        # Abbréviations harmonie pour le nom de fichier
        _HAR_SHORT = {
            "complementary": "comp", "analogous": "ana", "triadic": "triad",
            "monochromatic": "mono", "minimal": "min",
            "bw_light": "nb-l", "bw_dark": "nb-d",
        }
        har_tag = _HAR_SHORT.get(_harmony, _harmony[:4])
        project_name = f"{site_fam}_{har_tag}_{_uuid.uuid4().hex[:6]}"

    seed          = int(data.get("seed") or 42)
    harmony       = data.get("harmony") or "complementary"
    site_family   = data.get("site_family") or ""
    enable_capture = bool(data.get("enable_capture", True))
    enable_audit   = bool(data.get("enable_audit", True))
    nb_options     = max(1, min(5, int(data.get("nb_options") or 1)))
    charter_mode   = data.get("charter_mode") or "none"   # none | also | only
    # cp_palette provenant du visuel de référence uploadé
    _cp = data.get("cp_palette")
    cp_palette: dict | None = _cp if isinstance(_cp, dict) and _cp else None

    params = dict(seed=seed, harmony=harmony, site_family=site_family,
                  enable_capture=enable_capture, enable_audit=enable_audit,
                  nb_options=nb_options, charter_mode=charter_mode,
                  has_ref_palette=bool(cp_palette))
    job_id = _new_job(project_name, brief, params)

    t = threading.Thread(
        target=_run_job,
        args=(job_id, brief, project_name, seed,
              harmony, site_family, enable_capture, enable_audit,
              False, nb_options, charter_mode),
        kwargs={"cp_palette": cp_palette},
        daemon=True,
    )
    t.start()
    return jsonify(job_id=job_id)


@app.route(_PREFIX + "/api/status/<job_id>")
def api_status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify(error="Job introuvable"), 404
    data = dict(job)
    data["output_url"]   = _output_url(data.get("output_path"))
    data["output_urls"]  = [_output_url(p) for p in data.get("output_paths")  or [] if p]
    data["charter_urls"] = [_output_url(p) for p in data.get("charter_paths") or [] if p]
    return jsonify(data)


@app.route(_PREFIX + "/api/history")
def api_history():
    history = _load_history()
    for h in history:
        h["output_url"] = _output_url(h.get("output_path"))
    return jsonify(history[:30])


@app.route(_PREFIX + "/output/<path:filename>")
def serve_output(filename: str):
    return send_from_directory(str(OUTPUT_DIR), filename)


def _colors_to_cp_palette(colors: list[str], harmony: str = "complementary") -> dict | None:
    """Convertit couleurs hex → cp_palette avec harmonie appliquée (rotation de teinte)."""
    if not colors:
        return None
    import colorsys as _cs

    def _hex_rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def _sat(h: str) -> float:
        r, g, b = _hex_rgb(h)
        _, s, _ = _cs.rgb_to_hsv(r / 255, g / 255, b / 255)
        return s

    def _lum(h: str) -> float:
        r, g, b = _hex_rgb(h)
        return (r + g + b) / 765

    def _auto_text(bg: str) -> str:
        return "#111111" if _lum(bg) > 0.5 else "#f8f8f8"

    def _hsv_hex(hh: float, s: float, v: float) -> str:
        r2, g2, b2 = _cs.hsv_to_rgb(hh % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
        return f"#{int(r2*255):02x}{int(g2*255):02x}{int(b2*255):02x}"

    by_sat = sorted(colors, key=_sat, reverse=True)
    by_lum = sorted(colors, key=_lum)

    primary = by_sat[0]
    r, g, b = _hex_rgb(primary)
    ph, ps, pv = _cs.rgb_to_hsv(r / 255, g / 255, b / 255)

    # Secondary et accent dérivés par harmonie (rotation de teinte)
    if harmony in ("bw_light", "bw_dark", "black_and_white"):
        # Noir & blanc : palette désaturée, fond clair ou sombre
        dark = (harmony == "bw_dark")
        background = "#111111" if dark else "#f5f5f5"
        surface    = "#1e1e1e" if dark else "#ebebeb"
        primary    = "#eeeeee" if dark else "#1a1a1a"
        secondary  = "#aaaaaa" if dark else "#555555"
        accent     = "#ffffff" if dark else "#000000"
        text_primary   = "#f0f0f0" if dark else "#111111"
        text_secondary = "#aaaaaa" if dark else "#666666"
        border         = "#333333" if dark else "#cccccc"
        return {
            "primary": primary, "secondary": secondary, "accent": accent,
            "background": background, "surface": surface,
            "text_primary": text_primary, "text_secondary": text_secondary,
            "border": border,
        }
    elif harmony == "complementary":
        secondary = _hsv_hex(ph + 0.5, ps * 0.75, pv * 0.9)
        accent    = _hsv_hex(ph + 0.5, ps,         pv)
    elif harmony == "analogous":
        secondary = _hsv_hex(ph + 0.083, ps * 0.9, pv)
        accent    = _hsv_hex(ph - 0.083, ps,        pv * 0.9)
    elif harmony == "triadic":
        secondary = _hsv_hex(ph + 0.333, ps * 0.85, pv)
        accent    = _hsv_hex(ph + 0.667, ps * 0.85, pv)
    elif harmony in ("monochromatic", "minimal"):
        secondary = _hsv_hex(ph, ps * 0.55, pv * 0.80)
        accent    = _hsv_hex(ph, min(1.0, ps * 1.15), min(1.0, pv * 1.05))
    else:
        secondary = by_sat[1] if len(by_sat) > 1 else _hsv_hex(ph + 0.5, ps * 0.75, pv * 0.9)
        accent    = by_sat[2] if len(by_sat) > 2 else _hsv_hex(ph + 0.5, ps, pv)

    # Fond : couleur la plus lumineuse ou généré depuis primaire
    lightest = by_lum[-1]
    if _lum(lightest) > 0.65:
        background = lightest
    else:
        r2, g2, b2 = _cs.hsv_to_rgb(ph, ps * 0.08, 0.96)
        background = f"#{int(r2*255):02x}{int(g2*255):02x}{int(b2*255):02x}"

    bg_lum = _lum(background)
    br, bg_, bb = _hex_rgb(background)
    bh, bs, bv = _cs.rgb_to_hsv(br / 255, bg_ / 255, bb / 255)
    surface        = _hsv_hex(bh, bs, bv - 0.04 if bg_lum > 0.5 else bv + 0.06)
    text_primary   = _auto_text(background)
    text_secondary = "#666666" if text_primary == "#111111" else "#aaaaaa"
    border         = "#e0e0e0" if text_primary == "#111111" else "#333333"

    return {
        "primary":        primary,
        "secondary":      secondary,
        "accent":         accent,
        "background":     background,
        "surface":        surface,
        "text_primary":   text_primary,
        "text_secondary": text_secondary,
        "border":         border,
    }


@app.route(_PREFIX + "/api/upload-ref", methods=["POST"])
def api_upload_ref():
    """Reçoit une image, l'enregistre, extrait les couleurs dominantes → cp_palette."""
    f = request.files.get("image")
    if not f:
        return jsonify(ok=False, error="Pas de fichier"), 400

    # Sécurisation du nom de fichier
    import re as _re
    safe_name = _re.sub(r"[^a-zA-Z0-9._-]", "_", f.filename or "ref.png")
    ref_dir   = OUTPUT_DIR / "_refs"
    ref_dir.mkdir(parents=True, exist_ok=True)
    dest = ref_dir / f"{uuid.uuid4().hex[:8]}_{safe_name}"
    f.save(str(dest))

    colors: list[str] = []
    try:
        from PIL import Image as _Img
        img = _Img.open(dest).convert("RGB").resize((150, 150))
        quantized = img.quantize(colors=12, method=_Img.Quantize.FASTOCTREE)
        pal = quantized.getpalette() or []
        n = len(pal) // 3  # nombre réel de couleurs dans la palette
        all_colors: list[tuple[float, str]] = []
        for i in range(n):
            r, g, b = pal[i*3], pal[i*3+1], pal[i*3+2]
            # Exclure uniquement blanc/noir quasi-purs
            bright = (r + g + b) / 765
            if bright < 0.02 or bright > 0.98:
                continue
            sat = (max(r,g,b) - min(r,g,b)) / max(max(r,g,b), 1)
            all_colors.append((sat, f"#{r:02x}{g:02x}{b:02x}"))
        # Trier par saturation décroissante → couleurs chromatiques en tête
        all_colors.sort(key=lambda x: x[0], reverse=True)
        colors = [c for _, c in all_colors][:6]
    except ImportError:
        pass  # PIL non dispo
    except Exception as _pil_err:
        print(f"[upload-ref] PIL error: {_pil_err}", flush=True)
        import traceback; traceback.print_exc()

    cp_palette = _colors_to_cp_palette(colors)
    print(f"[upload-ref] extracted {len(colors)} colors: {colors}", flush=True)
    url = f"{_PREFIX}/output/_refs/{dest.name}"
    return jsonify(ok=True, url=url, colors=colors, cp_palette=cp_palette, path=str(dest))


@app.route(_PREFIX + "/api/ping")
def ping():
    return jsonify(ok=True, pipeline_ok=_PIPELINE_OK)


@app.route(_PREFIX + "/api/apply-harmony", methods=["POST"])
def api_apply_harmony():
    """Recalcule cp_palette depuis couleurs brutes + harmonie choisie."""
    data    = request.get_json(force=True, silent=True) or {}
    colors  = [c for c in (data.get("colors") or []) if isinstance(c, str) and c.startswith("#")]
    harmony = data.get("harmony") or "complementary"
    cp = _colors_to_cp_palette(colors, harmony)
    return jsonify(ok=bool(cp), cp_palette=cp)


@app.route(_PREFIX + "/api/pick-directory")
def api_pick_directory():
    """Ouvre une fenêtre Finder native (macOS osascript) et retourne le chemin."""
    import subprocess, sys as _sys
    try:
        if _sys.platform == "darwin":
            # AppleScript → vrai Finder natif
            script = (
                'POSIX path of (choose folder '
                'with prompt "EURKAI — Choisir le répertoire de destination")'
            )
            r = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=120,
            )
            if r.returncode == 0:
                path = r.stdout.strip().rstrip("/")
                return jsonify(ok=True, path=path)
            # Code 1 = annulé par l'utilisateur
            if r.returncode == 1:
                return jsonify(ok=False, cancelled=True)
            return jsonify(ok=False, error=r.stderr.strip()), 500

        else:
            # Linux / Windows — fallback tkinter
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk(); root.withdraw()
            root.wm_attributes("-topmost", True)
            path = filedialog.askdirectory(title="EURKAI — Répertoire de destination")
            root.destroy()
            if path:
                return jsonify(ok=True, path=path)
            return jsonify(ok=False, cancelled=True)

    except subprocess.TimeoutExpired:
        return jsonify(ok=False, cancelled=True)
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 500


@app.route(_PREFIX + "/api/scrape", methods=["POST"])
def api_scrape():
    """Démarre un job de scraping (page ou site). Retourne {ok, job_id}."""
    body      = request.get_json(silent=True) or {}
    url       = body.get("url", "").strip()
    mode      = body.get("mode", "page")           # "page" | "site"
    output_dir = body.get("output_dir") or None
    max_pages = int(body.get("max_pages", 100))
    max_depth = int(body.get("max_depth", 5))

    if not url:
        return jsonify(error="Paramètre 'url' manquant"), 400
    if mode not in ("page", "site"):
        return jsonify(error="mode doit être 'page' ou 'site'"), 400

    job_id = uuid.uuid4().hex[:10]
    with _jobs_lock:
        _jobs[job_id] = {
            "job_id":       job_id,
            "type":         "scrape",
            "url":          url,
            "mode":         mode,
            "status":       "running",
            "started_at":   datetime.now().isoformat(timespec="seconds"),
            "finished_at":  None,
            "duration_s":   None,
            "pages_count":  None,
            "assets_count": None,
            "output_dir":   None,
            "error":        None,
            "logs":         [],
        }

    thread = threading.Thread(
        target=_run_scrape_job,
        args=(job_id, url, mode, output_dir, max_pages, max_depth),
        daemon=True,
    )
    thread.start()

    return jsonify(ok=True, job_id=job_id)


@app.route(_PREFIX + "/api/scrape/status/<job_id>")
def api_scrape_status(job_id: str):
    """Retourne le statut d'un job de scraping."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        return jsonify(error="Job introuvable"), 404
    return jsonify(job)


def _run_scrape_job(
    job_id:     str,
    url:        str,
    mode:       str,
    output_dir: str | None,
    max_pages:  int,
    max_depth:  int,
) -> None:
    """Thread de scraping — met à jour _jobs[job_id] en temps réel."""
    import time as _time
    import sys as _sys

    t0 = _time.time()

    def _log(msg: str) -> None:
        stripped = msg.strip()
        if stripped:
            with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]["logs"].append(stripped)

    try:
        # Import du package web_scraper/src/ avec gestion correcte des imports relatifs.
        # On ajoute MODULES/web_scraper au sys.path pour que "src" soit un package valide.
        import importlib as _il
        _pkg_parent = str(SCRIPT_DIR / "MODULES" / "web_scraper")
        if _pkg_parent not in _sys.path:
            _sys.path.insert(0, _pkg_parent)
        # Nettoyer les modules en cache pour éviter les conflits si rechargé
        for _k in list(_sys.modules.keys()):
            if _k == "src" or _k.startswith("src."):
                del _sys.modules[_k]
        _ws = _il.import_module("src")

        if mode == "site":
            result = _ws.scrape_site(
                url          = url,
                output_dir   = output_dir,
                max_pages    = max_pages,
                max_depth    = max_depth,
                on_progress  = _log,
            )
        else:
            result = _ws.scrape_page(
                url          = url,
                output_dir   = output_dir,
                on_progress  = _log,
            )

        duration = round(_time.time() - t0, 1)
        with _jobs_lock:
            _jobs[job_id].update({
                "status":       "success" if result.success else "error",
                "finished_at":  datetime.now().isoformat(timespec="seconds"),
                "duration_s":   duration,
                "pages_count":  result.pages_count,
                "assets_count": result.assets_count,
                "output_dir":   str(result.output_dir),
                "error":        result.error,
            })

    except Exception as exc:
        import traceback as _tb
        duration = round(_time.time() - t0, 1)
        _log(f"ERREUR FATALE : {exc}")
        _log(_tb.format_exc())
        with _jobs_lock:
            _jobs[job_id].update({
                "status":      "error",
                "finished_at": datetime.now().isoformat(timespec="seconds"),
                "duration_s":  duration,
                "error":       str(exc),
            })


@app.route(_PREFIX + "/api/catalog")
def api_catalog():
    """Return all modules + endpoints as JSON. Scanned fresh on each call."""
    modules = [
        {
            "slug":        m["name"],
            "name":        m["name"],
            "item_type":   "module",
            "version":     m["version"],
            "description": m["description"],
            "status":      m["status"],
            "category":    m["category"],
            "tags":        m["tags"],
        }
        for m in _scan_manifests()
    ]
    endpoints = [
        {
            "slug":        e["slug"],
            "name":        e["name"],
            "item_type":   "endpoint",
            "version":     e["version"],
            "description": e["description"],
            "status":      e["status"],
            "category":    e["category"],
            "tags":        e["tags"],
        }
        for e in _scan_endpoints()
    ]
    items = modules + endpoints
    return jsonify({
        "items": items,
        "meta": {
            "count":      len(items),
            "modules":    len(modules),
            "endpoints":  len(endpoints),
            "scanned_at": datetime.now().isoformat(timespec="seconds"),
        },
    })


@app.route(_PREFIX + "/<module_name>")
def module_page(module_name: str):
    # Block routes that are "real" sub-paths (avoid matching output/, api/, page_generate)
    if module_name in ("output", "api", "page_generate", "favicon.ico", "static"):
        from flask import abort
        abort(404)
    html, status = _build_module_page_html(module_name)
    return html, status


@app.route(_PREFIX + "/api/run/<module_name>", methods=["POST"])
def api_run_module(module_name: str):
    """Dynamically import the module's main callable and run it with posted JSON."""
    import sys, importlib.util, traceback, time

    raw, mod_dir = _find_manifest_for(module_name)
    if raw is None:
        raw, mod_dir = _find_endpoint_for(module_name)
    if raw is None:
        return jsonify(error=f"Item '{module_name}' introuvable"), 404

    # For endpoints, use _py_file directly
    if raw.get("_py_file"):
        main_py = Path(raw["_py_file"])
    else:
        main_py = _module_main_py(raw, mod_dir)
    if main_py is None:
        return jsonify(error="Aucun fichier Python trouvé pour ce module"), 404

    body = request.get_json(silent=True) or {}
    inputs = body.get("inputs", body)

    # Load module dynamically
    spec = importlib.util.spec_from_file_location(f"_dyn_{module_name}", str(main_py))
    mod  = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return jsonify(error="Erreur au chargement du module", detail=traceback.format_exc()), 500

    # Try common entry point names
    fn = None
    for name in ("main", "run", "generate", "execute", module_name.replace("-", "_")):
        fn = getattr(mod, name, None)
        if callable(fn):
            break

    if fn is None:
        return jsonify(error="Aucune fonction d'entrée trouvée (main/run/generate)"), 404

    t0 = time.perf_counter()
    try:
        result = fn(**inputs) if inputs else fn()
    except TypeError:
        try:
            result = fn(inputs)
        except Exception:
            return jsonify(error="Erreur d'exécution", detail=traceback.format_exc()), 500
    except Exception:
        return jsonify(error="Erreur d'exécution", detail=traceback.format_exc()), 500

    elapsed = round(time.perf_counter() - t0, 3)

    # Serialize result
    if isinstance(result, dict):
        payload = result
    elif hasattr(result, "__dict__"):
        payload = result.__dict__
    else:
        payload = {"result": str(result)}

    return jsonify(ok=True, elapsed_s=elapsed, output=payload)


@app.route(_PREFIX + "/api/modules/<module_name>", methods=["PUT"])
def api_save_module(module_name: str):
    """Write description + tags back to the module's MANIFEST.json."""
    import json as _json

    raw, mod_dir = _find_manifest_for(module_name)
    is_endpoint = False
    if raw is None:
        raw, mod_dir = _find_endpoint_for(module_name)
        is_endpoint = raw is not None
    if raw is None:
        return jsonify(error=f"Item '{module_name}' introuvable"), 404

    body = request.get_json(silent=True) or {}
    if "description" in body:
        raw["description"] = str(body["description"])
    if "tags" in body and isinstance(body["tags"], list):
        raw["tags"] = [str(t) for t in body["tags"]]

    # Endpoints don't have MANIFEST.json — can't persist edits
    if is_endpoint:
        return jsonify(ok=False, error="Les endpoints ne supportent pas encore la sauvegarde (pas de MANIFEST.json)"), 400

    manifest_path = mod_dir / "MANIFEST.json"
    try:
        manifest_path.write_text(_json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        return jsonify(error=f"Écriture impossible : {exc}"), 500

    return jsonify(ok=True, saved=str(manifest_path))


# ─── Embedded HTML ────────────────────────────────────────────────────────────
_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EURKAI — Générateur</title>
<style>
:root {
  --bg:       #070710;
  --bg-card:  #0c0c18;
  --bg-input: #0a0a14;
  --border:   #1a1a2e;
  --border-hi:#262640;
  --text:     #e2e2f0;
  --muted:    #56566e;
  --accent:   #7c6bf5;
  --accent2:  #06b6d4;
  --success:  #34d399;
  --error:    #f87171;
  --warn:     #fbbf24;
  --radius:   8px;
  --font-mono:"SF Mono","Fira Code",monospace;
  --font-ui:  -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{
  font-family:var(--font-ui);font-size:14px;line-height:1.6;
  color:var(--text);background:var(--bg);
  background-image:radial-gradient(circle,#1c1c35 1px,transparent 1px);
  background-size:24px 24px;min-height:100vh;
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}

/* ── Header ── */
.header{
  position:sticky;top:0;z-index:100;
  height:52px;display:flex;align-items:center;gap:12px;padding:0 20px;
  background:rgba(7,7,16,.92);backdrop-filter:blur(14px);
  border-bottom:1px solid var(--border);
}
.logo-mark{
  width:26px;height:26px;border-radius:6px;background:var(--accent);
  display:flex;align-items:center;justify-content:center;
  font-size:10px;font-weight:800;color:#fff;letter-spacing:.04em;
}
.logo-text{font-size:14px;font-weight:700;letter-spacing:.02em}
.header-sep{color:var(--muted);font-size:16px;font-weight:200}
.header-sub{font-size:12px;color:var(--muted)}
.header-sp{flex:1}
.pill-status{
  font-size:11px;font-family:var(--font-mono);
  padding:3px 10px;border-radius:10px;
  background:rgba(52,211,153,.12);border:1px solid rgba(52,211,153,.3);
  color:var(--success);display:flex;align-items:center;gap:5px;
}
.pill-status.err{background:rgba(248,113,113,.12);border-color:rgba(248,113,113,.3);color:var(--error)}
.dot{width:6px;height:6px;border-radius:50%;background:currentColor}

/* ── Layout ── */
.layout{max-width:820px;margin:0 auto;padding:28px 20px 60px}

/* ── Card ── */
.card{
  background:var(--bg-card);border:1px solid var(--border);
  border-radius:var(--radius);margin-bottom:16px;overflow:hidden;
}
.card-hd{
  padding:14px 18px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:10px;
}
.card-title{font-size:14px;font-weight:600;letter-spacing:.01em}
.card-body{padding:18px}

/* ── Form controls ── */
label{display:block;font-size:12px;color:var(--muted);margin-bottom:5px;font-weight:500}
.field{margin-bottom:20px}

input[type=text],input[type=number],select,textarea{
  width:100%;padding:9px 12px;
  background:var(--bg-input);border:1px solid var(--border);border-radius:6px;
  color:var(--text);font-size:13px;font-family:var(--font-ui);
  outline:none;transition:border-color .12s;
  -webkit-appearance:none;
}
input[type=text]:focus,input[type=number]:focus,select:focus,textarea:focus{
  border-color:var(--accent);
}
textarea{resize:vertical;min-height:130px;line-height:1.55;font-family:var(--font-ui)}
select{cursor:pointer;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%2356566e' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 10px center;padding-right:30px}

/* ── File drop zone ── */
.drop-zone{
  border:1.5px dashed var(--border-hi);border-radius:6px;
  padding:14px 16px;text-align:center;cursor:pointer;
  color:var(--muted);font-size:12px;
  transition:border-color .12s,background .12s;
  margin-bottom:8px;
}
.drop-zone:hover,.drop-zone.drag-over{
  border-color:var(--accent);background:rgba(124,107,245,.05);color:var(--accent);
}
.drop-zone input{display:none}

/* ── Row layout ── */
.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.row2{display:grid;grid-template-columns:120px 1fr;gap:16px;margin-bottom:12px}
.row3{display:grid;grid-template-columns:100px 1fr 1fr;gap:16px;margin-bottom:12px}
@media(max-width:600px){.row,.row2,.row3{grid-template-columns:1fr}}

/* ── Options toggle ── */
.opts-toggle{
  font-size:12px;color:var(--muted);cursor:pointer;
  display:flex;align-items:center;gap:5px;padding:4px 0;
  background:none;border:none;font-family:var(--font-ui);
  transition:color .12s;
}
.opts-toggle:hover{color:var(--text)}
.opts-toggle svg{transition:transform .2s}
.opts-toggle.open svg{transform:rotate(90deg)}
.opts-body{display:none;padding-top:14px}
.opts-body.open{display:block}

/* ── Checkboxes ── */
.check-row{display:flex;gap:20px;margin-top:4px}
.check-label{display:flex;align-items:center;gap:7px;cursor:pointer;font-size:13px;color:var(--muted)}
.check-label input[type=checkbox]{
  width:15px;height:15px;accent-color:var(--accent);cursor:pointer;
}

/* ── Submit button ── */
.btn-generate{
  width:100%;padding:11px;border-radius:var(--radius);
  background:var(--accent);border:none;color:#fff;
  font-size:14px;font-weight:600;letter-spacing:.02em;
  cursor:pointer;transition:all .15s;margin-top:4px;
  display:flex;align-items:center;justify-content:center;gap:8px;
}
.btn-generate:hover:not(:disabled){background:#6b5ce0;transform:translateY(-1px);box-shadow:0 4px 16px rgba(124,107,245,.4)}
.btn-generate:disabled{opacity:.5;cursor:not-allowed;transform:none;box-shadow:none}

/* ── Status card ── */
.status-label{
  font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;
  display:flex;align-items:center;gap:6px;
}
.status-label.running{color:var(--accent2)}
.status-label.success{color:var(--success)}
.status-label.error  {color:var(--error)}

/* spinner */
.spin{
  width:14px;height:14px;border:2px solid rgba(6,182,212,.3);
  border-top-color:var(--accent2);border-radius:50%;
  animation:spin .7s linear infinite;flex-shrink:0;
}
@keyframes spin{to{transform:rotate(360deg)}}

/* progress bar */
.prog-track{height:3px;background:var(--border);border-radius:2px;margin:10px 0}
.prog-fill{height:100%;border-radius:2px;background:var(--accent);width:0%;transition:width .4s ease}

/* log box */
.log-box{
  background:var(--bg-input);border:1px solid var(--border);border-radius:5px;
  padding:10px 12px;max-height:160px;overflow-y:auto;
  font-family:var(--font-mono);font-size:11px;color:var(--muted);line-height:1.6;
  margin-top:10px;
}
.log-box .log-line{display:block;white-space:pre-wrap}
.log-box .log-line.hi{color:var(--text)}

/* result section */
.result-box{
  background:var(--bg-input);border:1px solid var(--border-hi);border-radius:6px;
  padding:14px 16px;margin-top:14px;
}
.score-big{
  font-size:36px;font-weight:700;font-family:var(--font-mono);
  line-height:1;margin-bottom:2px;
}
.score-sub{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.meta-row{display:flex;gap:20px;flex-wrap:wrap;margin:10px 0}
.meta-item{display:flex;flex-direction:column;gap:1px}
.meta-val{font-size:13px;font-family:var(--font-mono);color:var(--text)}
.meta-lbl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em}
.btn-open{
  display:inline-flex;align-items:center;gap:6px;
  padding:8px 16px;border-radius:6px;
  background:rgba(124,107,245,.14);border:1px solid rgba(124,107,245,.35);
  color:var(--accent);font-size:13px;font-weight:500;cursor:pointer;
  transition:all .12s;text-decoration:none;
}
.btn-open:hover{background:rgba(124,107,245,.22);text-decoration:none}

/* preview accordion */
.variant-acc{border:1px solid var(--border);border-radius:6px;overflow:hidden;margin-top:10px}
.variant-acc summary{
  list-style:none;display:flex;align-items:center;gap:8px;
  padding:9px 14px;cursor:pointer;background:var(--bg-card);
  font-size:12px;font-weight:600;user-select:none;
}
.variant-acc summary::-webkit-details-marker{display:none}
.variant-acc summary .acc-arrow{
  margin-left:auto;font-size:10px;color:var(--muted);transition:transform .18s;
}
.variant-acc[open] summary .acc-arrow{transform:rotate(90deg)}
.variant-acc summary:hover{background:rgba(124,107,245,.07)}
.variant-acc .acc-body{border-top:1px solid var(--border)}
/* preview iframe */
.iframe-wrap{background:#fff;position:relative;}
.iframe-label{
  font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;
  padding:6px 10px;background:var(--bg-card);border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
}
.iframe-wrap iframe{width:100%;height:520px;border:none;display:block}
/* ref image upload */
.ref-drop{
  border:1.5px dashed var(--border-hi);border-radius:6px;
  padding:10px 14px;cursor:pointer;color:var(--muted);font-size:12px;
  display:flex;align-items:center;gap:10px;
  transition:border-color .12s,background .12s;
}
.ref-drop:hover,.ref-drop.drag-over{border-color:var(--accent);background:rgba(124,107,245,.05);color:var(--accent)}
.ref-preview{width:52px;height:52px;border-radius:4px;object-fit:cover;border:1px solid var(--border);flex-shrink:0}
.ref-swatches{display:flex;gap:4px;flex-wrap:wrap;margin-top:4px}
.ref-swatch{width:16px;height:16px;border-radius:3px;border:1px solid rgba(255,255,255,.1)}
/* charter link */
.charter-btn{
  display:inline-flex;align-items:center;gap:6px;
  padding:6px 12px;border-radius:6px;font-size:12px;font-weight:600;
  background:rgba(251,191,36,.12);border:1px solid rgba(251,191,36,.3);
  color:var(--warn);text-decoration:none;margin-top:8px;
}
.charter-btn:hover{background:rgba(251,191,36,.22);text-decoration:none}

/* ── History ── */
.history-list{list-style:none;display:flex;flex-direction:column;gap:0}
.hist-item{
  display:flex;align-items:center;gap:12px;
  padding:10px 18px;border-bottom:1px solid var(--border);
  transition:background .1s;cursor:default;
}
.hist-item:last-child{border-bottom:none}
.hist-item:hover{background:rgba(255,255,255,.02)}
.hist-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.hist-name{font-size:13px;font-weight:500;font-family:var(--font-mono);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hist-score{font-size:12px;font-family:var(--font-mono);color:var(--muted);width:50px;text-align:right}
.hist-time{font-size:11px;color:var(--muted);width:90px;text-align:right;flex-shrink:0}
.hist-link{flex-shrink:0}
.hist-link a{font-size:11px;color:var(--accent);padding:2px 8px;border-radius:4px;border:1px solid rgba(124,107,245,.3);background:rgba(124,107,245,.08)}
.hist-link a:hover{background:rgba(124,107,245,.18);text-decoration:none}
.hist-empty{padding:18px;text-align:center;color:var(--muted);font-size:12px;font-style:italic}

/* ── Scrollbar ── */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border-hi);border-radius:2px}

/* ── Animations ── */
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.fade-in{animation:fadeIn .25s ease both}
</style>
</head>
<body>

<header class="header">
  <div class="logo-mark">EK</div>
  <span class="logo-text">EURKAI</span>
  <span class="header-sep">/</span>
  <span class="header-sub">Générateur</span>
  <div class="header-sp"></div>
  <div id="pipelineBadge"></div>
</header>

<div class="layout">

  <!-- ── Generation form ── -->
  <div class="card" id="formCard">
    <div class="card-hd">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" style="color:var(--accent)">
        <path d="M28,4 L14,26 L24,26 L18,44 L34,22 L24,22 Z" fill="currentColor"/>
        <polyline points="12,6 18,12 12,18" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>
        <line x1="2" y1="12" x2="18" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="square"/>
      </svg>
      <span class="card-title">Nouveau projet</span>
    </div>
    <div class="card-body">
      <form id="genForm" onsubmit="handleSubmit(event)">

        <div class="field">
          <label for="projectName">Nom du projet *</label>
          <input type="text" id="projectName" placeholder="mon-projet-2026" autocomplete="off">
        </div>

        <div class="field">
          <label for="briefText">Brief *</label>
          <!-- file drop zone -->
          <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()"
               ondragover="dragOver(event)" ondragleave="dragLeave(event)" ondrop="dropFile(event)">
            <input type="file" id="fileInput" accept=".md,.txt,.text" onchange="readFile(this)">
            <span id="dropLabel">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" style="display:inline;vertical-align:middle;margin-right:4px"><path d="M12 3v12m0-12L8 7m4-4l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M3 17v2a2 2 0 002 2h14a2 2 0 002-2v-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              Déposer un fichier .md / .txt ou cliquer pour parcourir
            </span>
          </div>
          <textarea id="briefText" placeholder="Distillerie normande premium, calvados artisanal depuis 1887. Clientèle : amateurs et professionnels. Ton : élégant, authentique, terroir." required></textarea>
        </div>

        <div class="field">
          <label>Visuel de référence <span style="font-weight:400;color:var(--muted)">(logo, charte, moodboard — optionnel)</span></label>
          <div class="ref-drop" id="refDrop"
               ondragover="refDragOver(event)" ondragleave="refDragLeave(event)" ondrop="refDropFile(event)"
               onclick="document.getElementById('refFileInput').click()">
            <input type="file" id="refFileInput" accept="image/*" style="display:none" onchange="refReadFile(this)">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" style="flex-shrink:0"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/><circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/><path d="M21 15l-5-5L5 21" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span id="refLabel">Déposer une image ou cliquer pour parcourir</span>
          </div>
          <div id="refSwatches" class="ref-swatches" style="display:none"></div>
        </div>

        <div class="row3">
          <div class="field">
            <label for="nbOptions">Variantes</label>
            <input type="number" id="nbOptions" value="3" min="1" max="5">
          </div>
          <div class="field">
            <label for="charterMode">Charte graphique</label>
            <select id="charterMode">
              <option value="none">Page seulement</option>
              <option value="also">Page + charte</option>
              <option value="only">Charte uniquement</option>
            </select>
          </div>
          <div class="field">
            <label for="seed">Seed</label>
            <input type="number" id="seed" value="42" min="1" max="99999">
          </div>
        </div>
        <div class="row3">
          <div class="field">
            <label for="siteFamily">Style</label>
            <select id="siteFamily">
              <option value="">— auto —</option>
              <option value="editorial_luxury">editorial_luxury</option>
              <option value="brutalist">brutalist</option>
              <option value="tech_minimal">tech_minimal</option>
              <option value="experimental_grid">experimental_grid</option>
              <option value="premium_brand">premium_brand</option>
              <option value="bold_marketing">bold_marketing</option>
            </select>
          </div>
          <div class="field">
            <label for="harmony">Harmonie couleurs</label>
            <select id="harmony" onchange="_applyHarmony()">
              <option value="complementary">complémentaire</option>
              <option value="analogous">analogue</option>
              <option value="triadic">triade</option>
              <option value="monochromatic">monochrome</option>
              <option value="minimal">minimal</option>
              <option value="bw_light">N&amp;B clair</option>
              <option value="bw_dark">N&amp;B sombre</option>
            </select>
          </div>
          <div class="field">
            <label>Pipeline</label>
            <div class="check-row">
              <label class="check-label">
                <input type="checkbox" id="enableCapture" checked>Screenshots
              </label>
              <label class="check-label">
                <input type="checkbox" id="enableAudit" checked>Audit
              </label>
            </div>
          </div>
        </div>

        <button type="submit" class="btn-generate" id="btnGenerate">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none">
            <path d="M28,4 L14,26 L24,26 L18,44 L34,22 L24,22 Z" fill="currentColor"/>
          </svg>
          Générer
        </button>
      </form>
    </div>
  </div>

  <!-- ── Status card (shown while running / after completion) ── -->
  <div class="card fade-in" id="statusCard" style="display:none">
    <div class="card-hd">
      <div class="status-label" id="statusLabel">
        <div class="spin" id="statusSpin"></div>
        <span id="statusText">Génération en cours…</span>
      </div>
      <div class="header-sp"></div>
      <span id="statusTimer" style="font-size:11px;color:var(--muted);font-family:var(--font-mono)"></span>
    </div>
    <div class="card-body">
      <div class="prog-track"><div class="prog-fill" id="progFill"></div></div>
      <div class="log-box" id="logBox"></div>
      <div id="resultBox"></div>
    </div>
  </div>

  <!-- ── History ── -->
  <div class="card">
    <div class="card-hd">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" style="color:var(--muted)">
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5" fill="none"/>
        <polyline points="12,7 12,12 15,14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      </svg>
      <span class="card-title">Historique</span>
      <div class="header-sp"></div>
      <button onclick="loadHistory()" style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:11px">↻ Rafraîchir</button>
    </div>
    <ul class="history-list" id="historyList">
      <li class="hist-empty">Chargement…</li>
    </ul>
  </div>

</div><!-- /layout -->

<script>
/* ── Base URL (set by server for reverse-proxy deployments) ─── */
const API_BASE = (document.currentScript && document.currentScript.dataset.prefix) || window.__API_BASE__ || '';
/* ── State ─────────────────────────────────────────────────── */
let activeJobId  = null;
let pollInterval = null;
let startTime    = null;
let timerInterval= null;
let logCount     = 0;
let refRawColors = [];   // couleurs brutes extraites (hex[])
let refColors    = [];   // alias pour compat
let refCpPalette = null; // cp_palette structuré avec harmonie appliquée

/* ── Init ──────────────────────────────────────────────────── */
(async function init() {
  // Check pipeline health
  try {
    const r = await fetch(API_BASE + '/api/ping');
    const d = await r.json();
    const badge = document.getElementById('pipelineBadge');
    if (d.pipeline_ok) {
      badge.innerHTML = '<div class="pill-status"><div class="dot"></div>Pipeline OK</div>';
    } else {
      badge.innerHTML = '<div class="pill-status err"><div class="dot"></div>Pipeline indisponible</div>';
    }
  } catch(e) {}

  // Resume running job from localStorage
  const saved = localStorage.getItem('eurkai_job');
  if (saved) {
    try {
      const j = JSON.parse(saved);
      if (j.job_id) {
        const r = await fetch(API_BASE + '/api/status/' + j.job_id);
        if (r.ok) {
          const d = await r.json();
          if (d.status === 'running') {
            activeJobId = j.job_id;
            showStatusCard();
            startPolling(j.job_id);
          } else {
            localStorage.removeItem('eurkai_job');
          }
        }
      }
    } catch(e) { localStorage.removeItem('eurkai_job'); }
  }

  loadHistory();
})();

/* ── Form submit ────────────────────────────────────────────── */
async function handleSubmit(e) {
  e.preventDefault();

  const brief = document.getElementById('briefText').value.trim();
  const name  = document.getElementById('projectName').value.trim();
  if (!brief) return;

  const payload = {
    brief,
    project_name:   name,
    seed:           parseInt(document.getElementById('seed').value) || 42,
    site_family:    document.getElementById('siteFamily').value,
    harmony:        document.getElementById('harmony').value,
    enable_capture:  document.getElementById('enableCapture').checked,
    enable_audit:    document.getElementById('enableAudit').checked,
    nb_options:     parseInt(document.getElementById('nbOptions').value) || 3,
    charter_mode:   document.getElementById('charterMode').value,
    cp_palette:     refCpPalette,
  };

  // Disable button
  const btn = document.getElementById('btnGenerate');
  btn.disabled = true;
  btn.innerHTML = '<div class="spin"></div> Démarrage…';

  try {
    const r = await fetch(API_BASE + '/api/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Erreur serveur');

    activeJobId = d.job_id;
    localStorage.setItem('eurkai_job', JSON.stringify({job_id: d.job_id, name}));
    logCount = 0;
    showStatusCard();
    startPolling(d.job_id);

  } catch(err) {
    btn.disabled = false;
    btn.innerHTML = '&#9654; Générer';
    alert('Erreur : ' + err.message);
  }
}

/* ── Status card ────────────────────────────────────────────── */
function showStatusCard() {
  const card = document.getElementById('statusCard');
  card.style.display = 'block';
  document.getElementById('logBox').innerHTML = '';
  document.getElementById('resultBox').innerHTML = '';
  document.getElementById('progFill').style.width = '5%';
  setStatusRunning();
  startTime = Date.now();
  timerInterval = setInterval(updateTimer, 1000);
  card.scrollIntoView({behavior:'smooth', block:'start'});
}

function setStatusRunning() {
  const lbl  = document.getElementById('statusLabel');
  const spin = document.getElementById('statusSpin');
  const text = document.getElementById('statusText');
  lbl.className  = 'status-label running';
  spin.style.display = 'block';
  text.textContent  = 'Génération en cours…';
}

function updateTimer() {
  const s = Math.round((Date.now() - startTime) / 1000);
  document.getElementById('statusTimer').textContent = s + 's';
  // Fake progress animation during run
  const pct = Math.min(90, 5 + s * 1.2);
  document.getElementById('progFill').style.width = pct + '%';
}

/* ── Polling ────────────────────────────────────────────────── */
function startPolling(jobId) {
  stopPolling();
  pollInterval = setInterval(() => pollStatus(jobId), 1500);
}

function stopPolling() {
  if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
  if (timerInterval){ clearInterval(timerInterval); timerInterval = null; }
}

async function pollStatus(jobId) {
  try {
    const r = await fetch(API_BASE + '/api/status/' + jobId);
    if (!r.ok) return;
    const job = await r.json();

    // Update logs
    const box = document.getElementById('logBox');
    const newLines = job.logs.slice(logCount);
    newLines.forEach(line => {
      const el = document.createElement('span');
      el.className = 'log-line' + (line.startsWith('✓') || line.startsWith('●') ? ' hi' : '');
      el.textContent = line;
      box.appendChild(el);
    });
    logCount = job.logs.length;
    box.scrollTop = box.scrollHeight;

    if (job.status !== 'running') {
      stopPolling();
      localStorage.removeItem('eurkai_job');
      showResult(job);
      loadHistory();
      // Re-enable button
      const btn = document.getElementById('btnGenerate');
      btn.disabled = false;
      btn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none"><path d="M5 3l14 9-14 9V3z" fill="currentColor"/></svg> Générer';
    }
  } catch(e) {}
}

/* ── Result display ─────────────────────────────────────────── */
function showResult(job) {
  const lbl  = document.getElementById('statusLabel');
  const spin = document.getElementById('statusSpin');
  const text = document.getElementById('statusText');

  document.getElementById('progFill').style.width = '100%';

  if (job.status === 'success') {
    lbl.className = 'status-label success';
    spin.style.display = 'none';
    text.textContent = 'Génération terminée';
  } else {
    lbl.className = 'status-label error';
    spin.style.display = 'none';
    text.textContent = 'Erreur de génération';
  }

  const score      = job.final_score || 0;
  const scoreColor = score >= 75 ? 'var(--success)' : score >= 50 ? 'var(--warn)' : 'var(--error)';
  const dur        = job.duration_s ? job.duration_s + 's' : '—';
  const urls       = job.output_urls && job.output_urls.length ? job.output_urls
                   : (job.output_url ? [job.output_url] : []);

  let html = `<div class="result-box">`;

  if (job.status === 'success') {
    html += `
      <div style="display:flex;align-items:flex-end;gap:6px;margin-bottom:12px">
        ${score ? `<div class="score-big" style="color:${scoreColor}">${score}</div>
        <div style="padding-bottom:6px"><div style="font-size:16px;color:var(--muted)">/100</div></div>
        <div style="padding-bottom:6px;flex:1"><div class="score-sub">Score lisibilité</div></div>` : ''}
      </div>
      <div class="meta-row">
        <div class="meta-item">
          <span class="meta-val">${dur}</span>
          <span class="meta-lbl">Durée</span>
        </div>
        <div class="meta-item">
          <span class="meta-val">${job.project_name}</span>
          <span class="meta-lbl">Projet</span>
        </div>
        <div class="meta-item">
          <span class="meta-val">${urls.length}</span>
          <span class="meta-lbl">Variante${urls.length > 1 ? 's' : ''}</span>
        </div>
      </div>`;

    const charterUrls = job.charter_urls || [];

    // Charte only — pas de pages
    if (urls.length === 0 && charterUrls.length > 0) {
      charterUrls.forEach((cu, idx) => {
        const lbl = charterUrls.length > 1 ? `Charte ${idx + 1}` : 'Charte graphique';
        html += `<div style="margin-top:8px">
          <a class="charter-btn" href="${cu}" target="_blank">
            ⬇ Charte graphique${charterUrls.length > 1 ? ' ' + (idx + 1) : ''}
          </a>
        </div>`;
      });
    }

    const variantsMeta = job.variants_meta || [];

    urls.forEach((url, idx) => {
      const label   = urls.length > 1 ? `Variante ${idx + 1}` : 'Résultat';
      const accId   = `acc-${idx}`;
      const frmId   = `frm-${idx}`;
      const isFirst = false;   // tous fermés par défaut
      const charterHtml = charterUrls[idx]
        ? `<a class="charter-btn" href="${charterUrls[idx]}" target="_blank">⬇ Charte graphique</a>` : '';

      // Metadata badges from eurkai:meta comment
      const vmeta = variantsMeta[idx] || {};
      const _badge = (txt, col) =>
        `<span style="font-size:10px;padding:1px 7px;border-radius:100px;background:${col}22;color:${col};border:1px solid ${col}44;line-height:1.6;white-space:nowrap">${txt}</span>`;
      let metaBadges = '';
      if (vmeta.archetype)       metaBadges += _badge(vmeta.archetype.replace(/_/g,' '), '#818cf8');
      if (vmeta.hero_type)       metaBadges += _badge(vmeta.hero_type, '#34d399');
      if (vmeta.visual_density)  metaBadges += _badge(vmeta.visual_density, '#fbbf24');
      if (vmeta.decorators_used && vmeta.decorators_used.length)
        metaBadges += _badge(vmeta.decorators_used.join('+'), '#22d3ee');
      const metaRow = metaBadges
        ? `<div style="display:flex;gap:5px;flex-wrap:wrap;padding:6px 14px 0;align-items:center">${metaBadges}</div>` : '';

      html += `
      <details class="variant-acc" id="${accId}" ${isFirst ? 'open' : ''}
               ontoggle="lazyFrame('${frmId}','${url}',this.open)">
        <summary>
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" style="color:var(--accent)"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          ${label}
          <a class="btn-open" href="${url}" target="_blank" onclick="event.stopPropagation()" style="padding:3px 8px;font-size:11px">
            <svg viewBox="0 0 24 24" width="11" height="11" fill="none"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><polyline points="15 3 21 3 21 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><line x1="10" y1="14" x2="21" y2="3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            Ouvrir
          </a>
          <span class="acc-arrow">▶</span>
        </summary>
        ${metaRow}
        <div class="acc-body">
          ${charterHtml}
          <div class="iframe-wrap">
            <div class="iframe-label">
              <span>Aperçu</span>
              <a href="${url}" target="_blank" style="font-size:10px;color:var(--muted)">Plein écran ↗</a>
            </div>
            <iframe id="${frmId}" ${isFirst ? `src="${url}"` : `data-src="${url}"`} sandbox="allow-scripts allow-same-origin"></iframe>
          </div>
        </div>
      </details>`;
    });

  } else {
    html += `<div style="color:var(--error);font-size:13px;font-family:var(--font-mono)">${escHtml(job.error || 'Erreur inconnue')}</div>`;
  }

  html += `</div>`;
  document.getElementById('resultBox').innerHTML = html;
}

/* ── History ────────────────────────────────────────────────── */
async function loadHistory() {
  try {
    const r = await fetch(API_BASE + '/api/history');
    const list = await r.json();
    renderHistory(list);
  } catch(e) {
    document.getElementById('historyList').innerHTML =
      '<li class="hist-empty">Impossible de charger l&#39;historique</li>';
  }
}

function renderHistory(list) {
  const ul = document.getElementById('historyList');
  if (!list.length) {
    ul.innerHTML = '<li class="hist-empty">Aucune g&#233;n&#233;ration pour l&#39;instant.</li>';
    return;
  }
  ul.innerHTML = list.map(h => {
    const isOk    = h.status === 'success';
    const dotClr  = isOk ? 'var(--success)' : 'var(--error)';
    const score   = h.final_score != null ? h.final_score + '/100' : '—';
    const dt      = h.started_at ? h.started_at.slice(0,16).replace('T',' ') : '—';
    const link    = h.output_url
      ? `<a href="${h.output_url}" target="_blank">Ouvrir →</a>`
      : '<span style="color:var(--muted);font-size:11px">—</span>';
    return `<li class="hist-item">
      <div class="hist-dot" style="background:${dotClr}"></div>
      <span class="hist-name" title="${escHtml(h.project_name)}">${escHtml(h.project_name)}</span>
      <span class="hist-score">${score}</span>
      <span class="hist-time">${dt}</span>
      <span class="hist-link">${link}</span>
    </li>`;
  }).join('');
}

/* ── File handling ──────────────────────────────────────────── */
function readFile(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById('briefText').value = e.target.result;
    document.getElementById('dropLabel').textContent = '📄 ' + file.name;
  };
  reader.readAsText(file);
}

function dragOver(e) {
  e.preventDefault();
  document.getElementById('dropZone').classList.add('drag-over');
}
function dragLeave(e) {
  document.getElementById('dropZone').classList.remove('drag-over');
}
function dropFile(e) {
  e.preventDefault();
  document.getElementById('dropZone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    document.getElementById('briefText').value = ev.target.result;
    document.getElementById('dropLabel').textContent = '📄 ' + file.name;
  };
  reader.readAsText(file);
}

/* ── Ref image upload ───────────────────────────────────────── */
function refDragOver(e){e.preventDefault();document.getElementById('refDrop').classList.add('drag-over')}
function refDragLeave(e){document.getElementById('refDrop').classList.remove('drag-over')}
function refDropFile(e){
  e.preventDefault();
  document.getElementById('refDrop').classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f && f.type.startsWith('image/')) _uploadRef(f);
}
function refReadFile(input){
  const f = input.files[0];
  if (f) _uploadRef(f);
}
function _uploadRef(file) {
  const fd = new FormData();
  fd.append('image', file);
  fetch(API_BASE + '/api/upload-ref', {method:'POST', body: fd})
    .then(r => r.json())
    .then(d => {
      if (!d.ok) { alert('Erreur upload : ' + (d.error || '?')); return; }
      refRawColors = d.colors || [];
      refColors    = refRawColors;
      refCpPalette = null; // pas encore dérivée
      // Preview miniature
      const drop = document.getElementById('refDrop');
      drop.innerHTML = `<img class="ref-preview" src="${d.url}">
        <div>
          <div style="font-size:12px;font-weight:600">${escHtml(file.name)}</div>
          <div style="font-size:11px;color:var(--muted);margin-top:2px">${refRawColors.length} couleurs extraites</div>
          <button onclick="clearRef(event)" style="background:none;border:none;color:var(--error);cursor:pointer;font-size:11px;padding:0;margin-top:4px">✕ Retirer</button>
        </div>`;
      _renderExtracted();   // afficher les couleurs brutes
      _applyHarmony();      // dériver et afficher la palette avec l'harmonie en cours
    })
    .catch(e => alert('Erreur : ' + e.message));
}
function _renderExtracted() {
  const sw = document.getElementById('refSwatches');
  if (!refRawColors.length) { sw.style.display = 'none'; return; }
  sw.style.display = 'flex';
  sw.innerHTML =
    `<div style="width:100%;font-size:10px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Couleurs extraites</div>` +
    `<div style="display:flex;gap:6px;flex-wrap:wrap;width:100%;margin-bottom:10px">` +
      refRawColors.map(c =>
        `<div title="${c}" style="width:28px;height:28px;border-radius:4px;background:${c};border:1px solid rgba(255,255,255,.1)"></div>`
      ).join('') +
    `</div>` +
    `<div id="paletteGeneree" style="width:100%"></div>`;
}
function _applyHarmony() {
  if (!refRawColors.length) return;
  const harmony = document.getElementById('harmony').value;
  const harmonyLabel = document.getElementById('harmony').options[document.getElementById('harmony').selectedIndex].text;
  const pg = document.getElementById('paletteGeneree');
  if (pg) pg.innerHTML = `<div style="font-size:10px;color:var(--muted)">Calcul palette ${harmonyLabel}…</div>`;
  fetch(API_BASE + '/api/apply-harmony', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({colors: refRawColors, harmony}),
  })
    .then(r => r.json())
    .then(d => {
      refCpPalette = d.cp_palette || null;
      _renderGeneratedPalette(harmonyLabel);
    })
    .catch(() => {});
}
function _renderGeneratedPalette(harmonyLabel) {
  const pg = document.getElementById('paletteGeneree');
  if (!pg || !refCpPalette) return;
  const labels = {
    primary:'Primaire', secondary:'Secondaire', accent:'Accent',
    background:'Fond', surface:'Surface', text_primary:'Texte',
    text_secondary:'Texte 2', border:'Bordure'
  };
  pg.innerHTML =
    `<div style="font-size:10px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Palette dérivée — ${harmonyLabel}</div>` +
    `<div style="display:flex;gap:8px;flex-wrap:wrap">` +
      Object.entries(refCpPalette).map(([k, c]) =>
        `<div style="display:flex;flex-direction:column;align-items:center;gap:2px">
          <div title="${k}: ${c}" style="width:28px;height:28px;border-radius:4px;background:${c};border:1px solid rgba(255,255,255,.1)"></div>
          <span style="font-size:9px;color:var(--muted);text-align:center;line-height:1.1;max-width:36px">${labels[k]||k}</span>
        </div>`
      ).join('') +
    `</div>`;
}
function clearRef(e) {
  e.stopPropagation();
  refRawColors = [];
  refColors    = [];
  refCpPalette = null;
  const drop = document.getElementById('refDrop');
  drop.innerHTML = `<input type="file" id="refFileInput" accept="image/*" style="display:none" onchange="refReadFile(this)">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" style="flex-shrink:0"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/><circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/><path d="M21 15l-5-5L5 21" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
    <span>Déposer une image ou cliquer pour parcourir</span>`;
  drop.onclick = () => document.getElementById('refFileInput').click();
  const sw = document.getElementById('refSwatches');
  sw.style.display = 'none';
  sw.innerHTML = '';
}

/* ── Options toggle ─────────────────────────────────────────── */
function toggleOpts() {
  const btn  = document.getElementById('optsToggle');
  const body = document.getElementById('optsBody');
  const open = body.classList.toggle('open');
  btn.classList.toggle('open', open);
}

/* ── Lazy iframe loader ─────────────────────────────────────── */
function lazyFrame(frmId, url, isOpen) {
  if (!isOpen) return;
  const f = document.getElementById(frmId);
  if (f && !f.src) f.src = url;
}

/* ── Utils ──────────────────────────────────────────────────── */
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
</body>
</html>"""

# ─── CLI ─────────────────────────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(description="EURKAI Generation UI")
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--debug", action="store_true")
    args = p.parse_args()

    print(f"\n⬡  EURKAI Generator — http://localhost:{args.port}\n")
    if not _PIPELINE_OK:
        print(f"   ⚠  Pipeline non disponible : {_PIPELINE_ERR}")
    else:
        print(f"   ✓  Pipeline OK — output → {OUTPUT_DIR}")
    print()

    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == "__main__":
    main()
