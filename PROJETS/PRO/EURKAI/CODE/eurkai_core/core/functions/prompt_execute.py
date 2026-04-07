"""
prompt_execute — méthode universelle d'appel IA.
Signature : prompt_execute(model_type, prompt, params, catalog)
Principe : jamais de provider hardcodé. Le modèle est résolu depuis le catalog.
           La clé API est chargée depuis secrets.env au runtime — jamais loggée.
"""

import os
from pathlib import Path

_ENV_PATH = Path("/Users/nathalie/Dropbox/____BIG_BOFF___/.env")


def prompt_execute(what, catalog):
    """
    Point d'entrée MRG.
    what doit contenir : model_type, prompt_text, prompt_params (optionnel)
    """
    model_type    = what.get("model_type", "llm")
    prompt_text   = what.get("prompt_text", "")
    prompt_params = what.get("prompt_params", {})

    result = execute(model_type, prompt_text, prompt_params, catalog)
    return {"success": True, "prompt_execute_result": result, "what": what}


def execute(model_type, prompt, params=None, catalog=None):
    """
    Fonction utilitaire directe — utilisable sans passer par la MRG.
    Résout le modèle depuis catalog, charge la clé depuis .env, appelle l'API.
    """
    params = params or {}
    model  = _resolve_model(model_type, catalog)

    if model is None:
        return {"success": False, "error": f"model_not_found:type={model_type}"}

    provider = model.get("model_provider")
    version  = model.get("model_version")

    _load_env()

    if provider == "anthropic":
        return _call_anthropic(version, prompt, params)
    else:
        return {"success": False, "error": f"provider_not_supported:{provider}"}


def _resolve_model(model_type, catalog):
    """Résout le modèle depuis catalog_ai_model_list par model_type."""
    if catalog is None:
        return None
    storage = catalog.get("_storage")
    if storage is None:
        return None
    models = storage.get_all("ai_model")
    # Priorité : modèle actif correspondant au type
    for m in models.values():
        if m.get("model_type") == model_type and m.get("model_active", True):
            return m
    return None


def _load_env():
    """Charge .env dans os.environ si les clés ne sont pas déjà présentes."""
    if not _ENV_PATH.exists():
        return
    with open(_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _call_anthropic(model_version, prompt, params):
    """Appelle l'API Anthropic. La clé n'est jamais loggée."""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"success": False, "error": "ANTHROPIC_API_KEY:missing"}

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=model_version,
        max_tokens=params.get("max_tokens", 4096),
        temperature=params.get("temperature", 1),
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "success":       True,
        "provider":      "anthropic",
        "model_version": model_version,
        "content":       message.content[0].text,
        "usage": {
            "input_tokens":  message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
        },
    }
