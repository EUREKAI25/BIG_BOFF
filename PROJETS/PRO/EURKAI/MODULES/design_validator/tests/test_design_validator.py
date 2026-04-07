"""
Tests unitaires — design_validator
Pas d'API, pas de dépendances externes.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from design_validator.src.design_validator import (
    DesignValidator,
    ValidationResult,
    validate_layout,
    _check_forbidden_item,
    _check_required_item,
    PASS_THRESHOLD,
    MAX_SECTION_REPETITION,
    SEVERITY_MAJOR,
    SEVERITY_MEDIUM,
    SEVERITY_MINOR,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_plan(
    forbidden=None,
    required=None,
    hero_type="offset_text_image",
    hero_positioning="left_panel_right_media",
    hero_text_placement="half_panel_left",
    layout_strategy="asymmetrical_split",
    density="medium",
    section_types=None,
):
    return {
        "layout_strategy": layout_strategy,
        "hero": {
            "type":           hero_type,
            "positioning":    hero_positioning,
            "text_placement": hero_text_placement,
            "media_role":     "atmospheric_backdrop",
        },
        "composition": {"density": density, "structure": "alternating"},
        "constraints": {
            "forbidden": forbidden if forbidden is not None else ["centered_hero", "uniform_card_grid"],
            "required":  required  if required  is not None else ["varying_section_heights", "cta_visual_isolation"],
        },
        "section_types": section_types if section_types is not None else [
            "hero", "feature_block", "testimonial", "cta_block"
        ],
    }


def _make_layout(
    hero_type="offset_text_image",
    hero_positioning="left_panel_right_media",
    hero_text_placement="half_panel_left",
    sections=None,
    global_symmetry=False,
    equal_section_heights=False,
    varying_heights=True,
    has_typographic_break=True,
    density="medium",
    repeated_layouts=None,
):
    if sections is None:
        sections = [
            {"type": "hero",          "layout_variant": "asymmetric_split",     "symmetric": False, "visually_isolated": False},
            {"type": "feature_block", "layout_variant": "staggered_two_column", "symmetric": False, "visually_isolated": False},
            {"type": "testimonial",   "layout_variant": "editorial_pull_quote",  "symmetric": False, "visually_isolated": False},
            {"type": "cta_block",     "layout_variant": "full_width_cta",        "symmetric": False, "visually_isolated": True},
        ]
    return {
        "hero": {
            "type":           hero_type,
            "positioning":    hero_positioning,
            "text_placement": hero_text_placement,
            "media_role":     "atmospheric_backdrop",
        },
        "sections": sections,
        "structure": {
            "global_symmetry":       global_symmetry,
            "equal_section_heights": equal_section_heights,
            "varying_heights":       varying_heights,
            "has_typographic_break": has_typographic_break,
            "density":               density,
            "repeated_layouts":      repeated_layouts or {},
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1. Imports et instanciation
# ─────────────────────────────────────────────────────────────────────────────

def test_imports():
    assert DesignValidator is not None
    assert ValidationResult is not None
    assert validate_layout is not None


def test_validator_instantiation():
    v = DesignValidator()
    assert hasattr(v, "validate")


def test_validation_result_fields():
    r = ValidationResult(valid=True, score=95, fail_reasons=[], warnings=["w1"])
    assert r.valid is True
    assert r.score == 95
    assert r.fail_reasons == []
    assert r.warnings == ["w1"]


def test_validation_result_to_dict():
    r = ValidationResult(valid=False, score=45, fail_reasons=["f1"], warnings=[])
    d = r.to_dict()
    assert set(d.keys()) == {"valid", "score", "fail_reasons", "warnings"}
    assert d["valid"] is False
    assert d["score"] == 45
    assert "f1" in d["fail_reasons"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. Layout valide — PASS
# ─────────────────────────────────────────────────────────────────────────────

def test_valid_layout_passes():
    plan   = _make_plan()
    layout = _make_layout()
    result = validate_layout(plan, layout)
    assert result.valid is True
    assert result.score >= PASS_THRESHOLD
    assert result.fail_reasons == []


def test_valid_layout_convenience_function():
    plan   = _make_plan()
    layout = _make_layout()
    result = validate_layout(plan, layout)
    assert isinstance(result, ValidationResult)
    assert result.valid is True


# ─────────────────────────────────────────────────────────────────────────────
# 3. Contraintes FORBIDDEN — hard constraints
# ─────────────────────────────────────────────────────────────────────────────

def test_forbidden_centered_hero_fails():
    plan   = _make_plan(forbidden=["centered_hero"])
    layout = _make_layout(hero_type="centered_hero", hero_positioning="center_dominant")
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("centered_hero" in r for r in result.fail_reasons)


def test_forbidden_centered_hero_via_positioning():
    plan   = _make_plan(forbidden=["centered_hero"])
    layout = _make_layout(hero_positioning="center_aligned")
    result = validate_layout(plan, layout)
    assert result.valid is False


def test_forbidden_centered_hero_via_text_placement():
    plan   = _make_plan(forbidden=["centered_hero"])
    layout = _make_layout(hero_text_placement="centered_below_headline")
    result = validate_layout(plan, layout)
    assert result.valid is False


def test_forbidden_uniform_card_grid_fails():
    sections = [
        {"type": "hero",          "layout_variant": "asymmetric_split", "symmetric": False},
        {"type": "feature_block", "layout_variant": "card_grid",        "symmetric": False},
        {"type": "feature_block", "layout_variant": "product_grid",     "symmetric": False},
        {"type": "cta_block",     "layout_variant": "full_width_cta",   "symmetric": False, "visually_isolated": True},
    ]
    plan   = _make_plan(forbidden=["uniform_card_grid"])
    layout = _make_layout(sections=sections)
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("uniform_card_grid" in r for r in result.fail_reasons)


def test_forbidden_uniform_card_grid_single_section_no_fail():
    """Un seul bloc contenu en grid ne déclenche pas uniform_card_grid."""
    sections = [
        {"type": "hero",          "layout_variant": "asymmetric_split", "symmetric": False},
        {"type": "feature_block", "layout_variant": "card_grid",        "symmetric": False},
        {"type": "cta_block",     "layout_variant": "full_width_cta",   "symmetric": False, "visually_isolated": True},
    ]
    plan   = _make_plan(forbidden=["uniform_card_grid"], required=[])
    layout = _make_layout(sections=sections)
    result = validate_layout(plan, layout)
    # 1 seul block contenu = pas "uniform"
    assert not any("uniform_card_grid" in r for r in result.fail_reasons)


def test_forbidden_equal_section_heights_fails():
    plan   = _make_plan(forbidden=["equal_section_heights"])
    layout = _make_layout(equal_section_heights=True)
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("equal_section_heights" in r for r in result.fail_reasons)


def test_forbidden_symmetrical_column_layout_fails():
    sections = [
        {"type": "hero",          "layout_variant": "asymmetric_split",    "symmetric": False},
        {"type": "feature_block", "layout_variant": "two_column_symmetric", "symmetric": True},
        {"type": "cta_block",     "layout_variant": "full_width_cta",       "symmetric": False, "visually_isolated": True},
    ]
    plan   = _make_plan(forbidden=["symmetrical_column_layout"])
    layout = _make_layout(sections=sections)
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("symmetrical_column_layout" in r for r in result.fail_reasons)


def test_hard_constraint_overrides_passing_score():
    """Même si le score calculé est >= 70, une hard constraint → FAIL."""
    plan = _make_plan(
        forbidden=["centered_hero"],
        required=[],
        section_types=[],  # pas de cta check
    )
    layout = _make_layout(
        hero_type="centered_hero",
        hero_positioning="center_dominant",
    )
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("centered_hero" in r for r in result.fail_reasons)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Contraintes REQUIRED
# ─────────────────────────────────────────────────────────────────────────────

def test_required_varying_heights_missing_fails():
    plan   = _make_plan(required=["varying_section_heights"], forbidden=[])
    layout = _make_layout(varying_heights=False, equal_section_heights=True)
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("varying_section_heights" in r for r in result.fail_reasons)


def test_required_cta_isolation_missing_fails():
    sections = [
        {"type": "hero",          "layout_variant": "asymmetric_split", "symmetric": False},
        {"type": "feature_block", "layout_variant": "staggered",        "symmetric": False},
        {"type": "cta_block",     "layout_variant": "full_width_cta",   "symmetric": False, "visually_isolated": False},
    ]
    plan   = _make_plan(required=["cta_visual_isolation"], forbidden=[])
    layout = _make_layout(sections=sections)
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("cta_visual_isolation" in r for r in result.fail_reasons)


def test_required_asymmetry_fails_when_symmetric():
    plan   = _make_plan(required=["asymmetry"], forbidden=[])
    layout = _make_layout(global_symmetry=True)
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("asymmetry" in r for r in result.fail_reasons)


def test_required_typographic_break_missing():
    plan   = _make_plan(required=["at_least_one_typographic_hierarchy_break"], forbidden=[])
    layout = _make_layout(has_typographic_break=False)
    result = validate_layout(plan, layout)
    assert result.valid is False


def test_unknown_required_item_does_not_penalize():
    """Item requis inconnu → on ne peut pas vérifier → pas de pénalité."""
    plan   = _make_plan(required=["some_unknown_requirement_xyz"], forbidden=[])
    layout = _make_layout()
    result = validate_layout(plan, layout)
    assert not any("some_unknown_requirement_xyz" in r for r in result.fail_reasons)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Correspondance Hero
# ─────────────────────────────────────────────────────────────────────────────

def test_hero_type_mismatch_medium_penalty():
    plan   = _make_plan(hero_type="offset_text_image", forbidden=[], required=[], section_types=[])
    layout = _make_layout(hero_type="brutalist_text_dominant")
    result = validate_layout(plan, layout)
    assert result.score == 100 - SEVERITY_MEDIUM
    assert result.valid is True  # 80 >= 70
    assert any("Type de hero" in w for w in result.warnings)


def test_hero_positioning_mismatch_medium_penalty():
    plan   = _make_plan(hero_positioning="left_panel_right_media", forbidden=[], required=[], section_types=[])
    layout = _make_layout(hero_positioning="top_left_dominant")
    result = validate_layout(plan, layout)
    assert result.score == 100 - SEVERITY_MEDIUM
    assert any("Positionnement hero" in w for w in result.warnings)


def test_hero_text_placement_mismatch_minor_penalty():
    plan   = _make_plan(hero_text_placement="half_panel_left", forbidden=[], required=[], section_types=[])
    layout = _make_layout(hero_text_placement="full_width_below")
    result = validate_layout(plan, layout)
    assert result.score == 100 - SEVERITY_MINOR
    assert any("Placement du texte" in w for w in result.warnings)


def test_hero_match_exact_no_penalty():
    plan   = _make_plan(
        hero_type="offset_text_image",
        hero_positioning="left_panel_right_media",
        hero_text_placement="half_panel_left",
        forbidden=[], required=[], section_types=[],
    )
    layout = _make_layout(
        hero_type="offset_text_image",
        hero_positioning="left_panel_right_media",
        hero_text_placement="half_panel_left",
    )
    result = validate_layout(plan, layout)
    assert result.score == 100


def test_hero_empty_plan_fields_no_penalty():
    """Si le plan n'a pas de hero.type défini, pas de pénalité pour mismatch."""
    plan = {
        "hero": {},
        "composition": {},
        "constraints": {"forbidden": [], "required": []},
        "section_types": [],
    }
    layout = _make_layout(hero_type="anything")
    result = validate_layout(plan, layout)
    assert result.score == 100


