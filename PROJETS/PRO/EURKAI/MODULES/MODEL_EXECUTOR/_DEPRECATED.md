# ⚠️ MODEL_EXECUTOR — DEPRECATED

**Date** : 2026-02-10

Ce module a été créé avant la compréhension complète de l'architecture EURKAI.

## Pourquoi deprecated ?

1. **Pas d'objets EURKAI** — utilisait des classes Python classiques
2. **Pas de catalogues** — configuration en YAML au lieu de manifests JSON
3. **Pas de respect de l'héritage** — pas de Object:Core:Model
4. **Pas de tracking Output** — pas d'objet Output avec price/token_amount
5. **Pattern adapter** — alors qu'EURKAI utilise override de méthodes

## Nouvelle implémentation

Voir : `/EURKAI/CORE/ARCHITECTURE_OBJECTS.md`

**Structure correcte** :

```
EURKAI/
├── catalogs/
│   ├── core/model/           → Types de modèles (manifests)
│   └── entity/company/       → Types de providers (manifests)
└── instances/
    ├── core/model/           → Instances modèles (gpt4o.json, flux_pro.json)
    └── entity/company/       → Instances providers (openai.json, anthropic.json)
```

**Hiérarchie correcte** :
- `Object:Core:Model` (base)
- `Object:Core:Model:TextToTextModel` (extends Model)
- `Object:Core:Model:TextToImageModel` (extends Model)
- etc.

**Pas d'adapters** → chaque modèle override `execute()` directement

**Tracking automatique** → via `Object:Core:Output` avec `price`, `token_amount`

---

## Migration

Le code Python actuel dans `src/` peut être utilisé temporairement, mais doit être remplacé par :

1. Runtime EURKAI qui charge depuis `catalogs/` et `instances/`
2. Classes Python générées dynamiquement depuis manifests
3. Override methods implémentées selon le type de modèle

---

**Ne pas utiliser ce module pour de nouveaux développements.**
