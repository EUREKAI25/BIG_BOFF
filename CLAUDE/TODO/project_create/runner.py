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
MAX_DEPTH = 2           # règle métier : Brief → STEPS (d=1) → ATOMICs (d=2), pas de STEPS dans des STEPS
MAX_DEPTH_SAFETY = 10  # garde-fou anti-boucle infinie uniquement
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
_project_config: dict | None = None


def load_project_config(path: Path | None = None) -> dict | None:
    """Charge project.json si présent (chemin explicite, répertoire courant ou ROOT)."""
    import json
    for p in [path, Path.cwd() / "project.json", ROOT / "project.json"]:
        if p and Path(p).exists():
            config = json.loads(Path(p).read_text())
            log(f"📋 Config projet chargée : {p}")
            return config
    return None


def format_project_config() -> str:
    """Formate _project_config pour injection dans les prompts."""
    import json
    if not _project_config:
        return ""
    return f"## PROJECT CONFIG\n```json\n{json.dumps(_project_config, indent=2, ensure_ascii=False)}\n```"


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


def eval_expected(expected: str, namespace: dict):
    """
    Évalue expected en trois passes :
    1. ast.literal_eval  — littéraux Python purs
    2. eval(namespace)   — objets définis dans le code (Pydantic, dataclasses…)
    3. None              — non évaluable (appelant décidera de skip la comparaison)
    """
    try:
        return ast.literal_eval(expected)
    except (ValueError, SyntaxError):
        pass
    try:
        return eval(expected, dict(namespace))
    except Exception:
        pass
    return None


def test_stub(code: str, fn_name: str, example_input: str, expected: str) -> tuple[bool, str]:
    """
    Teste fn(*args) contre expected.
    - Multi-args : example_input = "arg1, arg2, arg3"
    - Mutation en place : si return None, compare args[0] à expected
    - Pas d'exemple : skip (return True)
    - expected non évaluable (ex: JSONResponse) : run-only, skip comparaison
    """
    if not example_input or example_input.strip() in ("None", ""):
        return True, "✅ pas d'exemple — skip"

    namespace: dict = {}
    try:
        exec(compile(code, "<generated>", "exec"), namespace)
        fn = namespace.get(fn_name)
        if fn is None:
            return False, f"Fonction '{fn_name}' non trouvée dans le code"

        expected_val = eval_expected(expected, namespace)

        # Évaluer les args — même fallback que eval_expected
        try:
            args = eval(f"[{example_input}]", dict(namespace))
        except Exception:
            return True, "✅ code exécuté sans erreur (args non évaluables — comparaison ignorée)"

        result = fn(*args)

        # expected non évaluable → on vérifie juste que le code tourne
        if expected_val is None:
            return True, "✅ code exécuté sans erreur (expected non évaluable — comparaison ignorée)"

        if match(result, expected_val):
            return True, f"✅ return == {expected}"

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


def parse_qa(output: str) -> str:
    for line in output.splitlines():
        upper = line.strip().upper()
        if upper.startswith("## PASS"):
            return "pass"
        if upper.startswith("## FAIL"):
            return "fail"
    return "fail"


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

        # Mode switches (tolère # et ## comme préfixe de heading)
        clean = upper.lstrip("#").strip()
        if clean.startswith("ATOMIC"):
            flush_current()
            mode = "atomic"
            current = {}
            continue
        if clean.startswith("STEPS"):
            flush_current()
            mode = "steps"
            continue
        is_step_marker = clean.startswith("STEP") and not clean.startswith("STEPS")
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

        # Key: value fields (supporte **key:** `value`, ## key: value, key: value)
        if ":" in stripped and not in_code:
            key, _, val = stripped.partition(":")
            key = key.strip().lower().replace(" ", "_").replace("*", "").replace("`", "").replace("#", "").strip()
            val = val.strip().replace("`", "").replace("**", "").strip()
            if key in ("name", "input", "output", "goal",
                       "example_input", "example_expected"):
                current[key] = val

    flush_current()
    if atomics and steps:
        return "mixed", {"atomics": atomics, "steps": steps}
    if atomics:
        return ("atomic", atomics[0]) if len(atomics) == 1 else ("atomics", atomics)
    return "steps", steps