# ─────────────────────────────────────────────────────────────────────────────
# 6. Répétition de layout
# ─────────────────────────────────────────────────────────────────────────────

def test_repetition_via_structure_dict():
    plan   = _make_plan(forbidden=[], required=[], section_types=[])
    layout = _make_layout(repeated_layouts={"card_grid": 4})
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("card_grid" in r for r in result.fail_reasons)
    assert any("4×" in r for r in result.fail_reasons)


def test_repetition_computed_from_sections():
    """Si repeated_layouts absent, le validator le calcule depuis les sections."""
    sections = [
        {"type": "hero",          "layout_variant": "asymmetric_split"},
        {"type": "feature_block", "layout_variant": "card_grid"},
        {"type": "feature_block", "layout_variant": "card_grid"},
        {"type": "feature_block", "layout_variant": "card_grid"},
        {"type": "feature_block", "layout_variant": "card_grid"},
        {"type": "cta_block",     "layout_variant": "full_width_cta", "visually_isolated": True},
    ]
    plan   = _make_plan(forbidden=[], required=[], section_types=[])
    layout = _make_layout(sections=sections)
    layout["structure"]["repeated_layouts"] = {}  # forcer recalcul
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("card_grid" in r for r in result.fail_reasons)


def test_repetition_exactly_at_max_no_fail():
    """Exactement MAX_SECTION_REPETITION fois → pas de fail."""
    plan   = _make_plan(forbidden=[], required=[], section_types=[])
    layout = _make_layout(repeated_layouts={"card_grid": MAX_SECTION_REPETITION})
    result = validate_layout(plan, layout)
    assert not any("card_grid" in r for r in result.fail_reasons)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Symétrie globale
