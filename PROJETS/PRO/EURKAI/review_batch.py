#!/usr/bin/env python3
"""
review_batch.py — EURKAI Human Review Mode

Génère un batch de 8 pages (2 × 4 familles) pour inspection visuelle rapide.
Pipeline complet : visual_intent → color_palette → design_plan → validation
                → render → screenshot → vision_audit → auto_fix

Output : output/review/
    ecommerce/ event/ editorial/ saas/
    index.html
    review_summary.json

Usage :
    python review_batch.py
    python review_batch.py --no-screenshots
    python review_batch.py --family ecommerce
    python review_batch.py --count 2 --open
    python review_batch.py --quiet
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# API KEY
# ─────────────────────────────────────────────────────────────────────────────

def _load_api_key_if_missing() -> None:
    # Always prefer secrets.env (overrides a possibly-revoked env key)
    secrets = Path.home() / ".bigboff" / "secrets.env"
    if secrets.exists():
        with secrets.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY=") and not line.startswith("#"):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        os.environ["ANTHROPIC_API_KEY"] = val
                    break
        return
    # Fallback: keep existing env key if no secrets file
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pass  # no key available — VisionAudit will raise at instantiation

_load_api_key_if_missing()


# ─────────────────────────────────────────────────────────────────────────────
# PATH SETUP
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).parent
MODULES_DIR = SCRIPT_DIR / "MODULES"
REVIEW_DIR  = SCRIPT_DIR / "output" / "review"

sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(MODULES_DIR))
for _mod in sorted(MODULES_DIR.iterdir()):
    if _mod.is_dir() and not _mod.name.startswith(("_", ".")):
        sys.path.insert(0, str(_mod))


# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────

from pipeline import PipelineOrchestrator, PipelineResult  # noqa: E402

_HAS_SCREENSHOT = False
try:
    from screenshot_capture.src.screenshot_capture import ScreenshotCapture
    _HAS_SCREENSHOT = True
except ImportError:
    try:
        from screenshot_capture import ScreenshotCapture  # type: ignore
        _HAS_SCREENSHOT = True
    except ImportError:
        pass

_HAS_VISUAL_INTENT = False
try:
    from visual_intent_engine.src.visual_intent_engine import generate_visual_intent
    _HAS_VISUAL_INTENT = True
except ImportError:
    try:
        from visual_intent_engine import generate_visual_intent  # type: ignore
        _HAS_VISUAL_INTENT = True
    except ImportError:
        pass

_HAS_COLOR_PALETTE = False
try:
    from color_palette.src.color_palette import generate_palette as _gen_cp
    _HAS_COLOR_PALETTE = True
except ImportError:
    try:
        from color_palette import generate_palette as _gen_cp  # type: ignore
        _HAS_COLOR_PALETTE = True
    except ImportError:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# REVIEW BATCH DEFINITIONS — 8 pages, 4 familles × 2
# Seeds bien espacés pour diversité maximale
# ─────────────────────────────────────────────────────────────────────────────

REVIEW_PAGES: list[dict] = [

    # ── ECOMMERCE ──────────────────────────────────────────────────────────────
    {
        "family":        "ecommerce",
        "slug":          "ec_01",
        "project_name":  "Maison Rouge",
        "brief":         "Maroquinerie de luxe parisienne, sacs et accessoires faits main depuis 1923. "
                         "Savoir-faire traditionnel, cuirs nobles, collection automne-hiver. "
                         "Livraison internationale.",
        "seed":          11,
        "site_family":   "ecommerce_catalog",
        "harmony":       "complementary",
    },
    {
        "family":        "ecommerce",
        "slug":          "ec_02",
        "project_name":  "Volta Design",
        "brief":         "Mobilier design nordique contemporain, éditions limitées, matériaux durables. "
                         "Ateliers en Suède. Livraison France et Benelux sous 10 jours.",
        "seed":          157,
        "site_family":   "ecommerce_catalog",
        "harmony":       "monochromatic",
    },

    # ── EVENT ──────────────────────────────────────────────────────────────────
    {
        "family":        "event",
        "slug":          "ev_01",
        "project_name":  "Nuit Sonore",
        "brief":         "Festival de musique électronique underground, 3 scènes, 48h non-stop. "
                         "Lyon, juin 2026. Artistes internationaux, résidences, installations. "
                         "Billetterie en ligne.",
        "seed":          44,
        "site_family":   "event_campaign",
        "harmony":       "complementary",
    },
    {
        "family":        "event",
        "slug":          "ev_02",
        "project_name":  "Forum Climat",
        "brief":         "Conférence internationale sur la transition écologique et les solutions "
                         "industrielles. 2 jours, 80 intervenants, Paris La Défense. "
                         "Entreprises, institutions, ONG.",
        "seed":          213,
        "site_family":   "event_campaign",
        "harmony":       "analogous",
    },

    # ── EDITORIAL ──────────────────────────────────────────────────────────────
    {
        "family":        "editorial",
        "slug":          "ed_01",
        "project_name":  "Revue Matière",
        "brief":         "Magazine trimestriel indépendant dédié à la photographie documentaire "
                         "et au design contemporain. Tirage limité, abonnement digital et papier.",
        "seed":          78,
        "site_family":   "editorial_magazine",
        "harmony":       "monochromatic",
    },
    {
        "family":        "editorial",
        "slug":          "ed_02",
        "project_name":  "Studio Pellicule",
        "brief":         "Portfolio photographe mode et éditorial, Paris. Direction artistique, "
                         "campagnes publicité, éditoriaux presse internationale. "
                         "Représentation internationale.",
        "seed":          329,
        "site_family":   "studio_portfolio",
        "harmony":       "complementary",
    },

    # ── SAAS / PRODUCT ─────────────────────────────────────────────────────────
    {
        "family":        "saas",
        "slug":          "sa_01",
        "project_name":  "Synaptic",
        "brief":         "Plateforme analytique B2B en temps réel pour équipes data. "
                         "Dashboards, alertes, intégrations API. "
                         "Démarrage gratuit, plans Pro et Enterprise.",
        "seed":          55,
        "site_family":   "product_saas",
        "harmony":       "complementary",
    },
    {
        "family":        "saas",
        "slug":          "sa_02",
        "project_name":  "Fluxo",
        "brief":         "Outil de gestion de workflows et automatisation pour PME. "
                         "Intégration Slack, Notion, Google Workspace. "
                         "Zéro code, déploiement en 5 minutes.",
        "seed":          401,
        "site_family":   "product_saas",
        "harmony":       "analogous",
    },
]

FAMILY_LABELS = {
    "ecommerce": "E-Commerce",
    "event":     "Événement",
    "editorial": "Éditorial / Portfolio",
    "saas":      "SaaS / Produit",
}

FAMILY_COLORS = {
    "ecommerce": "#e67e22",
    "event":     "#8e44ad",
    "editorial": "#2c3e50",
    "saas":      "#2980b9",
}


# ─────────────────────────────────────────────────────────────────────────────
# LOCAL FILE SERVER — pour screenshot HTML
# ─────────────────────────────────────────────────────────────────────────────

import http.server


def _serve_html_file(html_path: Path) -> tuple[str, http.server.HTTPServer]:
    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(html_path.parent), **kwargs)
        def log_message(self, *a, **kw) -> None:
            pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}/{html_path.name}", srv


# ─────────────────────────────────────────────────────────────────────────────
# VISUAL INTENT + COLOR PALETTE — génération pour le meta uniquement
# (l'intégration complète dans pipeline.py = step suivant)
# ─────────────────────────────────────────────────────────────────────────────

def _build_visual_context(brief: str, family: str) -> dict:
    """
    Génère visual_intent + palette depuis le brief.
    Retourne un dict résumé pour meta.json et l'index de review.
    """
    out: dict = {
        "visual_intent":  None,
        "palette":        None,
        "intent_summary": {},
        "palette_summary": {},
    }

    if not _HAS_VISUAL_INTENT:
        return out

    try:
        intent = generate_visual_intent(brief=brief)
        out["visual_intent"] = intent
        ctx = intent.get("context", {})
        ad  = intent.get("art_direction", {})
        cb  = intent.get("composition_bias", {})
        out["intent_summary"] = {
            "product_type":      ctx.get("product_type", ""),
            "emotional_goal":    ctx.get("emotional_goal", ""),
            "brand_positioning": ctx.get("brand_positioning", ""),
            "style_family":      ad.get("style_family", ""),
            "intensity":         ad.get("intensity", ""),
            "dominance":         cb.get("dominance", ""),
            "density":           cb.get("density", ""),
        }

        if _HAS_COLOR_PALETTE:
            palette = _gen_cp(intent)
            out["palette"] = palette
            out["palette_summary"] = {
                "primary":        palette.get("primary", ""),
                "background":     palette.get("background", ""),
                "text_primary":   palette.get("text_primary", ""),
                "accent":         palette.get("accent", ""),
                "body_text_grade": palette.get("contrast_score", {}).get("body_text", ""),
            }
    except Exception:
        pass

    return out


# ─────────────────────────────────────────────────────────────────────────────
# REVIEW FLAGS — inférés depuis les données pipeline
# ─────────────────────────────────────────────────────────────────────────────

def _infer_review_flags(sample: dict, result: PipelineResult, palette_summary: dict) -> dict:
    """
    4 champs de review clairs, inférés objectivement depuis les données pipeline.
    Aucun score subjectif.
    """
    # structure_valid : plan validé (result.attempts > 0 et pas d'erreur de plan)
    structure_valid = (
        result.status == "success"
        and result.attempts <= 5
        and result.error is None
    )

    # readability_ok : final_score ≥ 70 (seuil design_validator)
    readability_ok = result.final_score >= 70 if result.final_score > 0 else None

    # recognizable_family : inféré depuis site_family déclaré (pas d'IA ici)
    recognizable_family = sample["site_family"].replace("_", " ")

    # variation_group : famille + seed → identification unique dans le batch
    variation_group = f"{sample['family']}·seed{sample['seed']}"

    return {
        "recognizable_family": recognizable_family,
        "readability_ok":      readability_ok,
        "structure_valid":     structure_valid,
        "variation_group":     variation_group,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PAGE RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_page(
    sample:             dict,
    enable_screenshots: bool,
    verbose:            bool = True,
) -> dict:
    family = sample["family"]
    slug   = sample["slug"]
    out_dir = REVIEW_DIR / family / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"\n  ▶  {sample['project_name']}  [{slug}]  seed={sample['seed']}")

    # ── Visual Intent + Palette (pour meta.json) ───────────────────────────────
    vc = _build_visual_context(sample["brief"], family)

    # ── Pipeline complet ──────────────────────────────────────────────────────
    orchestrator = PipelineOrchestrator(
        output_dir=REVIEW_DIR / family,
        enable_capture=True,
        enable_audit=True,
        enable_learning=False,
        verbose=verbose,
    )

    result: PipelineResult = orchestrator.run(
        brief=sample["brief"],
        project_name=slug,
        seed=sample["seed"],
        site_family=sample["site_family"],
        harmony=sample["harmony"],
    )

    record: dict = {
        "sample":          sample,
        "status":          result.status,
        "duration_ms":     result.duration_ms,
        "attempts":        result.attempts,
        "fix_iterations":  result.fix_iterations,
        "final_score":     result.final_score,
        "page_html":       None,
        "screenshot":      None,
        "design_plan":     None,
        "review_flags":    {},
        "intent_summary":  vc["intent_summary"],
        "palette_summary": vc["palette_summary"],
        "error":           result.error,
    }

    if result.status != "success":
        if verbose:
            print(f"  ✗  Pipeline failed: {result.error}")
        record["review_flags"] = _infer_review_flags(sample, result, {})
        return record

    # ── Copier HTML → page.html ───────────────────────────────────────────────
    src_html  = Path(result.output_path)
    page_html = out_dir / "page.html"
    shutil.copy2(src_html, page_html)
    record["page_html"] = f"{family}/{slug}/page.html"

    # ── Design plan summary ───────────────────────────────────────────────────
    plan_files = sorted(out_dir.glob("design_plan_*.json"))
    if plan_files:
        try:
            plan_data = json.loads(plan_files[-1].read_text(encoding="utf-8"))
            record["design_plan"] = {
                "layout_strategy": plan_data.get("layout_strategy"),
                "profile":         plan_data.get("brief_profile"),
                "section_types":   plan_data.get("section_types", []),
            }
        except Exception:
            pass

    # ── Review flags ──────────────────────────────────────────────────────────
    record["review_flags"] = _infer_review_flags(sample, result, vc["palette_summary"])

    # ── Screenshots — full_page + hero ────────────────────────────────────────
    # The pipeline's fix_loop already captured zones; find and copy them.
    captures_root = REVIEW_DIR / family / slug / "captures" / slug
    iter_dirs = sorted(captures_root.glob("iter_*")) if captures_root.exists() else []
    last_iter = iter_dirs[-1] if iter_dirs else None
    desktop_dir = last_iter / "desktop" if last_iter else None

    if desktop_dir and desktop_dir.exists():
        # full_page
        fp_src = desktop_dir / "full_page.png"
        if fp_src.exists():
            shutil.copy2(fp_src, out_dir / "screenshot.png")
            record["screenshot"] = f"{family}/{slug}/screenshot.png"
            if verbose:
                print(f"  📸  screenshot.png (full_page)")
        # hero
        hero_src = desktop_dir / "hero.png"
        if hero_src.exists():
            shutil.copy2(hero_src, out_dir / "hero.png")
            record["screenshot_hero"] = f"{family}/{slug}/hero.png"
            if verbose:
                print(f"  📸  hero.png")

    # Fallback: take a fresh full-page screenshot if pipeline captures missing
    if not record.get("screenshot") and enable_screenshots and _HAS_SCREENSHOT:
        screenshot_path = out_dir / "screenshot.png"
        url, srv = _serve_html_file(page_html)
        try:
            capturer = ScreenshotCapture(
                output_root=str(out_dir / "_captures"),
                default_viewport="desktop",
            )
            cr = capturer.capture_full_page(url=url, site=slug, page="review")
            if cr.ok and Path(cr.path).exists():
                shutil.copy2(cr.path, screenshot_path)
                record["screenshot"] = f"{family}/{slug}/screenshot.png"
                if verbose:
                    print(f"  📸  screenshot.png (fallback)")
            else:
                if verbose:
                    print(f"  ⚠️  screenshot failed: {getattr(cr, 'error', 'unknown')}")
        except Exception as exc:
            if verbose:
                print(f"  ⚠️  screenshot error: {exc}")
        finally:
            srv.shutdown()

    # ── meta.json ─────────────────────────────────────────────────────────────
    flags = record["review_flags"]
    _readability_pass = flags.get("readability_ok")  # True / False / None
    _readability_score = result.final_score
    meta = {
        "project_name":       sample["project_name"],
        "family":             family,
        "seed":               sample["seed"],
        "validation": {
            "valid": bool(flags.get("structure_valid")),
            "score": result.attempts,
        },
        "readability": {
            "pass":  _readability_pass,
            "score": _readability_score,
        },
        "fix_iterations":      result.fix_iterations,
        "design_plan_summary": record["design_plan"] or {},
        "visual_intent_summary": record["intent_summary"],
        "palette_summary":     record["palette_summary"],
        # extra context (non-spec but useful for index)
        "_slug":         slug,
        "_site_family":  sample["site_family"],
        "_brief":        sample["brief"],
        "_harmony":      sample["harmony"],
        "_duration_ms":  round(result.duration_ms),
        "_screenshot":   record.get("screenshot"),
        "_screenshot_hero": record.get("screenshot_hero"),
        "_page_html":    record.get("page_html"),
        "_generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if verbose:
        flags = record["review_flags"]
        rv = "✓" if flags.get("structure_valid") else "✗"
        rb = ("✓" if flags.get("readability_ok") else "✗") if flags.get("readability_ok") is not None else "—"
        print(f"  ✓  {sample['project_name']} — {round(result.duration_ms)}ms  "
              f"[structure:{rv} readability:{rb} fix:{result.fix_iterations}]")

    return record


# ─────────────────────────────────────────────────────────────────────────────
# INDEX HTML
# ─────────────────────────────────────────────────────────────────────────────

def _flag_badge(label: str, value, true_txt: str = "✓", false_txt: str = "✗") -> str:
    if value is None:
        return f'<span class="badge badge-na">{label}: —</span>'
    if value is True or value == true_txt:
        return f'<span class="badge badge-ok">{label}: {true_txt}</span>'
    return f'<span class="badge badge-fail">{label}: {false_txt}</span>'


def generate_index(records: list[dict], review_dir: Path) -> Path:
    by_family: dict[str, list[dict]] = {}
    for rec in records:
        fam = rec["sample"]["family"]
        by_family.setdefault(fam, []).append(rec)

    sections_html = ""
    for family, family_records in by_family.items():
        label = FAMILY_LABELS.get(family, family)
        color = FAMILY_COLORS.get(family, "#555")

        cards_html = ""
        for rec in family_records:
            s      = rec["sample"]
            ok     = rec["status"] == "success"
            flags  = rec.get("review_flags", {})
            intent = rec.get("intent_summary", {})
            pal    = rec.get("palette_summary", {})

            # Thumbnail — prefer hero, fallback to full_page
            hero_path = rec.get("screenshot_hero")
            full_path = rec.get("screenshot")
            thumb_src = hero_path or full_path
            if thumb_src:
                thumb = (f'<a href="{rec["page_html"] or "#"}" target="_blank">'
                         f'<img src="{thumb_src}" alt="{s["slug"]}" class="thumb"></a>')
            elif ok and rec.get("page_html"):
                thumb = (f'<a href="{rec["page_html"]}" target="_blank" class="no-thumb">'
                         f'Ouvrir la page →</a>')
            else:
                err = (rec.get("error") or "Échec")[:60]
                thumb = f'<div class="no-thumb-err">✗ {err}</div>'

            # Design plan
            plan_html = ""
            if rec.get("design_plan"):
                dp = rec["design_plan"]
                secs = ", ".join((dp.get("section_types") or [])[:4])
                plan_html = (f'<div class="plan-row">'
                             f'<span class="tag">{dp.get("layout_strategy","—")}</span>'
                             f'<span class="tag">{dp.get("profile","—")}</span>'
                             f'</div>'
                             f'<div class="plan-sections">{secs}</div>')

            # Review flags — 4 champs clés
            review_html = (
                f'<div class="review-flags">'
                + _flag_badge("structure",    flags.get("structure_valid"))
                + _flag_badge("readability",  flags.get("readability_ok"))
                + f'<span class="badge badge-info">fix: {rec.get("fix_iterations",0)}</span>'
                + f'<span class="badge badge-info">score: {rec.get("final_score",0)}</span>'
                + f'</div>'
            )

            # Visual intent summary
            intent_html = ""
            if intent:
                intent_html = (
                    f'<div class="intent-row">'
                    f'<span class="tag tag-intent">{intent.get("product_type","")}</span>'
                    f'<span class="tag tag-intent">{intent.get("emotional_goal","")}</span>'
                    f'<span class="tag tag-intent">{intent.get("brand_positioning","")}</span>'
                    f'</div>'
                )

            # Palette swatch
            palette_html = ""
            if pal.get("primary"):
                swatches = "".join(
                    f'<div class="swatch" style="background:{pal.get(k,"#888")}" title="{k}: {pal.get(k,"")}"></div>'
                    for k in ("primary", "background", "text_primary", "accent")
                    if pal.get(k)
                )
                grade = pal.get("body_text_grade", "")
                grade_cls = "grade-ok" if grade in ("AA","AAA") else "grade-fail"
                palette_html = (
                    f'<div class="palette-row">'
                    f'<div class="swatches">{swatches}</div>'
                    f'<span class="wcag-grade {grade_cls}">{grade or "—"}</span>'
                    f'</div>'
                )

            # Links — page / screenshot / hero / meta
            links_html = ""
            if ok and rec.get("page_html"):
                links_html += f'<a href="{rec["page_html"]}" target="_blank" class="link-btn">Page</a>'
            if rec.get("screenshot"):
                links_html += f'<a href="{rec["screenshot"]}" target="_blank" class="link-btn ghost">Full</a>'
            if rec.get("screenshot_hero"):
                links_html += f'<a href="{rec["screenshot_hero"]}" target="_blank" class="link-btn ghost">Hero</a>'
            links_html += f'<a href="{s["family"]}/{s["slug"]}/meta.json" target="_blank" class="link-btn ghost">meta</a>'

            # Variation group
            vg = flags.get("variation_group", "")

            dur = round(rec.get("duration_ms", 0))
            att = rec.get("attempts", "—")

            cards_html += f"""
      <div class="card {'card-ok' if ok else 'card-err'}">
        <div class="thumb-wrap">{thumb}</div>
        <div class="card-body">
          <div class="card-header">
            <span class="project-name">{s["project_name"]}</span>
            <span class="seed-badge">seed {s["seed"]}</span>
          </div>
          <div class="brief-text">{s["brief"][:110]}{"…" if len(s["brief"])>110 else ""}</div>
          {intent_html}
          {palette_html}
          {plan_html}
          {review_html}
          <div class="card-footer">
            <span class="vg-badge">{vg}</span>
            <div class="card-timing">
              <span>{dur}ms</span>
              <span>{att} attempt{"s" if att != 1 else ""}</span>
            </div>
            <div class="links">{links_html}</div>
          </div>
        </div>
      </div>"""

        sections_html += f"""
    <section class="family-section">
      <h2 class="family-title" style="--accent:{color}">{label}</h2>
      <div class="cards-grid">{cards_html}</div>
    </section>"""

    total   = len(records)
    success = sum(1 for r in records if r["status"] == "success")
    shots   = sum(1 for r in records if r.get("screenshot"))
    struct  = sum(1 for r in records if r.get("review_flags", {}).get("structure_valid"))
    read_ok = sum(1 for r in records if r.get("review_flags", {}).get("readability_ok") is True)
    ts      = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EURKAI — Review</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#0d0d0d;color:#e0e0e0;min-height:100vh}}

/* Header */
.site-header{{background:#141414;border-bottom:1px solid #252525;padding:20px 36px;display:flex;align-items:baseline;gap:20px;position:sticky;top:0;z-index:10}}
.site-header h1{{font-size:.95rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#fff}}
.header-sub{{font-size:.75rem;color:#555}}
.header-stats{{margin-left:auto;display:flex;gap:24px;font-size:.75rem;color:#666}}
.header-stats strong{{color:#e0e0e0}}

/* Legend */
.legend{{background:#141414;border-bottom:1px solid #1e1e1e;padding:10px 36px;display:flex;gap:20px;font-size:.7rem;color:#555}}
.legend-item{{display:flex;align-items:center;gap:6px}}
.legend .badge{{font-size:.65rem}}

/* Layout */
.main{{padding:36px}}
.family-section{{margin-bottom:52px}}
.family-title{{font-size:.7rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#fff;border-left:3px solid var(--accent,#555);padding-left:12px;margin-bottom:16px}}

.cards-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}}

/* Card */
.card{{background:#141414;border:1px solid #222;border-radius:6px;overflow:hidden;display:flex;flex-direction:column}}
.card-err{{opacity:.55;border-color:#3a1515}}

/* Thumb */
.thumb-wrap{{height:200px;overflow:hidden;background:#1a1a1a;position:relative;flex-shrink:0}}
.thumb-wrap img.thumb{{width:100%;height:100%;object-fit:cover;object-position:top;display:block;transition:transform .3s}}
.thumb-wrap:hover img.thumb{{transform:scale(1.03)}}
a.no-thumb,.no-thumb-err{{display:flex;align-items:center;justify-content:center;height:100%;font-size:.75rem;color:#444;text-decoration:none}}
a.no-thumb:hover{{color:#aaa}}
.no-thumb-err{{color:#6a2e2e;font-size:.7rem;padding:8px}}

/* Body */
.card-body{{padding:12px 14px;display:flex;flex-direction:column;gap:7px;flex:1}}
.card-header{{display:flex;align-items:baseline;gap:8px}}
.project-name{{font-size:.9rem;font-weight:600;color:#fff;flex:1}}
.seed-badge{{font-size:.62rem;color:#444;background:#1e1e1e;padding:2px 6px;border-radius:3px;white-space:nowrap}}
.brief-text{{font-size:.7rem;color:#666;line-height:1.5}}

/* Tags */
.intent-row{{display:flex;flex-wrap:wrap;gap:4px}}
.tag{{font-size:.62rem;padding:2px 7px;border-radius:3px;background:#1e1e1e;color:#888}}
.tag-intent{{background:#1a1e2e;color:#7a9aff}}
.plan-row{{display:flex;gap:4px;flex-wrap:wrap}}
.plan-sections{{font-size:.62rem;color:#555;margin-top:1px}}

/* Palette */
.palette-row{{display:flex;align-items:center;gap:8px}}
.swatches{{display:flex;gap:3px}}
.swatch{{width:16px;height:16px;border-radius:3px;border:1px solid #2a2a2a}}
.wcag-grade{{font-size:.6rem;font-weight:700;padding:2px 5px;border-radius:3px}}
.grade-ok{{background:#1a3a1a;color:#5cb85c}}
.grade-fail{{background:#3a1a1a;color:#d9534f}}

/* Review flags */
.review-flags{{display:flex;flex-wrap:wrap;gap:4px}}
.badge{{font-size:.62rem;padding:2px 7px;border-radius:3px;font-weight:600;white-space:nowrap}}
.badge-ok{{background:#1a3a1a;color:#5cb85c}}
.badge-fail{{background:#3a1a1a;color:#d9534f}}
.badge-na{{background:#222;color:#555}}
.badge-info{{background:#1e2030;color:#7a9aff}}

/* Footer */
.card-footer{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:auto;padding-top:4px}}
.vg-badge{{font-size:.6rem;color:#444;flex:1}}
.card-timing{{font-size:.62rem;color:#555;display:flex;gap:8px}}
.links{{display:flex;gap:6px;margin-left:auto}}
.link-btn{{font-size:.68rem;padding:3px 9px;border-radius:3px;background:#1e1e1e;color:#aaa;text-decoration:none;border:1px solid #2a2a2a}}
.link-btn:hover{{background:#2a2a2a;color:#fff}}
.link-btn.ghost{{background:transparent;color:#555}}
.link-btn.ghost:hover{{color:#aaa}}

/* Footer */
.site-footer{{border-top:1px solid #1e1e1e;padding:20px 36px;font-size:.7rem;color:#444;text-align:center}}
</style>
</head>
<body>
<header class="site-header">
  <h1>EURKAI Review</h1>
  <span class="header-sub">{ts}</span>
  <div class="header-stats">
    <span><strong>{success}</strong>/{total} pages</span>
    <span><strong>{shots}</strong> screenshots</span>
    <span><strong>{struct}</strong> structure ✓</span>
    <span><strong>{read_ok}</strong> readability ✓</span>
  </div>
</header>
<div class="legend">
  <span class="legend-item"><span class="badge badge-ok">structure: ✓</span> plan validé</span>
  <span class="legend-item"><span class="badge badge-ok">readability: ✓</span> score ≥ 70</span>
  <span class="legend-item"><span class="badge badge-info">fix: N</span> itérations auto-fix</span>
  <span class="legend-item"><span class="badge badge-info">score: N</span> lisibilité finale</span>
  <span class="legend-item"><span class="wcag-grade grade-ok">AA</span> WCAG AA palette</span>
</div>
<main class="main">
{sections_html}
</main>
<footer class="site-footer">
  EURKAI Review Batch — {total} pages — {ts}
</footer>
</body>
</html>"""

    idx = review_dir / "index.html"
    idx.write_text(html, encoding="utf-8")
    return idx


