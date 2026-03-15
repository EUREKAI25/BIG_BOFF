"""
design_dna_resolver
────────────────────
Module EURKAI standalone — convertit un brief en DesignDNA structuré.
Zero LLM, zero dépendance externe. Sortie déterministe.

Pipeline :
  brief (dict ou texte) → parse_brief → infer_archetype → style_mapper → DesignDNA

Usage :
    from design_dna_resolver import resolve
    dna = resolve({"project_name": "NovaBank", "industry": "finance", ...})
    print(dna.style_archetype)      # "startup_clean"
    print(dna.typography_style)     # "geometric_sans"
    print(dna.palette_bias)         # PaletteBias(preferred_colors=["electric_blue", ...])
"""

from .schemas import DesignDNA, BriefInput, PaletteBias
from .dna_builder import build_dna as resolve
from .archetype_inference import infer_archetype
from .style_mapper import list_archetypes

__version__ = "0.1.0"

__all__ = [
    "DesignDNA",
    "BriefInput",
    "PaletteBias",
    "resolve",
    "infer_archetype",
    "list_archetypes",
]
