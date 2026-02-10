
# PROMPT B3/3 — ERK → Actions système (modifications contrôlées)

## CONTEXTE

Les étapes B1/1 et B2/2 ont produit :
- un interpréteur ERK capable de parser des règles,
- d’évaluer ces règles avec conditions et contexte,
- de retourner des résultats détaillés,
- le tout **sans effet de bord**.

Tu passes maintenant à l’étape où certaines règles ERK peuvent :
- **proposer des actions** à appliquer sur la fractale (ajout de tag, marquage d’un objet, activation d’une méthode, etc.),
- mais ces actions doivent être :
  - listées,
  - contextualisées,
  - **jamais appliquées automatiquement sans validation**.

## CE QUE TU AS EN INPUT

- L’infrastructure ERK de B1/1 et B2/2 :
  - parser,
  - AST,
  - évaluation,
  - console.
- Le store fractal (objets, bundles, tags, etc.).
- La capacité à interagir avec :
  - les attributs,
  - les relations,
  - les tags,
  - certains flags d’état.

## CE QUE TU DOIS PRODUIRE

1. Un mécanisme pour que certaines règles ERK puissent **décrire des actions** du type :

   - `SUGGEST addTag(this, "core")`
   - `SUGGEST mark(this, "toReview")`
   - `SUGGEST enableMethod(this, "prompt")`

   Ces actions doivent être :
   - collectées,
   - structurées,
   - retournées à l’interface (cockpit / console).

2. Un **format standard** pour une action proposée, par exemple :

   ```json
   {
     "type": "addTag",
     "target": "Object:Agent:Core",
     "params": { "tag": "core" },
     "reason": "rule: ensure_core_tag"
   }
   ```

3. Un flux d’exécution clair :

   - L’utilisateur ou un agent IA demande : `ERK.apply(objectId, ruleName)`.
   - ERK :
     - évalue la règle,
     - produit éventuelles suggestions d’actions,
     - les retourne **sans les appliquer**.
   - Une autre couche (UI / Orchestrate) décide d’appliquer ou non ces actions.

4. Des **exemples de règles ERK** qui génèrent de telles actions,
   avec les cas de test associés.

## CONTRAINTES

- AUCUNE action ne doit être appliquée automatiquement dans cette étape :
  - B3/3 ne fait que **proposer**, pas modifier le store.
- Les actions doivent être :
  - idempotentes (faciles à appliquer une seule fois),
  - bien ciblées (référence claire à l’objet concerné),
  - tracées (quelle règle les a générées).
- Tu dois veiller à ce que :
  - les erreurs de génération d’actions ne compromettent pas l’évaluation des règles.

## FORMAT DE SORTIE

Ta réponse doit contenir :

1. Une **spécification textuelle** de la manière dont ERK exprime une action proposée :
   - syntaxe dans la règle ERK,
   - structure interne (objet Action).

2. Une description de l’API associée, par exemple :
   - `evaluateErkWithActions(ast, context) -> { status, actions[], log }`

3. Des **exemples complets** :
   - règle ERK,
   - objet cible,
   - contexte,
   - liste d’actions proposées.

4. Des **cas de test** :
   - règle sans action,
   - règle avec une action,
   - règle avec plusieurs actions,
   - règle invalide.

## CHECKLIST DE VALIDATION

- [ ] Les règles peuvent maintenant générer des **actions proposées** sous une forme structurée.
- [ ] Aucune action n’est appliquée automatiquement à la fractale.
- [ ] Les actions proposées incluent :
      - le type,
      - la cible,
      - les paramètres,
      - la règle d’origine.
- [ ] L’évaluation ERK reste robuste, même si une règle tente de générer des actions invalides.
- [ ] Tu as fourni plusieurs exemples de règles + actions + cas de test pour valider le comportement.
