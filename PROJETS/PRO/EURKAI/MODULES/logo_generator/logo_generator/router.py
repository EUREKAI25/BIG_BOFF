"""
logo_generator.router
──────────────────────
Endpoint FastAPI : POST /v1/logo/generate

Corps de la requête :
{
  "brand_name": "Acme",
  "slogan": "Built for speed",           // optionnel
  "logo_dna": {                          // champs LogoDNA (optionnels)
    "logo_structure": "icon_wordmark",   // wordmark|monogram|icon_wordmark|emblem|badge|mascot|abstract_symbol|stacked|lettermark
    "sector": "fintech",
    "style_tags": ["minimal", "modern"],
    "palette": ["#0A0A0A", "#F5F5F5"],
    "symbol_preference": "geometric",
    "icon_complexity": "minimal",
    "background_mode": "transparent"
  },
  "arbitration": {                       // optionnel
    "mode": "ai",                        // none|ai|human
    "n_concepts": 5,
    "n_variants": 5,
    "ai_score_threshold": 0.6
  },
  "output_dir": "/tmp/logos"             // optionnel, défaut: /tmp/logo_generator
}

Réponse (mode ai/none) :
{
  "brand_name": "Acme",
  "logo_structure": "icon_wordmark",
  "arbitration_mode": "ai",
  "selected_concept_id": "concept_2_abc123",
  "selected_concept_score": 0.85,
  "flags": [...],
  "variants": [
    {"variant_name": "logo", "file_path": "/tmp/logos/acme/logo.svg"},
    ...
  ],
  "all_concepts": [...],
  "trace": {...}
}

Réponse (mode human) :
{
  "arbitration_mode": "human",
  "all_concepts": [
    {"concept_id": "...", "prompt_used": "...", "score": null, "flags": [...]}
  ],
  "message": "Select a concept_id and re-call /v1/logo/select"
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

from .schemas import (
    LogoDNA, LogoStructure, ArbitrationConfig, ArbitrationMode,
    BackgroundMode, LogoOutput,
)
from .generator import generate_concepts
from .arbitration import select_concept
from .exporter import export_variants


# ─── Pydantic models ──────────────────────────────────────────────────────────

if _FASTAPI_AVAILABLE:
    class LogoDNAInput(BaseModel):
        logo_structure:     Optional[str]   = None   # LogoStructure value
        sector:             Optional[str]   = None
        style_tags:         list[str]       = Field(default_factory=list)
        palette:            list[str]       = Field(default_factory=list)
        typography:         list[str]       = Field(default_factory=list)
        tone:               Optional[str]   = None
        target:             Optional[str]   = None
        symbol_preference:  Optional[str]   = None
        composition_style:  Optional[str]   = None
        wordmark_weight:    Optional[str]   = None
        icon_complexity:    Optional[str]   = None
        background_mode:    str             = "transparent"

    class ArbitrationInput(BaseModel):
        mode:               str     = "ai"
        n_concepts:         int     = 5
        n_variants:         int     = 5
        ai_score_threshold: float   = 0.6

    class LogoGenerateRequest(BaseModel):
        brand_name:  str
        slogan:      Optional[str]              = None
        logo_dna:    Optional[LogoDNAInput]     = None
        arbitration: Optional[ArbitrationInput] = None
        output_dir:  str                        = "/tmp/logo_generator"

    # ─── Router ───────────────────────────────────────────────────────────────

    router = APIRouter(tags=["logo_generator"])

    def _get_model_executor():
        """
        Retourne le model_executor EURKAI.
        Import différé pour éviter la dépendance circulaire au niveau module.
        """
        try:
            from eurkai.model_executor import model_executor
            return model_executor
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="model_executor EURKAI non disponible. "
                       "Vérifier l'installation du package eurkai."
            )

    @router.post("/v1/logo/generate")
    async def generate_logo(request: LogoGenerateRequest):
        t0 = time.time()
        model_executor = _get_model_executor()

        # Construire LogoDNA
        dna_kwargs = dict(
            brand_name=request.brand_name,
            slogan=request.slogan,
        )
        if request.logo_dna:
            d = request.logo_dna
            logo_structure = None
            if d.logo_structure:
                try:
                    logo_structure = LogoStructure(d.logo_structure)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"logo_structure invalide: {d.logo_structure}. "
                               f"Valeurs: {[e.value for e in LogoStructure]}"
                    )
            dna_kwargs.update(
                logo_structure=logo_structure,
                sector=d.sector,
                style_tags=d.style_tags,
                palette=d.palette,
                typography=d.typography,
                tone=d.tone,
                target=d.target,
                symbol_preference=d.symbol_preference,
                composition_style=d.composition_style,
                wordmark_weight=d.wordmark_weight,
                icon_complexity=d.icon_complexity,
                background_mode=BackgroundMode(d.background_mode),
            )
        dna = LogoDNA(**dna_kwargs)

        # ArbitrationConfig
        arb_input = request.arbitration or ArbitrationInput()
        try:
            arb_mode = ArbitrationMode(arb_input.mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"mode arbitration invalide: {arb_input.mode}"
            )
        config = ArbitrationConfig(
            mode=arb_mode,
            n_concepts=arb_input.n_concepts,
            n_variants=arb_input.n_variants,
            ai_score_threshold=arb_input.ai_score_threshold,
        )

        # Génération des concepts
        concepts = generate_concepts(dna, config, model_executor)

        # Mode HUMAN : retour immédiat sans sélection
        if config.mode == ArbitrationMode.HUMAN:
            return {
                "arbitration_mode": "human",
                "all_concepts": [
                    {
                        "concept_id": c.concept_id,
                        "prompt_used": c.prompt_used,
                        "score": c.score,
                        "flags": c.flags,
                    }
                    for c in concepts
                ],
                "message": "Select a concept_id and re-call POST /v1/logo/select",
            }

        # Sélection
        selected = select_concept(concepts, config)
        if not selected:
            raise HTTPException(status_code=500, detail="Aucun concept sélectionnable.")

        # Export des variantes
        variant_set = export_variants(
            selected_concept=selected,
            dna=dna,
            output_dir=request.output_dir,
            model_executor=model_executor,
        )

        elapsed = round(time.time() - t0, 2)

        return {
            "brand_name": dna.brand_name,
            "logo_structure": dna.logo_structure.value if dna.logo_structure else "icon_wordmark",
            "arbitration_mode": config.mode.value,
            "selected_concept_id": selected.concept_id,
            "selected_concept_score": selected.score,
            "flags": selected.flags,
            "variants": [
                {
                    "variant_name": v.variant_name,
                    "file_path": v.file_path,
                }
                for v in variant_set.variants
            ],
            "all_concepts": [
                {
                    "concept_id": c.concept_id,
                    "score": c.score,
                    "flags": c.flags,
                }
                for c in concepts
            ],
            "trace": {
                "elapsed_seconds": elapsed,
                "n_concepts_generated": len(concepts),
                "n_variants_exported": len(variant_set.variants),
                "output_dir": request.output_dir,
            },
        }

else:
    # FastAPI non disponible — router stub pour import sans crash
    router = None
