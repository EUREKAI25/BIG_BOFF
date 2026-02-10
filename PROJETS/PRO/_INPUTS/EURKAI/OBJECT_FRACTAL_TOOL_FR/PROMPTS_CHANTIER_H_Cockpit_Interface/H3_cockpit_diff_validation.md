
# H3 — Vue Diff + Validation manuelle dans le Cockpit

## Objectif
Permettre à l’utilisateur de :
- voir la différence entre l’état actuel de la fractale et les propositions EURKAI,
- accepter / refuser / ajuster les modifications,
- journaliser les décisions.

## Ce que tu dois produire
- Un format de “diff fractal” lisible :
  - nouveaux objets,
  - objets modifiés,
  - objets supprimés ou désactivés,
  - modifications de bundles (attributes, methods, rules, relations, tags).
- Une API pour récupérer un diff proposé par un scénario / SuperTool.
- Un modèle d’interaction dans le Cockpit :
  - liste de changements,
  - détail par changement,
  - boutons “accepter / rejeter / modifier”,
  - confirmation explicite avant application.

## Contraintes
- L’application d’un diff doit passer par un SuperTool (SuperUpdate / SuperCreate / SuperDelete).
- Chaque action appliquée doit être loggée avec :
  - l’input source,
  - le scénario à l’origine de la proposition,
  - la décision de l’utilisateur.
