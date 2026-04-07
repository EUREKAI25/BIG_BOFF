"""Utility to resolve dotted paths inside nested dicts."""


def resolve_path_exists(obj: dict, dotted_path: str) -> bool:
    current = obj
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True
