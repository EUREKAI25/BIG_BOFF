#!/usr/bin/env python3
"""
design_tester_server.py
───────────────────────
Serveur de test du pipeline EURKAI — génère une landing page unique à chaque requête.

Usage :
    python design_tester_server.py          # port 8765
    python design_tester_server.py 9000     # port custom

Chaque GET "/" lance le pipeline complet :
    brief aléatoire → design_dna_resolver → color_psychology_engine
    → palette_generator → design_exploration_engine → theme_generator
    → generate_landing_page()

Le résultat est renvoyé directement dans le navigateur.
Recharger la page = nouveau site.
"""

from __future__ import annotations

import sys
import json
import random
import time
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# ── Path setup (même logique que generate_brand_charter.py) ───────────────────

SCRIPT_DIR  = Path(__file__).parent
MODULES_DIR = SCRIPT_DIR / "MODULES"

for _mod in sorted(MODULES_DIR.iterdir()):
    if _mod.is_dir() and not _mod.name.startswith(("_", ".")):
        sys.path.insert(0, str(_mod))

# ── Import pipeline ────────────────────────────────────────────────────────────

# On importe directement depuis generate_brand_charter pour réutiliser
# toutes les fonctions du pipeline sans dupliquer de code.
sys.path.insert(0, str(SCRIPT_DIR))
from generate_brand_charter import (
    step_dna,
    step_psychology,
    step_palette,
    step_explore,
    step_build_style_dna,
    step_theme,
    generate_landing_page,
    site_type_resolver,
    PAGE_FAMILIES,
)

# ── Générateur de briefs aléatoires ───────────────────────────────────────────

