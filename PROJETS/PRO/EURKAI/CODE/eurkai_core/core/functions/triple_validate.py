"""
triple_validate — scenario_execution_modality
Triple validation configurable sur un objet généré par agent.
  Check 1 — Règles respectées  : validate_object_vs_schema (L1)
  Check 2 — Règles comprises   : champs significatifs, pas de valeurs vides/placeholder (L1+L2)
  Check 3 — Objectif atteint   : lineage + description correspondent à la demande (L1+L2+L3)
"""

from core.functions.validate_object_vs_schema import validate_object_vs_schema

PLACEHOLDER_VALUES = {"coming", "todo", "tbd", "none", "", "null", "undefined"}


def triple_validate(generated_object, schema, params, modality="L1+L2+L3"):
    """
    Applique les checks selon la modality demandée.
    modality : "L1" | "L1+L2" | "L1+L2+L3"
    Retourne : dict avec success, score, checks détaillés.
    """
    levels  = [l.strip() for l in modality.split("+")]
    checks  = {}
    success = True

    # --- L1 : structure (validate_object_vs_schema) ---
    if "L1" in levels:
        r = validate_object_vs_schema(generated_object, schema)
        checks["L1"] = {
            "label":   "Règles respectées (schema)",
            "success": r.get("success", False),
            "score":   r.get("score", 0),
            "details": r,
        }
        if not r.get("success"):
            success = False

    # --- L2 : sémantique (pas de valeurs vides/placeholder) ---
    if "L2" in levels:
        r2 = _check_semantic(generated_object)
        checks["L2"] = r2
        if not r2["success"]:
            success = False

    # --- L3 : objectif (lineage + description vs demande) ---
    if "L3" in levels:
        r3 = _check_goal(generated_object, params)
        checks["L3"] = r3
        if not r3["success"]:
            success = False

    overall_score = round(
        sum(c.get("score", 100) for c in checks.values()) / len(checks)
    ) if checks else 0

    return {
        "success":  success,
        "score":    overall_score,
        "modality": modality,
        "checks":   checks,
    }


def _check_semantic(obj):
    """L2 — vérifie que les champs sont significatifs (pas placeholder/vides)."""
    issues = []
    for key, value in obj.items():
        if isinstance(value, str) and value.strip().lower() in PLACEHOLDER_VALUES:
            issues.append(f"{key} = '{value}' (valeur placeholder)")
        if isinstance(value, str) and len(value.strip()) < 2 and key not in ("object_how",):
            issues.append(f"{key} trop court")

    return {
        "label":   "Règles comprises (sémantique)",
        "success": len(issues) == 0,
        "score":   max(0, 100 - len(issues) * 20),
        "issues":  issues,
    }


def _check_goal(obj, params):
    """L3 — vérifie que l'objet correspond à la demande (lineage + goal)."""
    issues = []
    requested_lineage = params.get("object_lineage", "")
    requested_goal    = params.get("object_goal", "")

    actual_lineage = obj.get("object_lineage", "")
    actual_desc    = obj.get("object_description", "")

    if requested_lineage and actual_lineage:
        if not actual_lineage.startswith(requested_lineage.split(":")[0]):
            issues.append(f"lineage '{actual_lineage}' ne correspond pas à '{requested_lineage}'")

    if requested_goal and actual_desc:
        # Vérification simple — au moins un mot-clé commun
        goal_words = set(requested_goal.lower().split())
        desc_words = set(actual_desc.lower().split())
        if not goal_words.intersection(desc_words) and len(goal_words) > 2:
            issues.append("description ne reflète pas l'objectif demandé")

    return {
        "label":   "Objectif atteint",
        "success": len(issues) == 0,
        "score":   100 if not issues else 50,
        "issues":  issues,
    }
