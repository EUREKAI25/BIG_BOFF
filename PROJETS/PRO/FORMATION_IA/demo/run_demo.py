"""
run_demo.py — Démo FORMATION_IA
Génère une formation complète sur "Utiliser l'IA dans son travail quotidien"
en utilisant le module training_generator d'EURKAI.

Exporte :
    output_demo.json  — structure complète
    output_demo.html  — rendu consultable dans le navigateur

Usage :
    cd PROJETS/PRO/EURKAI/CODE/eurkai_core
    python ../../FORMATION_IA/demo/run_demo.py
"""

import json
import sys
from pathlib import Path

# Ajouter eurkai_core au path
EURKAI_CORE = Path(__file__).parent.parent.parent / "EURKAI" / "CODE" / "eurkai_core"
sys.path.insert(0, str(EURKAI_CORE))

from modules.training_generator import run

DEMO_INPUT = {
    "topic": "Utiliser l'IA dans son travail quotidien",
    "level": "beginner",
    "objectives": [
        "Comprendre ce qu'est l'IA et ce qu'elle peut faire concrètement",
        "Rédiger des prompts efficaces dès le premier jour",
        "Identifier des cas d'usage immédiatement applicables à son poste",
        "Adopter les bonnes pratiques de sécurité et de confidentialité",
    ],
    "logics":  ["editorial", "technical", "operational", "strategic"],
    "format":  "standard",
    "catalog": None,  # mode déterministe — fonctionne sans clé API
}

OUT_DIR = Path(__file__).parent


def main():
    print("▶ Génération de la formation démo...")
    result = run(DEMO_INPUT)

    if result["status"] != "success":
        print(f"✗ Erreur : {result.get('error')}")
        sys.exit(1)

    training = result["training"]
    mode     = result["meta"]["mode"]

    # ── Export JSON ───────────────────────────────────────────────────────────
    json_path = OUT_DIR / "output_demo.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON  → {json_path}")

    # ── Export HTML ───────────────────────────────────────────────────────────
    html_path = OUT_DIR / "output_demo.html"
    html      = _render_html(training, mode)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ HTML  → {html_path}")

    # ── Résumé console ────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  Formation : {training['training_title']}")
    print(f"  Niveau    : {training['level']}")
    print(f"  Mode      : {mode}")
    modules = training.get("modules", [])
    total_sections = sum(len(m["sections"]) for m in modules)
    print(f"  Modules   : {len(modules)} logiques / {total_sections} sections")
    print(f"{'─'*60}\n")


