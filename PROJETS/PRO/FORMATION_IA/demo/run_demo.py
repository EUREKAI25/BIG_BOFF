"""
run_demo.py — Démo FORMATION_IA interactive
Génère une formation complète et un rendu HTML interactif (parcours LMS).

Le rendu HTML utilise exclusivement des CSS custom properties pour les couleurs.
Le thème visuel final appartient au projet consommateur, pas au module.

Usage :
    python run_demo.py
    → output_demo.json  (structure + thème résolu)
    → output_demo.html  (mini-LMS interactif, thème injecté via CSS vars)

Injection de thème :
    Passer un dict "theme" dans DEMO_INPUT pour surcharger le thème par défaut.
    Seuls les tokens fournis sont appliqués — les autres gardent leurs valeurs par défaut.
"""

import json
import sys
from pathlib import Path

EURKAI_CORE = Path(__file__).parent.parent.parent / "EURKAI" / "CODE" / "eurkai_core"
sys.path.insert(0, str(EURKAI_CORE))

from modules.training_generator import run

DEMO_INPUT = {
    "topic": "Utiliser l'IA dans son travail quotidien",
    "level": "beginner",
    "objectives": [
        "Comprendre ce qu'est l'IA et ce qu'elle peut faire concrètement",
        "Rédiger des prompts efficaces dès le premier jour",
        "Identifier des cas d'usage immédiatement applicables",
        "Adopter les bonnes pratiques de sécurité",
    ],
    "logics":  ["editorial", "technical", "operational", "strategic"],
    "format":  "standard",
    "catalog": None,
    # "theme": {                        # décommenter pour tester un thème custom
    #     "mode": "custom",
    #     "tokens": {
    #         "primary":    "#0f172a",
    #         "accent":     "#6366f1",
    #         "background": "#f8fafc",
    #         "surface":    "#ffffff",
    #         "border":     "#e2e8f0",
    #         "radius":     "12px",
    #     }
    # }
}

OUT_DIR = Path(__file__).parent


def main():
    print("▶ Génération de la formation interactive...")
    result = run(DEMO_INPUT)

    if result["status"] != "success":
        print(f"✗ Erreur : {result.get('error')}")
        sys.exit(1)

    training = result["training"]
    mode     = result["meta"]["mode"]
    theme    = result["meta"]["theme"]
    prog     = training.get("progression", {})

    json_path = OUT_DIR / "output_demo.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON  → {json_path}")

    html_path = OUT_DIR / "output_demo.html"
    html      = _render_html(training, mode, theme)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ HTML  → {html_path}")

    print(f"\n{'─'*60}")
    print(f"  {training['training_title']}")
    print(f"  Niveau    : {training['level']}  |  Durée : {training.get('estimated_duration','')}")
    print(f"  Mode      : {mode}  |  Thème : {theme['mode']}")
    print(f"  Structure : {prog.get('total_chapters')} chapitres / "
          f"{prog.get('total_lessons')} leçons / {prog.get('total_tasks')} tâches")
    print(f"{'─'*60}\n")


# ── Theme helpers ─────────────────────────────────────────────────────────────

def _darken(hex_color, factor=0.88):
    """Assombrit un hex color d'un facteur. Retour gracieux si échec."""
    try:
        h = hex_color.lstrip('#')
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return '#{:02x}{:02x}{:02x}'.format(
                int(r * factor), int(g * factor), int(b * factor)
            )
    except Exception:
        pass
    return hex_color


def _hex_to_rgb(hex_color):
    """Retourne 'r, g, b' pour usage dans rgba(). Retour gracieux si échec."""
    try:
        h = hex_color.lstrip('#')
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f"{r}, {g}, {b}"
    except Exception:
        pass
    return "0, 0, 0"


_DEFAULT_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"


def _build_css_vars(theme):
    """Génère le bloc de CSS custom properties à injecter dans :root {}.
    Seuls les tokens du thème (fourni ou default) sont injectés.
    Les couleurs sémantiques fixes sont dans le template statique."""
    t        = theme["tokens"]
    primary  = t.get("primary", "#1a1a2e")
    accent   = t.get("accent",  "#e94560")
    font     = t.get("font_family", _DEFAULT_FONT)

    lines = [
        f"  /* ── Tokens injectés par training_generator (thème : {theme['mode']}) ── */",
        f"  --color-primary:     {primary};",
        f"  --color-primary-rgb: {_hex_to_rgb(primary)};",
        f"  --color-nav:         {_darken(primary, 0.88)};",
        f"  --color-accent:      {accent};",
        f"  --color-accent-rgb:  {_hex_to_rgb(accent)};",
        f"  --color-accent-dark: {_darken(accent, 0.82)};",
        f"  --color-bg:          {t.get('background', '#f0f2f5')};",
        f"  --color-surface:     {t.get('surface', '#ffffff')};",
        f"  --color-text:        {t.get('text', '#2d3436')};",
        f"  --color-muted:       {t.get('muted', '#636e72')};",
        f"  --color-border:      {t.get('border', '#e0e3e8')};",
        f"  --radius:            {t.get('radius', '8px')};",
        f"  --font:              {font};",
    ]
    return "\n".join(lines)


