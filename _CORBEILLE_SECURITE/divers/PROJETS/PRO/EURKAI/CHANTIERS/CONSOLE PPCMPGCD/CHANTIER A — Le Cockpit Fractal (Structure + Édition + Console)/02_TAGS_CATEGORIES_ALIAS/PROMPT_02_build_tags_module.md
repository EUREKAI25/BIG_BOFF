# PROMPT 02 — Construire le module Tags / Catégories / Alias

Tu es une IA développeuse front.

Lis :
- `SPEC_02_tags_categories_alias.md`
- Les structures JSON définies en 00_GLOBAL
- Et l’implémentation de 01_LINEAGE_EXPLORER.

Tâche :
- Étendre l’Explorateur de lineages avec :
  1. Une **sidebar des tags** (à droite) :
     - liste alphabétique,
     - scrollable,
     - tags draggable.
  2. L’**affectation de tags** :
     - drag & drop d’un tag sur un nœud de l’arbre,
     - mise à jour du JSON (tags de l’ObjectType).
  3. La gestion des **tags comme catégories** :
     - clic droit sur un tag pour :
       - définir `isCategory`,
       - choisir une `parentCategory` parmi les autres tags.
  4. La gestion des **alias** :
     - sur la vue de détail de l’ObjectType / vecteur actif,
       - afficher la liste des alias,
       - permettre d’en créer un nouveau.

Contraintes :
- Réutiliser le même JSON que l’étape 01.
- Séparer clairement le code :
  - UI,
  - mise à jour des données.

Output :
- Code HTML/JS mis à jour avec :
  - sidebar des tags,
  - gestion des tags/catégories,
  - gestion des alias.
