
# PROMPT D1/4 — Scénarios GEVR de base

## CONTEXTE

À ce stade :
- ERK est capable d’évaluer des règles et de proposer des actions (B1/1–B3/3),
- le MetaSchema et les MetaRules de structure/relations sont en place (C1/1–C3/3),
- le cockpit gère la fractale de manière stable.

Tu dois maintenant implémenter des **Scénarios GEVR de base** :
- GEVR = **GET → EXECUTE → VALIDATE → RENDER**,
- chaque scénario est une séquence d’étapes,
- chaque étape peut interagir avec la fractale, ERK, les MetaRules.

## CE QUE TU AS EN INPUT

- La définition conceptuelle de GEVR :
  - GET : récupérer les données nécessaires,
  - EXECUTE : appliquer une action / transformation,
  - VALIDATE : vérifier la cohérence (structure + ERK),
  - RENDER : produire un résultat lisible (log, vue, rapport…).

- Un premier besoin minimal :
  - scénario “Analyser un objet et compléter ses bundles”,
  - scénario “Créer un squelette de projet à partir d’un type de base”.

## CE QUE TU DOIS PRODUIRE

1. Un **modèle générique de scénario GEVR**, par exemple :

   ```json
   {
     "id": "Scenario.AnalyzeObject",
     "steps": [
       { "phase": "GET", "action": "loadObject", "params": { ... } },
       { "phase": "EXECUTE", "action": "runMetaRules", "params": { ... } },
       { "phase": "VALIDATE", "action": "checkErrors", "params": { ... } },
       { "phase": "RENDER", "action": "renderReport", "params": { ... } }
     ]
   }
   ```

2. Une **API d’exécution** :

   - `runScenario(scenarioId, input) -> { status, logs, output }`

3. Au moins **deux scénarios concrets** :
   - `Scenario.AnalyzeObject`
   - `Scenario.CreateProjectSkeleton` (simple)

4. Des **exemples d’exécution** complets :
   - input,
   - déroulé des étapes,
   - output.

## CONTRAINTES

- Les scénarios doivent être :
  - déclaratifs,
  - composables,
  - loggés (chaque étape doit laisser une trace).
- L’exécution doit passer systématiquement par :
  - une phase VALIDATE (MetaRules, ERK),
  - une phase RENDER claire.

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. La **structure canonique** d’un scénario GEVR (format JSON/objet).
2. La description de l’API `runScenario`.
3. La définition de 2 scénarios concrets (même en pseudo-code).
4. Des **exemples** d’exécution avec input/output.
5. Des **cas de test** (scénario qui passe, scénario qui échoue).

## CHECKLIST DE VALIDATION

- [ ] Le format d’un scénario GEVR est clairement défini et réutilisable.
- [ ] `runScenario` peut exécuter au moins deux scénarios différents.
- [ ] Chaque exécution inclut des logs par phase G/E/V/R.
- [ ] Tu as fourni des exemples + cas de test pour valider le pipeline.
