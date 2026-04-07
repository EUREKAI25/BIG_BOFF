"""
option_pools — toutes les options contrôlées du pipeline design.

Règle : aucune génération ex nihilo. Tout output vient d'ici.
Règle : aucun random ici. Les pools sont statiques. La sélection est dans milestone_runner.
"""

# ─── Visual families (12) ─────────────────────────────────────────────────────

VISUAL_FAMILIES = [
    "editorial_magazine",
    "luxury_minimal",
    "playful_brand",
    "warm_human",
    "startup_clean",
    "corporate_pro",
    "tech_futurist",
    "brutalist",
    "organic_natural",
    "premium_craft",
    "bold_challenger",
    "creative_studio",
]

# ─── Layout strategies (18) ──────────────────────────────────────────────────

LAYOUT_STRATEGIES = [
    # Originaux (9)
    "editorial_flow",
    "magazine_spread",
    "vertical_narrative",
    "asymmetrical_split",
    "staggered_blocks",
    "modular_grid",
    "brutalist_stack",
    "layered_overlap",
    "diagonal_tension",
    # Nouveaux (9)
    "centered_narrative",       # tout centré, rythme aéré, typographie dominante
    "hero_dominant",            # hero 100vh, contenu condensé dessous
    "zigzag_cascade",           # alternance gauche/droite stricte
    "minimal_whitespace",       # densité basse, espaces extrêmes
    "filmstrip_scroll",         # sections en bandes horizontales pleins-bleed
    "card_mosaic",              # grille de cartes asymétrique
    "typographic_poster",       # typographie comme seul élément visuel structurant
    "sidebar_anchored",         # navigation latérale fixe + contenu scrollable
    "data_forward",             # chiffres et stats en éléments visuels principaux
]

# ─── Hero types (12) ─────────────────────────────────────────────────────────

HERO_TYPES = [
    # Originaux
    "offset_text_image",
    "editorial_headline_only",
    "full_bleed_with_overlay",
    "split_diagonal",
    "text_panel_floating_media",
    "brutalist_text_dominant",
    "asymmetric_overlap",
    # Nouveaux (5)
    "centered_statement",       # titre centré, sous-titre, CTA — pas d'image
    "typographic_only",         # typographie géante, fond uni
    "split_color_block",        # moitié couleur / moitié contenu, sans image
    "manifesto_block",          # texte manifeste pleine largeur, ton fort
    "oversized_number_hero",    # chiffre clé énorme + tagline
]

# ─── Hero config par type — strictement défini ───────────────────────────────
# min_height, text_position, has_image, layout_class

HERO_CONFIG: dict[str, dict] = {
    "offset_text_image":        {"min_height": "88vh", "text_position": "left",   "has_image": True,  "layout_class": "hero--offset"},
    "editorial_headline_only":  {"min_height": "70vh", "text_position": "left",   "has_image": False, "layout_class": "hero--editorial"},
    "full_bleed_with_overlay":  {"min_height": "95vh", "text_position": "center", "has_image": True,  "layout_class": "hero--fullbleed"},
    "split_diagonal":           {"min_height": "85vh", "text_position": "left",   "has_image": True,  "layout_class": "hero--split-diag"},
    "text_panel_floating_media":{"min_height": "80vh", "text_position": "left",   "has_image": True,  "layout_class": "hero--text-panel"},
    "brutalist_text_dominant":  {"min_height": "75vh", "text_position": "left",   "has_image": False, "layout_class": "hero--brutalist"},
    "asymmetric_overlap":       {"min_height": "90vh", "text_position": "left",   "has_image": True,  "layout_class": "hero--asymmetric"},
    "centered_statement":       {"min_height": "72vh", "text_position": "center", "has_image": False, "layout_class": "hero--centered"},
    "typographic_only":         {"min_height": "85vh", "text_position": "center", "has_image": False, "layout_class": "hero--typo"},
    "split_color_block":        {"min_height": "80vh", "text_position": "left",   "has_image": False, "layout_class": "hero--split-color"},
    "manifesto_block":          {"min_height": "65vh", "text_position": "center", "has_image": False, "layout_class": "hero--manifesto"},
    "oversized_number_hero":    {"min_height": "78vh", "text_position": "center", "has_image": False, "layout_class": "hero--number"},
}

