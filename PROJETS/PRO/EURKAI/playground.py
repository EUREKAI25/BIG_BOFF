#!/usr/bin/env python3
"""
Design Playground — EURKAI interactive test interface.

Run:
    pip install flask
    python playground.py
    → Open http://localhost:8765
"""
from __future__ import annotations

import json as _json
import sys
import random
import time as _time
import traceback as _tb
import importlib.util as _ilu
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────

ROOT        = Path(__file__).parent
MODULES_DIR = ROOT / "MODULES"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(MODULES_DIR))
for _mod in sorted(MODULES_DIR.iterdir()):
    if _mod.is_dir() and not _mod.name.startswith(("_", ".")):
        if str(_mod) not in sys.path:
            sys.path.insert(0, str(_mod))


# ── Load design endpoint modules ──────────────────────────────────────────────

def _load_ep(rel: str):
    p    = ROOT / rel
    spec = _ilu.spec_from_file_location(p.stem.replace(".", "_"), p)
    mod  = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_vi_mod  = _load_ep("MODULES/design_endpoints/design.visual_intent.generate.py")
_pal_mod = _load_ep("MODULES/design_endpoints/design.palette.generate.py")

# ── Load visual_coherence_engine directly (immune to sys.modules shim) ────────

_VCE_PY  = ROOT / "MODULES" / "visual_coherence_engine" / "src" / "visual_coherence_engine.py"
_vce_spec = _ilu.spec_from_file_location("_vce_core_pg", _VCE_PY)
_vce_mod  = _ilu.module_from_spec(_vce_spec)
_vce_spec.loader.exec_module(_vce_mod)
_coh_run  = _vce_mod.run

# ── Load design_plan + design_validator ───────────────────────────────────────

_has_plan      = False
_has_validator = False

try:
    from design_plan.src.design_plan import generate_design_plan, DesignPlan
    _has_plan = True
except ImportError:
    try:
        from design_plan import generate_design_plan, DesignPlan  # type: ignore
        _has_plan = True
    except ImportError:
        pass

try:
    from design_validator.src.design_validator import validate_layout
    _has_validator = True
except ImportError:
    try:
        from design_validator import validate_layout  # type: ignore
        _has_validator = True
    except ImportError:
        pass

# ── Load renderer (also sets up sys.path for all modules) ─────────────────────

import generate_brand_charter as _gbc

# ── Flask ──────────────────────────────────────────────────────────────────────

from flask import Flask, request, jsonify, Response

app  = Flask(__name__)
PORT = 8765

SITE_FAMILIES = [
    ("",                      "— Auto-detect —"),
    ("brand_landing",         "Brand Landing"),
    ("editorial_magazine",    "Editorial Magazine"),
    ("studio_portfolio",      "Studio Portfolio"),
    ("product_saas",          "Product SaaS"),
    ("craft_artisan",         "Craft & Artisan"),
    ("ecommerce_catalog",     "E-Commerce Catalog"),
    ("event_campaign",        "Event Campaign"),
    ("institution_manifesto", "Institution Manifesto"),
]

_FAMILY_OPTIONS = "".join(
    f'<option value="{v}">{l}</option>' for v, l in SITE_FAMILIES
)

_SEED_MUTATION_PRIME = 97
_MAX_PLAN_ATTEMPTS   = 5


# ── Pipeline helpers ──────────────────────────────────────────────────────────

def _extract_layout_from_plan(plan) -> dict:
    """Mirror of pipeline.py — DesignPlan → layout dict for design_validator."""
    sections = [
        {
            "type":              s,
            "layout_variant":    s,
            "symmetric":         False,
            "visually_isolated": s == "cta_block",
        }
        for s in plan.section_types
    ]
    global_symmetry = (
        "center" in plan.hero.positioning.lower()
        or "centered" in plan.hero.type.lower()
    )
    return {
        "hero": {
            "type":           plan.hero.type,
            "positioning":    plan.hero.positioning,
            "text_placement": plan.hero.text_placement,
            "media_role":     plan.hero.media_role,
        },
        "sections": sections,
        "structure": {
            "global_symmetry":       global_symmetry,
            "equal_section_heights": False,
            "varying_heights":       True,
            "has_typographic_break": True,
            "density":               plan.composition.density,
            "repeated_layouts":      {},
        },
    }


def _validated_plan(brief: str, seed: int, vi: dict):
    """
    Generate + validate design_plan with seed mutation on failure.
    Mirror of pipeline.py _phase_validate_plan_loop().
    Returns DesignPlan or None.
    """
    if not _has_plan:
        return None

    for attempt in range(_MAX_PLAN_ATTEMPTS):
        current_seed = seed + attempt * _SEED_MUTATION_PRIME
        try:
            plan = generate_design_plan(brief=brief, seed=current_seed, visual_intent=vi)
        except Exception:
            continue

        errors = plan.validate()
        if errors:
            continue

        if _has_validator:
            layout  = _extract_layout_from_plan(plan)
            vresult = validate_layout(plan.to_dict(), layout)
            if not vresult.valid:
                continue

        return plan

    # Fallback — regen with large offset
    try:
        return generate_design_plan(
            brief=brief, seed=seed + 1000, visual_intent=vi
        )
    except Exception:
        return None


def _plan_summary(plan) -> dict | None:
    if plan is None:
        return None
    try:
        return {
            "layout_strategy": plan.layout_strategy,
            "profile":         plan.brief_profile,
            "hero_type":       plan.hero.type,
            "hero_positioning":plan.hero.positioning,
            "density":         plan.composition.density,
            "sections":        plan.section_types,
            "seed":            plan.seed,
        }
    except Exception:
        return None


def _run_pipeline(
    brief:         str,
    site_family:   str,
    name:          str,
    seed:          int,
    full_pipeline: bool = True,
) -> dict:
    ctx = {"name": name, "mode": "auto"}

    # Step 1 — visual_intent
    vi = _vi_mod.run(brief=brief)

    # Step 2 — color_palette
    cp_palette = _pal_mod.run(visual_intent=vi, context=ctx)

    coherence    = None
    plan         = None
    render_seed  = seed

    if full_pipeline:
        # Step 3 — visual_coherence_engine (CASE 2 — palette_drives_image)
        try:
            coherence = _coh_run(
                visual_intent=vi,
                context=ctx,
                palette=cp_palette,
                reference_type="none",
            )
        except Exception:
            coherence = None

        # Step 4 — design_plan (generate + validate)
        plan = _validated_plan(brief, seed, vi)
        if plan is not None:
            render_seed = plan.seed

    # Step 5 — render
    html = _gbc.generate_landing_page(
        project_name=name,
        brief_text=brief,
        dna=None,
        exploration=None,
        preset=None,
        css=None,
        render_seed=render_seed,
        cp_palette=cp_palette,
        site_family=site_family,
    )

    return {
        "html":          html,
        "visual_intent": vi,
        "palette":       cp_palette,
        "coherence":     coherence,
        "plan":          plan,
        "seed":          render_seed,
    }


def _vi_summary(vi: dict) -> dict:
    keys = ["archetype", "mood", "attitude", "energy", "emotion",
            "typography_strategy", "color_strategy", "composition_bias"]
    return {k: vi[k] for k in keys if k in vi}


def _pal_swatches(pal: dict) -> list[dict]:
    slots = [
        ("primary",      "Primary"),
        ("secondary",    "Secondary"),
        ("accent",       "Accent"),
        ("background",   "Background"),
        ("surface",      "Surface"),
        ("text_primary", "Text"),
    ]
    return [{"key": k, "label": l, "hex": pal.get(k, "")}
            for k, l in slots if pal.get(k)]


