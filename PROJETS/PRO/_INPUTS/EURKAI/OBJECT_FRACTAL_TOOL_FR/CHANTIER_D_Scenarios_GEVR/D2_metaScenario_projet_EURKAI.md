
# PROMPT D2/5 — MetaScénario “Projet EURKAI”

## CONTEXTE

Les scénarios GEVR de base fonctionnent (D1/4).  
Tu peux déjà :
- analyser un objet,
- lancer une vérification,
- produire un rapport.

Tu dois maintenant définir le **MetaScénario “Projet EURKAI”**, qui :

> prend en entrée une **idée, un brief, un cahier des charges ou un schéma complet**,  
> et produit une **structure de projet EURKAI** (objets, lineages, scénarios, ressources minimales).

Ce MetaScénario est le cœur du pipeline :
- Idée → Projet structuré.

## CE QUE TU AS EN INPUT

- Une entrée textuelle ou structurée :
  - ex : “Je veux un blog EURKAI sur la créativité”,
  - ou un brief plus long,
  - ou un début de schéma d’objets.

- Les capacités existantes :
  - scénarios GEVR,
  - MetaSchema,
  - MetaRules,
  - cockpit.

## CE QUE TU DOIS PRODUIRE

1. La **définition conceptuelle** du MetaScénario “Projet EURKAI” :

   - phases G/E/V/R explicites,
   - sous-scénarios appelés (ex : analyse du besoin, mapping vers ObjectTypes, création d’un arbre de projet).

2. Un **schéma de sortie** standard pour un “Projet EURKAI”, par exemple :

   ```json
   {
     "projectId": "...",
     "name": "...",
     "objects": [...],
     "relations": [...],
     "scenarios": [...],
     "tags": [...]
   }
   ```

3. Des **exemples** :
   - une idée en une phrase,
   - un brief plus structuré,
   - et pour chaque, la structure de projet générée.

4. Une proposition de **stratégie d’enrichissement itératif** :
   - comment le projet peut être progressivement complété,
   - quels scénarios secondaires interviennent ensuite.

## CONTRAINTES

- Le MetaScénario ne doit pas dépendre d’un type de projet unique :
  - blog,
  - labo,
  - SaaS,
  - etc. → doivent être possibles.
- La structure produite doit être :
  - compatible avec la fractale,
  - exploitable par les scénarios futurs (D3, E, F).

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. Une **description détaillée** du MetaScénario “Projet EURKAI”.
2. Le format canonique du “Projet EURKAI” (output).
3. Des exemples d’entrées + sorties.
4. Des cas de test (briefs variés et réponses attendues).

## CHECKLIST DE VALIDATION

- [ ] Le MetaScénario “Projet EURKAI” est défini de manière générique.
- [ ] Il peut accepter au moins 3 types d’entrées (phrase, brief, schéma).
- [ ] Il produit une structure réutilisable dans EURKAI (objets, relations, scénarios).
- [ ] Tu as fourni des exemples + cas de test cohérents.
