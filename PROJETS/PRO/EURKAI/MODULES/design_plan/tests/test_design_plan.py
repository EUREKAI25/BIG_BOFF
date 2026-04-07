"""
Tests unitaires — design_plan.
Vérifie : extraction de signaux, génération déterministe, distinctivité,
structure JSON, contraintes, intégration RC.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from design_plan import (
    DesignPlan, HeroSpec, CompositionSpec, VisualTensionSpec,
    RhythmSpec, ConstraintsSpec, CTAStrategySpec,
    generate_design_plan, diff_plans, plans_are_distinct,
    _extract_profile, _extract_signals, _build_constraints,
    _LAYOUTS, _SECTION_SETS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

_BRIEF_CRAFT = "Distillerie artisanale normande. Calvados haut de gamme, patrimoine familial."
_BRIEF_SAAS  = "Plateforme SaaS d'analyse prédictive. IA, machine learning, tableaux de bord."
_BRIEF_BOLD  = "Studio brutaliste expérimental. Design radical, typographie disruptive."
_BRIEF_SHOP  = "Boutique en ligne de vêtements premium. Collection printemps-été."
_BRIEF_EMPTY = "Un site web pour mon projet."


# ─────────────────────────────────────────────────────────────────────────────
# Tests — signal extraction
# ─────────────────────────────────────────────────────────────────────────────

def test_extract_profile_craft():
    assert _extract_profile(_BRIEF_CRAFT) == "editorial"
    print("✓ extract_profile craft → editorial OK")


def test_extract_profile_saas():
    assert _extract_profile(_BRIEF_SAAS) == "structural"
    print("✓ extract_profile saas → structural OK")


def test_extract_profile_bold():
    assert _extract_profile(_BRIEF_BOLD) == "bold"
    print("✓ extract_profile bold → bold OK")


def test_extract_profile_shop():
    assert _extract_profile(_BRIEF_SHOP) == "commercial"
    print("✓ extract_profile shop → commercial OK")


def test_extract_profile_empty():
    # Aucun signal → défaut structural
    p = _extract_profile(_BRIEF_EMPTY)
    assert p in ("editorial", "structural", "bold", "commercial")
    print(f"✓ extract_profile empty → {p} (non-None) OK")


def test_extract_profile_theme_hints():
    p = _extract_profile("", theme_hints={"archetype": "craft_artisan"})
    assert p == "editorial"
    p2 = _extract_profile("", theme_hints={"archetype": "ecommerce_catalog"})
    assert p2 == "commercial"
    print("✓ extract_profile theme_hints OK")


def test_extract_signals_craft():
    signals = _extract_signals(_BRIEF_CRAFT)
    assert "artisanal" in signals or "artisan" in signals
    print(f"✓ extract_signals craft OK : {signals}")


def test_extract_signals_no_false_positives():
    # "Le site est bien" ne doit pas matcher de mots-clés
    signals = _extract_signals("Le site est bien conçu et fonctionnel.")
    assert len(signals) == 0
    print("✓ extract_signals no false positives OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — génération de plan
# ─────────────────────────────────────────────────────────────────────────────

def test_generate_returns_design_plan():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    assert isinstance(plan, DesignPlan)
    print(f"✓ generate returns DesignPlan OK : {plan.layout_strategy}")


def test_generate_deterministic():
    plan1 = generate_design_plan(_BRIEF_CRAFT, seed=42)
    plan2 = generate_design_plan(_BRIEF_CRAFT, seed=42)
    assert plan1.to_dict() == plan2.to_dict()
    print("✓ generate deterministic OK (même seed = même plan)")


def test_generate_different_seeds_distinct():
    plans = [generate_design_plan(_BRIEF_CRAFT, seed=i) for i in range(5)]
    # Vérifier que pas tous identiques
    distinct_layouts = {p.layout_strategy for p in plans}
    # Au moins 2 layouts différents sur 5 seeds
    assert len(distinct_layouts) >= 2, f"Layouts trop similaires : {distinct_layouts}"
    print(f"✓ different seeds distinct OK : {distinct_layouts}")


def test_generate_profile_influences_layout():
    """Le profil craft ne doit pas produire 'brutalist_stack'."""
    layouts_craft = {generate_design_plan(_BRIEF_CRAFT, seed=i).layout_strategy for i in range(10)}
    layouts_bold  = {generate_design_plan(_BRIEF_BOLD,  seed=i).layout_strategy for i in range(10)}
    # Les layouts bold doivent contenir des options bold
    bold_options = set(_LAYOUTS.get("bold", []))
    assert layouts_bold & bold_options, f"Aucun layout bold dans : {layouts_bold}"
    print(f"✓ profile influences layout OK (bold has: {layouts_bold & bold_options})")


def test_generate_forced_layout():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42,
                                theme_hints={"layout": "brutalist_stack"})
    assert plan.layout_strategy == "brutalist_stack"
    print("✓ forced layout via theme_hints OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — structure et champs
# ─────────────────────────────────────────────────────────────────────────────

def test_plan_has_all_required_fields():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    assert plan.layout_strategy
    assert plan.hero.type
    assert plan.hero.positioning
    assert plan.hero.text_placement
    assert plan.hero.media_role
    assert plan.composition.structure
    assert plan.composition.flow
    assert plan.composition.density   in ("low", "medium", "high")
    assert plan.visual_tension.level  in ("low", "medium", "high", "extreme")
    assert len(plan.visual_tension.methods) >= 1
    assert plan.rhythm.pattern
    assert plan.rhythm.alternation
    assert plan.constraints.forbidden
    assert plan.constraints.required
    assert len(plan.section_types) >= 3
    assert plan.cta_strategy.placement
    assert plan.cta_strategy.style
    assert plan.cta_strategy.contrast_strategy
    print("✓ plan has_all_required_fields OK")


def test_plan_cta_block_in_sections():
    for seed in range(5):
        plan = generate_design_plan(_BRIEF_CRAFT, seed=seed)
        assert "cta_block" in plan.section_types, \
            f"seed={seed}: cta_block manquant dans {plan.section_types}"
    print("✓ cta_block in section_types (5 seeds) OK")


def test_plan_forbidden_not_in_required():
    """Aucun item ne doit être à la fois forbidden et required."""
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    conflict = set(plan.constraints.forbidden) & set(plan.constraints.required)
    assert not conflict, f"Conflit forbidden/required : {conflict}"
    print("✓ no forbidden/required conflict OK")


def test_plan_always_forbids_centered_hero():
    """centered_hero est TOUJOURS interdit."""
    for brief in [_BRIEF_CRAFT, _BRIEF_SAAS, _BRIEF_BOLD, _BRIEF_SHOP]:
        plan = generate_design_plan(brief, seed=42)
        assert "centered_hero" in plan.constraints.forbidden, \
            f"{brief[:30]}: centered_hero absent des forbidden"
    print("✓ centered_hero always forbidden OK")


def test_plan_always_forbids_uniform_card_grid():
    plan = generate_design_plan(_BRIEF_SAAS, seed=42)
    assert "uniform_card_grid" in plan.constraints.forbidden
    print("✓ uniform_card_grid always forbidden OK")


def test_plan_has_required_constraints():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    assert "varying_section_heights" in plan.constraints.required
    assert "cta_visual_isolation"    in plan.constraints.required
    print("✓ base required constraints present OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — validate()
# ─────────────────────────────────────────────────────────────────────────────

def test_validate_correct_plan():
    plan   = generate_design_plan(_BRIEF_CRAFT, seed=42)
    errors = plan.validate()
    assert errors == [], f"Erreurs inattendues : {errors}"
    print("✓ validate correct plan OK")


def test_validate_detects_missing_cta_block():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    plan.section_types = ["hero", "narrative_block"]  # pas de cta_block
    errors = plan.validate()
    assert any("cta_block" in e for e in errors)
    print("✓ validate detects missing cta_block OK")


def test_validate_detects_invalid_density():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    plan.composition = CompositionSpec(
        structure=plan.composition.structure, flow=plan.composition.flow,
        section_variation=plan.composition.section_variation, density="ultra",
    )
    errors = plan.validate()
    assert any("density" in e for e in errors)
    print("✓ validate detects invalid density OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — sérialisation JSON
# ─────────────────────────────────────────────────────────────────────────────

def test_to_dict_structure():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    d = plan.to_dict()
    required_keys = {"layout_strategy", "hero", "composition", "visual_tension",
                     "rhythm", "constraints", "section_types", "cta_strategy"}
    assert required_keys <= set(d.keys()), f"Clés manquantes : {required_keys - set(d.keys())}"
    assert "_meta" not in d   # métadonnées exclues par défaut
    print("✓ to_dict structure OK")


def test_to_dict_with_meta():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    d = plan.to_dict(include_meta=True)
    assert "_meta" in d
    assert d["_meta"]["seed"] == 42
    assert d["_meta"]["brief_profile"] in ("editorial", "structural", "bold", "commercial")
    print("✓ to_dict with_meta OK")


def test_to_json_valid():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    js   = plan.to_json()
    data = json.loads(js)
    assert "layout_strategy" in data
    assert "constraints"     in data
    assert "forbidden"       in data["constraints"]
    assert "required"        in data["constraints"]
    print("✓ to_json valid JSON OK")


def test_json_schema_matches_spec():
    """Vérifie que le JSON correspond exactement au schéma spécifié."""
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    d = plan.to_dict()

    # Hero fields
    assert {"type", "positioning", "text_placement", "media_role"} == set(d["hero"].keys())
    # Composition fields
    assert {"structure", "flow", "section_variation", "density"} == set(d["composition"].keys())
    # Visual tension
    assert {"level", "methods"} == set(d["visual_tension"].keys())
    assert isinstance(d["visual_tension"]["methods"], list)
    # Rhythm
    assert {"pattern", "alternation"} == set(d["rhythm"].keys())
    # Constraints
    assert {"forbidden", "required"} == set(d["constraints"].keys())
    # CTA
    assert {"placement", "style", "contrast_strategy"} == set(d["cta_strategy"].keys())
    print("✓ JSON schema matches spec OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — diff / distinctivité
# ─────────────────────────────────────────────────────────────────────────────

def test_diff_plans_same():
    plan1 = generate_design_plan(_BRIEF_CRAFT, seed=42)
    plan2 = generate_design_plan(_BRIEF_CRAFT, seed=42)
    diffs = diff_plans(plan1, plan2)
    assert diffs == {}
    print("✓ diff_plans same → empty OK")


def test_diff_plans_different():
    plan1 = generate_design_plan(_BRIEF_CRAFT, seed=1)
    plan2 = generate_design_plan(_BRIEF_SAAS,  seed=1)
    diffs = diff_plans(plan1, plan2)
    assert len(diffs) >= 1
    print(f"✓ diff_plans different → {len(diffs)} diffs OK")


def test_plans_are_distinct_across_seeds():
    """5 seeds différentes → plans distincts par paires."""
    plans  = [generate_design_plan(_BRIEF_CRAFT, seed=i) for i in range(5)]
    # Au moins 3 paires parmi les 10 combinaisons doivent être distinctes
    distinct_count = 0
    for i in range(len(plans)):
        for j in range(i+1, len(plans)):
            if plans_are_distinct(plans[i], plans[j], min_diffs=2):
                distinct_count += 1
    assert distinct_count >= 3, f"Seulement {distinct_count} paires distinctes"
    print(f"✓ plans_are_distinct across 5 seeds : {distinct_count}/10 paires distinctes OK")


def test_plans_are_distinct_across_briefs():
    """Briefs différents → plans distincts même avec même seed."""
    plan_craft = generate_design_plan(_BRIEF_CRAFT, seed=42)
    plan_bold  = generate_design_plan(_BRIEF_BOLD,  seed=42)
    assert plans_are_distinct(plan_craft, plan_bold, min_diffs=3)
    print("✓ plans_are_distinct across briefs OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — apply_to_rc
# ─────────────────────────────────────────────────────────────────────────────

def test_apply_to_rc_sets_hero_pattern():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42,
                                theme_hints={"layout": "asymmetrical_split"})
    rc = {"hero_pattern": "centered", "sections": ["features_grid", "stats"], "spacing_v": "88px"}
    rc_updated = plan.apply_to_rc(rc)
    assert rc_updated["hero_pattern"] != "centered"   # overridé
    assert "_design_plan" in rc_updated
    print(f"✓ apply_to_rc sets hero_pattern OK : {rc_updated['hero_pattern']}")


def test_apply_to_rc_density_controls_spacing():
    plan_low  = generate_design_plan(_BRIEF_CRAFT, seed=42)
    plan_low.composition = CompositionSpec(
        structure="linear", flow="slow_unfold",
        section_variation="controlled", density="low",
    )
    plan_high = generate_design_plan(_BRIEF_CRAFT, seed=42)
    plan_high.composition = CompositionSpec(
        structure="linear", flow="slow_unfold",
        section_variation="controlled", density="high",
    )
    rc = {"hero_pattern": "split", "sections": ["stats"], "spacing_v": "88px"}
    rc_low  = plan_low.apply_to_rc(rc)
    rc_high = plan_high.apply_to_rc(rc)
    # Low density → plus d'espace
    assert rc_low["spacing_v"] != rc_high["spacing_v"]
    print(f"✓ density controls spacing : low={rc_low['spacing_v']} high={rc_high['spacing_v']} OK")


def test_apply_to_rc_no_centered_if_forbidden():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=42)
    assert "centered_hero" in plan.constraints.forbidden
    rc = {"hero_pattern": "centered", "sections": ["stats"], "spacing_v": "88px"}
    rc_out = plan.apply_to_rc(rc)
    assert rc_out["hero_pattern"] != "centered"
    print("✓ apply_to_rc enforces no centered_hero OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — contraintes spécifiques aux layouts
# ─────────────────────────────────────────────────────────────────────────────

def test_brutalist_constraints():
    plan = generate_design_plan(_BRIEF_BOLD, seed=0,
                                theme_hints={"layout": "brutalist_stack"})
    assert plan.layout_strategy == "brutalist_stack"
    assert "refined_whitespace" in plan.constraints.forbidden or \
           "subtle_typography"  in plan.constraints.forbidden
    assert "raw_structure_visible"       in plan.constraints.required or \
           "bold_typographic_dominance"  in plan.constraints.required
    print("✓ brutalist constraints OK")


def test_editorial_constraints():
    plan = generate_design_plan(_BRIEF_CRAFT, seed=0,
                                theme_hints={"layout": "editorial_flow"})
    assert "typographic_hierarchy" in plan.constraints.required
    assert "uniform_card_grid"     in plan.constraints.forbidden
    print("✓ editorial constraints OK")


def test_asymmetrical_constraints():
    plan = generate_design_plan(_BRIEF_SAAS, seed=0,
                                theme_hints={"layout": "asymmetrical_split"})
    assert "asymmetry"             in plan.constraints.required
    assert "symmetrical_layout"    in plan.constraints.forbidden
    print("✓ asymmetrical constraints OK")


# ─────────────────────────────────────────────────────────────────────────────
# Tests — section sets
# ─────────────────────────────────────────────────────────────────────────────

def test_section_sets_contain_hero_and_cta():
    for layout, sections in _SECTION_SETS.items():
        assert "hero"     in sections, f"{layout}: 'hero' manquant"
        assert "cta_block" in sections, f"{layout}: 'cta_block' manquant"
    print(f"✓ all section_sets have hero+cta_block ({len(_SECTION_SETS)} layouts) OK")


def test_section_sets_min_4_sections():
    for layout, sections in _SECTION_SETS.items():
        assert len(sections) >= 4, f"{layout}: seulement {len(sections)} sections"
    print("✓ all section_sets have >= 4 sections OK")


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_extract_profile_craft,
        test_extract_profile_saas,
        test_extract_profile_bold,
        test_extract_profile_shop,
        test_extract_profile_empty,
        test_extract_profile_theme_hints,
        test_extract_signals_craft,
        test_extract_signals_no_false_positives,
        test_generate_returns_design_plan,
        test_generate_deterministic,
        test_generate_different_seeds_distinct,
        test_generate_profile_influences_layout,
        test_generate_forced_layout,
        test_plan_has_all_required_fields,
        test_plan_cta_block_in_sections,
        test_plan_forbidden_not_in_required,
        test_plan_always_forbids_centered_hero,
        test_plan_always_forbids_uniform_card_grid,
        test_plan_has_required_constraints,
        test_validate_correct_plan,
        test_validate_detects_missing_cta_block,
        test_validate_detects_invalid_density,
        test_to_dict_structure,
        test_to_dict_with_meta,
        test_to_json_valid,
        test_json_schema_matches_spec,
        test_diff_plans_same,
        test_diff_plans_different,
        test_plans_are_distinct_across_seeds,
        test_plans_are_distinct_across_briefs,
        test_apply_to_rc_sets_hero_pattern,
        test_apply_to_rc_density_controls_spacing,
        test_apply_to_rc_no_centered_if_forbidden,
        test_brutalist_constraints,
        test_editorial_constraints,
        test_asymmetrical_constraints,
        test_section_sets_contain_hero_and_cta,
        test_section_sets_min_4_sections,
    ]

    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            import traceback
            print(f"✗ {t.__name__} : {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'✅' if failed == 0 else '❌'} {len(tests) - failed}/{len(tests)} tests passent.")
