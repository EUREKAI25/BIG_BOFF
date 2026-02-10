import importlib
import os
import sys
import traceback
import inspect

PROJECT_NAME = "EURKAI"
CHANTIER_NAME = "METHODLIBRARY"
FUNCTION_NAME = "function_intake_execute"
MODULE_REL_PATH = "function_library_intake/function_intake_execute"

BASE_INPUT = "/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/_INPUTS/EURKAI"
MODULE_NAME = CHANTIER_NAME + "." + MODULE_REL_PATH.replace("/", ".")

def load_target():
    if BASE_INPUT not in sys.path:
        sys.path.insert(0, BASE_INPUT)
    try:
        mod = importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as e:
        raise FileNotFoundError(f"Target module not importable: {MODULE_NAME}: {e}")
    return mod

def run_test():
    try:
        mod = load_target()
        target = getattr(mod, FUNCTION_NAME)
        sig = inspect.signature(target)
        required_params = [
            p for p in sig.parameters.values()
            if p.default is p.empty
            and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        if required_params:
            status = "SKIPPED_NEEDS_ARGS"
            details = "Function requires positional arguments: " + ", ".join(
                p.name for p in required_params
            )
        else:
            result = target()
            status = "OK"
            details = f"Function returned: {result!r}"
    except Exception as e:
        status = "ERROR"
        details = "Exception during test:\n" + "".join(
            traceback.format_exception(type(e), e, e.__traceback__)
        )

    report_dir = os.path.dirname(__file__)
    report_path = os.path.join(report_dir, "validation_report.md")

    lines = [
        f"# Validation Report — {FUNCTION_NAME}",
        "",
        f"- Project: {PROJECT_NAME}",
        f"- Chantier: {CHANTIER_NAME}",
        f"- Function: {FUNCTION_NAME}",
        f"- Module: {MODULE_NAME}",
        f"- Status: {status}",
        "",
        "## Details",
        "",
        details,
        "",
    ]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[{FUNCTION_NAME}] status={status}")
    print(details)
    abs_report = os.path.abspath(report_path)
    print(f"file://{abs_report}")

if __name__ == "__main__":
    run_test()