# ─────────────────────────────────────────────────────────────────────────────

def test_global_symmetry_with_centered_hero_forbidden_fails():
    plan   = _make_plan(forbidden=["centered_hero", "symmetrical_column_layout"], required=[])
    layout = _make_layout(global_symmetry=True)
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("Symétrie globale" in r for r in result.fail_reasons)


def test_global_symmetry_not_in_forbidden_no_fail():
    """Symétrie globale OK si pas de centered_hero ni symmetrical_column dans forbidden."""
    plan   = _make_plan(forbidden=["uniform_card_grid"], required=[], section_types=[])
    layout = _make_layout(global_symmetry=True)
    result = validate_layout(plan, layout)
    assert not any("Symétrie globale" in r for r in result.fail_reasons)


def test_global_symmetry_symmetrical_column_in_forbidden_fails():
    plan   = _make_plan(forbidden=["symmetrical_column_layout"], required=[])
    layout = _make_layout(global_symmetry=True)
    result = validate_layout(plan, layout)
    assert result.valid is False


# ─────────────────────────────────────────────────────────────────────────────
# 8. Nombre de sections et CTA
# ─────────────────────────────────────────────────────────────────────────────

def test_section_count_too_few_medium_penalty():
    sections = [
        {"type": "hero",      "layout_variant": "asymmetric_split", "symmetric": False},
        {"type": "cta_block", "layout_variant": "full_width_cta",   "symmetric": False, "visually_isolated": True},
    ]
    plan   = _make_plan(forbidden=[], required=[])
    layout = _make_layout(sections=sections)
    result = validate_layout(plan, layout)
    # 2 sections < 3 → SEVERITY_MEDIUM déduit
    assert result.score <= 100 - SEVERITY_MEDIUM
    assert any("sections" in w for w in result.warnings)


