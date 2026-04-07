"""
agent_generate_object
Agent IA qui génère un objet EURKAI conforme depuis un schema.
Tout le contenu textuel vient du catalog (role, contraintes, template, expected_output).
Python = exécuteur uniquement.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run(schema_ident, params, catalog, model_type="llm", verbose=True,
        agent_ident="agent_generate_object"):
    """
    Génère un objet depuis un schema.
    params : dict avec object_lineage, object_goal, etc.
    Retourne : dict avec generated_object + validate_result.
    """
    from core.functions.prompt_execute import execute
    from core.functions.placeholder_resolve import resolve_template
    from core.functions.validate_object_vs_schema import validate_object_vs_schema

    storage = catalog["_storage"]

    # Agent
    agent = storage.get("agent", agent_ident)
    if agent is None:
        return {"success": False, "error": f"agent_not_found:{agent_ident}"}

    # Role
    role = storage.get("role", agent.get("agent_role", ""))
    role_description = role.get("role_description", "") if role else ""

    # PromptTemplate
    template_ident  = agent.get("agent_prompt_template", "template_generate_object")
    prompt_template = storage.get("prompt_template", template_ident)
    if prompt_template is None:
        return {"success": False, "error": f"prompt_template_not_found:{template_ident}"}
    template_text = prompt_template.get("prompt_template_text", "")

    # Schema cible
    schema = storage.get("schema", schema_ident)
    if schema is None:
        return {"success": False, "error": f"schema_not_found:{schema_ident}"}

    # Contraintes (toutes, formatées en liste)
    constraint_list = "\n".join(
        f"- {c.get('constraint_statement', '')}"
        for c in storage.get_all("constraint").values()
    )

    # Expected output
    expected_output = storage.get("expected_output", "expected_output_json_object")
    expected_output_description = (
        expected_output.get("expected_output_description", "") if expected_output else ""
    )

    # Exemple depuis le catalog
    example = _find_example(schema_ident, storage)
    example_json = json.dumps(example, indent=2, ensure_ascii=False) if example else "aucun"

    # Contexte pour résolution des placeholders
    context = {
        "role_description":          role_description,
        "erk_principles":            constraint_list,
        "constraint_list":           constraint_list,
        "schema_json":               json.dumps(schema, indent=2, ensure_ascii=False),
        "params_json":               json.dumps(params, indent=2, ensure_ascii=False),
        "example_json":              example_json,
        "goal_description":          params.get("object_goal", params.get("object_lineage", "")),
        "expected_output_description": expected_output_description,
    }

    # Assemblage du prompt via resolve_template
    prompt = resolve_template(template_text, context, catalog)

    if verbose:
        print(f"  [agent]   {agent_ident} — schema:{schema_ident} lineage:{params.get('object_lineage','?')}")

    # Appel IA
    ai_result = execute(model_type, prompt, {"max_tokens": 2048}, catalog)
    if not ai_result.get("success"):
        return {"success": False, "error": ai_result.get("error"), "stage": "prompt_execute"}

    # Parser la réponse JSON
    generated = _parse_json(ai_result.get("content", ""))
    if generated is None:
        return {
            "success": False,
            "error":   "invalid_json_response",
            "raw":     ai_result.get("content", "")[:500],
        }

    # Valider contre le schema
    validate_result = validate_object_vs_schema(generated, schema)

    if verbose:
        status = "OK" if validate_result.get("success") else "FAIL"
        score  = validate_result.get("score", 0)
        print(f"  [{status}]   Validation L1 — score {score}%")
        if not validate_result.get("success"):
            for f in validate_result.get("failures", []):
                print(f"         x {f.get('field')} : {f.get('detail')}")

    return {
        "success":          validate_result.get("success", False),
        "generated_object": generated,
        "validate_result":  validate_result,
        "usage":            ai_result.get("usage", {}),
        "schema_ident":     schema_ident,
    }


def _find_example(schema_ident, storage):
    """Cherche un objet existant utilisant ce schema comme référence."""
    for obj in storage.get_all("object").values():
        if obj.get("object_schema") == schema_ident:
            return obj
    for obj in storage.get_all("schema").values():
        if obj.get("object_schema") == schema_ident:
            return obj
    return None


def _parse_json(text):
    """Parse le JSON depuis la réponse de l'agent — robuste aux blocs markdown."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text  = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
    return None
