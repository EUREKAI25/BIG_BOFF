"""
design.palette.generate
Endpoint : génère une palette couleur depuis le visual_intent.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from color_palette.src.color_palette import generate_palette as _fn

NAME     = "design.palette.generate"
CATEGORY = "design"
OBJECT   = "palette"
ACTION   = "generate"
VERSION  = "1.0.0"

INPUTS = {
    "visual_intent": {"type": "dict",       "required": True,  "description": "From design.visual_intent.generate"},
    "context":       {"type": "dict|None",  "required": False, "description": "{mode, name, family} — palette context"},
}

OUTPUTS = {
    "palette": {"type": "dict", "description": "Color palette: primary, background, text_primary, accent, body_text_grade, ..."},
}


def run(
    visual_intent: dict,
    context: dict | None = None,
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS
    """
    return _fn(visual_intent=visual_intent, context=context)
