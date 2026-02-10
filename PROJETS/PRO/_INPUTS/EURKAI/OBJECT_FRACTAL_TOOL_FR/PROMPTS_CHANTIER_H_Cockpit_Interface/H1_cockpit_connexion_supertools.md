
# H1 — Connexion du Cockpit aux SuperTools (lecture seule + actions basiques)

## Objectif
Brancher concrètement le Cockpit sur le backend EURKAI via les SuperTools (SuperRead, SuperEvaluate) :
- afficher la fractale réelle (objets, lineages, bundles),
- exécuter des audits et validations,
- sans aucun write à ce stade (lecture seule + rapports).

## Ce que tu dois produire
- Les points d’entrée API côté backend pour :
  - charger la fractale ou un sous-ensemble (SuperRead),
  - lancer des audits MetaRules / MetaRelations / MetaTests (SuperEvaluate).
- Le contrat de données entre Cockpit et backend pour :
  - la vue “arbre d’objets + lineage”,
  - la vue “fiche d’objet + bundles”,
  - la vue “rapport d’audit”.
- Un design d’intégration minimal côté Cockpit :
  - comment il récupère et met à jour ces vues,
  - comment il déclenche les audits (boutons / actions).

## Contraintes
- Aucun write : pas de création / modification d’objet.
- Utiliser uniquement les SuperTools (pas d’accès direct à la base).
- Prévoir la pagination / filtrage si la fractale devient volumineuse.
