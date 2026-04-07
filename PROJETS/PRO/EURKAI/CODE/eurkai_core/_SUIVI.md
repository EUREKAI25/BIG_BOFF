# EURKAI CORE — Suivi
Sous-projet de : EURKAI
Créé le : 2026-04-02
Statut : EN COURS — Itération 7

---

## Objectif

Poser le noyau constitutionnel d'EURKAI :
- Object père dont tout dérive
- Schema + Rule + History
- MRG (scan_and_do, SuperGet/Execute/Validate/Render)
- Scénarios fondamentaux (validate, get_create, extract_rules)
- Agent IA de génération d'objets depuis schema + règles

Ce noyau sert de garde-fou : il stabilise EURKAI en validant la conformité à chaque itération.

---

## Références

- Cadre : `/PROJETS/PRO/EURKAI/cadre/`
  - ERK_LANG_v1.md — grammaire fonctionnelle (référence)
  - FORMULAS_v1.md — formules de validation (référence)
  - CONSTITUTION_v0.md, CADRE_STABLE_v0.3, EXECUTION_CONSTITUTION_v0...
- Sources docs : `/PROJETS/PRO/_INPUTS/EURKAI/`
- Bootstrap précédent (référence) : `CODE/eurkai_bootstrap_minimal/`

---

## Règles de travail

- Nomenclature : `<objet>_<paramètre>` snake_case — identique dans tous les langages
- GEV : langage des objets (`Schema.validate.ruleList`)
- ERK : grammaire fonctionnelle (règles, conditions, hooks)
- Formulas : briques atomiques pour les conditions de règles
- `placeholder_resolve` : méthode universelle sur tous les formats, overridable
- Itérations successives avec validation de conformité à chaque étape
- 100% des actions MRG loggées dans History (action, déclencheur, résultat, justification)
- Agents IA : priorité 1 = choisir parmi options, priorité 2 = créer avec triple validation

---

## État par itération

### Itération 0 — Cadre ✅ TERMINÉE
- [x] ERK_LANG_v1.md créé (`cadre/ERK_LANG_v1.md`)
- [x] FORMULAS_v1.md créé — 8 catégories dont ARITHMETIC (`cadre/FORMULAS_v1.md`)
- [ ] FORMULAS_v1.md compléter : CONDITIONAL, TEMPORAL, TYPE (non-bloquant)
- [ ] GEV_LANG_v1.md à créer (non-bloquant pour itérations suivantes)

### Itération 1 — Extraction des règles ✅ TERMINÉE
- [x] Agent extract_rules (`agents/agent_extract_rules.md`)
- [x] rule_list_cadre.json : 87 règles + 31 méthodes (`output/rule_list_cadre.json`)

### Itération 2 — Noyau catalog ✅ TERMINÉE
- [x] Object, Schema, Rule, History, AiModel dans catalog_object_list
- [x] ObjectSchema, SchemaSchema, RuleSchema, HistorySchema, AiModelSchema
- [x] model_claude_opus / sonnet / haiku (catalog_ai_model_list)
- [x] catalog_core.json — chaque entrée porte son object_schema correct

### Itération 3 — MRG Core ✅ TERMINÉE
- [x] scan_and_do, SuperGet/Execute/Validate/Render, history_update, log_hooks
- [x] function_registry (lazy), validate_object_vs_schema (FORMULAS complet)
- [x] CatalogStorage, load_catalog, mrg.py
- [x] scenario_debug_validate — hook after automatique

### Itération 4 — Scénarios fondamentaux ✅ TERMINÉE
- [x] scenario_validate, scenario_get_create (3 niveaux), placeholder_resolve
- [x] Scenario, Placeholder, Format, Structure, Unit, Module, Slot, Delimiter (9 instances)
- [x] 42/42 — 100%

### Itération 5 — Agents IA ✅ TERMINÉE
- [x] prompt_execute — méthode universelle d'appel IA, clé lue au runtime
- [x] agent_generate_object — catalog-driven, zéro texte hardcodé
- [x] triple_validate (L1+L2+L3), scenario_get_create niveau 3 complet
- [x] catalog_role_list, catalog_constraint_list, catalog_expected_output_list, catalog_prompt_template_list
- [x] CatalogStorage → interface agnostique get/get_all/get_all_by_filter
- [x] agent_extract_rules.py + scenario_extract_rules.py — contenu migré dans catalog
- [x] catalog_env_list → catalog_env_item_list (cohérence nomenclature)
- [x] 143/143 — 100%

### Itération 6 — Objets métier + catalog_extract ✅ TERMINÉE
- [x] scenario_get_create validé sur Object, Schema, Rule, History — 4/4
- [x] Design, VisualIntent, Palette, DesignSystem + schemas dans catalog_core.json
- [x] catalog_extract — méthode d'extraction d'un sous-catalog (lineage_prefix / type_list / list_name_list)
- [x] 151/151 — 100%

### Itération 7 — 🔵 EN COURS
- [x] GEV_LANG_v1.md — spécification stable, symboles finalisés (voir détail journal)
- [x] gev_compile.py — compilateur mis à jour (nouveaux symboles)
- [x] recursive_query — moteur de requête récursif N niveaux, composable, catalog-native
- [x] Object:Criteria + Object:Query + CriteriaSchema + QuerySchema — catalog 73/73 100%
- [ ] scenario_define_agent — cycle de vie complet d'un agent depuis le catalog
- [ ] FORMULAS_v1.md : compléter CONDITIONAL, TEMPORAL, TYPE
- [ ] Milestone — Object:Scenario:Milestone
- [x] Object:Query:StandardQuery + 13 instances (catalog_standard_query_list) + standard_queries.py
- [x] Object:Relation + Object:Relation:CriteriaOf + RelationSchema — catalog 77/77 100%
- [ ] Cache query — memoize par hash(criteria), invalidation sur mutation catalog (hook after_write)
- [ ] Migration object_elementlist : base_list/attribute_list/relation_list/option_list/method_list (via script validation règles — non-bloquant)
- [ ] Auto-génération <object>_of pour tous les objets (non-bloquant)

---

## Journal

### 2026-04-02 — Session 1
- Session de cadrage : lecture de tous les docs de référence
- ERK_LANG_v1.md et FORMULAS_v1.md créés dans cadre/
- Clarification GEV vs ERK, nomenclature, placeholder_resolve
- Feuille de route validée → démarrage itération 1

### 2026-04-02 — Session 5 (actuelle)
- GEV_LANG_v1.md : symboles finalisés (// et /* */ pour commentaires, $ règle, > méthode, ? optionnel)
- gev_compile.py mis à jour en conséquence
- recursive_query.py : moteur récursif N niveaux inspiré de l'ancien MetaSuperQuery, adapté catalog dict
- Object:Criteria + Object:Query + schémas → catalog 73/73 100%
- Décision : pas de RDF, catalog dict suffit. Cache query = futur (hash criteria + invalidation after_write)

### 2026-04-02 — Sessions 2 à 4
- Itérations 1 à 6 réalisées
- catalog_core.json : 151 objets validés — 151/151 100%
- MRG complète, agents IA catalog-driven, interface storage agnostique
- Objets métier Design intégrés, catalog_extract créé
- Prochaine étape : itération 7 — GEV_LANG, scenario_define_agent, Milestone
