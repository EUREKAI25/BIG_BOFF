# EURKAI CORE — Feuille de route
Date : 2026-04-02
Mise à jour : 2026-04-02
Statut : EN COURS — Itération 4

---

## Principe d'organisation

Construction par itérations successives.
Chaque itération : construire → tester → valider la conformité → itération suivante.
Le scénario `scenario_debug_validate` est présent dès l'itération 3 et maintenu en permanence.

---

## ITÉRATION 0 — Cadre de référence ✅ TERMINÉE
**Objectif** : poser les références stables avant tout code.

| Livrable | Description | Statut |
|----------|-------------|--------|
| ERK_LANG_v1.md | Grammaire ERK (syntaxe, lineage, listes, hooks, MRG) | ✅ Fait |
| FORMULAS_v1.md | Formules atomiques pour les règles (8 catégories dont ARITHMETIC) | ✅ Fait |
| FORMULAS_v1.md complément | CONDITIONAL, TEMPORAL, TYPE | ⏳ Non-bloquant |
| GEV_LANG_v1.md | Langage des objets GEV (vocabulaire, dot notation) | ⏳ Non-bloquant |

**Sortie** : deux docs de référence stables dans `cadre/`.

---

## ITÉRATION 1 — Extraction des règles ✅ TERMINÉE
**Objectif** : extraire et normaliser toutes les règles énoncées dans les docs de cadre.

| Livrable | Description | Statut |
|----------|-------------|--------|
| `agent_extract_rules` | Prompt agent qui lit un doc et extrait les règles | ✅ `agents/agent_extract_rules.md` |
| `rule_list_cadre.json` | 87 règles + 31 méthodes extraites, normalisées | ✅ `output/rule_list_cadre.json` |
| `scenario_extract_rules` | Scénario MRG formel | ⏳ Itération future |

**Structure d'une règle extraite** :
```
rule_ident
rule_source          (nom du doc, section)
rule_type            (axiome / contrainte / interdiction / obligation)
rule_condition       (FORMULAS si applicable)
rule_severity        (error / warning / info)
rule_message
rule_justification
rule_scope           (null | * | valeur explicite — périmètre d'application)
```

**Structure d'une méthode extraite** :
```
method_ident
method_object        (objet auquel la méthode appartient)
method_type          (central | secondary)
method_parent        (CentralMethod associée si secondary)
method_input
method_output
method_scope
```

**Sortie** : rule_list complète validée — devient la référence pour le noyau.

---

## ITÉRATION 2 — Noyau catalog ✅ TERMINÉE
**Objectif** : poser les 4 objets fondamentaux en JSON/dict.

| Objet | Statut |
|-------|--------|
| `Object`, `Schema`, `Rule`, `History`, `AiModel` | ✅ `catalog_object_list` |
| `ObjectSchema`, `SchemaSchema`, `RuleSchema`, `HistorySchema`, `AiModelSchema` | ✅ `catalog_schema_list` |
| `model_claude_opus`, `model_claude_sonnet`, `model_claude_haiku` | ✅ `catalog_ai_model_list` |

**Fix crucial** : les archétypes de `catalog_object_list` portent `object_schema = ObjectSchema` ; les schémas portent `object_schema = SchemaSchema` ; les modèles portent `object_schema = AiModelSchema`.

**Sortie** : `catalog/catalog_core.json` — 13 entrées validées à 100% contre leurs schémas propres.

---

## ITÉRATION 3 — MRG Core ✅ TERMINÉE
**Objectif** : le moteur d'exécution minimal et fonctionnel.

| Composant | Fichier | Statut |
|-----------|---------|--------|
| `mrg.py` | `core/mrg.py` | ✅ Pipeline Get→Execute→Validate→Render→History→HowReset |
| `scan_and_do` | `core/functions/scan_and_do.py` | ✅ Récursif, agnostique |
| `SuperGet` | `core/supermethods/super_get.py` | ✅ 3 niveaux : ident → scenario_what → payload |
| `SuperExecute` | `core/supermethods/super_execute.py` | ✅ |
| `SuperValidate` | `core/supermethods/super_validate.py` | ✅ FORMULAS evaluator complet |
| `SuperRender` | `core/supermethods/super_render.py` | ✅ raw + summary |
| `history_update` | `core/hooks/history_update.py` | ✅ Hook after, loggé après chaque MRG |
| `log_hooks` | `core/hooks/log_hooks.py` | ✅ log_success / log_failure |
| `function_registry` | `core/functions/function_registry.py` | ✅ Lazy, sans imports circulaires |
| `validate_object_vs_schema` | `core/functions/validate_object_vs_schema.py` | ✅ FORMULAS complet |
| `CatalogStorage` | `core/storage/catalog_storage.py` | ✅ Abstraction storage |
| `scenario_debug_validate` | `scenarios/scenario_debug_validate.py` | ✅ 13/13 — 100% |