def test_section_count_three_is_acceptable():
    sections = [
        {"type": "hero",          "layout_variant": "asymmetric_split", "symmetric": False},
        {"type": "feature_block", "layout_variant": "staggered",        "symmetric": False},
        {"type": "cta_block",     "layout_variant": "full_width_cta",   "symmetric": False, "visually_isolated": True},
    ]
    plan   = _make_plan(forbidden=[], required=[])
    layout = _make_layout(sections=sections)
    result = validate_layout(plan, layout)
    assert not any("sections" in w for w in result.warnings)


def test_cta_block_missing_fails():
    sections = [
        {"type": "hero",          "layout_variant": "asymmetric_split", "symmetric": False},
        {"type": "feature_block", "layout_variant": "staggered",        "symmetric": False},
        {"type": "testimonial",   "layout_variant": "editorial",        "symmetric": False},
    ]
    plan   = _make_plan(forbidden=[], required=[], section_types=["hero", "feature_block", "cta_block"])
    layout = _make_layout(sections=sections)
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("CTA" in r for r in result.fail_reasons)


def test_cta_not_in_plan_no_check():
    """Si le plan ne liste pas cta_block, on ne vérifie pas sa présence."""
    sections = [
        {"type": "hero",          "layout_variant": "asymmetric_split"},
        {"type": "feature_block", "layout_variant": "staggered"},
        {"type": "testimonial",   "layout_variant": "editorial"},
    ]
    plan   = _make_plan(forbidden=[], required=[], section_types=["hero", "feature_block"])
    layout = _make_layout(sections=sections)
    result = validate_layout(plan, layout)
    assert not any("CTA" in r for r in result.fail_reasons)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Densité
