"""
design_dna_resolver.router
────────────────────────────
POST /v1/design/dna

Corps :
{
  "project_name": "NovaBank",
  "industry": "finance",
  "values": ["trust", "innovation"],
  "tone": "modern premium",
  "target_audience": "young professionals",
  "keywords": ["digital", "secure", "simple"]
}

Réponse :
{
  "project_name": "NovaBank",
  "industry": "finance",
  "brand_values": ["trust", "innovation"],
  "tone": "modern_premium",
  "target_audience": "young_professionals",
  "style_archetype": "startup_clean",
  "typography_style": "geometric_sans",
  "icon_style": "line",
  "layout_style": "clean_grid",
  "visual_style": "minimal_tech",
  "image_style": "soft_light_photography",
  "composition_style": "balanced_asymmetric",
  "motion_energy": "moderate",
  "logo_structure_hint": "icon_wordmark",
  "wordmark_weight_hint": "medium",
  "palette_bias": {
    "preferred_colors": ["electric_blue", "navy", "indigo"],
    "accent_candidates": ["cyan", "teal", "violet"],
    ...
  },
  "confidence": 0.72,
  "trace": {...}
}
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter
    from pydantic import BaseModel, Field
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from .dna_builder import build_dna


if _FASTAPI_AVAILABLE:
    import dataclasses

    class BriefRequest(BaseModel):
        # Accepte les deux nommages (values / brand_values, etc.)
        project_name:    Optional[str]  = None
        industry:        Optional[str]  = None
        values:          List[str]      = Field(default_factory=list)
        brand_values:    List[str]      = Field(default_factory=list)
        tone:            Optional[str]  = None
        target_audience: Optional[str]  = None
        audience:        Optional[str]  = None
        keywords:        List[str]      = Field(default_factory=list)
        style_tags:      List[str]      = Field(default_factory=list)
        region:          Optional[str]  = None

    router = APIRouter(tags=["design_dna_resolver"])

    @router.post("/v1/design/dna")
    async def resolve_dna(request: BriefRequest):
        # Fusionner values + brand_values, audience + target_audience
        brief_dict: Dict[str, Any] = {
            "project_name":    request.project_name,
            "industry":        request.industry,
            "brand_values":    list(set(request.values + request.brand_values)),
            "tone":            request.tone,
            "target_audience": request.target_audience or request.audience,
            "keywords":        request.keywords,
            "style_tags":      request.style_tags,
            "region":          request.region,
        }
        dna = build_dna(brief_dict)
        return dataclasses.asdict(dna)

else:
    router = None
