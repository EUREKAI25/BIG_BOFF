"""
visual_consistency_validator.router
─────────────────────────────────────
POST /v1/design/validate

Corps :
{
  "design_dna": {
    "style_archetype": "startup_clean",
    "typography_style": "geometric_sans",
    "icon_style": "line",
    "layout_style": "clean_grid",
    "visual_style": "minimal_tech",
    "image_style": "soft_light_photography",
    "composition_style": "balanced_asymmetric",
    "motion_energy": "subtle",
    "palette_bias": {
      "preferred_colors": ["electric_blue", "navy"],
      "avoid_colors": ["deep_red"],
      "saturation_level": "medium",
      "color_temperature": "cold"
    }
  },
  "palette": {
    "primary_colors": ["#1a53ff", "#001f5c"],
    "accent_colors": ["#00ffff"],
    "neutral_colors": ["#f5f5f5", "#111111"],
    "saturation_level": "high",
    "color_temperature": "cold"
  },
  "typography": {
    "style": "geometric_sans",
    "weight_hint": "medium"
  },
  "icons": {
    "style": "line",
    "corner_radius": "slightly_rounded",
    "weight": "regular"
  },
  "ui_theme": {
    "layout_style": "clean_grid",
    "visual_style": "minimal_tech",
    "spacing_type": "balanced",
    "border_radius": "small"
  }
}

Réponse :
{
  "status": "valid",
  "overall_score": 0.91,
  "palette_score": 0.92,
  "typography_score": 1.0,
  "icon_style_score": 0.95,
  "visual_style_score": null,
  "layout_score": 0.93,
  "warnings": [],
  "suggestions": [],
  "threshold": 0.80
}
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import dataclasses

try:
    from fastapi import APIRouter
    from pydantic import BaseModel, Field
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from .validator import validate
from .schemas import (
    ValidationInput,
    LogoAsset, PaletteAsset, TypographyAsset,
    IconAsset, UIThemeAsset, VisualAsset,
)


if _FASTAPI_AVAILABLE:

    class PaletteBiasModel(BaseModel):
        preferred_colors:   List[str] = Field(default_factory=list)
        accent_candidates:  List[str] = Field(default_factory=list)
        neutral_candidates: List[str] = Field(default_factory=list)
        avoid_colors:       List[str] = Field(default_factory=list)
        saturation_level:   str = "medium"
        color_temperature:  str = "neutral"

    class LogoAssetModel(BaseModel):
        style_archetype:   Optional[str] = None
        logo_structure:    Optional[str] = None
        palette_colors:    List[str]     = Field(default_factory=list)
        typography_style:  Optional[str] = None
        icon_style:        Optional[str] = None
        composition_style: Optional[str] = None

    class PaletteAssetModel(BaseModel):
        primary_colors:    List[str] = Field(default_factory=list)
        accent_colors:     List[str] = Field(default_factory=list)
        neutral_colors:    List[str] = Field(default_factory=list)
        saturation_level:  Optional[str] = None
        color_temperature: Optional[str] = None
        harmony_type:      Optional[str] = None

    class TypographyAssetModel(BaseModel):
        style:         Optional[str] = None
        font_family:   Optional[str] = None
        weight_hint:   Optional[str] = None
        pairing_style: Optional[str] = None

    class IconAssetModel(BaseModel):
        style:         Optional[str] = None
        corner_radius: Optional[str] = None
        weight:        Optional[str] = None

    class UIThemeAssetModel(BaseModel):
        layout_style:  Optional[str] = None
        visual_style:  Optional[str] = None
        spacing_type:  Optional[str] = None
        border_radius: Optional[str] = None

    class VisualAssetModel(BaseModel):
        image_style:       Optional[str] = None
        composition_style: Optional[str] = None
        motion_energy:     Optional[str] = None
        color_palette:     List[str]     = Field(default_factory=list)

    class ValidateRequest(BaseModel):
        design_dna: Dict[str, Any] = Field(default_factory=dict)
        threshold:  float           = 0.80
        logo:       Optional[LogoAssetModel]       = None
        palette:    Optional[PaletteAssetModel]    = None
        typography: Optional[TypographyAssetModel] = None
        icons:      Optional[IconAssetModel]       = None
        ui_theme:   Optional[UIThemeAssetModel]    = None
        visuals:    Optional[VisualAssetModel]     = None

    router = APIRouter(tags=["visual_consistency_validator"])

    @router.post("/v1/design/validate")
    async def validate_design(request: ValidateRequest):
        input_data = ValidationInput(
            design_dna = request.design_dna,
            logo       = LogoAsset(**request.logo.model_dump())       if request.logo       else None,
            palette    = PaletteAsset(**request.palette.model_dump()) if request.palette    else None,
            typography = TypographyAsset(**request.typography.model_dump()) if request.typography else None,
            icons      = IconAsset(**request.icons.model_dump())      if request.icons      else None,
            ui_theme   = UIThemeAsset(**request.ui_theme.model_dump()) if request.ui_theme  else None,
            visuals    = VisualAsset(**request.visuals.model_dump())   if request.visuals   else None,
        )
        report = validate(input_data, threshold=request.threshold)

        # Sérialiser en dict (exclure les CheckResults détaillés de la réponse top-level)
        result = dataclasses.asdict(report)
        # Simplifier la réponse : retirer checks (verbeux) sauf si demandé
        result.pop("checks", None)
        return result

else:
    router = None
