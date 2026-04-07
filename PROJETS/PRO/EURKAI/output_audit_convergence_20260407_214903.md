# EURKAI — Audit Global de Convergence
**2026-04-07 — Session s77**

---

## A. ÉTAT DES LIEUX RÉEL

### Branché dans le pipeline idea→github

| Fichier | Branché | Qualité |
|---|---|---|
| scenario_idea_to_brief | ✅ pipeline | appelle agent_brief directement |
| scenario_brief_to_cdc | ✅ pipeline | déterministe pur, 0 agent |
| scenario_cdc_to_specs | ✅ pipeline | déterministe pur, 0 agent |
| scenario_specs_to_deliverable | ✅ pipeline | délègue à product_create |
| scenario_deliverable_to_preprod | ✅ pipeline | **BUG : écrit 1 fichier sur 12** |
| scenario_preprod_to_prod | ✅ pipeline | simulé |
| scenario_prod_to_backup | ✅ pipeline | simulé |
| scenario_prod_to_github | ✅ pipeline | simulé |
| modules/product_create | ✅ branché | orchestre 3 sous-modules, MANIFEST |
| modules/backend_create | ✅ branché | génère N modules backend, MANIFEST |
| modules/frontend_create | ✅ branché | génère N classes frontend, MANIFEST |
| modules/storage_create | ✅ branché | génère N classes storage, MANIFEST |
| agents/agent_brief | ✅ branché | idée → brief structuré |
| agents/agent_generate_code | ✅ branché | squelette code déterministe |

### Codé mais PAS branché dans le pipeline

| Fichier | Usage actuel |
|---|---|
| scenario_orchestrate | standalone : idée → objet → code via 7 agents |
| agents/agent_intake | seulement dans scenario_orchestrate |
| agents/agent_architect | seulement dans scenario_orchestrate |
| agents/agent_generate_object | seulement dans scenario_orchestrate |
| agents/agent_debug_fix | seulement dans scenario_orchestrate |
| agents/agent_validator | seulement dans scenario_orchestrate |
| core/functions/gev_compile.py | jamais appelé nulle part |
| catalog/catalog_core.json (38 objets) | seulement via scenario_orchestrate |

### MODULES/ design/document (25+ modules)
Fonctionnels. Standalone. Pas connectés au pipeline idea→github.

### Doublons
- agent_brief : appelé dans scenario_idea_to_brief ET scenario_orchestrate
- Génération code : chemin riche (orchestrate : +debug_fix +validator) vs chemin direct (backend_create : agent_generate_code seul)
- MANIFEST Python inline dans modules/ vs catalog_core.json → deux systèmes de déclaration

---

## B. CENTRE D'ORCHESTRATION ACTUEL

scenario_orchestrate n'est PAS le centre du pipeline opérationnel.
Il est un générateur standalone : schema_ident → objet catalog → code qualifié.
Signature incompatible avec le pipeline (run(schema_ident, params, ...) ≠ run(input_data, verbose)).

Le vrai centre du pipeline : scenario_specs_to_deliverable → product_create.

---

## C. CARTOGRAPHIE DES RESPONSABILITÉS

- GEV : déclarations objets/schemas/règles/méthodes → catalog (compilateur prêt, jamais utilisé)
- CATALOG : référentiel meta EURKAI (38 objets, 36 schemas) — déconnecté du pipeline
- OBJET : données + lineage + fields. Produit par agent_generate_object OU inline
- RÈGLE : contraintes GEV, exécutées par agent_validator (partiellement)
- SCHEMA : ontologie objet. 36 schemas meta, 0 schema domaine (Invoice, Payment...)
- SCENARIO (pipeline) : conversion from→to. Contrat run(input_data, verbose) → {status, from, to, data, meta}
- SCENARIO ORCHESTRATE : build_object_from_catalog. Standalone. Hors pipeline
- MODULE : unité de création avec MANIFEST. run(input_data) → {status, ...output}
- AGENT EXÉCUTANT : action atomique (générer, valider, fixer, enrichir)

---

## D. FUSIONS À FAIRE MAINTENANT

1. scenario_deliverable_to_preprod._write_code() → écrire TOUS les modules (backend+frontend+storage)
2. agent_validator + agent_debug_fix → brancher dans backend_create après agent_generate_code
3. MANIFEST modules/ → convertir en .gev (après round-trip test)

---

## E. DÉCISIONS D'ARCHITECTURE FIGÉES

- D1 : Pipeline figé — idea → brief → cdc → specs → deliverable → preprod → prod → [backup, github]. Jamais de nouvelle étape.
- D2 : scenario_orchestrate = build_object_from_catalog. Standalone. Jamais dans le pipeline.
- D3 : product_create = unique entrée pour la création de code. Pas d'appel direct à agent_generate_code depuis les scenarios.
- D4 : Contrat unifié pipeline : run(input_data, verbose) → {status, from, to, data, meta}
- D5 : catalog_core.json = objets meta EURKAI uniquement. Objets domaine → inférés dynamiquement ou enregistrés via GEV après création.
- D6 : MODULES/ design/document reste découplé. Branchement via scenarios dédiés (scenario_specs_to_page, etc.)

---

## F. DÉCISION GEV/ERK

PARTIELLEMENT — sur périmètre borné, après correction des bugs critiques.

Convertir maintenant :
- MANIFEST modules/ → 4 fichiers .gev compilés
- Objets domaine (Invoice, Payment, User) → Object:Domain:X: après création pipeline

Ne pas convertir :
- 8 scenarios de pipeline → contrat Python stable
- Agents → exécutants, contrat Python adapté

Ordre si on lance GEV :
1. Écrire backend_create.gev → compiler → vérifier round-trip
2. Enregistrer objets domaine dans catalog via GEV
3. scenario_orchestrate peut alors fonctionner sur objets domaine réels

---

## G. FEUILLE DE ROUTE UNIQUE

### NOW
- N1 : Fixer scenario_deliverable_to_preprod._write_code() — écrire les 12 fichiers
- N2 : Brancher agent_validator + agent_debug_fix dans backend_create

### NEXT
- X1 : Round-trip GEV test (product_create.gev → compiler → catalog → code)
- X2 : Enregistrer objets domaine dans catalog via GEV
- X3 : MANIFEST modules/ → .gev compilés
- X4 : Modules page_create / content_create (éliminer stubs)

### LATER
- L1 : Steps simulés → actions réelles (git, copy, deploy)
- L2 : Catalog runtime des modules générés (réutilisabilité)
- L3 : Branchement MODULES/ design/document dans le pipeline
- L4 : Playground admin (exposer scenario_orchestrate)

---

## H. RISQUES SI ON CONTINUE SANS FUSIONNER

| Risque | Conséquence |
|---|---|
| Laisser _write_code à 1 fichier sur 12 | 8/8 success = illusion. Preprod incomplet. Tout l'aval est faux. |
| Convertir GEV avant N1+N2 | Layer d'abstraction sur fondation avec bug critique. Round-trip non vérifié. |
| Continuer sans validation dans backend_create | Modules générés sont des squelettes non vérifiés. Score jamais calculé. |
| Connecter MODULES/design avant X2 | Objets domaine inexistants dans catalog. Design ne répond pas au métier réel. |
| Refondre scenario_orchestrate | Perte d'une brique qualifiée (debug_fix + validator) nécessaire pour X2. |
| Ouvrir playground avant N1+N2 | 3 chantiers parallèles sur core instable. |

