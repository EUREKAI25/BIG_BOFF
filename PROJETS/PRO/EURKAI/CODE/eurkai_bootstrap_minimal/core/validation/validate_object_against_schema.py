def resolve_path_exists(obj, dotted_path):
    current = obj
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True

def validate_object_against_schema(obj, catalog):
    from core.registry.function_registry import FUNCTION_REGISTRY

    schema_ident = obj.get("schema")
    schema = catalog["schema_list"].get(schema_ident)

    if not schema:
        return {
            "success": False,
            "status": "failure",
            "object_ident": obj.get("ident"),
            "schema_ident": schema_ident,
            "tested_rule_count": 1,
            "success_count": 0,
            "failure_count": 1,
            "score": 0,
            "failure_list": ["unknown_schema"],
        }

    tested_rule_count = 0
    success_count = 0
    failure_list = []

    for element_name in schema.get("required_element_list", {}).keys():
        tested_rule_count += 1
        if resolve_path_exists(obj, element_name):
            success_count += 1
        else:
            failure_list.append(f"missing_required_element:{element_name}")

    for rule_ident, rule in schema.get("validation_rule_list", {}).items():
        tested_rule_count += 1
        how_ident = rule.get("how")
        how_fn = FUNCTION_REGISTRY.get(how_ident)

        if how_fn is None:
            failure_list.append(f"unknown_rule_method:{how_ident}")
            continue

        rule_result = how_fn(obj=obj, schema=schema, rule=rule, catalog=catalog)

        if rule_result.get("success"):
            success_count += 1
        else:
            failure_list.append(rule_ident)

    failure_count = tested_rule_count - success_count
    score = 100 if tested_rule_count == 0 else int((success_count / tested_rule_count) * 100)

    return {
        "success": failure_count == 0,
        "status": "success" if failure_count == 0 else "failure",
        "object_ident": obj.get("ident"),
        "schema_ident": schema_ident,
        "tested_rule_count": tested_rule_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "score": score,
        "failure_list": failure_list,
    }
