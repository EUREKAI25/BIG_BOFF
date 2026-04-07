"""Minimal failure hook for schema validation."""

from pprint import pprint


def schema_validate_failurehook_print(result: dict, scenario: dict, catalog: dict) -> None:
    print("\n[FAILUREHOOK] schema_validate a échoué")
    pprint(result)