BRIEFS = [
    # ── EDITORIAL / LUXURY ─────────────────────────────────────────────────────
    {
        "name": "Maison Calva",
        "brief": (
            "Maison Calva est un magazine de design et d'art de vivre haut de gamme. "
            "Typographie serif élégante, noir et ivoire, layouts asymétriques. "
            "Audience : architectes, collectionneurs, amateurs de culture. "
            "Ton : raffiné, contemplatif, sans compromis."
        ),
    },
    {
        "name": "Verbe",
        "brief": (
            "Verbe est une revue littéraire indépendante. "
            "Design épuré, encre sur papier, grandes marges. "
            "Couleurs : noir profond, crème chaud, rouge discret. "
            "Audience : lecteurs exigeants, auteurs, éditeurs. "
            "Valeurs : littérature, lenteur, profondeur."
        ),
    },
    {
        "name": "Studio Dix",
        "brief": (
            "Studio Dix est un cabinet d'architecture reconnu pour ses projets résidentiels. "
            "Esthétique : béton, bois, lumière naturelle. "
            "Couleurs : gris ardoise, blanc cassé, bois naturel. "
            "Tone : premium, sérieux, minimaliste."
        ),
    },
    {
        "name": "Gallerie Onze",
        "brief": (
            "Gallerie Onze est une galerie d'art contemporain parisienne. "
            "Black & white avec un accent couleur par exposition. "
            "Audience : collectionneurs, curateurs, institutions culturelles. "
            "Valeurs : avant-garde, dialogue, excellence."
        ),
    },
    {
        "name": "Noir de Vigne",
        "brief": (
            "Noir de Vigne est un domaine viticole de prestige en Bourgogne. "
            "Packaging d'exception, couleurs : bordeaux, or, lin. "
            "Tone : patrimoine, terroir, excellence artisanale. "
            "Audience : sommeliers, connaisseurs, restaurants étoilés."
        ),
    },
    # ── PLAYFUL / LIFESTYLE ────────────────────────────────────────────────────
    {
        "name": "Zestly",
        "brief": (
            "Zestly est une app de recettes saines et colorées pour millennials actifs. "
            "Couleurs vives, illustrations friendly, typo ronde. "
            "Valeurs : joie, simplicité, nutrition colorée. "
            "Audience : 25-40 ans urbains, sportifs du dimanche."
        ),
    },
    {
        "name": "Bouton d'Or",
        "brief": (
            "Bouton d'Or est une marque de cosmétiques naturels pour enfants. "
            "Couleurs : jaune soleil, vert herbe, blanc doux. "
            "Valeurs : sécurité, nature, fun. "
            "Ton : chaleureux, rassurant, joyeux."
        ),
    },
    {
        "name": "Confetti Club",
        "brief": (
            "Confetti Club organise des événements festifs et workshops créatifs. "
            "Identité visuelle : explosions de couleur, formes géométriques, énergie. "
            "Audience : équipes d'entreprise, particuliers, 28-45 ans. "
            "Valeurs : célébration, créativité, souvenirs."
        ),
    },
    {
        "name": "Pétale Studio",
        "brief": (
            "Pétale Studio propose des cours de poterie et céramique en ligne. "
            "Esthétique : terre cuite, vert sauge, beige chaud. "
            "Tone : artisanal, doux, communauté bienveillante. "
            "Audience : femmes 30-55 ans, créatives, cherchant un ancrage."
        ),
    },
    {
        "name": "Sunny Routes",
        "brief": (
            "Sunny Routes est une agence de voyages durables pour familles aventurières. "
            "Couleurs : orange mandarine, vert forêt, bleu océan. "
            "Valeurs : aventure responsable, souvenirs, famille. "
            "Ton : enthousiaste, bienveillant, inspirant."
        ),
    },
    # ── TECH / SAAS ────────────────────────────────────────────────────────────
    {
        "name": "Nexvault",
        "brief": (
            "Nexvault est une plateforme B2B de sécurité des données pour PME. "
            "Design technique, sombre, futuriste. "
            "Couleurs : bleu nuit, cyan électrique, gris métal. "
            "Audience : DSI, RSSI, équipes IT. "
            "Valeurs : confiance, performance, protection."
        ),
    },
    {
        "name": "Klaara",
        "brief": (
            "Klaara est un SaaS de gestion de projets pour agences créatives. "
            "Interface claire, moderne, épurée. "
            "Couleurs : indigo, blanc, accents violet. "
            "Audience : chefs de projet, directeurs artistiques, studios. "
            "Valeurs : clarté, efficacité, collaboration."
        ),
    },
    {
        "name": "Synaptic",
        "brief": (
            "Synaptic est une API d'intelligence artificielle pour développeurs. "
            "Brand : sombre, tech, minimal. "
            "Couleurs : noir absolu, vert terminal, gris code. "
            "Audience : engineers, CTOs, startups AI-first. "
            "Valeurs : puissance, précision, développeurs d'abord."
        ),
    },
    {
        "name": "Luminary",
        "brief": (
            "Luminary est une plateforme d'analytique marketing temps réel. "
            "Visualisations de données, dashboards lumineux sur fond sombre. "
            "Couleurs : marine profond, or, blanc. "
            "Audience : CMOs, growth hackers, équipes data. "
            "Valeurs : insights, vitesse, décision."
        ),
    },
    {
        "name": "Archon",
        "brief": (
            "Archon est un OS pour flottes de drones industriels. "
            "Identité visuelle : brutale, technique, sans ornement. "
            "Couleurs : anthracite, orange sécurité, blanc froid. "
            "Audience : industriels, logisticiens, défense civile. "
            "Valeurs : fiabilité, contrôle, puissance brute."
        ),
    },
    # ── CREATIVE STUDIO / BOLD ─────────────────────────────────────────────────
    {
        "name": "Fractal Lab",
        "brief": (
            "Fractal Lab est un studio de design expérimental et d'art génératif. "
            "Esthétique : maximaliste, géométrique, couleurs saturées. "
            "Audience : galeries, marques avant-garde, festivals. "
            "Valeurs : expérimentation, rupture, beauté étrange."
        ),
    },
    {
        "name": "Ondes",
        "brief": (
            "Ondes est un label de musique électronique underground. "
            "Visuel : noir total, typographie condensée, néon violet. "
            "Audience : clubbers, DJs, curateurs musicaux. "
            "Valeurs : nuit, transe, communauté souterraine."
        ),
    },
    {
        "name": "Brut",
        "brief": (
            "Brut est une agence de communication qui refuse les conventions. "
            "Design brutalist : grilles brisées, typographie massive, contraste brutal. "
            "Couleurs : noir, blanc, rouge agressif. "
            "Audience : marques disruptives, startups qui veulent se démarquer. "
            "Valeurs : audace, provocation, impact."
        ),
    },
    {
        "name": "Volcan Studio",
        "brief": (
            "Volcan Studio crée des expériences immersives et installations artistiques. "
            "Identité : rouge magma, noir volcanique, matières brutes. "
            "Audience : festivals, musées, marques luxe expérientiel. "
            "Valeurs : puissance sensorielle, émotion, transformation."
        ),
    },
    # ── PREMIUM CRAFT / ORGANIC ────────────────────────────────────────────────
    {
        "name": "Forges du Nord",
        "brief": (
            "Forges du Nord fabrique des couteaux artisanaux forgés à la main. "
            "Esthétique : métal, bois sombre, cuir naturel. "
            "Couleurs : gris fer, marron foncé, bronze. "
            "Valeurs : savoir-faire, durée, authenticité. "
            "Audience : chefs cuisiniers, collectionneurs d'outils, artisans."
        ),
    },
    {
        "name": "Terra Rossa",
        "brief": (
            "Terra Rossa produit des céramiques artisanales portugaises. "
            "Couleurs : terracotta, blanc calcaire, ocre. "
            "Valeurs : tradition, main, matière. "
            "Audience : décorateurs, boutiques lifestyle, amateurs de craft."
        ),
    },
]

