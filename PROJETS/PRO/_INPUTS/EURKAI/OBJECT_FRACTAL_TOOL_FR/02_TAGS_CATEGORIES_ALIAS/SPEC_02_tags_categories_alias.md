# SPEC 02 — Tags, Catégories & Alias

But : ajouter la gestion des **tags**, **catégories** et **alias**.

Fonctionnalités :

1. **Sidebar des tags**
   - Barre latérale (droite) listant tous les tags par ordre alphabétique.
   - Liste scrollable.
   - Chaque tag est draggable.

2. **Affectation de tags**
   - Drag & drop d’un tag sur un ObjectType dans l’arbre.
   - L’ObjectType reçoit ce tag dans ses métadonnées.
   - Plusieurs tags par ObjectType sont autorisés.

3. **Tags comme catégories**
   - Clic droit sur un tag dans la sidebar :
     - possibilité de basculer `isCategory` (true/false),
     - si `isCategory` est true, possibilité de définir `parentCategory` (un autre tag).
   - Permet de construire un système de catégories hiérarchiques à partir des tags.

4. **Gestion des alias**
   - Un **alias** est un nom court pointant vers un **vecteur** (lineage + éventuel state).
   - Interface minimale :
     - dans la vue de détail d’un ObjectType (ou vecteur), section “Alias” :
       - liste des alias existants,
       - formulaire ou bouton pour en ajouter un nouveau.
   - Un alias pourra être utilisé pour naviguer rapidement vers ce vecteur/objet.

Pas de backend pour l’instant : tout est en mémoire / JSON.
