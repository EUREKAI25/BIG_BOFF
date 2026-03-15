"""
design_exploration_engine
──────────────────────────
Module EURKAI standalone — génère N directions créatives distinctes
à partir d'un DesignDNA. Mime le process agence : plusieurs pistes
stylistiques présentables au client.

Zero LLM. Sortie déterministe.

Pipeline :
  DesignDNA → archetype_variator → direction_builder × N → ExplorationOutput

Usage :
    from design_exploration_engine import explore

    output = explore({
        "style_archetype": "startup_clean",
        "industry": "finance",
        "brand_values": ["trust", "innovation"],
        "tone": "modern_premium",
        "palette_bias": {"preferred_colors": ["electric_blue", "navy"]},
    }, n_directions=3)

    for d in output.directions:
        print(d.id, d.name, d.style_archetype)
        # direction_1  Clean Tech         startup_clean
        # direction_2  Corporate Pro      corporate_pro
        # direction_3  Editorial Bold     editorial_magazine
"""

from .schemas            import ExplorationInput, ExplorationOutput, DesignDirection
from .direction_generator import generate_directions


def explore(design_dna: dict, n_directions: int = 3) -> ExplorationOutput:
    """Point d'entrée public."""
    return generate_directions(ExplorationInput(
        design_dna=design_dna,
        n_directions=n_directions,
    ))


__version__ = "0.1.0"

__all__ = [
    "explore",
    "ExplorationInput",
    "ExplorationOutput",
    "DesignDirection",
    "generate_directions",
]
