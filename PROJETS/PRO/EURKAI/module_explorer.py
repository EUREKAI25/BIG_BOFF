"""
module_explorer.py — v2
EURKAI Module Explorer — HTML generator

Integrates:
  GlyphSystem    → parametric SVG icons per category
  BackgroundSystem → dot-grid CSS (24px, aligned to icon grid)
  BorderSystem   → left-accent cards, corner_radius unified
  MotionSystem   → timing tokens, stagger, slideInRight detail panel

Usage:
  python module_explorer.py
  python module_explorer.py --output /tmp/explorer.html
"""
from __future__ import annotations
import argparse, colorsys, json, sys
from pathlib import Path
from datetime import datetime

ROOT        = Path(__file__).parent
MODULES_DIR = ROOT / "MODULES"
OUTPUT_HTML = ROOT / "module_explorer.html"


# ─── PictogramSystem (GlyphSystem) ───────────────────────────────────────────
try:
    sys.path.insert(0, str(MODULES_DIR / "pictogram_system"))
    from pictogram_system import generate_pictogram_set as _gen_pict  # type: ignore
    _PICT_OK = True
except ImportError:
    _PICT_OK = False


def _pict_set(archetype: str = "startup_clean", color: str = "#7c6bf5") -> dict[str, str]:
    if not _PICT_OK:
        return {}
    ps = _gen_pict(archetype, color=color)
    return ps.all


# ─── Color helpers ────────────────────────────────────────────────────────────
def hsl_hex(h: float, s: float = 0.62, l_: float = 0.48) -> str:
    r, g, b = colorsys.hls_to_rgb(h / 360, l_, s)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


# ─── Category metadata ────────────────────────────────────────────────────────
CAT_META: dict[str, dict] = {
    "ai":            {"label": "AI",            "color": "#818cf8"},
    "design":        {"label": "Design",        "color": "#34d399"},
    "document":      {"label": "Document",      "color": "#fb923c"},
    "capture":       {"label": "Capture",       "color": "#22d3ee"},
    "quality":       {"label": "Qualité",       "color": "#fbbf24"},
    "orchestration": {"label": "Orchestration", "color": "#a78bfa"},
    "utility":       {"label": "Utilitaire",    "color": "#6b7280"},
}

_CAT_RULES: list[tuple[list[str], str]] = [
    (["model_executor", "ai_inquiry", "conversational_brief",
      "design_exploration", "visual_intent", "vision_audit"],          "ai"),
    (["color_palette", "color_psychology", "visual_decorators",
      "brand", "logo", "palette", "seed_builder", "theme",
      "pictogram", "design_plan", "design_dna"],                       "design"),
    (["document_objects", "page_builder"],                             "document"),
    (["screenshot_capture", "scraper", "scan_and_do"],                 "capture"),
    (["auto_fix", "design_validator", "pipeline_validator",
      "visual_coherence", "visual_consistency", "design_learning"],    "quality"),
    (["project_orchestration", "design_endpoints",
      "design_scenarios", "design_catalog"],                           "orchestration"),
]

# GlyphSystem — inline SVG per category (startup_clean rules: 2px square/round cr=4)
# Injected via Python if PictogramSystem available, else inline fallback
_CAT_ICONS_FALLBACK: dict[str, str] = {
    "ai":            '<svg viewBox="0 0 48 48" width="16" height="16" fill="none"><path d="M28,4 L14,26 L24,26 L18,44 L34,22 L24,22 Z" fill="currentColor" stroke-width="0"/></svg>',
    "design":        '<svg viewBox="0 0 48 48" width="16" height="16" fill="none"><path d="M24,4 L29,19 L44,24 L29,29 L24,44 L19,29 L4,24 L19,19 Z" fill="currentColor" stroke-width="0"/></svg>',
    "document":      '<svg viewBox="0 0 48 48" width="16" height="16" fill="none"><rect x="4" y="4" width="18" height="18" stroke="currentColor" stroke-width="2" rx="2" fill="none"/><rect x="26" y="4" width="18" height="18" stroke="currentColor" stroke-width="2" rx="2" fill="none"/><rect x="4" y="26" width="18" height="18" stroke="currentColor" stroke-width="2" rx="2" fill="none"/><rect x="26" y="26" width="18" height="18" stroke="currentColor" stroke-width="2" rx="2" fill="none"/></svg>',
    "capture":       '<svg viewBox="0 0 24 24" width="16" height="16" fill="none"><circle cx="10" cy="10" r="6.5" stroke="currentColor" stroke-width="2"/><line x1="14.6" y1="14.6" x2="21" y2="21" stroke="currentColor" stroke-width="2" stroke-linecap="square"/></svg>',
    "quality":       '<svg viewBox="0 0 48 48" width="16" height="16" fill="none"><path d="M24,4 L44,11 L44,26 Q44,38 24,45 Q4,38 4,26 L4,11 Z" stroke="currentColor" stroke-width="2" fill="none"/></svg>',
    "orchestration": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none"><line x1="2" y1="12" x2="18" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="square"/><polyline points="12,6 18,12 12,18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="square" stroke-linejoin="round"/></svg>',
    "utility":       '<svg viewBox="0 0 24 24" width="16" height="16" fill="none"><line x1="2" y1="6" x2="22" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="square"/><circle cx="8" cy="6" r="2.5" stroke="currentColor" stroke-width="2" fill="none"/><line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="square"/><circle cx="16" cy="12" r="2.5" stroke="currentColor" stroke-width="2" fill="none"/><line x1="2" y1="18" x2="22" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="square"/><circle cx="10" cy="18" r="2.5" stroke="currentColor" stroke-width="2" fill="none"/></svg>',
}

# Try to replace with PictogramSystem icons
def _build_cat_icons() -> dict[str, str]:
    if not _PICT_OK:
        return _CAT_ICONS_FALLBACK
    mapping = {
        "ai":            ("lightning", "feature",    "#818cf8"),
        "design":        ("star_four", "feature",    "#34d399"),
        "document":      ("grid_modules", "feature", "#fb923c"),
        "capture":       ("search",   "functional",  "#22d3ee"),
        "quality":       ("shield",   "feature",     "#fbbf24"),
        "orchestration": ("arrow_right", "functional", "#a78bfa"),
        "utility":       ("settings", "functional",  "#6b7280"),
    }
    result = {}
    for cat, (icon_name, family, color) in mapping.items():
        ps = _gen_pict("startup_clean", color=color)  # type: ignore
        svgs = ps.feature if family == "feature" else ps.functional
        result[cat] = svgs.get(icon_name, _CAT_ICONS_FALLBACK.get(cat, ""))
    return result

_CAT_ICONS = _build_cat_icons()


# ─── Tag taxonomy ─────────────────────────────────────────────────────────────
_TAG_MAP: dict[str, list[str]] = {
    "visual":   ["color", "visual", "design", "palette", "brand", "logo", "theme", "pictogram"],
    "ai":       ["model", "ai_inquiry", "vision", "intent", "anthropic", "openai", "gemini"],
    "css":      ["css", "html", "render", "page_builder", "decorators", "scss"],
    "audit":    ["audit", "validator", "coherence", "fix", "learning", "score"],
    "capture":  ["screenshot", "scraper", "scan", "capture"],
    "svg":      ["svg", "pictogram", "logo", "glyph"],
    "wcag":     ["wcag", "contrast", "accessibility"],
    "pipeline": ["pipeline", "orchestration", "scenario", "endpoint", "batch"],
    "document": ["document", "invoice", "dashboard"],
    "seed":     ["seed", "dna", "brief", "context"],
}