def _coherence_summary(coherence: dict | None) -> dict | None:
    if not coherence:
        return None
    return {
        "mode":     coherence.get("reference_mode", ""),
        "conflicts": coherence.get("conflicts", []),
        "readability": coherence.get("readability_rules", {}).get(
            "recommended_text_color", ""
        ),
        "overlay_opacity": coherence.get("image_adjustments", {}).get(
            "overlay_opacity", ""
        ),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return Response(_html_page(), mimetype="text/html")


@app.route("/generate", methods=["POST"])
def generate():
    data          = request.json or {}
    brief         = (data.get("brief") or "Brand agency website").strip()
    site_family   = data.get("site_family", "")
    name          = (data.get("name") or "Playground").strip()
    seed          = int(data.get("seed") or random.randint(1, 9999))
    full_pipeline = bool(data.get("full_pipeline", True))

    try:
        result = _run_pipeline(brief, site_family, name, seed, full_pipeline)
        return jsonify({
            "ok":            True,
            "html":          result["html"],
            "visual_intent": _vi_summary(result["visual_intent"]),
            "swatches":      _pal_swatches(result["palette"]),
            "coherence":     _coherence_summary(result["coherence"]),
            "design_plan":   _plan_summary(result["plan"]),
            "seed":          result["seed"],
            "full_pipeline": full_pipeline,
        })
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(exc)}), 500


# ── HTML UI ───────────────────────────────────────────────────────────────────

def _html_page() -> str:
    modules_status = (
        f"design_plan={'✓' if _has_plan else '✗'}  "
        f"design_validator={'✓' if _has_validator else '✗'}  "
        f"coherence_engine=✓"
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Design Playground — EURKAI</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --bg:      #0f0f11;
  --surface: #18181d;
  --border:  #2a2a32;
  --text:    #e8e8f0;
  --muted:   #7a7a90;
  --accent:  #6c63ff;
  --green:   #22c55e;
  --orange:  #f59e0b;
}}
body {{
  font-family: system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  display: flex;
  flex-direction: column;
  font-size: 14px;
  overflow: hidden;
}}
header {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 10px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}}
header h1 {{ font-size: 15px; font-weight: 700; letter-spacing: .04em; }}
header .modules {{ color: var(--muted); font-size: 11px; margin-left: auto; font-family: monospace; }}
.main {{ display: flex; flex: 1; overflow: hidden; }}
/* ── LEFT PANEL ── */
.panel {{
  width: 300px;
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 16px;
  gap: 14px;
}}
label {{ display: block; font-size: 11px; color: var(--muted); text-transform: uppercase;
         letter-spacing: .08em; margin-bottom: 5px; font-weight: 600; }}
