# ERK — NOTE SUR LES LAYERS (v1.0)

Cette note décrit :
- la liste des layers,
- les objets principaux de chaque layer,
- leurs règles / attributs spécifiques,
- la façon dont ils interagissent entre eux,
- la place des domaines (ex. biomimétisme), clients et projets.

---

## RÈGLES GLOBALES (VALABLES POUR TOUS LES LAYERS)

1. **Tout objet possède une méthode `convert()`**
   - Définie dès `Object` dans le Core.
   - Peut être spécialisée dans les objets hérités.
   - Rôle :
     - recevoir n’importe quel objet ERK (ou bundle d’objets),
     - retourner deux vecteurs :
       - `WhatVector` = Vector.MergedDefinition()
       - `HowVector`  = Vector.MergedRule()

2. **Les SuperTools reçoivent des vecteurs, jamais des structures brutes**
   - Entrée : `HowVector`, `WhatVector`
   - Sortie : `ScriptVector`
   - `ScriptVector` est envoyé à la MRG qui retourne un ou plusieurs `ResultVector`.

3. **Toute fonction / méthode reçoit et retourne un *bundle* de 1 à N vecteurs**
   - Pas d’API “primitive” — tout circule sous forme vectorielle.
   - Cohérent avec un langage orienté vecteurs.

4. **Accès à la MRG**
   - Tous les accès à la MRG passent par un **Hub** unique (Gateway).
   - Pas de connexion directe sauvage depuis les layers supérieurs.
   - Le Hub applique les règles de sécurité et de validation avant tout appel.

---

# LAYER 0 — CORE / MRG / ERK LANGUAGE / GLOBAL RULES

### 1. Rôle du Layer 0
C’est le **cœur absolu** du système :
- définit la fractale (IVC × DRO),
- définit les objets de base,
- définit le langage ERK,
- définit les règles globales et la MRG (Machine de Règles Généralisée),
- ne dépend d’aucun autre layer.

### 2. Objets principaux

- `Object`
  - schéma minimal (id, lineage, element_list, fractal_slot, metadata…)
  - porte la méthode `convert()`.
- `MetaObject`
  - schéma universel pour tous les méta-objets.
- **Catégories Méta Fondamentales (3×3)**
  - `IdentityDefinitionObject`
  - `IdentityRuleObject`
  - `IdentityOptionObject`
  - `ViewDefinitionObject`
  - `ViewRuleObject`
  - `ViewOptionObject`
  - `ContextDefinitionObject`
  - `ContextRuleObject`
  - `ContextOptionObject`
- Objets liés à la fractale :
  - `FractalSchema`
  - `FractalSlot`
  - `Vector` (et sous-types : DefinitionVector, RuleVector, OptionVector…)
- Moteur de récursivité :
  - `GlobalRecursiveMethod`
    - méthode minimale + variante complète.
- `MRG` (Machine de Règles Généralisée)
  - reçoit un `ScriptVector`,
  - applique les règles,
  - retourne un ou plusieurs `ResultVector`.
- Langage ERK :
  - grammaire,
  - DSL structurel (`.erk`),
  - mapping vers la fractale.

### 3. Règles spécifiques

- Le Layer 0 :
  - ne connaît **aucun domaine**, **aucune entité**, **aucun scénario métier**,
  - ne gère que :
    - la structure,
    - les vecteurs,
    - la fractale,
    - la récursivité,
    - la MRG,
    - le langage ERK.

### 4. Interactions avec les autres layers

- Tous les layers supérieurs s’appuient sur :
  - `Object`,
  - la fractale,
  - `Vector`,
  - `GlobalRecursiveMethod`,
  - la MRG.
- Aucun layer ne peut modifier Layer 0.
- Toute évolution passe par extension/addition, jamais par destruction.

---

# LAYER 1 — SECURITY

### 1. Rôle du Layer 1
- Sécuriser l’accès au Core et à la MRG.
- Centraliser toutes les vérifications de sécurité.
- Héberger le **Hub** / Gateway inter-layer.

### 2. Objets principaux

- `SecurityPolicy` (ContextRuleObject / IdentityRuleObject)
- `PermissionSet`
- `RoleProfile`
- `AccessVector` (vecteur annoté de droits / scopes)
- `SecurityHub` / `Gateway`
  - unique point d’entrée vers :
    - la MRG,
    - les SuperTools,
    - les ressources critiques.

