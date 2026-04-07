import os

REPLACEMENTS = {
    "core.utils.resolve_how": "core.utils.resolve_how",
    "core.utils.resolve_path_exists": "core.utils.resolve_path_exists",
    "core.utils.run": "core.utils.run",
    "core.validation.filter_has_schema": "core.validation.filter_has_schema",
    "core.validation.rule_has_schema_reference": "core.validation.rule_has_schema_reference",
    "core.validation.validate": "core.validation.validate",
    "core.validation.validate_object_against_schema": "core.validation.validate_object_against_schema",
    "core.validation.validate_attending_result": "core.validation.validate_attending_result",
    "core.render.render_validation_result": "core.render.render_validation_result",
    "core.hooks.on_success": "core.hooks.on_success",
    "core.hooks.on_failure": "core.hooks.on_failure",
    "core.hooks.execute_named_hook": "core.hooks.execute_named_hook",
    "core.hooks.before": "core.hooks.before",
    "core.hooks.after": "core.hooks.after",
    "core.hooks.print_success": "core.hooks.print_success",
    "core.hooks.schema_validate_failurehook_print": "core.hooks.schema_validate_failurehook_print",
    "core.registry.function_registry": "core.registry.function_registry",
}

for root, _, files in os.walk("."):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r") as file:
                content = file.read()
            for old, new in REPLACEMENTS.items():
                content = content.replace(old, new)
            with open(path, "w") as file:
                file.write(content)

print("done")
