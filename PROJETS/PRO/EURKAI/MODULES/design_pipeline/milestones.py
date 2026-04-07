"""
milestones — 9 milestones du pipeline design v2.

Chaque milestone est une fonction run(context) → (context, output).
Chaque milestone utilise standard_milestone_run sans exception.

Ordre d'exécution :
  1. derive_context
  2. choose_visual_family
  3. choose_palette_family
  4. choose_typography_family
  5. choose_layout_strategy
  6. choose_hero_type
  7. compose_design_plan
  8. validate_design_plan
  9. render_from_plan
"""

from __future__ import annotations
import re
from typing import Any

from .milestone_runner import standard_milestone_run, seed_select, MilestoneError
from .option_pools import (
    VISUAL_FAMILIES, LAYOUT_STRATEGIES, HERO_TYPES,
    PALETTE_FAMILIES, TYPOGRAPHY_FAMILIES, SECTION_FLOWS,
    ALLOWED_LAYOUTS, ALLOWED_HEROES, HERO_CONFIG, COMPOSITION_PATTERNS,
)


# ─────────────────────────────────────────────────────────────────────────────
# MILESTONE 1 — derive_context
# ─────────────────────────────────────────────────────────────────────────────

_PRODUCT_TYPE_SIGNALS = {
    "saas":        ["saas", "logiciel", "plateforme", "app", "software", "outil"],
    "ecommerce":   ["boutique", "shop", "produit", "vente", "e-commerce", "collection"],
    "editorial":   ["magazine", "media", "journal", "publication", "article", "contenu"],
    "luxury":      ["luxe", "luxury", "prestige", "premium", "exclusif", "haut de gamme"],
    "food_drink":  ["restaurant", "distillerie", "brasserie", "traiteur", "gastronomie", "vin", "café"],
    "health":      ["santé", "bien-être", "médical", "thérapie", "soin", "clinique"],
    "creative":    ["studio", "agence", "design", "créatif", "artiste", "portfolio"],
    "corporate":   ["entreprise", "cabinet", "conseil", "audit", "juridique", "finance"],
    "event":       ["événement", "festival", "concert", "conférence", "salon"],
    "education":   ["formation", "école", "cours", "apprentissage", "certification"],
}

_EMOTIONAL_GOAL_SIGNALS = {
    "trust":        ["confiance", "fiable", "sécurisé", "garanti", "certifié", "sérieux"],
    "excitement":   ["innovation", "nouveau", "révolutionnaire", "disruptif", "pionnier"],
    "desire":       ["premium", "exclusif", "luxe", "rare", "unique", "collector"],
    "calm":         ["naturel", "zen", "serein", "doux", "organique", "bien-être"],
    "curiosity":    ["découverte", "exploration", "mystère", "inattendu", "créatif"],
    "authority":    ["expert", "référence", "leader", "depuis", "ans d'expérience", "spécialiste"],
}

_POSITIONING_SIGNALS = {
    "premium":      ["premium", "luxe", "haut de gamme", "prestige", "artisanal", "craft"],
    "challenger":   ["différent", "disruption", "alternative", "innovation", "bousculer"],
    "accessible":   ["accessible", "simple", "tout le monde", "abordable", "facile"],
    "expert":       ["expert", "spécialiste", "professionnel", "certifié", "maîtrise"],
    "community":    ["communauté", "ensemble", "partage", "collectif", "mouvement"],
}

