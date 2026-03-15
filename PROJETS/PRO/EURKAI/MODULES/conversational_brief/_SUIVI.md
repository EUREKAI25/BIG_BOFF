# conversational_brief — Suivi

## Objectif
Conversation guidée (LLM) pour transformer un brief vague en JSON structuré.
Agnostique : le prompt, la checklist et le schéma de sortie sont injectés
par le projet consommateur. Standalone, réutilisable pour tout type de brief.

## Statut
🟢 Actif — v0.1.0 (extrait de project_create)

## Architecture

```
conversational_brief/
├── conversational_brief/
│   ├── agent.py     ✅ logique principale (run_brief) — tout injectable
│   └── __init__.py  ✅ expose run_brief
└── pyproject.toml   ✅
```

## Interface publique

```python
from conversational_brief import run_brief

spec = run_brief(
    system_prompt  = Path("prompts/agent_brief.md"),  # str ou Path
    checklist      = ["REFORMULATION", "UTILISATEURS", ...],
    initial_brief  = "une marketplace de recettes",
    outdir         = Path("outputs"),
    logdir         = Path("logs"),
    registry_path  = Path("product_registry.json"),   # optionnel
    model          = "claude-haiku-4-5-20251001",      # optionnel
    api_key        = "sk-...",                         # optionnel (défaut : env)
)
```

## Paramètres injectables
| Paramètre | Obligatoire | Description |
|---|---|---|
| `system_prompt` | ✅ | Prompt système (str ou Path .md) |
| `checklist` | ✅ | Points à établir dans l'ordre |
| `initial_brief` | ➖ | Brief initial (si absent → demande interactive) |
| `outdir` | ➖ | Répertoire de sortie du JSON (défaut : `outputs/`) |
| `logdir` | ➖ | Répertoire des logs de conversation |
| `registry_path` | ➖ | Fichier JSON du registre produits (si besoin) |
| `model` | ➖ | Modèle Anthropic (défaut : `PROJECT_CREATE_MODEL` ou haiku) |
| `api_key` | ➖ | Clé API (défaut : `ANTHROPIC_API_KEY`) |

## Consommateurs
| Projet | Prompt | Checklist | Output |
|---|---|---|---|
| `project_create` | `prompts/agent_brief.md` | 7 points (REFORMULATION → VALIDATION) | `project.json` |

## Historique
| Date | Action |
|---|---|
| 2026-03-15 | Extraction depuis project_create/brief.py → module EURKAI standalone |

## Prochaines étapes
- [ ] Tests unitaires (mock LLM)
- [ ] Mode non-interactif (input fourni programmatiquement — pour tests et pipeline)
- [ ] Endpoint FastAPI optionnel (`POST /v1/brief/message`) pour usage web