# ─────────────────────────────────────────────────────────────────────────────
# REVIEW SUMMARY JSON
# ─────────────────────────────────────────────────────────────────────────────

def generate_summary(records: list[dict], review_dir: Path) -> Path:
    total   = len(records)
    success = sum(1 for r in records if r["status"] == "success")
    shots   = sum(1 for r in records if r.get("screenshot"))
    struct  = sum(1 for r in records if r.get("review_flags", {}).get("structure_valid"))
    read_ok = sum(1 for r in records if r.get("review_flags", {}).get("readability_ok") is True)

    fix_counts = [r.get("fix_iterations", 0) for r in records if r["status"] == "success"]
    avg_fix = round(sum(fix_counts) / len(fix_counts), 2) if fix_counts else 0

    durations = [r.get("duration_ms", 0) for r in records if r["status"] == "success"]
    avg_dur = round(sum(durations) / len(durations)) if durations else 0

    by_family: dict = {}
    for rec in records:
        fam = rec["sample"]["family"]
        by_family.setdefault(fam, {"total": 0, "success": 0, "structure_ok": 0, "readability_ok": 0})
        by_family[fam]["total"] += 1
        if rec["status"] == "success":
            by_family[fam]["success"] += 1
        if rec.get("review_flags", {}).get("structure_valid"):
            by_family[fam]["structure_ok"] += 1
        if rec.get("review_flags", {}).get("readability_ok") is True:
            by_family[fam]["readability_ok"] += 1

    pages_with_issues = [
        {
            "slug":   r["sample"]["slug"],
            "name":   r["sample"]["project_name"],
            "family": r["sample"]["family"],
            "issue":  (
                "pipeline_failure" if r["status"] != "success"
                else "readability_fail" if r.get("review_flags", {}).get("readability_ok") is False
                else "fix_heavy" if r.get("fix_iterations", 0) >= 3
                else "score_low" if r.get("final_score", 100) < 70
                else None
            ),
        }
        for r in records
        if (
            r["status"] != "success"
            or r.get("review_flags", {}).get("readability_ok") is False
            or r.get("fix_iterations", 0) >= 3
            or r.get("final_score", 100) < 70
        )
    ]
    pages_with_issues = [p for p in pages_with_issues if p["issue"]]

    summary = {
        "generated_at":       datetime.now(timezone.utc).isoformat(),
        "total_pages":        total,
        "validation_pass":    struct,
        "readability_pass":   read_ok,
        "avg_fix_iterations": avg_fix,
        "pages_with_issues":  pages_with_issues,
        # Extended detail
        "_success_count":         success,
        "_screenshots_count":     shots,
        "_avg_duration_ms":       avg_dur,
        "_families":              by_family,
        "_pages": [
            {
                "slug":           r["sample"]["slug"],
                "family":         r["sample"]["family"],
                "project_name":   r["sample"]["project_name"],
                "seed":           r["sample"]["seed"],
                "validation":     {"valid": r["status"] == "success",
                                   "score": r.get("attempts", 0)},
                "readability":    {"pass":  r.get("review_flags", {}).get("readability_ok"),
                                   "score": r.get("final_score", 0)},
                "fix_iterations": r.get("fix_iterations", 0),
                "visual_intent":  r.get("intent_summary", {}),
                "palette":        r.get("palette_summary", {}),
            }
            for r in records
        ],
    }

    path = review_dir / "review_summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="EURKAI Human Review — génère un batch de 8 pages pour inspection visuelle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python review_batch.py
  python review_batch.py --no-screenshots
  python review_batch.py --family ecommerce
  python review_batch.py --count 1 --quiet
  python review_batch.py --open
        """,
    )
    parser.add_argument("--family",          metavar="NAME",  help="une seule famille (ecommerce|event|editorial|saas)")
    parser.add_argument("--count",           metavar="N", type=int, default=2, help="pages par famille (défaut: 2)")
    parser.add_argument("--no-screenshots",  action="store_true",   help="skip screenshots (plus rapide)")
    parser.add_argument("--open",            action="store_true",   help="ouvrir l'index à la fin")
    parser.add_argument("--quiet",           action="store_true",   help="moins de logs")
    args = parser.parse_args()

    verbose = not args.quiet
    enable_screenshots = not args.no_screenshots

    # Filtrer les pages selon --family et --count
    pages = REVIEW_PAGES
    if args.family:
        pages = [p for p in pages if p["family"] == args.family]
        if not pages:
            print(f"✗  Famille inconnue : {args.family}. Choix : ecommerce, event, editorial, saas")
            sys.exit(1)

    count = max(1, min(args.count, 3))
    by_family: dict[str, list[dict]] = {}
    for p in pages:
        by_family.setdefault(p["family"], []).append(p)
    pages = [p for fam_pages in by_family.values() for p in fam_pages[:count]]

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'─'*60}")
    print(f"  EURKAI Review Batch")
    print(f"{'─'*60}")
    print(f"  Pages            : {len(pages)}")
    print(f"  Familles         : {', '.join(sorted({p['family'] for p in pages}))}")
    print(f"  Screenshots      : {'oui' if enable_screenshots and _HAS_SCREENSHOT else 'non'}")
    print(f"  Visual Intent    : {'✓' if _HAS_VISUAL_INTENT else '✗ non disponible'}")
    print(f"  Color Palette    : {'✓' if _HAS_COLOR_PALETTE else '✗ non disponible'}")
    print(f"  Output           : {REVIEW_DIR}")
    print(f"{'─'*60}\n")

    t_start = time.time()
    records: list[dict] = []

    for page in pages:
        try:
            rec = run_page(page, enable_screenshots=enable_screenshots, verbose=verbose)
            records.append(rec)
        except Exception as exc:
            print(f"  ✗  {page['slug']}: fatal — {exc}")
            records.append({
                "sample":         page,
                "status":         "failure",
                "duration_ms":    0,
                "attempts":       0,
                "fix_iterations": 0,
                "final_score":    0,
                "page_html":      None,
                "screenshot":     None,
                "design_plan":    None,
                "review_flags":   {},
                "intent_summary": {},
                "palette_summary":{},
                "error":          str(exc),
            })

    # ── Générer les outputs ────────────────────────────────────────────────────
    idx_path     = generate_index(records, REVIEW_DIR)
    summary_path = generate_summary(records, REVIEW_DIR)

    elapsed = round((time.time() - t_start))
    success = sum(1 for r in records if r["status"] == "success")
    shots   = sum(1 for r in records if r.get("screenshot"))

    print(f"\n{'─'*60}")
    print(f"  Review terminé en {elapsed}s")
    print(f"  {success}/{len(records)} pages générées")
    if shots:
        print(f"  {shots} screenshots")
    print(f"  Index   : {idx_path}")
    print(f"  Summary : {summary_path}")
    print(f"{'─'*60}\n")

    if args.open:
        subprocess.run(["open", str(idx_path)], check=False)


if __name__ == "__main__":
    main()