# ─────────────────────────────────────────────────────────────────────────────

def test_density_mismatch_minor_warning():
    plan   = _make_plan(density="low", forbidden=[], required=[], section_types=[])
    layout = _make_layout(density="high")
    result = validate_layout(plan, layout)
    assert result.score == 100 - SEVERITY_MINOR
    assert any("Densité" in w for w in result.warnings)


def test_density_match_no_penalty():
    plan   = _make_plan(density="medium", forbidden=[], required=[], section_types=[])
    layout = _make_layout(density="medium")
    result = validate_layout(plan, layout)
    assert not any("Densité" in w for w in result.warnings)


def test_density_empty_plan_no_check():
    plan = {"constraints": {"forbidden": [], "required": []}, "hero": {}, "section_types": []}
    layout = _make_layout(density="high")
    result = validate_layout(plan, layout)
    assert result.score == 100


# ─────────────────────────────────────────────────────────────────────────────
# 10. Score et seuils
# ─────────────────────────────────────────────────────────────────────────────

def test_score_below_threshold_fails_without_hard_constraint():
    """Plusieurs violations medium/minor → score < 70 → FAIL même sans hard constraint."""
    plan = _make_plan(
        hero_type="offset_text_image",
        hero_positioning="left_panel_right_media",
        density="low",
        forbidden=[],
        required=[],
        section_types=[],
    )
    layout = _make_layout(
        hero_type="brutalist_text_dominant",      # −20
        hero_positioning="top_left_dominant",     # −20
        density="high",                           # −5 = total −45 → score 55
    )
    result = validate_layout(plan, layout)
    assert result.score == 55
    assert result.valid is False  # 55 < 70


def test_score_exactly_at_threshold_passes():
    """Score == 60 (deux violations medium) → FAIL car < 70."""
    plan = _make_plan(
        hero_type="offset_text_image",
        hero_positioning="left_panel_right_media",
        density="medium",  # match → pas de pénalité densité
        forbidden=[],
        required=[],
        section_types=[],
    )
    layout = _make_layout(
        hero_type="brutalist_text_dominant",  # −20
        hero_positioning="top_left_dominant", # −20
        density="medium",                     # match
    )
    result = validate_layout(plan, layout)
    assert result.score == 60
    assert result.valid is False  # 60 < 70


def test_score_never_negative():
    """Score plancher à 0."""
    plan = _make_plan(forbidden=["centered_hero", "uniform_card_grid", "equal_section_heights"])
    sections = [
        {"type": "hero",          "layout_variant": "centered_grid", "symmetric": True},
        {"type": "feature_block", "layout_variant": "card_grid",     "symmetric": False},
        {"type": "feature_block", "layout_variant": "product_grid",  "symmetric": False},
    ]
    layout = _make_layout(
        hero_type="centered_hero",
        hero_positioning="center_dominant",
        hero_text_placement="centered_below",
        sections=sections,
        equal_section_heights=True,
        varying_heights=False,
    )
    result = validate_layout(plan, layout)
    assert result.score >= 0


# ─────────────────────────────────────────────────────────────────────────────
# 11. fail_reasons vs warnings
# ─────────────────────────────────────────────────────────────────────────────

def test_fail_reasons_contain_hard_violations():
    plan   = _make_plan(forbidden=["centered_hero"])
    layout = _make_layout(hero_type="centered_hero", hero_positioning="center_dominant")
    result = validate_layout(plan, layout)
    assert len(result.fail_reasons) >= 1
    assert all(isinstance(r, str) for r in result.fail_reasons)


def test_warnings_contain_soft_violations():
    plan = _make_plan(
        hero_type="offset_text_image",
        forbidden=[], required=[], section_types=[],
    )
    layout = _make_layout(hero_type="brutalist_text_dominant")
    result = validate_layout(plan, layout)
    assert len(result.warnings) >= 1
    assert result.fail_reasons == []


def test_no_overlap_between_fail_and_warnings():
    plan   = _make_plan()
    layout = _make_layout(
        hero_type="brutalist_text_dominant",
        hero_positioning="center_aligned",  # centré → centered_hero forbidden
    )
    result = validate_layout(plan, layout)
    # fail_reasons et warnings ne doivent pas contenir les mêmes messages
    assert set(result.fail_reasons).isdisjoint(set(result.warnings))


