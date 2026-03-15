"""
color_psychology_engine.router
────────────────────────────────
Endpoint FastAPI : POST /v1/color/psychology

Corps :
{
  "industry": "finance",
  "brand_values": ["trust", "innovation"],
  "tone": "premium",
  "target_audience": "professionals",
  "region": "global",
  "style_tags": ["minimal", "tech"]
}

Réponse :
{
  "preferred_colors": ["navy", "deep_blue", "indigo", "electric_blue"],
  "accent_candidates": ["gold", "cyan", "silver"],
  "neutral_candidates": ["cool_gray", "charcoal", "off_white"],
  "avoid_colors": ["neon_orange", "hot_pink", "lime", "acid_green"],
  "saturation_level": "medium",
  "contrast_style": "clean",
  "color_temperature": "cool",
  "dominant_emotion": "trust",
  "confidence": 0.87
}
"""

from __future__ import annotations
from typing import Optional

try:
    from fastapi import APIRouter
    from pydantic import BaseModel, Field
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from .schemas import PsychologyInput
from .suggestion_resolver import resolve


if _FASTAPI_AVAILABLE:

    class PsychologyRequest(BaseModel):
        industry:        Optional[str]  = None
        brand_values:    list[str]      = Field(default_factory=list)
        tone:            Optional[str]  = None
        target_audience: Optional[str]  = None
        region:          Optional[str]  = None
        style_tags:      list[str]      = Field(default_factory=list)

    router = APIRouter(tags=["color_psychology_engine"])

    @router.post("/v1/color/psychology")
    async def psychology(request: PsychologyRequest):
        from dataclasses import asdict
        input_data = PsychologyInput(
            industry=request.industry,
            brand_values=request.brand_values,
            tone=request.tone,
            target_audience=request.target_audience,
            region=request.region,
            style_tags=request.style_tags,
        )
        result = resolve(input_data)
        return asdict(result)

else:
    router = None