# ── Wrapper HTML avec bouton de rechargement ───────────────────────────────────

_HARMONY_LABELS = {
    "complementary": "Complément.", "analogous": "Analogue",
    "triadic": "Triade", "monochromatic": "Mono", "minimal": "Minimal",
    "bw_light": "N/B ☀", "bw_dark": "N/B ☾",
}

_PAGE_LABELS = {
    "landing": "Landing",
    "about":   "About",
    "product": "Produit",
    "minimal": "Minimal",
}
_ALL_PAGES = list(_PAGE_LABELS.keys())

_FAMILY_LABELS = {k: v["label"] for k, v in PAGE_FAMILIES.items()}
_ALL_FAMILIES  = list(PAGE_FAMILIES.keys())

def _wrap_with_reload_bar(html: str, elapsed: float, brief_name: str, brief_text: str,
                          harmony: str = "complementary", available_harmonies=None,
                          brief_idx=None, page_type: str = "landing",
                          site_family: str = "brand_landing",
                          auto_family: str = "") -> str:
    """Injecte une barre fixe de contrôle dans la landing page générée."""
    idx_param = f"&idx={brief_idx}" if brief_idx is not None else ""

    # Boutons harmonie
    harmony_buttons = ""
    if available_harmonies:
        for h in available_harmonies:
            active = "background:#fff;color:#000" if h == harmony else "background:rgba(255,255,255,.15);color:#ccc"
            label = _HARMONY_LABELS.get(h, h)
            harmony_buttons += f'<a href="/?harmony={h}&page={page_type}&family={site_family}{idx_param}" style="padding:4px 10px;border-radius:4px;font-size:11px;font-weight:600;text-decoration:none;{active}">{label}</a>'
        harmony_bar = f'<div style="display:flex;gap:4px;align-items:center">{harmony_buttons}</div>'
    else:
        harmony_bar = ""

    # Boutons type de page
    page_buttons = ""
    for pt in _ALL_PAGES:
        active_p = "background:#4ade80;color:#000" if pt == page_type else "background:rgba(255,255,255,.12);color:#bbb"
        page_buttons += f'<a href="/?page={pt}&harmony={harmony}&family={site_family}{idx_param}" style="padding:4px 10px;border-radius:4px;font-size:11px;font-weight:600;text-decoration:none;{active_p}">{_PAGE_LABELS[pt]}</a>'
    page_bar = f'<div style="display:flex;gap:3px;align-items:center;border-left:1px solid rgba(255,255,255,.15);padding-left:10px">{page_buttons}</div>'

    # Boutons famille (2 rangées compactes)
    fam_buttons = ""
    for fam in _ALL_FAMILIES:
        active_f = "background:#f59e0b;color:#000" if fam == site_family else "background:rgba(255,255,255,.10);color:#aaa"
        short = _FAMILY_LABELS[fam].split(" / ")[0]  # "Brand", "Édito", etc.
        auto_marker = " ●" if fam == auto_family and fam == site_family else ""
        fam_buttons += f'<a href="/?family={fam}&page={page_type}&harmony={harmony}{idx_param}" style="padding:3px 8px;border-radius:3px;font-size:10px;font-weight:600;text-decoration:none;white-space:nowrap;{active_f}">{short}{auto_marker}</a>'
    family_bar = f'<div style="display:flex;gap:3px;flex-wrap:wrap;align-items:center">{fam_buttons}</div>'

    bar = f"""
<style>
  #__tester_bar {{
    position: fixed; top: 0; left: 0; right: 0; z-index: 99999;
    background: rgba(0,0,0,0.88);
    backdrop-filter: blur(12px);
    display: flex; flex-direction: column; align-items: flex-start;
    padding: 6px 16px 5px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 13px; color: #fff;
    border-bottom: 1px solid rgba(255,255,255,0.12);
    box-sizing: border-box;
    gap: 5px;
  }}
  #__tester_bar .row1 {{
    display: flex; align-items: center; gap: 10px; width: 100%;
    overflow: hidden;
  }}
  #__tester_bar .row2 {{
    display: flex; align-items: center; gap: 4px; flex-wrap: wrap;
    padding-top: 2px; border-top: 1px solid rgba(255,255,255,.08); width: 100%;
  }}
  #__tester_bar button {{
    background: #fff; color: #000;
    border: none; border-radius: 6px;
    padding: 4px 12px; font-size: 12px; font-weight: 600;
    cursor: pointer; white-space: nowrap;
    transition: opacity .15s;
  }}
  #__tester_bar button:hover {{ opacity: .8; }}
  #__tester_bar .badge {{
    background: rgba(255,255,255,0.15);
    border-radius: 4px; padding: 2px 7px;
    font-size: 10px; color: #ccc; white-space: nowrap;
  }}
  #__tester_bar .brief-name {{
    font-weight: 700; font-size: 13px;
    max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }}
  #__tester_bar .brief-snippet {{
    flex: 1; color: #aaa; font-size: 11px;
    overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
  }}
  #__tester_bar .elapsed {{
    color: #888; font-size: 11px; white-space: nowrap;
  }}
  body {{ padding-top: 80px !important; }}
</style>
<div id="__tester_bar">
  <div class="row1">
    <button onclick="location.reload()">↻</button>
    <span class="badge">EURKAI</span>
    <span class="brief-name">{brief_name}</span>
    {page_bar}
    {harmony_bar}
    <span class="brief-snippet">{brief_text[:100].replace('"', '&quot;')}…</span>
    <span class="elapsed">{elapsed:.1f}s</span>
  </div>
  <div class="row2">
    <span style="font-size:10px;color:#666;white-space:nowrap;margin-right:4px">Site type :</span>
    {family_bar}
  </div>
</div>
<script>
  // Keyboard shortcut : R ou Espace = reload
  document.addEventListener('keydown', function(e) {{
    if ((e.key === 'r' || e.key === 'R' || e.key === ' ') && !['INPUT','TEXTAREA'].includes(e.target.tagName)) {{
      e.preventDefault();
      location.reload();
    }}
  }});
</script>
"""
    # Injecter juste après <body>
    if "<body" in html:
        idx = html.index("<body")
        end = html.index(">", idx) + 1
        return html[:end] + "\n" + bar + html[end:]
    return bar + html


