"""
design_validator.py — Validateur PASS/FAIL d'un layout généré contre un Design Plan.

Ce module vérifie que la structure de layout produite RESPECTE STRICTEMENT le Design Plan.
Pas de suggestion. Pas de jugement esthétique. PASS ou FAIL.

Usage :
    from design_validator import validate_layout

    result = validate_layout(design_plan_dict, layout_dict)
    print(result.to_dict())
    # {"valid": True, "score": 85, "fail_reasons": [], "warnings": ["..."]}

Input format :
    design_plan : dict  — issu de DesignPlan.to_dict() ou JSON brut
    layout      : {
        "hero": {
            "type":          str,   # ex: "offset_text_image"
            "positioning":   str,   # ex: "left_panel_right_media"
            "text_placement": str,  # ex: "half_panel_left"
            "media_role":    str,   # ex: "atmospheric_backdrop"
        },
        "sections": [
            {
                "type":             str,   # ex: "hero", "feature_block", "cta_block"
                "layout_variant":   str,   # ex: "asymmetric_split", "card_grid"
                "symmetric":        bool,  # True si colonnes symétriques
                "visually_isolated": bool, # True pour cta_block isolé visuellement
            },
            ...
        ],
        "structure": {
            "global_symmetry":       bool,   # True si layout global symétrique
            "equal_section_heights": bool,   # True si toutes sections = même hauteur
            "varying_heights":       bool,   # True si hauteurs variées
            "has_typographic_break": bool,   # True si rupture de hiérarchie typo
            "density":               str,    # "low" | "medium" | "high"
            "repeated_layouts":      dict,   # {"variant": count} — calculé automatiquement si absent
        }
    }

Output :
    ValidationResult(valid, score, fail_reasons, warnings)
    score : 100 − Σ déductions (major=50, medium=20, minor=5)
    valid : score >= 70 ET aucune contrainte dure violée
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

PASS_THRESHOLD        = 70   # score minimum pour PASS
MAX_SECTION_REPETITION = 3   # même layout_variant répété > 3× → FAIL

SEVERITY_MAJOR  = 50
SEVERITY_MEDIUM = 20
SEVERITY_MINOR  =  5


# ─────────────────────────────────────────────────────────────────────────────
# Structures de données
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    valid:        bool
    score:        int
    fail_reasons: list = field(default_factory=list)
    warnings:     list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "valid":        self.valid,
            "score":        self.score,
            "fail_reasons": self.fail_reasons,
            "warnings":     self.warnings,
        }


@dataclass
class _Violation:
    message:  str
    severity: int   # SEVERITY_MAJOR / MEDIUM / MINOR
    is_hard:  bool  # True → toujours FAIL, quels que soient les autres scores


# ─────────────────────────────────────────────────────────────────────────────
# Détection des items FORBIDDEN
# ─────────────────────────────────────────────────────────────────────────────

def _check_forbidden_item(
    item: str,
    hero: dict,
    sections: list,
    structure: dict,
) -> bool:
    """
    Retourne True si le pattern interdit EST PRÉSENT dans le layout.
    Chaque item a sa propre logique de détection.
    """
    positioning    = hero.get("positioning", "").lower()
    text_placement = hero.get("text_placement", "").lower()
    hero_type      = hero.get("type", "").lower()
    section_types  = [s.get("type", "") for s in sections]
    variants       = [s.get("layout_variant", "") for s in sections]

    if item == "centered_hero":
        return (
            "center" in positioning
            or "centered" in text_placement
            or "centered" in hero_type
            or "full_center" in hero_type
            or hero_type == "centered"
        )

    if item == "uniform_card_grid":
        content = [s for s in sections if s.get("type") not in ("hero", "cta_block")]
        if len(content) < 2:
            return False
        return all("grid" in s.get("layout_variant", "") for s in content)

    if item == "standard_nav_hero_grid_footer":
        if len(section_types) < 4:
            return False
        # Pattern : nav, hero, *tout grid/card (type ou variant), footer/cta
        non_frame = sections[2:-1]
        def _is_grid_like(s: dict) -> bool:
            return (
                "grid" in s.get("type", "") or "card" in s.get("type", "")
                or "grid" in s.get("layout_variant", "") or "card" in s.get("layout_variant", "")
            )
        return (
            section_types[0] in ("nav", "header", "navigation")
            and section_types[1] == "hero"
            and section_types[-1] in ("footer", "cta_block")
            and bool(non_frame)
            and all(_is_grid_like(s) for s in non_frame)
        )

    if item == "equal_section_heights":
        return structure.get("equal_section_heights", False)

    if item == "symmetrical_column_layout":
        return any(
            s.get("symmetric", False) and "column" in s.get("layout_variant", "")
            for s in sections
        )

    # ─── Générique : l'item apparaît dans un variant ou type de section ───
    return (
        any(item in v for v in variants)
        or any(item in t for t in section_types)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Détection des items REQUIRED
# ─────────────────────────────────────────────────────────────────────────────

def _check_required_item(
    item: str,
    hero: dict,
    sections: list,
    structure: dict,
) -> bool:
    """
    Retourne True si l'élément requis EST PRÉSENT dans le layout.
    Retourne True par défaut pour les items inconnus (on ne peut pas vérifier).
    """
    if item == "varying_section_heights":
        return (
            structure.get("varying_heights", True)
            and not structure.get("equal_section_heights", False)
        )

    if item == "cta_visual_isolation":
        cta_sections = [s for s in sections if s.get("type") == "cta_block"]
        if not cta_sections:
            return False
        return any(s.get("visually_isolated", True) for s in cta_sections)

    if item == "at_least_one_typographic_hierarchy_break":
        return structure.get("has_typographic_break", True)

    if item == "asymmetry":
        return not structure.get("global_symmetry", False)

    if item in ("editorial_asymmetry", "directional_flow", "irregular_rhythm"):
        return not structure.get("global_symmetry", False)

    if item in ("structural_columns", "grid_precision", "modular_precision"):
        return any(
            "column" in s.get("layout_variant", "") or "grid" in s.get("layout_variant", "")
            for s in sections
        )

    if item in (
        "high_visual_impact", "scale_contrast", "typographic_dominance",
        "raw_composition", "visual_tension",
    ):
        return structure.get("has_typographic_break", True)

    # Inconnu — on ne peut pas détecter → on ne pénalise pas
    return True


# ─────────────────────────────────────────────────────────────────────────────
# DesignValidator
# ─────────────────────────────────────────────────────────────────────────────

class DesignValidator:
    """
    Valide un layout généré contre un Design Plan.
    Pure logique — pas de LLM, pas d'API.
    """

    def validate(self, design_plan: dict, layout: dict) -> ValidationResult:
        """
        Args:
            design_plan : dict issu de DesignPlan.to_dict()
            layout      : structure décrite ci-dessus

        Returns:
            ValidationResult(valid, score, fail_reasons, warnings)
        """
        violations: list[_Violation] = []

        hero      = layout.get("hero", {})
        sections  = layout.get("sections", [])
        structure = layout.get("structure", {})

        constraints = design_plan.get("constraints", {})
        forbidden   = constraints.get("forbidden", [])
        required    = constraints.get("required", [])

        # ── 1. Contraintes dures : items FORBIDDEN ─────────────────────────
        for item in forbidden:
            if _check_forbidden_item(item, hero, sections, structure):
                violations.append(_Violation(
                    message=f"Pattern interdit détecté : '{item}'",
                    severity=SEVERITY_MAJOR,
                    is_hard=True,
                ))

        # ── 2. Contraintes dures : items REQUIRED ──────────────────────────
        for item in required:
            if not _check_required_item(item, hero, sections, structure):
                violations.append(_Violation(
                    message=f"Élément requis absent : '{item}'",
                    severity=SEVERITY_MAJOR,
                    is_hard=True,
                ))

        # ── 3. Correspondance hero.type ────────────────────────────────────
        plan_hero       = design_plan.get("hero", {})
        plan_hero_type  = plan_hero.get("type", "")
        layout_hero_type = hero.get("type", "")
        if plan_hero_type and layout_hero_type and plan_hero_type != layout_hero_type:
            violations.append(_Violation(
                message=(
                    f"Type de hero ne correspond pas au plan : "
                    f"plan='{plan_hero_type}', layout='{layout_hero_type}'"
                ),
                severity=SEVERITY_MEDIUM,
                is_hard=False,
            ))

        # ── 4. Correspondance hero.positioning ─────────────────────────────
        plan_pos   = plan_hero.get("positioning", "")
        layout_pos = hero.get("positioning", "")
        if plan_pos and layout_pos and plan_pos != layout_pos:
            violations.append(_Violation(
                message=(
                    f"Positionnement hero ne correspond pas au plan : "
                    f"plan='{plan_pos}', layout='{layout_pos}'"
                ),
                severity=SEVERITY_MEDIUM,
                is_hard=False,
            ))

        # ── 5. Correspondance hero.text_placement ──────────────────────────
        plan_tp   = plan_hero.get("text_placement", "")
        layout_tp = hero.get("text_placement", "")
        if plan_tp and layout_tp and plan_tp != layout_tp:
            violations.append(_Violation(
                message=(
                    f"Placement du texte hero ne correspond pas : "
                    f"plan='{plan_tp}', layout='{layout_tp}'"
                ),
                severity=SEVERITY_MINOR,
                is_hard=False,
            ))

        # ── 6. Détection des répétitions de layout ─────────────────────────
        repeated = structure.get("repeated_layouts", {})
        if not repeated:
            # Calculé depuis les sections si non fourni
            variant_counts = Counter(
                s.get("layout_variant", "")
                for s in sections
                if s.get("layout_variant", "")
            )
            repeated = {v: c for v, c in variant_counts.items() if c > MAX_SECTION_REPETITION}

        for variant, count in repeated.items():
            if count > MAX_SECTION_REPETITION:
                violations.append(_Violation(
                    message=(
                        f"Layout '{variant}' répété {count}× "
                        f"(maximum autorisé : {MAX_SECTION_REPETITION})"
                    ),
                    severity=SEVERITY_MAJOR,
                    is_hard=True,
                ))

        # ── 7. Symétrie globale interdite ──────────────────────────────────
        if structure.get("global_symmetry", False):
            symmetry_forbidden = {"symmetrical_column_layout", "centered_hero"} & set(forbidden)
            if symmetry_forbidden:
                violations.append(_Violation(
                    message=(
                        f"Symétrie globale détectée mais interdite par le plan "
                        f"({', '.join(sorted(symmetry_forbidden))})"
                    ),
                    severity=SEVERITY_MAJOR,
                    is_hard=True,
                ))

        # ── 8. Nombre de sections ──────────────────────────────────────────
        plan_section_types = design_plan.get("section_types", [])
        if plan_section_types and len(sections) < 3:
            violations.append(_Violation(
                message=(
                    f"Trop peu de sections : {len(sections)} "
                    f"(minimum 3 attendu selon le plan)"
                ),
                severity=SEVERITY_MEDIUM,
                is_hard=False,
            ))

        # ── 9. Présence du bloc CTA ────────────────────────────────────────
        if plan_section_types and "cta_block" in plan_section_types:
            cta_present = any(s.get("type") == "cta_block" for s in sections)
            if not cta_present:
                violations.append(_Violation(
                    message="Bloc CTA absent du layout (requis par le plan)",
                    severity=SEVERITY_MAJOR,
                    is_hard=True,
                ))

        # ── 10. Cohérence de densité ───────────────────────────────────────
        plan_density   = design_plan.get("composition", {}).get("density", "")
        layout_density = structure.get("density", "")
        if plan_density and layout_density and plan_density != layout_density:
            violations.append(_Violation(
                message=(
                    f"Densité incompatible avec le plan : "
                    f"plan='{plan_density}', layout='{layout_density}'"
                ),
                severity=SEVERITY_MINOR,
                is_hard=False,
            ))

        # ── Calcul du score et du verdict ──────────────────────────────────
        deduction = sum(v.severity for v in violations)
        score     = max(0, 100 - deduction)
        has_hard  = any(v.is_hard for v in violations)
        valid     = (score >= PASS_THRESHOLD) and (not has_hard)

        fail_reasons = [v.message for v in violations if v.is_hard or v.severity >= SEVERITY_MAJOR]
        warnings     = [v.message for v in violations if not v.is_hard and v.severity < SEVERITY_MAJOR]

        return ValidationResult(
            valid=valid,
            score=score,
            fail_reasons=fail_reasons,
            warnings=warnings,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Fonction utilitaire
# ─────────────────────────────────────────────────────────────────────────────

def validate_layout(design_plan: dict, layout: dict) -> ValidationResult:
    """
    Crée un DesignValidator et exécute la validation.

    Args:
        design_plan : dict issu de DesignPlan.to_dict()
        layout      : structure du layout rendu

    Returns:
        ValidationResult(valid, score, fail_reasons, warnings)
    """
    return DesignValidator().validate(design_plan, layout)
