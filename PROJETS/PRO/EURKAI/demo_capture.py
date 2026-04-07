"""
demo_capture.py — Démo du module screenshot_capture.

Génère une landing page via generate_brand_charter.py,
la sert sur un port local, puis capture les zones audit.

Usage :
    python demo_capture.py
    python demo_capture.py --brief maison-calva --viewport mobile
    python demo_capture.py --url http://localhost:8765?brief=brut  # URL existante
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import sys
import threading
import time
from pathlib import Path

# ── Chemin vers le module ────────────────────────────────────────────────────
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE / "MODULES" / "screenshot_capture" / "src"))

from screenshot_capture import ScreenshotCapture, AUDIT_ZONES

OUTPUT_ROOT = _HERE / "output" / "captures"
DEMO_PORT   = 18765
DEMO_BRIEF  = "maison-calva"


# ── Serveur HTML minimal ─────────────────────────────────────────────────────

class _SinglePageHandler(http.server.BaseHTTPRequestHandler):
    html_content: bytes = b""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(self.html_content)))
        self.end_headers()
        self.wfile.write(self.html_content)

    def log_message(self, *args):
        pass  # silencieux


def _serve_html(html: str, port: int) -> http.server.HTTPServer:
    _SinglePageHandler.html_content = html.encode("utf-8")
    server = http.server.HTTPServer(("127.0.0.1", port), _SinglePageHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# ── Génération landing page ──────────────────────────────────────────────────

def _generate_html(brief_slug: str) -> str:
    from generate_brand_charter import generate_landing_page

    # Briefs de démo prédéfinis
    _briefs = {
        "maison-calva": {
            "name":  "Maison Calva",
            "brief": "Distillerie artisanale normande. Calvados haut de gamme, patrimoine familial depuis 1887.",
            "primary": "#8B4513",
        },
        "brut": {
            "name":  "BRUT Studio",
            "brief": "Studio de design brutaliste. Identité visuelle, typographie, systèmes graphiques.",
            "primary": "#111111",
        },
        "synaptic": {
            "name":  "Synaptic",
            "brief": "Plateforme SaaS d'analyse prédictive. IA, machine learning, tableaux de bord temps réel.",
            "primary": "#2563eb",
        },
        "bouton-dor": {
            "name":  "Le Bouton d'Or",
            "brief": "Boutique en ligne de mercerie fine. Boutons, tissus, accessoires couture haut de gamme.",
            "primary": "#c8a850",
        },
    }

    ctx = _briefs.get(brief_slug, _briefs["maison-calva"])
    print(f"  → Génération landing page : {ctx['name']}")

    html = generate_landing_page(
        project_name=ctx["name"],
        brief_text=ctx["brief"],
        dna=None,
        exploration=None,
        palette_output=None,
        render_seed=42,
        primary=ctx["primary"],
    )
    return html


# ── Capture principale ───────────────────────────────────────────────────────

def run_demo(
    brief_slug: str = DEMO_BRIEF,
    viewport: str = "desktop",
    url: str | None = None,
    zones: list[str] | None = None,
) -> None:
    print("\n── Screenshot Capture Demo ──────────────────────────────────────")

    server = None
    if url is None:
        # Générer HTML + serveur local
        html = _generate_html(brief_slug)
        server = _serve_html(html, DEMO_PORT)
        url = f"http://127.0.0.1:{DEMO_PORT}/"
        print(f"  → Serveur local : {url}")
        time.sleep(0.3)  # laisser le serveur démarrer

    site = brief_slug
    page = "landing"
    cap  = ScreenshotCapture(output_root=str(OUTPUT_ROOT))

    results = []

    # 1. Full page
    print(f"\n[1/3] Capture full page — {viewport}")
    r = cap.capture_full_page(url, site=site, page=page, viewport=viewport)
    results.append(r)
    _print_result(r)

    # 2. Viewport only
    print(f"\n[2/3] Capture viewport — {viewport}")
    r = cap.capture_viewport(url, site=site, page=page, viewport=viewport)
    results.append(r)
    _print_result(r)

    # 3. Zones audit
    target_zones = zones or ["nav", "hero", "first_section", "primary_cta", "final_cta"]
    print(f"\n[3/3] Zones audit : {target_zones}")
    for zone in target_zones:
        r = cap.capture_audit_zone(url, audit_name=zone, site=site, page=page, viewport=viewport)
        results.append(r)
        _print_result(r)

    # Résumé
    ok  = sum(1 for r in results if r.ok)
    err = sum(1 for r in results if not r.ok)
    print(f"\n── Résumé : {ok} OK / {err} erreurs ──")
    print(f"   Fichiers dans : {OUTPUT_ROOT / site / page / viewport}/\n")

    if server:
        server.shutdown()


def _print_result(r) -> None:
    status = "✓" if r.ok else "✗"
    label  = r.zone or "full"
    ms     = f"{r.duration_ms:.0f}ms"
    path   = Path(r.path).name if r.path else "—"
    err    = f"  ⚠ {r.error}" if r.error else ""
    print(f"  {status} [{label:<16}] {ms:>6}  {path}{err}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def _cli() -> None:
    ap = argparse.ArgumentParser(description="Démo screenshot_capture")
    ap.add_argument("--brief",    default=DEMO_BRIEF,
                    choices=["maison-calva", "brut", "synaptic", "bouton-dor"],
                    help="Brief de démo prédéfini")
    ap.add_argument("--viewport", default="desktop",
                    choices=["desktop", "tablet", "mobile"])
    ap.add_argument("--url",      default=None,
                    help="URL existante (bypass génération)")
    ap.add_argument("--zones",    nargs="*", default=None,
                    help="Zones audit à capturer (défaut : nav hero first_section primary_cta final_cta)")
    args = ap.parse_args()
    run_demo(
        brief_slug=args.brief,
        viewport=args.viewport,
        url=args.url,
        zones=args.zones,
    )


if __name__ == "__main__":
    _cli()
