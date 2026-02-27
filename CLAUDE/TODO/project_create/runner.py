#!/usr/bin/env python3
"""
Project Create - Pipeline récursive
process(item): TRIAGE → SPLIT → recurse(stubs) | ATOMIC → lib? → BUILD → test_stub → QA
"""

import ast
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
PROMPTS = ROOT / "prompts"
LOGS = ROOT / "logs"
LIB = ROOT / "lib"
MAX_DEPTH = 3
MAX_QA_RETRIES = 2


# ─── Env ──────────────────────────────────────────────────────────────────────

def load_env() -> str | None:
    from dotenv import load_dotenv
    local_env = ROOT / ".env"
    if local_env.exists():
        load_dotenv(local_env, override=False)
        return str(local_env)
    secrets = Path.home() / ".bigboff" / "secrets.env"
    if secrets.exists():
        load_dotenv(secrets, override=False)
        return str(secrets)
    return None


def load_prompt(agent_name: str) -> str:
    path = PROMPTS / f"agent_{agent_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt introuvable: {path}")
    return path.read_text()


# ─── Logging ──────────────────────────────────────────────────────────────────

_log_file: Path | None = None


def log(message: str):
    print(message)
    if _log_file:
        with open(_log_file, "a") as f:
            f.write(message + "\n")


def log_call(agent_name: str, system: str, user: str, response: str, depth: int):
    pad = "  " * depth
    ts = datetime.now().strftime("%H:%M:%S")
    bar = "─" * max(10, 56 - depth * 2)
    log(f"\n{pad}{bar}")
    log(f"{pad}[{ts}] ▶ {agent_name.upper()}  depth={depth}")
    log(f"{pad}── SYSTEM ({len(system)} chars) ──")
    for line in system.splitlines():
        log(f"{pad}{line}")
    log(f"{pad}── INPUT ({len(user)} chars) ──")
    for line in user.splitlines():
        log(f"{pad}{line}")
    log(f"{pad}── OUTPUT ({len(response)} chars) ──")
    for line in response.splitlines():
        log(f"{pad}{line}")
    log(f"{pad}{bar}")


# ─── API ──────────────────────────────────────────────────────────────────────

def call_agent(client, agent_name: str, user_content: str, model: str, depth: int) -> str:
    system_prompt = load_prompt(agent_name)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    response = message.content[0].text
    log_call(agent_name, system_prompt, user_content, response, depth)
    return response


# ─── Lib (stockage fonctions validées) ────────────────────────────────────────

def lib_find(name: str) -> str | None:
    """Cherche une fonction dans lib/ par nom. Retourne le code source ou None."""
    path = LIB / f"{name}.py"
    return path.read_text() if path.exists() else None


def lib_store(name: str, code: str):
    """Stocke une fonction validée dans lib/."""
    LIB.mkdir(exist_ok=True)
    (LIB / f"{name}.py").write_text(code)
    log(f"  📦 lib/{name}.py enregistré")


def lib_context(contract: dict) -> str:
    """Retourne le code des fonctions lib/ dont le nom apparaît dans le contrat."""
    text = " ".join(str(v) for v in contract.values()).lower()
    snippets = []
    for path in sorted(LIB.glob("*.py")):
        if path.stem.lower() in text:
            snippets.append(f"# {path.name}\n{path.read_text().strip()}")
    return "\n\n".join(snippets)


# ─── Test stub ────────────────────────────────────────────────────────────────

def match(actual, expected) -> bool:
    """
    Comparaison avec wildcard "*" pour les valeurs non-déterministes.
    - "*" dans expected → accepte n'importe quelle valeur
    - dict : compare récursivement les clés présentes dans expected
    """
    if expected == "*":
        return True
    if isinstance(expected, dict) and isinstance(actual, dict):
        return all(match(actual.get(k), v) for k, v in expected.items())
    return actual == expected


def test_stub(code: str, fn_name: str, example_input: str, expected: str) -> tuple[bool, str]:
    """
    Teste fn(*args) contre expected.
    - Multi-args : example_input = "arg1, arg2, arg3"
    - Mutation en place : si return None, compare args[0] à expected
    - Pas d'exemple : skip (return True)
    """
    if not example_input or example_input.strip() in ("None", ""):
        return True, "✅ pas d'exemple — skip"

    namespace: dict = {}
    try:
        exec(compile(code, "<generated>", "exec"), namespace)
        fn = namespace.get(fn_name)
        if fn is None:
            return False, f"Fonction '{fn_name}' non trouvée dans le code"

        expected_val = ast.literal_eval(expected)

        # Évalue les args comme une liste → supporte multi-args et capture l'état
        args = eval(f"[{example_input}]", {})
        result = fn(*args)

        # 1. Comparer la valeur de retour
        if match(result, expected_val):
            return True, f"✅ return == {expected}"

        # 2. Si return None (mutation en place) → comparer args[0]
        if result is None and args and match(args[0], expected_val):
            return True, f"✅ state == {expected}"

        got = result if result is not None else (args[0] if args else None)
        return False, f"❌ attendu {expected_val!r}, obtenu {got!r}"

    except Exception as e:
        return False, f"❌ erreur: {e}"


