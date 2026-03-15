"""
palette_generator.router
──────────────────────────
Endpoint FastAPI : POST /v1/palette/generate

Corps de la requête :
{
  "scenario": "ui_palette",
  "base_color": "#3B82F6",
  "base_colors": [],
  "brand_dna": {
    "palette": ["#3B82F6"],
    "style_tags": ["minimal", "tech"],
    "tone": "modern"
  },
  "palette_style": "cool",
  "metal_finish": "titanium",
  "wcag_level": "AA",
  "output_dir": "/tmp/palettes/acme"
}

Réponse :
{
  "base_hex": "#3B82F6",
  "scenario": "ui_palette",
  "monochromatic": { "harmony": "...", "primary": [...], ... },
  "complementary": {...},
  "minimal": {...},
  "ui_safe": {...},
  "black_and_white_variant": { "false_blacks": [...], "false_whites": [...] },
  "accessibility_report": { "all_aa_pass": true, "checks": [...] },
  "export_paths": { "json": "...", "tokens": "...", "svg": "..." },
  "trace": {...}
}
"""

from __future__ import annotations
from typing import Optional

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from .schemas import PaletteScenario, MetalFinish, WCAGLevel, BrandDNAInput, PaletteInput
from .generator import generate_palette
from .palette_exporter import _palette_set_to_dict


if _FASTAPI_AVAILABLE:

    class BrandDNABody(BaseModel):
        brand_name:   Optional[str]  = None
        tone:         Optional[str]  = None
        style_tags:   list[str]      = Field(default_factory=list)
        palette:      list[str]      = Field(default_factory=list)
        brand_values: list[str]      = Field(default_factory=list)

    class PaletteGenerateRequest(BaseModel):
        scenario:      str  = "brand_palette"
        base_color:    Optional[str]       = None
        base_colors:   list[str]           = Field(default_factory=list)
        brand_dna:     Optional[BrandDNABody] = None
        style_tags:    list[str]           = Field(default_factory=list)
        palette_style: Optional[str]       = None
        metal_finish:  Optional[str]       = None
        wcag_level:    str                 = "AA"
        output_dir:    Optional[str]       = None

    router = APIRouter(tags=["palette_generator"])

    @router.post("/v1/palette/generate")
    async def generate(request: PaletteGenerateRequest):
        try:
            scenario = PaletteScenario(request.scenario)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"scenario invalide: {request.scenario}. "
                       f"Valeurs: {[e.value for e in PaletteScenario]}"
            )

        metal_finish = None
        if request.metal_finish:
            try:
                metal_finish = MetalFinish(request.metal_finish)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"metal_finish invalide: {request.metal_finish}. "
                           f"Valeurs: {[e.value for e in MetalFinish]}"
                )

        wcag_level = WCAGLevel.AA
        if request.wcag_level:
            try:
                wcag_level = WCAGLevel(request.wcag_level)
            except ValueError:
                pass

        brand_dna = None
        if request.brand_dna:
            d = request.brand_dna
            brand_dna = BrandDNAInput(
                brand_name=d.brand_name,
                tone=d.tone,
                style_tags=d.style_tags,
                palette=d.palette,
                brand_values=d.brand_values,
            )

        input_data = PaletteInput(
            scenario=scenario,
            base_color=request.base_color,
            base_colors=request.base_colors,
            brand_dna=brand_dna,
            style_tags=request.style_tags,
            palette_style=request.palette_style,
            metal_finish=metal_finish,
            wcag_level=wcag_level,
        )

        try:
            output = generate_palette(
                input_data=input_data,
                output_dir=request.output_dir,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        result = _palette_set_to_dict(output.palette_set)
        result["export_paths"] = output.export_paths
        result["trace"] = output.trace
        return result

else:
    router = None