# ── Rendu HTML ─────────────────────────────────────────────────────────────────

def _render_html(training, mode, theme):
    training_json = json.dumps(training, ensure_ascii=False)
    training_json = training_json.replace("</script>", "<\\/script>")

    css_vars = _build_css_vars(theme)
    html = HTML_TEMPLATE.replace("/*THEME_VARS*/", css_vars)
    html = html.replace("/*TRAINING_DATA*/", training_json)
    return html


# ── Template HTML ─────────────────────────────────────────────────────────────
# Règle : aucune couleur hardcodée hors du bloc :root {}.
# Toutes les couleurs de marque passent par var(--color-xxx).
# Les couleurs sémantiques (types de blocs pédagogiques) sont fixes par conception.

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Formation — Parcours interactif</title>
<style>
:root {
/*THEME_VARS*/

  /* ── Couleurs sémantiques — fixes, non thémables ──────────────────────────
     Ces couleurs encodent le TYPE de contenu pédagogique (theory, warning…).
     Elles ne font pas partie de l'identité visuelle du projet consommateur. */
  --sem-success:    #27ae60;
  --sem-success-bg: #e8f8f1;
  --sem-success-bd: #b2dfdb;
  --sem-warning:    #f39c12;
  --sem-purple:     #8e44ad;
  --sem-teal:       #16a085;
  --sem-blue:       #2980b9;

  /* Type blocs contenu */
  --sem-theory-bg:  #e8f4fd;
  --sem-example-bg: #e8f8f1;
  --sem-method-bg:  #f3e8fd;
  --sem-warn-bg:    #fef9e7;
  --sem-check-bg:   #e8f5f4;

  /* Bloc prompt (dark code style) */
  --sem-code-bg:       #1e1e2e;
  --sem-code-text:     #cdd3de;
  --sem-code-muted:    #a8b3cf;
  --sem-code-btn:      #3a3a5c;
  --sem-code-btn-hover:#4a4a6c;
  --sem-code-border:   #555;
  --sem-code-title:    #e2e8f0;

  /* UI états fixes */
  --sem-locked-icon:   #bbb;
  --sem-locked-bg:     #f5f5f5;
  --sem-locked-fg:     #bbb;

  /* Type badges tâches */
  --sem-tt-question-bg:    #dbeafe;
  --sem-tt-question-fg:    #1d4ed8;
  --sem-tt-exercise-bg:    #ede9fe;
  --sem-tt-exercise-fg:    #7c3aed;
  --sem-tt-prompt-bg:      #1e1e2e;
  --sem-tt-prompt-fg:      #a78bfa;
  --sem-tt-assess-bg:      #fef3c7;
  --sem-tt-assess-fg:      #d97706;
  --sem-tt-checklist-bg:   #d1fae5;
  --sem-tt-checklist-fg:   #059669;

  /* Layout */
  --sidebar-w: 280px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--font);
  background: var(--color-bg);
  color: var(--color-text);
}

/* ── Header ── */
#header {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  background: var(--color-primary); color: var(--color-surface);
  display: flex; align-items: center; gap: 1.5rem;
  padding: .8rem 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,.3);
}
#header-title {
  font-size: 1rem; font-weight: 700; flex: 1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
#header-progress { display: flex; align-items: center; gap: .75rem; min-width: 220px; }
#progress-bar-wrap {
  flex: 1; height: 8px; background: rgba(255,255,255,.15);
  border-radius: var(--radius); overflow: hidden;
}
#progress-bar-fill {
  height: 100%; background: var(--color-accent); border-radius: var(--radius);
  transition: width .4s ease;
}
#progress-text { font-size: .8rem; color: rgba(255,255,255,.8); white-space: nowrap; }

/* ── Layout ── */
#layout { display: flex; min-height: 100vh; padding-top: 52px; }

/* ── Sidebar ── */
#sidebar {
  width: var(--sidebar-w); flex-shrink: 0;
  background: var(--color-nav); color: var(--color-surface);
  position: fixed; top: 52px; bottom: 0; left: 0;
  overflow-y: auto; padding: 1rem 0;
}
#sidebar h2 {
  font-size: .75rem; text-transform: uppercase; letter-spacing: .08em;
  color: rgba(255,255,255,.4); padding: .5rem 1.2rem .25rem;
}
.ch-item {
  display: flex; align-items: center; gap: .6rem;
  padding: .65rem 1.2rem; cursor: pointer;
  transition: background .15s; border-left: 3px solid transparent;
}
.ch-item:hover { background: rgba(255,255,255,.06); }
.ch-item.active {
  background: rgba(var(--color-accent-rgb), .15);
  border-left-color: var(--color-accent);
}
.ch-item.completed .ch-icon { color: var(--sem-success); }
.ch-item.locked { opacity: .45; cursor: not-allowed; }
.ch-icon { font-size: 1rem; width: 20px; text-align: center; flex-shrink: 0; }
.ch-label { font-size: .85rem; line-height: 1.3; }
.ch-label small { display: block; font-size: .72rem; color: rgba(255,255,255,.45); margin-top: .15rem; }
.sidebar-footer {
  padding: 1rem 1.2rem; border-top: 1px solid rgba(255,255,255,.1); margin-top: .5rem;
}
.sidebar-footer .stat { font-size: .78rem; color: rgba(255,255,255,.5); margin-bottom: .3rem; }

