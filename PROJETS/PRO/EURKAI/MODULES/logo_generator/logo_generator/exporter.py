"""
logo_generator.exporter
─────────────────────────
Génère les 5 variantes SVG d'un concept sélectionné
et les écrit sur disque dans output_dir/{brand_name}/.

Variantes produites :
  logo.svg              ← layout standard
  logo_horizontal.svg   ← icône + texte, ligne unique
  logo_icon.svg         ← icône seule
  logo_monochrome.svg   ← monochrome noir
  favicon.svg           ← variante 16px ultra-simplifiée
"""

from __future__ import annotations
import os
import re
from typing import List

from .schemas import LogoConcept, LogoDNA, LogoType, LogoVariant, LogoVariantSet
from .prompt_builder import build_variant_prompts
from .vector_optimizer import optimize_svg


def export_variants(
    selected_concept: LogoConcept,
    dna: LogoDNA,
    logo_type: LogoType,
    output_dir: str,
    model_executor,        # callable: (prompt: str, model: str, output_format: str) -> str
) -> LogoVariantSet:
    """
    Génère les 5 variantes du concept sélectionné via Recraft,
    optimise chaque SVG et écrit les fichiers dans output_dir.

    Returns:
        LogoVariantSet avec les variantes et leurs chemins de fichiers.
    """
    brand_slug = _slugify(dna.brand_name)
    dest_dir = os.path.join(output_dir, brand_slug)
    os.makedirs(dest_dir, exist_ok=True)

    variant_prompts = build_variant_prompts(dna, selected_concept.prompt_used, logo_type)
    variants: List[LogoVariant] = []

    for variant_name, prompt in variant_prompts.items():
        raw_svg: str = model_executor(
            prompt=prompt,
            model="recraftv3",
            output_format="svg",
        )

        optimized_svg, flags = optimize_svg(raw_svg)

        file_path = os.path.join(dest_dir, f"{variant_name}.svg")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(optimized_svg)

        variant = LogoVariant(
            variant_name=variant_name,
            prompt_used=prompt,
            svg_content=optimized_svg,
            file_path=file_path,
        )
        # Propager les flags sur la variante si besoin
        if flags:
            # flags ne sont pas dans LogoVariant mais on peut les noter dans le concept
            selected_concept.flags.extend(
                [f"[{variant_name}] {flag}" for flag in flags]
            )
        variants.append(variant)

    return LogoVariantSet(
        concept_id=selected_concept.concept_id,
        variants=variants,
    )


# ─── Helper ───────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    """Convertit un nom de marque en slug de répertoire."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text
