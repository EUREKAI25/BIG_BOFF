"""
scenario_debug_validate — itération 2
Valide catalog_core.json contre ses propres schémas.
Produit un rapport de validation + entrées History.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

CATALOG_PATH = Path(__file__).parent.parent / "catalog" / "catalog_core.json"
OUTPUT_PATH  = Path(__file__).parent.parent / "output" / "validation_report.json"

# ─────────────────────────────────────────────
# FORMULAS — implémentation minimale
# ─────────────────────────────────────────────

def formula_exists(obj, key):
    return key in obj and obj[key] is not None

def formula_is_not_empty(obj, key):
    v = obj.get(key)
    if v is None: return False
    if isinstance(v, (str, list, dict)): return len(v) > 0
    return True

def formula_in(obj, key, values):
    return obj.get(key) in values

def formula_starts_with(obj, key, prefix):
    v = obj.get(key, "")
    return isinstance(v, str) and v.startswith(prefix)

def formula_ends_with(obj, key, suffix):
    v = obj.get(key, "")
    return isinstance(v, str) and v.endswith(suffix)

def formula_matches_regex(obj, key, pattern):
    v = obj.get(key, "")
    return isinstance(v, str) and bool(re.match(pattern, v))

def formula_typeof(obj, key, expected_type):
    v = obj.get(key)
    type_map = {"string": str, "int": int, "bool": bool,
                "list": list, "dict": dict, "number": (int, float)}
    t = type_map.get(expected_type)
    return isinstance(v, t) if t else False

# ─────────────────────────────────────────────
# ÉVALUATEUR DE CONDITIONS (FORMULAS → bool)
# ─────────────────────────────────────────────

def eval_condition(condition, obj):
    """Évalue une condition FORMULAS sur un objet dict."""
    if not condition:
        return True, "no_condition"
    try:
        # Extraction simple des formules supportées
        c = condition.strip()

        # AND(a, b)
        if c.startswith("AND("):
            inner = c[4:-1]
            parts = split_args(inner)
            results = [eval_condition(p.strip(), obj) for p in parts]
            ok = all(r[0] for r in results)
            return ok, f"AND({', '.join(r[1] for r in results)})"

        # OR(a, b)
        if c.startswith("OR("):
            inner = c[3:-1]
            parts = split_args(inner)
            results = [eval_condition(p.strip(), obj) for p in parts]
            ok = any(r[0] for r in results)
            return ok, f"OR({', '.join(r[1] for r in results)})"

        # EXISTS(key)
        if c.startswith("EXISTS("):
            key = c[7:-1].strip().strip("'\"")
            ok = formula_exists(obj, key)
            return ok, f"EXISTS({key})={'ok' if ok else 'FAIL'}"

        # IS_NOT_EMPTY(key)
        if c.startswith("IS_NOT_EMPTY("):
            key = c[13:-1].strip().strip("'\"")
            ok = formula_is_not_empty(obj, key)
            return ok, f"IS_NOT_EMPTY({key})={'ok' if ok else 'FAIL'}"

        # IN(key, [...])
        if c.startswith("IN("):
            inner = c[3:-1]
            parts = split_args(inner)
            key = parts[0].strip().strip("'\"")
            vals_str = parts[1].strip()
            vals = json.loads(vals_str.replace("'", '"'))
            ok = formula_in(obj, key, vals)
            return ok, f"IN({key})={'ok' if ok else 'FAIL'}"

        # STARTS_WITH(key, prefix)
        if c.startswith("STARTS_WITH("):
            inner = c[12:-1]
            parts = split_args(inner)
            key = parts[0].strip().strip("'\"")
            prefix = parts[1].strip().strip("'\"")
            ok = formula_starts_with(obj, key, prefix)
            return ok, f"STARTS_WITH({key}, {prefix})={'ok' if ok else 'FAIL'}"

        # ENDS_WITH(key, suffix)
        if c.startswith("ENDS_WITH("):
            inner = c[10:-1]
            parts = split_args(inner)
            key = parts[0].strip().strip("'\"")
            suffix = parts[1].strip().strip("'\"")
            ok = formula_ends_with(obj, key, suffix)
            return ok, f"ENDS_WITH({key}, {suffix})={'ok' if ok else 'FAIL'}"

        # MATCHES_REGEX(key, pattern)
        if c.startswith("MATCHES_REGEX("):
            inner = c[14:-1]
            parts = split_args(inner)
            key = parts[0].strip().strip("'\"")
            pattern = parts[1].strip().strip("'\"")
            ok = formula_matches_regex(obj, key, pattern)
            return ok, f"MATCHES_REGEX({key})={'ok' if ok else 'FAIL'}"

        return True, f"unsupported_formula:{c[:40]}"

    except Exception as e:
        return False, f"eval_error:{str(e)[:60]}"


def split_args(s):
    """Découpe les arguments top-level d'une formule (gère les parenthèses imbriquées)."""
    args, depth, current = [], 0, ""
    for ch in s:
        if ch == "," and depth == 0:
            args.append(current)
            current = ""
        else:
            if ch in "([": depth += 1
            elif ch in ")]": depth -= 1
            current += ch
    if current:
        args.append(current)
    return args


