"""
design.visual_intent.generate
Endpoint : génère le visual_intent depuis un brief textuel.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from visual_intent_engine.src.visual_intent_engine import generate_visual_intent as _fn

NAME     = "design.visual_intent.generate"
CATEGORY = "design"
OBJECT   = "visual_intent"
ACTION   = "generate"
VERSION  = "1.0.0"

INPUTS = {
    "brief":              {"type": "str",       "required": True,  "description": "Brand/project description"},
    "style_dna":          {"type": "dict|None", "required": False, "description": "Style DNA overrides"},
    "constraints":        {"type": "dict|None", "required": False, "description": "Hard constraints on intent"},
    "reference_image":    {"type": "str|None",  "required": False, "description": "Path to reference image (CASE 1)"},
    "reference_type":     {"type": "str|None",  "required": False, "description": "none | image | screenshot | mockup"},
    "reference_analysis": {"type": "dict|None", "required": False, "description": "Structural analysis from design.coherence.apply (CASE 3)"},
}

OUTPUTS = {
    "visual_intent": {"type": "dict", "description": "Full visual intent: emotion, mood, archetype, composition_bias, typography_strategy, color_strategy, ..."},
}


def run(
    brief: str,
    style_dna: dict | None = None,
    constraints: dict | None = None,
    reference_image: str | None = None,
    reference_type: str | None = None,
    reference_analysis: dict | None = None,
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS
    """
    return _fn(
        brief=brief,
        style_dna=style_dna,
        constraints=constraints,
        reference_image=reference_image,
        reference_type=reference_type,
        reference_analysis=reference_analysis,
    )
