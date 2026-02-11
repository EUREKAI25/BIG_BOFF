"""
MODEL_EXECUTOR — Interface principale
model_execute(model_type, prompt, data, provider=None)
"""

import time
from typing import Dict, Any, Optional
from .config import config


def model_execute(
    model_type: str,
    prompt: str,
    data: Dict[str, Any] = None,
    provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Interface universelle pour appeler n'importe quel modèle IA.

    Args:
        model_type: Type (text2text, text2img, img2video, etc.)
        prompt: Prompt ou instruction
        data: Données complémentaires (optionnel)
        provider: Provider spécifique (override config, optionnel)

    Returns:
        {
            "result": ...,  # Résultat (texte, URL, etc.)
            "metadata": {
                "provider": "...",
                "model": "...",
                "cost_usd": 0.0,
                "duration_seconds": 0.0
            }
        }

    Exemples:
        >>> result = model_execute("text2text", "Écris un poème")
        >>> result = model_execute("text2img", "A sunset", {"width": 1024})
        >>> result = model_execute("img2video", "Zoom in", {"image_url": "..."})
    """
    if data is None:
        data = {}

    # Déterminer provider
    if provider is None:
        provider = config.get_active_provider(model_type)
        if not provider:
            raise ValueError(f"Type de modèle inconnu : {model_type}")

    fallback = config.get_fallback_provider(model_type)

    # Tenter avec provider actif
    try:
        start = time.time()
        result = _execute_with_provider(provider, model_type, prompt, data)
        result["metadata"]["duration_seconds"] = round(time.time() - start, 2)
        return result

    except Exception as e:
        if fallback:
            print(f"⚠️  {provider} échoué, tentative fallback {fallback}: {e}")
            try:
                start = time.time()
                result = _execute_with_provider(fallback, model_type, prompt, data)
                result["metadata"]["duration_seconds"] = round(time.time() - start, 2)
                return result
            except Exception as e2:
                raise RuntimeError(f"Tous les providers ont échoué : {e} | {e2}")
        else:
            raise RuntimeError(f"Provider {provider} échoué et pas de fallback : {e}")


def _execute_with_provider(provider: str, model_type: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Exécute avec un provider spécifique."""

    # Charger API key et modèle
    api_key = config.get_api_key(provider)
    model = config.get_model_name(provider, model_type)

    if not model:
        raise ValueError(f"Provider {provider} ne supporte pas {model_type}")

    # Importer et instancier le provider
    if provider == "openai":
        from .providers.openai_provider import OpenAIProvider
        p = OpenAIProvider(api_key)
    elif provider == "anthropic":
        from .providers.anthropic_provider import AnthropicProvider
        p = AnthropicProvider(api_key)
    # ... autres providers à ajouter au fur et à mesure
    else:
        raise NotImplementedError(f"Provider {provider} pas encore implémenté")

    # Exécuter
    return p.execute(model_type, model, prompt, data)
