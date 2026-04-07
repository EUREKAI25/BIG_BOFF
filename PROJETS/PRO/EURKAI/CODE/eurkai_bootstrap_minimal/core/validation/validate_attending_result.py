"""Minimal result validator."""


def validate_attending_result(result: dict, scenario: dict, catalog: dict) -> dict:
    attending_result = scenario.get("attending_result", {"success": True})
    expected_success = attending_result.get("success", True)
    actual_success = result.get("success", False)
    is_valid = actual_success == expected_success

    if not is_valid:
        failurehook_name = scenario.get("failurehook")
        if failurehook_name:
            failurehook = catalog["function_list"].get(failurehook_name)
            if failurehook:
                failurehook(result=result, scenario=scenario, catalog=catalog)

    return {
        "success": is_valid,
        "status": "success" if is_valid else "failure",
        "expected": attending_result,
        "actual": {"success": actual_success},
        "upstream_result": result,
    }