/* ── Main content ── */
#main { margin-left: var(--sidebar-w); flex: 1; padding: 2rem; }

/* ── Chapter view ── */
.ch-header { margin-bottom: 1.5rem; }
.ch-header h1 { font-size: 1.4rem; color: var(--color-primary); margin-bottom: .4rem; }
.ch-header .objective { color: var(--color-muted); font-size: .95rem; }
.ch-header .meta { display: flex; gap: .75rem; margin-top: .75rem; flex-wrap: wrap; }
.badge {
  display: inline-block; padding: .2rem .65rem; border-radius: 20px;
  font-size: .75rem; font-weight: 600;
}
.badge-logic { background: var(--color-primary); color: var(--color-surface); }
.badge-duration { background: rgba(0,0,0,.06); color: var(--color-muted); }
.badge-status-available { background: var(--sem-example-bg); color: var(--sem-success); }
.badge-status-locked { background: var(--sem-locked-bg); color: var(--sem-locked-fg); }
.badge-status-completed { background: var(--sem-example-bg); color: var(--sem-success); }

/* ── Lesson card ── */
.lesson-card {
  background: var(--color-surface); border-radius: var(--radius); margin-bottom: 1rem;
  box-shadow: 0 1px 4px rgba(0,0,0,.06); overflow: hidden;
}
.lesson-header {
  display: flex; align-items: center; gap: .75rem;
  padding: 1rem 1.25rem; cursor: pointer; user-select: none;
  transition: background .15s;
}
.lesson-header:hover { background: rgba(0,0,0,.02); }
.lesson-header.locked { cursor: not-allowed; opacity: .5; }
.lesson-status-icon { font-size: 1.1rem; width: 24px; text-align: center; flex-shrink: 0; }
.lesson-title-wrap { flex: 1; }
.lesson-title { font-size: .95rem; font-weight: 600; color: var(--color-primary); }
.lesson-obj { font-size: .8rem; color: var(--color-muted); margin-top: .1rem; }
.lesson-toggle { color: var(--color-muted); transition: transform .2s; font-size: .8rem; }
.lesson-toggle.open { transform: rotate(180deg); }
.lesson-body { padding: 0 1.25rem 1.25rem; border-top: 1px solid var(--color-border); }

/* ── Content blocks ── */
.content-block {
  border-radius: var(--radius); padding: .9rem 1rem; margin: .85rem 0;
  border-left: 4px solid transparent;
}
.cb-theory    { background: var(--sem-theory-bg);  border-color: var(--sem-blue); }
.cb-example   { background: var(--sem-example-bg); border-color: var(--sem-success); }
.cb-method    { background: var(--sem-method-bg);  border-color: var(--sem-purple); }
.cb-warning   { background: var(--sem-warn-bg);    border-color: var(--sem-warning); }
.cb-prompt    { background: var(--sem-code-bg);    border-color: var(--sem-code-border); color: var(--sem-code-text); }
.cb-checklist { background: var(--sem-check-bg);   border-color: var(--sem-teal); }
.cb-label {
  font-size: .68rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .07em; opacity: .65; margin-bottom: .35rem;
}
.cb-theory .cb-label    { color: var(--sem-blue); }
.cb-example .cb-label   { color: var(--sem-success); }
.cb-method .cb-label    { color: var(--sem-purple); }
.cb-warning .cb-label   { color: var(--sem-warning); }
.cb-prompt .cb-label    { color: var(--sem-code-muted); }
.cb-checklist .cb-label { color: var(--sem-teal); }
.cb-title { font-size: .9rem; font-weight: 700; margin-bottom: .4rem; }
.cb-prompt .cb-title { color: var(--sem-code-title); }
.cb-content { font-size: .88rem; line-height: 1.65; white-space: pre-wrap; }
.cb-prompt .cb-content { color: var(--sem-code-muted); font-family: 'SF Mono', monospace; font-size: .82rem; }
.copy-btn {
  margin-top: .5rem; padding: .3rem .75rem; background: var(--sem-code-btn); border: none;
  color: var(--sem-code-muted); border-radius: 5px; cursor: pointer; font-size: .78rem;
}
.copy-btn:hover { background: var(--sem-code-btn-hover); }

