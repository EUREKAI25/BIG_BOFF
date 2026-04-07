"""
agent_extract_rules
Extrait les règles et méthodes depuis un document source.
Tout le contenu textuel vient du catalog (role, template, expected_output).
Python = exécuteur uniquement.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run(source_document, catalog, model_type="llm", verbose=True,
        agent_ident="agent_extract_rules"):
    """
    Extrait rules + methods depuis source_document.
    Retourne : dict avec rule_list, method_list, success.
    """
    from core.functions.prompt_execute import execute
    from core.functions.placeholder_resolve import resolve_template

    storage = catalog["_storage"]

    agent = storage.get("agent", agent_ident)
    if agent is None:
        return {"success": False, "error": f"agent_not_found:{agent_ident}"}

    role = storage.get("role", agent.get("agent_role", ""))
    role_description = role.get("role_description", "") if role else ""

    template_ident  = agent.get("agent_prompt_template", "template_extract_rules")
    prompt_template = storage.get("prompt_template", template_ident)
    if prompt_template is None:
        return {"success": False, "error": f"prompt_template_not_found:{template_ident}"}

    expected_output = storage.get("expected_output", "expected_output_rule_list")
    expected_output_description = (
        expected_output.get("expected_output_description", "") if expected_output else ""
    )

    context = {
        "role_description":            role_description,
        "source_document":             source_document,
        "expected_output_description": expected_output_description,
    }

    prompt = resolve_template(prompt_template.get("prompt_template_text", ""), context, catalog)

    if verbose:
        preview = source_document[:80].replace("\n", " ")
        print(f"  [agent]   {agent_ident} — document: {preview}…")

    ai_result = execute(model_type, prompt, {"max_tokens": 4096}, catalog)
    if not ai_result.get("success"):
        return {"success": False, "error": ai_result.get("error"), "stage": "prompt_execute"}

    extracted = _parse_json(ai_result.get("content", ""))
    if extracted is None:
        return {
            "success": False,
            "error":   "invalid_json_response",
            "raw":     ai_result.get("content", "")[:500],
        }

    rule_list   = extracted.get("rule_list", [])
    method_list = extracted.get("method_list", [])

    if verbose:
        print(f"  [OK]   {len(rule_list)} règles + {len(method_list)} méthodes extraites")

    return {
        "success":     True,
        "rule_list":   rule_list,
        "method_list": method_list,
        "usage":       ai_result.get("usage", {}),
    }


def _parse_json(text):
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
