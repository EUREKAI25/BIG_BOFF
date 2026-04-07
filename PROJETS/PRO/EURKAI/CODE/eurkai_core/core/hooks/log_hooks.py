"""
log_success / log_failure — hooks conditionnels de la MRG.
"""


def log_success(context, catalog):
    obj   = context.get("object_ident", context.get("scenario_ident", "?"))
    score = context.get("validate_result", {}).get("score", 100)
    print(f"  [OK]   {obj} — score {score}%")
    return context


def log_failure(context, catalog):
    obj      = context.get("object_ident", context.get("scenario_ident", "?"))
    result   = context.get("validate_result", {})
    score    = result.get("score", 0)
    failures = result.get("failures", [])
    print(f"  [FAIL] {obj} — score {score}% — {len(failures)} échec(s)")
    for f in failures:
        label = f.get("field") or f.get("rule") or "?"
        print(f"         ✗ {label} : {f.get('detail', '')}")
    for w in result.get("warnings", []):
        print(f"         ⚠ {w.get('rule', '?')} : {w.get('detail', '')}")
    return context