# ─── Section flows par layout strategy (20+ flows) ───────────────────────────
# Règle : chaque flow contient "hero" en premier et "cta_block" en dernier.
# Règle : minimum 5 sections, maximum 8.

SECTION_FLOWS: dict[str, list[str]] = {
    # Originaux enrichis
    "editorial_flow":       ["hero", "editorial_narrative", "visual_break",   "feature_split",    "quote_pull",        "cta_block"],
    "magazine_spread":      ["hero", "spread_feature",      "column_narrative","visual_interrupt", "byline_block",      "cta_block"],
    "vertical_narrative":   ["hero", "chapter_opener",      "narrative_text",  "visual_pause",     "feature_list",      "cta_block"],
    "asymmetrical_split":   ["hero", "feature_offset",      "narrative_block", "visual_contrast",  "feature_split",     "cta_block"],
    "staggered_blocks":     ["hero", "staggered_feature",   "data_strip",      "offset_visual",    "asymmetric_grid",   "cta_block"],
    "modular_grid":         ["hero", "module_cluster",      "stat_row",        "visual_module",    "feature_tiles",     "cta_block"],
    "brutalist_stack":      ["hero", "data_wall",           "brutal_text_block","raw_visual",      "asymmetric_grid",   "cta_block"],
    "layered_overlap":      ["hero", "layer_reveal",        "depth_feature",   "overlap_narrative","floating_cta",      "cta_block"],
    "diagonal_tension":     ["hero", "diagonal_feature",    "tension_visual",  "oblique_narrative","contrast_block",    "cta_block"],
    # Nouveaux
    "centered_narrative":   ["hero", "manifesto_strip",     "stat_centered",   "feature_centered", "quote_centered",    "cta_block"],
    "hero_dominant":        ["hero", "anchor_statement",    "feature_compact",  "social_proof",    "cta_block"],
    "zigzag_cascade":       ["hero", "zigzag_left",         "zigzag_right",    "zigzag_left",      "stat_row",          "cta_block"],
    "minimal_whitespace":   ["hero", "whitespace_text",     "single_feature",  "quote_pull",       "cta_block"],
    "filmstrip_scroll":     ["hero", "filmstrip_band",      "filmstrip_band",  "filmstrip_band",   "data_strip",        "cta_block"],
    "card_mosaic":          ["hero", "mosaic_header",       "mosaic_grid",     "stat_row",         "feature_compact",   "cta_block"],
    "typographic_poster":   ["hero", "poster_statement",    "type_hierarchy",  "type_feature",     "cta_block"],
    "sidebar_anchored":     ["hero", "sidebar_content",     "sidebar_feature", "sidebar_stats",    "sidebar_cta",       "cta_block"],
    "data_forward":         ["hero", "data_showcase",       "stat_grid",       "data_narrative",   "proof_strip",       "cta_block"],
    # Variantes alternatives (pour diversité seed)
    "editorial_flow_b":     ["hero", "visual_break",        "feature_split",   "editorial_narrative","quote_pull",      "cta_block"],
    "staggered_blocks_b":   ["hero", "data_strip",          "staggered_feature","offset_visual",   "stat_row",          "cta_block"],
    "modular_grid_b":       ["hero", "stat_row",            "feature_tiles",   "module_cluster",   "visual_module",     "cta_block"],
}

# ─── Palette families par visual_family ──────────────────────────────────────

