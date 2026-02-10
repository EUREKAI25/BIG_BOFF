
# PROMPT C3/3 — MetaRelations & optimisation structurelle

## CONTEXTE

Après C2/2, les MetaRules de structure permettent de vérifier les invariants essentiels
(attributs obligatoires, méthodes minimales, etc.).

L’étape C3/3 se concentre sur :
- la qualité du **réseau de relations** entre objets,
- la détection de **cycles indésirables**,
- la mise en évidence de **relations redondantes** ou inutiles,
- des **propositions de simplification**.

Ce travail prépare directement les optimisations futures (PGCD/PPCM logiques en G1/9).

## CE QUE TU AS EN INPUT

- La fractale :
  - objets,
  - relations (`depends_on`, `related_to`, `inherits_from`, etc.),
  - lineages.
- Les MetaRules existantes (C2/2).
- Éventuellement, quelques règles ERK spécifiques aux relations.

## CE QUE TU DOIS PRODUIRE

1. Une **analyse des relations** permettant de détecter :

   - cycles (ex : A depends_on B, B depends_on C, C depends_on A),
   - chemins redondants (ex : A depends_on C directement et via B),
   - relations inutiles (jamais utilisées ou redondantes par construction).

2. Une API centrale, par ex. :

   - `analyzeRelations() -> { cycles[], redundancies[], suggestions[] }`

3. Des **suggestions de simplification**, par exemple :
   - “Supprimer relation X → Y (redondante avec X → Z → Y)”,
   - “Introduire un parent commun pour A et B au lieu de doubler les relations”.

4. Des **exemples concrets** :
   - un mini-graphe d’objets,
   - les anomalies détectées,
   - les suggestions produites.

## CONTRAINTES

- Aucune modification automatique de la fractale dans cette étape :
  - uniquement analyse + suggestions.
- Les algorithmes doivent être :
  - compréhensibles,
  - raisonnablement efficaces,
  - robustes aux structures modestement complexes.

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. Une description des **algorithmes ou heuristiques** utilisés :
   - détection de cycles,
   - détection de redondances.

2. La spécification de l’API `analyzeRelations()` :
   - format des cycles retournés,
   - format des redondances,
   - format des suggestions.

3. Des **exemples détaillés** :
   - graphe d’entrée,
   - résultat d’analyse.

4. Des **cas de test** :
   - graphe sans anomalies,
   - graphe avec cycles,
   - graphe avec redondances.

## CHECKLIST DE VALIDATION

- [ ] Les cycles dans les relations sont détectés et listés clairement.
- [ ] Les relations redondantes sont identifiées.
- [ ] Des suggestions de simplification sont proposées,
      sans être appliquées automatiquement.
- [ ] Tu as fourni plusieurs exemples + cas de test pour valider le comportement.