### 3. Règles spécifiques

- Toute interaction entre deux layers passe :
  - par le **Hub**,
  - par un contrôle de sécurité (droits, contexte).
- Les règles de sécurité s’expriment en vecteurs de règles (RuleVectors).
- Possible d’étendre la sécurité via des meta-objets :
  - MetaSecurityPolicy ∈ ContextRuleObject.

### 4. Interactions

- En dessous :
  - protège le Layer 0.
- Au-dessus :
  - tous les layers 2+ doivent passer par Layer 1 pour accéder :
    - à la MRG,
    - aux SuperTools,
    - à certaines ressources de la Library.

---

# LAYER 2 — RULES / MÉTHODES CENTRALES / SUPERTOOLS

### 1. Rôle du Layer 2
- Définir les **méthodes centrales** (CRUDOE).
- Définir un SuperTool par méthode centrale :
  - `SuperCreate`
  - `SuperRead`
  - `SuperUpdate`
  - `SuperDelete`
  - `SuperOrchestrate`
  - `SuperExecute` (si tu souhaites garder E de CRUDOE explicitement).

### 2. Objets principaux

- Méthodes centrales (ContextDefinitionObject / ViewDefinitionObject) :
  - `CentralMethod.Create`
  - `CentralMethod.Read`
  - `CentralMethod.Update`
  - `CentralMethod.Delete`
  - `CentralMethod.Orchestrate`
  - `CentralMethod.Execute` (optionnel).
- SuperTools :
  - `SuperCreate`
  - `SuperRead`
  - `SuperUpdate`
  - `SuperDelete`
  - `SuperOrchestrate`
  - `SuperExecute`
- Règles associées :
  - `CentralMethodRule` (ContextRuleObject)
  - `SuperToolRule` (ContextRuleObject / ViewRuleObject)

### 3. Règles spécifiques

- Un SuperTool :
  - reçoit `HowVector` et `WhatVector`,
  - construit un `ScriptVector`,
  - envoie ce `ScriptVector` à la MRG (via le Hub / Security),
  - reçoit un ou plusieurs `ResultVector`.
- Les méthodes centrales ne décident pas du *détail* métier :
  - elles appliquent un comportement générique (CREATE, READ, etc.)
  - sur les vecteurs produits par `convert()`.

### 4. Interactions

- En dessous :
  - s’appuie sur Layer 0 (vecteurs, fractale, MRG)
  - est sécurisé par Layer 1 (Hub).
- Au-dessus :
  - toutes les méthodes secondaires, scénarios, entités, domains, etc.
    utilisent les SuperTools pour agir.

---

# LAYER 3 — MÉTHODES SECONDAIRES / STEPS / SCÉNARIOS

### 1. Rôle du Layer 3
- Définir les **méthodes secondaires** (spécialisées par type d’objet ou par domaine).
- Définir les **steps** et les **scénarios** d’exécution.
- Servir d’interface entre :
  - les besoins métier,
  - les méthodes centrales / SuperTools.

### 2. Objets principaux

- `SecondaryMethod` (spécifique à un type ou une famille d’objets).
- `StepDefinition` (ContextDefinitionObject).
- `ContextFlowDefinition` (plutôt que “scenario métier”).
- Règles :
  - `StepRule`, `ContextFlowRule` (ContextRuleObject).
- Objets de validation de flow :
  - `ContextFlowValidator`
    - utilisé **à la création** pour vérifier la cohérence des enchaînements.

### 3. Règles spécifiques

- La validation des enchaînements (steps) :
  - se fait *à la création* du flow / contexte,
  - pas à chaque exécution (pour ne pas surcharger le runtime).
- `StepDefinition` et `ContextFlowDefinition` n’appellent jamais directement la MRG :
  - ils passent par les central methods / SuperTools (Layer 2),
  - eux-mêmes passent par le Hub (Layer 1).

### 4. Interactions

- En dessous :
  - s’appuie sur Layer 2 pour exécuter les actions réelles,
  - s’appuie sur Layer 4 pour charger des templates, seeds, schemas.
- Au-dessus :
  - les entités, domaines, projets réutilisent ces flows comme blocs.

---

# LAYER 4 — LIBRARY / INTRANET (RESSOURCES, SCHÉMAS, TEMPLATES…)