PALETTE_FAMILIES: dict[str, list[str]] = {
    "editorial_magazine":   ["editorial_cool",    "editorial_warm",   "editorial_mono"],
    "luxury_minimal":       ["luxury_black",      "luxury_cream",     "luxury_gold"],
    "playful_brand":        ["playful_vivid",     "playful_pastel",   "playful_neon"],
    "warm_human":           ["warm_terracotta",   "warm_sage",        "warm_peach"],
    "startup_clean":        ["startup_blue",      "startup_green",    "startup_purple"],
    "corporate_pro":        ["corporate_navy",    "corporate_slate",  "corporate_charcoal"],
    "tech_futurist":        ["tech_dark_blue",    "tech_cyan",        "tech_violet"],
    "brutalist":            ["brutalist_bw",      "brutalist_accent", "brutalist_raw"],
    "organic_natural":      ["organic_earth",     "organic_forest",   "organic_sand"],
    "premium_craft":        ["craft_linen",       "craft_copper",     "craft_ink"],
    "bold_challenger":      ["bold_red",          "bold_orange",      "bold_electric"],
    "creative_studio":      ["studio_gradient",   "studio_minimal",   "studio_eclectic"],
}

# ─── Typography families par visual_family ───────────────────────────────────

TYPOGRAPHY_FAMILIES: dict[str, list[str]] = {
    "editorial_magazine":   ["serif_editorial",   "sans_editorial"],
    "luxury_minimal":       ["serif_luxury",      "sans_luxury"],
    "playful_brand":        ["display_playful",   "rounded_playful"],
    "warm_human":           ["humanist_sans",     "serif_warm"],
    "startup_clean":        ["geometric_sans",    "system_sans"],
    "corporate_pro":        ["corporate_sans",    "corporate_serif"],
    "tech_futurist":        ["mono_tech",         "geometric_tech"],
    "brutalist":            ["slab_brutal",       "grotesque_brutal"],
    "organic_natural":      ["organic_serif",     "handwritten_natural"],
    "premium_craft":        ["refined_serif",     "craft_sans"],
    "bold_challenger":      ["bold_display",      "condensed_impact"],
    "creative_studio":      ["experimental_type", "mixed_editorial"],
}

# ─── Allowed layouts par visual_family ───────────────────────────────────────

ALLOWED_LAYOUTS: dict[str, list[str]] = {
    "editorial_magazine":   ["editorial_flow", "magazine_spread", "vertical_narrative", "editorial_flow_b"],
    "luxury_minimal":       ["minimal_whitespace", "centered_narrative", "typographic_poster", "editorial_flow"],
    "playful_brand":        ["card_mosaic", "zigzag_cascade", "hero_dominant", "staggered_blocks"],
    "warm_human":           ["centered_narrative", "zigzag_cascade", "vertical_narrative", "staggered_blocks"],
    "startup_clean":        ["hero_dominant", "modular_grid", "staggered_blocks", "modular_grid_b"],
    "corporate_pro":        ["sidebar_anchored", "modular_grid", "asymmetrical_split", "staggered_blocks_b"],
    "tech_futurist":        ["data_forward", "modular_grid", "filmstrip_scroll", "diagonal_tension"],
    "brutalist":            ["brutalist_stack", "typographic_poster", "diagonal_tension"],
    "organic_natural":      ["vertical_narrative", "centered_narrative", "minimal_whitespace"],
    "premium_craft":        ["editorial_flow", "layered_overlap", "magazine_spread"],
    "bold_challenger":      ["hero_dominant", "diagonal_tension", "filmstrip_scroll", "brutalist_stack"],
    "creative_studio":      ["layered_overlap", "diagonal_tension", "card_mosaic", "asymmetrical_split"],
}

# ─── Allowed hero types par layout strategy ──────────────────────────────────