def _render_html(training, mode):
    title    = training.get("training_title", "Formation")
    level    = training.get("level", "")
    summary  = training.get("summary", "")
    modules  = training.get("modules", [])
    nexts    = training.get("next_steps", [])

    level_labels = {"beginner": "Débutant", "intermediate": "Intermédiaire", "advanced": "Avancé"}
    mode_label   = "LLM (Claude)" if mode == "llm" else "Déterministe (template)"

    modules_html = ""
    for m in modules:
        logic = m.get("logic_type", "")
        sections_html = ""
        for s in m.get("sections", []):
            kc  = "".join(f"<li>{c}</li>" for c in s.get("key_concepts", []))
            ex  = "".join(f"<li>{e}</li>" for e in s.get("examples", []))
            exo = "".join(f"<li>{e}</li>" for e in s.get("exercises", []))
            pr  = "".join(f"<li><code>{p}</code></li>" for p in s.get("prompts", []))
            sections_html += f"""
            <div class="section">
              <h3>{s.get('title','')}</h3>
              <p class="desc">{s.get('description','')}</p>
              <div class="cols">
                <div><h4>Concepts clés</h4><ul>{kc}</ul></div>
                <div><h4>Exemples</h4><ul>{ex}</ul></div>
                <div><h4>Exercices</h4><ul>{exo}</ul></div>
              </div>
              {'<div class="prompts"><h4>Prompts</h4><ul>' + pr + '</ul></div>' if pr else ''}
            </div>"""

        modules_html += f"""
        <div class="module">
          <div class="module-header">
            <span class="logic-badge">{logic}</span>
          </div>
          {sections_html}
        </div>"""

    nexts_html = "".join(f"<li>{n}</li>" for n in nexts)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{
    --primary: #1a1a2e;
    --accent: #e94560;
    --bg: #f8f9fa;
    --card: #ffffff;
    --text: #2d3436;
    --muted: #636e72;
    --border: #e0e0e0;
    --logic: #0f3460;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: var(--bg); color: var(--text); line-height: 1.6; }}
  header {{
    background: var(--primary); color: white; padding: 2.5rem 2rem;
    border-bottom: 4px solid var(--accent);
  }}
  header h1 {{ font-size: 1.8rem; font-weight: 700; margin-bottom: .5rem; }}
  .meta {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-top: .75rem; }}
  .badge {{
    display: inline-block; padding: .25rem .75rem; border-radius: 20px;
    font-size: .8rem; font-weight: 600;
  }}
  .badge-level {{ background: var(--accent); color: white; }}
  .badge-mode  {{ background: rgba(255,255,255,.15); color: white; }}
  .badge-eurkai {{ background: #16213e; color: #e94560; border: 1px solid #e94560; }}
  main {{ max-width: 960px; margin: 2rem auto; padding: 0 1rem; }}
  .summary-card {{
    background: var(--card); border-radius: 8px; padding: 1.5rem;
    border-left: 4px solid var(--accent); margin-bottom: 2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
  }}
  .summary-card h2 {{ font-size: 1rem; color: var(--muted); margin-bottom: .5rem; text-transform: uppercase; letter-spacing: .05em; }}
  .module {{
    background: var(--card); border-radius: 8px; margin-bottom: 2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.06); overflow: hidden;
  }}
  .module-header {{
    background: var(--logic); padding: .75rem 1.5rem;
  }}
  .logic-badge {{
    display: inline-block; background: var(--accent); color: white;
    padding: .2rem .8rem; border-radius: 20px; font-size: .85rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .05em;
  }}
  .section {{
    padding: 1.5rem; border-bottom: 1px solid var(--border);
  }}
  .section:last-child {{ border-bottom: none; }}
  .section h3 {{ font-size: 1.1rem; color: var(--primary); margin-bottom: .5rem; }}
  .desc {{ color: var(--muted); margin-bottom: 1rem; }}
  .cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
  h4 {{ font-size: .85rem; text-transform: uppercase; letter-spacing: .05em;
        color: var(--accent); margin-bottom: .4rem; }}
  ul {{ padding-left: 1.2rem; }}
  li {{ margin-bottom: .3rem; font-size: .9rem; }}
  .prompts {{ margin-top: 1rem; background: #f0f4ff; border-radius: 6px; padding: 1rem; }}
  .prompts code {{ font-size: .85rem; color: var(--logic); background: #e8eeff;
                   padding: .1rem .4rem; border-radius: 3px; }}
  .next-steps {{
    background: var(--card); border-radius: 8px; padding: 1.5rem;
    border-left: 4px solid #27ae60; margin-top: 2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
  }}
  .next-steps h2 {{ font-size: 1rem; color: var(--muted); margin-bottom: .75rem;
                    text-transform: uppercase; letter-spacing: .05em; }}
  footer {{
    text-align: center; padding: 2rem; color: var(--muted); font-size: .8rem;
    border-top: 1px solid var(--border); margin-top: 3rem;
  }}
</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <div class="meta">
    <span class="badge badge-level">{level_labels.get(level, level)}</span>
    <span class="badge badge-mode">Mode : {mode_label}</span>
    <span class="badge badge-eurkai">Module EURKAI · training_generator v1.0.0</span>
  </div>
</header>
<main>
  <div class="summary-card">
    <h2>Résumé</h2>
    <p>{summary}</p>
  </div>
  {modules_html}
  <div class="next-steps">
    <h2>Prochaines étapes</h2>
    <ul>{nexts_html}</ul>
  </div>
</main>
<footer>
  Généré par training_generator · Module EURKAI · 2026-04-29
</footer>
</body>
</html>"""


if __name__ == "__main__":
    main()
