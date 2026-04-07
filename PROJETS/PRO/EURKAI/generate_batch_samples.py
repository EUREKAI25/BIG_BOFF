#!/usr/bin/env python3
"""
generate_batch_samples.py — EURKAI Visual Batch Generator

Génère 12 pages (3 ecommerce / 3 event / 3 editorial / 3 saas) via le pipeline
complet, puis produit un index HTML de navigation visuelle.

Usage :
    python generate_batch_samples.py
    python generate_batch_samples.py --no-screenshots
    python generate_batch_samples.py --family ecommerce
    python generate_batch_samples.py --open
"""

from __future__ import annotations

import argparse
import http.server
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
# API KEY — chargement depuis secrets.env si absente de l'environnement
# ─────────────────────────────────────────────────────────────────────────────

def _load_api_key_if_missing() -> None:
    """Charge ANTHROPIC_API_KEY depuis ~/.bigboff/secrets.env si non définie."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    secrets = Path.home() / ".bigboff" / "secrets.env"
    if not secrets.exists():
        return
    with secrets.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY=") and not line.startswith("#"):
                val = line.split("=", 1)[1].strip()
                if val:
                    os.environ["ANTHROPIC_API_KEY"] = val
                break


_load_api_key_if_missing()


# ─────────────────────────────────────────────────────────────────────────────
# PATH SETUP — même que pipeline.py
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
MODULES_DIR = SCRIPT_DIR / "MODULES"
BATCH_DIR   = SCRIPT_DIR / "output" / "samples"

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


# ─────────────────────────────────────────────────────────────────────────────
# BATCH DEFINITIONS — 12 pages, 4 familles × 3
# ─────────────────────────────────────────────────────────────────────────────

SAMPLES: list[dict] = [

    # ── E-COMMERCE ──────────────────────────────────────────────────────────
    {
        "family":       "ecommerce",
        "slug":         "shop_01",
        "project_name": "Maison Rouge",
        "brief":        "Maroquinerie de luxe parisienne, sacs et accessoires faits main depuis 1923. Savoir-faire traditionnel, cuirs nobles, collection automne-hiver. Livraison internationale.",
        "seed":         11,
        "site_family":  "ecommerce_catalog",
        "harmony":      "complementary",
    },
    {
        "family":       "ecommerce",
        "slug":         "shop_02",
        "project_name": "Botanica Studio",
        "brief":        "Boutique de plantes rares et soins botaniques. Plus de 300 espèces sélectionnées, conseils d'entretien personnalisés, envois express partout en Europe.",
        "seed":         22,
        "site_family":  "ecommerce_catalog",
        "harmony":      "analogous",
    },
    {
        "family":       "ecommerce",
        "slug":         "shop_03",
        "project_name": "Volta Design",
        "brief":        "Mobilier design nordique contemporain. Éditions limitées, matériaux durables et sourcés. Ateliers en Suède, livraison France et Benelux sous 10 jours.",
        "seed":         33,
        "site_family":  "ecommerce_catalog",
        "harmony":      "monochromatic",
    },

    # ── ÉVÉNEMENT ────────────────────────────────────────────────────────────
    {
        "family":       "event",
        "slug":         "event_01",
        "project_name": "Signal Festival",
        "brief":        "Festival de design et technologie, 3 jours à Lyon, juin 2026. 80 intervenants, conférences, ateliers pratiques, expositions installations. Billets disponibles.",
        "seed":         44,
        "site_family":  "event_campaign",
        "harmony":      "complementary",
    },
    {
        "family":       "event",
        "slug":         "event_02",
        "project_name": "Nuit Graphique",
        "brief":        "Exposition nocturne d'art graphique contemporain. Vernissage à Paris, novembre 2026. 40 artistes internationaux, éditions limitées, galerie ouverte de 19h à minuit.",
        "seed":         55,
        "site_family":  "event_campaign",
        "harmony":      "triadic",
    },
    {
        "family":       "event",
        "slug":         "event_03",
        "project_name": "Forge Summit",
        "brief":        "Conférence internationale pour fondateurs de startups deeptech. Bordeaux, octobre 2026. 500 participants, 3 tracks thématiques, pitchs et networking investisseurs.",
        "seed":         66,
        "site_family":  "event_campaign",
        "harmony":      "analogous",
    },

    # ── ÉDITORIAL ────────────────────────────────────────────────────────────
    {
        "family":       "editorial",
        "slug":         "editorial_01",
        "project_name": "Materia Magazine",
        "brief":        "Magazine trimestriel de design, architecture et matière. Audience internationale, 12 000 abonnés. Contributions de studios reconnus, portraits de créateurs, essais critiques.",
        "seed":         77,
        "site_family":  "editorial_magazine",
        "harmony":      "complementary",
    },
    {
        "family":       "editorial",
        "slug":         "editorial_02",
        "project_name": "Sillon Revue",
        "brief":        "Revue indépendante sur l'agriculture régénératrice et les nouvelles ruralités. Publication semestrielle, enquêtes de terrain, photographie documentaire, tirage papier.",
        "seed":         88,
        "site_family":  "editorial_magazine",
        "harmony":      "analogous",
    },
    {
        "family":       "editorial",
        "slug":         "editorial_03",
        "project_name": "Spectre Publication",
        "brief":        "Publication critique art et culture pop underground. Parution bi-mensuelle, tirage limité 2000 exemplaires, distribution indépendante. Ton libre, graphisme expérimental.",
        "seed":         99,
        "site_family":  "editorial_magazine",
        "harmony":      "monochromatic",
    },

    # ── SAAS / PRODUIT ───────────────────────────────────────────────────────
    {
        "family":       "saas",
        "slug":         "saas_01",
        "project_name": "Orbit Platform",
        "brief":        "Plateforme de planification de projets pour équipes distribuées. API-first, intégrations Slack, Notion, Linear. B2B, 3 niveaux d'abonnement, essai gratuit 14 jours.",
        "seed":         101,
        "site_family":  "product_saas",
        "harmony":      "complementary",
    },
    {
        "family":       "saas",
        "slug":         "saas_02",
        "project_name": "Klar Finance",
        "brief":        "Outil d'analyse financière pour PME. Tableaux de bord temps réel, prévisions trésorerie, connexion bancaire automatique. SaaS, abonnement mensuel, données sécurisées.",
        "seed":         112,
        "site_family":  "product_saas",
        "harmony":      "analogous",
    },
    {
        "family":       "saas",
        "slug":         "saas_03",
        "project_name": "Mesh Data",
        "brief":        "Infrastructure de données pour équipes data science. Déploiement cloud multi-région, versioning modèles ML, monitoring en production, pipelines no-code.",
        "seed":         123,
        "site_family":  "product_saas",
        "harmony":      "triadic",
    },
]

FAMILY_LABELS = {
    "ecommerce": "E-commerce",
    "event":     "Événement",
    "editorial": "Éditorial",
    "saas":      "SaaS / Produit",
}

FAMILY_COLORS = {
    "ecommerce": "#c0392b",
    "event":     "#8e44ad",
    "editorial": "#2c3e50",
    "saas":      "#2980b9",
}


# ─────────────────────────────────────────────────────────────────────────────
# LOCAL FILE SERVER — pour screenshot du HTML sauvegardé
# ─────────────────────────────────────────────────────────────────────────────

def _serve_html_file(html_path: Path) -> tuple[str, http.server.HTTPServer]:
    """Sert html_path depuis un serveur HTTP local sur un port aléatoire."""
    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(html_path.parent), **kwargs)
        def log_message(self, *a, **kw) -> None:
            pass  # silence

    srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}/{html_path.name}", srv


# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_sample(
    sample:             dict,
    enable_screenshots: bool,
    verbose:            bool = True,
) -> dict:
    """
    Exécute le pipeline complet pour un sample.
    Retourne un dict de résultat pour l'index.
    """
    family = sample["family"]
    slug   = sample["slug"]

    # Dossier de sortie pour cette page
    out_dir = BATCH_DIR / family / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"\n  ▶  {sample['project_name']}  [{slug}]  seed={sample['seed']}")

    # ── Pipeline complet ──────────────────────────────────────────────────────
    orchestrator = PipelineOrchestrator(
        output_dir=BATCH_DIR / family,
        enable_capture=True,    # pipeline complet — capture si Playwright dispo
        enable_audit=True,      # pipeline complet — audit si API key dispo
        enable_learning=False,  # pas utile pour batch review
        verbose=verbose,
    )

    result: PipelineResult = orchestrator.run(
        brief=sample["brief"],
        project_name=slug,           # slug = project_name pour avoir out_dir/slug/
        seed=sample["seed"],
        site_family=sample["site_family"],
        harmony=sample["harmony"],
    )

    record: dict = {
        "sample":        sample,
        "status":        result.status,
        "duration_ms":   result.duration_ms,
        "attempts":      result.attempts,
        "fix_iterations": result.fix_iterations,
        "final_score":   result.final_score,
        "page_html":     None,
        "screenshot":    None,
        "design_plan":   None,
        "error":         result.error,
    }

    if result.status != "success":
        print(f"  ✗  Pipeline failed: {result.error}")
        return record

    # ── Copier le HTML → page.html ────────────────────────────────────────────
    src_html  = Path(result.output_path)
    page_html = out_dir / "page.html"
    shutil.copy2(src_html, page_html)
    record["page_html"] = f"{family}/{slug}/page.html"

    # ── Lire le design plan sauvegardé ────────────────────────────────────────
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

    # ── Screenshot page entière ───────────────────────────────────────────────
    if enable_screenshots and _HAS_SCREENSHOT:
        screenshot_path = out_dir / "screenshot.png"
        url, srv = _serve_html_file(page_html)
        try:
            capturer = ScreenshotCapture(
                output_root=str(out_dir / "_captures"),
                default_viewport="desktop",
            )
            cr = capturer.capture_full_page(url=url, site=slug, page="preview")
            if cr.ok and Path(cr.path).exists():
                shutil.copy2(cr.path, screenshot_path)
                record["screenshot"] = f"{family}/{slug}/screenshot.png"
                if verbose:
                    print(f"  📸  Screenshot saved: {screenshot_path.name}")
            else:
                print(f"  ⚠️  Screenshot failed: {getattr(cr, 'error', 'unknown')}")
        except Exception as exc:
            print(f"  ⚠️  Screenshot error: {exc}")
        finally:
            srv.shutdown()

    # ── Sauvegarder meta.json ─────────────────────────────────────────────────
    meta = {
        "project_name":  sample["project_name"],
        "slug":          slug,
        "family":        family,
        "site_family":   sample["site_family"],
        "brief":         sample["brief"],
        "seed":          sample["seed"],
        "harmony":       sample["harmony"],
        "design_plan":   record["design_plan"],
        "pipeline": {
            "status":         result.status,
            "attempts":       result.attempts,
            "fix_iterations": result.fix_iterations,
            "final_score":    result.final_score,
            "duration_ms":    round(result.duration_ms),
        },
        "screenshot":    record["screenshot"],
        "generated_at":  datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if verbose:
        print(f"  ✓  {sample['project_name']} — {round(result.duration_ms)}ms")

    return record


# ─────────────────────────────────────────────────────────────────────────────
# INDEX HTML GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_index(records: list[dict], batch_dir: Path) -> Path:
    """Génère output/samples/index.html listant toutes les pages produites."""

    # Regrouper par famille
    by_family: dict[str, list[dict]] = {}
    for rec in records:
        fam = rec["sample"]["family"]
        by_family.setdefault(fam, []).append(rec)

    # ── Générer les cards HTML ────────────────────────────────────────────────
    sections_html = ""
    for family, family_records in by_family.items():
        label = FAMILY_LABELS.get(family, family)
        color = FAMILY_COLORS.get(family, "#555")

        cards_html = ""
        for rec in family_records:
            s      = rec["sample"]
            status = rec["status"]
            ok     = status == "success"

            # Thumbnail
            if rec["screenshot"]:
                thumb = f'<a href="{rec["page_html"]}" target="_blank"><img src="{rec["screenshot"]}" alt="screenshot {s["slug"]}" class="thumb"></a>'
            elif ok and rec["page_html"]:
                thumb = f'<a href="{rec["page_html"]}" target="_blank" class="no-thumb">Ouvrir la page →</a>'
            else:
                thumb = '<div class="no-thumb-err">✗ Échec</div>'

            # Design plan summary
            plan_html = ""
            if rec.get("design_plan"):
                dp = rec["design_plan"]
                sections_list = ", ".join((dp.get("section_types") or [])[:4])
                plan_html = f"""
                <div class="plan-info">
                  <span class="plan-tag">{dp.get("layout_strategy", "—")}</span>
                  <span class="plan-tag">{dp.get("profile", "—")}</span>
                  <div class="plan-sections">{sections_list}</div>
                </div>"""

            # Pipeline info
            dur  = round(rec.get("duration_ms", 0))
            att  = rec.get("attempts", "—")
            fix  = rec.get("fix_iterations", 0)
            scr  = rec.get("final_score", 0)

            status_badge = (
                f'<span class="badge ok">✓ {dur}ms</span>'
                if ok else
                f'<span class="badge err">✗ {rec.get("error", "error")[:40]}</span>'
            )

            brief_short = s["brief"][:120] + ("…" if len(s["brief"]) > 120 else "")

            links_html = ""
            if ok and rec["page_html"]:
                links_html += f'<a href="{rec["page_html"]}" target="_blank" class="link-btn">Ouvrir page</a>'
            if ok:
                links_html += f'<a href="{s["family"]}/{s["slug"]}/meta.json" target="_blank" class="link-btn ghost">meta.json</a>'

            cards_html += f"""
        <div class="card {'card-ok' if ok else 'card-err'}">
          <div class="thumb-wrap">{thumb}</div>
          <div class="card-body">
            <div class="card-header">
              <span class="project-name">{s["project_name"]}</span>
              <span class="seed-badge">seed {s["seed"]}</span>
            </div>
            <div class="brief-text">{brief_short}</div>
            {plan_html}
            <div class="card-meta">
              <span>tentatives: {att}</span>
              <span>fix: {fix}</span>
              <span>score: {scr}</span>
            </div>
            <div class="card-footer">
              {status_badge}
              <div class="links">{links_html}</div>
            </div>
          </div>
        </div>"""

        sections_html += f"""
      <section class="family-section">
        <h2 class="family-title" style="border-left-color:{color}">{label}</h2>
        <div class="cards-grid">
          {cards_html}
        </div>
      </section>"""

    # ── Stats globales ────────────────────────────────────────────────────────
    total   = len(records)
    success = sum(1 for r in records if r["status"] == "success")
    shots   = sum(1 for r in records if r.get("screenshot"))
    ts      = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EURKAI — Batch Visual Review</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0 }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #0e0e0e;
    color: #e0e0e0;
    min-height: 100vh;
  }}

  /* ── Header ── */
  .site-header {{
    background: #161616;
    border-bottom: 1px solid #2a2a2a;
    padding: 24px 40px;
    display: flex;
    align-items: baseline;
    gap: 24px;
  }}
  .site-header h1 {{
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: #fff;
  }}
  .header-sub {{
    font-size: .8rem;
    color: #666;
  }}
  .header-stats {{
    margin-left: auto;
    font-size: .8rem;
    color: #888;
    display: flex;
    gap: 20px;
  }}
  .header-stats strong {{ color: #e0e0e0 }}

  /* ── Layout ── */
  .main {{ padding: 40px }}

  .family-section {{ margin-bottom: 56px }}

  .family-title {{
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: .15em;
    text-transform: uppercase;
    color: #fff;
    border-left: 3px solid #555;
    padding-left: 12px;
    margin-bottom: 20px;
  }}

  .cards-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }}

  /* ── Card ── */
  .card {{
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }}
  .card-err {{ opacity: .6; border-color: #4a1a1a }}

  /* Thumbnail */
  .thumb-wrap {{
    height: 220px;
    overflow: hidden;
    background: #1e1e1e;
    position: relative;
  }}
  .thumb-wrap img.thumb {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top;
    display: block;
    transition: transform .3s ease;
  }}
  .thumb-wrap:hover img.thumb {{ transform: scale(1.02) }}

  a.no-thumb, .no-thumb-err {{
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    font-size: .8rem;
    color: #555;
    text-decoration: none;
  }}
  a.no-thumb:hover {{ color: #aaa }}
  .no-thumb-err {{ color: #7a3333 }}

  /* Card body */
  .card-body {{
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
  }}

  .card-header {{
    display: flex;
    align-items: baseline;
    gap: 8px;
  }}
  .project-name {{
    font-size: .95rem;
    font-weight: 600;
    color: #fff;
    flex: 1;
  }}
  .seed-badge {{
    font-size: .65rem;
    color: #555;
    background: #1e1e1e;
    padding: 2px 6px;
    border-radius: 3px;
    white-space: nowrap;
  }}

  .brief-text {{
    font-size: .75rem;
    color: #888;
    line-height: 1.5;
  }}

  .plan-info {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }}
  .plan-tag {{
    font-size: .65rem;
    color: #aaa;
    background: #1e1e1e;
    border: 1px solid #333;
    padding: 2px 6px;
    border-radius: 3px;
  }}
  .plan-sections {{
    font-size: .65rem;
    color: #555;
    width: 100%;
    margin-top: 2px;
  }}

  .card-meta {{
    display: flex;
    gap: 12px;
    font-size: .65rem;
    color: #555;
  }}

  .card-footer {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: auto;
    padding-top: 6px;
    border-top: 1px solid #222;
  }}

  .badge {{
    font-size: .65rem;
    padding: 2px 7px;
    border-radius: 3px;
  }}
  .badge.ok  {{ background: #1a3a1a; color: #6abf6a }}
  .badge.err {{ background: #3a1a1a; color: #bf6a6a }}

  .links {{ display: flex; gap: 6px }}
  .link-btn {{
    font-size: .65rem;
    padding: 3px 8px;
    border-radius: 3px;
    text-decoration: none;
    background: #2a2a2a;
    color: #ccc;
    transition: background .15s;
  }}
  .link-btn:hover  {{ background: #3a3a3a }}
  .link-btn.ghost  {{ background: transparent; border: 1px solid #333; color: #666 }}
  .link-btn.ghost:hover {{ border-color: #555; color: #aaa }}

  /* ── Footer ── */
  .site-footer {{
    padding: 24px 40px;
    border-top: 1px solid #1e1e1e;
    font-size: .7rem;
    color: #444;
  }}

  @media (max-width: 900px) {{
    .cards-grid {{ grid-template-columns: repeat(2, 1fr) }}
    .main {{ padding: 20px }}
  }}
  @media (max-width: 600px) {{
    .cards-grid {{ grid-template-columns: 1fr }}
  }}
</style>
</head>
<body>

<header class="site-header">
  <h1>EURKAI — Batch Visual Review</h1>
  <span class="header-sub">Généré le {ts}</span>
  <div class="header-stats">
    <span><strong>{success}/{total}</strong> pages générées</span>
    <span><strong>{shots}</strong> screenshots</span>
    <span><strong>{len(by_family)}</strong> familles</span>
  </div>
</header>

<main class="main">
  {sections_html}
</main>

<footer class="site-footer">
  EURKAI Design Pipeline — Batch generation {ts}
</footer>

</body>
</html>"""

    index_path = batch_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="EURKAI — Batch Visual Generator (12 pages, 4 familles)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python generate_batch_samples.py
  python generate_batch_samples.py --no-screenshots
  python generate_batch_samples.py --family ecommerce
  python generate_batch_samples.py --open
        """,
    )
    parser.add_argument(
        "--family",
        choices=["ecommerce", "event", "editorial", "saas"],
        default=None,
        help="Générer uniquement cette famille (défaut: toutes)",
    )
    parser.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Ne pas prendre de screenshots (plus rapide)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Ouvrir l'index dans le navigateur après génération",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Logs minimaux",
    )
    args = parser.parse_args()

    enable_screenshots = not args.no_screenshots
    verbose            = not args.quiet

    # Filtrer les samples
    samples = SAMPLES
    if args.family:
        samples = [s for s in SAMPLES if s["family"] == args.family]
        if not samples:
            print(f"Aucun sample pour la famille '{args.family}'.")
            sys.exit(1)

    BATCH_DIR.mkdir(parents=True, exist_ok=True)

    # ── Banner ────────────────────────────────────────────────────────────────
    print()
    print("=" * 64)
    print("  EURKAI — Batch Visual Generator")
    print("=" * 64)
    print(f"  Pages         : {len(samples)}")
    print(f"  Screenshots   : {'oui (Playwright requis)' if enable_screenshots else 'désactivé'}")
    print(f"  Playwright    : {'✓ disponible' if _HAS_SCREENSHOT else '✗ non disponible — sans screenshots'}")
    print(f"  Sortie        : {BATCH_DIR}")
    print("=" * 64)

    t_start  = time.time()
    records  = []
    success  = 0
    failures = 0

    for i, sample in enumerate(samples, 1):
        fam   = sample["family"]
        label = FAMILY_LABELS.get(fam, fam)

        print(f"\n{'─' * 64}")
        print(f"  [{i}/{len(samples)}]  {label}  →  {sample['slug']}")
        print(f"{'─' * 64}")

        try:
            rec = run_sample(
                sample=sample,
                enable_screenshots=enable_screenshots,
                verbose=verbose,
            )
            records.append(rec)
            if rec["status"] == "success":
                success += 1
            else:
                failures += 1
        except Exception as exc:
            print(f"  ✗  Exception inattendue : {exc}")
            import traceback
            traceback.print_exc()
            records.append({
                "sample":  sample,
                "status":  "failure",
                "error":   str(exc),
                "page_html":  None,
                "screenshot": None,
                "design_plan": None,
                "duration_ms": 0,
                "attempts": 0,
                "fix_iterations": 0,
                "final_score": 0,
            })
            failures += 1

    # ── Index HTML ────────────────────────────────────────────────────────────
    print(f"\n{'─' * 64}")
    print("  Génération de l'index HTML...")
    index_path = generate_index(records, BATCH_DIR)
    print(f"  ✓  Index : {index_path}")

    # ── Rapport final ─────────────────────────────────────────────────────────
    elapsed = round(time.time() - t_start)
    shots   = sum(1 for r in records if r.get("screenshot"))

    print()
    print("=" * 64)
    print("  RAPPORT FINAL")
    print("=" * 64)
    print(f"  Succès    : {success}/{len(samples)}")
    print(f"  Échecs    : {failures}")
    print(f"  Screenshots : {shots}/{success}")
    print(f"  Durée totale : {elapsed}s")
    print(f"  Index     : {index_path}")
    print("=" * 64)

    if args.open and index_path.exists():
        print("\n  Ouverture de l'index...")
        subprocess.run(["open", str(index_path)], check=False)


if __name__ == "__main__":
    main()