/* ── Interactive tasks ── */
.task-block {
  background: var(--color-bg); border-radius: var(--radius); padding: 1rem;
  margin: .85rem 0; border: 1px solid var(--color-border);
}
.task-block.completed { border-color: var(--sem-success); background: var(--sem-success-bg); }
.task-type-badge {
  font-size: .68rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .07em; padding: .15rem .5rem; border-radius: 20px;
  margin-bottom: .5rem; display: inline-block;
}
.tt-question         { background: var(--sem-tt-question-bg); color: var(--sem-tt-question-fg); }
.tt-exercise         { background: var(--sem-tt-exercise-bg); color: var(--sem-tt-exercise-fg); }
.tt-prompt_practice  { background: var(--sem-tt-prompt-bg);   color: var(--sem-tt-prompt-fg); }
.tt-self_assessment  { background: var(--sem-tt-assess-bg);   color: var(--sem-tt-assess-fg); }
.tt-checklist        { background: var(--sem-tt-checklist-bg);color: var(--sem-tt-checklist-fg); }
.task-instruction { font-size: .88rem; margin-bottom: .75rem; line-height: 1.5; }
.task-input {
  width: 100%; padding: .6rem .75rem; border: 1px solid var(--color-border);
  border-radius: var(--radius); font-size: .87rem; resize: vertical; min-height: 80px;
  font-family: inherit; background: var(--color-surface); color: var(--color-text);
}
.task-input:focus { outline: none; border-color: var(--color-accent); }
.rating-wrap { display: flex; gap: .5rem; margin: .5rem 0; }
.rating-btn {
  width: 38px; height: 38px; border-radius: 50%; border: 2px solid var(--color-border);
  background: var(--color-surface); cursor: pointer; font-size: .9rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center; transition: all .15s;
}
.rating-btn:hover { border-color: var(--color-accent); color: var(--color-accent); }
.rating-btn.selected { background: var(--color-accent); border-color: var(--color-accent); color: var(--color-surface); }
.task-checklist-items { list-style: none; margin: .5rem 0; }
.task-checklist-items li {
  display: flex; align-items: center; gap: .5rem;
  padding: .3rem 0; font-size: .88rem; cursor: pointer;
}
.task-checklist-items li input[type=checkbox] { width: 16px; height: 16px; cursor: pointer; }
.task-checklist-items li.checked { color: var(--sem-success); text-decoration: line-through; opacity: .7; }
.done-btn {
  margin-top: .75rem; padding: .5rem 1.25rem;
  background: var(--color-primary); color: var(--color-surface); border: none;
  border-radius: var(--radius); cursor: pointer; font-size: .85rem;
  transition: background .15s;
}
.done-btn:hover { background: var(--color-accent); }
.done-btn:disabled { background: var(--sem-success); cursor: default; }
.task-done-label {
  color: var(--sem-success); font-size: .85rem; font-weight: 600;
  display: flex; align-items: center; gap: .4rem;
}
.success-criteria { margin-top: .75rem; font-size: .8rem; color: var(--color-muted); }
.success-criteria ul { padding-left: 1.2rem; margin-top: .25rem; }
.success-criteria li { margin-bottom: .2rem; }

/* ── Lesson completion / chapter validation ── */
.section-divider { border: none; border-top: 1px dashed var(--color-border); margin: 1.25rem 0; }
.validate-lesson-btn, .validate-chapter-btn {
  display: block; width: 100%; padding: .75rem 1rem;
  background: var(--color-nav); color: var(--color-surface); border: none;
  border-radius: var(--radius); cursor: pointer; font-size: .9rem; font-weight: 600;
  text-align: center; margin-top: 1rem; transition: background .15s;
}
.validate-lesson-btn:hover { background: var(--color-accent); }
.validate-chapter-btn {
  background: var(--color-accent); font-size: 1rem; padding: 1rem;
}
.validate-chapter-btn:hover { background: var(--color-accent-dark); }
.validate-chapter-btn:disabled { background: var(--sem-success); cursor: default; }
.lesson-completed-banner {
  background: var(--sem-success-bg); border: 1px solid var(--sem-success);
  border-radius: var(--radius); padding: .75rem 1rem;
  color: var(--sem-success); font-weight: 600; font-size: .9rem;
  display: flex; align-items: center; gap: .5rem; margin-top: 1rem;
}
.chapter-validated-banner {
  background: var(--sem-success-bg); border: 2px solid var(--sem-success);
  border-radius: var(--radius); padding: 1rem 1.25rem;
  color: var(--sem-success); font-weight: 700;
  display: flex; align-items: center; gap: .75rem; margin-top: 1.25rem;
}

/* ── Chapter validation form ── */
.ch-validation-card {
  background: var(--color-surface); border-radius: var(--radius); padding: 1.5rem;
  border: 2px solid var(--color-nav); margin-top: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.ch-validation-card h3 { color: var(--color-primary); margin-bottom: .5rem; }
.ch-validation-card .val-type {
  font-size: .75rem; font-weight: 700; text-transform: uppercase;
  color: var(--color-accent); letter-spacing: .07em; margin-bottom: .75rem;
}
.ch-validation-card .val-instructions {
  font-size: .9rem; color: var(--color-text); margin-bottom: .75rem; line-height: 1.6;
}
.ch-validation-card .val-criteria { font-size: .82rem; color: var(--color-muted); margin-bottom: 1rem; }
.ch-validation-card .val-criteria ul { padding-left: 1.2rem; margin-top: .3rem; }
.ch-validation-card .val-criteria li { margin-bottom: .2rem; }

/* ── Final validation ── */
.final-card {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-nav) 100%);
  color: var(--color-surface); border-radius: var(--radius); padding: 2rem; margin-top: 2rem;
}
.final-card h2 { font-size: 1.3rem; margin-bottom: .5rem; }
.final-card p  { opacity: .8; font-size: .9rem; line-height: 1.6; margin-bottom: 1rem; }
.final-card textarea {
  width: 100%; background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.2);
  border-radius: var(--radius); color: var(--color-surface); padding: .75rem;
  font-size: .88rem; resize: vertical; min-height: 120px; font-family: inherit;
}
.final-card textarea::placeholder { color: rgba(255,255,255,.4); }
.final-validate-btn {
  margin-top: 1rem; padding: .85rem 2rem; background: var(--color-accent);
  color: var(--color-surface); border: none; border-radius: var(--radius);
  cursor: pointer; font-size: .95rem; font-weight: 700; transition: background .15s;
}
.final-validate-btn:hover { background: var(--color-accent-dark); }
.final-validate-btn:disabled { background: var(--sem-success); cursor: default; }

