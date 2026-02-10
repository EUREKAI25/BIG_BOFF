import json
import sys
from pathlib import Path

REQUIRED_FRACTAL_KEYS = ("inheritedlist", "ownedlist", "injectedlist")

def _is_dict(x):
    return isinstance(x, dict)

def _has_fractal_lists(d):
    return all(k in d for k in REQUIRED_FRACTAL_KEYS)

def validate(obj, name="root"):
    errors = []

    def err(path, msg):
        errors.append(f"{path}: {msg}")

    def walk(x, path):
        if isinstance(x, dict):
            # Attribute rule (compat + canonical):
            # - legacy: Attribute.value may be a scalar
            # - canonical: Attribute.value is a dict that must contain its payload in Attribute.value.value
            if x.get("type") == "Attribute":
                if "value" not in x:
                    err(path, "Attribute missing 'value'")
                else:
                    v = x.get("value")
                    if isinstance(v, dict):
                        if "value" not in v:
                            err(path, "Attribute.value is dict but missing payload key 'value' (canonical is value.value)")
                        else:
                            # Optional typing (canon-aware, non-breaking):
                            vm = v.get("valuemode")
                            if vm is not None and vm not in ("bool", "value"):
                                err(path, "Attribute.value.valuemode must be 'bool' or 'value' when present")
                            if vm == "bool" and not isinstance(v.get("value"), bool):
                                err(path, "Attribute.value.valuemode='bool' requires Attribute.value.value to be boolean")

            # If these blocks exist, enforce your canonical structure
            if "xelementlist" in x:
                xl = x.get("xelementlist")
                if not isinstance(xl, dict):
                    err(path + ".xelementlist", "must be a dict")
                else:
                    if not _has_fractal_lists(xl):
                        err(path + ".xelementlist", "missing fractal lists (inheritedlist/ownedlist/injectedlist)")
                    if "value" not in xl:
                        err(path + ".xelementlist", "missing 'value' (primary embedded list reference)")

            if "injectionlist" in x:
                inj = x.get("injectionlist")
                if not isinstance(inj, dict):
                    err(path + ".injectionlist", "must be a dict")
                else:
                    for k in ("attributelist", "rulelist", "methodlist", "optionlist"):
                        if k not in inj:
                            err(path + ".injectionlist", f"missing '{k}'")

            if "treelist" in x:
                t = x.get("treelist")
                if not isinstance(t, dict):
                    err(path + ".treelist", "must be a dict")
                else:
                    for k in ("childlist", "parentlist", "siblinglist"):
                        if k not in t:
                            err(path + ".treelist", f"missing '{k}'")

            # continue walking
            for k, v in x.items():
                walk(v, path + "." + k)

        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")

    walk(obj, name)
    return errors

def main():
    if len(sys.argv) < 2:
        print("usage: validator_core_lists_v1.py <json_file>")
        return 2
    p = Path(sys.argv[1]).expanduser().resolve()
    d = json.loads(p.read_text(encoding="utf-8"))
    errs = validate(d, p.name)
    if errs:
        print("VALIDATION: FAIL")
        for e in errs:
            print("-", e)
        return 1
    print("VALIDATION: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
