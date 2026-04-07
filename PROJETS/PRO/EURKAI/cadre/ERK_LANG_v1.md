ERK — EUREKAI Rule Kernel
Spécification de référence v1
Date : 2026-04-02
Statut : STABLE — source de vérité unique

Sources : ERK_v2.md (déc. 2025), CONSTITUTION_v0.md, CADRE_STABLE_v0.3
Règle : en cas de conflit avec une autre source, ce document prime.

-- Les commentaires ERK commencent par --


================================
1. PRINCIPES FONDAMENTAUX
================================

A1. Tout est objet.
A2. Tout objet a un lineage unique.
A3. Tout objet descend de Object (racine unique).
A4. ERK est agnostique du runtime (Python, JSON, JS...).
A5. Le catalogue ne contient que des spécificités.
A6. Tout le reste est hérité ou injecté.
A7. On ne définit pas ce que les objets ne sont pas.


================================
2. LINEAGE
================================

-- Le lineage encode la hiérarchie avec :

Object:Parent:Enfant:PetitEnfant

-- Règles :
-- - Commence par une majuscule
-- - Alphanumérique + underscore : [A-Z][A-Za-z0-9_]*
-- - Segments séparés par :
-- - Le : final indique une déclaration (les ancêtres sont créés si nécessaires)
-- - Plus le lineage est long, plus l'objet est précis

Exemples :
  Object:
  Object:Entity:
  Object:Entity:User:
  Object:Design:Palette:BrandPalette:


================================
3. DÉCLARATION D'OBJET
================================

-- Forme complète :
Object:Entity:User:
  .description = "Utilisateur du système"
  .version = "1.0"

-- Forme courte (shorthand) :
Object:Entity:User:
  .description = "Utilisateur du système"


================================
4. LISTES (AttributeList, MethodList, RuleList, RelationList)
================================

-- Pas de bundles. Les listes sont directes.

-- 4.1 AttributeList

temperature IN Object:Agent:AttributeList
  .type = number
  .default = 0.7
  .description = "Température de génération"

-- Syntaxe courte :
Object:Agent.temperature = 0.7

-- Types supportés :
-- str / string   chaîne (défaut)
-- int            entier
-- number         nombre décimal
-- bool           booléen
-- date           date/datetime
-- json           objet JSON
-- lineage        référence à un objet ERK


-- 4.2 MethodList

CreateFrom IN Object:Agent:MethodList
  .parent = Create
  .params = [source]
  .description = "Crée un agent depuis une source"

-- Syntaxe courte :
Object:Agent.method:CreateFrom


-- 4.3 RuleList

NotEmpty IN Object:Agent:RuleList
  .type = validation
  .condition = NEQ(value, "")
  .severity = error
  .message = "Ne peut pas être vide"

-- Syntaxe courte :
Object:Agent.rule:NotEmpty

-- Valeurs severity : error | warning | info
-- .condition utilise les FORMULAS (voir FORMULAS_v1.md)


-- 4.4 RelationList

Object:Agent depends_on Object:Role
Object:Agent related_to Object:Context

-- Relations canoniques :
-- inherits_from   héritage structurel (implicite via lineage)
-- depends_on      dépendance fonctionnelle
-- related_to      association sémantique


================================
5. ALIAS & RACCOURCIS
================================

-- Raccourcis listes :
X.attr      → attr IN X:AttributeList
X.method    → method IN X:MethodList
X.rule      → rule IN X:RuleList
X.relation  → relation IN X:RelationList

-- Notations ancêtres / descendants :
:Tag        est descendant de Tag
Tag:        est ancêtre de Tag
.Tag        a Tag comme attribut
Tag.        est attribut de Tag

-- Alias de relations :
IN          related_to + appartenance à dataset
tag_of      related_to + ancêtre Tag
type_of     inherits_from (héritage explicite)
scope_of    related_to (contexte/périmètre)


================================
6. DATASETS (Dict & List)
================================

-- List (clés numériques) :
TabList:
  [0]: Explorer
  [1]: Créer
  [2]: Console

-- Dict (clés quelconques) :
Config:
  [apiKey]: "xxx"
  [maxTokens]: 4096

-- Opérateur IN :
X IN Y              cherche dans keys ET values
X IN Y.keys         cherche uniquement dans keys
X IN Y.values       cherche uniquement dans values

-- Scope (contrainte de types autorisés dans un dataset) :
TabList.scope = [Page, Category, Tag, Module]


================================
7. CONTEXTES D'INTERPRÉTATION
================================

-- Trois contextes :

ASSERTION (sans préfixe) → retourne bool
  Object:Agent.temperature > 0

ACTION (DO) → exécute Create/Update
  DO Object:Agent.temperature = 0.8

CONDITION (IF) → branchement
  IF Object:Agent.temperature > 1 THEN Object:Agent.status = "hot"


================================
8. HOOKS
================================

BEFORE DO Object:Agent.save THEN Object:Agent.validate
IF DO Object:Agent.save THEN Log.success
IF NOT DO Object:Agent.save THEN Log.error

