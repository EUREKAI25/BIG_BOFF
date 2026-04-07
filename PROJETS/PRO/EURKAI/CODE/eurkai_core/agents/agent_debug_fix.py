"""
agent_debug_fix
Reçoit du code + une erreur, tente une correction déterministe.
Fallback LLM isolé disponible mais non utilisé par défaut.
"""

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run(code, error="", context=None, model_type="deterministic", verbose=True,
        agent_ident="agent_debug_fix"):
    """
    code       : str — code à corriger
    error      : str — message d'erreur (SyntaxError, IndentationError, etc.)
    context    : dict — infos additionnelles (object_type, goal…)
    model_type : "deterministic" | "llm" — llm activé uniquement si explicitement demandé

    Retourne :
        status      — "success" | "failure"
        fixed_code  — code corrigé (ou original si échec)
        fix_applied — description de la correction appliquée
        confidence  — float 0.0–1.0
    """
    context = context or {}

    if not code or not code.strip():
        return _result("failure", code, "code_empty", 0.0)

    # Séquence de fixes déterministes — ordre fixe, premier qui réussit gagne
    fixers = [
        _fix_indentation,
        _fix_missing_return,
        _fix_incomplete_function,
        _fix_syntax_trivial,
        _fix_reconstruct,
    ]

    for fixer in fixers:
        result = fixer(code, error)
        if result["applied"]:
            fixed = result["code"]
            if verbose:
                print(f"  [agent]   {agent_ident} — fix:{result['name']}")
            if _is_valid_python(fixed):
                if verbose:
                    print(f"  [OK]      syntax valid après fix:{result['name']}")
                return _result("success", fixed, result["name"], result["confidence"])
            # Fix appliqué mais toujours invalide → continuer
            code = fixed  # propager le fix partiel pour le fixer suivant

    # Aucun fix déterministe suffisant — vérifier si le code original est déjà valide
    if _is_valid_python(code):
        if verbose:
            print(f"  [OK]      {agent_ident} — code already valid")
        return _result("success", code, "no_fix_needed", 1.0)

    # Fallback LLM si demandé
    if model_type != "deterministic":
        llm_result = _call_llm_fix(code, error, model_type, context)
        if llm_result["success"]:
            if verbose:
                print(f"  [OK]      {agent_ident} — fix:llm")
            return _result("success", llm_result["code"], "llm_fix", 0.6)
        if verbose:
            print(f"  [FAIL]    {agent_ident} — llm_fix failed: {llm_result.get('error')}")

    if verbose:
        print(f"  [FAIL]    {agent_ident} — no fix found")
    return _result("failure", code, "no_fix_found", 0.0)


# ── Déterministic fixers ───────────────────────────────────────────────────────

def _fix_indentation(code, error):
    """
    Réindente tout le code en suivant la structure syntaxique.
    Applique l'indentation courante à TOUTES les lignes non-vides
    (correction du bug précédent : lignes sans tab ignorées).
    """
    name = "fix_indentation"
    if _is_valid_python(code):
        return _no_fix(name)

    lines   = code.splitlines()
    fixed   = []
    indent  = 0
    changed = False

    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            fixed.append("")
            continue

        # Mots-clés qui diminuent l'indentation avant d'écrire la ligne
        if re.match(r"^(else\s*:|elif\s+|except\s*[\w(:]|except\s*:|finally\s*:)", stripped):
            indent = max(0, indent - 1)

        correct = "    " * indent + stripped
        if correct != line:
            changed = True
        fixed.append(correct)

        # Mots-clés qui augmentent l'indentation après avoir écrit la ligne
        if stripped.endswith(":") and re.match(
            r"^(def |class |if |elif |else\s*:|for |while |try\s*:|except|finally\s*:|with )",
            stripped
        ):
            indent += 1

    if not changed:
        return _no_fix(name)

    return {"applied": True, "name": name, "code": "\n".join(fixed), "confidence": 0.75}