### 1. Rôle du Layer 4
- Stocker et exposer toutes les **ressources partagées** :
  - templates,
  - schemas,
  - seeds,
  - catalogues,
  - documentation interne.

### 2. Objets principaux

- `SchemaDefinition` (ViewDefinitionObject / ContextDefinitionObject).
- `TemplateDefinition` (ViewDefinitionObject).
- `SeedBundle` (ContextOptionObject).
- `ResourceCatalog` :
  - catalogue par type (schemas, templates, seeds…).
- `FractalMapping` (ex. `erk_structure_mapping_dom.erk` + JSON associé).

### 3. Règles spécifiques

- Les ressources sont :
  - testées / validées avant exposition,
  - lues par tous les layers supérieurs,
  - jamais modifiées directement par ces layers (passage par des méthodes dédiées).
- Bibliothèque structurée :
  - par MetaObject de base,
  - par case fractale,
  - par domaine éventuellement.

### 4. Interactions

- En dessous :
  - repose sur fractale et vecteurs de Layer 0.
- Au-dessus :
  - tous les layers consomment la Library via leurs propres objets,
  - ex. Layer 3 utilise les templates de flow,
  - Layer 5 utilise des seeds d’organisation,
  - Layer 8–9 utilisent des modules prêts à l’emploi.

---

# LAYER 5 — ENTITIES / TEAMS / AGENTS

### 1. Rôle du Layer 5
- Modéliser toutes les **entités actives** du système :
  - Teams,
  - Agents (humains ou IA),
  - rôles,
  - responsabilités.

### 2. Objets principaux

- `Entity`
- `Team`
- `Agent`
- `Role` (IdentityDefinitionObject / IdentityRuleObject)
- `PermissionProfile` (lié à Layer 1 Security)
- `EntityLineage` (généalogies d’entités)

### 3. Règles spécifiques

- Les entités :
  - ne modifient jamais directement la MRG,
  - orchestrent l’usage des flows (Layer 3),
  - invoquent les SuperTools (Layer 2) via le Hub (Layer 1).
- Les agents peuvent :
  - déclencher des flows,
  - choisir des templates,
  - paramétrer des seeds,
  - mais toujours dans le cadre des règles de sécurité.

### 4. Interactions

- En dessous :
  - utilisent Library (Layer 4) pour récupérer modules, templates,
  - utilisent Secondary Methods (Layer 3) pour agir.
- Au-dessus :
  - sont utilisés par les domaines (Layer 8), les projets (Layer 9)
    comme “force de travail” structurelle.

---

# LAYER 6 — AGENCY / DOMAIN / ORCHESTRATION / AUTOMATION

### 1. Rôle du Layer 6
- Modéliser l’**Agence** elle-même :
  - domaines métiers “cœur agence”,
  - orchestration,
  - automation,
  - hooks.

### 2. Objets principaux

- `DomainHub` (point de coordination des domains internes).
- `AutomationFlow` / `AutomationRule`.
- `Hook` / `HookEvent` / `HookTrigger`.
- `OrchestrationPlan` (utilise `SuperOrchestrate`).
- `Monitoring` / `OptimizationRule` (si tu veux les garder ici ou en sous-layer).

### 3. Règles spécifiques

- L’Agence définit :
  - comment les différents flows et domains s’appuient sur les layers 0–5,
  - où les hooks se déclenchent,
  - comment les optimisations et audits sont faits.
- Ce layer :
  - utilise les autres, ne les re-spécifie pas.

### 4. Interactions

- En dessous :
  - utilise entités, flows, SuperTools, Library.
- Au-dessus :
  - fournit des patterns d’utilisation pour les domains d’activité (Layer 8),
  - inspire les structures de projets (Layer 9).

---

# LAYER 7 — AI

### 1. Rôle du Layer 7
- Encapsuler toutes les interactions avec les IA externes :
  - modèles (LLM, vision, audio…),
  - prompts,
  - exécution IA.

### 2. Objets principaux

- `MetaPrompt`
- `PromptExecutor`
- `ModelProvider`
- `AIConnector`
- Seeds IA (paramètres de modèles / providers).

### 3. Règles spécifiques

- L’IA est toujours un **plan B**, jamais un prérequis absolu :
  - le système doit continuer à fonctionner si l’IA est coupée,
  - on doit pouvoir désactiver tous les connecteurs IA instantanément.