input[type=text], input[type=number], textarea, select {{
  width: 100%;
  background: #0f0f11;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  padding: 8px 10px;
  font-size: 13px;
  outline: none;
  font-family: inherit;
  transition: border-color .15s;
}}
input:focus, textarea:focus, select:focus {{ border-color: var(--accent); }}
textarea {{ resize: vertical; min-height: 90px; line-height: 1.5; }}
select option {{ background: #1a1a22; }}
.seed-row {{ display: flex; gap: 6px; align-items: flex-end; }}
.seed-row input {{ flex: 1; }}
.btn {{ border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600;
        padding: 9px 14px; width: 100%; letter-spacing: .02em; transition: opacity .15s; }}
.btn:hover {{ opacity: .85; }}
.btn-primary   {{ background: var(--accent); color: #fff; }}
.btn-secondary {{ background: var(--border); color: var(--text); }}
.btn-tertiary  {{ background: transparent; border: 1px solid var(--border); color: var(--muted); }}
.btn:disabled  {{ opacity: .4; cursor: not-allowed; }}
.divider {{ border: none; border-top: 1px solid var(--border); margin: 2px 0; }}
/* ── Toggle ── */
.toggle-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}}
.toggle-label {{ font-size: 12px; color: var(--text); font-weight: 600; }}
.toggle-sub   {{ font-size: 10px; color: var(--muted); margin-top: 2px; }}
.toggle {{
  position: relative;
  width: 38px;
  height: 21px;
  flex-shrink: 0;
}}
.toggle input {{ opacity: 0; width: 0; height: 0; }}
.toggle-slider {{
  position: absolute;
  inset: 0;
  background: var(--border);
  border-radius: 21px;
  cursor: pointer;
  transition: background .2s;
}}
.toggle-slider::before {{
  content: "";
  position: absolute;
  width: 15px; height: 15px;
  border-radius: 50%;
  background: var(--muted);
  top: 3px; left: 3px;
  transition: transform .2s, background .2s;
}}
.toggle input:checked + .toggle-slider {{ background: #2d2b52; }}
.toggle input:checked + .toggle-slider::before {{ transform: translateX(17px); background: var(--accent); }}
/* ── RIGHT AREA ── */
.output {{
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}}
.output-header {{
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--muted);
  flex-wrap: wrap;
}}
.tag {{
  background: #1e1e28;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px 7px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: .05em;
  white-space: nowrap;
}}
.tag.green  {{ background: #0d2218; border-color: #154a2b; color: var(--green); }}
.tag.orange {{ background: #1e1509; border-color: #3d2d00; color: var(--orange); }}
.tag.blue   {{ background: #0d1228; border-color: #1a2448; color: #7ab2ff; }}
.views {{
  flex: 1;
  display: flex;
  overflow: hidden;
  gap: 1px;
  background: var(--border);
}}
.view-slot {{
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  overflow: hidden;
  position: relative;
  min-width: 0;
}}
.view-slot iframe {{
  flex: 1;
  border: none;
  width: 100%;
  background: #fff;
  min-height: 0;
}}
/* ── META PANEL ── */
.meta {{
  height: 180px;
  flex-shrink: 0;
  background: var(--surface);
  border-top: 1px solid var(--border);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}}
.meta-tabs {{
  display: flex;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}}
.meta-tab {{
  padding: 5px 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: .06em;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color .15s;
  white-space: nowrap;
}}
.meta-tab.active {{ color: var(--text); border-bottom-color: var(--accent); }}
.meta-tab:hover:not(.active) {{ color: var(--text); }}
.meta-panel {{ display: none; flex: 1; overflow-y: auto; padding: 10px 14px; }}
.meta-panel.active {{ display: block; }}
.swatches {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }}
.swatch {{
  width: 26px; height: 26px;
  border-radius: 5px;
  border: 1px solid rgba(255,255,255,.08);
  position: relative; cursor: default; flex-shrink: 0;
}}
.swatch:hover::after {{
  content: attr(data-label) " " attr(data-hex);
  position: absolute;
  bottom: calc(100% + 4px); left: 50%;
  transform: translateX(-50%);
  background: #111; color: #fff;
  font-size: 10px; padding: 3px 6px;
  border-radius: 4px; white-space: nowrap; z-index: 10;
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 4px 10px;
}}
.grid-item {{ font-size: 11px; }}
.grid-key {{ color: var(--muted); text-transform: uppercase; letter-spacing: .05em; font-size: 10px; }}
.grid-val {{ color: var(--text); font-weight: 600; margin-top: 1px;
             white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.plan-sections {{
  display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px;
}}
.plan-section-tag {{
  background: #1a1a24;
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 1px 6px;
  font-size: 10px;
  color: var(--muted);
  font-family: monospace;
}}
.coherence-mode {{
  display: inline-flex; align-items: center; gap: 6px;
  background: #0d1228; border: 1px solid #1a2448;
  border-radius: 5px; padding: 4px 10px;
  font-size: 11px; font-weight: 600; color: #7ab2ff;
  margin-bottom: 8px;
}}
.placeholder {{
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 100%; color: var(--muted); gap: 10px; font-size: 13px;
}}
.placeholder svg {{ opacity: .25; }}
.loader {{
  position: absolute; inset: 0;
  background: rgba(15,15,17,.9);
  display: flex; align-items: center; justify-content: center;
  z-index: 5; font-size: 13px; color: var(--muted); gap: 10px;
  flex-direction: column;
}}
.loader.hidden {{ display: none; }}
.loader-step {{
  font-size: 11px; color: var(--muted); font-family: monospace;
  margin-top: 4px;
}}
.spin {{ animation: spin .8s linear infinite; display: inline-block; }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
.seed-badge {{ font-size: 11px; color: var(--muted); font-family: monospace; }}
.muted {{ color: var(--muted); }}
</style>
</head>
<body>

<header>
  <h1>⬡ Design Playground</h1>
  <span style="color:var(--muted);font-size:12px">EURKAI Full Pipeline Interface</span>
  <a href="/nodes" style="color:var(--accent);font-size:12px;text-decoration:none;padding:4px 10px;
     border:1px solid var(--border);border-radius:5px;letter-spacing:.03em">Nodes →</a>
  <span class="modules">{modules_status}</span>
</header>

<div class="main">

  <!-- LEFT PANEL -->
  <div class="panel">
    <div>
      <label>Nom du projet</label>
      <input type="text" id="name" placeholder="Ex: Vectorstack" value="Playground">
    </div>

    <div>
      <label>Brief</label>
      <textarea id="brief" placeholder="Ex: A premium B2B SaaS platform for data engineers.">A premium B2B SaaS platform for data engineers. Clean, technical, international.</textarea>
    </div>

    <div>
      <label>Famille de site</label>
      <select id="site_family">
        {_FAMILY_OPTIONS}
      </select>
    </div>

    <div>
      <label>Seed</label>
      <div class="seed-row">
        <input type="number" id="seed" min="1" max="99999" placeholder="Random">
        <button class="btn btn-secondary" style="width:auto;padding:9px 10px"
                onclick="randomSeed()" title="Nouveau seed aléatoire">⟳</button>
      </div>
    </div>

    <div style="background:#111118;border:1px solid var(--border);border-radius:8px;padding:10px 12px">
      <div class="toggle-row">
        <div>
          <div class="toggle-label">Full Pipeline</div>
          <div class="toggle-sub">vi → palette → coherence → plan → render</div>
        </div>
        <label class="toggle">
          <input type="checkbox" id="full_pipeline" checked>
          <span class="toggle-slider"></span>
        </label>
      </div>
    </div>

    <hr class="divider">

    <button class="btn btn-primary"    id="btn-generate" onclick="generate()">▶ Générer</button>
    <button class="btn btn-secondary"  id="btn-regen"    onclick="regenerate()" disabled>⟳ Regénérer</button>
    <button class="btn btn-tertiary"   id="btn-var3"     onclick="variation3()" disabled>⊞ Variation ×3</button>
  </div>

  <!-- RIGHT OUTPUT -->
  <div class="output">
    <div class="output-header" id="output-header">
      <span id="status-text">Prêt — remplissez le brief et cliquez Générer</span>
    </div>

    <div class="views" id="views">
      <div class="view-slot" id="slot-0">
        <div class="placeholder">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
          </svg>
          <span>La page générée apparaîtra ici</span>
        </div>
        <div class="loader hidden" id="loader-0">
          <span class="spin" style="font-size:22px">⟳</span>
          <span id="loader-step-0" class="loader-step">Initialisation…</span>
        </div>
      </div>
    </div>
  </div>

</div>

<script>
let _lastSeed = null;

const PIPELINE_STEPS = [
  'visual_intent…',
  'color_palette…',
  'coherence_engine…',
  'design_plan + validation…',
  'render…',
];

function randomSeed() {{
  document.getElementById('seed').value = Math.floor(Math.random() * 99999) + 1;
}}

function getSeed() {{
  const v = parseInt(document.getElementById('seed').value);
  return isNaN(v) ? Math.floor(Math.random() * 99999) + 1 : v;
}}

function isFullPipeline() {{
  return document.getElementById('full_pipeline').checked;
}}

function animateSteps(loaderStepEl, full) {{
  const steps = full ? PIPELINE_STEPS : ['visual_intent…', 'color_palette…', 'render…'];
  let i = 0;
  const iv = setInterval(() => {{
    if (!loaderStepEl || !document.body.contains(loaderStepEl)) {{ clearInterval(iv); return; }}
    loaderStepEl.textContent = steps[i % steps.length];
    i++;
  }}, 800);
  return iv;
}}

async function generate(seedOverride) {{
  const brief       = document.getElementById('brief').value.trim() || 'Agency website';
  const name        = document.getElementById('name').value.trim() || 'Playground';
  const site_family = document.getElementById('site_family').value;
  const seed        = seedOverride ?? getSeed();
  const full        = isFullPipeline();

  _lastSeed = seed;
  document.getElementById('seed').value = seed;

  setViews(1);
  setLoading(true, [0]);
  setStatus('Génération pipeline…', seed);

  const stepEl = document.getElementById('loader-step-0');
  const iv = animateSteps(stepEl, full);

  try {{
    const res  = await fetch('/generate', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ brief, name, site_family, seed, full_pipeline: full }}),
    }});
    const data = await res.json();
    clearInterval(iv);
    if (!data.ok) throw new Error(data.error || 'Erreur inconnue');

    renderSlot(0, data);
    setStatus('OK', data.seed, data.visual_intent?.archetype,
              data.design_plan?.layout_strategy, data.full_pipeline);
    document.getElementById('btn-regen').disabled = false;
    document.getElementById('btn-var3').disabled  = false;
  }} catch(e) {{
    clearInterval(iv);
    setError(0, e.message);
    setStatus('Erreur: ' + e.message);
  }}
  setLoading(false, [0]);
}}

async function regenerate() {{
  await generate(Math.floor(Math.random() * 99999) + 1);
}}

async function variation3() {{
  const brief       = document.getElementById('brief').value.trim() || 'Agency website';
  const name        = document.getElementById('name').value.trim() || 'Playground';
  const site_family = document.getElementById('site_family').value;
  const full        = isFullPipeline();
  const base        = getSeed();
  const seeds       = [base, base + 111, base + 222];

  setViews(3);
  setLoading(true, [0,1,2]);
  setStatus('Génération ×3…', base);

  const intervals = seeds.map((seed, i) => {{
    const stepEl = document.getElementById('loader-step-' + i);
    return animateSteps(stepEl, full);
  }});

  await Promise.all(seeds.map(async (seed, i) => {{
    try {{
      const res  = await fetch('/generate', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ brief, name, site_family, seed, full_pipeline: full }}),
      }});
      const data = await res.json();
      clearInterval(intervals[i]);
      if (!data.ok) throw new Error(data.error || 'Erreur');
      renderSlot(i, data);
    }} catch(e) {{
      clearInterval(intervals[i]);
      setError(i, e.message);
    }}
    setLoading(false, [i]);
  }}));

  setStatus('×3 variantes générées', base);
  document.getElementById('btn-regen').disabled = false;
  document.getElementById('btn-var3').disabled  = false;
}}

// ── DOM helpers ───────────────────────────────────────────────────────────────

function setViews(n) {{
  const views = document.getElementById('views');
  views.innerHTML = '';
  for (let i = 0; i < n; i++) {{
    views.innerHTML += `
      <div class="view-slot" id="slot-${{i}}">
        <div class="placeholder"><span>Chargement…</span></div>
        <div class="loader" id="loader-${{i}}">
          <span class="spin" style="font-size:22px">⟳</span>
          <span id="loader-step-${{i}}" class="loader-step">Initialisation…</span>
        </div>
      </div>`;
  }}
}}

function setLoading(show, slots) {{
  slots.forEach(i => {{
    const el = document.getElementById('loader-' + i);
    if (el) el.classList.toggle('hidden', !show);
  }});
  ['btn-generate','btn-regen','btn-var3'].forEach(id => {{
    document.getElementById(id).disabled = show;
  }});
}}

function renderSlot(i, data) {{
  const slot = document.getElementById('slot-' + i);
  if (!slot) return;

  const ifr = document.createElement('iframe');
  ifr.srcdoc = data.html;

  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.innerHTML = buildMeta(data);

  slot.innerHTML = '';
  slot.appendChild(ifr);
  slot.appendChild(meta);

  // Activate first tab
  const firstTab = meta.querySelector('.meta-tab');
  if (firstTab) activateTab(meta, firstTab.dataset.tab);
}}

function activateTab(container, tab) {{
  container.querySelectorAll('.meta-tab').forEach(t =>
    t.classList.toggle('active', t.dataset.tab === tab));
  container.querySelectorAll('.meta-panel').forEach(p =>
    p.classList.toggle('active', p.dataset.tab === tab));
}}

function buildMeta(data) {{
  const tabs    = [];
  const panels  = [];

  // ── Tab: Palette ──────────────────────────────────────────────────────────
  if (data.swatches && data.swatches.length) {{
    tabs.push(`<div class="meta-tab" data-tab="palette" onclick="activateTab(this.closest('.meta'), 'palette')">Palette</div>`);
    let p = '<div class="swatches">';
    data.swatches.forEach(sw => {{
      p += `<div class="swatch" style="background:${{sw.hex}}" data-label="${{sw.label}}" data-hex="${{sw.hex}}"></div>`;
    }});
    p += '</div>';
    panels.push(`<div class="meta-panel" data-tab="palette">${{p}}</div>`);
  }}

  // ── Tab: Visual Intent ────────────────────────────────────────────────────
  if (data.visual_intent && Object.keys(data.visual_intent).length) {{
    tabs.push(`<div class="meta-tab" data-tab="vi" onclick="activateTab(this.closest('.meta'), 'vi')">Visual Intent</div>`);
    let p = '<div class="grid">';
    for (const [k, v] of Object.entries(data.visual_intent)) {{
      const vStr = typeof v === 'object' ? JSON.stringify(v) : String(v);
      p += `<div class="grid-item">
        <div class="grid-key">${{k}}</div>
        <div class="grid-val" title="${{vStr}}">${{vStr}}</div>
      </div>`;
    }}
    p += '</div>';
    panels.push(`<div class="meta-panel" data-tab="vi">${{p}}</div>`);
  }}

  // ── Tab: Design Plan ──────────────────────────────────────────────────────
  if (data.design_plan) {{
    const dp = data.design_plan;
    tabs.push(`<div class="meta-tab" data-tab="plan" onclick="activateTab(this.closest('.meta'), 'plan')">Design Plan</div>`);
    let p = '<div class="grid">';
    const planFields = {{
      layout: dp.layout_strategy,
      profile: dp.profile,
      hero: dp.hero_type,
      positioning: dp.hero_positioning,
      density: dp.density,
      seed: dp.seed,
    }};
    for (const [k, v] of Object.entries(planFields)) {{
      if (v !== undefined && v !== null)
        p += `<div class="grid-item"><div class="grid-key">${{k}}</div><div class="grid-val">${{v}}</div></div>`;
    }}
    p += '</div>';
    if (dp.sections && dp.sections.length) {{
      p += '<div class="plan-sections">';
      dp.sections.forEach(s => {{ p += `<span class="plan-section-tag">${{s}}</span>`; }});
      p += '</div>';
    }}
    panels.push(`<div class="meta-panel" data-tab="plan">${{p}}</div>`);
  }}

  // ── Tab: Coherence ────────────────────────────────────────────────────────
  if (data.coherence) {{
    const c = data.coherence;
    tabs.push(`<div class="meta-tab" data-tab="coh" onclick="activateTab(this.closest('.meta'), 'coh')">Coherence</div>`);
    let p = `<div class="coherence-mode">⬡ ${{c.mode || '—'}}</div>`;
    p += '<div class="grid">';
    if (c.readability)      p += `<div class="grid-item"><div class="grid-key">text color</div><div class="grid-val">${{c.readability}}</div></div>`;
    if (c.overlay_opacity)  p += `<div class="grid-item"><div class="grid-key">overlay opacity</div><div class="grid-val">${{c.overlay_opacity}}</div></div>`;
    p += '</div>';
    if (c.conflicts && c.conflicts.length) {{
      p += `<div style="margin-top:6px;font-size:11px;color:#f87171">⚠ ${{c.conflicts.join(', ')}}</div>`;
    }}
    panels.push(`<div class="meta-panel" data-tab="coh">${{p}}</div>`);
  }}

  if (!tabs.length) return '<div style="padding:12px;color:var(--muted);font-size:12px">Aucune métadonnée disponible.</div>';

  return `
    <div class="meta-tabs">${{tabs.join('')}}</div>
    ${{panels.join('')}}
  `;
}}

function setError(i, msg) {{
  const slot = document.getElementById('slot-' + i);
  if (slot) slot.innerHTML = `<div class="placeholder" style="color:#ff6b6b">
    <span>⚠ Erreur</span>
    <span style="font-size:11px;max-width:280px;text-align:center;word-break:break-word">${{msg}}</span>
  </div>`;
}}

function setStatus(msg, seed, archetype, layout, full) {{
  let html = `<span id="status-text">${{msg}}</span>`;
  if (seed)      html += ` <span class="seed-badge">seed:${{seed}}</span>`;
  if (archetype) html += ` <span class="tag green">${{archetype}}</span>`;
  if (layout)    html += ` <span class="tag blue">${{layout}}</span>`;
  if (full === true)  html += ` <span class="tag orange">full pipeline</span>`;
  document.getElementById('output-header').innerHTML = html;
}}
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# NODES SYSTEM — catalog, per-node debug pages, universal runner
# ═══════════════════════════════════════════════════════════════════════════════

_CATALOG_PATH = ROOT / "MODULES" / "design_catalog" / "design_catalog.json"
_EP_DIR       = ROOT / "MODULES" / "design_endpoints"
_SC_DIR       = ROOT / "MODULES" / "design_scenarios"

# Endpoints that require external deps (Playwright / Anthropic API key)
_EP_EXTERNAL  = {"design.capture.page", "design.audit.page"}


def _load_node_module(name: str):
    """Load an endpoint or scenario module by its dotted name."""
    for base_dir in (_EP_DIR, _SC_DIR):
        p = base_dir / f"{name}.py"
        if p.exists():
            spec = _ilu.spec_from_file_location(
                name.replace(".", "_") + "_dyn", p)
            mod = _ilu.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                return mod
            except Exception:
                return None
    return None


def _scenario_steps(name: str) -> list[dict]:
    try:
        mod = _load_node_module(name)
        if mod and hasattr(mod, "STEPS"):
            return sorted(mod.STEPS, key=lambda s: s.get("order", 0))
    except Exception:
        pass
    return []


def _load_catalog_augmented() -> list[dict]:
    """Load design_catalog.json and augment every entry with UI-required fields."""
    try:
        raw = _json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
        entries = list(raw.get("entries", []))
    except Exception:
        entries = []

    # Build belongs_to_pipeline map (endpoint → list of scenario names)
    belongs: dict[str, list[str]] = {}
    for e in entries:
        if e.get("type") == "scenario":
            for step in _scenario_steps(e["name"]):
                ep = step.get("endpoint", "")
                if ep:
                    belongs.setdefault(ep, []).append(e["name"])

    for e in entries:
        name      = e.get("name", "")
        item_type = e.get("type", "endpoint")
        e["item_type"] = item_type

        inputs   = e.get("inputs", {})
        required = [k for k, v in inputs.items() if v.get("required")]
        optional = [k for k, v in inputs.items() if not v.get("required")]
        e["input_types_summary"] = {
            "required": required, "optional": optional, "count": len(inputs),
        }
        e["playground_enabled"] = name not in _EP_EXTERNAL
        e.setdefault("status", "stable")
        e.setdefault("tags", list(e.get("dependencies", [])))
        e["belongs_to_pipeline"] = belongs.get(name, [])

        # CLI example
        req_pairs = ", ".join(f'{k}="..."' for k in required[:3])
        if item_type == "endpoint":
            slug = name.replace(".", "_")
            e["cli_example"] = (
                f"from MODULES.design_endpoints.{name} import run\n"
                f"result = run({req_pairs})"
            )
        else:
            e["cli_example"] = (
                f"from MODULES.design_scenarios.{name} import run\n"
                f"result = run({req_pairs})"
            )

        # STEPS for scenarios
        if item_type == "scenario":
            e["steps"] = _scenario_steps(name)
        else:
            e["steps"] = []

    return entries


def _safe_serialize(obj):
    """Recursively convert any object to JSON-safe primitives."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_serialize(i) for i in obj]
    try:
        from dataclasses import asdict as _asdict, is_dataclass
        if is_dataclass(obj):
            return _safe_serialize(_asdict(obj))
    except Exception:
        pass
    if hasattr(obj, "to_dict"):
        return _safe_serialize(obj.to_dict())
    if hasattr(obj, "__dict__"):
        return _safe_serialize(vars(obj))
    return str(obj)


# ── New routes ────────────────────────────────────────────────────────────────

@app.route("/nodes")
def nodes_page():
    catalog = _load_catalog_augmented()
    return Response(_nodes_list_html(catalog), mimetype="text/html")


@app.route("/node/<path:name>")
def node_detail(name: str):
    catalog = {e["name"]: e for e in _load_catalog_augmented()}
    entry   = catalog.get(name)
    if not entry:
        return f"<pre>Node '{name}' not found in catalog.</pre>", 404
    return Response(_node_page_html(entry), mimetype="text/html")


@app.route("/api/run/<path:name>", methods=["POST"])
def api_run(name: str):
    data = request.json or {}
    mod  = _load_node_module(name)
    if not mod or not hasattr(mod, "run"):
        return jsonify({"ok": False, "error": f"'{name}' not found or no run()"}), 404

    catalog = {e["name"]: e for e in _load_catalog_augmented()}
    schema  = catalog.get(name, {}).get("inputs", {})

    kwargs: dict = {}
    for k, meta in schema.items():
        if k not in data or data[k] == "" or data[k] is None:
            continue
        val      = data[k]
        type_str = meta.get("type", "str")
        if "int" in type_str and not isinstance(val, int):
            try: val = int(val)
            except Exception: pass
        elif "bool" in type_str and not isinstance(val, bool):
            val = str(val).lower() in ("true", "1", "yes")
        elif "dict" in type_str and isinstance(val, str):
            try: val = _json.loads(val)
            except Exception: pass
        elif "list" in type_str and isinstance(val, str):
            try: val = _json.loads(val)
            except Exception: pass
        kwargs[k] = val

    t0 = _time.time()
    try:
        result  = mod.run(**kwargs)
        elapsed = round(_time.time() - t0, 3)
        return jsonify({
            "ok":        True,
            "result":    _safe_serialize(result),
            "elapsed_s": elapsed,
        })
    except Exception as exc:
        elapsed = round(_time.time() - t0, 3)
        return jsonify({
            "ok":        False,
            "error":     str(exc),
            "traceback": _tb.format_exc().strip(),
            "elapsed_s": elapsed,
        }), 500


# ── Page builders ─────────────────────────────────────────────────────────────

_NODE_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f0f11;--surface:#18181d;--border:#2a2a32;
  --text:#e8e8f0;--muted:#7a7a90;
  --accent:#6c63ff;--green:#22c55e;--orange:#f59e0b;--red:#f87171;
  --radius:6px;
}
body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);
     font-size:14px;line-height:1.5;min-height:100vh}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
code,pre{font-family:ui-monospace,monospace}
.hdr{background:var(--surface);border-bottom:1px solid var(--border);
     padding:10px 20px;display:flex;align-items:center;gap:12px;font-size:13px}
.hdr-title{font-size:15px;font-weight:700;letter-spacing:.04em}
.breadcrumb{color:var(--muted);font-size:12px}
.page{max-width:980px;margin:0 auto;padding:24px 20px;display:flex;flex-direction:column;gap:20px}
/* ── Section blocks ── */
.section{background:var(--surface);border:1px solid var(--border);border-radius:8px;overflow:hidden}
.section-hd{padding:10px 16px;border-bottom:1px solid var(--border);
            display:flex;align-items:center;justify-content:space-between}
.section-title{font-size:12px;font-weight:700;text-transform:uppercase;
               letter-spacing:.1em;color:var(--muted)}
.section-body{padding:16px}
/* ── Badges / tags ── */
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;
       font-weight:600;letter-spacing:.04em}
.badge-ep{background:#1a2248;border:1px solid #2a3560;color:#7ab2ff}
.badge-sc{background:#182d20;border:1px solid #254836;color:#34d399}
.badge-ext{background:#2d1f0a;border:1px solid #4a3210;color:var(--orange)}
.badge-ok{background:#0d2218;border:1px solid #154a2b;color:var(--green)}
.tag{display:inline-block;padding:1px 7px;border-radius:3px;font-size:11px;
     background:#1e1e28;border:1px solid var(--border);color:var(--muted);font-family:monospace}
/* ── Meta grid ── */
.meta-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px 16px}
.meta-item .meta-key{font-size:10px;text-transform:uppercase;letter-spacing:.08em;
                     color:var(--muted);font-weight:600}
.meta-item .meta-val{font-size:13px;color:var(--text);font-weight:600;margin-top:2px}
/* ── CLI block ── */
.cli-block{background:#0a0a0e;border:1px solid var(--border);border-radius:6px;
           padding:10px 14px;font-family:monospace;font-size:12px;color:#a8a8c8;
           white-space:pre;overflow-x:auto;position:relative}
.copy-btn{cursor:pointer;font-size:11px;padding:3px 9px;border-radius:4px;
          background:var(--border);color:var(--text);border:none;
          letter-spacing:.03em;transition:opacity .15s}
.copy-btn:hover{opacity:.75}
/* ── Pipeline chain ── */
.chain{display:flex;flex-direction:column;gap:2px}
.chain-step{display:flex;align-items:center;gap:8px;font-size:12px;font-family:monospace}
.chain-arrow{color:var(--muted);font-size:11px}
.chain-name{color:var(--accent)}
.chain-note{color:var(--muted);font-size:11px}
/* ── Inputs form ── */
.inputs-grid{display:flex;flex-direction:column;gap:10px}
.field-row{display:flex;flex-direction:column;gap:4px}
.field-label{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;
             color:var(--muted);display:flex;align-items:center;gap:6px}
.req-mark{color:var(--red);font-size:12px}
.field-type{font-size:10px;color:var(--muted);font-family:monospace;margin-left:auto}
.field-desc{font-size:11px;color:var(--muted);margin-top:1px}
input[type=text],input[type=number],textarea,select{
  width:100%;background:#0f0f11;border:1px solid var(--border);border-radius:var(--radius);
  color:var(--text);padding:7px 10px;font-size:13px;outline:none;font-family:inherit}
input:focus,textarea:focus,select:focus{border-color:var(--accent)}
textarea{resize:vertical;min-height:72px;line-height:1.5;font-family:monospace;font-size:12px}
.field-note{font-size:10px;color:var(--muted);margin-top:2px;font-family:monospace}
/* ── Run zone ── */
.run-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.btn-run{background:var(--accent);color:#fff;border:none;border-radius:var(--radius);
         padding:9px 20px;font-size:13px;font-weight:700;cursor:pointer;
         letter-spacing:.03em;transition:opacity .15s}
.btn-run:hover{opacity:.85}
.btn-run:disabled{opacity:.4;cursor:not-allowed}
.elapsed{font-size:12px;color:var(--muted);font-family:monospace}
.run-status{font-size:12px}
.run-status.ok{color:var(--green)}
.run-status.err{color:var(--red)}
/* ── Outputs ── */
.out-block{border:1px solid var(--border);border-radius:6px;overflow:hidden;margin-bottom:10px}
.out-hd{padding:7px 12px;background:#0f0f11;border-bottom:1px solid var(--border);
        display:flex;align-items:center;gap:8px}
.out-key{font-family:monospace;font-size:12px;font-weight:700;color:var(--text)}
.out-type{font-size:10px;color:var(--muted);font-family:monospace}
.out-desc{font-size:11px;color:var(--muted);margin-left:auto;max-width:300px;
          overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.out-body{padding:12px}
/* ── Palette swatches ── */
.palette-grid{display:flex;flex-direction:column;gap:6px}
.pal-row{display:flex;align-items:center;gap:10px}
.pal-swatch{width:36px;height:36px;border-radius:6px;border:1px solid rgba(255,255,255,.1);flex-shrink:0}
.pal-info{font-size:12px}
.pal-key{font-weight:700;color:var(--text)}
.pal-hex{color:var(--muted);font-family:monospace;font-size:11px}
/* ── HTML preview ── */
.html-preview{background:#fff;border-radius:4px;overflow:hidden;position:relative}
.html-preview iframe{width:100%;height:340px;border:none;display:block}
.view-tabs{display:flex;gap:0;margin-bottom:8px}
.view-tab{padding:4px 12px;font-size:11px;font-weight:600;cursor:pointer;
          border:1px solid var(--border);color:var(--muted);background:transparent;
          transition:all .1s}
.view-tab:first-child{border-radius:4px 0 0 4px}
.view-tab:last-child{border-radius:0 4px 4px 0;margin-left:-1px}
.view-tab.active{background:var(--accent);border-color:var(--accent);color:#fff}
/* ── JSON view ── */
.json-view{background:#0a0a0e;border:1px solid var(--border);border-radius:6px;
           padding:12px;font-family:monospace;font-size:11px;color:#a8a8c8;
           max-height:280px;overflow:auto;white-space:pre-wrap;word-break:break-all}
/* ── List/table view ── */
.list-view{display:flex;flex-direction:column;gap:4px;max-height:240px;overflow-y:auto}
.list-item{background:#0a0a0e;border-radius:4px;padding:6px 10px;font-size:11px;
           font-family:monospace;color:#a8a8c8}
.show-all-btn{font-size:11px;color:var(--accent);cursor:pointer;
              padding:4px 0;background:none;border:none;text-align:left}
/* ── Error display ── */
.err-box{background:#1a0808;border:1px solid #4a1010;border-radius:6px;
         padding:12px;color:var(--red);font-size:12px;font-family:monospace;
         white-space:pre-wrap;max-height:300px;overflow:auto}
"""


def _nodes_list_html(catalog: list[dict]) -> str:
    endpoints = [e for e in catalog if e["item_type"] == "endpoint"]
    scenarios = [e for e in catalog if e["item_type"] == "scenario"]

    def _row(e: dict) -> str:
        name   = e["name"]
        goal   = e.get("goal", "")
        deps   = ", ".join(e.get("dependencies", []))
        badge  = "badge-ep" if e["item_type"] == "endpoint" else "badge-sc"
        btext  = "endpoint" if e["item_type"] == "endpoint" else "scenario"
        pg_ok  = e.get("playground_enabled", True)
        pg_tag = ('<span class="badge badge-ok">runnable</span>' if pg_ok
                  else '<span class="badge badge-ext">external deps</span>')
        req    = ", ".join(e["input_types_summary"]["required"][:4])
        return f"""
        <tr style="border-bottom:1px solid var(--border)">
          <td style="padding:10px 14px">
            <a href="/node/{name}" style="font-weight:700;font-family:monospace;
               font-size:12px">{name}</a>
            <div style="font-size:11px;color:var(--muted);margin-top:3px">{goal}</div>
          </td>
          <td style="padding:10px 8px;white-space:nowrap">
            <span class="badge {badge}">{btext}</span>
          </td>
          <td style="padding:10px 8px">{pg_tag}</td>
          <td style="padding:10px 8px;font-size:11px;color:var(--muted);font-family:monospace">
            {req or "—"}
          </td>
          <td style="padding:10px 8px;font-size:11px;color:var(--muted)">{deps}</td>
        </tr>"""

    ep_rows = "".join(_row(e) for e in endpoints)
    sc_rows = "".join(_row(e) for e in scenarios)

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8">
<title>Nodes — EURKAI</title>
<style>
{_NODE_CSS}
body{{padding:0}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:7px 8px;font-size:10px;text-transform:uppercase;
    letter-spacing:.08em;color:var(--muted);border-bottom:1px solid var(--border)}}