def _extract_signals(brief: str, signals_map: dict) -> str:
    """Extrait le signal dominant depuis le brief. Retourne la clé avec le plus de hits."""
    brief_lower = brief.lower()
    scores = {}
    for key, keywords in signals_map.items():
        scores[key] = sum(1 for kw in keywords if kw in brief_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else list(signals_map.keys())[0]


def run_derive_context(context: dict) -> tuple[dict, dict]:
    brief = context.get("brief", "")

    # Pas de randomness — déduction pure
    def option_resolver(inp, ctx):
        return [{
            "product_type":   _extract_signals(brief, _PRODUCT_TYPE_SIGNALS),
            "emotional_goal": _extract_signals(brief, _EMOTIONAL_GOAL_SIGNALS),
            "positioning":    _extract_signals(brief, _POSITIONING_SIGNALS),
            "brief_length":   "short" if len(brief) < 100 else "medium" if len(brief) < 300 else "long",
        }]

    def selection_rules(options, inp, ctx):
        return options[0]  # déterministe — un seul résultat possible

    return standard_milestone_run(
        context=context,
        milestone_ident="derive_context",
        input_object=brief,
        option_resolver=option_resolver,
        selection_rules=selection_rules,
        output_schema={"product_type": None, "emotional_goal": None, "positioning": None},
        validators=[],
    )


# ─────────────────────────────────────────────────────────────────────────────
# MILESTONE 2 — choose_visual_family
# ─────────────────────────────────────────────────────────────────────────────

_PRODUCT_TO_FAMILIES = {
    "saas":       ["startup_clean", "tech_futurist", "corporate_pro"],
    "ecommerce":  ["warm_human", "playful_brand", "bold_challenger"],
    "editorial":  ["editorial_magazine", "premium_craft", "luxury_minimal"],
    "luxury":     ["luxury_minimal", "premium_craft", "editorial_magazine"],
    "food_drink": ["warm_human", "organic_natural", "premium_craft"],
    "health":     ["organic_natural", "warm_human", "luxury_minimal"],
    "creative":   ["creative_studio", "bold_challenger", "editorial_magazine"],
    "corporate":  ["corporate_pro", "startup_clean", "premium_craft"],
    "event":      ["bold_challenger", "playful_brand", "creative_studio"],
    "education":  ["startup_clean", "warm_human", "corporate_pro"],
}


def run_choose_visual_family(context: dict) -> tuple[dict, str]:
    derived = context.get("derive_context", {})
    product_type = derived.get("product_type", "saas")

    def option_resolver(inp, ctx):
        return _PRODUCT_TO_FAMILIES.get(product_type, VISUAL_FAMILIES[:4])

    def selection_rules(options, inp, ctx):
        return seed_select(options, ctx, "choose_visual_family")

    def validate_in_pool(output, ctx):
        return (output in VISUAL_FAMILIES, f"{output!r} not in VISUAL_FAMILIES")

    return standard_milestone_run(
        context=context,
        milestone_ident="choose_visual_family",
        input_object=derived,
        option_resolver=option_resolver,
        selection_rules=selection_rules,
        output_schema={},
        validators=[validate_in_pool],
    )


# ─────────────────────────────────────────────────────────────────────────────
# MILESTONE 3 — choose_palette_family
# ─────────────────────────────────────────────────────────────────────────────

def run_choose_palette_family(context: dict) -> tuple[dict, str]:
    visual_family = context.get("choose_visual_family", "startup_clean")

    def option_resolver(inp, ctx):
        return PALETTE_FAMILIES.get(visual_family, ["startup_blue"])

    def selection_rules(options, inp, ctx):
        return seed_select(options, ctx, "choose_palette_family")

    return standard_milestone_run(
        context=context,
        milestone_ident="choose_palette_family",
        input_object=visual_family,
        option_resolver=option_resolver,
        selection_rules=selection_rules,
        output_schema={},
        validators=[],
    )


# ─────────────────────────────────────────────────────────────────────────────
# MILESTONE 4 — choose_typography_family
# ─────────────────────────────────────────────────────────────────────────────

def run_choose_typography_family(context: dict) -> tuple[dict, str]:
    visual_family = context.get("choose_visual_family", "startup_clean")

    def option_resolver(inp, ctx):
        return TYPOGRAPHY_FAMILIES.get(visual_family, ["geometric_sans"])

    def selection_rules(options, inp, ctx):
        return seed_select(options, ctx, "choose_typography_family")

    return standard_milestone_run(
        context=context,
        milestone_ident="choose_typography_family",
        input_object=visual_family,
        option_resolver=option_resolver,
        selection_rules=selection_rules,
        output_schema={},
        validators=[],
    )


# ─────────────────────────────────────────────────────────────────────────────
# MILESTONE 5 — choose_layout_strategy
# ─────────────────────────────────────────────────────────────────────────────

def run_choose_layout_strategy(context: dict) -> tuple[dict, str]:
    visual_family = context.get("choose_visual_family", "startup_clean")

    def option_resolver(inp, ctx):
        return ALLOWED_LAYOUTS.get(visual_family, LAYOUT_STRATEGIES[:4])

    def selection_rules(options, inp, ctx):
        return seed_select(options, ctx, "choose_layout_strategy")

    def validate_in_pool(output, ctx):
        all_layouts = list(SECTION_FLOWS.keys())
        return (output in all_layouts, f"{output!r} has no SECTION_FLOW defined")

    return standard_milestone_run(
        context=context,
        milestone_ident="choose_layout_strategy",
        input_object=visual_family,
        option_resolver=option_resolver,
        selection_rules=selection_rules,
        output_schema={},
        validators=[validate_in_pool],
    )


# ─────────────────────────────────────────────────────────────────────────────
# MILESTONE 6 — choose_hero_type
# ─────────────────────────────────────────────────────────────────────────────

def run_choose_hero_type(context: dict) -> tuple[dict, str]:
    layout_strategy = context.get("choose_layout_strategy", "staggered_blocks")

    def option_resolver(inp, ctx):
        return ALLOWED_HEROES.get(layout_strategy, HERO_TYPES[:3])

    def selection_rules(options, inp, ctx):
        return seed_select(options, ctx, "choose_hero_type")

    def validate_has_config(output, ctx):
        return (output in HERO_CONFIG, f"{output!r} has no HERO_CONFIG entry")

    return standard_milestone_run(
        context=context,
        milestone_ident="choose_hero_type",
        input_object=layout_strategy,
        option_resolver=option_resolver,
        selection_rules=selection_rules,
        output_schema={},
        validators=[validate_has_config],
    )


# ─────────────────────────────────────────────────────────────────────────────
# MILESTONE 7 — compose_design_plan
# ─────────────────────────────────────────────────────────────────────────────

def run_compose_design_plan(context: dict) -> tuple[dict, dict]:
    layout_strategy  = context.get("choose_layout_strategy",  "staggered_blocks")
    hero_type        = context.get("choose_hero_type",        "centered_statement")
    visual_family    = context.get("choose_visual_family",    "startup_clean")
    palette_family   = context.get("choose_palette_family",   "startup_blue")
    typography_family= context.get("choose_typography_family","geometric_sans")

    def option_resolver(inp, ctx):
        section_types = SECTION_FLOWS.get(layout_strategy, SECTION_FLOWS["staggered_blocks"])
        hero_cfg      = HERO_CONFIG.get(hero_type, HERO_CONFIG["centered_statement"])
        composition   = COMPOSITION_PATTERNS.get(layout_strategy, {"density": "medium", "grid": "12col"})

        return [{
            "layout_strategy":   layout_strategy,
            "hero_type":         hero_type,
            "hero_config":       hero_cfg,
            "visual_family":     visual_family,
            "palette_family":    palette_family,
            "typography_family": typography_family,
            "section_types":     section_types,
            "composition":       composition,
            "seed":              context.get("seed", 42),
        }]

    def selection_rules(options, inp, ctx):
        return options[0]  # composition pure — un seul résultat

    def validate_sections(output, ctx):
        sections = output.get("section_types", [])
        if len(sections) < 4:
            return (False, f"section_types needs ≥4, got {len(sections)}")
        if sections[0] != "hero":
            return (False, "section_types[0] must be 'hero'")
        if sections[-1] != "cta_block":
            return (False, "section_types[-1] must be 'cta_block'")
        return (True, "ok")

    def validate_hero_config(output, ctx):
        hero_cfg = output.get("hero_config", {})
        required = ["min_height", "text_position", "layout_class"]
        missing = [k for k in required if k not in hero_cfg]
        return (not missing, f"hero_config missing: {missing}")

    return standard_milestone_run(
        context=context,
        milestone_ident="compose_design_plan",
        input_object={"layout_strategy": layout_strategy, "hero_type": hero_type},
        option_resolver=option_resolver,
        selection_rules=selection_rules,
        output_schema={"layout_strategy": None, "hero_type": None, "section_types": None},
        validators=[validate_sections, validate_hero_config],
    )


# ─────────────────────────────────────────────────────────────────────────────
# MILESTONE 8 — validate_design_plan
# ─────────────────────────────────────────────────────────────────────────────

def run_validate_design_plan(context: dict) -> tuple[dict, dict]:
    plan = context.get("compose_design_plan", {})

    def option_resolver(inp, ctx):
        return [inp]  # on valide le plan tel quel, pas de choix

    def selection_rules(options, inp, ctx):
        return options[0]

    def validate_no_orphan_sections(output, ctx):
        sections = output.get("section_types", [])
        known = set(s for flow in SECTION_FLOWS.values() for s in flow)
        unknown = [s for s in sections if s not in known]
        return (not unknown, f"unknown section types: {unknown}")

    def validate_layout_has_hero(output, ctx):
        layout = output.get("layout_strategy", "")
        hero   = output.get("hero_type", "")
        allowed = ALLOWED_HEROES.get(layout, [])
        return (hero in allowed, f"hero_type {hero!r} not allowed for layout {layout!r}")

    return standard_milestone_run(
        context=context,
        milestone_ident="validate_design_plan",
        input_object=plan,
        option_resolver=option_resolver,
        selection_rules=selection_rules,
        output_schema={"layout_strategy": None, "section_types": None},
        validators=[validate_no_orphan_sections, validate_layout_has_hero],
    )


# ─────────────────────────────────────────────────────────────────────────────
# MILESTONE 9 — render_from_plan
# ─────────────────────────────────────────────────────────────────────────────

def run_render_from_plan(context: dict) -> tuple[dict, str]:
    from .render_strict import render_from_plan as _render

    plan   = context.get("validate_design_plan", context.get("compose_design_plan", {}))
    palette = context.get("palette", {})

    def option_resolver(inp, ctx):
        return [_render(plan, ctx, palette)]

    def selection_rules(options, inp, ctx):
        return options[0]

    def validate_non_empty(output, ctx):
        return (bool(output) and "<html" in output, "render produced empty or invalid HTML")

    return standard_milestone_run(
        context=context,
        milestone_ident="render_from_plan",
        input_object=plan,
        option_resolver=option_resolver,
        selection_rules=selection_rules,
        output_schema={},
        validators=[validate_non_empty],
    )


# ─────────────────────────────────────────────────────────────────────────────
# SÉQUENCE COMPLÈTE
# ─────────────────────────────────────────────────────────────────────────────

PIPELINE_MILESTONES = [
    ("derive_context",       run_derive_context),
    ("choose_visual_family", run_choose_visual_family),
    ("choose_palette_family",run_choose_palette_family),
    ("choose_typography_family", run_choose_typography_family),
    ("choose_layout_strategy",   run_choose_layout_strategy),
    ("choose_hero_type",         run_choose_hero_type),
    ("compose_design_plan",      run_compose_design_plan),
    ("validate_design_plan",     run_validate_design_plan),
    ("render_from_plan",         run_render_from_plan),
]