- L’IA est invoquée :
  - par des flows (Layer 3),
  - par des agents (Layer 5),
  - par des modules d’automatisation (Layer 6),
  - mais jamais au centre du Core (Layer 0).

### 4. Interactions

- En dessous :
  - lit et écrit des vecteurs produit par les autres layers,
  - ne touche pas à la structure fondamentale.
- Au-dessus :
  - les domains, projets, UI peuvent proposer des fonctions “augmentées IA”
    en s’appuyant sur ce layer.

---

# LAYER 8 — LAYERS D’ACTIVITÉ (SHOPPING, CRM, BIOMIMÉTISME, …) — USERS

### 1. Rôle du Layer 8
- Regrouper les **domains d’activité** :
  - Shopping,
  - CRM,
  - Biomimétisme,
  - Education,
  - etc.
- Chaque domain :
  - est un sous-layer de Layer 8,
  - s’appuie sur toute la pile 0–7,
  - ne modifie pas les couches inférieures.

### 2. Objets principaux

- `DomainObject` (ex. `BiomimicryPattern`, `ShoppingCart`, `CustomerProfile`…)
- Flows métier dérivés :
  - `ShoppingFlow`, `BiomimicryFlow`, etc.
- Seeds métier :
  - `DefaultBiomimicrySeed`, `DefaultShoppingSeed`…

### 3. Règles spécifiques

- Ces layers métier :
  - **lisent** les layers inférieurs (Core, Library, Entités, AI…),
  - n’interagissent **jamais directement entre eux** : ils passent par les layers inférieurs (et le Hub).
- Pour ton exemple :
  - le **biomimétisme** est un domain → donc un sous-layer de Layer 8.

### 4. Interactions

- En dessous :
  - utilisent l’Agence (Layer 6) pour les patterns d’automatisation,
  - utilisent AI (Layer 7) pour l’intelligence augmentée.
- Au-dessus :
  - sont utilisés par les Applications / Projets / UI (Layer 9).

---

# LAYER 9 — APPLICATIONS / PROJETS / UI

### 1. Rôle du Layer 9
- Regrouper les **applications concrètes** :
  - sites web,
  - SaaS,
  - apps mobiles,
  - outils internes,
  - etc.

### 2. Objets principaux

- `Project`
- `AppUI`
- `DeploymentConfig` (stack choisie : PHP, Python, React…)
- `ProjectConfigFlow` (config initiale via UI ou via agent).

### 3. Règles spécifiques

- Bootstrap :
  - `main.py -> bootstrap.py`
  - Bootstrap :
    - lit la config du projet,
    - sait vers quelle stack `build/<stack>` rediriger,
    - s’appuie sur la fractale + lineages,
    - si un élément n’est pas défini :
      - redirige vers une page de configuration (`project_config`),
      - ou applique les valeurs par défaut (Seeds).

### 4. Interactions

- En dessous :
  - utilise les piles complètes des layers 0–8.
- Entre projets :
  - isolation logique (et éventuellement Docker séparé par client).

---

# LAYER 10 — LAB / BLOG / EXPÉRIMENTATIONS

### 1. Rôle du Layer 10
- Servir de **terrain d’expérimentation** :
  - prototypes,
  - démonstrations,
  - blog,
  - documentation vivante.

### 2. Objets principaux

- `LabExperiment`
- `DemoFlow`
- `Tutorial` / `DocPage`

### 3. Règles spécifiques

- Ne doit jamais être prérequis pour le runtime de production.
- Peut être désactivé sans casser le reste.

---

## PLACE DES LAYERS CLIENT / PROJET

- Les **clients** et **projets** spécifiques :
  - vivent dans Layer 9 (Applications / Projets / UI),
  - chaque client peut avoir :
    - son propre cube logique,
    - voire son propre Docker / serveur.
- Créer un Layer séparé par client **dans la fractale globale** n’est pas nécessaire :
  - il suffit de les considérer comme sous-espaces de Layer 9,
  - structurés par domain (Layer 8) + seeds spécifiques.

---

# FICHIER UTILISATEUR

Ce document doit être gardé comme **référence de base** pour :
- savoir où ranger chaque nouvel objet,
- vérifier qu’on ne casse pas la logique des layers,
- garder la pile stable et lisible.