tr:hover td{{background:rgba(108,99,255,.04)}}
</style></head><body>
<div class="hdr">
  <a href="/" style="color:var(--muted);font-size:12px">← Playground</a>
  <span class="hdr-title">⬡ Nodes</span>
  <span style="font-size:12px;color:var(--muted)">{len(catalog)} entrées — {len(endpoints)} endpoints · {len(scenarios)} scenarios</span>
</div>
<div class="page">
  <div class="section">
    <div class="section-hd">
      <span class="section-title">Endpoints</span>
      <span style="font-size:11px;color:var(--muted)">{len(endpoints)} modules atomiques</span>
    </div>
    <table>
      <thead><tr>
        <th>Nom</th><th>Type</th><th>Status</th><th>Inputs requis</th><th>Dépendances</th>
      </tr></thead>
      <tbody>{ep_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <div class="section-hd">
      <span class="section-title">Scenarios</span>
      <span style="font-size:11px;color:var(--muted)">{len(scenarios)} pipelines orchestrés</span>
    </div>
    <table>
      <thead><tr>
        <th>Nom</th><th>Type</th><th>Status</th><th>Inputs requis</th><th>Dépendances</th>
      </tr></thead>
      <tbody>{sc_rows}</tbody>
    </table>
  </div>
</div>
</body></html>"""


def _build_input_field(k: str, meta: dict) -> str:
    """Return HTML for a single input field based on its type."""
    type_str = meta.get("type", "str")
    desc     = meta.get("description", "")
    required = meta.get("required", False)
    req_mark = '<span class="req-mark">*</span>' if required else ""
    label    = f"""<div class="field-label">{k}{req_mark}
                   <span class="field-type">{type_str}</span></div>"""
    note     = f'<div class="field-desc">{desc}</div>' if desc else ""

    if "bool" in type_str:
        field = (f'<select id="f_{k}" name="{k}">'
                 f'<option value="">— (optionnel)</option>'
                 f'<option value="true">true</option>'
                 f'<option value="false">false</option></select>')
    elif "int" in type_str:
        field = f'<input type="number" id="f_{k}" name="{k}" placeholder="ex: 42">'
    elif "dict" in type_str or "list" in type_str:
        placeholder = '{"key": "value"}' if "dict" in type_str else '["item1", "item2"]'
        field = (f'<textarea id="f_{k}" name="{k}" rows="3" '
                 f'placeholder="{placeholder}" style="font-family:monospace;font-size:11px">'
                 f'</textarea>')
        note += f'<div class="field-note">JSON {type_str.split("|")[0]}</div>'
    else:
        field = f'<input type="text" id="f_{k}" name="{k}" placeholder="{desc[:60]}">'

    return f'<div class="field-row">{label}{field}{note}</div>'


def _node_page_html(entry: dict) -> str:
    name       = entry["name"]
    item_type  = entry["item_type"]
    goal       = entry.get("goal", "")
    mission    = entry.get("mission", "")
    deps       = entry.get("dependencies", [])
    tags       = entry.get("tags", [])
    status     = entry.get("status", "stable")
    pg_enabled = entry.get("playground_enabled", True)
    cli        = entry.get("cli_example", "")
    steps      = entry.get("steps", [])
    belongs    = entry.get("belongs_to_pipeline", [])
    inputs     = entry.get("inputs", {})
    outputs    = entry.get("outputs", {})
    inp_sum    = entry.get("input_types_summary", {})

    # ── A. Metadata section ────────────────────────────────────────────────────
    badge_cls = "badge-ep" if item_type == "endpoint" else "badge-sc"
    badge_txt = item_type
    pg_badge  = ('<span class="badge badge-ok">playground enabled</span>' if pg_enabled
                 else '<span class="badge badge-ext">requires external deps</span>')

    tags_html = " ".join(f'<span class="tag">{t}</span>' for t in (tags or deps))
    belongs_html = (" ".join(
        f'<a href="/node/{s}" class="tag" style="color:var(--accent)">{s}</a>'
        for s in belongs) or '<span style="color:var(--muted);font-size:11px">—</span>')

    meta_section = f"""
    <div class="section">
      <div class="section-hd">
        <span class="section-title">A. Metadata</span>
        <div style="display:flex;gap:6px;align-items:center">
          <span class="badge {badge_cls}">{badge_txt}</span>
          {pg_badge}
          <span class="badge" style="background:#1a1a22;border:1px solid var(--border);
            color:var(--muted)">{status}</span>
        </div>
      </div>
      <div class="section-body">
        <div class="meta-grid" style="margin-bottom:12px">
          <div class="meta-item">
            <div class="meta-key">name</div>
            <div class="meta-val" style="font-family:monospace;font-size:12px">{name}</div>
          </div>
          <div class="meta-item">
            <div class="meta-key">inputs</div>
            <div class="meta-val">{inp_sum.get("count",0)} ({len(inp_sum.get("required",[]))} requis)</div>
          </div>
          <div class="meta-item">
            <div class="meta-key">outputs</div>
            <div class="meta-val">{len(outputs)}</div>
          </div>
          {'<div class="meta-item"><div class="meta-key">steps</div><div class="meta-val">'+str(len(steps))+'</div></div>' if steps else ''}
        </div>
        <div style="margin-bottom:10px">
          <div style="font-size:11px;color:var(--muted);font-weight:600;
               text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px">Goal</div>
          <div style="font-size:13px">{goal}</div>
          {f'<div style="font-size:12px;color:var(--muted);margin-top:4px">{mission}</div>' if mission else ''}
        </div>
        <div style="margin-bottom:10px;display:flex;gap:6px;flex-wrap:wrap;align-items:center">
          <span style="font-size:11px;color:var(--muted);font-weight:600;
                text-transform:uppercase;letter-spacing:.07em">Deps:</span>
          {tags_html or '<span style="color:var(--muted);font-size:11px">—</span>'}
        </div>
        {'<div style="margin-bottom:10px;display:flex;gap:6px;flex-wrap:wrap;align-items:center"><span style="font-size:11px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.07em">Used in:</span>' + belongs_html + '</div>' if belongs else ''}
        <div>
          <div style="font-size:11px;color:var(--muted);font-weight:600;text-transform:uppercase;
               letter-spacing:.07em;margin-bottom:6px;display:flex;gap:8px;align-items:center">
            CLI
            <button class="copy-btn" onclick="copyText(this,document.getElementById('cli-{name.replace('.','_')}').textContent)">Copy</button>
          </div>
          <div class="cli-block" id="cli-{name.replace('.','_')}">{cli}</div>
        </div>
      </div>
    </div>"""

    # ── Pipeline chaining (scenarios only) ────────────────────────────────────
    chain_html = ""
    if steps:
        def _chain_row(i, s):
            arrow = "" if i == 0 else '<span class="chain-arrow">→</span>'
            ep    = s.get("endpoint", "")
            note  = (f'<span class="chain-note">({s["note"]})</span>'
                     if s.get("note") else "")
            return (f'<div class="chain-step">{arrow}'
                    f'<a class="chain-name" href="/node/{ep}">{ep}</a>{note}</div>')
        rows = "".join(_chain_row(i, s) for i, s in enumerate(steps))
        chain_html = f"""
    <div class="section">
      <div class="section-hd"><span class="section-title">Pipeline Chaining</span></div>
      <div class="section-body"><div class="chain">{rows}</div></div>
    </div>"""

    # ── B. Inputs section ─────────────────────────────────────────────────────
    req_fields = [(k, v) for k, v in inputs.items() if v.get("required")]
    opt_fields = [(k, v) for k, v in inputs.items() if not v.get("required")]

    req_html = "".join(_build_input_field(k, v) for k, v in req_fields)
    opt_html = "".join(_build_input_field(k, v) for k, v in opt_fields)
    opt_block = (f"""
      <details style="margin-top:10px">
        <summary style="cursor:pointer;font-size:12px;color:var(--muted);
          list-style:none;display:flex;gap:6px;align-items:center;padding:4px 0">
          <span>▶</span> Inputs optionnels ({len(opt_fields)})
        </summary>
        <div style="margin-top:10px;display:flex;flex-direction:column;gap:10px">
          {opt_html}
        </div>
      </details>""" if opt_fields else "")

    disabled = "" if pg_enabled else "disabled"
    inputs_section = f"""
    <div class="section">
      <div class="section-hd">
        <span class="section-title">B. Inputs</span>
        <span style="font-size:11px;color:var(--muted)">{len(inputs)} champs · {len(req_fields)} requis</span>
      </div>
      <div class="section-body">
        <div class="inputs-grid">{req_html}</div>
        {opt_block}
      </div>
    </div>"""

    # ── C. Execution section ──────────────────────────────────────────────────
    exec_section = f"""
    <div class="section">
      <div class="section-hd"><span class="section-title">C. Execution</span></div>
      <div class="section-body">
        <div class="run-row">
          <button class="btn-run" id="btn-run" onclick="runNode()" {disabled}>
            ▶ Exécuter
          </button>
          <span class="elapsed" id="elapsed"></span>
          <span class="run-status" id="run-status"></span>
        </div>
        {'<div style="margin-top:8px;font-size:12px;color:var(--orange)">⚠ Requiert des dépendances externes (Playwright / Anthropic API). Non exécutable directement.</div>' if not pg_enabled else ''}
      </div>
    </div>"""

    # ── D. Outputs section ────────────────────────────────────────────────────
    out_schema_js = _json.dumps({k: v for k, v in outputs.items()})
    outputs_section = f"""
    <div class="section" id="output-section" style="display:none">
      <div class="section-hd">
        <span class="section-title">D. Outputs</span>
        <div style="display:flex;gap:6px">
          <span id="out-status" style="font-size:12px"></span>
          <button class="copy-btn" id="copy-raw-btn"
                  onclick="copyText(this, document.getElementById('raw-output').textContent)"
                  style="display:none">Copy Raw</button>
        </div>
      </div>
      <div class="section-body">
        <div id="out-viz"></div>
        <details style="margin-top:12px" id="raw-details">
          <summary style="cursor:pointer;font-size:11px;color:var(--muted);
            list-style:none;display:flex;align-items:center;gap:6px;padding:2px 0">
            <span>▶</span> Raw JSON
          </summary>
          <pre class="json-view" id="raw-output" style="margin-top:8px"></pre>
        </details>
      </div>
    </div>"""

    # ── JS ────────────────────────────────────────────────────────────────────
    input_keys = _json.dumps(list(inputs.keys()))
    js = f"""
<script>
const NODE_NAME   = {_json.dumps(name)};
const INPUT_KEYS  = {input_keys};
const OUT_SCHEMA  = {out_schema_js};

function getInputs() {{
  const data = {{}};
  INPUT_KEYS.forEach(k => {{
    const el = document.getElementById('f_' + k);
    if (!el) return;
    const v = el.value.trim();
    if (v) data[k] = v;
  }});
  return data;
}}

async function runNode() {{
  const btn   = document.getElementById('btn-run');
  const elEl  = document.getElementById('elapsed');
  const stEl  = document.getElementById('run-status');
  const outSec= document.getElementById('output-section');
  btn.disabled = true;
  elEl.textContent = '';
  stEl.textContent = 'Running…';
  stEl.className   = 'run-status';
  outSec.style.display = 'none';

  const t0 = Date.now();
  let ticker = setInterval(() => {{
    elEl.textContent = ((Date.now()-t0)/1000).toFixed(1) + 's';
  }}, 100);

  try {{
    const res  = await fetch('/api/run/' + NODE_NAME, {{
      method:  'POST',
      headers: {{'Content-Type':'application/json'}},
      body:    JSON.stringify(getInputs()),
    }});
    clearInterval(ticker);
    const data = await res.json();
    elEl.textContent = (data.elapsed_s || ((Date.now()-t0)/1000).toFixed(1)) + 's';

    if (data.ok) {{
      stEl.textContent = '✓ OK';
      stEl.className   = 'run-status ok';
      renderOutputs(data.result);
    }} else {{
      stEl.textContent = '✗ Erreur';
      stEl.className   = 'run-status err';
      renderError(data.error, data.traceback);
      outSec.style.display = '';
    }}
  }} catch(e) {{
    clearInterval(ticker);
    stEl.textContent = '✗ ' + e.message;
    stEl.className   = 'run-status err';
  }}
  btn.disabled = false;
}}

// ── Typed output rendering ────────────────────────────────────────────────────

function isPalette(v) {{
  return v && typeof v === 'object' && !Array.isArray(v) &&
    ('primary' in v || 'background' in v || 'accent' in v);
}}

function detectType(key, value) {{
  if (key === 'html' || (typeof value === 'string' &&
      (value.trimStart().startsWith('<!') || value.trimStart().startsWith('<html')))) {{
    return 'html';
  }}
  if (isPalette(value)) return 'palette';
  if (Array.isArray(value))  return 'list';
  if (typeof value === 'object' && value !== null) return 'dict';
  if (typeof value === 'string') return 'string';
  return 'scalar';
}}

function vizPalette(val) {{
  const COLOR_KEYS = ['primary','secondary','accent','background','surface',
                      'text_primary','text_secondary','border'];
  let rows = '';
  COLOR_KEYS.forEach(k => {{
    if (!val[k] || typeof val[k] !== 'string') return;
    rows += `<div class="pal-row">
      <div class="pal-swatch" style="background:${{val[k]}}"></div>
      <div class="pal-info">
        <div class="pal-key">${{k}}</div>
        <div class="pal-hex">${{val[k]}}</div>
      </div>
    </div>`;
  }});
  // Extra keys
  Object.entries(val).forEach(([k,v]) => {{
    if (COLOR_KEYS.includes(k) || typeof v !== 'string') return;
    if (/^#[0-9a-f]{{3,8}}$/i.test(v)) {{
      rows += `<div class="pal-row">
        <div class="pal-swatch" style="background:${{v}}"></div>
        <div class="pal-info"><div class="pal-key">${{k}}</div><div class="pal-hex">${{v}}</div></div>
      </div>`;
    }}
  }});
  return `<div class="palette-grid">${{rows}}</div>`;
}}

