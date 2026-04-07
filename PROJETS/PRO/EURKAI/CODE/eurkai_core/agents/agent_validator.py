"""
agent_validator
Valide la cohérence entre un objet EURKAI enrichi et le code généré.
Logique déterministe — zéro dépendance externe.

Checks :
  1. code non vide
  2. type cohérent (def / class présent)
  3. inputs dans signature ou commentaires
  4. return présent si outputs définis
  5. structure minimale respectée
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Poids des checks pour le score final (total = 100)
_WEIGHTS = {
    "code_not_empty":    25,
    "type_coherent":     25,
    "inputs_present":    20,
    "return_present":    20,
    "structure_minimal": 10,
}


def run(obj, code, context=None, verbose=True, agent_ident="agent_validator"):
    """
    Valide la cohérence objet / code.

    obj     : dict — objet EURKAI enrichi (sortie architect)
    code    : str  — code généré
    context : dict — infos additionnelles (optionnel)

    Retourne :
        status   — "success" | "failure"
        score    — 0–100
        issues   — liste de problèmes bloquants
        warnings — liste de problèmes non bloquants
    """
    obj     = obj or {}
    code    = code or ""
    issues  = []
    warnings = []
    score   = 0

    object_type = obj.get("type") or obj.get("object_type") or "function"
    ident       = obj.get("ident") or obj.get("object_ident") or ""
    inputs      = obj.get("inputs") or obj.get("attributes") or {}
    outputs     = obj.get("outputs") or {}

    # ── Check 1 — code non vide ───────────────────────────────────────────────
    if _check_code_not_empty(code):
        score += _WEIGHTS["code_not_empty"]
    else:
        issues.append({"check": "code_not_empty", "detail": "code vide ou None"})

    # ── Check 2 — type cohérent ───────────────────────────────────────────────
    ok2, issue2, warn2 = _check_type_coherent(object_type, ident, code)
    if ok2:
        score += _WEIGHTS["type_coherent"]
    else:
        issues.append(issue2)
    warnings.extend(warn2)

    # ── Check 3 — inputs dans le code ─────────────────────────────────────────
    ok3, warn3 = _check_inputs_present(inputs, code, object_type)
    if ok3:
        score += _WEIGHTS["inputs_present"]
    else:
        warnings.extend(warn3)   # non bloquant si inputs absents du code

    # ── Check 4 — return présent si outputs définis ───────────────────────────
    ok4, issue4 = _check_return_present(outputs, code, object_type)
    if ok4:
        score += _WEIGHTS["return_present"]
    else:
        issues.append(issue4)

    # ── Check 5 — structure minimale ──────────────────────────────────────────
    ok5, warn5 = _check_structure_minimal(object_type, code)
    if ok5:
        score += _WEIGHTS["structure_minimal"]
    else:
        warnings.extend(warn5)

    status = "success" if not issues else "failure"

    if verbose:
        print(f"  [agent]   {agent_ident} — {object_type}:{ident} score:{score}/100")
        if issues:
            for i in issues:
                print(f"  [ISSUE]   {i['check']} : {i['detail']}")
        if warnings:
            for w in warnings:
                print(f"  [WARN]    {w}")

    return {
        "status":   status,
        "score":    score,
        "issues":   issues,
        "warnings": warnings,
    }


# ── Checks ────────────────────────────────────────────────────────────────────

def _check_code_not_empty(code):
    return bool(code and code.strip())


def _check_type_coherent(object_type, ident, code):
    issues   = []
    warnings = []

    if object_type in ("function",):
        if not re.search(r"^\s*def\s+\w+", code, re.MULTILINE):
            return False, {"check": "type_coherent",
                           "detail": f"function attendue mais aucun 'def' trouvé"}, []
        if ident and not re.search(rf"\bdef\s+{re.escape(ident)}\b", code):
            warnings.append(f"def présent mais nom '{ident}' absent — nom différent généré")

    elif object_type == "class":
        if not re.search(r"^\s*class\s+\w+", code, re.MULTILINE):
            return False, {"check": "type_coherent",
                           "detail": "class attendue mais aucune 'class' trouvée"}, []

    elif object_type == "module":
        if not re.search(r"^\s*def\s+run\b", code, re.MULTILINE):
            warnings.append("module sans fonction 'run()' — point d'entrée manquant")

    elif object_type == "scenario":
        has_class = re.search(r"^\s*class\s+\w+", code, re.MULTILINE)
        has_run   = re.search(r"^\s*def\s+run\b", code, re.MULTILINE)
        if not has_class and not has_run:
            warnings.append("scenario sans class ni run() — structure attendue absente")

    return True, None, warnings


def _check_inputs_present(inputs, code, object_type):
    if not inputs:
        return True, []   # pas d'inputs définis → check non applicable

    # Pour function : chercher dans la signature
    if object_type == "function":
        sig_match = re.search(r"def\s+\w+\((.*?)\)", code, re.DOTALL)
        sig       = sig_match.group(1) if sig_match else ""
        missing   = [k for k in inputs if k not in sig and f"# {k}" not in code]
    else:
        # Pour class/module : chercher dans __init__ ou commentaires
        missing = [k for k in inputs
                   if k not in code and f"self.{k}" not in code]

    if missing:
        return False, [f"input '{k}' absent du code" for k in missing]
    return True, []


def _check_return_present(outputs, code, object_type):
    if not outputs or object_type in ("page",):
        return True, None   # pas d'outputs ou type non applicable

    if object_type in ("function", "module", "scenario"):
        if not re.search(r"^\s*return\b", code, re.MULTILINE):
            return False, {"check": "return_present",
                           "detail": "outputs définis mais aucun 'return' trouvé"}
    return True, None


def _check_structure_minimal(object_type, code):
    warnings = []

    if object_type == "class":
        if not re.search(r"def\s+__init__\b", code):
            warnings.append("class sans __init__")
        if not re.search(r"def\s+validate\b", code):
            warnings.append("class sans validate()")

    if object_type == "function":
        lines = [l for l in code.splitlines() if l.strip() and not l.strip().startswith("#")]
        body  = [l for l in lines if not l.startswith("def ") and '"""' not in l and "'''" not in l]
        if len(body) <= 1:
            warnings.append("fonction avec corps quasi-vide (seulement pass/return)")

    return (len(warnings) == 0), warnings