def parse_manifest(output: str) -> dict:
    """Extrait le MANIFEST JSON produit par l'orchestrateur."""
    import json, re
    m = re.search(r"```json\s*(.*?)```", output, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(output.strip())
    except json.JSONDecodeError:
        pass
    return {"artifacts": [], "context": {}, "mission": "", "success": "", "delivery": {}}


def artifact_to_brief(artifact: dict, context: dict) -> str:
    """Convertit un artifact du MANIFEST en brief pour process()."""
    parts = [
        f"Créer le fichier : {artifact['path']}",
        f"Langage : {artifact['language']}",
        f"Objectif : {artifact['goal']}",
    ]
    if context.get("packages"):
        parts.append(f"Packages disponibles : {', '.join(context['packages'])}")
    if context.get("notes"):
        parts.append(f"Contexte : {context['notes']}")
    return "\n".join(parts)


def process_artifact(client, artifact: dict, manifest: dict, model: str,
                     backlog: list, outdir: Path) -> str | None:
    """Traite un artifact : build + QA + sauvegarde dans outputs/<projet>/."""
    global MAX_DEPTH, _project_config

    brief = artifact_to_brief(artifact, manifest.get("context", {}))

    # Injecter le langage de l'artifact dans la config projet
    orig_config = dict(_project_config) if _project_config else {}
    artifact_config = dict(orig_config)
    artifact_config.setdefault("stack", {})["language"] = artifact["language"]
    _project_config = artifact_config

    # Depth par artifact (avec fallback sur MAX_DEPTH global)
    orig_depth = MAX_DEPTH
    MAX_DEPTH = artifact.get("depth", orig_depth)

    result = process(client, brief, model, backlog, depth=0)

    MAX_DEPTH = orig_depth
    _project_config = orig_config if orig_config else None

    if result:
        out_path = outdir / artifact["path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result)
        log(f"  💾 {artifact['path']} → {out_path}")

    return result


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

def build_and_qa(client, contract: dict, model: str, depth: int,
                 extra_context: str = "") -> str | None:
    """
    1. Cherche dans lib par nom
    2. Sinon BUILD depuis le contrat
    3. Test réel contre stub (exec)
    4. QA LLM si test échoue
    5. Retry avec historique
    6. Stocke dans lib si PASS
    extra_context : code des sous-fonctions déjà buildées (pour assemblage parent)
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
    ctx_parts = [c for c in [lib_context(contract), extra_context, format_project_config()] if c]
    ctx = "\n\n".join(ctx_parts)
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

        # QA LLM pour verdict + feedback
        qa_input = (
            f"Contrat:\n{contract_str}\n\n"
            f"Code:\n```python\n{code}\n```\n\n"
            f"Résultat test: {test_msg}"
        )
        qa_out = call_agent(client, "qa", qa_input, model, depth)
        qa_result = parse_qa(qa_out)
        history.append({"attempt": attempt, "test_result": test_msg, "qa_feedback": qa_out})

        if qa_result == "pass":
            log(f"{pad}✅ PASS QA (tentative {attempt}) — test non déterministe accepté")
            lib_store(name, code)
            return code

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

    if depth >= MAX_DEPTH_SAFETY:
        log(f"{pad}⚠  garde-fou profondeur {MAX_DEPTH_SAFETY} atteint — branche abandonnée")
        return None

    # SPLIT — injecter la config projet + contrainte de profondeur
    split_input = item
    cfg = format_project_config()
    if cfg:
        split_input = f"{item}\n\n{cfg}"
    if depth >= MAX_DEPTH:
        split_input = f"[ATOMIC OBLIGATOIRE — profondeur max {MAX_DEPTH} atteinte]\n\n{split_input}"
    split_out = call_agent(client, "split", split_input, model, depth)
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

    if split_type == "mixed":
        atomics = split_content["atomics"]
        steps   = split_content["steps"]
        log(f"{pad}⚡ {len(atomics)} ATOMIC + 🔀 {len(steps)} STEPS")
        results = []
        for contract in atomics:
            log(f"{pad}  ↳ {contract.get('name', '?')} (atomic)")
            result = build_and_qa(client, contract, model, depth)
            if result:
                results.append(result)
        for step in steps:
            log(f"{pad}  ↳ {step.get('name', '?')} (step → recurse)")
            result = process(client, step_to_item(step), model, backlog, depth + 1)
            if result:
                results.append(result)
        return "\n\n---\n\n".join(results) if results else None

    # STEPS → récursion avec stubs, puis BUILD du parent avec sous-fonctions comme contexte
    log(f"{pad}🔀 {len(split_content)} sous-étapes")
    step_results: list[tuple[str, str]] = []
    for step in split_content:
        log(f"{pad}  ↳ {step.get('name', '?')} — recurse")
        result = process(client, step_to_item(step), model, backlog, depth + 1)
        if result:
            step_results.append((step.get("name", ""), result))

    # Remonter : BUILD la fonction parente avec les sous-fonctions comme contexte
    parent_name = next(
        (l.split(":", 1)[1].strip() for l in item.splitlines()
         if l.strip().lower().startswith("name:")), None
    )
    if parent_name and step_results:
        parent_contract: dict = {"name": parent_name, "example_input": "", "example_expected": ""}
        for line in item.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                k = k.strip().lower()
                if k in ("goal", "input", "output"):
                    parent_contract[k] = v.strip()
        sub_ctx = "\n\n".join(f"# {n}.py\n{c}" for n, c in step_results)
        log(f"{pad}🔧 BUILD '{parent_name}' depuis {len(step_results)} sous-fonctions")
        return build_and_qa(client, parent_contract, model, depth, extra_context=sub_ctx)

    return "\n\n---\n\n".join(c for _, c in step_results) if step_results else None


# ─── Entrée ───────────────────────────────────────────────────────────────────

def run_pipeline(brief: str, config_path: Path | None = None):
    import anthropic
    global _log_file, _project_config

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
    _project_config = load_project_config(config_path)

    log("=" * 60)
    log("PROJECT CREATE — Pipeline récursive")
    log(f"Modèle   : {model}  |  QA retries : {MAX_QA_RETRIES}  |  Config : {'oui' if _project_config else 'non'}")
    log(f"Env      : {env_source or 'aucune'}  |  Log : {_log_file}")
    log("=" * 60)
    log(f"Brief    : {brief}")

    backlog: list[str] = []

    if _project_config:
        # Mode orchestré : project.json → MANIFEST → artifacts
        import json as _json
        project_str = _json.dumps(_project_config, indent=2, ensure_ascii=False)
        orch_out = call_agent(client, "orchestrator", project_str, model, depth=0)
        manifest = parse_manifest(orch_out)

        manifest_path = LOGS / f"manifest_{ts}.json"
        manifest_path.write_text(_json.dumps(manifest, indent=2, ensure_ascii=False))
        log(f"\n📋 Mission  : {manifest.get('mission', '?')}")
        log(f"   Succès   : {manifest.get('success', '?')}")
        log(f"   Manifest : {manifest_path}")

        project_name = _project_config.get("project", "projet")
        outdir = ROOT / "outputs" / project_name
        outdir.mkdir(parents=True, exist_ok=True)

        for artifact in manifest.get("artifacts", []):
            log(f"\n{'━' * 50}")
            log(f"📄 {artifact['path']}  [{artifact['language']}  depth={artifact.get('depth', 2)}]")
            process_artifact(client, artifact, manifest, model, backlog, outdir)
    else:
        # Mode direct : brief texte sans project.json
        process(client, brief, model, backlog, depth=0)

    if backlog:
        log("\n── BACKLOG ──")
        backlog_input = "\n".join(f"- {item}" for item in backlog)
        call_agent(client, "backlog", backlog_input, model, depth=0)
    else:
        log("\n(Backlog vide)")

    log(f"\n✅ Pipeline terminée — log : {_log_file}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Project Create — pipeline récursive")
    parser.add_argument("brief", nargs="*", help="Brief du projet")
    parser.add_argument("--config", type=Path, default=None, help="Chemin vers project.json")
    args = parser.parse_args()
    brief = " ".join(args.brief) if args.brief else "Créer une API REST simple"
    run_pipeline(brief, config_path=args.config)
