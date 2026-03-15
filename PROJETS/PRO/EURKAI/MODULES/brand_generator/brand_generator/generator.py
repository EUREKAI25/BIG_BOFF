"""
brand_generator.generator
──────────────────────────
Point d'entrée principal du module.
Orchestre : analyze → build_prompt → llm_executor → parse → BrandGeneratorOutput.
"""

from __future__ import annotations
import time

from .schemas import BrandGeneratorInput, BrandGeneratorOutput
from .analyzer import analyze
from .direction_builder import build_prompt, parse_llm_response


def generate_brand_directions(
    input_data: BrandGeneratorInput,
    llm_executor,    # callable: (prompt: str, model: str) -> str  (retourne du texte JSON)
    model: str = "claude-sonnet",
    max_retries: int = 2,
) -> BrandGeneratorOutput:
    """
    Génère 3 directions créatives distinctes à partir d'un brief et d'un BrandDNA.

    Args:
        input_data:    BrandGeneratorInput (brief + BrandDNA + contexte optionnel)
        llm_executor:  Callable EURKAI standard pour appels LLM texte
        model:         Modèle LLM à utiliser (défaut: claude-sonnet)
        max_retries:   Tentatives en cas de JSON invalide

    Returns:
        BrandGeneratorOutput avec direction_a, direction_b, direction_c
    """
    t0 = time.time()

    # Analyse du contexte créatif
    ctx = analyze(input_data)

    # Construction du prompt
    prompt = build_prompt(ctx)

    # Appel LLM avec retry sur erreur de parsing
    last_error = None
    for attempt in range(max_retries + 1):
        raw: str = llm_executor(prompt=prompt, model=model)
        try:
            dir_a, dir_b, dir_c = parse_llm_response(raw)
            break
        except ValueError as e:
            last_error = e
            if attempt == max_retries:
                raise RuntimeError(
                    f"Impossible de parser la réponse LLM après {max_retries + 1} tentatives. "
                    f"Dernière erreur : {last_error}"
                ) from e

    elapsed = round(time.time() - t0, 2)

    return BrandGeneratorOutput(
        direction_a=dir_a,
        direction_b=dir_b,
        direction_c=dir_c,
        trace={
            "brand_name":    ctx.brand_name,
            "sector":        ctx.sector,
            "contrast_axes": ctx.contrast_axes,
            "model":         model,
            "attempt":       attempt + 1,
            "elapsed_seconds": elapsed,
        },
    )
