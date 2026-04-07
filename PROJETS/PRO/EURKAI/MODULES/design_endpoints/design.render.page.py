"""
design.render.page
Endpoint : génère une page HTML en utilisant exclusivement l'Eurkai DOM Library.

Pipeline :
  assemble_page(brief, palette, visual_intent, plan, site_family, seed)
  → Page (blocs v0.2)
  → render_page(page)
  → HTML

Toute la structure DOM passe par page_builder.
Aucun HTML arbitraire n'est généré directement.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from page_builder.src.assembler     import assemble_page
from page_builder.src.renderer.html import render_page

NAME     = "design.render.page"
CATEGORY = "design"
OBJECT   = "render"
ACTION   = "page"
VERSION  = "2.0.0"

INPUTS = {
    "project_name":  {"type": "str",       "required": True,  "description": "Nom du projet / marque"},
    "brief_text":    {"type": "str",       "required": True,  "description": "Description du projet"},
    "site_family":   {"type": "str",       "required": False, "description": "Famille : product_saas | brand_landing | editorial_magazine | studio_portfolio | ecommerce_catalog | event_campaign"},
    "seed":          {"type": "int",       "required": False, "description": "Seed déterministe (default: 42)"},
    "cp_palette":    {"type": "dict|None", "required": False, "description": "Palette couleurs (design.palette.generate)"},
    "visual_intent": {"type": "dict|None", "required": False, "description": "Intent visuel (design.visual_intent.generate) — typo, mood, hero"},
    "plan":          {"type": "dict|None", "required": False, "description": "Design plan (design.plan.generate) — layout hero"},
}

OUTPUTS = {
    "html":         {"type": "str", "description": "HTML complet — Eurkai DOM Library"},
    "project_name": {"type": "str", "description": "Echo project_name"},
    "seed":         {"type": "int", "description": "Echo seed"},
    "site_family":  {"type": "str", "description": "Echo site_family"},
}


def run(
    project_name:  str,
    brief_text:    str,
    site_family:   str = "",
    seed:          int = 42,
    cp_palette:    dict | None = None,
    visual_intent: dict | None = None,
    plan:          dict | None = None,
    # Paramètres legacy conservés pour compat descendante (ignorés)
    dna=None,
    exploration=None,
    preset: dict | None = None,
    css:    str  | None = None,
) -> dict:
    """
    Génère une page HTML via l'Eurkai DOM Library.

    Structure DOM : uniquement blocs v0.2 page_builder (NavBar, Hero, Stat, Steps,
    Pricing, Testimonial, CTA, Footer, …).
    Tokens CSS injectés depuis la palette pipeline via generate_page_css().
    """
    page = assemble_page(
        project_name=project_name,
        brief_text=brief_text,
        cp_palette=cp_palette,
        site_family=site_family,
        seed=seed,
        visual_intent=visual_intent,
        plan=plan,
    )

    html = render_page(page)

    # CSS supplémentaire optionnel (ex: theme.css du pipeline brand charter)
    if css:
        html = html.replace("</style>", f"\n/* extra */\n{css}\n</style>", 1)

    return {
        "html":         html,
        "project_name": project_name,
        "seed":         seed,
        "site_family":  site_family,
    }
