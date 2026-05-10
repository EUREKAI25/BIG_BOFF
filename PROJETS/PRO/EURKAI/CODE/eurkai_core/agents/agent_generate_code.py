"""
agent_generate_code
Agent qui génère du code (Python ou HTML) depuis un schema/objet EURKAI.
Deterministic-first : squelette sans LLM.
LLM optionnel : enrichissement si model_type != "deterministic".
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run(schema_ident, params, catalog, model_type="deterministic", verbose=True,
        agent_ident="agent_generate_code", context=None):
    """
    Génère du code depuis un schema EURKAI.

    params accepte :
        object_type     — function | class | module | scenario | page | tool_page
        target_language — "python" (défaut) ou "html"
        filename        — auto-résolu si absent
        goal            — description fonctionnelle libre
        attributes      — dict des champs / attributs
        manifest        — dict MANIFEST si disponible

    Retourne :
        status          — "ok" | "partial" | "error"
        schema_ident    — echo de l'entrée
        target_language — langage généré
        filename        — nom de fichier résolu
        code            — contenu généré
        warnings        — liste de messages
    """
    storage = catalog.get("_storage") if isinstance(catalog, dict) else None

    schema = storage.get("schema", schema_ident) if storage else None

    warnings = []

    object_type     = params.get("object_type") or _infer_type(schema, schema_ident)
    target_language = params.get("target_language") or _infer_language(object_type)
    goal            = params.get("goal") or params.get("object_goal") or ""
    attributes      = params.get("attributes") or (schema.get("schema_fields", {}) if schema else {})
    filename        = params.get("filename") or _resolve_filename(schema_ident, target_language)

    if not object_type:
        warnings.append("object_type absent — fallback vers 'class'")
        object_type = "class"

    if verbose:
        print(f"  [agent]   {agent_ident} — schema:{schema_ident} type:{object_type} lang:{target_language}")

    code = _generate_skeleton(
        schema_ident=schema_ident,
        object_type=object_type,
        target_language=target_language,
        goal=goal,
        attributes=attributes or {},
    )

    if model_type != "deterministic":
        llm_result = _enrich_with_llm(code, schema_ident, goal, model_type, catalog)
        if llm_result.get("success"):
            code = llm_result["code"]
        else:
            warnings.append(f"llm_enrich_failed:{llm_result.get('error')} — using skeleton")

    if not code:
        return {
            "status":          "error",
            "schema_ident":    schema_ident,
            "target_language": target_language,
            "filename":        filename,
            "code":            "",
            "warnings":        warnings + ["generation_failed"],
        }

    status = "partial" if warnings else "ok"

    if verbose:
        lines = code.count("\n") + 1
        print(f"  [{'OK' if status == 'ok' else 'WARN'}]   {filename} — {lines} lignes — {target_language}")

    return {
        "status":          status,
        "schema_ident":    schema_ident,
        "target_language": target_language,
        "filename":        filename,
        "code":            code,
        "warnings":        warnings,
    }


# ── Skeleton generators ───────────────────────────────────────────────────────

def _generate_skeleton(schema_ident, object_type, target_language, goal, attributes):
    if target_language == "html":
        return _skeleton_html(schema_ident, goal, attributes)

    generators = {
        "function": _skeleton_function,
        "class":    _skeleton_class,
        "object":   _skeleton_class,
        "module":   _skeleton_module,
        "scenario": _skeleton_scenario,
    }
    gen = generators.get(object_type, _skeleton_class)
    return gen(schema_ident, goal, attributes)


def _skeleton_function(ident, goal, attributes):
    name = _to_snake(ident)
    args = ", ".join(attributes.keys()) if attributes else "data"
    doc  = goal or f"Function {name}."
    body = "\n".join(f"    # {k}: {v}" for k, v in attributes.items()) or "    pass"
    return (
        f"def {name}({args}):\n"
        f'    """\n'
        f"    {doc}\n"
        f'    """\n'
        f"{body}\n"
        f"    return None\n"
    )


def _skeleton_class(ident, goal, attributes):
    name      = _to_pascal(ident)
    doc       = goal or f"Object {name}."
    init_args = ", ".join(f"{k}=None" for k in attributes.keys())
    init_body = "\n".join(f"        self.{k} = {k}" for k in attributes.keys()) or "        pass"
    sep       = ", " if init_args else ""
    return (
        f"from typing import Any, Dict\n\n\n"
        f"class {name}:\n"
        f'    """\n'
        f"    {doc}\n"
        f'    """\n\n'
        f"    def __init__(self{sep}{init_args}):\n"
        f"{init_body}\n\n"
        f"    def validate(self) -> Dict[str, Any]:\n"
        f"        errors = []\n"
        f"        return {{\"valid\": len(errors) == 0, \"errors\": errors}}\n\n"
        f"    def to_dict(self) -> Dict[str, Any]:\n"
        f"        return {{k: v for k, v in self.__dict__.items()}}\n\n"
        f"    @classmethod\n"
        f"    def test(cls) -> bool:\n"
        f"        obj = cls()\n"
        f"        assert \"valid\" in obj.validate()\n"
        f"        return True\n"
    )


def _skeleton_module(ident, goal, attributes):
    name = _to_snake(ident)
    doc  = goal or f"Module {name}."
    return (
        f'"""\n'
        f"{name}\n"
        f"{doc}\n"
        f'"""\n\n\n'
        f"def run(params: dict) -> dict:\n"
        f'    """\n'
        f"    Point d'entrée principal.\n"
        f'    """\n'
        f"    return {{\"success\": True, \"result\": None, \"params\": params}}\n\n\n"
        f"if __name__ == \"__main__\":\n"
        f"    print(run({{}}))\n"
    )


