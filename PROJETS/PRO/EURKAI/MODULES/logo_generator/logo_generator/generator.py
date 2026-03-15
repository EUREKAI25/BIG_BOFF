"""
logo_generator.generator
─────────────────────────
Génère N concepts logo via model_executor (Recraft v3).
Retourne des LogoConcept avec SVG brut + flags vector_optimizer.
"""

from __future__ import annotations
import uuid
from typing import List

from .schemas import LogoDNA, LogoType, LogoConcept, ArbitrationConfig
from .prompt_builder import build_concept_prompts
from .vector_optimizer import optimize_svg


def generate_concepts(
    dna: LogoDNA,
    logo_type: LogoType,
    config: ArbitrationConfig,
    model_executor,           # callable: (prompt: str, model: str, output_format: str) -> str
) -> List[LogoConcept]:
    """
    Génère config.n_concepts concepts logo via Recraft v3.
    Chaque concept contient le SVG brut + flags de vector_optimizer.

    Args:
        dna:            LogoDNA de la marque
        logo_type:      Type de logo souhaité
        config:         ArbitrationConfig (n_concepts, mode, etc.)
        model_executor: Callable EURKAI standard (prompt → SVG string)

    Returns:
        Liste de LogoConcept (non sélectionnés)
    """
    prompts = build_concept_prompts(dna, logo_type, n=config.n_concepts)
    concepts: List[LogoConcept] = []

    for i, prompt in enumerate(prompts):
        concept_id = f"concept_{i+1}_{uuid.uuid4().hex[:6]}"

        # Appel model_executor — retourne SVG brut
        raw_svg: str = model_executor(
            prompt=prompt,
            model="recraftv3",
            output_format="svg",
        )

        # Optimisation + détection de flags (jamais de suppression)
        optimized_svg, flags = optimize_svg(raw_svg)

        concepts.append(LogoConcept(
            concept_id=concept_id,
            logo_type=logo_type,
            prompt_used=prompt,
            svg_content=optimized_svg,
            flags=flags,
        ))

    return concepts