-- Hooks disponibles :
-- BEFORE ACTION     → hookBefore
-- IF ACTION         → hookAfter (si succès)
-- IF NOT ACTION     → hookFailure (si échec)


================================
9. OPÉRATEUR TEMPOREL WHEN
================================

-- WHEN est polymorphe selon le contexte :
-- + LoopBehavior    → While (boucle continue)
-- + Task            → Veille (attente événement)
-- + Trigger/Date    → Planner (cron)

WHEN Object:Agent.status EQ "ready" THEN DO Object:Agent.run


================================
10. MRG — MACHINE RÉCURSIVE GÉNÉRIQUE
================================

-- GEVR = Get → Execute → Validate → Render

-- Méthodes centrales (CentralMethod) :
-- Create, Read, Update, Delete, Orchestrate, Engage

-- Méthodes secondaires (SecondaryMethod) :
-- jamais point d'entrée, rattachées à une CentralMethod

-- HOW :
-- how appartient à what (l'objet cible)
-- how est vide par défaut
-- how est mis à jour par SuperGet (status = ready)
-- how.execute.after[] = value.reset (remise à zéro après exécution)

-- Boucle d'exécution :
-- À chaque loop, how s'exécute sur tous les what dont status = ready
-- Le nombre de loops dépend des étapes, pas du nombre d'objets
-- Exécution parallèle par défaut (par dict), séquentielle en fallback

-- Exécution canonique :
run =
  if get and execute :
    if validate then success else failure
  after


================================
11. STATUS & LIFECYCLE
================================

-- status est défini par type d'objet
-- lifecycle commence à 2
-- lifecycle[2] = ident du scénario de validation pour passer à status = ready
-- Un status ne peut être upgradé qu'après validate.success du scénario correspondant


================================
12. RÈGLES DE NON-DUPLICATION
================================

-- Pas de copie, seulement override
-- Un élément hérité/injecté ne peut pas être redéfini, seulement overridé
-- Une donnée owned est spécifique si elle diffère de sa valeur automatisée
-- automated = no explicit payload value required


================================
13. RÈGLES DE SCHÉMA — CONTAINERS ET LISTES D'OPTIONS
================================

-- Un schéma ne définit jamais une valeur directe
-- Si un champ peut prendre une valeur parmi une liste d'options :
--   le schéma référence l'objet CONTAINER qui porte cette liste, jamais la valeur elle-même
-- Pas de liste sans container
-- Un schéma ne définit que des containers (types/lineages), jamais des instances

-- FAUX dans un schema :
--   model = "claude-opus"          -- valeur directe, hardcodée
-- JUSTE :
--   model = AiModel                -- référence au type container
--   model = AiModel:LlmModel       -- plus spécifique si nécessaire

-- Cette règle s'applique à tous les objets, pas seulement aux modules
-- Exemple : un module peut dépendre d'un autre module, mais le schéma
--   référence Module (ou Module:FunctionalModule) jamais "masonry_gallery"


================================
14. NOMMAGE — RÈGLE OBJET COMPOSÉ
================================

-- On ne crée pas d'objet à nom composé sans créer l'objet père (section 2 du nom)
-- On ne crée l'objet père que si ses conditions d'utilité et de spécificités sont remplies
-- Si les conditions ne sont pas remplies, on reste sur un nom simple

-- Exemples :
--   ContentSensitivity → père = Sensitivity (créé si Sensitivity a d'autres enfants)
--   FunctionalUnit     → père = Unit        (créé si Unit a d'autres enfants)
--   Si le père n'a pas encore d'autres enfants confirmés, on attend avant de le créer


================================
15. GOUVERNANCE — ALIASES ET PLACEHOLDERS
================================

-- Tout alias ou placeholder référençant un nom d'objet crée une dépendance structurelle
-- Tout renommage d'objet doit :
--   1. Provoquer un audit de toutes les occurrences avant application
--   2. Déclencher une alerte niveau 1 aux responsables de projet utilisant ces aliases ou placeholders
--      Sinon : simple mise à jour des conditions générales et/ou de la documentation de l'agence
-- Le traçage est automatique (toutes les actions MRG sont loggées dans History)
-- Cette règle est impérative en mode assisté non-autonome
-- En mode autonome : le renommage ne peut être effectué que si l'audit est à 0 occurrence externe
--   ou si toutes les occurrences sont dans le scope de la modification


================================
16. NOMMAGE — RÈGLES GÉNÉRALES
================================

-- Nomenclature : <objet>_<paramètre> snake_case — identique dans tous les langages et formats
-- Jamais de pluriel dans le nommage d'un objet ou d'un attribut
--   FAUX : module_slot_list, object_rules, model_strengths (dans le schema)
--   JUSTE : module_slot, object_rule, model_strength (le container porte la multiplicité)
-- Un objet à nom composé requiert la création préalable de l'objet père (section 14)
-- Les noms sont stables : tout renommage déclenche la procédure section 15
