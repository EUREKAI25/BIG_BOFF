
# PROMPT B1/1 — Interpréteur ERK minimal

## CONTEXTE
Tu travailles sur EURKAI.  
Le **Cockpit / Object Fractal Tool** est déjà opérationnel :  
- les objets, lineages et bundles (owned / inherited / injected) sont gérés,  
- les règles ERK sont stockées comme texte dans les RuleLists,  
- une console de test (mock) existe déjà.

Cette étape consiste à implémenter un **interpréteur ERK minimal** capable de :
- lire une règle ERK simple attachée à un objet,
- la parser,
- l’évaluer dans un contexte donné,
- retourner un résultat structuré.

L’objectif n’est PAS encore de modifier la fractale, mais de **comprendre** les règles.

## CE QUE TU AS EN INPUT

- Le store JSON interne du cockpit décrivant :
  - les ObjectTypes,
  - leurs bundles (attributes, methods, rules, relations),
  - les lineages.
- Pour chaque objet : une ou plusieurs règles ERK sous forme de texte brut.
- Une console qui permet déjà d’appeler des fonctions du style :
  - `evaluateRule(objectId, ruleName, context?)`.

Tu peux supposer que :
- les données du store sont cohérentes (validées en étape 99),
- les règles ERK sont syntaxiquement simples au départ.

## CE QUE TU DOIS PRODUIRE

1. Un **interpréteur ERK minimal** qui supporte au moins :
   - des règles de type “flags” / autorisations simples,
   - des expressions basiques (égalité, présence, booléens),
   - la résolution de `this` (l’objet courant),
   - des références simples à d’autres objets (par id / lineage).

2. Une **API interne** claire, par exemple :
   - `parseErk(ruleText) -> ast`
   - `evaluateErk(ast, context) -> { status, details }`

3. L’intégration avec la **console** existante :
   - pouvoir appeler depuis la console :
     - `ERK.eval(objectId, ruleName, context?)`
   - et recevoir un résultat lisible, par exemple :
     - `{ "ok": true, "rule": "enable_prompt", "reason": "flag set" }`.

4. Des **exemples concrets de règles ERK** adaptées à cette V1,
   ET des **cas de test** qui démontrent que l’interpréteur fonctionne.

## CONTRAINTES

- Ne modifie **pas** la structure du MetaSchema ni la logique de la fractale.
- Ne modifie **pas** les invariants de sécurité déjà posés (Layer 0).
- Ne crée **aucun effet de bord** : cette étape est en lecture seule.
- Le parsing doit être :
  - robuste sur les cas attendus,
  - tolérant : en cas d’erreur de syntaxe, retourner une erreur claire.
- Le design doit rester **simple et extensible**, pour préparer B2/2.

## FORMAT DE SORTIE

Tu dois fournir, dans ta réponse :

1. Une description structurée de l’architecture que tu proposes :
   - noms des fonctions principales,
   - responsabilités de chacune,
   - structure des objets `AST` et `Result`.

2. Des exemples de règles ERK compatibles avec cette version minimale,
   par exemple (en pseudo-syntaxe ERK) :
   - `enable: this.flags.contains("prompt_enabled")`
   - `allow: this.type == "Agent" AND this.priority == "natural"`

3. Des **exemples d’appels** via la console et des résultats attendus.

4. Des **propositions de tests** :
   - soit sous forme de pseudo-tests (liste de cas avec entrée / sortie attendue),
   - soit sous forme de squelettes de tests automatisables.

## CHECKLIST DE VALIDATION

Pour considérer B1/1 comme réussie, les conditions suivantes doivent être remplies :

- [ ] Une règle ERK simple associée à un objet peut être :
      chargée → parsée → évaluée → retourner un résultat structuré.
- [ ] La console permet d’appeler `ERK.eval(objectId, ruleName, context?)`
      et d’afficher un retour compréhensible.
- [ ] En cas de règle invalide, un message d’erreur clair est produit
      (sans planter le système).
- [ ] L’interpréteur est clairement conçu comme **extensible** pour B2/2.
- [ ] Tu as fourni plusieurs **exemples de règles + cas de test** pour valider le comportement.