/* ── Certificate ── */
#certificate {
  display: none; background: var(--color-surface); border-radius: var(--radius);
  border: 3px solid var(--color-accent); padding: 2.5rem; text-align: center;
  margin-top: 2rem; box-shadow: 0 4px 20px rgba(var(--color-accent-rgb), .15);
}
#certificate.show { display: block; }
#certificate .cert-icon { font-size: 3rem; margin-bottom: .75rem; }
#certificate h2 { font-size: 1.6rem; color: var(--color-primary); margin-bottom: .5rem; }
#certificate p { color: var(--color-muted); margin-bottom: .25rem; }
#certificate .cert-title { font-size: 1.1rem; font-weight: 700; color: var(--color-accent); margin: .75rem 0; }
#certificate .cert-date { font-size: .85rem; color: var(--color-muted); }

/* ── Empty state ── */
.empty-state { text-align: center; padding: 4rem 2rem; color: var(--color-muted); }
.empty-state h2 { font-size: 1.2rem; margin-bottom: .5rem; }

/* ── Responsive ── */
@media (max-width: 768px) {
  :root { --sidebar-w: 0px; }
  #sidebar { transform: translateX(-100%); transition: transform .3s; z-index: 50; width: 260px; }
  #sidebar.open { transform: translateX(0); --sidebar-w: 260px; }
  #main { margin-left: 0; padding: 1rem; }
  #menu-btn { display: flex !important; }
}
#menu-btn { display: none; background: none; border: none; color: var(--color-surface); font-size: 1.3rem; cursor: pointer; }
</style>
</head>
<body>

<!-- Header -->
<div id="header">
  <button id="menu-btn" onclick="toggleSidebar()">☰</button>
  <div id="header-title">Formation</div>
  <div id="header-progress">
    <div id="progress-bar-wrap"><div id="progress-bar-fill" style="width:0%"></div></div>
    <div id="progress-text">0%</div>
  </div>
</div>

<!-- Sidebar -->
<nav id="sidebar">
  <h2>Chapitres</h2>
  <div id="ch-list"></div>
  <div class="sidebar-footer">
    <div class="stat" id="stat-tasks"></div>
    <div class="stat" id="stat-duration"></div>
  </div>
</nav>

<!-- Main -->
<main id="main">
  <div id="content"></div>
</main>

<script>
// ── Data ──────────────────────────────────────────────────────────────────────
const data = /*TRAINING_DATA*/;

// ── State ─────────────────────────────────────────────────────────────────────
const STATE_KEY = 'training_state_' + (data.training_title || 'default').replace(/\W/g,'_').slice(0,40);

let state = {
  tasks:           {},   // taskId → true/false
  taskValues:      {},   // taskId → string (textarea) or rating int
  chValidated:     {},   // chapterId → true/false
  chValText:       {},   // chapterId → string
  finalValidated:  false,
  finalText:       '',
  activeChapter:   null,
  openLessons:     {},   // lessonId → true/false
};

function loadState() {
  try {
    const s = localStorage.getItem(STATE_KEY);
    if (s) state = Object.assign(state, JSON.parse(s));
  } catch(e) {}
  if (!state.activeChapter) {
    state.activeChapter = data.chapters[0].chapter_id;
  }
}

function saveState() {
  try { localStorage.setItem(STATE_KEY, JSON.stringify(state)); } catch(e) {}
}

// ── Progress ──────────────────────────────────────────────────────────────────
function calcProgress() {
  const total = data.progression.total_tasks
    + data.progression.total_chapters
    + 1; // final validation
  let done = 0;
  done += Object.values(state.tasks).filter(Boolean).length;
  done += Object.values(state.chValidated).filter(Boolean).length;
  if (state.finalValidated) done++;
  return { done, total, pct: total > 0 ? Math.round(done / total * 100) : 0 };
}

function updateProgressBar() {
  const { done, total, pct } = calcProgress();
  document.getElementById('progress-bar-fill').style.width = pct + '%';
  document.getElementById('progress-text').textContent = pct + '%';
  document.getElementById('stat-tasks').textContent =
    done + ' / ' + total + ' étapes terminées';
  document.getElementById('stat-duration').textContent =
    '⏱ ' + (data.estimated_duration || '');
}

// ── Chapter unlock logic ──────────────────────────────────────────────────────
function isChapterAvailable(ch) {
  if (ch.order === 1) return true;
  const prev = data.chapters.find(c => c.order === ch.order - 1);
  return prev && state.chValidated[prev.chapter_id];
}

