# EURKAI — Architecture orientée objets

**Créé** : 2026-02-10
**Version** : 1.0.0

---

## Principe fondamental

**TOUT est objet** dans EURKAI, y compris les attributs d'objets.

Un objet = **Type** (dans `catalogs/`) + **Instance** (dans `instances/`)

---

## Notation GEV

Convention d'écriture des relations d'héritage et d'attributs :

### Héritage
```
Object:Model           → Model hérite de Object
Object:Core:Model      → Model dans le namespace core, hérite de Object
Object:Core:Model:TextToTextModel  → TextToTextModel hérite de Model
```

### Attributs
```
Output.price                    → Attribut price de l'objet Output
Model.output                    → Attribut output de l'objet Model (override Output)
Model.ai_provider               → Attribut ai_provider (qui est Object:Entity:Company:AIProvider)
Result.token_amount             → Attribut token_amount de l'objet Result
```

---

## Hiérarchie des objets

```
Object (racine universelle)
├── ident           (string)
├── created_at      (datetime)
├── version         (string)
├── validate()      (method)
├── test()          (method)
└── serialize()     (method)

Object:Entity
├── Object:Entity:User
├── Object:Entity:Contact
├── Object:Entity:Company
│   └── Object:Entity:Company:AIProvider  (OpenAI, Anthropic, etc.)
└── Object:Entity:Agent
    ├── HumanAgent      (admin, client, opérateur, visiteur)
    ├── ServiceAgent    (billing, notifier, scheduler)
    ├── SystemAgent     (cron, watcher, orchestrator, dispatcher)
    ├── ExternalAgent   (Stripe, Brevo, GitHub, API tierce)
    ├── ScriptAgent     (script autonome, job batch)
    └── RuleAgent       (moteur de règles déterministes)

Object:Core
├── Object:Core:Function
├── Object:Core:Method
├── Object:Core:Scenario
├── Object:Core:Input
├── Object:Core:Output
│   ├── .result         (any)
│   ├── .price          (float)
│   └── .duration_seconds (float)
├── Object:Core:Template
└── Object:Core:Model
    ├── .ai_provider    (Object:Entity:Company:AIProvider)
    ├── .output         (Object:Core:Output, override avec token_amount)
    ├── .execute()      (method)
    ├── Object:Core:Model:TextToTextModel
    │   └── .execute()  (override, gère text2text)
    ├── Object:Core:Model:TextToImageModel
    │   └── .execute()  (override, gère text2img)
    ├── Object:Core:Model:ImageToTextModel
    ├── Object:Core:Model:ImageToVideoModel
    ├── Object:Core:Model:TextToAudioModel
    ├── Object:Core:Model:TextToVideoModel
    ├── Object:Core:Model:AudioToTextModel
    └── Object:Core:Model:ImageToImageModel

Object:Domain
├── Object:Domain:Product
├── Object:Domain:Service
├── Object:Domain:Price
├── Object:Domain:Offer
└── Object:Domain:BillingObject

Object:Governance
├── Object:Governance:Auth
├── Object:Governance:Role
├── Object:Governance:Permission
├── Object:Governance:Policy
└── Object:Governance:Rule

Object:Flow
├── Object:Flow:Event
├── Object:Flow:Process
├── Object:Flow:Hook
├── Object:Flow:Cron
└── Object:Flow:Workflow

Object:Interface
├── Object:Interface:API
├── Object:Interface:Endpoint
├── Object:Interface:Form
└── Object:Interface:Catalog  (PAS d'Adapter — override methods à la place)

Object:System
├── Object:System:Server
├── Object:System:Path
├── Object:System:Storage
└── Object:System:Runtime

Object:Config
├── Object:Config:Context
├── Object:Config:Env
├── Object:Config:Settings
├── Object:Config:Meta
└── Object:Config:Schema

Object:Util
├── Object:Util:Formatter
├── Object:Util:Converter
├── Object:Util:Validator
└── Object:Util:Helper
```

---

## Override de méthodes (pas d'Adapters)

**Principe EURKAI** : Chaque objet porte ses méthodes qui overrident celles du parent.

**PAS d'adapter pattern** → les méthodes spécialisées sont dans l'objet lui-même.

### Exemple : Model.execute()

```
Object:Core:Model
└── execute(prompt, data) → méthode abstraite

Object:Core:Model:TextToTextModel
└── execute(prompt, data) → override, appelle API OpenAI/Anthropic/etc.

Object:Core:Model:ImageToVideoModel
└── execute(prompt, data) → override, appelle API MiniMax/Runway/etc.
```

**Pas besoin d'adapter** : chaque modèle sait comment s'exécuter lui-même.

---

## Structure fichiers

### `catalogs/` — Définitions de TYPES

```
EURKAI/catalogs/
├── core/
│   ├── model/
│   │   ├── Model/manifest.json                    (type de base)
│   │   ├── TextToTextModel/manifest.json          (extends Model)
│   │   ├── TextToImageModel/manifest.json         (extends Model)
│   │   └── ImageToVideoModel/manifest.json        (extends Model)
│   └── output/
│       └── Output/manifest.json                   (type générique)
└── entity/
    └── company/
        └── AIProvider/manifest.json               (type provider IA)
```

### `instances/` — Objets CONCRETS

```
EURKAI/instances/
├── core/
│   └── model/
│       ├── gpt4o.json                 (instance de TextToTextModel)
│       ├── flux_pro.json              (instance de TextToImageModel)
│       └── minimax_video01.json       (instance de ImageToVideoModel)
└── entity/
    └── company/
        ├── openai.json                (instance de AIProvider)
        ├── anthropic.json             (instance de AIProvider)
        └── replicate.json             (instance de AIProvider)
```

