# MODEL_EXECUTOR

> Interface universelle pour appeler n'importe quel modèle IA avec une méthode unique

## Description

MODULE_EXECUTOR est un module EURKAI qui abstrait tous les appels aux modèles IA derrière une interface unique : `model_execute(model_type, prompt, data)`.

**Principe** : Un seul point d'entrée pour tous les modèles, quelle que soit la technologie (OpenAI, Anthropic, Flux, MiniMax, etc.).

## Avantages

✅ **Interface unique** : `model_execute()` pour tous les types de modèles
✅ **Configuration centralisée** : `config.yaml` définit quel provider pour quel type
✅ **Flexibilité** : changer de provider sans modifier le code
✅ **Fallback automatique** : si provider principal échoue, essaie le fallback
✅ **Métriques unifiées** : coût, temps, tokens pour tous les providers

## Installation

```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/EURKAI/MODULES/MODEL_EXECUTOR
pip install -r requirements.txt
```

## Configuration

Éditer `config.yaml` pour définir les providers actifs :

```yaml
model_types:
  text2text:
    active: openai
    fallback: anthropic
  text2img:
    active: replicate
    fallback: openai
  img2video:
    active: minimax
```

Les clés API sont chargées depuis `~/.bigboff/secrets.env`.

## Utilisation

### Import

```python
from eurkai.modules.model_executor import model_execute
```

### Exemples

#### Text → Text (GPT-4)
```python
result = model_execute(
    model_type="text2text",
    prompt="Écris un poème sur Paris",
    data={}
)
print(result["text"])
```

#### Text → Image (Flux)
```python
result = model_execute(
    model_type="text2img",
    prompt="A beautiful sunset over Paris, cinematic",
    data={
        "width": 1024,
        "height": 768,
        "steps": 30
    }
)
print(result["image_url"])
```

#### Image → Video (MiniMax)
```python
result = model_execute(
    model_type="img2video",
    prompt="Camera slowly zooms in on the Eiffel Tower",
    data={
        "image_url": "https://example.com/paris.jpg",
        "duration": 6
    }
)
print(result["video_url"])
```

#### Override provider
```python
# Force OpenAI DALL-E au lieu de Flux
result = model_execute(
    model_type="text2img",
    prompt="A beautiful sunset over Paris",
    data={},
    provider="openai"  # Override config
)
```

## Types de modèles supportés

| Type | Description | Providers |
|---|---|---|
| `text2text` | Génération de texte (LLM) | openai, anthropic, gemini |
| `text2img` | Génération d'images depuis texte | replicate, openai, fal |
| `img2text` | Description d'image (vision) | openai, gemini, anthropic |
| `img2video` | Génération vidéo depuis image | minimax, runway |
| `text2audio` | Génération audio/voix | elevenlabs, openai |
| `text2video` | Génération vidéo depuis texte | runway |
| `audio2text` | Transcription audio | openai |
| `img2img` | Transformation d'image | replicate |

## Métadonnées retournées

Chaque appel retourne :

```python
{
    "result": "...",  # Résultat spécifique au type
    "metadata": {
        "provider": "openai",
        "model": "gpt-4o",
        "cost_usd": 0.02,
        "duration_seconds": 1.5,
        "tokens_input": 100,
        "tokens_output": 200
    }
}
```

## Architecture

```
MODEL_EXECUTOR/
├── config.yaml           # Configuration providers
├── src/
│   ├── executor.py       # Interface principale
│   ├── config.py         # Chargement config
│   └── providers/
│       ├── base.py       # Classe abstraite Provider
│       ├── openai.py     # Provider OpenAI
│       ├── anthropic.py  # Provider Anthropic
│       ├── replicate.py  # Provider Replicate
│       ├── minimax.py    # Provider MiniMax
│       └── ...
```

## Ajouter un nouveau provider

1. Créer `src/providers/mon_provider.py` héritant de `BaseProvider`
2. Implémenter les méthodes requises
3. Ajouter dans `config.yaml`

Exemple :

```python
# src/providers/mon_provider.py
from .base import BaseProvider

class MonProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__("mon_provider", api_key)

    def text2text(self, prompt: str, data: dict) -> dict:
        # Implémentation
        pass
```

## Module EURKAI

Ce module suit les standards EURKAI :
- Identifiant : `module_model_executor`
- Endpoint : `/api/model/execute`
- Héritage : `Object` (ident, created_at, version, validate(), test())
- Réutilisable par tous les projets EURKAI
