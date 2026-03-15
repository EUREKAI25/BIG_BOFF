"""
design_exploration_engine.direction_generator
──────────────────────────────────────────────
Orchestrateur principal : DesignDNA → ExplorationOutput (N directions).

Pipeline :
  1. Extraire l'archétype source du DesignDNA
  2. Sélectionner N archétypes distincts (archetype_variator)
  3. Assembler chaque direction (direction_builder)
  4. Retourner ExplorationOutput
"""

from __future__ import annotations
from typing import Any, Dict

from .schemas          import ExplorationInput, ExplorationOutput, DesignDirection
from .archetype_variator import select_archetypes
from .direction_builder  import build_direction


def generate_directions(input_data: ExplorationInput) -> ExplorationOutput:
    """
    Génère N directions créatives à partir d'un DesignDNA.
    """
    dna = input_data.design_dna or {}
    n   = max(2, min(5, input_data.n_directions))

    source_archetype = dna.get("style_archetype") or "startup_clean"

    # Sélectionner les N archétypes
    archetype_list = select_archetypes(source_archetype, n=n)

    # Assembler chaque direction
    directions = []
    for i, (archetype, family, relation) in enumerate(archetype_list, start=1):
        direction = build_direction(
            archetype    = archetype,
            direction_id = f"direction_{i}",
            family       = family,
            relation     = relation,
            source_dna   = dna,
            index        = i,
        )
        directions.append(direction)

    return ExplorationOutput(
        directions=directions,
        source_archetype=source_archetype,
        trace={
            "n_requested": input_data.n_directions,
            "n_generated": len(directions),
            "archetypes": [d.style_archetype for d in directions],
        },
    )
