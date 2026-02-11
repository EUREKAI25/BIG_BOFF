# PROMPT 01 — Construire l’Explorateur de lineages

Tu es une IA développeuse front.

Lis :
- `SPEC_01_lineage_explorer.md`
- Les fichiers de 00_GLOBAL (overview + metaschema + règles).

Tâche :
- Implémenter la vue **Explorateur de lineages** comme décrit :
  - Arbre des ObjectTypes à gauche.
  - Vue fractale / lignée au centre.
  - Input pour ajouter un objet par saisie de son lineage complet.

Contraintes :
- Utiliser HTML + JavaScript simple (framework léger possible mais non obligatoire).
- Utiliser un objet JSON en mémoire pour représenter :
  - les ObjectTypes,
  - leur parent / enfants,
  - leur chaîne de lineage.
- Implémenter :
  - rendu de l’arbre,
  - sélection d’un nœud au clic,
  - drag & drop de re-parenting (mise à jour du parent, du lineage, et du JSON),
  - parsing d’un lineage tapé et création des ObjectTypes manquants, en les marquant `toFinalize: true`.

Output :
- Code HTML/JS pour cette vue.
- Fonctions séparées pour :
  - le rendu de l’arbre,
  - la gestion de la sélection,
  - la gestion du drag & drop,
  - le parsing et l’ajout de lineages.
