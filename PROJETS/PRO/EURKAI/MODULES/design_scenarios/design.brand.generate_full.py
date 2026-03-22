"""
design.brand.generate_full — EURKAI Design Scenario
Scénario : pipeline brand identity complet depuis brief.

Pipeline :
    1. design.visual_intent.generate
    2. design.palette.generate
    3. design.brand.generate
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[3]
_EP   = _ROOT / "MODULES" / "design_endpoints"
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from _ep_loader import load_endpoint  # noqa

# ── Metadata ──────────────────────────────────────────────────────────────────

NAME    = "design.brand.generate_full"
VERSION = "1.0.0"

STEPS: list[dict] = [
    {"step": 1, "endpoint": "design.visual_intent.generate",
     "description": "Générer le visual intent depuis le brief"},
    {"step": 2, "endpoint": "design.palette.generate",
     "description": "Générer la palette couleur depuis le visual intent"},
    {"step": 3, "endpoint": "design.brand.generate",
     "description": "Générer l'identité visuelle complète"},
]

INPUTS: dict = {
    "brief":       {"type": "str",  "required": True,  "description": "Brand/project description"},
    "context":     {"type": "dict", "required": True,  "description": "{name, mode, family, product_type, ...}"},
    "site_family": {"type": "str",  "required": False, "description": "Famille de site (optionnel, pour contexte)"},
}

OUTPUTS: dict = {
    "brand_identity": {"type": "dict", "description": "Identité complète : brand_core, logo, icons, typography, visual_signature"},
    "visual_intent":  {"type": "dict", "description": "Visual intent intermédiaire"},
    "palette":        {"type": "dict", "description": "Palette couleur intermédiaire"},
    "trace":          {"type": "list", "description": "Trace d'exécution [{step, endpoint, ok}]"},
}

# ── Lazy load ──────────────────────────────────────────────────────────────────

_ep_vi    = None
_ep_pal   = None
_ep_brand = None


def _get_eps():
    global _ep_vi, _ep_pal, _ep_brand
    if _ep_vi is None:
        _ep_vi    = load_endpoint("design.visual_intent.generate")
        _ep_pal   = load_endpoint("design.palette.generate")
        _ep_brand = load_endpoint("design.brand.generate")
    return _ep_vi, _ep_pal, _ep_brand


# ── Scenario ──────────────────────────────────────────────────────────────────

def run(
    brief: str,
    context: dict,
    site_family: str = "",
) -> dict:
    """
    Pipeline brand identity complet depuis brief.

    Args:
        brief      : str  — description de la marque/projet
        context    : dict — {name, mode, family, product_type, ...}
        site_family: str  — optionnel, ajouté au context si fourni

    Returns:
        dict — brand_identity, visual_intent, palette, trace
    """
    ep_vi, ep_pal, ep_brand = _get_eps()
    trace: list[dict] = []

    # Enrichir context avec site_family si fourni
    ctx = dict(context)
    if site_family and "family" not in ctx:
        ctx["family"] = site_family

    # Step 1 — visual_intent
    visual_intent = ep_vi.run(brief=brief)
    trace.append({"step": 1, "endpoint": "design.visual_intent.generate", "ok": True})

    # Step 2 — palette
    palette = ep_pal.run(visual_intent=visual_intent, context=ctx)
    trace.append({"step": 2, "endpoint": "design.palette.generate", "ok": True})

    # Step 3 — brand identity
    brand_identity = ep_brand.run(
        brief=brief,
        visual_intent=visual_intent,
        palette=palette,
        context=ctx,
        reference=None,
    )
    trace.append({"step": 3, "endpoint": "design.brand.generate", "ok": True})

    return {
        "brand_identity": brand_identity,
        "visual_intent":  visual_intent,
        "palette":        palette,
        "trace":          trace,
    }