# ─── Scenario membership (manually curated) ───────────────────────────────────
_SCENARIOS: dict[str, list[str]] = {
    "visual_intent_engine":    ["design_pipeline", "design.page.generate_full"],
    "color_palette":           ["design_pipeline", "design.page.generate_full"],
    "visual_coherence_engine": ["design_pipeline", "design.page.generate_full"],
    "design_plan":             ["design_pipeline", "design.page.generate_full"],
    "visual_decorators":       ["design_pipeline"],
    "auto_fix_engine":         ["design_pipeline", "design.page.fix"],
    "screenshot_capture":      ["design.page.capture", "design.page.fix"],
    "vision_audit":            ["design.page.audit", "design.page.fix"],
    "brand_identity":          ["design.brand.generate_full"],
    "logo_generator":          ["design.brand.generate_full"],
    "color_psychology_engine": ["design.brand.generate_full"],
    "design_learning":         ["design_pipeline"],
    "design_validator":        ["design.page.audit"],
}


# ─── Pipeline stages (known design pipeline) ─────────────────────────────────
PIPELINE_STAGES: list[dict] = [
    {"id": "input",                   "label": "Brief",         "io": True},
    {"id": "visual_intent_engine",    "label": "Visual\nIntent","cat": "ai"},
    {"id": "color_palette",           "label": "Palette",       "cat": "design"},
    {"id": "visual_coherence_engine", "label": "Coherence",     "cat": "quality"},
    {"id": "design_plan",             "label": "Design Plan",   "cat": "design"},
    {"id": "visual_decorators",       "label": "Decorators",    "cat": "design"},
    {"id": "screenshot_capture",      "label": "Capture",       "cat": "capture"},
    {"id": "vision_audit",            "label": "Audit",         "cat": "quality"},
    {"id": "auto_fix_engine",         "label": "Auto Fix",      "cat": "quality"},
    {"id": "output",                  "label": "HTML\nOutput",  "io": True},
]


# ─── MANIFEST normalization ───────────────────────────────────────────────────
def _ext_inputs(raw: dict) -> dict:
    if "inputs" in raw:
        return raw["inputs"]
    fn = raw.get("function", {})
    return fn.get("inputs", {})


def _ext_outputs(raw: dict) -> dict:
    for key in ("outputs", "output_schema"):
        if key in raw:
            v = raw[key]
            return v if isinstance(v, dict) else {"result": str(v)}
    fn  = raw.get("function", {})
    out = fn.get("output", {})
    return out if isinstance(out, dict) else {"result": str(out)}


def _ext_deps(raw: dict) -> tuple[list, list]:
    d = raw.get("dependencies", {})
    if isinstance(d, list):
        return d, []
    if isinstance(d, dict):
        # could be {"anthropic": ">=0.40.0"} or {"required": [...], "optional": [...]}
        if "required" in d or "optional" in d:
            return d.get("required", []), d.get("optional", [])
        return list(d.keys()), []
    return [], []


def _derive_cat(name: str) -> str:
    n = name.lower()
    for keys, cat in _CAT_RULES:
        if any(k in n for k in keys):
            return cat
    return "utility"


def _derive_tags(name: str, raw: dict) -> list[str]:
    blob = (name + " " + json.dumps(raw)).lower()
    return [t for t, kws in _TAG_MAP.items() if any(k in blob for k in kws)]


def _build_preview(name: str, raw: dict) -> tuple[str, dict]:
    """Return (preview_type, preview_data) for a module."""
    n = name.lower()

    # Color palette modules → swatch strip
    if any(k in n for k in ("color_palette", "palette_generator", "color_psychology")):
        hues_raw = raw.get("emotional_goal_hues", {})
        if hues_raw:
            hues = []
            labels = []
            for lbl, val in hues_raw.items():
                try:
                    hues.append(int(str(val).split("°")[0]))
                    labels.append(lbl)
                except ValueError:
                    pass
            hues = hues[:6]
            labels = labels[:6]
        else:
            hues   = [220, 350, 340, 168, 268, 218]
            labels = ["trust", "excitement", "desire", "calm", "curiosity", "authority"]
        swatches = [hsl_hex(h) for h in hues]
        return "palette", {"swatches": swatches, "labels": labels}

    # Pictogram system → show actual SVG icons
    if "pictogram" in n and _PICT_OK:
        icons = _pict_set("startup_clean", color="#818cf8")
        preview = {}
        for k in ("home", "search", "check", "star_four", "lightning", "diamond"):
            if k in icons:
                preview[k] = icons[k]
        return "pictograms", {"icons": preview}

    # Audit/quality modules → score bar visualization
    if any(k in n for k in ("audit", "coherence", "validator")):
        metrics_raw = raw.get("fail_conditions", raw.get("fix_types", []))
        metrics = [str(m).split("—")[0].strip()[:22] for m in metrics_raw[:3]]
        if not metrics:
            metrics = ["readability", "contrast", "layout"]
        return "score", {"metrics": metrics}

    # Default: I/O diagram
    inputs  = _ext_inputs(raw)
    outputs = _ext_outputs(raw)
    return "io", {
        "inputs":  list(inputs.keys())[:3],
        "outputs": list(outputs.keys())[:3],
    }


def normalize(raw: dict, mf: Path) -> dict:
    dir_name = mf.parent.name
    name     = raw.get("module") or raw.get("name") or dir_name
    fn       = raw.get("function", {})
    dr, do   = _ext_deps(raw)
    inputs   = _ext_inputs(raw)
    outputs  = _ext_outputs(raw)
    integ    = raw.get("integration", {})
    ptype, pdata = _build_preview(name, raw)

    pub_api = raw.get("public_api", [])
    if fn.get("name") and fn["name"] not in pub_api:
        pub_api = [fn["name"]] + list(pub_api)

    return {
        "name":        name,
        "dir":         dir_name,
        "version":     raw.get("version", "?"),
        "description": raw.get("description", ""),
        "philosophy":  raw.get("philosophy", ""),
        "category":    _derive_cat(name),
        "tags":        _derive_tags(name, raw),
        "status":      raw.get("status", "stable"),
        "endpoint":    raw.get("endpoint", ""),
        "fn_name":     fn.get("name", ""),
        "fn_sig":      fn.get("signature", ""),
        "public_api":  pub_api,
        "inputs":      inputs,
        "outputs":     outputs,
        "deps_req":    dr,
        "deps_opt":    do,
        "integration": integ if isinstance(integ, dict) else {"note": str(integ)},
        "scenarios":   _SCENARIOS.get(name, []),
        "preview_type": ptype,
        "preview_data": pdata,
    }


# ─── Relationship builder ─────────────────────────────────────────────────────
def build_relationships(modules: list[dict]) -> dict[str, list[str]]:
    """Compute used_by: name → list of modules that depend on it."""
    used_by: dict[str, list[str]] = {}
    for m in modules:
        for dep in m["deps_req"] + m["deps_opt"]:
            dep_norm = dep.lower().split("(")[0].strip().replace("-", "_").replace(" ", "_")
            for other in modules:
                if other["name"] == m["name"]:
                    continue
                if other["name"].lower() in dep_norm or dep_norm in other["name"].lower():
                    used_by.setdefault(other["name"], [])
                    if m["name"] not in used_by[other["name"]]:
                        used_by[other["name"]].append(m["name"])
    return used_by


