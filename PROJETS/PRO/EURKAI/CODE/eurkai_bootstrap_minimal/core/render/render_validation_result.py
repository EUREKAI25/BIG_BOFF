"""Minimal render function for validation output."""


def render_validation_result(result: dict, scenario: dict, catalog: dict) -> dict:
    upstream = result.get("upstream_result", {})
    return {
        "scenario_ident": scenario.get("ident"),
        "status": result.get("status"),
        "expected": result.get("expected"),
        "actual": result.get("actual"),
        "object_ident": upstream.get("object_ident"),
        "schema_ident": upstream.get("schema_ident"),
        "score": upstream.get("score"),
        "tested_rule_count": upstream.get("tested_rule_count"),
        "success_count": upstream.get("success_count"),
        "failure_count": upstream.get("failure_count"),
        "failure_list": upstream.get("failure_list"),
    }
