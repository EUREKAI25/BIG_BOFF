"""Minimal validation rule: object references the expected schema."""


def rule_has_schema_reference(obj: dict, schema: dict, rule: dict, catalog: dict) -> dict:
    expected_schema = rule.get("params", {}).get("expected_schema_ident")
    actual_schema = obj.get("schema")
    ok = expected_schema == actual_schema
    return {
        "success": ok,
        "status": "success" if ok else "failure",
        "rule_ident": rule.get("ident"),
        "expected_schema_ident": expected_schema,
        "actual_schema_ident": actual_schema,
    }