---

## Format manifest.json

Chaque type a un `manifest.json` définissant :

```json
{
  "ident": "core.model.TextToTextModel",
  "type": "Object:Core:Model:TextToTextModel",
  "extends": "Object:Core:Model",
  "created_at": "2026-02-10",
  "version": "1.0.0",
  "description": "Modèle de génération de texte (LLM)",

  "attributes_override": {
    "model_type": {
      "type": "string",
      "fixed": "text2text"
    },
    "output": {
      "type": "Object:Core:Output",
      "schema": {
        "result": {
          "text": "string",
          "finish_reason": "string"
        },
        "token_amount": {
          "input": "integer",
          "output": "integer",
          "total": "integer"
        }
      }
    }
  },

  "methods_override": {
    "execute": {
      "description": "Génère du texte depuis un prompt",
      "parameters": {
        "prompt": "string | array<message>",
        "data": "object"
      },
      "returns": "Object:Core:Output"
    }
  }
}
```

---

## Format instance.json

Chaque instance concrète :

```json
{
  "ident": "model_gpt4o",
  "type": "Object:Core:Model:TextToTextModel",
  "created_at": "2026-02-10T21:00:00Z",
  "version": "1.0.0",

  "name": "gpt-4o",
  "ai_provider": "ai_provider_openai",
  "model_type": "text2text",

  "pricing": {
    "input": 0.005,
    "output": 0.015
  },

  "context_window": 128000,
  "max_output_tokens": 4096,

  "output": {
    "result": {
      "text": "",
      "finish_reason": ""
    },
    "token_amount": {
      "input": 0,
      "output": 0,
      "total": 0
    },
    "price": 0.0,
    "duration_seconds": 0.0
  }
}
```

---

## Utilisation

### Charger un modèle
```python
# Charger instance depuis instances/core/model/gpt4o.json
model = load_instance("model_gpt4o")

# model est de type Object:Core:Model:TextToTextModel
# model.ai_provider pointe vers ai_provider_openai
# model.output est Object:Core:Output avec token_amount
```

### Exécuter un modèle
```python
# Appeler execute() défini dans TextToTextModel
result = model.execute(
    prompt="Écris un poème",
    data={"temperature": 0.7}
)

# result est Object:Core:Output
# result.result.text contient le texte généré
# result.token_amount.total contient les tokens consommés
# result.price contient le coût en USD
```

---

## Tracking consommation

**Automatique via Output** :

Chaque `Object:Core:Model.output` est `Object:Core:Output` avec :
- `Output.price` (float USD)
- `Output.duration_seconds` (float)
- `Result.token_amount` (si applicable, null sinon)

**Model.output override Output** pour ajouter :
- `token_amount.input` (integer)
- `token_amount.output` (integer)
- `token_amount.total` (integer)

**Function.output override Output** également, mais peut avoir d'autres attributs selon le type de fonction.

---

## Catalogues

Les **providers** et **modèles** sont définis dans des catalogues JSON séparés.

**Catalog** est lui-même un objet (`Object:Interface:Catalog`) avec :
- `Catalog.items` (array d'objets)
- `Catalog.index()` (method)
- `Catalog.search()` (method)

---

## Organisation par catégorie

```
catalogs/
├── entity/       → qui existe (user, contact, company, agent, team)
├── core/         → briques abstraites (function, method, scenario, input, output, model, template)
├── domain/       → valeur métier EURKAI (product, service, price, offer, billing_object)
├── governance/   → règles & droits (auth, role, permission, policy, rule)
├── flow/         → orchestration & temps (event, process, hook, cron, workflow)
├── interface/    → exposition & accès (api, endpoint, form, catalog)
├── system/       → infrastructure & runtime (server, path, storage, runtime)
├── config/       → contexte & méta (context, env, settings, meta, schema)
└── util/         → helpers techniques (formatter, converter, validator, helper)
```

---

## Exemple complet : appel modèle

```python
# 1. Charger provider
provider = load_instance("ai_provider_openai")
# type: Object:Entity:Company:AIProvider
# provider.api_key_env = "OPENAI_API_KEY"

# 2. Charger modèle
model = load_instance("model_gpt4o")
# type: Object:Core:Model:TextToTextModel
# model.ai_provider = "ai_provider_openai" (référence)

# 3. Exécuter (TextToTextModel.execute override Model.execute)
result = model.execute("Écris un poème", {"temperature": 0.7})
# type: Object:Core:Output
# result.result.text = "Il était une fois..."
# result.token_amount.total = 250
# result.price = 0.00375  # (100 input + 150 output) * pricing
# result.duration_seconds = 1.5

# 4. Tracking automatique
print(f"Coût: ${result.price}")
print(f"Tokens: {result.token_amount.total}")
print(f"Durée: {result.duration_seconds}s")
```

---

## Prochaines étapes

1. **Créer tous les types de modèles** (TextToVideo, AudioToText, etc.)
2. **Créer toutes les instances providers** (Replicate, MiniMax, Runway, etc.)
3. **Créer toutes les instances modèles** (Claude, Gemini, Flux, etc.)
4. **Implémenter le runtime EURKAI** qui charge et exécute depuis les catalogues
5. **Créer les outils de gestion** (CLI, UI) pour manipuler catalogues et instances

---

**Cette architecture permet une flexibilité totale tout en maintenant une structure cohérente et traçable.** ✨
