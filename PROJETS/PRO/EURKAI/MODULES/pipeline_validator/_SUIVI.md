# _SUIVI — Module `pipeline_validator`

> Prévalidation externe de pipelines de modules EURKAI
> Créé le : 2026-03-14
> **Temporaire MVP** — sera remplacé par les SuperTools

---

## Statut

🟢 Actif — implémentation initiale complète

---

## Rôle

Vérifier si une séquence de modules peut être chaînée **avant exécution**.

Règle unique : `outputs(A) ∩ inputs(B) ≠ ∅` pour chaque transition.

Les modules restent des boîtes noires. Toute la logique est externe.

---

## Fichiers

| Fichier | Rôle |
|---|---|
| `contracts.py` | `ContractRegistry` + `_STATIC_CONTRACTS` — source de vérité des contrats |
| `validator.py` | `PipelineValidator` — algorithme de validation O(n) |
| `router.py` | Router FastAPI — `POST /v1/pipeline/prevalidate` + endpoints bonus |
| `__init__.py` | Exports publics |

---

## Endpoints

| Méthode | Path | Rôle |
|---|---|---|
| `POST` | `/v1/pipeline/prevalidate` | Valider un pipeline |
| `GET` | `/v1/pipeline/contracts` | Lister tous les contrats connus |
| `GET` | `/v1/pipeline/contracts/{id}/next` | Modules compatibles après |
| `GET` | `/v1/pipeline/contracts/{id}/prev` | Modules compatibles avant |

---

## Ajouter un module

Ouvrir `contracts.py` et ajouter une entrée dans `_STATIC_CONTRACTS` :

```python
"mon_module": ModuleContract(
    module_id    = "mon_module",
    input_datas  = ["ThemeTokens"],
    output_datas = ["CssBundle"],
    description  = "...",
),
```

Alternativement : ajouter `input_datas` et `output_datas` dans le `MANIFEST.json` du module.
La registry les chargera automatiquement au démarrage.

---

## Intégration FastAPI

```python
from pipeline_validator.router import router as pipeline_router
app.include_router(pipeline_router, prefix="/v1")
```

---

## Suppression prévue

Ce module sera supprimé quand les SuperTools prendront en charge la validation de pipelines.
Ne pas investir dans des fonctionnalités complexes ici.

---

## Historique

| Date | Action |
|---|---|
| 2026-03-14 | Création — contracts.py, validator.py, router.py |