function isLessonAvailable(chOrder, lesson) {
  if (!isChapterAvailable(data.chapters.find(c => c.order === chOrder))) return false;
  if (lesson.order === 1) return true;
  const ch = data.chapters.find(c => c.order === chOrder);
  const prev = ch.lessons.find(l => l.order === lesson.order - 1);
  return prev && isLessonCompleted(prev);
}

function isLessonCompleted(lesson) {
  return lesson.completion_rules.required_tasks.every(tid => state.tasks[tid]);
}

function isChapterDone(ch) {
  return ch.lessons.every(l => isLessonCompleted(l)) && state.chValidated[ch.chapter_id];
}

// ── Sidebar render ────────────────────────────────────────────────────────────
function renderSidebar() {
  const list = document.getElementById('ch-list');
  list.innerHTML = '';
  for (const ch of data.chapters) {
    const avail      = isChapterAvailable(ch);
    const done       = isChapterDone(ch);
    const active     = state.activeChapter === ch.chapter_id;
    const n_tasks    = ch.lessons.reduce((s,l) => s + l.interactive_tasks.length, 0);
    const done_tasks = ch.lessons.reduce((s,l) =>
      s + l.completion_rules.required_tasks.filter(t => state.tasks[t]).length, 0);

    const icon = done ? '✓' : avail ? '●' : '🔒';
    const cls  = ['ch-item', active?'active':'', done?'completed':'', !avail?'locked':'']
      .filter(Boolean).join(' ');

    const el = document.createElement('div');
    el.className = cls;
    el.innerHTML = `
      <span class="ch-icon">${icon}</span>
      <span class="ch-label">
        ${esc(ch.title)}
        <small>${done_tasks}/${n_tasks} tâches · ${ch.estimated_duration || ''}</small>
      </span>`;
    if (avail || done) {
      el.onclick = () => { state.activeChapter = ch.chapter_id; saveState(); render(); };
    }
    list.appendChild(el);
  }
}

// ── Main content render ───────────────────────────────────────────────────────
function render() {
  document.getElementById('header-title').textContent = data.training_title;
  renderSidebar();
  renderContent();
  updateProgressBar();
}

function renderContent() {
  const ch = data.chapters.find(c => c.chapter_id === state.activeChapter);
  if (!ch) {
    document.getElementById('content').innerHTML = '<div class="empty-state"><h2>Sélectionnez un chapitre</h2></div>';
    return;
  }

  const avail = isChapterAvailable(ch);
  if (!avail) {
    document.getElementById('content').innerHTML = `
      <div class="empty-state">
        <h2>🔒 Chapitre verrouillé</h2>
        <p>Terminez le chapitre précédent pour débloquer celui-ci.</p>
      </div>`;
    return;
  }

  const logicLabel = {
    editorial:'Comprendre & Communiquer', technical:'Maîtriser les Outils',
    strategic:'Vision & Stratégie', operational:'Mise en Pratique',
    cognitive:'Esprit Critique', collaborative:'Collaboration', creative:'Créativité',
  }[ch.logic_type] || ch.logic_type;

  const chDone = isChapterDone(ch);

  let html = `
  <div class="ch-header">
    <h1>${esc(ch.title)}</h1>
    <p class="objective">${esc(ch.objective)}</p>
    <div class="meta">
      <span class="badge badge-logic">${esc(logicLabel)}</span>
      <span class="badge badge-duration">⏱ ${esc(ch.estimated_duration || '')}</span>
      ${chDone
        ? '<span class="badge badge-status-completed">✓ Terminé</span>'
        : '<span class="badge badge-status-available">En cours</span>'}
    </div>
  </div>`;

  for (const lesson of ch.lessons) {
    html += renderLesson(ch, lesson);
  }

  if (!chDone) {
    const allLessonsDone = ch.lessons.every(l => isLessonCompleted(l));
    if (allLessonsDone) {
      html += renderChValidation(ch);
    }
  } else {
    html += `<div class="chapter-validated-banner">✓ Chapitre validé — Bien joué !</div>`;
    const lastCh = data.chapters[data.chapters.length - 1];
    if (ch.chapter_id === lastCh.chapter_id) {
      html += renderFinalValidation();
    }
  }

  document.getElementById('content').innerHTML = html;
  bindEvents(ch);
}

function renderLesson(ch, lesson) {
  const avail     = isLessonAvailable(ch.order, lesson);
  const completed = isLessonCompleted(lesson);
  const isOpen    = state.openLessons[lesson.lesson_id] !== false && avail;
  const icon      = completed ? '✓' : avail ? '▶' : '🔒';
  const iconColor = completed ? 'var(--sem-success)' : avail ? 'var(--color-accent)' : 'var(--sem-locked-icon)';

  let html = `
  <div class="lesson-card" id="${lesson.lesson_id}">
    <div class="lesson-header ${avail ? '' : 'locked'}" onclick="toggleLesson('${lesson.lesson_id}', ${avail})">
      <span class="lesson-status-icon" style="color:${iconColor}">${icon}</span>
      <div class="lesson-title-wrap">
        <div class="lesson-title">${esc(lesson.title)}</div>
        <div class="lesson-obj">${esc(lesson.objective)}</div>
      </div>
      <span class="lesson-toggle ${isOpen ? 'open' : ''}">▼</span>
    </div>`;

  if (avail && isOpen) {
    html += `<div class="lesson-body">`;
    for (const cb of lesson.content_blocks) {
      html += renderContentBlock(cb);
    }
    html += `<hr class="section-divider">`;
    html += `<div style="font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--color-accent);margin-bottom:.75rem;">À faire</div>`;
    for (const task of lesson.interactive_tasks) {
      html += renderTask(task, lesson);
    }
    if (completed) {
      html += `<div class="lesson-completed-banner">✓ Leçon terminée</div>`;
    } else {
      html += `<button class="validate-lesson-btn" onclick="validateLesson('${lesson.lesson_id}', '${ch.chapter_id}')">
        Valider cette leçon →
      </button>`;
    }
    html += `</div>`;
  }

  html += `</div>`;
  return html;
}

