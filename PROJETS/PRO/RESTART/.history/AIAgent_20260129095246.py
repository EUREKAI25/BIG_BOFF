# AIAgent.py
# =============================================================================
# Minimal AI Agent layer
# - AIAgent.choose(options, rules)
# - AIAgent.validate(datas, rules)
# - AIAgent.score(data, rules)
# Each method:
#   1) builds a prompt from a dedicated template
#   2) calls model_execute(type_model="text", prompt=..., datas=...)
#   3) parses strict JSON output
# =============================================================================

import json
from typing import Any, Dict, List, Optional

from Model import model_execute  # assumes your Model.py is in PYTHONPATH


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Tries to parse JSON from:
    - pure JSON string
    - or JSON embedded in text (first {...} block)
    """
    if not text:
        return None

    text = text.strip()

    # 1) direct parse
    try:
        out = json.loads(text)
        if isinstance(out, dict):
            return out
        return {"result": out}
    except Exception:
        pass

    # 2) find first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = text[start : end + 1]
        try:
            out = json.loads(chunk)
            if isinstance(out, dict):
                return out
            return {"result": out}
        except Exception:
            return None

    return None


# -----------------------------------------------------------------------------
# Prompt templates (dedicated per method)
# -----------------------------------------------------------------------------
# Keep them as strings; no hardcoded logic elsewhere.

PROMPT_TEMPLATES: Dict[str, str] = {
    "choose": """You are a decision agent.
You must pick the SINGLE best option id from the provided list, based strictly on the rules.

RULES:
{rules_json}

OPTIONS (list of objects, each has at least an "id" and "label"):
{options_json}

OUTPUT (STRICT JSON ONLY, no extra text):
{{
  "result": "<id>" | "none",
  "reason": "<short explanation>",
  "confidence": <number between 0 and 1>
}}
""",

    "validate": """You are a validation agent.
You must validate the provided datas against the rules. Be strict and practical.

RULES:
{rules_json}

DATAS:
{datas_json}

OUTPUT (STRICT JSON ONLY, no extra text):
{{
  "ok": true | false,
  "missing": [<string>],
  "issues": [<string>],
  "suggestions": [<string>]
}}
""",

    "score": """You are a scoring agent.
You must score the provided data according to the rules. Provide sub-scores if relevant.

RULES:
{rules_json}

DATA:
{data_json}

OUTPUT (STRICT JSON ONLY, no extra text):
{{
  "score": <number 0..100>,
  "subscores": {{ "<dimension>": <number 0..100> }},
  "reason": "<short explanation>",
  "improvements": [<string>]
}}
""",
}


def render_prompt(template_name: str, **kwargs) -> str:
    if template_name not in PROMPT_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")
    tpl = PROMPT_TEMPLATES[template_name]
    return tpl.format(**kwargs)


# -----------------------------------------------------------------------------
# Agent
# -----------------------------------------------------------------------------

class AIAgent:
    """
    Minimal agent that delegates to model_execute("text", prompt, datas)
    """

    def __init__(self, name: str, type_model: str = "text", model_name: Optional[str] = None):
        self.name = name
        self.type_model = type_model
        self.model_name = model_name  # if None: uses default model of this type

    # ---------------------------
    # Public methods
    # ---------------------------

    def choose(self, options: List[Dict[str, Any]], rules: Dict[str, Any]) -> Dict[str, Any]:
        prompt = render_prompt(
            "choose",
            rules_json=_json_dumps(rules),
            options_json=_json_dumps(options),
        )

        res = model_execute(self.type_model, prompt, datas={"options": options, "rules": rules}, model_name=self.model_name)
        text = self._extract_text(res)
        out = _extract_json(text)

        if not out or "result" not in out:
            return {
                "ok": False,
                "error": "MODEL_OUTPUT_NOT_JSON_OR_MISSING_RESULT",
                "raw_text": text,
                "raw_model_response": res,
            }

        return {
            "ok": True,
            "result": out.get("result"),
            "reason": out.get("reason", ""),
            "confidence": out.get("confidence", None),
            "raw": out,
        }

    def validate(self, datas: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        prompt = render_prompt(
            "validate",
            rules_json=_json_dumps(rules),
            datas_json=_json_dumps(datas),
        )

        res = model_execute(self.type_model, prompt, datas={"datas": datas, "rules": rules}, model_name=self.model_name)
        text = self._extract_text(res)
        out = _extract_json(text)

        if not out or "ok" not in out:
            return {
                "ok": False,
                "error": "MODEL_OUTPUT_NOT_JSON_OR_MISSING_OK",
                "raw_text": text,
                "raw_model_response": res,
            }

        # Normalize fields
        out.setdefault("missing", [])
        out.setdefault("issues", [])
        out.setdefault("suggestions", [])

        return out

    def score(self, data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        prompt = render_prompt(
            "score",
            rules_json=_json_dumps(rules),
            data_json=_json_dumps(data),
        )

        res = model_execute(self.type_model, prompt, datas={"data": data, "rules": rules}, model_name=self.model_name)
        text = self._extract_text(res)
        out = _extract_json(text)

        if not out or "score" not in out:
            return {
                "ok": False,
                "error": "MODEL_OUTPUT_NOT_JSON_OR_MISSING_SCORE",
                "raw_text": text,
                "raw_model_response": res,
            }

        # Normalize
        out.setdefault("subscores", {})
        out.setdefault("reason", "")
        out.setdefault("improvements", [])

        return out

    # ---------------------------
    # Internals
    # ---------------------------

    def _extract_text(self, model_response: Dict[str, Any]) -> str:
        """
        Assumes your models return:
          { "output": {"text": "..."} }
        Adjust here if your provider returns a different shape.
        """
        if not isinstance(model_response, dict):
            return ""
        output = model_response.get("output", {})
        if isinstance(output, dict) and "text" in output and isinstance(output["text"], str):
            return output["text"]
        # fallback: stringify
        return str(model_response)


# -----------------------------------------------------------------------------
# Example usage
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # assumes you already bootstrapped models somewhere OR your Model.py does lazy bootstrap
    agent = AIAgent(name="decision_agent", type_model="text")  # default text model

    options = [
        {"id": "a", "label": "Generate 4 keyframes"},
        {"id": "b", "label": "Generate 1 keyframe + extend to video"},
        {"id": "c", "label": "Ask user for more details"},
    ]

    rules = {
        "goal": "Produce the most realistic short video pipeline",
        "constraints": ["minimize user steps", "maximize identity consistency"],
        "must_avoid": ["long explanations", "vague outputs"],
    }

    print("CHOOSE:", agent.choose(options, rules))

    datas = {"dream": "Tomber amoureux à Rome", "duration_sec": 15}
    validate_rules = {"required": ["dream", "duration_sec"], "duration_range": [5, 90]}
    print("VALIDATE:", agent.validate(datas, validate_rules))

    score_data = {"prompt": "A cinematic meet-cute in Rome at sunset...", "len": 72}
    score_rules = {"criteria": {"clarity": 0.4, "cinematic": 0.4, "constraints_match": 0.2}}
    print("SCORE:", agent.score(score_data, score_rules))