# ─── Scanner ─────────────────────────────────────────────────────────────────
def scan_modules(modules_dir: Path) -> list[dict]:
    modules = []
    for mf in sorted(modules_dir.rglob("MANIFEST.json")):
        if mf.parent.parent != modules_dir:
            continue
        try:
            raw = json.loads(mf.read_text(encoding="utf-8"))
            modules.append(normalize(raw, mf))
        except Exception as e:
            print(f"  ⚠  {mf.parent.name}: {e}", file=sys.stderr)
    return modules


# ─── CSS ─────────────────────────────────────────────────────────────────────
# Written as a regular string (not f-string) so {} are literal CSS
_CSS = """
/* ── MotionSystem tokens ──────────────────────────────────────── */
:root {
  --dur-fast:    110ms;
  --dur-normal:  220ms;
  --dur-slow:    380ms;
  --dur-detail:  300ms;
  --ease-enter:  cubic-bezier(0, 0, 0.2, 1);
  --ease-exit:   cubic-bezier(0.4, 0, 1, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* BorderSystem */
  --radius: 8px;

  /* Colors */
  --bg:        #070710;
  --bg-card:   #0b0b16;
  --bg-detail: #0e0e1a;
  --border:    #18182e;
  --border-hi: #242440;
  --text:      #e2e2f0;
  --muted:     #56566e;
  --accent:    #7c6bf5;
  --accent2:   #06b6d4;
  --font-mono: "SF Mono","Fira Code","Cascadia Code",monospace;
  --font-ui:   -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
}

/* ── MotionSystem keyframes ───────────────────────────────────── */
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0);    }
}
@keyframes slideInRight {
  from { opacity: 0; transform: translateX(20px); }
  to   { opacity: 1; transform: translateX(0);    }
}
@keyframes drawIn {
  from { stroke-dashoffset: 100; }
  to   { stroke-dashoffset: 0;   }
}
@keyframes pulseDot {
  0%, 100% { opacity: .5; transform: scale(.9); }
  50%       { opacity: 1;  transform: scale(1.1); }
}

/* ── Reset ────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: var(--font-ui);
  font-size: 14px;
  line-height: 1.6;
  color: var(--text);
  min-height: 100vh;
  /* BackgroundSystem — dot grid, 24px (aligned to GlyphSystem icon grid) */
  background-color: var(--bg);
  background-image: radial-gradient(circle, #1c1c35 1px, transparent 1px);
  background-size: 24px 24px;
}

/* ── Layout ───────────────────────────────────────────────────── */
.site-header {
  position: sticky; top: 0; z-index: 200;
  height: 52px;
  display: flex; align-items: center; gap: 14px;
  padding: 0 20px;
  background: rgba(7,7,16,.92);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border);
}
.logo-mark {
  width: 26px; height: 26px;
  border-radius: 6px;
  background: var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 800; color: #fff; letter-spacing: .04em;
  flex-shrink: 0;
}
.logo-text { font-size: 14px; font-weight: 700; letter-spacing: .02em; }
.header-divider { color: var(--muted); font-size: 16px; font-weight: 200; }
.header-section { font-size: 12px; color: var(--muted); }
.header-spacer  { flex: 1; }
.header-meta    { font-size: 11px; color: var(--muted); font-family: var(--font-mono); }

.view-toggle { display: flex; gap: 4px; }
.vbtn {
  padding: 5px 11px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--muted);
  font-size: 11.5px; font-family: var(--font-ui);
  cursor: pointer;
  display: flex; align-items: center; gap: 5px;
  transition: all var(--dur-fast) var(--ease-enter);
}
.vbtn:hover { color: var(--text); border-color: var(--border-hi); }
.vbtn.active {
  background: rgba(124,107,245,.14);
  border-color: var(--accent);
  color: var(--accent);
}

/* ── Shell ────────────────────────────────────────────────────── */
.shell {
  display: flex;
  min-height: calc(100vh - 52px);
}
.main {
  flex: 1; min-width: 0;
  padding: 24px 20px;
}
.detail-pane {
  position: sticky; top: 52px;
  height: calc(100vh - 52px);
  width: 0; overflow: hidden;
  border-left: 1px solid var(--border);
  background: var(--bg-detail);
  transition: width var(--dur-detail) var(--ease-enter);
  flex-shrink: 0;
}
.detail-pane.open {
  width: 468px;
  overflow-y: auto;
}

/* ── Hero ─────────────────────────────────────────────────────── */
.hero { margin-bottom: 22px; }
.hero-title {
  font-size: 24px; font-weight: 700; letter-spacing: -.02em; margin-bottom: 4px;
}
.hero-title span {
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-sub { font-size: 13px; color: var(--muted); margin-bottom: 14px; }
.stats-row { display: flex; gap: 24px; }
.stat { display: flex; flex-direction: column; gap: 1px; }
.stat-val {
  font-size: 20px; font-weight: 700;
  font-family: var(--font-mono); color: var(--accent); line-height: 1;
}
.stat-lbl {
  font-size: 10px; color: var(--muted);
  text-transform: uppercase; letter-spacing: .08em;
}

/* ── Filter bar ───────────────────────────────────────────────── */
.filter-bar {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 14px;
  margin-bottom: 18px;
  display: flex; flex-direction: column; gap: 10px;
}
.filter-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.search-box {
  flex: 1; min-width: 160px; max-width: 260px;
  padding: 7px 11px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text); font-size: 13px; font-family: var(--font-ui);
  outline: none;
  transition: border-color var(--dur-fast) var(--ease-enter);
}
.search-box::placeholder { color: var(--muted); }
.search-box:focus { border-color: var(--accent); }

.pill {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 10px;
  border-radius: 20px; border: 1px solid var(--border);
  background: transparent; color: var(--muted);
  font-size: 11.5px; cursor: pointer;
  transition: all var(--dur-fast) var(--ease-enter);
  font-family: var(--font-ui); white-space: nowrap;
  --pc: var(--accent);
}
.pill:hover  { border-color: var(--pc); color: var(--pc); }
.pill.active { border-color: var(--pc); color: var(--pc); background: rgba(124,107,245,.1); }
.pill.active { background-color: var(--pc-bg, rgba(124,107,245,.1)); }
.pill svg    { width: 14px; height: 14px; }
.pill .cnt   {
  font-size: 10px; font-family: var(--font-mono);
  background: rgba(255,255,255,.06); padding: 0 5px; border-radius: 8px;
}

.tags-wrap { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
.tags-label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-right: 2px; }
.tag-chip {
  padding: 2px 8px;
  border-radius: 4px; border: 1px solid var(--border);
  background: transparent; color: var(--muted);
  font-size: 10.5px; font-family: var(--font-mono); cursor: pointer;
  transition: all var(--dur-fast) var(--ease-enter);
}
.tag-chip:hover  { border-color: var(--accent); color: var(--accent); }
.tag-chip.active { background: rgba(124,107,245,.14); border-color: rgba(124,107,245,.6); color: var(--accent); }

/* Active filters strip */
.active-strip {
  display: none; align-items: center; gap: 6px;
  font-size: 11px;
}
.active-strip.visible { display: flex; }
.active-strip-label { color: var(--muted); }
.clear-all {
  margin-left: auto; color: var(--muted);
  background: none; border: none; cursor: pointer; font-size: 11px;
  transition: color var(--dur-fast);
}
.clear-all:hover { color: var(--text); }

/* ── Results bar ─────────────────────────────────────────────── */
.results-bar {
  display: flex; align-items: center;
  margin-bottom: 12px;
}
.results-label { font-size: 11.5px; color: var(--muted); font-family: var(--font-mono); }

/* ── Card grid ────────────────────────────────────────────────── */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(268px,1fr));
  gap: 10px;
}
.no-results {
  grid-column: 1/-1; padding: 56px;
  text-align: center; color: var(--muted); display: none;
}

/* ── Card — BorderSystem ──────────────────────────────────────── */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-left: 3px solid var(--cc, var(--border));  /* left accent — BorderSystem */
  border-radius: var(--radius);
  cursor: pointer;
  display: flex; flex-direction: column;
  transition:
    border-color var(--dur-fast) var(--ease-enter),
    transform   var(--dur-normal) var(--ease-spring),
    box-shadow  var(--dur-normal) var(--ease-enter);
  animation: fadeSlideUp var(--dur-slow) var(--ease-enter) both;
}
.card:hover {
  border-color: var(--cc, var(--accent));
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0,0,0,.45),
              0 0 0 1px color-mix(in srgb, var(--cc, var(--accent)) 35%, transparent);
}
.card.selected {
  border-color: var(--cc, var(--accent));
  box-shadow: 0 0 0 1px var(--cc, var(--accent)), 0 8px 24px rgba(0,0,0,.45);
}
/* stagger animation */
.card:nth-child(1)  { animation-delay:  0ms }
.card:nth-child(2)  { animation-delay: 30ms }
.card:nth-child(3)  { animation-delay: 60ms }
.card:nth-child(4)  { animation-delay: 90ms }
.card:nth-child(5)  { animation-delay:120ms }
.card:nth-child(6)  { animation-delay:150ms }
.card:nth-child(7)  { animation-delay:180ms }
.card:nth-child(8)  { animation-delay:210ms }

.card-top {
  padding: 9px 12px 8px;
  display: flex; align-items: center; gap: 7px;
  border-bottom: 1px solid var(--border);
}
.card-icon { display: flex; color: var(--cc, var(--muted)); }
.card-cat  { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .1em; color: var(--cc, var(--muted)); flex: 1; }
.vbadge    { font-size: 10px; color: var(--muted); font-family: var(--font-mono); background: var(--border); padding: 1px 6px; border-radius: 4px; }

.card-body { padding: 10px 12px 6px; flex: 1; }
.card-name {
  font-size: 13px; font-weight: 600; font-family: var(--font-mono);
  color: var(--text); margin-bottom: 4px;
}
.card-desc {
  font-size: 11.5px; color: var(--muted); line-height: 1.45;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

/* ── Card preview area ────────────────────────────────────────── */
.card-preview {
  margin: 7px 12px 4px;
  padding: 8px 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 5px;
  min-height: 38px;
  display: flex; align-items: center;
}

/* I/O mini */
.io-mini { display: flex; align-items: center; gap: 6px; overflow: hidden; font-size: 10.5px; font-family: var(--font-mono); }
.io-col  { display: flex; flex-direction: column; gap: 2px; }
.io-key  { color: var(--accent2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 80px; }
.io-key.out { color: var(--accent); }
.io-arr  { color: var(--muted); flex-shrink: 0; font-size: 13px; }
.io-dot  { width: 20px; height: 20px; border-radius: 50%; border: 1.5px solid var(--cc, var(--border)); flex-shrink: 0; }

/* Palette mini */
.pal-mini { display: flex; gap: 3px; height: 20px; width: 100%; }
.swatch   { flex: 1; border-radius: 3px; }

/* Pictograms mini */
.pict-mini { display: flex; gap: 8px; }

/* Score mini */
.score-mini { display: flex; flex-direction: column; gap: 5px; width: 100%; }
.score-row  { display: flex; align-items: center; gap: 7px; font-size: 10px; color: var(--muted); font-family: var(--font-mono); }
.score-track { flex: 1; height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; }
.score-fill  { height: 100%; border-radius: 2px; background: var(--cc, var(--accent)); }

/* ── Card footer ──────────────────────────────────────────────── */
.card-footer { padding: 7px 12px; display: flex; gap: 4px; flex-wrap: wrap; border-top: 1px solid var(--border); }
.tag { font-size: 10px; padding: 2px 6px; border-radius: 3px; background: var(--border); color: var(--muted); font-family: var(--font-mono); }

/* ── Pipeline view ────────────────────────────────────────────── */
.pipeline-view { display: none; padding: 32px 0; }
.pipeline-view.visible { display: block; }
.pipeline-scroll { overflow-x: auto; cursor: grab; padding-bottom: 16px; }
.pipeline-scroll:active { cursor: grabbing; }
.pipeline-flow { display: flex; align-items: center; min-width: max-content; padding: 0 20px; gap: 0; }
.pipe-node {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-top: 3px solid var(--nc, var(--border));
  border-radius: var(--radius);
  padding: 16px 18px;
  min-width: 108px;
  text-align: center; cursor: pointer;
  transition: all var(--dur-normal) var(--ease-enter);
}
.pipe-node:hover { border-color: var(--nc, var(--accent)); transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.5); }
.pipe-node.io-node { border-top-color: var(--border); cursor: default; }
.pipe-node.io-node:hover { transform: none; box-shadow: none; }
.pipe-icon { display: flex; justify-content: center; margin-bottom: 6px; color: var(--nc, var(--muted)); }
.pipe-label { font-size: 11px; font-family: var(--font-mono); color: var(--text); font-weight: 600; white-space: pre; }
.pipe-node.io-node .pipe-label { color: var(--muted); }
.pipe-arr { padding: 0 6px; }
.pipe-arr svg { color: var(--border-hi); }

/* ── Detail panel ─────────────────────────────────────────────── */
.detail-inner {
  padding: 20px;
  animation: slideInRight var(--dur-normal) var(--ease-enter) both;
}
.detail-hd { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 14px; }
.detail-title-row { flex: 1; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.detail-name  { font-size: 17px; font-weight: 700; font-family: var(--font-mono); }
.cat-pill { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; padding: 3px 8px; border-radius: 4px; }
.close-btn {
  background: var(--border); border: 1px solid var(--border-hi); border-radius: 6px;
  padding: 6px; cursor: pointer; color: var(--muted);
  display: flex; align-items: center; justify-content: center;
  transition: all var(--dur-fast) var(--ease-enter); flex-shrink: 0;
}
.close-btn:hover { color: var(--text); background: var(--border-hi); }

.detail-desc { font-size: 13px; margin-bottom: 10px; line-height: 1.6; }
.philosophy  { font-size: 12px; color: var(--accent2); font-style: italic; border-left: 2px solid rgba(6,182,212,.35); padding-left: 10px; margin-bottom: 14px; line-height: 1.5; }
.ep-row { display: inline-flex; align-items: center; gap: 8px; background: var(--border); border-radius: 6px; padding: 5px 11px; margin-bottom: 12px; font-family: var(--font-mono); font-size: 11.5px; }
.ep-label { font-size: 10px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
.sig-block { background: #080813; border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; margin-bottom: 12px; overflow-x: auto; font-family: var(--font-mono); font-size: 11.5px; color: var(--accent2); line-height: 1.5; }
.api-strip { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 16px; }
.api-fn { font-family: var(--font-mono); font-size: 11px; background: rgba(124,107,245,.12); color: var(--accent); border: 1px solid rgba(124,107,245,.3); padding: 3px 8px; border-radius: 4px; }

/* ── Detail preview ───────────────────────────────────────────── */
.detail-preview { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 14px; margin-bottom: 16px; }
.preview-lbl { font-size: 10px; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin-bottom: 10px; font-weight: 600; }

/* I/O diagram */
.io-diagram { display: flex; align-items: flex-start; gap: 14px; }
.io-dcol    { display: flex; flex-direction: column; gap: 5px; min-width: 90px; }
.io-dcol-hd { font-size: 10px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: 2px; }
.io-item    { font-family: var(--font-mono); font-size: 11px; padding: 3px 8px; border-radius: 4px; background: rgba(6,182,212,.1); color: var(--accent2); border: 1px solid rgba(6,182,212,.25); }
.io-item.out{ background: rgba(124,107,245,.1); color: var(--accent); border-color: rgba(124,107,245,.25); }
.io-mid     { display: flex; flex-direction: column; align-items: center; gap: 5px; padding-top: 16px; }
.io-mid-arr { color: var(--muted); font-size: 16px; }
.io-mbox    { background: rgba(124,107,245,.12); border: 1.5px solid rgba(124,107,245,.4); border-radius: 6px; padding: 7px 12px; font-family: var(--font-mono); font-size: 11px; color: var(--accent); text-align: center; font-weight: 600; white-space: nowrap; }

/* Palette full */
.pal-full { display: flex; gap: 6px; }
.pal-item { flex: 1; display: flex; flex-direction: column; gap: 4px; align-items: center; }
.pal-swatch { width: 100%; height: 32px; border-radius: 5px; }
.pal-label  { font-size: 9px; color: var(--muted); font-family: var(--font-mono); }

/* Pictograms full */
.pict-full { display: flex; gap: 14px; flex-wrap: wrap; justify-content: center; }
.pict-item { display: flex; flex-direction: column; align-items: center; gap: 5px; }
.pict-item svg { width: 32px; height: 32px; }
.pict-label { font-size: 9px; color: var(--muted); font-family: var(--font-mono); }

/* ── Detail sections ──────────────────────────────────────────── */
.ds-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.ds { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
.ds-hd { font-size: 10.5px; font-weight: 600; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); padding: 6px 12px; border-bottom: 1px solid var(--border); background: var(--bg-card); }
.pt { width: 100%; border-collapse: collapse; font-size: 11.5px; }
.pt th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); padding: 5px 12px; background: var(--bg-card); border-bottom: 1px solid var(--border); }
.pt td { padding: 6px 12px; border-bottom: 1px solid var(--border); vertical-align: top; line-height: 1.4; }
.pt tr:last-child td { border-bottom: none; }
.pk { font-family: var(--font-mono); color: var(--accent2); font-size: 11px; white-space: nowrap; }
.pv { color: var(--muted); font-size: 11px; }

/* Relationships */
.rel-inner { padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; }
.rel-row   { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
.rel-lbl   { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; min-width: 72px; }
.rel-chip  { font-family: var(--font-mono); font-size: 11px; padding: 2px 8px; border-radius: 4px; cursor: pointer; transition: opacity var(--dur-fast); }
.rel-chip:hover { opacity: .72; }
.rel-dep  { background: rgba(6,182,212,.1);   color: var(--accent2); border: 1px solid rgba(6,182,212,.3); }
.rel-used { background: rgba(124,107,245,.1); color: var(--accent);  border: 1px solid rgba(124,107,245,.3); }
.rel-scen { background: rgba(244,114,182,.1); color: #f472b6;        border: 1px solid rgba(244,114,182,.3); }

/* Deps */
.deps-inner { padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; }
.deps-grp-lbl { font-size: 10px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: 4px; }
.deps-grp ul { list-style: none; display: flex; flex-direction: column; gap: 3px; }
.deps-grp li code { font-family: var(--font-mono); font-size: 11px; color: var(--text); background: var(--border); padding: 2px 7px; border-radius: 3px; }

.empty-note { padding: 10px 12px; color: var(--muted); font-size: 12px; font-style: italic; }

/* Detail footer */
.detail-footer { display: flex; gap: 4px; flex-wrap: wrap; padding-top: 12px; border-top: 1px solid var(--border); }

/* ── Scrollbars ───────────────────────────────────────────────── */
::-webkit-scrollbar       { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 2px; }
"""


