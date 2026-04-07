"""
validate_object_vs_schema
Valide un objet dict contre un schema du catalog.
Retourne un résultat structuré avec score, failures, warnings.
"""

import re


def _eval_condition(condition, obj):
    """Évalue une condition FORMULAS sur un objet dict."""
    if not condition:
        return True, "no_condition"
    try:
        c = condition.strip()

        if c.startswith("AND("):
            parts = _split_args(c[4:-1])
            results = [_eval_condition(p.strip(), obj) for p in parts]
            ok = all(r[0] for r in results)
            return ok, f"AND({', '.join(r[1] for r in results)})"

        if c.startswith("OR("):
            parts = _split_args(c[3:-1])
            results = [_eval_condition(p.strip(), obj) for p in parts]
            ok = any(r[0] for r in results)
            return ok, f"OR({', '.join(r[1] for r in results)})"

        if c.startswith("EXISTS("):
            key = c[7:-1].strip().strip("'\"")
            ok = key in obj and obj[key] is not None
            return ok, f"EXISTS({key})={'ok' if ok else 'FAIL'}"

        if c.startswith("IS_NOT_EMPTY("):
            key = c[13:-1].strip().strip("'\"")
            v = obj.get(key)
            ok = v is not None and (len(v) > 0 if isinstance(v, (str, list, dict)) else True)
            return ok, f"IS_NOT_EMPTY({key})={'ok' if ok else 'FAIL'}"

        if c.startswith("IN("):
            parts = _split_args(c[3:-1])
            key = parts[0].strip().strip("'\"")
            import json as _json
            vals = _json.loads(parts[1].strip().replace("'", '"'))
            ok = obj.get(key) in vals
            return ok, f"IN({key})={'ok' if ok else 'FAIL'}"

        if c.startswith("STARTS_WITH("):
            parts = _split_args(c[12:-1])
            key = parts[0].strip().strip("'\"")
            prefix = parts[1].strip().strip("'\"")
            ok = isinstance(obj.get(key), str) and obj[key].startswith(prefix)
            return ok, f"STARTS_WITH({key})={'ok' if ok else 'FAIL'}"

        if c.startswith("ENDS_WITH("):
            parts = _split_args(c[10:-1])
            key = parts[0].strip().strip("'\"")
            suffix = parts[1].strip().strip("'\"")
            ok = isinstance(obj.get(key), str) and obj[key].endswith(suffix)
            return ok, f"ENDS_WITH({key})={'ok' if ok else 'FAIL'}"

        if c.startswith("MATCHES_REGEX("):
            parts = _split_args(c[14:-1])
            key = parts[0].strip().strip("'\"")
            pattern = parts[1].strip().strip("'\"")
            ok = isinstance(obj.get(key), str) and bool(re.match(pattern, obj[key]))
            return ok, f"MATCHES_REGEX({key})={'ok' if ok else 'FAIL'}"

        return True, f"unsupported:{c[:40]}"

    except Exception as e:
        return False, f"eval_error:{str(e)[:60]}"


def _split_args(s):
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


def validate_object_vs_schema(obj, schema):
    """
    Valide obj contre schema.
    Retourne : { success, score, tested, failure_count, warning_count, failures, warnings }
    """
    failures, warnings, tested = [], [], 0

    for field, rule in schema.get("schema_required_element_list", {}).items():
        tested += 1
        condition = rule.get("rule_condition") if isinstance(rule, dict) else None
        ok, detail = _eval_condition(condition, obj) if condition else (field in obj, f"EXISTS({field})")
        if not ok:
            failures.append({"field": field, "detail": detail, "type": "required"})

    for rule_ident, rule in schema.get("schema_validation_rule_list", {}).items():
        tested += 1
        condition = rule.get("rule_condition") if isinstance(rule, dict) else None
        severity  = rule.get("rule_severity", "error") if isinstance(rule, dict) else "error"
        ok, detail = _eval_condition(condition, obj) if condition else (True, "no_condition")
        if not ok:
            entry = {"rule": rule_ident, "detail": detail, "severity": severity}
            if severity == "error":
                failures.append(entry)
            else:
                warnings.append(entry)

    return {
        "success":       len(failures) == 0,
        "score":         round(100 * (tested - len(failures)) / tested) if tested else 100,
        "tested":        tested,
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "failures":      failures,
        "warnings":      warnings,
    }