**FORMULAS implémentées** : EXISTS, IS_NOT_EMPTY, IN, STARTS_WITH, ENDS_WITH, MATCHES_REGEX, AND

**Sortie** : MRG opérationnelle, history loggée, 13/13 — 100%.

---

## ITÉRATION 4 — Scénarios fondamentaux ✅ TERMINÉE

| Livrable | Statut |
|----------|--------|
| `scenario_validate` | ✅ `scenarios/scenario_validate.py` |
| `scenario_get_create` | ✅ `scenarios/scenario_get_create.py` — niveau 3 agent : `coming` |
| `placeholder_resolve` | ✅ `core/functions/placeholder_resolve.py` — `{{field}}`, délimiteur catalog |
| Scenario, Placeholder, Format, Structure, Unit, Module, Slot | ✅ catalog |
| Delimiter, PairDelimiter, SingleDelimiter + 9 instances | ✅ `catalog_delimiter_list` |
| **42/42 — score 100%** | ✅ |

**scenario_get_create** :
```
SuperGet (3 niveaux)
  → trouvé : retourne l'objet
  → absent : SuperExecute (agent génère depuis schema + règles)
    → SuperValidate (triple validation si modality définie)
      → SuperRender
```

**Sortie** : les 3 scénarios testés sur les objets du noyau.

---

## ITÉRATION 5 — Agent de génération 🔵 EN COURS
**Objectif** : agent IA capable de générer des objets conformes depuis schema + règles.

| Livrable | Description |
|----------|-------------|
| `agent_generate_object` | Prompt nourri : GEV + ERK + FORMULAS + schema cible + règles |
| `scenario_execution_modality` | Attribut configurable dans scenario — active triple validation |
| Triple validation | Objectif atteint ? Règles comprises ? Règles respectées ? |

**Priorité agent** :
1. Choisir parmi options fournies
2. Sinon : créer librement avec triple validation

**Sortie** : agent testé sur génération de Schema, Rule, History.

---

## ITÉRATION 6 — GEV comme langage de définition
**Objectif** : GEV devient la source de vérité. JSON est compilé depuis GEV, pas l'inverse.

| Livrable | Description |
|----------|-------------|
| `GEV_LANG_v1.md` complet | Syntaxe de définition complète (pas seulement notation de référence) |
| Parser GEV → dict/JSON | Compilateur : fichiers `.gev` → catalog JSON |
| Migration catalog | Réécrire `catalog_core.json` en source GEV |
| Validation | Le parser produit un JSON identique au catalog actuel — test de non-régression |

**Principe** : comme TypeScript → JavaScript. On écrit en GEV, on exécute en JSON.
**Impact** : zéro régression — JSON reste le format runtime. Seule la source change.

---

## ITÉRATION 8 — Validation noyau complet
**Objectif** : tout le noyau tourne, se valide lui-même.

| Action | Description |
|--------|-------------|
| Enregistrer Object, Schema, Rule, History | Via scenario_get_create |
| Valider | Via scenario_validate |
| Premiers objets métier | Palette, VisualIntent — même pipeline |
| Bilan conformité | scenario_debug_validate sur l'ensemble |

**Sortie** : noyau auto-validant, prêt pour le déploiement des objets métier.

---

## Questions résolues

1. ~~GEV_LANG_v1.md avant itération 2 ?~~ → non-bloquant, créé après.
2. ~~FORMULAS manquantes bloquantes ?~~ → non, les 7 FORMULAS implémentées suffisent pour le noyau.
3. ~~scenario_debug_validate vs scenario_validate ?~~ → **deux distincts** : `debug_validate` est le test permanent intégré à la MRG via hook after ; `scenario_validate` est un scénario métier autonome (itération 4).
4. ~~History après chaque SuperMethod ou après la MRG complète ?~~ → **après la MRG complète** (hook after dans `history_update`).
5. `placeholder_resolve` → à définir en itération 4 : méthode Python sur les dicts, overridable par objet.

## Questions ouvertes

- `scenario_get_create` : comment gérer l'absence d'objet quand l'agent n'est pas encore posé (itération 5) ? Retourner `not_found` propre et logger ?
- `placeholder_resolve` : scope d'application (catalog_object_list uniquement, ou aussi schemas / rules) ?
