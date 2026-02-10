# PROMPT 03 — Construire l’éditeur de schémas / Bundles

Tu es une IA développeuse front.

Lis :
- `SPEC_03_schemas_bundles_catalog.md`
- Le JSON global défini en 00_GLOBAL
- Le code existant des étapes 01 et 02.

Tâche :
- Implémenter une page **Schémas** qui permet :
  1. De sélectionner un ObjectType via un input à saisie semi-automatique (suggestions après 2 caractères).
  2. De visualiser et éditer le schéma de Bundle :
     - `elementName`,
     - `expectedObjectType`,
     - `quantity`,
     - `required`.
  3. D’instancier une **instance d’exemple** pour le catalogue via un bouton :
     - créer une entrée dans `catalog.examples` basée sur ce schéma.

Contraintes :
- Respecter les structures JSON existantes.
- Séparer le code en :
  - rendu UI,
  - fonctions de mise à jour des données,
  - logique d’ajout dans le catalogue.

Output :
- Code HTML/JS pour cette page ou module réutilisable.
