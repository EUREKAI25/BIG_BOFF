import json
from pathlib import Path
import sys

REQUIRED_LIST_KEYS = [
    "attributelist","rulelist","methodlist","relationlist","optionlist","elementlist",
    "inheritedlist","ownedlist","injectedlist"
]

def validate(obj, path_label="(root)"):
    errors = []
    for k in REQUIRED_LIST_KEYS:
        if k not in obj:
            errors.append(f"missing key: {k} at {path_label}")
        elif not isinstance(obj[k], list):
            errors.append(f"key not list: {k} at {path_label} (got {type(obj[k]).__name__})")
    el = obj.get("elementlist")
    if isinstance(el, list):
        for i, child in enumerate(el):
            if isinstance(child, dict):
                errors.extend(validate(child, f"{path_label}.elementlist[{i}]"))
    return errors

def main():
    if len(sys.argv) < 2:
        print("usage: validator_fractal_lists_required.py <json_file>")
        return 2
    p = Path(sys.argv[1]).expanduser().resolve()
    d = json.loads(p.read_text(encoding="utf-8"))
    errs = validate(d, p.name)
    if errs:
        print("VALIDATION: FAIL")
        for e in errs:
            print(" -", e)
        return 1
    print("VALIDATION: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