# ─── JS app ───────────────────────────────────────────────────────────────────
# Written as a regular string (not f-string) — free use of {}
_JS_APP = r"""
/* ── State ──────────────────────────────────────────────────── */
const CAT  = window.CAT_META;
const MODS = window.MODULES;
const RELS = window.RELATIONSHIPS;
const PIPE = window.PIPELINE;

let state = {
  cat:    'all',       // single-select category
  tags:   new Set(),   // multi-select tags (OR logic)
  search: '',
  view:   'grid',      // 'grid' | 'pipeline'
  sel:    null,        // selected module index
};

/* ── Utils ───────────────────────────────────────────────────── */
function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function catColor(cat) { return (CAT[cat]||{}).color || '#6b7280'; }
function catLabel(cat) { return (CAT[cat]||{}).label || cat; }
function catIcon(cat)  { return window.CAT_ICONS[cat] || ''; }

/* ── Card rendering ──────────────────────────────────────────── */
function renderCardPreview(m) {
  const p = m.preview_data, cc = catColor(m.category);

  if (m.preview_type === 'palette' && p.swatches) {
    const swatches = p.swatches.map(c =>
      `<div class="swatch" style="background:${esc(c)}"></div>`).join('');
    return `<div class="card-preview"><div class="pal-mini">${swatches}</div></div>`;
  }

  if (m.preview_type === 'pictograms') {
    const icons = Object.values(p.icons||{}).slice(0,4).join('');
    return `<div class="card-preview"><div class="pict-mini">${icons}</div></div>`;
  }

  if (m.preview_type === 'score') {
    const bars = (p.metrics||[]).slice(0,3).map((metric, i) =>
      `<div class="score-row">
         <span style="width:72px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">${esc(metric)}</span>
         <div class="score-track" style="--cc:${cc}">
           <div class="score-fill" style="width:${55+i*18}%"></div>
         </div>
       </div>`).join('');
    return `<div class="card-preview"><div class="score-mini">${bars}</div></div>`;
  }

  // I/O mini
  const ins  = (p.inputs||[]).slice(0,2).map(k=>`<span class="io-key">${esc(k)}</span>`).join('');
  const outs = (p.outputs||[]).slice(0,2).map(k=>`<span class="io-key out">${esc(k)}</span>`).join('');
  return `<div class="card-preview">
    <div class="io-mini">
      <div class="io-col">${ins||'<span class="io-key" style="opacity:.3">—</span>'}</div>
      <span class="io-arr">→</span>
      <div class="io-dot" style="--cc:${cc}"></div>
      <span class="io-arr">→</span>
      <div class="io-col">${outs||'<span class="io-key out" style="opacity:.3">—</span>'}</div>
    </div>
  </div>`;
}

function renderCard(m, idx) {
  const cc  = catColor(m.category);
  const ico = catIcon(m.category);
  const tags = m.tags.slice(0,4).map(t=>`<span class="tag">${esc(t)}</span>`).join('');

  return `<div class="card" data-idx="${idx}" data-cat="${m.category}"
      data-name="${esc(m.name)}" data-tags='${JSON.stringify(m.tags)}'
      onclick="openDetail(${idx})"
      style="--cc:${cc}">
    <div class="card-top">
      <span class="card-icon">${ico}</span>
      <span class="card-cat">${esc(catLabel(m.category))}</span>
      <span class="vbadge">v${esc(m.version)}</span>
    </div>
    <div class="card-body">
      <div class="card-name">${esc(m.name)}</div>
      <div class="card-desc">${esc(m.description)}</div>
    </div>
    ${renderCardPreview(m)}
    <div class="card-footer">${tags}</div>
  </div>`;
}

/* ── Detail preview ──────────────────────────────────────────── */
function renderDetailPreview(m) {
  const p  = m.preview_data;
  const cc = catColor(m.category);
  let inner = '';

  if (m.preview_type === 'palette' && p.swatches) {
    inner = `<div class="pal-full">` +
      p.swatches.map((c,i) =>
        `<div class="pal-item">
           <div class="pal-swatch" style="background:${esc(c)}"></div>
           <span class="pal-label">${esc((p.labels||[])[i]||'')}</span>
         </div>`).join('') + `</div>`;

  } else if (m.preview_type === 'pictograms') {
    inner = `<div class="pict-full">` +
      Object.entries(p.icons||{}).map(([name,svg]) =>
        `<div class="pict-item">${svg}<span class="pict-label">${esc(name)}</span></div>`
      ).join('') + `</div>`;

  } else {
    const inKeys  = Object.keys(m.inputs||{}).slice(0,4);
    const outKeys = Object.keys(m.outputs||{}).slice(0,4);
    const ins  = inKeys.map(k=>`<span class="io-item">${esc(k)}</span>`).join('');
    const outs = outKeys.map(k=>`<span class="io-item out">${esc(k)}</span>`).join('');
    inner = `<div class="io-diagram">
      <div class="io-dcol">
        <div class="io-dcol-hd">Inputs</div>
        ${ins||'<span class="io-item" style="opacity:.3">—</span>'}
      </div>
      <div class="io-mid">
        <span class="io-mid-arr">→</span>
        <div class="io-mbox" style="--cc:${cc}">${esc(m.name)}</div>
        <span class="io-mid-arr">→</span>
      </div>
      <div class="io-dcol">
        <div class="io-dcol-hd">Outputs</div>
        ${outs||'<span class="io-item out" style="opacity:.3">—</span>'}
      </div>
    </div>`;
  }

  return `<div class="detail-preview">
    <div class="preview-lbl">Aperçu</div>${inner}</div>`;
}

/* ── Detail panel ────────────────────────────────────────────── */
function renderDetail(m) {
  if (!m) return '';
  const cc    = catColor(m.category);
  const usedBy = (RELS.used_by||{})[m.name] || [];
  const deps   = m.deps_req || [];
  const depsOpt = m.deps_opt || [];
  const scens  = m.scenarios || [];

  // Tables
  function tableRows(obj) {
    const entries = Object.entries(obj||{});
    if (!entries.length) return `<tr><td colspan="2" class="empty-note">Non documenté</td></tr>`;
    return entries.map(([k,v]) => {
      const vs = typeof v==='object' ? JSON.stringify(v) : String(v);
      return `<tr><td class="pk">${esc(k)}</td><td class="pv">${esc(vs)}</td></tr>`;
    }).join('');
  }

  // Relationships
  const relContent = (deps.length || usedBy.length || scens.length) ? `
    ${deps.length ? `<div class="rel-row"><span class="rel-lbl">Dépend de</span>
      ${deps.map(d=>`<span class="rel-chip rel-dep">${esc(d.split('(')[0].trim())}</span>`).join('')}
    </div>` : ''}
    ${usedBy.length ? `<div class="rel-row"><span class="rel-lbl">Utilisé par</span>
      ${usedBy.map(u=>`<span class="rel-chip rel-used" onclick="jumpToModule('${esc(u)}')" title="Ouvrir ${esc(u)}">${esc(u)}</span>`).join('')}
    </div>` : ''}
    ${scens.length ? `<div class="rel-row"><span class="rel-lbl">Scénarios</span>
      ${scens.map(s=>`<span class="rel-chip rel-scen">${esc(s)}</span>`).join('')}
    </div>` : ''}
  ` : `<p class="empty-note">Aucune relation documentée</p>`;

  // Deps section
  const depsContent = (deps.length||depsOpt.length) ? `<div class="deps-inner">
    ${deps.length ? `<div class="deps-grp"><div class="deps-grp-lbl">Required</div>
      <ul>${deps.map(d=>`<li><code>${esc(d)}</code></li>`).join('')}</ul></div>` : ''}
    ${depsOpt.length ? `<div class="deps-grp"><div class="deps-grp-lbl">Optional</div>
      <ul>${depsOpt.map(d=>`<li><code>${esc(d)}</code></li>`).join('')}</ul></div>` : ''}
  </div>` : `<p class="empty-note">Zéro dépendance externe</p>`;

  const api = (m.public_api||[]).filter(Boolean)
    .map(fn=>`<span class="api-fn">${esc(fn)}</span>`).join('');
  const tags = m.tags.map(t=>`<span class="tag">${esc(t)}</span>`).join('');

  return `<div class="detail-inner" style="--cc:${cc}">
    <div class="detail-hd">
      <div class="detail-title-row">
        ${catIcon(m.category)}
        <span class="detail-name">${esc(m.name)}</span>
        <span class="vbadge">v${esc(m.version)}</span>
        <span class="cat-pill" style="background:${cc}20;color:${cc}">${esc(catLabel(m.category))}</span>
      </div>
      <button class="close-btn" onclick="closeDetail()" title="Fermer (Esc)">
        <svg viewBox="0 0 16 16" width="14" height="14" fill="none">
          <line x1="3" y1="3" x2="13" y2="13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="13" y1="3" x2="3" y2="13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <p class="detail-desc">${esc(m.description)}</p>
    ${m.philosophy ? `<p class="philosophy">${esc(m.philosophy)}</p>` : ''}
    ${m.endpoint   ? `<div class="ep-row"><span class="ep-label">Endpoint</span><code>${esc(m.endpoint)}</code></div>` : ''}
    ${m.fn_sig     ? `<div class="sig-block">${esc(m.fn_sig)}</div>` : ''}
    ${api          ? `<div class="api-strip">${api}</div>` : ''}

    ${renderDetailPreview(m)}

    <div class="ds-list">
      <div class="ds">
        <div class="ds-hd">Inputs</div>
        <table class="pt"><thead><tr><th>Paramètre</th><th>Description</th></tr></thead>
          <tbody>${tableRows(m.inputs)}</tbody></table>
      </div>
      <div class="ds">
        <div class="ds-hd">Outputs</div>
        <table class="pt"><thead><tr><th>Clé</th><th>Valeur</th></tr></thead>
          <tbody>${tableRows(m.outputs)}</tbody></table>
      </div>
      <div class="ds">
        <div class="ds-hd">Relations</div>
        <div class="rel-inner">${relContent}</div>
      </div>
      <div class="ds">
        <div class="ds-hd">Dépendances</div>
        ${depsContent}
      </div>
      ${Object.keys(m.integration||{}).length ? `<div class="ds">
        <div class="ds-hd">Intégration</div>
        <table class="pt"><tbody>${tableRows(m.integration)}</tbody></table>
      </div>` : ''}
    </div>

    <div class="detail-footer">${tags}</div>
  </div>`;
}

/* ── Pipeline view ───────────────────────────────────────────── */
function renderPipeline() {
  const nodes = PIPE.map((stage, i) => {
    const cc  = stage.io ? '#374151' : catColor(stage.cat||'utility');
    const ico = stage.io ? '' : catIcon(stage.cat||'utility');
    const onClick = stage.io ? '' :
      `onclick="document.getElementById('vgrid').click(); openModuleByName('${esc(stage.id)}')"`;
    const arr = i < PIPE.length-1
      ? `<div class="pipe-arr"><svg viewBox="0 0 24 12" width="20" height="12" fill="none"><line x1="0" y1="6" x2="18" y2="6" stroke="currentColor" stroke-width="1.5"/><polyline points="12,2 18,6 12,10" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round"/></svg></div>`
      : '';

    return `<div class="pipe-node ${stage.io?'io-node':''}" style="--nc:${cc}" ${onClick} title="${esc(stage.id)}">
      ${ico ? `<div class="pipe-icon">${ico}</div>` : `<div style="height:22px"></div>`}
      <div class="pipe-label">${esc(stage.label)}</div>
    </div>${arr}`;
  }).join('');

  return `<div class="pipeline-view" id="pipelineView">
    <p style="color:var(--muted);font-size:12px;margin-bottom:16px">Pipeline de design — cliquez sur un nœud pour voir ses détails.</p>
    <div class="pipeline-scroll"><div class="pipeline-flow">${nodes}</div></div>
  </div>`;
}

/* ── Filter logic ────────────────────────────────────────────── */
function updateVisible() {
  const cards = document.querySelectorAll('.card');
  let n = 0;

  cards.forEach(card => {
    const cat    = card.dataset.cat;
    const name   = card.dataset.name.toLowerCase();
    const tags   = JSON.parse(card.dataset.tags||'[]');
    const descEl = card.querySelector('.card-desc');
    const desc   = descEl ? descEl.textContent.toLowerCase() : '';

    const matchCat    = state.cat === 'all' || cat === state.cat;
    const matchSearch = !state.search || name.includes(state.search) || desc.includes(state.search);
    const matchTags   = state.tags.size === 0 ||
      [...state.tags].some(t => tags.includes(t));

    const show = matchCat && matchSearch && matchTags;
    card.style.display = show ? '' : 'none';
    if (show) n++;
  });

  document.getElementById('resultsLabel').textContent = n + ' module' + (n>1?'s':'');
  document.getElementById('noResults').style.display  = n===0 ? 'block' : 'none';
  updateActiveStrip();
}

function updateActiveStrip() {
  const strip   = document.getElementById('activeStrip');
  const hasFilter = state.cat !== 'all' || state.tags.size > 0 || state.search;
  strip.classList.toggle('visible', hasFilter);

  const parts = [];
  if (state.cat !== 'all') parts.push(catLabel(state.cat));
  state.tags.forEach(t => parts.push(`#${t}`));
  if (state.search) parts.push(`"${state.search}"`);
  document.getElementById('activeFiltersText').textContent = parts.join('  ·  ');
}

function filterCat(btn, cat) {
  document.querySelectorAll('.cat-pill-btn').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  state.cat = cat;
  updateVisible();
}

function toggleTag(tag, el) {
  if (state.tags.has(tag)) {
    state.tags.delete(tag);
    el.classList.remove('active');
  } else {
    state.tags.add(tag);
    el.classList.add('active');
  }
  updateVisible();
}

function filterSearch(val) {
  state.search = val.toLowerCase().trim();
  updateVisible();
}

function clearAll() {
  state.cat    = 'all';
  state.tags   = new Set();
  state.search = '';
  document.querySelectorAll('.cat-pill-btn').forEach(p => p.classList.remove('active'));
  document.querySelector('[data-cat="all"]').classList.add('active');
  document.querySelectorAll('.tag-chip').forEach(c => c.classList.remove('active'));
  document.getElementById('searchBox').value = '';
  updateVisible();
}

/* ── Detail panel ────────────────────────────────────────────── */
function openDetail(idx) {
  state.sel = idx;
  const m   = MODS[idx];
  document.getElementById('detailContent').innerHTML = renderDetail(m);
  document.getElementById('detailPane').classList.add('open');
  document.querySelectorAll('.card').forEach(c => c.classList.remove('selected'));
  const card = document.querySelector(`[data-idx="${idx}"]`);
  if (card) card.classList.add('selected');
  document.getElementById('detailPane').scrollTop = 0;
}

function closeDetail() {
  state.sel = null;
  document.getElementById('detailPane').classList.remove('open');
  document.getElementById('detailContent').innerHTML = '';
  document.querySelectorAll('.card').forEach(c => c.classList.remove('selected'));
}

function jumpToModule(name) {
  const idx = MODS.findIndex(m => m.name === name);
  if (idx >= 0) {
    // Switch to grid view first
    if (state.view !== 'grid') setView('grid');
    openDetail(idx);
    const card = document.querySelector(`[data-idx="${idx}"]`);
    if (card) card.scrollIntoView({behavior:'smooth', block:'center'});
  }
}

function openModuleByName(name) {
  jumpToModule(name);
}

/* ── View toggle ─────────────────────────────────────────────── */
function setView(v) {
  state.view = v;
  document.getElementById('vgrid').classList.toggle('active', v==='grid');
  document.getElementById('vpipe').classList.toggle('active', v==='pipeline');
  document.getElementById('cardGrid').style.display    = v==='grid' ? '' : 'none';
  document.getElementById('noResults').style.display   = v==='grid' ? '' : 'none';
  const pv = document.getElementById('pipelineView');
  pv.classList.toggle('visible', v==='pipeline');
}

/* ── Init ────────────────────────────────────────────────────── */
function init() {
  // Render pipeline
  document.getElementById('pipelineMount').innerHTML = renderPipeline();

  // Render cards
  const grid = document.getElementById('cardGrid');
  grid.innerHTML = MODS.map((m, i) => renderCard(m, i)).join('') +
    `<div class="no-results" id="noResults">Aucun module trouvé pour ces filtres.</div>`;

  // Keyboard shortcuts
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeDetail();
    if ((e.ctrlKey||e.metaKey) && e.key === 'k') {
      e.preventDefault();
      document.getElementById('searchBox').focus();
    }
  });
}

document.addEventListener('DOMContentLoaded', init);
"""