def _fix_missing_return(code, error):
    """Ajoute un return None en fin de fonction si manifestement absent."""
    name = "fix_missing_return"
    if not re.search(r"^\s*def\s+\w+", code, re.MULTILINE):
        return _no_fix(name)

    lines = code.splitlines()
    fixed = list(lines)

    # Trouver les fonctions sans return
    i = 0
    changed = False
    while i < len(lines):
        if re.match(r"^(\s*)def\s+\w+.*:", lines[i]):
            base_indent = len(lines[i]) - len(lines[i].lstrip())
            body_start  = i + 1
            body_end    = body_start

            # Trouver la fin du corps de la fonction
            while body_end < len(lines):
                l = lines[body_end]
                if l.strip() == "":
                    body_end += 1
                    continue
                cur_indent = len(l) - len(l.lstrip())
                if cur_indent <= base_indent:
                    break
                body_end += 1

            body = lines[body_start:body_end]
            has_return = any(re.match(r"^\s*return\b", l) for l in body)
            has_body   = any(l.strip() not in ("", "pass") for l in body)

            if not has_return and has_body:
                # Insérer return None avant la fin du corps
                last_real = body_end - 1
                while last_real > body_start and not lines[last_real].strip():
                    last_real -= 1
                func_indent = base_indent + 4
                fixed.insert(last_real + 1, " " * func_indent + "return None")
                changed = True

        i += 1

    if not changed:
        return _no_fix(name)

    return {"applied": True, "name": name, "code": "\n".join(fixed), "confidence": 0.75}


def _fix_incomplete_function(code, error):
    """Ajoute pass dans les fonctions/classes avec un corps vide."""
    name = "fix_incomplete_function"
    lines   = code.splitlines()
    fixed   = []
    changed = False

    for i, line in enumerate(lines):
        fixed.append(line)
        if re.match(r"^\s*(def |class )\w+.*:\s*$", line):
            # Vérifier si la ligne suivante est vide ou manquante ou au même niveau
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            cur_indent = len(line) - len(line.lstrip())
            next_indent = len(next_line) - len(next_line.lstrip()) if next_line.strip() else -1

            if not next_line.strip() or next_indent <= cur_indent:
                fixed.append(" " * (cur_indent + 4) + "pass")
                changed = True

    if not changed:
        return _no_fix(name)

    return {"applied": True, "name": name, "code": "\n".join(fixed), "confidence": 0.8}


def _fix_syntax_trivial(code, error):
    """Corrections syntaxiques triviales : parenthèses, virgules, guillemets."""
    name    = "fix_syntax_trivial"
    fixed   = code
    changed = False

    # Parenthèse fermante manquante en fin de ligne
    for pat, rep in [
        (r"^(\s*(?:print|return|raise)\s+[^(\n]+[^)\n])\s*$", None),  # heuristique print/return
    ]:
        pass  # placeholder — extensions futures

    # Guillemets non fermés sur une ligne simple (chaîne ouverte)
    lines   = fixed.splitlines()
    out     = []
    for line in lines:
        stripped = line.rstrip()
        # Ne pas toucher aux lignes avec triple-quotes (docstrings)
        if '"""' in stripped or "'''" in stripped:
            out.append(stripped)
            continue
        # Compter les guillemets simples non échappés
        dq = stripped.count('"') - stripped.count('\\"')
        sq = stripped.count("'") - stripped.count("\\'")
        if dq % 2 != 0:
            stripped += '"'
            changed = True
        elif sq % 2 != 0:
            stripped += "'"
            changed = True
        out.append(stripped)

    if not changed:
        return _no_fix(name)

    return {"applied": True, "name": name, "code": "\n".join(out), "confidence": 0.5}


