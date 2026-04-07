"""
design_plan.py — Générateur de plan de design déterministe.

Génère un plan strict AVANT le rendu, qui définit la stratégie de layout,
la composition, le rythme et les contraintes que le renderer DOIT respecter.

Ce n'est PAS une suggestion. C'est un contrat de rendu.

Usage :
    from design_plan import generate_design_plan

    plan = generate_design_plan(
        brief="Distillerie artisanale normande, calvados haut de gamme, 1887.",
        seed=42,
        theme_hints={"archetype": "craft_artisan"},
    )
    print(plan.to_json())

Intégration dans le pipeline :
    plan = generate_design_plan(brief, seed)
    rc   = _build_rendering_contract(ad, pal, typo, ctx, rng)
    rc   = plan.apply_to_rc(rc)      # surcharge les champs RC
    html = renderer(rc, ...)
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field, asdict
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# OPTION POOLS — chaque dimension a des pools par profil de brief
# ─────────────────────────────────────────────────────────────────────────────

_LAYOUTS = {
    "editorial":   ["editorial_flow", "magazine_spread", "vertical_narrative",
                    "cinematic_flow", "typographic_grid", "portrait_focus"],
    "structural":  ["asymmetrical_split", "staggered_blocks", "modular_grid",
                    "card_matrix", "split_columns", "dashboard_stack"],
    "bold":        ["brutalist_stack", "layered_overlap", "diagonal_tension",
                    "raw_manifest", "collision_grid", "oversized_type"],
    "commercial":  ["asymmetrical_split", "staggered_blocks", "editorial_flow",
                    "product_showcase", "catalog_flow", "card_matrix"],
}

_HERO_TYPES = {
    "editorial":   ["offset_text_image", "editorial_headline_only", "full_bleed_with_overlay",
                    "cinematic_overlay", "floating_text_on_gradient"],
    "structural":  ["split_diagonal", "text_panel_floating_media", "offset_text_image",
                    "portrait_right_text_left"],
    "bold":        ["brutalist_text_dominant", "asymmetric_overlap", "full_bleed_with_overlay",
                    "typographic_only"],
    "commercial":  ["split_diagonal", "offset_text_image", "full_bleed_with_overlay",
                    "product_center_text_surround"],
}

_POSITIONING = {
    "editorial":   ["top_left_dominant", "bottom_anchored", "diagonal_axis"],
    "structural":  ["left_panel_right_media", "right_text_left_media", "staggered_entry"],
    "bold":        ["extreme_left", "extreme_right", "edge_bleeding"],
    "commercial":  ["left_panel_right_media", "top_left_dominant", "staggered_entry"],
}

_TEXT_PLACEMENTS = {
    "editorial":   ["large_typographic_mass", "column_inset", "baseline_aligned"],
    "structural":  ["half_panel_left", "half_panel_right", "vertical_strip"],
    "bold":        ["full_width_over_image", "extreme_scale", "rotated_axis"],
    "commercial":  ["half_panel_left", "column_inset", "half_panel_right"],
}

_MEDIA_ROLES = {
    "editorial":   ["atmospheric_backdrop", "story_element", "textural_field"],
    "structural":  ["functional_illustration", "product_showcase", "data_visualization"],
    "bold":        ["disruptive_element", "texture_field", "raw_material"],
    "commercial":  ["product_showcase", "lifestyle_context", "functional_illustration"],
}

_STRUCTURES      = ["linear", "alternating", "fragmented", "modular_dynamic", "stacked_contrast"]
_FLOWS           = ["top_down_narrative", "tension_release", "progressive_reveal",
                    "fragmented_attention", "crescendo_build", "slow_unfold"]
_VARIATIONS      = ["high", "medium", "controlled"]
_DENSITIES       = {"editorial": ["low", "medium"], "structural": ["medium"],
                    "bold": ["high"], "commercial": ["medium", "high"]}

_TENSION_LEVELS  = {"editorial": ["medium", "high"], "structural": ["medium"],
                    "bold": ["high", "extreme"], "commercial": ["medium"]}

_TENSION_METHODS = [
    "overlap", "rotation", "scale_contrast", "negative_space_imbalance",
    "layering", "asymmetric_weight", "typographic_scale_jump",
    "bleeding_elements", "unexpected_proportion", "color_field_clash",
    "grid_break", "whitespace_tension",
]

_RHYTHM_PATTERNS = ["irregular_pulse", "build_and_release", "uniform_slow", "staccato",
                    "crescendo", "wave", "syncopated", "long_short_long"]

_RHYTHM_ALTS     = ["wide_narrow", "dense_sparse", "dark_light", "text_heavy_visual_heavy",
                    "structured_free", "large_small", "full_contained", "image_type_image"]

_SECTION_SETS: dict[str, list[str]] = {
    # ── Originals (9) ────────────────────────────────────────────────────────
    "editorial_flow":     ["hero", "editorial_narrative", "visual_break",
                           "feature_split", "quote_pull", "cta_block"],
    "magazine_spread":    ["hero", "spread_feature", "column_narrative",
                           "visual_interrupt", "byline_block", "cta_block"],
    "vertical_narrative": ["hero", "chapter_opener", "narrative_text",
                           "visual_pause", "feature_list", "cta_block"],
    "asymmetrical_split": ["hero", "feature_offset", "narrative_block",
                           "visual_contrast", "feature_split", "cta_block"],
    "staggered_blocks":   ["hero", "staggered_feature", "data_strip",
                           "offset_visual", "asymmetric_grid", "cta_block"],
    "modular_grid":       ["hero", "module_cluster", "stat_row",
                           "visual_module", "feature_tiles", "cta_block"],
    "brutalist_stack":    ["hero", "data_wall", "brutal_text_block",
                           "raw_visual", "asymmetric_grid", "cta_block"],
    "layered_overlap":    ["hero", "layer_reveal", "depth_feature",
                           "overlap_narrative", "floating_cta", "cta_block"],
    "diagonal_tension":   ["hero", "diagonal_feature", "tension_visual",
                           "oblique_narrative", "contrast_block", "cta_block"],
    # ── New editorial (3) ─────────────────────────────────────────────────────
    "cinematic_flow":     ["hero", "layer_reveal", "editorial_narrative",
                           "visual_break", "quote_pull", "cta_block"],
    "typographic_grid":   ["hero", "brutal_text_block", "feature_split",
                           "stat_row", "byline_block", "cta_block"],
    "portrait_focus":     ["hero", "spread_feature", "narrative_text",
                           "feature_offset", "visual_pause", "cta_block"],
    # ── New structural (3) ────────────────────────────────────────────────────
    "card_matrix":        ["hero", "module_cluster", "feature_tiles",
                           "data_strip", "floating_cta", "cta_block"],
    "split_columns":      ["hero", "feature_split", "narrative_block",
                           "stat_row", "asymmetric_grid", "cta_block"],
    "dashboard_stack":    ["hero", "data_wall", "stat_row",
                           "module_cluster", "feature_list", "cta_block"],
    # ── New bold (3) ──────────────────────────────────────────────────────────
    "raw_manifest":       ["hero", "brutal_text_block", "data_wall",
                           "tension_visual", "contrast_block", "cta_block"],
    "collision_grid":     ["hero", "asymmetric_grid", "overlap_narrative",
                           "diagonal_feature", "raw_visual", "cta_block"],
    "oversized_type":     ["hero", "editorial_narrative", "data_strip",
                           "visual_contrast", "feature_split", "cta_block"],
    # ── New commercial (2) ────────────────────────────────────────────────────
    "product_showcase":   ["hero", "offset_visual", "feature_list",
                           "stat_row", "visual_module", "cta_block"],
    "catalog_flow":       ["hero", "module_cluster", "feature_tiles",
                           "staggered_feature", "data_strip", "cta_block"],
}

_CTA_PLACEMENTS = {
    "editorial":  ["post_narrative", "isolated_bottom", "within_feature"],
    "structural": ["isolated_block", "post_features", "sticky_side"],
    "bold":       ["disruption_point", "isolated_contrast", "full_width_break"],
    "commercial": ["post_features", "isolated_block", "in_hero"],
}

_CTA_STYLES = {
    "editorial":  ["minimal_underline", "bordered_box", "text_button"],
    "structural": ["solid_fill", "high_contrast_pill", "bordered_button"],
    "bold":       ["reversed_block", "oversized_text", "raw_box"],
    "commercial": ["solid_fill", "high_contrast_pill", "solid_fill"],
}

_CTA_CONTRASTS = {
    "editorial":  "whitespace_isolation — CTA floats in open space",
    "structural": "color_inversion — CTA uses inverted bg/fg from section",
    "bold":       "extreme_contrast — maximum color/size opposition",
    "commercial": "accent_color_dominance — CTA in primary accent, surrounded by neutral",
}


# ─────────────────────────────────────────────────────────────────────────────
# BRIEF SIGNAL EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

# Mots-clés → profil de brief (le profil détermine les pools utilisés)
_SIGNAL_MAP: dict[str, str] = {
    # Editorial / luxury / artisan
    "luxury":     "editorial", "premium":   "editorial", "haute":      "editorial",
    "prestige":   "editorial", "maison":    "editorial", "artisan":    "editorial",
    "craft":      "editorial", "artisanal": "editorial", "heritage":   "editorial",
    "distillerie":"editorial", "domaine":   "editorial", "atelier":    "editorial",
    "galerie":    "editorial", "editorial": "editorial", "magazine":   "editorial",
    "studio":     "editorial", "agence":    "editorial",
    # Structural / tech / saas
    "tech":       "structural", "saas":     "structural", "digital":   "structural",
    "platform":   "structural", "app":      "structural", "data":      "structural",
    "logiciel":   "structural", "software": "structural", "startup":   "structural",
    "analytics":  "structural", "dashboard":"structural", "api":       "structural",
    # Bold / experimental
    "bold":       "bold", "brut":      "bold", "brutalist": "bold",
    "radical":    "bold", "expérimental":"bold", "disruptif": "bold",
    "underground":"bold", "avant-garde":"bold",
    # Commercial / product
    "boutique":   "commercial", "shop":     "commercial", "vente":     "commercial",
    "ecommerce":  "commercial", "produit":  "commercial", "collection":"commercial",
    "marque":     "commercial", "brand":    "commercial", "retail":    "commercial",
}


def _extract_profile(brief: str, theme_hints: dict | None = None) -> str:
    """
    Détermine le profil de brief depuis le texte (editorial / structural / bold / commercial).
    Le profil guide le choix des pools d'options.
    Retourne "structural" par défaut (neutre, non-générique).
    """
    lower   = brief.lower()
    scores  = {"editorial": 0, "structural": 0, "bold": 0, "commercial": 0}

    for keyword, profile in _SIGNAL_MAP.items():
        if keyword in lower:
            scores[profile] += 1

    # Hint explicite depuis le thème
    if theme_hints:
        archetype = (theme_hints.get("archetype") or "").lower()
        if any(k in archetype for k in ("craft", "artisan", "editorial", "magazine")):
            scores["editorial"] += 2
        elif any(k in archetype for k in ("saas", "tech", "product")):
            scores["structural"] += 2
        elif any(k in archetype for k in ("brutalist", "experimental")):
            scores["bold"] += 2
        elif any(k in archetype for k in ("ecommerce", "catalog")):
            scores["commercial"] += 2

    best_score = max(scores.values())
    if best_score == 0:
        return "structural"   # défaut non-générique

    # En cas d'égalité, priorité : editorial > commercial > structural > bold
    for p in ("editorial", "commercial", "structural", "bold"):
        if scores[p] == best_score:
            return p
    return "structural"


def _extract_signals(brief: str) -> list[str]:
    """Extrait les mots-clés de signal présents dans le brief."""
    lower = brief.lower()
    return [kw for kw in _SIGNAL_MAP if kw in lower]


# ─────────────────────────────────────────────────────────────────────────────
# CONSTRAINT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

# Contraintes TOUJOURS interdites — les layouts génériques par défaut
_ALWAYS_FORBIDDEN = [
    "centered_hero",
    "uniform_card_grid",
    "standard_nav_hero_grid_footer",
    "equal_section_heights",
    "symmetrical_column_layout",
]

# Contraintes TOUJOURS requises — règles de composition minimales
_ALWAYS_REQUIRED = [
    "varying_section_heights",
    "cta_visual_isolation",
    "at_least_one_typographic_hierarchy_break",
]

_LAYOUT_FORBIDDEN: dict[str, list[str]] = {
    "editorial_flow":     ["image_dominant_hero", "product_grid_sections"],
    "magazine_spread":    ["single_column_sections", "uniform_padding"],
    "vertical_narrative": ["horizontal_split_hero", "floating_elements"],
    "asymmetrical_split": ["symmetrical_layout", "centered_content_blocks"],
    "staggered_blocks":   ["linear_stack", "equal_block_sizes"],
    "modular_grid":       ["free_form_layout", "unstructured_sections"],
    "brutalist_stack":    ["refined_whitespace", "subtle_typography", "decorative_elements"],
    "layered_overlap":    ["flat_sections", "rigid_grid"],
    "diagonal_tension":   ["horizontal_only_layout", "perpendicular_avoidance"],
    # New
    "cinematic_flow":     ["product_grid_sections", "rigid_grid", "equal_section_heights"],
    "typographic_grid":   ["image_dominant_hero", "decorative_elements", "free_form_layout"],
    "portrait_focus":     ["image_background_hero", "uniform_padding", "symmetrical_layout"],
    "card_matrix":        ["free_form_layout", "irregular_grid", "overlapping_elements"],
    "split_columns":      ["single_column_sections", "full_width_blocks"],
    "dashboard_stack":    ["free_form_layout", "decorative_elements", "irregular_grid"],
    "raw_manifest":       ["refined_whitespace", "decorative_elements", "subtle_typography"],
    "collision_grid":     ["uniform_grid", "linear_stack", "equal_block_sizes"],
    "oversized_type":     ["balanced_type_image", "equal_section_heights"],
    "product_showcase":   ["text_dominant_hero", "complex_layouts", "editorial_whitespace"],
    "catalog_flow":       ["free_form_layout", "editorial_whitespace", "single_column_sections"],
}

_LAYOUT_REQUIRED: dict[str, list[str]] = {
    "editorial_flow":     ["typographic_hierarchy", "editorial_whitespace", "text_as_structure"],
    "magazine_spread":    ["column_breaks", "pull_quote_element", "editorial_rhythm"],
    "vertical_narrative": ["chapter_progression", "pacing_through_whitespace"],
    "asymmetrical_split": ["asymmetry", "varying_column_widths", "visual_weight_offset"],
    "staggered_blocks":   ["offset_rhythm", "size_variation", "alternating_alignment"],
    "modular_grid":       ["strict_grid_system", "module_repetition_with_variation"],
    "brutalist_stack":    ["raw_structure_visible", "bold_typographic_dominance", "deliberate_imbalance"],
    "layered_overlap":    ["z_axis_depth", "element_overlap", "visual_layering"],
    "diagonal_tension":   ["oblique_elements", "directional_energy", "counter_balance"],
    # New
    "cinematic_flow":     ["full_bleed_imagery", "cinematic_pacing", "text_over_image"],
    "typographic_grid":   ["typographic_hierarchy", "grid_discipline", "text_as_structure"],
    "portrait_focus":     ["portrait_framing", "asymmetric_text_position", "editorial_whitespace"],
    "card_matrix":        ["strict_grid_system", "uniform_card_rhythm", "scannable_structure"],
    "split_columns":      ["column_discipline", "asymmetry", "visual_anchor_per_column"],
    "dashboard_stack":    ["data_legibility", "strict_grid_system", "scannable_structure"],
    "raw_manifest":       ["raw_structure_visible", "bold_typographic_dominance", "maximum_contrast"],
    "collision_grid":     ["deliberate_imbalance", "element_overlap", "visual_conflict_point"],
    "oversized_type":     ["extreme_typographic_scale", "typographic_hierarchy", "scale_variation"],
    "product_showcase":   ["product_visual_dominance", "clean_background", "clarity_over_complexity"],
    "catalog_flow":       ["strict_grid_system", "uniform_card_rhythm", "visual_consistency"],
}

_HERO_FORBIDDEN: dict[str, list[str]] = {
    "editorial_headline_only":       ["large_image_hero", "hero_image_background"],
    "brutalist_text_dominant":       ["refined_hero_image", "centered_hero_text"],
    "full_bleed_with_overlay":       ["white_background_hero", "text_without_contrast_treatment"],
    "offset_text_image":             ["centered_text", "full_width_text_block"],
    "split_diagonal":                ["horizontal_division_only"],
    # New
    "cinematic_overlay":             ["white_background_hero", "small_imagery"],
    "floating_text_on_gradient":     ["hero_image_background", "image_dominant_hero"],
    "portrait_right_text_left":      ["centered_text", "full_width_text_block"],
    "typographic_only":              ["large_image_hero", "hero_image_background", "centered_hero_text"],
    "product_center_text_surround":  ["full_bleed_image", "editorial_whitespace"],
}

_HERO_REQUIRED: dict[str, list[str]] = {
    "editorial_headline_only":       ["typographic_emphasis", "whitespace_as_design"],
    "brutalist_text_dominant":       ["extreme_typographic_scale", "structural_rawness"],
    "full_bleed_with_overlay":       ["overlay_contrast_treatment", "text_readability_guarantee"],
    "offset_text_image":             ["visual_weight_balance_offset"],
    "split_diagonal":                ["directional_division", "cross_axis_composition"],
    # New
    "cinematic_overlay":             ["overlay_contrast_treatment", "cinematic_pacing"],
    "floating_text_on_gradient":     ["gradient_depth", "typographic_emphasis"],
    "portrait_right_text_left":      ["visual_weight_balance_offset", "column_discipline"],
    "typographic_only":              ["extreme_typographic_scale", "whitespace_as_design"],
    "product_center_text_surround":  ["product_visual_dominance", "clarity_over_complexity"],
}

_TENSION_REQUIRED: dict[str, list[str]] = {
    "extreme": ["maximum_scale_opposition", "deliberate_visual_clash", "rule_breaking_element"],
    "high":    ["visual_contrast_elements", "scale_variation", "tension_point"],
    "medium":  ["focal_hierarchy", "controlled_contrast"],
    "low":     ["refined_restraint", "unified_palette_application"],
}


def _build_constraints(
    layout: str, hero_type: str, tension_level: str, profile: str,
) -> "ConstraintsSpec":
    forbidden: list[str] = list(_ALWAYS_FORBIDDEN)
    required:  list[str] = list(_ALWAYS_REQUIRED)

    forbidden.extend(_LAYOUT_FORBIDDEN.get(layout, []))
    required.extend(_LAYOUT_REQUIRED.get(layout, []))
    forbidden.extend(_HERO_FORBIDDEN.get(hero_type, []))
    required.extend(_HERO_REQUIRED.get(hero_type, []))
    required.extend(_TENSION_REQUIRED.get(tension_level, []))

    # Déduplication ordonnée
    seen_f: set[str] = set()
    seen_r: set[str] = set()
    forbidden = [x for x in forbidden if not (x in seen_f or seen_f.add(x))]
    required  = [x for x in required  if not (x in seen_r or seen_r.add(x))]

    return ConstraintsSpec(forbidden=forbidden, required=required)


# ─────────────────────────────────────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HeroSpec:
    type:           str
    positioning:    str
    text_placement: str
    media_role:     str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CompositionSpec:
    structure:          str
    flow:               str
    section_variation:  str
    density:            str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VisualTensionSpec:
    level:   str
    methods: list[str]

    def to_dict(self) -> dict:
        return {"level": self.level, "methods": self.methods}


@dataclass
class RhythmSpec:
    pattern:     str
    alternation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ConstraintsSpec:
    forbidden: list[str]
    required:  list[str]

    def to_dict(self) -> dict:
        return {"forbidden": self.forbidden, "required": self.required}

    def is_forbidden(self, item: str) -> bool:
        return item in self.forbidden

    def is_required(self, item: str) -> bool:
        return item in self.required


@dataclass
class CTAStrategySpec:
    placement:         str
    style:             str
    contrast_strategy: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DesignPlan:
    layout_strategy: str
    hero:            HeroSpec
    composition:     CompositionSpec
    visual_tension:  VisualTensionSpec
    rhythm:          RhythmSpec
    constraints:     ConstraintsSpec
    section_types:   list[str]
    cta_strategy:    CTAStrategySpec

    # Métadonnées (non incluses dans la sortie JSON principale)
    seed:           int          = 0
    brief_profile:  str          = ""
    brief_signals:  list[str]    = field(default_factory=list)
    generated_at:   str          = ""

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self, include_meta: bool = False) -> dict:
        d = {
            "layout_strategy": self.layout_strategy,
            "hero":            self.hero.to_dict(),
            "composition":     self.composition.to_dict(),
            "visual_tension":  self.visual_tension.to_dict(),
            "rhythm":          self.rhythm.to_dict(),
            "constraints":     self.constraints.to_dict(),
            "section_types":   self.section_types,
            "cta_strategy":    self.cta_strategy.to_dict(),
        }
        if include_meta:
            d["_meta"] = {
                "seed":          self.seed,
                "brief_profile": self.brief_profile,
                "brief_signals": self.brief_signals,
                "generated_at":  self.generated_at,
            }
        return d

    def to_json(self, indent: int = 2, include_meta: bool = False) -> str:
        return json.dumps(self.to_dict(include_meta=include_meta),
                          indent=indent, ensure_ascii=False)

    # ── Integration helpers ────────────────────────────────────────────────

    def apply_to_rc(self, rc: dict) -> dict:
        """
        Surcharge les champs pertinents du Rendering Contract avec le plan.
        Le plan est SOURCE DE VÉRITÉ — ses valeurs remplacent toujours les defaults RC.

        Ordre de priorité :
        1. plan.hero.type (le plus spécifique)
        2. plan.layout_strategy → hero_pattern (si hero.type inconnu)
        3. plan.section_types → sections RC (liste complète, ordonnée, sans doublons)
        """
        rc = dict(rc)

        # ── 1. hero.type → hero_pattern (priorité sur layout→pattern) ───────
        _hero_type_to_pattern = {
            "offset_text_image":             "layered",
            "editorial_headline_only":       "editorial",
            "full_bleed_with_overlay":       "full-bleed",
            "split_diagonal":                "split",
            "text_panel_floating_media":     "split",
            "brutalist_text_dominant":       "raw_bold",
            "asymmetric_overlap":            "asymmetric",
            # New
            "cinematic_overlay":             "full-bleed",
            "floating_text_on_gradient":     "layered",
            "portrait_right_text_left":      "split",
            "typographic_only":              "editorial",
            "product_center_text_surround":  "centered",
        }
        if self.hero.type in _hero_type_to_pattern:
            rc["hero_pattern"] = _hero_type_to_pattern[self.hero.type]
        else:
            # Fallback : layout → hero_pattern
            _layout_to_hero_pattern = {
                "editorial_flow":     "layered",
                "magazine_spread":    "asymmetric",
                "vertical_narrative": "split",
                "asymmetrical_split": "asymmetric",
                "staggered_blocks":   "split",
                "modular_grid":       "centered",
                "brutalist_stack":    "raw_bold",
                "layered_overlap":    "layered",
                "diagonal_tension":   "asymmetric",
                # New
                "cinematic_flow":     "full-bleed",
                "typographic_grid":   "editorial",
                "portrait_focus":     "asymmetric",
                "card_matrix":        "centered",
                "split_columns":      "split",
                "dashboard_stack":    "centered",
                "raw_manifest":       "raw_bold",
                "collision_grid":     "asymmetric",
                "oversized_type":     "editorial",
                "product_showcase":   "centered",
                "catalog_flow":       "centered",
            }
            if self.layout_strategy in _layout_to_hero_pattern:
                rc["hero_pattern"] = _layout_to_hero_pattern[self.layout_strategy]

        # ── 2. Contrainte centered_hero ───────────────────────────────────────
        if self.constraints.is_forbidden("centered_hero") and rc.get("hero_pattern") == "centered":
            rc["hero_pattern"] = "asymmetric"

        # ── 3. Density → spacing ──────────────────────────────────────────────
        _density_spacing = {"low": "120px", "medium": "88px", "high": "60px"}
        rc["spacing_v"] = _density_spacing.get(self.composition.density, "88px")

        # ── 4. section_types → sections list (REPLACE, not filter) ───────────
        # Mapping exhaustif plan → RC (tous les types plan couverts)
        _section_map = {
            # Features / grid
            "feature_split":          "features_grid",
            "staggered_feature":      "features_cards",
            "module_cluster":         "features_grid",
            "feature_tiles":          "features_cards",
            "feature_list":           "features_list",
            "feature_offset":         "features_list",
            "asymmetric_grid":        "features_cards",
            "offset_visual":          "features_cards",
            "depth_feature":          "features_grid",
            "diagonal_feature":       "features_grid",
            "layer_reveal":           "features_cards",
            # Narrative / édito
            "editorial_narrative":    "manifesto",
            "narrative_text":         "manifesto",
            "narrative_block":        "manifesto",
            "oblique_narrative":      "manifesto",
            "overlap_narrative":      "manifesto",
            "column_narrative":       "manifesto",
            "brutal_text_block":      "manifesto",
            "contrast_block":         "manifesto",
            # Quote
            "quote_pull":             "pull_quote",
            "spread_feature":         "pull_quote",
            # Stats / data
            "stat_row":               "stats",
            "data_strip":             "stats",
            "data_wall":              "stats",
            "visual_module":          "stats",
            # Valeurs / chapitre
            "chapter_opener":         "values_list",
            "byline_block":           "values_list",
            # Process / visual (non structurel → process)
            "visual_break":           "process",
            "visual_interrupt":       "process",
            "visual_contrast":        "process",
            "visual_pause":           "process",
            "tension_visual":         "process",
            "floating_cta":           "process",
            "raw_visual":             "work_grid",
            # Pas de mapping (supprimés de la liste RC)
            "hero":                   None,
            "cta_block":              None,
        }
        mapped: list[str] = []
        seen: set[str] = set()
        for st in self.section_types:
            rc_key = _section_map.get(st)
            if rc_key is None:
                continue  # hero, cta_block, ou inconnu → ignorés ici
            if rc_key not in seen:
                mapped.append(rc_key)
                seen.add(rc_key)
        if len(mapped) >= 2:
            rc["sections"] = mapped
        # Si plan ne produit pas assez de sections mappées → on garde le blueprint

        # ── 5. Annotation debug ───────────────────────────────────────────────
        rc["_design_plan"]    = self.layout_strategy
        rc["_plan_hero_type"] = self.hero.type
        return rc

    def validate(self) -> list[str]:
        """Retourne la liste des violations de contraintes internes."""
        errors = []
        if self.layout_strategy not in [v for vals in _LAYOUTS.values() for v in vals]:
            errors.append(f"layout_strategy inconnu : {self.layout_strategy!r}")
        if self.visual_tension.level not in ("low", "medium", "high", "extreme"):
            errors.append(f"tension.level invalide : {self.visual_tension.level!r}")
        if self.composition.density not in ("low", "medium", "high"):
            errors.append(f"density invalide : {self.composition.density!r}")
        if len(self.section_types) < 3:
            errors.append("section_types : minimum 3 sections requises")
        if "cta_block" not in self.section_types:
            errors.append("section_types : 'cta_block' manquant")
        if not self.constraints.forbidden:
            errors.append("constraints.forbidden : doit contenir au moins une interdiction")
        if not self.constraints.required:
            errors.append("constraints.required : doit contenir au moins une exigence")
        return errors


# ─────────────────────────────────────────────────────────────────────────────
# WEIGHTED RANDOM PICK
# ─────────────────────────────────────────────────────────────────────────────

def _pick(rng: random.Random, pool: list[str], boost: list[str] | None = None) -> str:
    """
    Sélectionne un élément du pool avec la graine.
    Si boost est fourni, les éléments boostés ont un poids ×3.
    """
    if not pool:
        raise ValueError("Pool vide")
    if not boost:
        return rng.choice(pool)

    weights = [3 if item in boost else 1 for item in pool]
    total   = sum(weights)
    r       = rng.uniform(0, total)
    acc     = 0
    for item, w in zip(pool, weights):
        acc += w
        if r <= acc:
            return item
    return pool[-1]


def _pick_n(rng: random.Random, pool: list[str], n: int,
            boost: list[str] | None = None) -> list[str]:
    """Sélectionne n éléments distincts du pool sans répétition."""
    n = min(n, len(pool))
    if not boost:
        return rng.sample(pool, n)
    # Trier par poids pour favoriser les boostés, puis sample
    boosted_first = sorted(pool, key=lambda x: (0 if x in (boost or []) else 1))
    # Shuffler avec poids : mettre les boostés en tête puis échantillonner
    weighted = ([x for x in boosted_first if x in (boost or [])] +
                [x for x in boosted_first if x not in (boost or [])])
    return weighted[:n]


# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE ANALYSIS → DESIGN PLAN OVERRIDES
# ─────────────────────────────────────────────────────────────────────────────

def _reference_analysis_to_overrides(ra: dict) -> dict:
    """
    Traduit reference_analysis (depuis visual_coherence_engine CASE 3) en overrides
    directs pour generate_design_plan.

    Ces overrides sont des inputs durs — ils priment sur visual_intent.

    Mapping :
        dominance + density → profile_override
        spacing             → density_override   (plus sémantique que density brute)
        hierarchy           → tension_override + tension_methods
        asymmetry           → layout_boost
        density (low)       → extra_required: editorial_whitespace
    """
    dominance = ra.get("dominance", "balanced")
    density   = ra.get("density", "medium")
    hierarchy = ra.get("hierarchy", "strong")
    spacing   = ra.get("spacing", "balanced")
    cb        = ra.get("composition_bias", {})
    asymmetry = cb.get("asymmetry", "medium")

    # Profile depuis dominance + density
    if dominance == "text" or (dominance == "balanced" and density == "low"):
        profile_override = "editorial"
    elif dominance == "image":
        profile_override = "editorial"      # layouts éditoriaux pour les designs image-dominant
    elif density == "high":
        profile_override = "commercial"
    else:
        profile_override = "structural"

    # Density depuis spacing (sémantique design > brut pixel)
    _spacing_density = {"airy": "low", "balanced": "medium", "tight": "high"}
    density_override = _spacing_density.get(spacing, density)

    # Tension depuis hierarchy
    _hierarchy_tension = {"calm": "medium", "strong": "high", "aggressive": "high"}
    tension_override = _hierarchy_tension.get(hierarchy, "medium")

    # Méthodes de tension depuis hierarchy
    _hierarchy_methods: dict[str, list[str]] = {
        "calm":       ["whitespace_tension", "scale_contrast"],
        "strong":     ["scale_contrast", "asymmetric_weight", "typographic_scale_jump"],
        "aggressive": ["scale_contrast", "typographic_scale_jump", "grid_break",
                       "asymmetric_weight"],
    }
    tension_methods = _hierarchy_methods.get(hierarchy, ["scale_contrast"])

    # Layout boost depuis asymmetry
    _asym_boost: dict[str, list[str]] = {
        "high":   ["asymmetrical_split", "diagonal_tension", "staggered_blocks"],
        "medium": ["asymmetrical_split", "staggered_blocks", "magazine_spread"],
        "low":    ["modular_grid", "editorial_flow", "vertical_narrative"],
    }
    layout_boost = _asym_boost.get(asymmetry, [])

    # Extra required
    extra_required: list[str] = []
    if density_override == "low":
        extra_required.append("editorial_whitespace")
    if asymmetry in ("medium", "high"):
        extra_required.append("asymmetry")

    return {
        "profile_override": profile_override,
        "density_override": density_override,
        "tension_override": tension_override,
        "tension_methods":  tension_methods,
        "layout_boost":     layout_boost,
        "layout_avoid":     [],
        "extra_required":   extra_required,
        "extra_forbidden":  [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_design_plan(
    brief:              str,
    seed:               int  = 42,
    style_dna:          dict | None = None,
    theme_hints:        dict | None = None,
    visual_intent:      dict | None = None,
    reference_analysis: dict | None = None,
) -> DesignPlan:
    """
    Génère un DesignPlan déterministe depuis le brief et la graine.

    brief              : texte libre du projet
    seed               : graine — seeds différentes produisent des plans distincts
    style_dna          : optionnel — influence les choix visuels
    theme_hints        : optionnel — {"archetype": str, "layout": str, ...}
    visual_intent      : optionnel — dict produit par visual_intent_engine.generate_visual_intent()
                         Quand fourni, surcharge profile, density, tension et layout_boost.
    reference_analysis : optionnel — dict produit par visual_coherence_engine CASE 3
                         (design_reference_drives_plan). Quand fourni, ses overrides
                         priment sur visual_intent : dominance, density, hierarchy,
                         spacing, asymmetry, rhythm sont des inputs durs.

    Retourne un DesignPlan strict que le renderer doit respecter.
    """
    rng = random.Random(seed)

    # ── 0. Traduction du visual_intent en overrides ───────────────────────
    _vi_overrides: dict = {}
    if visual_intent:
        try:
            # Import local pour éviter la dépendance circulaire
            import sys as _sys
            from pathlib import Path as _Path
            _vie_dir = _Path(__file__).parent.parent.parent / "visual_intent_engine"
            if str(_vie_dir) not in _sys.path:
                _sys.path.insert(0, str(_vie_dir))
            from src.visual_intent_engine import intent_to_plan_overrides
            _vi_overrides = intent_to_plan_overrides(visual_intent)
        except ImportError:
            pass   # visual_intent_engine non disponible — continuer sans overrides

    # ── 0.5 Reference analysis overrides (priorité absolue sur visual_intent) ──
    if reference_analysis:
        _ra_overrides = _reference_analysis_to_overrides(reference_analysis)
        # RA wins : merge avec priorité RA sur vi
        _vi_overrides.update(_ra_overrides)

    # ── 1. Profil et signaux ──────────────────────────────────────────────
    profile = _vi_overrides.get("profile_override") or _extract_profile(brief, theme_hints)
    signals = _extract_signals(brief)

    # Hint layout explicite (priorité absolue)
    forced_layout: str | None = None
    if theme_hints:
        forced_layout = theme_hints.get("layout")

    # ── 2. Layout strategy ────────────────────────────────────────────────
    layout_pool = (
        _LAYOUTS.get(profile, []) +
        _LAYOUTS.get("structural", [])   # toujours enrichir avec le pool structurel
    )
    layout_pool = list(dict.fromkeys(layout_pool))   # dédupliqué, ordre conservé

    # Filtrer les layouts explicitement évités par visual_intent
    vi_avoid = _vi_overrides.get("layout_avoid", [])
    if vi_avoid:
        layout_pool = [l for l in layout_pool if l not in vi_avoid] or layout_pool

    # Boost les layouts favorisés par visual_intent
    vi_boost = _vi_overrides.get("layout_boost", [])

    layout = forced_layout or _pick(rng, layout_pool, boost=vi_boost or None)

    # ── 3. Hero ───────────────────────────────────────────────────────────
    hero_pool = (
        _HERO_TYPES.get(profile, []) +
        _HERO_TYPES.get("structural", [])
    )
    hero_pool = list(dict.fromkeys(hero_pool))

    hero_type      = _pick(rng, hero_pool)
    positioning    = _pick(rng, _POSITIONING.get(profile, _POSITIONING["structural"]))
    text_placement = _pick(rng, _TEXT_PLACEMENTS.get(profile, _TEXT_PLACEMENTS["structural"]))
    media_role     = _pick(rng, _MEDIA_ROLES.get(profile, _MEDIA_ROLES["structural"]))

    # ── 4. Composition ────────────────────────────────────────────────────
    structure    = _pick(rng, _STRUCTURES)
    flow         = _pick(rng, _FLOWS)
    variation    = _pick(rng, _VARIATIONS)
    density_pool = _DENSITIES.get(profile, ["medium"])
    density      = _vi_overrides.get("density_override") or _pick(rng, density_pool)
    # Valider que density est dans les valeurs autorisées
    if density not in ("low", "medium", "high"):
        density = _pick(rng, density_pool)

    # ── 5. Visual tension ─────────────────────────────────────────────────
    tension_pool  = _TENSION_LEVELS.get(profile, ["medium"])
    tension_level = _vi_overrides.get("tension_override") or _pick(rng, tension_pool)
    # Valider
    if tension_level not in ("low", "medium", "high", "extreme"):
        tension_level = _pick(rng, tension_pool)

    n_methods = {"extreme": 4, "high": 3, "medium": 2, "low": 1}.get(tension_level, 2)

    # Méthodes : priorité aux méthodes du visual_intent, complétées par le pool
    vi_methods = _vi_overrides.get("tension_methods", [])
    if vi_methods:
        # Partir des méthodes du visual_intent, compléter jusqu'à n_methods
        extra_needed = max(0, n_methods - len(vi_methods))
        remaining_pool = [m for m in _TENSION_METHODS if m not in vi_methods]
        extra = _pick_n(rng, remaining_pool, n=extra_needed) if extra_needed and remaining_pool else []
        tension_methods = vi_methods[:n_methods] + extra
    else:
        tension_methods = _pick_n(rng, _TENSION_METHODS, n=n_methods)

    # ── 6. Rhythm ─────────────────────────────────────────────────────────
    rhythm_pattern = _pick(rng, _RHYTHM_PATTERNS)
    rhythm_alt     = _pick(rng, _RHYTHM_ALTS)

    # ── 7. Sections ───────────────────────────────────────────────────────
    section_types = _SECTION_SETS.get(layout, _SECTION_SETS["staggered_blocks"])

    # ── 8. CTA strategy ───────────────────────────────────────────────────
    cta_placement = _pick(rng, _CTA_PLACEMENTS.get(profile, _CTA_PLACEMENTS["structural"]))
    cta_style     = _pick(rng, _CTA_STYLES.get(profile, _CTA_STYLES["structural"]))
    cta_contrast  = _CTA_CONTRASTS.get(profile, _CTA_CONTRASTS["structural"])

    # ── 9. Constraints ────────────────────────────────────────────────────
    constraints = _build_constraints(layout, hero_type, tension_level, profile)

    # Fusionner les extra contraintes du visual_intent
    vi_extra_req = _vi_overrides.get("extra_required", [])
    vi_extra_for = _vi_overrides.get("extra_forbidden", [])
    if vi_extra_req:
        seen: set[str] = set(constraints.required)
        constraints.required.extend(x for x in vi_extra_req if x not in seen)
    if vi_extra_for:
        seen_f: set[str] = set(constraints.forbidden)
        constraints.forbidden.extend(x for x in vi_extra_for if x not in seen_f)

    # ── 10. Assemblage ────────────────────────────────────────────────────
    plan = DesignPlan(
        layout_strategy=layout,
        hero=HeroSpec(
            type=hero_type,
            positioning=positioning,
            text_placement=text_placement,
            media_role=media_role,
        ),
        composition=CompositionSpec(
            structure=structure,
            flow=flow,
            section_variation=variation,
            density=density,
        ),
        visual_tension=VisualTensionSpec(
            level=tension_level,
            methods=tension_methods,
        ),
        rhythm=RhythmSpec(
            pattern=rhythm_pattern,
            alternation=rhythm_alt,
        ),
        constraints=constraints,
        section_types=section_types,
        cta_strategy=CTAStrategySpec(
            placement=cta_placement,
            style=cta_style,
            contrast_strategy=cta_contrast,
        ),
        seed=seed,
        brief_profile=profile,
        brief_signals=signals,
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )

    return plan


# ─────────────────────────────────────────────────────────────────────────────
# PLAN COMPARISON (debug / test)
# ─────────────────────────────────────────────────────────────────────────────

def diff_plans(plan_a: DesignPlan, plan_b: DesignPlan) -> dict:
    """Retourne les dimensions qui diffèrent entre deux plans."""
    diffs = {}
    a, b = plan_a.to_dict(), plan_b.to_dict()

    def _compare(da: Any, db: Any, path: str = "") -> None:
        if isinstance(da, dict) and isinstance(db, dict):
            for k in set(da) | set(db):
                _compare(da.get(k), db.get(k), f"{path}.{k}" if path else k)
        elif isinstance(da, list) and isinstance(db, list):
            if sorted(str(x) for x in da) != sorted(str(x) for x in db):
                diffs[path] = {"a": da, "b": db}
        elif da != db:
            diffs[path] = {"a": da, "b": db}

    _compare(a, b)
    return diffs


def plans_are_distinct(plan_a: DesignPlan, plan_b: DesignPlan,
                       min_diffs: int = 3) -> bool:
    """
    Vérifie que deux plans sont suffisamment distincts.
    min_diffs = nombre minimum de dimensions différentes requises.
    """
    return len(diff_plans(plan_a, plan_b)) >= min_diffs
