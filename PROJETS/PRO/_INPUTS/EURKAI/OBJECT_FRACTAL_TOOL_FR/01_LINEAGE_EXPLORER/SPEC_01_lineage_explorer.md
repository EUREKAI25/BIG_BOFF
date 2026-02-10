# SPEC 01 — Explorateur de lineages

But : implémenter la vue **Explorateur de lineages**.

Layout (V1) :
- **Gauche** : arbre des ObjectTypes (lineages).
- **Centre** : vue fractale (complète ou partielle) de l’objet sélectionné :
  - affiche sa lignée (ancêtres → objet courant),
  - affiche une représentation textuelle de XFractal à une profondeur donnée.
- **Haut ou centre** : fil d’Ariane des objets de niveau 1 (racines) triés par ordre alphabétique.

Fonctionnalités cœur :
1. **Arbre des ObjectTypes**
   - Afficher tous les ObjectTypes sous forme d’arbre, selon leur lineage.
   - Un clic sur un ObjectType le sélectionne.
   - Drag & drop d’un ObjectType pour le re-parenté sous un autre :
     - recalcul du parent,
     - recalcul du lineage,
     - validation du lineage via la regex,
     - mise à jour des données JSON.

2. **Saisie manuelle de lineage**
   - Input permettant de saisir un lineage complet.
   - Le système parse la chaîne, vérifie la nomenclature,
   - crée les ObjectTypes manquants si nécessaire,
   - marque les nouveaux comme `toFinalize: true`.

3. **Vue fractale au centre**
   - Pour l’ObjectType sélectionné :
     - afficher la chaîne d’ancêtres (un par ligne),
     - afficher, pour chaque niveau, la contribution à XFractal (simple texte pour la V1).
   - Contrôle de profondeur (slider ou champ numérique) :
     - limite l’expansion de la fractale.
   - Si la limite est atteinte, afficher un placeholder du type :
     - “Suite… (appeler la méthode de vecteur pour continuer)”.

Ce step se concentre sur :
- le rendu de l’arbre,
- la sélection,
- le drag & drop de re-parenting,
- la création d’objets par saisie de lineage,
- une première vue textuelle de la fractale.

Pas besoin pour l’instant de :
- tags / alias,
- console de test avancée,
- design visuel poussé.
