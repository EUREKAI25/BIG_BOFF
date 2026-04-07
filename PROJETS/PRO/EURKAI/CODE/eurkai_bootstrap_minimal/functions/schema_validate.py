from core.mrg import mrg

def schema_validate(catalog):
    context = {
        "scenario_ident": "schema_validate",
        "scenario": {
            "ident": "schema_validate",
            "hooks": {"on_success": "print_success"}
        },
        "object_ident": "Schema"
    }
    return mrg(context, catalog)