# ─── Parsers ──────────────────────────────────────────────────────────────────

def parse_triage(output: str) -> str:
    for line in output.splitlines():
        upper = line.strip().upper()
        if upper.startswith("## MVP"):
            return "mvp"
        if upper.startswith("## NEXT"):
            return "next"
    return "mvp"


def parse_split(output: str) -> tuple[str, dict | list[dict]]:
    """
    Retourne:
      ('atomic',  {name, input, output, goal, example_input, example_expected, code})
      ('atomics', [{...}, ...])   — plusieurs blocs ## ATOMIC
      ('steps',   [{name, goal, input, output, stub_code}, ...])
    """
    lines = output.splitlines()
    mode = None  # 'atomic' | 'steps'
    current: dict = {}
    steps: list[dict] = []
    atomics: list[dict] = []
    code_block: list[str] = []
    in_code = False

    def flush_current():
        if current.get("name"):
            if mode == "atomic":
                atomics.append(dict(current))
            elif mode == "steps":
                steps.append(dict(current))

    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()

        # Mode switches
        if upper.startswith("## ATOMIC"):
            flush_current()
            mode = "atomic"
            current = {}
            continue
        if upper.startswith("## STEPS"):
            mode = "steps"
            continue
        is_step_marker = (
            (upper.startswith("## STEP") and not upper.startswith("## STEPS"))
            or upper.startswith("### STEP")
        )
        if mode == "steps" and is_step_marker:
            flush_current()
            current = {}
            continue

        # Code block tracking
        if stripped.startswith("```python"):
            in_code = True
            code_block = []
            continue
        if stripped == "```" and in_code:
            in_code = False
            code_str = "\n".join(code_block).strip()
            if mode == "atomic":
                current["code"] = code_str
            elif mode == "steps":
                current["stub_code"] = code_str
            continue
        if in_code:
            code_block.append(line)
            continue

        # Key: value fields (supporte **key:** `value` et key: value)
        if ":" in stripped and not in_code:
            key, _, val = stripped.partition(":")
            key = key.strip().lower().replace(" ", "_").replace("*", "").replace("`", "").strip()
            val = val.strip().replace("`", "").replace("**", "").strip()
            if key in ("name", "input", "output", "goal",
                       "example_input", "example_expected"):
                current[key] = val

    flush_current()
    if atomics:
        return ("atomic", atomics[0]) if len(atomics) == 1 else ("atomics", atomics)
    return "steps", steps


def parse_code_block(output: str) -> str:
    """Extrait le premier bloc ```python ... ``` d'une réponse BUILD."""
    lines = output.splitlines()
    in_block = False
    result = []
    for line in lines:
        if line.strip().startswith("```python"):
            in_block = True
            continue
        if line.strip() == "```" and in_block:
            break
        if in_block:
            result.append(line)
    return "\n".join(result).strip() if result else output.strip()


def is_qa_pass(output: str) -> bool:
    for line in output.splitlines():
        upper = line.strip().upper()
        if upper.startswith("## PASS"):
            return True
        if upper.startswith("## FAIL"):
            return False
    return False


def format_contract(data: dict) -> str:
    """Formate un contrat pour l'envoyer à BUILD."""
    parts = [
        f"name: {data.get('name', 'unknown')}",
        f"goal: {data.get('goal', '')}",
        f"input: {data.get('input', '')}",
        f"output: {data.get('output', '')}",
        f"example_input: {data.get('example_input', '')}",
        f"example_expected: {data.get('example_expected', '')}",
    ]
    return "\n".join(parts)


def format_history(history: list[dict]) -> str:
    parts = []
    for h in history:
        parts.append(
            f"Tentative {h['attempt']}:\n"
            f"  Test: {h['test_result']}\n"
            f"  QA: {h.get('qa_feedback', '')}"
        )
    return "\n\n".join(parts)


# ─── Build + test stub ────────────────────────────────────────────────────────

def build_and_qa(client, contract: dict, model: str, depth: int) -> str | None:
    """
    1. Cherche dans lib par nom
    2. Sinon BUILD depuis le contrat
    3. Test réel contre stub (exec)
    4. QA LLM si test échoue
    5. Retry avec historique
    6. Stocke dans lib si PASS
    """
    pad = "  " * depth
    name = contract.get("name", "unknown")
    ex_in = contract.get("example_input", "")
    ex_ex = contract.get("example_expected", "")

    # 1. Cherche dans lib
    existing = lib_find(name)
    if existing:
        log(f"{pad}🔍 '{name}' trouvé en lib — test contre stub…")
        ok, msg = test_stub(existing, name, ex_in, ex_ex)
        if ok:
            log(f"{pad}♻️  Réutilisé : {msg}")
            return existing
        log(f"{pad}⚠️  Lib KO ({msg}) → rebuild")

    # 2. BUILD + retry
    history: list[dict] = []
    contract_str = format_contract(contract)
    ctx = lib_context(contract)
    build_input = contract_str if not ctx else f"{contract_str}\n\n## CONTEXT\n{ctx}"
    code_raw = call_agent(client, "build", build_input, model, depth)
    code = parse_code_block(code_raw)

    for attempt in range(1, MAX_QA_RETRIES + 1):
        # Test réel
        ok, test_msg = test_stub(code, name, ex_in, ex_ex)
        log(f"{pad}  test_stub: {test_msg}")

        if ok:
            log(f"{pad}✅ PASS (tentative {attempt})")
            lib_store(name, code)
            return code

        # QA LLM pour feedback enrichi
        qa_input = (
            f"Contrat:\n{contract_str}\n\n"
            f"Code:\n```python\n{code}\n```\n\n"
            f"Résultat test: {test_msg}"
        )
        qa_out = call_agent(client, "qa", qa_input, model, depth)
        history.append({"attempt": attempt, "test_result": test_msg, "qa_feedback": qa_out})

        if attempt < MAX_QA_RETRIES:
            retry_input = (
                f"{build_input}\n\n"
                f"Historique des tentatives:\n{format_history(history)}"
            )
            code_raw = call_agent(client, "build", retry_input, model, depth)
            code = parse_code_block(code_raw)

    log(f"{pad}⚠️  KO après {MAX_QA_RETRIES} tentatives — code retourné sans validation")
    return code


