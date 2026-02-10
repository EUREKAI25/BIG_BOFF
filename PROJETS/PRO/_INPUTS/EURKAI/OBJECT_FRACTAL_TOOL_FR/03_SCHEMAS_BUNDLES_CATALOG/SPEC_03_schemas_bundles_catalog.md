# SPEC 03 — Schémas, Bundles & Catalogue

But : fournir une page pour définir/éditer les **schémas de Bundles** et instancier des exemples pour le **catalogue**.

Fonctionnalités :

1. **Sélection d’ObjectType**
   - Input avec saisie semi-automatique (suggestions après 2 caractères).
   - L’utilisateur choisit l’ObjectType dont il veut :
     - définir/éditer le schéma,
     - ou instancier un exemple.

2. **Éditeur de schéma de Bundle**
   - Pour l’ObjectType sélectionné, afficher la liste des éléments de Bundle :
     - `elementName`,
     - `expectedObjectType`,
     - `quantity` (min/max ou exact),
     - `required` (checkbox).
   - Permettre :
     - d’ajouter un élément,
     - de modifier un élément,
     - de supprimer un élément.

3. **Instantiation pour le catalogue**
   - Bouton “Instancier pour le catalogue” :
     - crée une instance d’exemple basée sur le schéma,
     - ajoute cette instance dans une section `catalog.examples` (JSON).

Remarque :
- Les schémas peuvent être pré-remplis automatiquement via héritage/tags, mais cette page permet un **ajustement manuel fin**.
- Il s’agit uniquement de structure (pas de logique métier exécutée ici).