# ─── HTML generation ──────────────────────────────────────────────────────────
def generate_html(modules: list[dict], rels: dict) -> str:
    now   = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(modules)

    # Category counts
    cat_counts: dict[str, int] = {}
    for m in modules:
        cat_counts[m["category"]] = cat_counts.get(m["category"], 0) + 1

    # Stats
    all_tags = sorted({t for m in modules for t in m["tags"]})

    # Category filter pills
    pills = '<button class="pill cat-pill-btn active" data-cat="all" onclick="filterCat(this,\'all\')" style="--pc:var(--accent)">Tous <span class="cnt">' + str(total) + "</span></button>"
    for cat, meta in CAT_META.items():
        if cat not in cat_counts:
            continue
        n, color, label = cat_counts[cat], meta["color"], meta["label"]
        icon = _CAT_ICONS.get(cat, "")
        pills += (
            f'<button class="pill cat-pill-btn" data-cat="{cat}"'
            f' onclick="filterCat(this,\'{cat}\')"'
            f' style="--pc:{color}">'
            f'{icon} {label} <span class="cnt">{n}</span></button>'
        )

    # Tag chips
    tag_chips = "".join(
        f'<button class="tag-chip" onclick="toggleTag(\'{t}\',this)">{t}</button>'
        for t in all_tags
    )

    # JSON data to embed
    js_modules = json.dumps(modules, ensure_ascii=False)
    js_rels    = json.dumps({"used_by": rels}, ensure_ascii=False)
    js_cat     = json.dumps(CAT_META, ensure_ascii=False)
    js_icons   = json.dumps(_CAT_ICONS, ensure_ascii=False)
    js_pipe    = json.dumps(PIPELINE_STAGES, ensure_ascii=False)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="fr">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>EURKAI — Module Explorer</title>\n"
        "<style>\n" + _CSS + "\n</style>\n"
        "</head>\n"
        "<body>\n\n"

        # Header
        '<header class="site-header">\n'
        '  <div class="logo-mark">EK</div>\n'
        '  <span class="logo-text">EURKAI</span>\n'
        '  <span class="header-divider">/</span>\n'
        '  <span class="header-section">Module Explorer</span>\n'
        '  <div class="header-spacer"></div>\n'
        '  <span class="header-meta">v2 · ' + now + '</span>\n'
        '  <div class="view-toggle" style="margin-left:12px">\n'
        '    <button class="vbtn active" id="vgrid" onclick="setView(\'grid\')">'
        '<svg viewBox="0 0 16 16" width="13" height="13" fill="none" style="margin-right:4px"><rect x="1" y="1" width="6" height="6" stroke="currentColor" stroke-width="1.5" rx="1"/><rect x="9" y="1" width="6" height="6" stroke="currentColor" stroke-width="1.5" rx="1"/><rect x="1" y="9" width="6" height="6" stroke="currentColor" stroke-width="1.5" rx="1"/><rect x="9" y="9" width="6" height="6" stroke="currentColor" stroke-width="1.5" rx="1"/></svg>'
        'Modules</button>\n'
        '    <button class="vbtn" id="vpipe" onclick="setView(\'pipeline\')">'
        '<svg viewBox="0 0 16 16" width="13" height="13" fill="none" style="margin-right:4px"><line x1="1" y1="8" x2="13" y2="8" stroke="currentColor" stroke-width="1.5"/><polyline points="9,4 13,8 9,12" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round"/></svg>'
        'Pipeline</button>\n'
        '  </div>\n'
        "</header>\n\n"

        # Shell
        '<div class="shell">\n'
        '<div class="main">\n'

        # Hero
        '<div class="hero">\n'
        '  <h1 class="hero-title">Modules <span>EURKAI</span></h1>\n'
        '  <p class="hero-sub">Bibliothèque de modules standalone — chaque module fait une chose, fait-la bien.</p>\n'
        '  <div class="stats-row">\n'
        f'    <div class="stat"><span class="stat-val">{total}</span><span class="stat-lbl">Modules</span></div>\n'
        f'    <div class="stat"><span class="stat-val">{len(cat_counts)}</span><span class="stat-lbl">Catégories</span></div>\n'
        f'    <div class="stat"><span class="stat-val">{len(all_tags)}</span><span class="stat-lbl">Tags</span></div>\n'
        '  </div>\n'
        '</div>\n\n'

        # Filter bar
        '<div class="filter-bar">\n'
        '  <div class="filter-row">\n'
        '    <input class="search-box" type="search" id="searchBox" placeholder="Rechercher…  ⌘K" oninput="filterSearch(this.value)"/>\n'
        '  </div>\n'
        '  <div class="filter-row">\n'
        + pills +
        '  </div>\n'
        '  <div class="filter-row tags-wrap">\n'
        '    <span class="tags-label">Tags</span>\n'
        + tag_chips +
        '  </div>\n'
        '  <div class="active-strip" id="activeStrip">\n'
        '    <span class="active-strip-label">Filtre actif :</span>\n'
        '    <span id="activeFiltersText" style="color:var(--accent);font-size:11px;font-family:var(--font-mono)"></span>\n'
        '    <button class="clear-all" onclick="clearAll()">Tout effacer</button>\n'
        '  </div>\n'
        '</div>\n\n'

        # Results bar
        '<div class="results-bar">\n'
        f'  <span class="results-label" id="resultsLabel">{total} modules</span>\n'
        '</div>\n\n'

        # Card grid
        '<div class="card-grid" id="cardGrid"></div>\n\n'

        # Pipeline mount
        '<div id="pipelineMount"></div>\n\n'

        '</div>\n'  # end .main

        # Detail pane
        '<aside class="detail-pane" id="detailPane">\n'
        '  <div id="detailContent"></div>\n'
        '</aside>\n'

        '</div>\n\n'  # end .shell

        # Data injection
        "<script>\n"
        "window.MODULES       = " + js_modules + ";\n"
        "window.RELATIONSHIPS = " + js_rels    + ";\n"
        "window.CAT_META      = " + js_cat     + ";\n"
        "window.CAT_ICONS     = " + js_icons   + ";\n"
        "window.PIPELINE      = " + js_pipe    + ";\n"
        "</script>\n\n"

        "<script>\n" + _JS_APP + "\n</script>\n\n"
        "</body>\n</html>"
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(description="EURKAI Module Explorer — générateur HTML v2")
    p.add_argument("--modules-dir", default=str(MODULES_DIR))
    p.add_argument("--output",      default=str(OUTPUT_HTML))
    p.add_argument("--json",        action="store_true", help="Dump JSON normalisé")
    args = p.parse_args()

    mdir   = Path(args.modules_dir)
    output = Path(args.output)

    print(f"  Scan : {mdir}")
    modules = scan_modules(mdir)
    print(f"  ✓ {len(modules)} modules")

    rels = build_relationships(modules)
    print(f"  ✓ Relations calculées ({sum(len(v) for v in rels.values())} liens)")

    if args.json:
        print(json.dumps({"modules": modules, "relationships": rels}, indent=2, ensure_ascii=False))

    html = generate_html(modules, rels)
    output.write_text(html, encoding="utf-8")
    print(f"  ✓ Explorer → {output}")
    print(f"  Ouvre : open '{output}'")


if __name__ == "__main__":
    main()
