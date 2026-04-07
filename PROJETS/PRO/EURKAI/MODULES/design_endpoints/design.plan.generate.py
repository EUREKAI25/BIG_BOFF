"""
design.plan.generate
Endpoint : génère un DesignPlan déterministe depuis le brief + intent.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from design_plan.src.design_plan import generate_design_plan as _fn

NAME     = "design.plan.generate"
CATEGORY = "design"
OBJECT   = "plan"
ACTION   = "generate"
VERSION  = "1.0.0"

INPUTS = {
    "brief":              {"type": "str",       "required": True,  "description": "Brand/project description"},
    "seed":               {"type": "int",       "required": False, "description": "Determinism seed (default: 42)"},
    "visual_intent":      {"type": "dict|None", "required": False, "description": "From design.visual_intent.generate"},
    "reference_analysis": {"type": "dict|None", "required": False, "description": "From design.coherence.apply — CASE 3 hard overrides"},
    "style_dna":          {"type": "dict|None", "required": False, "description": "Style DNA"},
    "theme_hints":        {"type": "dict|None", "required": False, "description": "Theme hints"},
}

OUTPUTS = {
    "plan": {"type": "dict", "description": "Serialized DesignPlan: layout_strategy, hero, composition, visual_tension, rhythm, constraints, section_types, cta_strategy, seed, brief_profile"},
}


def run(
    brief: str,
    seed: int = 42,
    visual_intent: dict | None = None,
    reference_analysis: dict | None = None,
    style_dna: dict | None = None,
    theme_hints: dict | None = None,
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → DesignPlan sérialisé (dict)

    reference_analysis (CASE 3) est appliqué en hard override :
    profile, density, tension, layout_boost priment sur visual_intent.
    """
    plan = _fn(
        brief=brief,
        seed=seed,
        style_dna=style_dna,
        theme_hints=theme_hints,
        visual_intent=visual_intent,
        reference_analysis=reference_analysis,
    )
    return plan.to_dict()