# ─────────────────────────────────────────────
# VALIDATEUR object vs schema
# ─────────────────────────────────────────────

def validate_object_vs_schema(obj, schema, schema_ident):
    """Valide un objet contre un schema. Retourne un rapport."""
    failures = []
    warnings = []
    tested   = 0

    # 1. Required elements
    for field, rule in schema.get("schema_required_element_list", {}).items():
        tested += 1
        condition = rule.get("rule_condition")
        ok, detail = eval_condition(condition, obj) if condition else (field in obj, f"EXISTS({field})")
        if not ok:
            failures.append({"field": field, "detail": detail, "type": "required"})

    # 2. Validation rules
    for rule_ident, rule in schema.get("schema_validation_rule_list", {}).items():
        tested += 1
        condition = rule.get("rule_condition")
        severity  = rule.get("rule_severity", "error")
        ok, detail = eval_condition(condition, obj) if condition else (True, "no_condition")
        if not ok:
            entry = {"rule": rule_ident, "detail": detail, "severity": severity}
            if severity == "error":
                failures.append(entry)
            else:
                warnings.append(entry)

    return {
        "schema_ident":    schema_ident,
        "tested":          tested,
        "failure_count":   len(failures),
        "warning_count":   len(warnings),
        "success":         len(failures) == 0,
        "score":           round(100 * (tested - len(failures)) / tested) if tested else 100,
        "failures":        failures,
        "warnings":        warnings,
    }


# ─────────────────────────────────────────────
# HISTORY — enregistrement d'une action
# ─────────────────────────────────────────────