# ─────────────────────────────────────────────────────────────────────────────
# 12. Cas limites et robustesse
# ─────────────────────────────────────────────────────────────────────────────

def test_empty_plan_empty_layout():
    plan   = {}
    layout = {}
    result = validate_layout(plan, layout)
    assert isinstance(result, ValidationResult)
    assert result.score == 100
    assert result.valid is True


def test_empty_forbidden_required():
    plan   = _make_plan(forbidden=[], required=[], section_types=[])
    layout = _make_layout()
    result = validate_layout(plan, layout)
    assert result.score == 100
    assert result.valid is True


def test_no_sections_in_layout():
    plan   = _make_plan(forbidden=[], required=[], section_types=[])
    layout = {
        "hero": {"type": "offset_text_image", "positioning": "left_panel_right_media"},
        "sections": [],
        "structure": {"global_symmetry": False, "equal_section_heights": False},
    }
    result = validate_layout(plan, layout)
    assert isinstance(result, ValidationResult)


def test_generic_forbidden_item_in_variant():
    """Item générique inconnu : si présent dans layout_variant → fail."""
    sections = [
        {"type": "hero",          "layout_variant": "three_column_grid"},
        {"type": "feature_block", "layout_variant": "three_column_grid"},
        {"type": "cta_block",     "layout_variant": "full_width_cta", "visually_isolated": True},
    ]
    plan   = _make_plan(forbidden=["three_column_grid"], required=[], section_types=[])
    layout = _make_layout(sections=sections)
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("three_column_grid" in r for r in result.fail_reasons)


def test_standard_nav_hero_grid_footer_forbidden():
    """Pattern standard nav→hero→grid→footer interdit."""
    sections = [
        {"type": "navigation",    "layout_variant": "top_nav"},
        {"type": "hero",          "layout_variant": "full_bleed"},
        {"type": "feature_block", "layout_variant": "card_grid"},
        {"type": "testimonial",   "layout_variant": "product_grid"},
        {"type": "cta_block",     "layout_variant": "footer_cta", "visually_isolated": True},
    ]
    plan   = _make_plan(forbidden=["standard_nav_hero_grid_footer"], required=[])
    layout = _make_layout(sections=sections)
    result = validate_layout(plan, layout)
    assert result.valid is False
    assert any("standard_nav_hero_grid_footer" in r for r in result.fail_reasons)


# ─────────────────────────────────────────────────────────────────────────────
# 13. _check_forbidden_item / _check_required_item — unit tests
# ─────────────────────────────────────────────────────────────────────────────

def test_unit_check_forbidden_centered_hero_via_type():
    assert _check_forbidden_item("centered_hero", {"type": "centered"}, [], {}) is True


def test_unit_check_forbidden_centered_hero_not_present():
    hero = {"type": "offset_text_image", "positioning": "left_panel", "text_placement": "half_left"}
    assert _check_forbidden_item("centered_hero", hero, [], {}) is False


def test_unit_check_required_varying_heights_ok():
    structure = {"varying_heights": True, "equal_section_heights": False}
    assert _check_required_item("varying_section_heights", {}, [], structure) is True


def test_unit_check_required_varying_heights_fail():
    structure = {"varying_heights": False, "equal_section_heights": True}
    assert _check_required_item("varying_section_heights", {}, [], structure) is False


def test_unit_check_required_cta_isolation_present():
    sections  = [{"type": "cta_block", "visually_isolated": True}]
    assert _check_required_item("cta_visual_isolation", {}, sections, {}) is True


def test_unit_check_required_cta_isolation_absent_block():
    sections = [{"type": "feature_block", "visually_isolated": True}]
    assert _check_required_item("cta_visual_isolation", {}, sections, {}) is False


def test_unit_check_required_asymmetry_global_symmetry():
    structure = {"global_symmetry": True}
    assert _check_required_item("asymmetry", {}, [], structure) is False


def test_unit_check_required_asymmetry_no_symmetry():
    structure = {"global_symmetry": False}
    assert _check_required_item("asymmetry", {}, [], structure) is True
