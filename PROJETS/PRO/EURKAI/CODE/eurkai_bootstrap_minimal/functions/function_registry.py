from core.validation.filter_has_schema import filter_has_schema
from core.utils.resolve_how import resolve_how
from core.validation.validate_object_against_schema import validate_object_against_schema
from core.validation.rule_has_schema_reference import rule_has_schema_reference
from core.validation.validate_attending_result import validate_attending_result
from core.render.render_validation_result import render_validation_result
from core.hooks.print_success import print_success
from core.hooks.schema_validate_failurehook_print import schema_validate_failurehook_print

FUNCTION_REGISTRY = {
    "filter_has_schema": filter_has_schema,
    "resolve_how": resolve_how,
    "validate_object_against_schema": validate_object_against_schema,
    "rule_has_schema_reference": rule_has_schema_reference,
    "validate_attending_result": validate_attending_result,
    "render_validation_result": render_validation_result,
    "print_success": print_success,
    "schema_validate_failurehook_print": schema_validate_failurehook_print,
}
