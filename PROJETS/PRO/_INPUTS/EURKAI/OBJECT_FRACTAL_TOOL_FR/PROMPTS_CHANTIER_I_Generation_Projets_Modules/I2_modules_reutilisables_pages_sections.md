
# I2 — Modules réutilisables (pages, sections, composants, templates)

## Objectif
Formaliser le type d’objet `Module` dans la fractale EURKAI et préparer :
- des modules UI réutilisables (pages, sections, composants),
- des templates de stratégie / offres / flows,
utilisables par I1 et par les futurs scénarios.

## Ce que tu dois produire
- La définition de l’ObjectType `Module` :
  - attributs (nom, type, domaine, compatibilité, version, etc.),
  - méthodes (render, export, validate…),
  - relations (depends_on Seeds, Styles, Scénarios…),
  - règles (où et comment il peut être utilisé).
- Un modèle de catalogue de modules :
  - comment les lister,
  - comment les tagger,
  - comment les sélectionner automatiquement en fonction d’un brief.

## Contraintes
- Ne pas entrer dans le code front réel : rester au niveau structure / manifest.
- Garder `Module` générique (pas seulement pour le web : appli mobile, email, flow…).