# ── Handler HTTP ───────────────────────────────────────────────────────────────

class PipelineHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Log concis
        print(f"  {self.address_string()} {fmt % args}")

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path not in ("/", "/generate"):
            self.send_error(404, "Not Found")
            return

        # Choisir un brief aléatoire (ou forcé via ?idx=N)
        params = parse_qs(parsed.query)
        if "idx" in params:
            idx = int(params["idx"][0]) % len(BRIEFS)
            brief_data = BRIEFS[idx]
        else:
            idx = None
            brief_data = random.choice(BRIEFS)

        project_name = brief_data["name"]
        brief_text   = brief_data["brief"]

        print(f"\n  ► Projet : {project_name}")
        print(f"    Brief  : {brief_text[:80]}…")

        t0 = time.time()
        render_seed = random.randint(0, 999999)
        harmony      = params.get("harmony", ["complementary"])[0]
        page_type    = params.get("page", ["landing"])[0]
        family_param = params.get("family", [""])[0]
        if page_type not in _ALL_PAGES:
            page_type = "landing"

        print(f"    Page   : {page_type} | Harmony : {harmony}")

        try:
            # ── Pipeline complet ───────────────────────────────────────────────
            dna           = step_dna(brief_text, project_name)
            rec           = step_psychology(dna)
            palette_out   = step_palette(dna, rec)
            exploration   = step_explore(dna)
            style_dna     = step_build_style_dna(dna, palette_out, rec)
            preset, css   = step_theme(style_dna)

            # Auto-détection famille si pas forcée via ?family=
            auto_family = site_type_resolver(brief_text, dna)
            site_family = family_param if family_param in _ALL_FAMILIES else auto_family
            print(f"    Family : {site_family} (auto={auto_family})")

            _ALL_HARMONIES = ["complementary","analogous","triadic","monochromatic","minimal"]
            available_harmonies = [
                h for h in _ALL_HARMONIES
                if palette_out and getattr(palette_out.palette_set, h, None) is not None
            ] if palette_out else []
            # Ajouter faux N/B (light + dark) si bw_variant disponible
            if palette_out and getattr(palette_out.palette_set, "black_and_white_variant", None):
                available_harmonies += ["bw_light", "bw_dark"]

            html = generate_landing_page(
                project_name=project_name,
                brief_text=brief_text,
                dna=dna,
                exploration=exploration,
                preset=preset,
                css=css,
                render_seed=render_seed,
                palette_output=palette_out,
                harmony=harmony,
                page_type=page_type,
                site_family=site_family,
            )

            elapsed = time.time() - t0
            print(f"    ✅ {elapsed:.2f}s")

            # Injecter la barre de contrôle
            html = _wrap_with_reload_bar(
                html, elapsed, project_name, brief_text,
                harmony=harmony, available_harmonies=available_harmonies,
                brief_idx=idx if idx is not None else None,
                page_type=page_type,
                site_family=site_family, auto_family=auto_family,
            )

        except Exception as exc:
            elapsed = time.time() - t0
            tb = traceback.format_exc()
            print(f"    ❌ Erreur : {exc}")
            print(tb)
            html = _error_page(project_name, brief_text, str(exc), tb, elapsed)

        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def _error_page(name: str, brief: str, error: str, tb: str, elapsed: float) -> str:
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Erreur pipeline — {name}</title>
  <style>
    body {{ font-family: monospace; background: #0a0a0a; color: #f44; margin: 0; padding: 40px; }}
    h1 {{ color: #fff; font-size: 20px; }}
    .brief {{ color: #888; font-size: 12px; margin: 8px 0 24px; }}
    .error {{ color: #f88; font-size: 15px; margin-bottom: 16px; }}
    pre {{ background: #111; color: #ccc; padding: 24px; border-radius: 8px;
           font-size: 12px; overflow-x: auto; line-height: 1.5; }}
    .reload {{ display: inline-block; margin-top: 24px; background: #fff; color: #000;
               padding: 8px 20px; border-radius: 6px; text-decoration: none;
               font-weight: bold; cursor: pointer; }}
  </style>
</head>
<body>
  <h1>Erreur pipeline ({elapsed:.2f}s)</h1>
  <div class="brief">Projet : {name} — {brief[:100]}…</div>
  <div class="error">{error}</div>
  <pre>{tb}</pre>
  <a class="reload" onclick="location.reload()">↻ Réessayer</a>
</body>
</html>"""


# ── Entrée ─────────────────────────────────────────────────────────────────────

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = HTTPServer(("", port), PipelineHandler)
    print(f"""
╔══════════════════════════════════════════════╗
║    EURKAI Design Tester — Pipeline Python    ║
╠══════════════════════════════════════════════╣
║  URL  :  http://localhost:{port:<5}              ║
║  {len(BRIEFS)} briefs disponibles                     ║
║  Recharger la page = nouveau site            ║
║  Ctrl+C pour arrêter                         ║
╚══════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Serveur arrêté.")


if __name__ == "__main__":
    main()
