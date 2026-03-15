"""
design_exploration_engine.router
──────────────────────────────────
POST /v1/design/explore

Corps :
{
  "design_dna": {
    "style_archetype": "startup_clean",
    "industry": "finance",
    "brand_values": ["trust", "innovation"],
    "tone": "modern_premium",
    "target_audience": "young_professionals",
    "palette_bias": {
      "preferred_colors": ["electric_blue", "navy"]
    }
  },
  "n_directions": 3
}

Réponse :
{
  "source_archetype": "startup_clean",
  "directions": [
    {
      "id": "direction_1",
      "name": "Clean Tech",
      "tagline": "Clarté moderne, efficacité maximale",
      "style_archetype": "startup_clean",
      "palette_bias": ["electric_blue", "navy", "indigo", "cyan", "teal"],
      "typography_style": "geometric_sans",
      "icon_style": "line",
      "visual_style": "minimal_tech",
      "layout_style": "clean_grid",
      "logo_structure_hint": "icon_wordmark",
      "direction_family": "clean_modern",
      "differentiation": ["Fidèle au brief initial", "Direction de référence"],
      "confidence": 1.0
    },
    {
      "id": "direction_2",
      "name": "Corporate Pro",
      "tagline": "Confiance professionnelle, image institutionnelle",
      "style_archetype": "corporate_pro",
      ...
    },
    {
      "id": "direction_3",
      "name": "Editorial Bold",
      "style_archetype": "editorial_magazine",
      ...
    }
  ],
  "trace": {
    "n_requested": 3,
    "n_generated": 3,
    "archetypes": ["startup_clean", "corporate_pro", "editorial_magazine"]
  }
}
"""

from __future__ import annotations
import dataclasses
from typing import Any, Dict, Optional

try:
    from fastapi import APIRouter
    from pydantic import BaseModel, Field
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from .direction_generator import generate_directions
from .schemas import ExplorationInput


if _FASTAPI_AVAILABLE:

    class ExploreRequest(BaseModel):
        design_dna:   Dict[str, Any] = Field(default_factory=dict)
        n_directions: int            = 3

    router = APIRouter(tags=["design_exploration_engine"])

    @router.post("/v1/design/explore")
    async def explore_design(request: ExploreRequest):
        input_data = ExplorationInput(
            design_dna   = request.design_dna,
            n_directions = request.n_directions,
        )
        output = generate_directions(input_data)
        return dataclasses.asdict(output)

else:
    router = None