# ─── Récursion ────────────────────────────────────────────────────────────────

def step_to_item(step: dict) -> str:
    """Convertit une étape (avec stub) en item pour le prochain process()."""
    return (
        f"name: {step.get('name', '')}\n"
        f"goal: {step.get('goal', '')}\n"
        f"input: {step.get('input', '')}\n"
        f"output: {step.get('output', '')}\n"
        f"stub:\n```python\n{step.get('stub_code', '')}\n```"
    )


def process(client, item: str, model: str, backlog: list, depth: int) -> str | None:
    pad = "  " * depth
    short = item[:60] + "…" if len(item) > 60 else item
    log(f"\n{pad}{'━' * max(10, 50 - depth * 2)}")
    log(f"{pad}🔄 [depth={depth}] {short}")

    # TRIAGE
    triage_out = call_agent(client, "triage", item, model, depth)
    decision = parse_triage(triage_out)

    if decision == "next":
        log(f"{pad}⏭  NEXT → backlog")
        backlog.append(item)
        return None

    log(f"{pad}✓  MVP → continue")

    if depth >= MAX_DEPTH:
        log(f"{pad}⚠  profondeur max → BUILD direct")
        name = next(
            (l.split(":", 1)[1].strip() for l in item.splitlines() if l.startswith("name:")),
            "unknown_fn"
        )
        return build_and_qa(client, {"name": name, "goal": item,
                                      "input": "unknown", "output": "unknown",
                                      "example_input": "None", "example_expected": "None"},
                             model, depth)

    # SPLIT
    split_out = call_agent(client, "split", item, model, depth)
    split_type, split_content = parse_split(split_out)

    if split_type == "atomic":
        log(f"{pad}⚡ ATOMIC → BUILD + test")
        return build_and_qa(client, split_content, model, depth)

    if split_type == "atomics":
        log(f"{pad}⚡ {len(split_content)} ATOMIC → BUILD + test chacun")
        results = []
        for contract in split_content:
            log(f"{pad}  ↳ {contract.get('name', '?')}")
            result = build_and_qa(client, contract, model, depth)
            if result:
                results.append(result)
        return "\n\n---\n\n".join(results) if results else None

    # STEPS → récursion avec stubs
    log(f"{pad}🔀 {len(split_content)} sous-étapes")
    results = []
    for step in split_content:
        log(f"{pad}  ↳ {step.get('name', '?')} — stub dispo, on recurse")
        result = process(client, step_to_item(step), model, backlog, depth + 1)
        if result:
            results.append(result)
    return "\n\n---\n\n".join(results) if results else None


# ─── Entrée ───────────────────────────────────────────────────────────────────

def run_pipeline(brief: str):
    import anthropic
    global _log_file

    env_source = load_env()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY manquante")
        sys.exit(1)

    model = os.getenv("PROJECT_CREATE_MODEL", "claude-haiku-4-5-20251001")
    client = anthropic.Anthropic(api_key=api_key)

    LOGS.mkdir(exist_ok=True)
    LIB.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _log_file = LOGS / f"run_{ts}.log"

    log("=" * 60)
    log("PROJECT CREATE — Pipeline récursive")
    log(f"Modèle   : {model}  |  MaxDepth : {MAX_DEPTH}  |  QA retries : {MAX_QA_RETRIES}")
    log(f"Env      : {env_source or 'aucune'}  |  Log : {_log_file}")
    log("=" * 60)
    log(f"Brief    : {brief}")

    backlog: list[str] = []
    process(client, brief, model, backlog, depth=0)

    if backlog:
        log("\n── BACKLOG ──")
        backlog_input = "\n".join(f"- {item}" for item in backlog)
        call_agent(client, "backlog", backlog_input, model, depth=0)
    else:
        log("\n(Backlog vide)")

    log(f"\n✅ Pipeline terminée — log : {_log_file}")


if __name__ == "__main__":
    brief = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Créer une API REST simple"
    run_pipeline(brief)
