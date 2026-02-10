
# PROMPT C1/1 — Lineages assistés (suggestions d’héritage)

## CONTEXTE

Le cockpit EURKAI est opérationnel :
- les objets et leurs lineages sont créés,
- la fractale est visualisable,
- ERK sait déjà évaluer des règles simples (B1/1, B2/2),
- mais la définition des **parents** et des **héritages** est encore largement manuelle.

Cette étape vise à mettre en place un système de **lineages assistés** :
- quand un nouvel objet est créé ou qu’un lineage est incomplet,
- le système peut proposer un ou plusieurs parents probables,
- à partir de la structure existante.

## CE QUE TU AS EN INPUT

- Le store fractal :
  - objets avec leurs lineages existants,
  - position dans l’arbre,
  - bundles partiellement définis.
- Des **patterns** implicites dans les noms de lineages, par exemple :
  - `Core:Agent:LLM`,
  - `Core:Agent:Human`,
  - `Agency:Project:Blog`.

Tu peux supposer :
- que certains objets n’ont pas encore de parent déclaré,
- que certains lineages sont tronqués ou approximatifs.

## CE QUE TU DOIS PRODUIRE

1. Une logique de **détection de parent candidat** pour un objet donné, basée sur :
   - des similarités de noms,
   - des patterns dans les lineages,
   - éventuellement des règles ERK simples.

2. Une API du genre :
   - `suggestParents(objectId) -> [ { parentId, score, reason } ]`

3. L’intégration avec le cockpit :
   - pour qu’en sélectionnant un objet “orphelin” ou incomplet,
     le système affiche une liste de parents suggérés,
     avec une indication de confiance.

4. Des **exemples concrets** :
   - cas où la suggestion est évidente,
   - cas où plusieurs parents sont possibles,
   - cas où aucune suggestion n’est raisonnable.

## CONTRAINTES

- Aucune suggestion ne doit être appliquée automatiquement :
  - la décision finale reste humaine (ou via un scénario plus tard).
- Le système doit clairement indiquer :
  - qu’il s’agit de suggestions,
  - les raisons de chaque suggestion (pattern, similarité, etc.).
- La logique doit être conçue pour pouvoir être enrichie plus tard
  (ex : via ERK, via statistiques, via IA).

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. Une description de la **stratégie de suggestion** :
   - comment tu identifies les candidats parents,
   - quels critères tu utilises (nom, profondeur, type, tags…).

2. La définition de la **structure de retour** :
   - `parentId`,
   - `score` (0–1 ou 0–100),
   - `reason` (texte court).

3. Des **exemples** :
   - input = objet X (avec ses métadonnées),
   - output = liste de parents suggérés.

4. Des **cas de test** :
   - objet avec parent évident,
   - objet ambigu,
   - objet unique / sans parent.

## CHECKLIST DE VALIDATION

- [ ] Pour tout objet sans parent clair, le système peut fournir zéro, une ou plusieurs suggestions.
- [ ] Les suggestions sont accompagnées de scores et de raisons.
- [ ] Aucun changement n’est fait à la fractale sans validation explicite.
- [ ] Tu as fourni plusieurs exemples + cas de test pour vérifier le comportement.