function renderContentBlock(cb) {
  const cls = 'content-block cb-' + cb.type;
  const typelabel = {
    theory:'Théorie', example:'Exemple', method:'Méthode',
    warning:'Point de vigilance', prompt:'Prompt', checklist:'Checklist'
  }[cb.type] || cb.type;
  let inner = `<div class="cb-label">${typelabel}</div>
    <div class="cb-title">${esc(cb.title)}</div>
    <div class="cb-content">${esc(cb.content)}</div>`;
  if (cb.type === 'prompt') {
    inner += `<button class="copy-btn" onclick="copyPrompt(this, ${JSON.stringify(cb.content)})">📋 Copier</button>`;
  }
  return `<div class="${cls}">${inner}</div>`;
}

function renderTask(task, lesson) {
  const tid      = task.task_id;
  const done     = !!state.tasks[tid];
  const ttCls    = 'task-type-badge tt-' + task.type;
  const typeLabel = {
    question:'Question', exercise:'Exercice', prompt_practice:'Pratique Prompt',
    self_assessment:'Auto-évaluation', checklist:'Checklist'
  }[task.type] || task.type;

  let inner = `<span class="${ttCls}">${typeLabel}</span>
    <div class="task-instruction">${esc(task.instruction)}</div>`;

  if (done) {
    inner += `<div class="task-done-label">✓ Terminé</div>`;
  } else if (task.type === 'self_assessment') {
    const cur = state.taskValues[tid] || 0;
    let btns = '';
    for (let i = 1; i <= 5; i++) {
      btns += `<button class="rating-btn ${cur===i?'selected':''}" onclick="setRating('${tid}', ${i})">${i}</button>`;
    }
    inner += `<div class="rating-wrap">${btns}</div>`;
    inner += `<button class="done-btn" onclick="markDone('${tid}')">Valider</button>`;
  } else if (task.type === 'checklist') {
    const items = task.success_criteria || [];
    let checkHtml = '<ul class="task-checklist-items">';
    items.forEach((item, i) => {
      const cid   = tid + '_c' + i;
      const chked = state.taskValues[cid] || false;
      checkHtml += `<li class="${chked?'checked':''}" onclick="toggleCheck('${tid}', '${cid}', ${items.length})">
        <input type="checkbox" ${chked?'checked':''} onclick="event.stopPropagation();toggleCheck('${tid}','${cid}',${items.length})">
        ${esc(item)}
      </li>`;
    });
    checkHtml += '</ul>';
    inner += checkHtml;
  } else {
    const val = state.taskValues[tid] || '';
    inner += `<textarea class="task-input" id="ta_${tid}" placeholder="Votre réponse..."
      onchange="saveTaskValue('${tid}', this.value)">${esc(val)}</textarea>`;
    inner += `<button class="done-btn" onclick="markDone('${tid}')">Marquer comme terminé</button>`;
  }

  if (task.success_criteria && task.success_criteria.length && !done) {
    const items = task.success_criteria.map(c => `<li>${esc(c)}</li>`).join('');
    inner += `<div class="success-criteria"><strong>Critères :</strong><ul>${items}</ul></div>`;
  }

  return `<div class="task-block ${done?'completed':''}" id="tb_${tid}">${inner}</div>`;
}

function renderChValidation(ch) {
  const val = ch.chapter_validation;
  const typelabel = {
    quiz:'Quiz', practical_case:'Cas pratique', checklist:'Checklist', reflection:'Réflexion'
  }[val.type] || val.type;
  const criteria = (val.success_criteria||[]).map(c=>`<li>${esc(c)}</li>`).join('');
  const saved = state.chValText[ch.chapter_id] || '';
  return `
  <div class="ch-validation-card" id="chval_${ch.chapter_id}">
    <div class="val-type">Validation du chapitre — ${typelabel}</div>
    <h3>✍ Valider ce chapitre</h3>
    <div class="val-instructions">${esc(val.instructions)}</div>
    ${criteria ? `<div class="val-criteria"><strong>Critères de succès :</strong><ul>${criteria}</ul></div>` : ''}
    <textarea class="task-input" id="chval_ta_${ch.chapter_id}" placeholder="Votre réponse..."
      onchange="saveChValText('${ch.chapter_id}', this.value)">${esc(saved)}</textarea>
    <button class="validate-chapter-btn" onclick="validateChapter('${ch.chapter_id}')">
      ✓ Valider ce chapitre et continuer →
    </button>
  </div>`;
}