ALLOWED_HEROES: dict[str, list[str]] = {
    "editorial_flow":       ["offset_text_image", "editorial_headline_only", "text_panel_floating_media"],
    "magazine_spread":      ["offset_text_image", "full_bleed_with_overlay", "split_diagonal"],
    "vertical_narrative":   ["editorial_headline_only", "centered_statement", "manifesto_block"],
    "asymmetrical_split":   ["split_diagonal", "asymmetric_overlap", "text_panel_floating_media"],
    "staggered_blocks":     ["offset_text_image", "split_diagonal", "asymmetric_overlap"],
    "modular_grid":         ["centered_statement", "full_bleed_with_overlay", "split_diagonal"],
    "brutalist_stack":      ["brutalist_text_dominant", "typographic_only", "oversized_number_hero"],
    "layered_overlap":      ["full_bleed_with_overlay", "asymmetric_overlap", "split_diagonal"],
    "diagonal_tension":     ["split_diagonal", "asymmetric_overlap", "full_bleed_with_overlay"],
    "centered_narrative":   ["centered_statement", "manifesto_block", "editorial_headline_only"],
    "hero_dominant":        ["full_bleed_with_overlay", "centered_statement", "typographic_only"],
    "zigzag_cascade":       ["offset_text_image", "split_diagonal", "text_panel_floating_media"],
    "minimal_whitespace":   ["editorial_headline_only", "centered_statement", "typographic_only"],
    "filmstrip_scroll":     ["full_bleed_with_overlay", "split_color_block", "split_diagonal"],
    "card_mosaic":          ["centered_statement", "offset_text_image", "split_color_block"],
    "typographic_poster":   ["typographic_only", "manifesto_block", "oversized_number_hero"],
    "sidebar_anchored":     ["split_color_block", "offset_text_image", "editorial_headline_only"],
    "data_forward":         ["oversized_number_hero", "data_forward", "centered_statement"],
    "editorial_flow_b":     ["offset_text_image", "editorial_headline_only"],
    "staggered_blocks_b":   ["split_diagonal", "asymmetric_overlap"],
    "modular_grid_b":       ["centered_statement", "full_bleed_with_overlay"],
}

# ─── Composition patterns ────────────────────────────────────────────────────

COMPOSITION_PATTERNS: dict[str, dict] = {
    "editorial_flow":       {"density": "low",    "grid": "12col", "section_variation": "high"},
    "magazine_spread":      {"density": "medium", "grid": "12col", "section_variation": "high"},
    "vertical_narrative":   {"density": "low",    "grid": "8col",  "section_variation": "medium"},
    "asymmetrical_split":   {"density": "medium", "grid": "12col", "section_variation": "high"},
    "staggered_blocks":     {"density": "medium", "grid": "12col", "section_variation": "high"},
    "modular_grid":         {"density": "high",   "grid": "12col", "section_variation": "medium"},
    "brutalist_stack":      {"density": "high",   "grid": "free",  "section_variation": "low"},
    "layered_overlap":      {"density": "medium", "grid": "free",  "section_variation": "high"},
    "diagonal_tension":     {"density": "high",   "grid": "free",  "section_variation": "high"},
    "centered_narrative":   {"density": "low",    "grid": "8col",  "section_variation": "low"},
    "hero_dominant":        {"density": "low",    "grid": "12col", "section_variation": "low"},
    "zigzag_cascade":       {"density": "medium", "grid": "12col", "section_variation": "medium"},
    "minimal_whitespace":   {"density": "low",    "grid": "8col",  "section_variation": "low"},
    "filmstrip_scroll":     {"density": "high",   "grid": "full",  "section_variation": "low"},
    "card_mosaic":          {"density": "high",   "grid": "masonry","section_variation": "medium"},
    "typographic_poster":   {"density": "low",    "grid": "free",  "section_variation": "low"},
    "sidebar_anchored":     {"density": "high",   "grid": "sidebar","section_variation": "medium"},
    "data_forward":         {"density": "high",   "grid": "12col", "section_variation": "medium"},
    "editorial_flow_b":     {"density": "low",    "grid": "12col", "section_variation": "high"},
    "staggered_blocks_b":   {"density": "medium", "grid": "12col", "section_variation": "high"},
    "modular_grid_b":       {"density": "high",   "grid": "12col", "section_variation": "medium"},
}