def make_history_entry(action, trigger, result, justification, status, agent="validate_catalog.py", scenario="scenario_debug_validate", object_ident=None):
    now = datetime.now(timezone.utc)
    return {
        "history_ident":         f"history_{now.strftime('%Y%m%d%H%M%S%f')}",
        "history_action":        action,
        "history_trigger":       trigger,
        "history_result":        result,
        "history_justification": justification,
        "history_timestamp":     now.isoformat(),
        "history_agent":         agent,
        "history_scenario":      scenario,
        "history_object_ident":  object_ident,
        "history_status":        status,
    }


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def run():
    print("=" * 60)
    print("scenario_debug_validate — catalog_core")
    print("=" * 60)

    with open(CATALOG_PATH) as f:
        catalog = json.load(f)

    schemas  = catalog.get("catalog_schema_list", {})
    objects  = catalog.get("catalog_object_list", {})
    models   = catalog.get("catalog_ai_model_list", {})

    report         = {"validation_results": [], "history_list": [], "summary": {}}
    total, passed  = 0, 0

    # Valider chaque objet du catalog contre ObjectSchema uniquement.
    # catalog_object_list contient des définitions de type (archetypes), pas des instances.
    # Les schemas spécifiques (SchemaSchema, RuleSchema...) s'appliquent aux instances.
    for obj_ident, obj in objects.items():
        schema_ident = "ObjectSchema"
        schema       = schemas.get(schema_ident)
        if not schema:
            print(f"  [SKIP] {obj_ident} — schema '{schema_ident}' introuvable")
            continue

        result = validate_object_vs_schema(obj, schema, schema_ident)
        result["object_ident"] = obj_ident
        report["validation_results"].append(result)
        total += 1

        status = "success" if result["success"] else "failure"
        if result["success"]:
            passed += 1
            print(f"  [OK]   {obj_ident} — score {result['score']}% ({result['tested']} règles)")
        else:
            print(f"  [FAIL] {obj_ident} — score {result['score']}% — {result['failure_count']} échec(s)")
            for f in result["failures"]:
                print(f"         ✗ {f.get('field', f.get('rule', '?'))} : {f['detail']}")
        if result["warnings"]:
            for w in result["warnings"]:
                print(f"         ⚠ {w.get('rule', '?')} : {w['detail']}")

        report["history_list"].append(make_history_entry(
            action       = f"validate_object_vs_schema:{obj_ident}",
            trigger      = "scenario_debug_validate",
            result       = f"score={result['score']}% failures={result['failure_count']}",
            justification= "Validation de conformité itération 2 — noyau catalog",
            status       = status,
            object_ident = obj_ident,
        ))

    # Valider les schémas entre eux (SchemaSchema)
    schema_schema = schemas.get("SchemaSchema")
    if schema_schema:
        print("\n  — Validation des schémas (SchemaSchema) —")
        for s_ident, schema in schemas.items():
            result = validate_object_vs_schema(schema, schema_schema, "SchemaSchema")
            result["object_ident"] = s_ident
            report["validation_results"].append(result)
            total += 1
            status = "success" if result["success"] else "failure"
            if result["success"]:
                passed += 1
                print(f"  [OK]   {s_ident}")
            else:
                print(f"  [FAIL] {s_ident} — {result['failure_count']} échec(s)")
                for f in result["failures"]:
                    print(f"         ✗ {f.get('field', f.get('rule', '?'))} : {f['detail']}")
            if result["warnings"]:
                for w in result["warnings"]:
                    print(f"         ⚠ {w.get('rule', '?')} : {w['detail']}")

            report["history_list"].append(make_history_entry(
                action       = f"validate_schema:{s_ident}",
                trigger      = "scenario_debug_validate",
                result       = f"score={result['score']}% failures={result['failure_count']}",
                justification= "Validation schéma contre SchemaSchema",
                status       = status,
                object_ident = s_ident,
            ))

    # Valider les AiModel contre AiModelSchema
    ai_schema = schemas.get("AiModelSchema")
    if ai_schema and models:
        print("\n  — Validation des AiModel —")
        for m_ident, model in models.items():
            result = validate_object_vs_schema(model, ai_schema, "AiModelSchema")
            result["object_ident"] = m_ident
            report["validation_results"].append(result)
            total += 1
            status = "success" if result["success"] else "failure"
            if result["success"]:
                passed += 1
                print(f"  [OK]   {m_ident}")
            else:
                print(f"  [FAIL] {m_ident} — {result['failure_count']} échec(s)")
                for f in result["failures"]:
                    print(f"         ✗ {f.get('field', f.get('rule', '?'))} : {f['detail']}")
            if result["warnings"]:
                for w in result["warnings"]:
                    print(f"         ⚠ {w.get('rule', '?')} : {w['detail']}")

    # Résumé
    report["summary"] = {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "score": round(100 * passed / total) if total else 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    print(f"\n{'=' * 60}")
    print(f"RÉSULTAT : {passed}/{total} — score global {report['summary']['score']}%")
    print(f"{'=' * 60}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Rapport + History → {OUTPUT_PATH}")

    return report["summary"]["score"] == 100


if __name__ == "__main__":
    import sys
    ok = run()
    sys.exit(0 if ok else 1)