function renderFinalValidation() {
  if (state.finalValidated) return renderCertificate();
  const fv = data.final_validation;
  const criteria = (fv.success_criteria||[]).map(c=>`<li>${esc(c)}</li>`).join('');
  const typelabel = {
    practical_case:'Cas pratique', action_plan:"Plan d'action", quiz:'Quiz'
  }[fv.type] || fv.type;
  return `
  <div class="final-card" id="final-validation">
    <h2>🎯 Validation finale — ${typelabel}</h2>
    <p>${esc(fv.instructions)}</p>
    ${criteria ? `<ul style="margin-bottom:1rem;padding-left:1.2rem;opacity:.8;font-size:.88rem;">${criteria}</ul>` : ''}
    <textarea placeholder="Votre plan d'action..." onchange="saveFinalText(this.value)">${esc(state.finalText)}</textarea>
    <button class="final-validate-btn" onclick="validateFinal()">
      ✓ Valider la formation et obtenir mon attestation
    </button>
  </div>`;
}

function renderCertificate() {
  const d = new Date().toLocaleDateString('fr-FR', {year:'numeric',month:'long',day:'numeric'});
  return `
  <div id="certificate" class="show">
    <div class="cert-icon">🎓</div>
    <h2>Attestation de formation</h2>
    <div class="cert-title">${esc(data.training_title)}</div>
    <p>Formation complétée avec succès.</p>
    <p>Durée estimée : ${esc(data.estimated_duration||'')}</p>
    <p class="cert-date">Délivré le ${d}</p>
    <p style="margin-top:1rem;font-size:.8rem;opacity:.5;">
      Généré par training_generator v2.0.0 — Module EURKAI
    </p>
  </div>`;
}

// ── Event handlers ────────────────────────────────────────────────────────────
function toggleLesson(lessonId, avail) {
  if (!avail) return;
  state.openLessons[lessonId] = !state.openLessons[lessonId];
  saveState(); renderContent();
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

function copyPrompt(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = '✓ Copié !';
    setTimeout(() => { btn.textContent = '📋 Copier'; }, 2000);
  });
}

function setRating(tid, val) {
  state.taskValues[tid] = val;
  saveState(); renderContent();
}

function saveTaskValue(tid, val) {
  state.taskValues[tid] = val; saveState();
}

function saveChValText(chId, val) {
  state.chValText[chId] = val; saveState();
}

function saveFinalText(val) {
  state.finalText = val; saveState();
}

function toggleCheck(tid, cid, total) {
  state.taskValues[cid] = !state.taskValues[cid];
  const allDone = Array.from({length: total}, (_,i) => state.taskValues[tid + '_c' + i]).every(Boolean);
  if (allDone) state.tasks[tid] = true;
  saveState(); renderContent();
}

function markDone(tid) {
  state.tasks[tid] = true; saveState(); renderContent();
}

function validateLesson(lessonId, chId) {
  const ch     = data.chapters.find(c => c.chapter_id === chId);
  const lesson = ch.lessons.find(l => l.lesson_id === lessonId);
  lesson.completion_rules.required_tasks.forEach(tid => { state.tasks[tid] = true; });
  state.openLessons[lessonId] = false;
  const next = ch.lessons.find(l => l.order === lesson.order + 1);
  if (next) state.openLessons[next.lesson_id] = true;
  saveState(); render();
}

function validateChapter(chId) {
  state.chValidated[chId] = true;
  const ch    = data.chapters.find(c => c.chapter_id === chId);
  const nextCh = data.chapters.find(c => c.order === ch.order + 1);
  if (nextCh) {
    state.activeChapter = nextCh.chapter_id;
    state.openLessons[nextCh.lessons[0].lesson_id] = true;
  }
  saveState(); render(); window.scrollTo(0, 0);
}

function validateFinal() {
  state.finalValidated = true; saveState(); render();
  setTimeout(() => {
    const cert = document.getElementById('certificate');
    if (cert) cert.scrollIntoView({ behavior: 'smooth' });
  }, 100);
}

function bindEvents(ch) {
  for (const lesson of ch.lessons) {
    for (const task of lesson.interactive_tasks) {
      const ta = document.getElementById('ta_' + task.task_id);
      if (ta && state.taskValues[task.task_id]) ta.value = state.taskValues[task.task_id];
    }
  }
  const chTa = document.getElementById('chval_ta_' + ch.chapter_id);
  if (chTa && state.chValText[ch.chapter_id]) chTa.value = state.chValText[ch.chapter_id];
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function esc(s) {
  if (!s) return '';
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ── Init ──────────────────────────────────────────────────────────────────────
loadState();
const activeCh = data.chapters.find(c => c.chapter_id === state.activeChapter);
if (activeCh && activeCh.lessons.length > 0) {
  const firstLesson = activeCh.lessons[0];
  if (state.openLessons[firstLesson.lesson_id] === undefined) {
    state.openLessons[firstLesson.lesson_id] = true;
  }
}
render();
</script>
</body>
</html>"""


if __name__ == "__main__":
    main()