function vizHTML(val) {{
  const uid  = 'ifrm' + Math.random().toString(36).slice(2);
  const rawId= 'raw'  + Math.random().toString(36).slice(2);
  setTimeout(() => {{
    const el = document.getElementById(uid);
    if (el) el.srcdoc = val;
  }}, 0);
  return `
    <div class="view-tabs">
      <button class="view-tab active" onclick="switchView(this,'${{uid}}-wrap','${{rawId}}-wrap')">Preview</button>
      <button class="view-tab" onclick="switchView(this,'${{rawId}}-wrap','${{uid}}-wrap')">Raw HTML</button>
    </div>
    <div id="${{uid}}-wrap" class="html-preview">
      <iframe id="${{uid}}" sandbox="allow-scripts allow-same-origin"></iframe>
    </div>
    <div id="${{rawId}}-wrap" style="display:none">
      <pre class="json-view" style="max-height:300px">${{escHtml(val.slice(0,8000))}}</pre>
      ${{val.length > 8000 ? '<div style="font-size:11px;color:var(--muted);padding:4px 0">… '+val.length+' chars total</div>' : ''}}
    </div>`;
}}

function vizList(key, val) {{
  const MAX = 5;
  const total = val.length;
  const items = val.slice(0, MAX);
  let rows = items.map(item =>
    `<div class="list-item">${{escHtml(JSON.stringify(item, null, 1))}}</div>`
  ).join('');
  let showAll = '';
  if (total > MAX) {{
    const rest = val.slice(MAX);
    const restId = 'rest-' + Math.random().toString(36).slice(2);
    showAll = `<div id="${{restId}}" style="display:none">
      ${{rest.map(i => `<div class="list-item">${{escHtml(JSON.stringify(i,null,1))}}</div>`).join('')}}
    </div>
    <button class="show-all-btn" onclick="toggleRest('${{restId}}',this)">
      ▶ Voir les ${{total - MAX}} suivants
    </button>`;
  }}
  return `<div class="list-view">${{rows}}</div>${{showAll}}
    <div style="font-size:11px;color:var(--muted);margin-top:4px">${{total}} éléments total</div>`;
}}

