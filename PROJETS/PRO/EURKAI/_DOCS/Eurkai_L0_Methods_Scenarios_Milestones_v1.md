# Eurkai — Layer 0 — Méthodes, Scenarios, Orchestration et Milestones (v1)

## 1. Méthode : contrat minimal
Toute méthode expose (au minimum) :
- input
- output
- goal
- description
- orchestrate_scenario (unique)

## 2. OrchestrateScenario (unique)
La méthode référence un unique scenario d’orchestration dont le nom est :
- simple
- logique
- stable
- et explicite

Recommandation de pattern de nommage :
- `condition_action_object`
- ou, quand c’est une action “liste” : `parent_method_list` (comme tu l’indiques)

## 3. MilestoneScenario
L’OrchestrateScenario organise 1..N milestones.

Deux assertions à figer (cohérence et clarté) :
- `OrchestrateScenario.milestone_scenario_list.count >= 1`
- `OrchestrateScenario.executehook.milestone_scenario_list.count >= 1`

La première dit : “un orchestrate scenario n’existe pas vide”.
La seconde dit : “l’exécution hookée ne peut pas ignorer les milestones”.

> Oui : c’est clair et optimal. Le seul piège : éviter d’avoir 2 sources de vérité pour le comptage (utiliser la même liste, pas une copie).

## 4. Ce que ça implique côté modularité
- Chaque milestone est lui-même un scenario (donc composable, testable, substituable).
- Les méthodes restent des “contrats” : la logique est portée par scenarios + formulas + règles.

## 5. Formulas
- `Formula` n’est pas toujours bool.
- Les formulas couvrent l’ensemble des fonctions atomiques (math/logique/manipulation) permettant d’articuler le langage et d’exécuter des opérations.
- Seules les formulas de la catégorie “conditional” (ou équivalent) sont utilisées pour `validate` (retour bool) dans les transitions / checks.

## 6. Optimisation IA (batch par WHAT)
Pendant l’exécution de tâches par des IA :
- regrouper par `what` (liste d’objets)
- exécuter plusieurs missions “how” sur le même `what` dans un batch
- réduire IO et appels IA
