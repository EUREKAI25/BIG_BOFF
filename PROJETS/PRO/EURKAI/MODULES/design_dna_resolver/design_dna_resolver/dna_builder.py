"""
design_dna_resolver.dna_builder
─────────────────────────────────
Assemble le DesignDNA final depuis le BriefInput + archétype + style_profile.
Point d'entrée unique du module.
"""

from __future__ import annotations
from typing import Union, Dict

from .schemas import BriefInput, DesignDNA
from .brief_parser import parse_brief
from .archetype_inference import infer_archetype
from .style_mapper import get_style_profile


def build_dna(brief: Union[str, Dict]) -> DesignDNA:
    """
    Pipeline complet : brief → DesignDNA.

    1. parse_brief       → BriefInput normalisé
    2. infer_archetype   → archétype + confidence + scores
    3. get_style_profile → hints stylistiques par module
    4. Assemblage DesignDNA
    """
    # 1. Parse
    brief_input: BriefInput = parse_brief(brief)

    # 2. Archétype
    archetype, confidence, archetype_scores = infer_archetype(brief_input)

    # 3. Style
    profile = get_style_profile(archetype)

    # 4. Assemblage
    dna = DesignDNA(
        project_name=brief_input.project_name,
        industry=brief_input.industry,
        brand_values=brief_input.brand_values,
        tone=brief_input.tone,
        target_audience=brief_input.target_audience,
        keywords=brief_input.keywords,

        style_archetype=archetype,

        palette_bias=profile.palette_bias,
        typography_style=profile.typography_style,
        icon_style=profile.icon_style,
        layout_style=profile.layout_style,
        visual_style=profile.visual_style,
        image_style=profile.image_style,
        composition_style=profile.composition_style,
        motion_energy=profile.motion_energy,

        logo_structure_hint=profile.logo_structure,
        wordmark_weight_hint=profile.wordmark_weight,

        confidence=confidence,
        trace={
            "archetype_scores": archetype_scores,
            "brief_industry":   brief_input.industry,
            "brief_tone":       brief_input.tone,
            "brief_values":     brief_input.brand_values,
        },
    )

    return dna