# ── Smoke test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cases = [
        {
            "label": "✓ Function VAT valide",
            "obj":   {"type": "function", "ident": "calculate_vat",
                      "inputs": {"price": "float", "rate": "float"},
                      "outputs": {"amount_ttc": "float"}},
            "code":  "def calculate_vat(price, rate):\n    # price: float\n    # rate: float\n    return price * (1 + rate)\n",
        },
        {
            "label": "✗ Code vide",
            "obj":   {"type": "function", "ident": "foo", "inputs": {}, "outputs": {}},
            "code":  "",
        },
        {
            "label": "✗ Function sans def",
            "obj":   {"type": "function", "ident": "add", "inputs": {}, "outputs": {"result": "float"}},
            "code":  "result = a + b\nreturn result\n",
        },
        {
            "label": "✗ Outputs sans return",
            "obj":   {"type": "function", "ident": "compute",
                      "inputs": {"x": "float"},
                      "outputs": {"result": "float"}},
            "code":  "def compute(x):\n    y = x * 2\n",
        },
        {
            "label": "~ Class partielle (warnings)",
            "obj":   {"type": "class", "ident": "UserProfile",
                      "inputs": {"name": "str"}, "outputs": {}},
            "code":  "class UserProfile:\n    def __init__(self, name=None):\n        self.name = name\n",
        },
        {
            "label": "✓ Module avec run()",
            "obj":   {"type": "module", "ident": "email_sender",
                      "inputs": {}, "outputs": {"success": "bool"}},
            "code":  "def run(params):\n    return {'success': True}\n",
        },
    ]

    print("=" * 60)
    print("  agent_validator — smoke test")
    print("=" * 60)

    passed = failed = 0
    for case in cases:
        r = run(case["obj"], case["code"], verbose=False)
        ok = r["status"] == "success"
        print(f"\n{case['label']}")
        print(f"  status : {r['status']}   score : {r['score']}/100")
        if r["issues"]:
            for i in r["issues"]:
                print(f"  issue  : {i['check']} — {i['detail']}")
        if r["warnings"]:
            for w in r["warnings"]:
                print(f"  warn   : {w}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  {passed}/{passed + failed} success (les failures sont attendues)")
    print("=" * 60)