def _fix_reconstruct(code, error):
    """
    Dernier recours déterministe : extrait les signatures def/class
    et reconstruit un squelette minimal valide avec pass.
    Utilisé uniquement si tous les autres fixers ont échoué.
    """
    name = "fix_reconstruct"
    if _is_valid_python(code):
        return _no_fix(name)

    lines = code.splitlines()
    sigs  = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(def |class )\w+", stripped):
            # Normaliser la signature : s'assurer qu'elle se termine par ":"
            sig = stripped if stripped.endswith(":") else stripped + ":"
            sigs.append(sig)

    if not sigs:
        return _no_fix(name)

    out = []
    for sig in sigs:
        out.append(sig)
        out.append("    pass")
        out.append("")

    rebuilt = "\n".join(out).strip()
    if not _is_valid_python(rebuilt):
        return _no_fix(name)

    return {"applied": True, "name": name, "code": rebuilt, "confidence": 0.4}


# ── LLM fallback (isolé, non utilisé par défaut) ──────────────────────────────

def _call_llm_fix(code, error, model_type, context):
    """
    Fallback LLM — uniquement si model_type != "deterministic".
    Retourne {"success": bool, "code": str, "error": str}.
    """
    try:
        from core.functions.prompt_execute import execute
    except ImportError:
        return {"success": False, "error": "prompt_execute_not_available"}

    prompt = (
        f"Tu es un correcteur de code Python.\n"
        f"Erreur : {error or 'code invalide'}\n\n"
        f"Code à corriger :\n```python\n{code}\n```\n\n"
        f"Corrige uniquement le problème signalé. "
        f"Réponds avec le code corrigé entre balises ```python ... ```."
    )

    catalog = context.get("catalog", {})
    result  = execute(model_type, prompt, {"max_tokens": 1024}, catalog)
    if not result.get("success"):
        return {"success": False, "error": result.get("error")}

    fixed = _extract_code_block(result.get("content", ""))
    if not fixed:
        return {"success": False, "error": "no_code_block_in_response"}

    return {"success": True, "code": fixed}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_valid_python(code):
    if not code or not code.strip():
        return False
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _extract_code_block(text):
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else None


def _result(status, code, fix_applied, confidence):
    return {
        "status":      status,
        "fixed_code":  code or "",
        "fix_applied": fix_applied,
        "confidence":  confidence,
    }


def _no_fix(name):
    return {"applied": False, "name": name, "code": "", "confidence": 0.0}


# ── Smoke test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cases = [
        {
            "label": "Code vide",
            "code":  "",
            "error": "",
        },
        {
            "label": "Fonction sans return",
            "code":  "def add(a, b):\n    x = a + b\n",
            "error": "",
        },
        {
            "label": "Fonction incomplète (corps vide)",
            "code":  "def calculate():\n\ndef other():\n    pass\n",
            "error": "expected an indented block",
        },
        {
            "label": "Indentation tabs",
            "code":  "def foo():\n\tx = 1\n\treturn x\n",
            "error": "IndentationError",
        },
        {
            "label": "Code valide (pas de fix nécessaire)",
            "code":  "def hello():\n    return 'world'\n",
            "error": "",
        },
        {
            "label": "Guillemet non fermé",
            "code":  'x = "hello\ny = 1\n',
            "error": "SyntaxError",
        },
    ]

    print("=" * 55)
    print("  agent_debug_fix — smoke test")
    print("=" * 55)

    passed = 0
    for case in cases:
        r = run(case["code"], case["error"], verbose=False)
        ok = "✓" if r["status"] == "success" else "✗"
        print(f"\n{ok} {case['label']}")
        print(f"  fix     : {r['fix_applied']}")
        print(f"  conf    : {r['confidence']}")
        print(f"  status  : {r['status']}")
        if r["fixed_code"] and r["fixed_code"] != case["code"]:
            print("  code    :")
            for line in r["fixed_code"].splitlines():
                print(f"    {line}")
        if r["status"] == "success":
            passed += 1

    print(f"\n{'=' * 55}")
    print(f"  {passed}/{len(cases)} passed")
    print("=" * 55)
