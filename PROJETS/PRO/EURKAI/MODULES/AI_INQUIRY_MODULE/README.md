# AI_INQUIRY_MODULE

**Module EURKAI agnostique** — Interroge plusieurs IA, extrait les citations, détecte la présence d'un prospect.

Version : `0.1.0`

---

## Fonction principale

```python
from AI_INQUIRY_MODULE import run

result = run(
    payload={"profession": "couvreur", "city": "Rennes", "prospect_name": "Toit Breton"},
    question_prompt="Quels sont les meilleurs {profession}s à {city} ?",
    poll_inquiry_datas={"city": "Brest"},  # optionnel
    output_format="json",                  # optionnel
    dry_run=False,                         # True pour test sans appel IA
)
```

---

## Inputs

| Paramètre | Type | Requis | Description |
|---|---|---|---|
| `payload` | dict | ✅ | Variables du template + `prospect_name`, `website` optionnels |
| `question_prompt` | str | ✅ | Template avec `{clés}` remplacées par `payload` |
| `poll_inquiry_datas` | dict | ➖ | Variantes supplémentaires à tester |
| `output_format` | str | ➖ | `"json"` (défaut) |
| `dry_run` | bool | ➖ | `True` = pas d'appel IA réel (simulé) |

### Clés payload reconnues

| Clé | Rôle |
|---|---|
| `profession` | Métier à rechercher |
| `city` | Ville cible |
| `prospect_name` | Nom du prospect (pour présence_check) |
| `website` / `prospect_website` | URL du prospect (pour exclusion + matching domaine) |

---

## Output — Contrat uniforme EURKAI

```json
{
  "success": true,
  "result": {
    "inquiry_dict": {
      "questions": ["Quels sont les meilleurs couvreurs à Rennes ?"],
      "payload": {"profession": "couvreur", "city": "Rennes", "prospect_name": "Toit Breton"}
    },
    "answers": [
      {"model": "openai", "question": "...", "answer": "...", "ts": "2026-02-20T..."}
    ],
    "citations": [
      {"type": "company", "value": "Couverture Bretonne", "from_model": "openai"},
      {"type": "url", "value": "https://concurrent.fr", "domain": "concurrent.fr", "from_model": "gemini"}
    ],
    "prospect_present": false,
    "competitors": ["Couverture Bretonne", "concurrent.fr"],
    "meta": {
      "models": ["openai", "anthropic", "gemini"],
      "ts": ["2026-02-20T10:00:00Z", "2026-02-20T10:00:05Z"],
      "dry_run": false
    }
  },
  "message": "3 réponse(s) collectée(s), 2 citation(s) extraite(s)",
  "error": null
}
```

### En cas d'erreur

```json
{
  "success": false,
  "result": null,
  "message": "Erreur inattendue dans AI_INQUIRY_MODULE",
  "error": {"code": "INTERNAL_ERROR", "detail": "..."}
}
```

---

## 4 étapes internes

```
payload + question_prompt
        │
        ▼
1. prompt_generate()  → inquiry_dict (questions générées)
        │
        ▼
2. ask_ia()           → answers (appels OpenAI / Anthropic / Gemini)
        │
        ▼
3. extract_citations() → citations (entités extraites, dédupliquées)
        │
        ▼
4. presence_check()   → prospect_present (bool) + competitors (list)
```

---

## Variables d'environnement

| Variable | Modèle activé |
|---|---|
| `OPENAI_API_KEY` | gpt-4o-mini |
| `ANTHROPIC_API_KEY` | claude-haiku-4-5-20251001 |
| `GEMINI_API_KEY` | gemini-2.0-flash |

Seuls les modèles avec une clé configurée sont utilisés. Sans aucune clé → 0 réponse.

---

## Endpoint PRESENCE_IA

`POST /api/ai-inquiry/run`

### Requête

```json
{
  "payload": {
    "profession": "couvreur",
    "city": "Rennes",
    "prospect_name": "Toit Breton",
    "website": "https://toitbreton.fr"
  },
  "question_prompt": "Quels sont les meilleurs {profession}s à {city} ? Citez des noms.",
  "poll_inquiry_datas": {"city": "Brest"},
  "dry_run": false
}
```

### Exemples curl

**Appel réel :**
```bash
curl -X POST http://localhost:8001/api/ai-inquiry/run \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"profession": "couvreur", "city": "Rennes", "prospect_name": "Toit Breton"},
    "question_prompt": "Quels sont les meilleurs {profession}s à {city} ? Citez des entreprises.",
    "dry_run": false
  }'
```

**Dry run (test sans appel IA) :**
```bash
curl -X POST http://localhost:8001/api/ai-inquiry/run \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"profession": "plombier", "city": "Lyon", "prospect_name": "Plomb Sud"},
    "question_prompt": "Meilleurs {profession}s à {city} ?",
    "dry_run": true
  }'
```

**Avec variantes (poll) :**
```bash
curl -X POST http://localhost:8001/api/ai-inquiry/run \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"profession": "electricien", "city": "Bordeaux"},
    "question_prompt": "Recommandez des {profession}s à {city}.",
    "poll_inquiry_datas": {"city": "Mérignac"},
    "dry_run": false
  }'
```

---

## Tests

```bash
cd TESTS/
pytest test_module.py -v
```

Tests couverts :
- Normalisation (`norm`, accents, suffixes légaux)
- Matching flou (`is_mentioned`)
- Extraction entités + dédoublonnage
- Filtrage stopwords (Google, Maps, Facebook...)
- `competitors_from` (exclusion prospect + website)
- `prompt_generate` (template + variantes + clé manquante)
- `ask_ia` en dry_run (3 modèles × N questions)
- `extract_citations` (tag `from_model`, dédoublonnage cross-modèles)
- `presence_check` (trouvé / non trouvé)
- `run()` intégration complète en dry_run
- Contrat uniforme EURKAI respecté
- Erreur gracieuse (success=False, error.code=INTERNAL_ERROR)

---

## Intégration EURKAI

Ce module est agnostique : pas de dépendance à SQLAlchemy, PRESENCE_IA ou toute autre BDD.
Il peut être importé directement ou exposé comme service FastAPI autonome.

Consommé par :
- **PRESENCE_IA** via `POST /api/ai-inquiry/run`
- Tout projet EURKAI ayant besoin d'interroger des IA sur un secteur + prospect