function vizDict(val) {{
  return `<pre class="json-view">${{escHtml(JSON.stringify(val, null, 2))}}</pre>`;
}}

function vizScalar(val) {{
  const s = String(val);
  if (s.length < 60) {{
    return `<span class="badge" style="background:#1a1a22;border:1px solid var(--border);
            color:var(--text);font-family:monospace;font-size:13px">${{escHtml(s)}}</span>`;
  }}
  return `<pre class="json-view" style="max-height:120px">${{escHtml(s)}}</pre>`;
}}

function renderOutputs(result) {{
  const viz    = document.getElementById('out-viz');
  const rawEl  = document.getElementById('raw-output');
  const outSec = document.getElementById('output-section');
  const stEl   = document.getElementById('out-status');
  const cpBtn  = document.getElementById('copy-raw-btn');

  stEl.textContent = Object.keys(result).length + ' sorties';
  rawEl.textContent = JSON.stringify(result, null, 2);
  cpBtn.style.display = '';
  outSec.style.display = '';

  viz.innerHTML = '';
  for (const [key, value] of Object.entries(result)) {{
    const meta  = OUT_SCHEMA[key] || {{}};
    const ctype = (meta.type || '').toLowerCase();
    const dtype = detectType(key, value);

    const block = document.createElement('div');
    block.className = 'out-block';
    block.innerHTML = `
      <div class="out-hd">
        <span class="out-key">${{key}}</span>
        <span class="out-type">${{meta.type || dtype}}</span>
        <span class="out-desc">${{meta.description || ''}}</span>
      </div>
      <div class="out-body" id="obody-${{key}}"></div>`;
    viz.appendChild(block);

    const body = block.querySelector('.out-body');
    if (dtype === 'html') {{
      body.innerHTML = vizHTML(value);
    }} else if (dtype === 'palette') {{
      body.innerHTML = vizPalette(value);
    }} else if (dtype === 'list') {{
      body.innerHTML = vizList(key, value);
    }} else if (dtype === 'dict') {{
      body.innerHTML = vizDict(value);
    }} else {{
      body.innerHTML = vizScalar(value);
    }}
  }}
}}