def _skeleton_scenario(ident, goal, attributes):
    name = _to_pascal(ident)
    doc  = goal or f"Scenario {name}."
    snake = _to_snake(ident)
    return (
        f'"""\n'
        f"{snake}\n"
        f"{doc}\n"
        f'"""\n\n\n'
        f"class {name}:\n"
        f'    """\n'
        f"    {doc}\n"
        f'    """\n\n'
        f'    NAME    = "{snake}"\n'
        f'    VERSION = "0.1.0"\n\n'
        f"    def run(self, context: dict, catalog: dict) -> dict:\n"
        f"        return {{\"success\": True, \"outputs\": {{}}}}\n\n"
        f"    @classmethod\n"
        f"    def test(cls) -> bool:\n"
        f"        r = cls().run({{}}, {{}})\n"
        f"        assert r.get(\"success\") is True\n"
        f"        return True\n\n\n"
        f"if __name__ == \"__main__\":\n"
        f"    print({name}().run({{}}, {{}}))\n"
    )


def _skeleton_html(ident, goal, attributes):
    title  = _to_pascal(ident).replace("_", " ")
    doc    = goal or f"Page {title}"
    fields = "\n".join(
        f'    <div class="field"><label>{k}</label><span></span></div>'
        for k in attributes.keys()
    ) or "    <!-- fields -->"
    return (
        f"<!DOCTYPE html>\n"
        f'<html lang="fr">\n'
        f"<head>\n"
        f'  <meta charset="UTF-8">\n'
        f'  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"  <title>{title}</title>\n"
        f"  <style>\n"
        f"    body {{ font-family: system-ui, sans-serif; margin: 2rem; }}\n"
        f"    .field {{ margin-bottom: 1rem; }}\n"
        f"    label {{ font-weight: bold; margin-right: .5rem; }}\n"
        f"  </style>\n"
        f"</head>\n"
        f"<body>\n"
        f"  <h1>{title}</h1>\n"
        f"  <p>{doc}</p>\n"
        f"  <section>\n"
        f"{fields}\n"
        f"  </section>\n"
        f"</body>\n"
        f"</html>\n"
    )


# ── LLM enrichment (optional) ─────────────────────────────────────────────────

def _enrich_with_llm(code, schema_ident, goal, model_type, catalog):
    try:
        from core.functions.prompt_execute import execute
    except ImportError:
        return {"success": False, "error": "prompt_execute_not_available"}

    prompt = (
        f"Tu es un générateur de code EURKAI.\n"
        f"Objet : `{schema_ident}`. Objectif : {goal or 'non spécifié'}.\n\n"
        f"Squelette :\n```python\n{code}\n```\n\n"
        f"Complète avec une implémentation minimale et cohérente. "
        f"Réponds uniquement avec le code entre balises ```python ... ```."
    )

    result = execute(model_type, prompt, {"max_tokens": 2048}, catalog)
    if not result.get("success"):
        return {"success": False, "error": result.get("error")}

    enriched = _extract_code_block(result.get("content", ""))
    if not enriched:
        return {"success": False, "error": "no_code_block_in_response"}

    return {"success": True, "code": enriched}


def _extract_code_block(text):
    m = re.search(r"```(?:python|html)?\s*(.*?)```", text, re.DOTALL)
    return m.group(1).strip() if m else None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _infer_type(schema, schema_ident):
    if schema:
        t = schema.get("schema_type") or schema.get("object_type")
        if t:
            return t
    ident = (schema_ident or "").lower()
    for kw in ("function", "scenario", "module", "page", "tool_page"):
        if kw in ident:
            return kw
    return "class"


def _infer_language(object_type):
    return "html" if object_type in ("page", "tool_page") else "python"


def _resolve_filename(schema_ident, target_language):
    base = _to_snake(schema_ident or "generated")
    ext  = "html" if target_language == "html" else "py"
    return f"{base}.{ext}"


def _to_snake(s):
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s or "")
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _to_pascal(s):
    # Si déjà PascalCase (contient une majuscule interne), ne pas re-capitaliser
    clean = re.sub(r"[_\-\s]+", "", s or "generated")
    if re.search(r"[a-z][A-Z]", clean):
        return clean
    return "".join(w.capitalize() for w in re.split(r"[_\-\s]+", s or "generated"))


# ── Smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _catalog = {"_storage": None}

    cases = [
        ("my_function",    {"object_type": "function",  "goal": "Calcule un total HT/TTC.",
                            "attributes": {"price_ht": "float", "tva_rate": "float"}}),
        ("UserProfile",    {"object_type": "class",     "attributes": {"name": "str", "email": "str"}}),
        ("invoice_module", {"object_type": "module",    "goal": "Génère des factures PDF."}),
        ("checkout_flow",  {"object_type": "scenario",  "goal": "Orchestration paiement."}),
        ("tool_dashboard", {"object_type": "tool_page", "goal": "Dashboard EURKAI."}),
        ("unknown_thing",  {}),
    ]

    for ident, params in cases:
        r = run(ident, params, _catalog, model_type="deterministic", verbose=True)
        print(f"\n--- {r['filename']} [{r['status']}] ---")
        print(r["code"][:300] + ("..." if len(r["code"]) > 300 else ""))
        if r["warnings"]:
            print("WARNINGS:", r["warnings"])
