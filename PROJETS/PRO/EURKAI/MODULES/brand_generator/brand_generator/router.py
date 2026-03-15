"""
brand_generator.router
───────────────────────
Endpoint FastAPI : POST /v1/brand/directions

Corps de la requête :
{
  "project_brief": "Plateforme SaaS B2B de gestion RH...",
  "brand_dna": {
    "brand_name": "Acme",
    "slogan": "Built for teams",
    "sector": "saas",
    "style_tags": ["modern", "trustworthy"],
    "palette": ["#0A1628", "#3B82F6"],
    "tone": "professional"
  },
  "sector": "saas",           // optionnel, surcharge brand_dna.sector
  "audience": "HR managers, B2B",
  "positioning": "premium but accessible"
}

Réponse :
{
  "direction_A": {
    "name": "Clarity",
    "description": "...",
    "design_intent": "...",
    "style_tags": [...],
    "mood_keywords": [...],
    "palette_profile": { "palette_type": "monochromatic", ... },
    "typography_profile": { "personality": "geometric sans", ... },
    "icon_style": "minimal",
    "logo_structure": "icon_wordmark",
    ...
  },
  "direction_B": { ... },
  "direction_C": { ... },
  "trace": { ... }
}
"""

from __future__ import annotations
import time
from typing import Optional

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from .schemas import BrandDNA, BrandGeneratorInput
from .generator import generate_brand_directions


if _FASTAPI_AVAILABLE:

    class BrandDNAInput(BaseModel):
        brand_name:  str
        slogan:      Optional[str]  = None
        sector:      Optional[str]  = None
        style_tags:  list[str]      = Field(default_factory=list)
        palette:     list[str]      = Field(default_factory=list)
        typography:  list[str]      = Field(default_factory=list)
        tone:        Optional[str]  = None
        target:      Optional[str]  = None

    class BrandDirectionsRequest(BaseModel):
        project_brief:  str
        brand_dna:      BrandDNAInput
        sector:         Optional[str] = None
        audience:       Optional[str] = None
        positioning:    Optional[str] = None
        model:          str           = "claude-sonnet"

    # ─── Router ───────────────────────────────────────────────────────────────

    router = APIRouter(tags=["brand_generator"])

    def _get_llm_executor():
        try:
            from eurkai.llm_executor import llm_executor
            return llm_executor
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="llm_executor EURKAI non disponible."
            )

    @router.post("/v1/brand/directions")
    async def generate_directions(request: BrandDirectionsRequest):
        llm_executor = _get_llm_executor()

        # Construire BrandDNA
        d = request.brand_dna
        brand_dna = BrandDNA(
            brand_name=d.brand_name,
            slogan=d.slogan,
            sector=d.sector,
            style_tags=d.style_tags,
            palette=d.palette,
            typography=d.typography,
            tone=d.tone,
            target=d.target,
        )

        input_data = BrandGeneratorInput(
            project_brief=request.project_brief,
            brand_dna=brand_dna,
            sector=request.sector,
            audience=request.audience,
            positioning=request.positioning,
        )

        try:
            output = generate_brand_directions(
                input_data=input_data,
                llm_executor=llm_executor,
                model=request.model,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        result = output.as_dict()
        result["trace"] = output.trace
        return result

else:
    router = None