function renderError(error, tb) {{
  const viz    = document.getElementById('out-viz');
  const stEl   = document.getElementById('out-status');
  stEl.textContent = '';
  viz.innerHTML = `<div class="err-box">${{escHtml(error)}}${{tb ? '\\n\\n' + escHtml(tb) : ''}}</div>`;
}}

// ── Helpers ───────────────────────────────────────────────────────────────────

function switchView(btn, showId, hideId) {{
  document.getElementById(showId).style.display = '';
  document.getElementById(hideId).style.display = 'none';
  btn.closest('.view-tabs').querySelectorAll('.view-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}}

function toggleRest(id, btn) {{
  const el = document.getElementById(id);
  const hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▼ Réduire' : '▶ Voir les suivants';
}}

function copyText(btn, text) {{
  navigator.clipboard.writeText(text).then(() => {{
    const orig = btn.textContent;
    btn.textContent = 'Copié ✓';
    setTimeout(() => btn.textContent = orig, 1500);
  }});
}}

function escHtml(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}
</script>"""

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8">
<title>{name} — EURKAI Nodes</title>
<style>{_NODE_CSS}</style>
</head><body>
<div class="hdr">
  <a href="/nodes" class="breadcrumb">← Nodes</a>
  <span class="breadcrumb">/</span>
  <span class="hdr-title">{name}</span>
</div>
<div class="page">
  {meta_section}
  {chain_html}
  {inputs_section}
  {exec_section}
  {outputs_section}
</div>
{js}
</body></html>"""


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n⬡ Design Playground — http://localhost:{PORT}\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)
