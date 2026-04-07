"""
test_e2e_minimal.py
Prouve que la chaîne EURKAI tourne sans intervention humaine.

Flow nominal  : input → scenario_orchestrate → agent_generate_code → output
Flow fix loop : generate → code cassé → agent_debug_fix → code corrigé → output

Exécution : python tests/test_e2e_minimal.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scenarios.scenario_orchestrate import run as orchestrate
from agents.agent_generate_code     import run as generate_code
from agents.agent_debug_fix         import run as debug_fix


# ── Catalog minimal (sans LLM) ─────────────────────────────────────────────────
_CATALOG = {"_storage": None}


# ── Cas nominaux ───────────────────────────────────────────────────────────────

CASES = [
    {
        "label":  "Function : additionne deux nombres",
        "schema": "add_numbers",
        "params": {
            "object_type":    "function",
            "object_lineage": "Object:add_numbers",
            "object_goal":    "Additionne deux nombres et retourne le résultat.",
            "attributes":     {"a": "float", "b": "float"},
        },
    },
    {
        "label":  "Class : profil utilisateur",
        "schema": "UserProfile",
        "params": {
            "object_type":    "class",
            "object_lineage": "Object:UserProfile",
            "object_goal":    "Représente un profil utilisateur avec nom et email.",
            "attributes":     {"name": "str", "email": "str"},
        },
    },
    {
        "label":  "Module : calcul TVA",
        "schema": "tva_calculator",
        "params": {
            "object_type":    "module",
            "object_lineage": "Object:tva_calculator",
            "object_goal":    "Calcule le montant TTC depuis un prix HT et un taux TVA.",
        },
    },
    {
        "label":  "Scenario : orchestration paiement",
        "schema": "CheckoutScenario",
        "params": {
            "object_type":    "scenario",
            "object_lineage": "Object:CheckoutScenario",
            "object_goal":    "Orchestration du tunnel de paiement.",
        },
    },
]


# ── Cas fix loop : generate → casser → fix ─────────────────────────────────────

def _break_code(code, break_type):
    """Casse volontairement du code valide pour forcer le passage par debug_fix."""
    if break_type == "remove_return":
        # Supprimer toutes les lignes `return`
        lines = [l for l in code.splitlines() if "return" not in l]
        return "\n".join(lines)

    if break_type == "bad_indent":
        # Supprimer toute l'indentation du corps → IndentationError garanti
        lines = code.splitlines()
        out   = []
        in_body = False
        for line in lines:
            if line.startswith("def ") or line.startswith("class "):
                in_body = True
                out.append(line)
            elif in_body and line.startswith("    "):
                out.append(line.lstrip())  # colonne 0 → IndentationError
            else:
                out.append(line)
        return "\n".join(out)

    if break_type == "incomplete_body":
        # Fonction standalone vide — garanti de casser ast.parse
        return "def incomplete_stub():\n"

    return code


FIX_CASES = [
    {
        "label":      "Fix loop — return manquant",
        "object_type": "function",
        "goal":       "Calcule la moyenne d'une liste.",
        "attributes": {"values": "list"},
        "break_type": "remove_return",
        "expect_fix": "fix_missing_return",
    },
    {
        "label":      "Fix loop — indentation cassée",
        "object_type": "function",
        "goal":       "Convertit Celsius en Fahrenheit.",
        "attributes": {"celsius": "float"},
        "break_type": "bad_indent",
        "expect_fix": "fix_indentation",
    },
    {
        "label":      "Fix loop — corps de fonction vide",
        "object_type": "module",
        "goal":       "Génère un identifiant unique.",
        "attributes": {},
        "break_type": "incomplete_body",
        "expect_fix": "fix_incomplete_function",
    },
]


# ── Runners ────────────────────────────────────────────────────────────────────

def run_nominal(case):
    t0 = time.perf_counter()
    result = orchestrate(
        case["schema"], case["params"],
        catalog=_CATALOG, model_type="deterministic", verbose=False,
    )
    return result, time.perf_counter() - t0


def run_fix_loop(case):
    """
    1. Génère du code valide avec agent_generate_code
    2. Le casse volontairement
    3. Passe par agent_debug_fix
    4. Retourne résultat enrichi avec trace
    """
    t0 = time.perf_counter()

    schema = case["goal"].lower().replace(" ", "_")[:20]
    gen = generate_code(
        schema,
        {"object_type": case["object_type"], "goal": case["goal"],
         "attributes": case["attributes"]},
        _CATALOG, model_type="deterministic", verbose=False,
    )
    original_code = gen.get("code", "")
    broken_code   = _break_code(original_code, case["break_type"])

    fix = debug_fix(broken_code, error=case["break_type"], verbose=False)

    elapsed = time.perf_counter() - t0
    return {
        "original_code": original_code,
        "broken_code":   broken_code,
        "fix_result":    fix,
        "elapsed":       elapsed,
    }


# ── Affichage ──────────────────────────────────────────────────────────────────

def print_nominal(case, result, elapsed):
    ok = result["status"] in ("success", "partial") and bool(result.get("code"))
    print(f"\n{'✓' if ok else '✗'} {case['label']}")
    print(f"  STATUS : {result['status']}")
    print(f"  FILE   : {result.get('filename', '—')}")
    print(f"  TIME   : {elapsed * 1000:.1f}ms")
    if result.get("warnings"):
        for w in result["warnings"]:
            print(f"  WARN   : {w}")
    code = result.get("code", "")
    if code:
        print("  CODE   :")
        for line in code.splitlines():
            print(f"    {line}")
    return ok


def print_fix_loop(case, data):
    fix    = data["fix_result"]
    ok     = fix.get("status") == "success"
    expect = case["expect_fix"]
    hit    = fix.get("fix_applied") == expect

    print(f"\n{'✓' if ok else '✗'} {case['label']}")
    print(f"  BREAK  : {case['break_type']}")
    print(f"  STATUS : {fix.get('status')}")
    print(f"  FIX    : {fix.get('fix_applied')}  {'✓ attendu' if hit else f'⚠ attendu={expect}'}")
    print(f"  CONF   : {fix.get('confidence')}")
    print(f"  TIME   : {data['elapsed'] * 1000:.1f}ms")
    print("  BROKEN CODE :")
    for line in data["broken_code"].splitlines()[:6]:
        print(f"    {line}")
    if fix.get("fixed_code"):
        print("  FIXED CODE  :")
        for line in fix["fixed_code"].splitlines():
            print(f"    {line}")
    return ok


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    passed = failed = 0
    total_t = 0.0

    # ── Partie 1 : cas nominaux ───────────────────────────────────────────────
    print("=" * 60)
    print("  EURKAI — test e2e minimal")
    print("  Partie 1 : chaîne nominale")
    print("=" * 60)

    for case in CASES:
        try:
            result, elapsed = run_nominal(case)
            total_t += elapsed
            ok = print_nominal(case, result, elapsed)
            if ok:
                passed += 1
            else:
                failed += 1
        except Exception as exc:
            failed += 1
            print(f"\n✗ {case['label']}\n  ERROR : {exc}")

    # ── Partie 2 : fix loop ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Partie 2 : fix loop — generate → casser → fix")
    print("=" * 60)

    for case in FIX_CASES:
        try:
            data = run_fix_loop(case)
            total_t += data["elapsed"]
            ok = print_fix_loop(case, data)
            if ok:
                passed += 1
            else:
                failed += 1
        except Exception as exc:
            failed += 1
            print(f"\n✗ {case['label']}\n  ERROR : {exc}")

    print("\n" + "=" * 60)
    print(f"  {passed}/{passed + failed} cas OK — {total_t * 1000:.0f}ms total")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
