# MetaSchema Eurkai — Check-list de finalisation

Objectif : vérifier que le MetaSchema couvre bien tous les objets nécessaires au noyau Eurkai, sans sur-complexité ni trous.

---

## 1. Objets fondamentaux (niveau CORE)

À valider / compléter :
- `Object:Object` (métatype de base)
- `Object:Attribute`
- `Object:Method`
- `Object:Relation`
- `Object:Rule`
- `Object:Schema`
- `Object:Vector`
- `Object:Bundle` (structure interne de tout objet)
- `Object:XFractal` (vue globale d’un objet dans la fractale)

Questions :
- Chaque objet possède-t-il :
  - `id`
  - `name`
  - `type`
  - `createdAt` / `updatedAt`
- Les relations autorisées sont-elles limitées à :
  - `depends_on`
  - `inherits_from`
  - `related_to`
  - (tout alias est-il documenté ?)

---

## 2. Objets d’exécution et de scénarios

- `Object:Scenario` (GEVR)
- `Object:Step`
- `Object:GEVRScenario` (ou alias)
- `Object:Log`
- `Object:Event`

À vérifier :
- Un scénario connaît-il :
  - ses entrées
  - ses sorties
  - ses prérequis (depends_on)
  - ses règles ERK associées ?

---

## 3. Objets liés aux IA et aux prompts

- `Object:Prompt`
- `Object:PromptPart` (role, contexte, mission, objectif, contraintes…)
- `Object:Response`
- `Object:Diagnosis` (pour SuperEngage)
- `Object:Agent` (humain/IA)
- `Object:AIAgent` (spécialisation)

Questions :
- Chaque réponse IA est-elle liée à :
  - un `Prompt`
  - un `Agent`
  - un `Scenario` / `SuperTool` ?
- Où stocke-t-on :
  - le `score`
  - les `flags` (hallucination, incomplétude…)
  - les `suggestions` d’amélioration ?

---

## 4. Objets de produits & modules

- `Object:Project`
- `Object:Module`
- `Object:Template`
- `Object:Page`
- `Object:Section`

Questions :
- Peut-on décrire n’importe quel “produit” Eurkai comme combinaison de ces objets ?
- Le MetaSchema est-il indépendant du domaine (business, web, app, etc.) ?

---

## 5. Objets ERK (nouvel ajout)

À intégrer si absents :
- `Object:ERKRule`
- `Object:ERKScript`

Relier :
- `ERKRule` ←→ `Object` ciblés (via `related_to`)
- `ERKScript` ←→ `Scenario`, `Module`, `SuperTool`

---

## 6. Cohérence PGCD / PPCM

PGCD (cœur minimal commun) :
- Quels objets sont absolument indispensables ?
  - Object, Attribute, Method, Relation, Rule, Vector, Scenario, Agent, Project…

PPCM (extensions possibles) :
- Quels objets peuvent être ajoutés par domaine ?
  - Domain:Education.Course
  - Domain:SaaS.Subscription
  - etc.

Vérifier :
- que le MetaSchema CORE n’est pas pollué par des détails de domaine
- que les extensions se font bien par héritage et non par duplication.

---

## 7. Tests de MetaSchema

Prévoir :
- 2–3 “mini univers” :
  - un projet simple (site vitrine)
  - un projet SaaS
  - un module interne (ex : Blog Eurkai)
- Vérifier que ces 3 univers peuvent être décrits **sans ajouter un nouvel objet CORE**.

Si oui → MetaSchema CORE validé.  
Si non → identifier le manque → corriger → re-tester.

---

Une fois cette check-list passée, ton MetaSchema peut être considéré comme **stabilisé v1**, prêt pour les tests T1/T2/T3 et la création progressive d’objets via le cockpit.
