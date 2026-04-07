"""
render_validator — Validation du contrat de rendu.

validate_render_contract(html, plan_dict) → (bool, list[str])

Vérifie que le HTML produit par render_strict respecte exactement le DesignPlan :
- data-layout-strategy sur <body> correspond à plan["layout_strategy"]
- data-hero-type sur <body> correspond à plan["hero_type"]
- Nombre de sections = len(plan["section_types"])
- Chaque section_type est présent exactement une fois dans l'ordre
- data-section-index suit 0..n-1

PAS d'import circulaire : aucun import de render_strict ici.
"""

from __future__ import annotations
import re


def validate_render_contract(html: str, plan: dict) -> tuple[bool, list[str]]:
    """
    Valide qu'un HTML rendu respecte le contrat du DesignPlan.

    Args:
        html : HTML complet produit par render_strict
        plan : dict avec layout_strategy, hero_type, section_types

    Returns:
        (ok: bool, errors: list[str])
        ok=True si aucune erreur, errors=[] si ok.
    """
    errors: list[str] = []

    if not html:
        return False, ["HTML vide"]

    layout_strategy = plan.get("layout_strategy", "")
    hero_type       = plan.get("hero_type", "")
    section_types   = plan.get("section_types", [])

    # ── 1. data-layout-strategy sur <body> ───────────────────────────────────
    body_match = re.search(r'<body\s[^>]*>', html, re.DOTALL)
    if not body_match:
        errors.append("Pas de <body> trouvé dans le HTML")
    else:
        body_tag = body_match.group(0)
        layout_in_html = _extract_attr(body_tag, "data-layout-strategy")
        if layout_in_html != layout_strategy:
            errors.append(
                f"data-layout-strategy: attendu={layout_strategy!r}, trouvé={layout_in_html!r}"
            )

        hero_in_html = _extract_attr(body_tag, "data-hero-type")
        if hero_in_html != hero_type:
            errors.append(
                f"data-hero-type: attendu={hero_type!r}, trouvé={hero_in_html!r}"
            )

    # ── 2. Sections présentes et dans l'ordre ─────────────────────────────────
    # Extrait tous les data-section-type dans l'ordre d'apparition
    found_types = re.findall(r'data-section-type="([^"]+)"', html)

    if len(found_types) != len(section_types):
        errors.append(
            f"Nombre de sections: attendu={len(section_types)}, trouvé={len(found_types)} "
            f"(trouvé: {found_types})"
        )
    else:
        for i, (expected, actual) in enumerate(zip(section_types, found_types)):
            if expected != actual:
                errors.append(
                    f"Section[{i}]: attendu={expected!r}, trouvé={actual!r}"
                )

    # ── 3. data-section-index séquentiels ─────────────────────────────────────
    found_indices = [int(m) for m in re.findall(r'data-section-index="(\d+)"', html)]
    expected_indices = list(range(len(section_types)))

    if found_indices != expected_indices:
        errors.append(
            f"data-section-index: attendu={expected_indices}, trouvé={found_indices}"
        )

    # ── 4. Section hero présente et data-hero-type cohérent ───────────────────
    hero_section_match = re.search(r'data-section-type="hero"[^>]*data-hero-type="([^"]+)"', html)
    if not hero_section_match:
        # Try alternate attribute order
        hero_section_match = re.search(r'data-hero-type="([^"]+)"[^>]*data-section-type="hero"', html)

    if "hero" in section_types:
        # Find the hero section element
        hero_elem_match = re.search(
            r'<section[^>]*data-section-type="hero"[^>]*data-hero-type="([^"]+)"',
            html
        )
        if not hero_elem_match:
            hero_elem_match = re.search(
                r'<section[^>]*data-hero-type="([^"]+)"[^>]*data-section-type="hero"',
                html
            )
        if hero_elem_match:
            hero_type_in_section = hero_elem_match.group(1)
            if hero_type_in_section != hero_type:
                errors.append(
                    f"Section hero data-hero-type: attendu={hero_type!r}, trouvé={hero_type_in_section!r}"
                )
        else:
            errors.append("Section hero sans data-hero-type")

    # ── 5. HTML minimal valide ────────────────────────────────────────────────
    if "<html" not in html:
        errors.append("Tag <html> manquant")
    if "</html>" not in html:
        errors.append("Tag </html> manquant")
    if "<head>" not in html and "<head " not in html:
        errors.append("Tag <head> manquant")
    if "<main>" not in html:
        errors.append("Tag <main> manquant")

    return (len(errors) == 0), errors


# ─── Helper ───────────────────────────────────────────────────────────────────

def _extract_attr(tag: str, attr_name: str) -> str:
    """Extrait la valeur d'un attribut HTML depuis un tag string."""
    m = re.search(rf'{re.escape(attr_name)}="([^"]*)"', tag)
    return m.group(1) if m else ""
