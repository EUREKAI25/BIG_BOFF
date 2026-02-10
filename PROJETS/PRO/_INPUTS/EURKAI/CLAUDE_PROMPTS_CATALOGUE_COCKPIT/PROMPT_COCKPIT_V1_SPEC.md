# 🖥️ Prompt Claude — Cockpit Eurkai v1 “vierge mais complet”

## 🎯 OBJECTIF
Concevoir la **première version du Cockpit Eurkai** qui soit :
- entièrement **vierge côté données métier** (aucun objet pré-créé dans les catalogues),
- totalement **opérationnel côté structure**,
- capable de :
  - se connecter aux catalogues (vides au départ),
  - créer de nouvelles instances via des formulaires dynamiques,
  - valider ces instances via ERK,
  - afficher la fractale de chaque objet (owned / inherited / injected) dès que le MetaSchema et les catalogues seront alimentés.

Je veux un cockpit qui soit **un pur outil de manipulation de la fractale et des catalogues**, pas un système avec des règles métier déjà figées.

---

## 🧩 CONTRAINTES MAJEURES

1. **Aucune donnée métier pré-remplie.**
   - Pas de SuperCreate, pas de Projets, pas de Modules concrets.
   - Seulement :
     - la structure de base,
     - les connecteurs vers MetaSchema / catalogues,
     - les formulaires dynamiques,
     - la vue fractale.

2. **Tout est objet.**
   - Formulaires, champs, vues, panneaux, etc. sont eux-mêmes des objets (ou au moins pensés comme tels).
   - Le cockpit manipule des “instances d’objets” qui correspondent aux entrées des catalogues ou à d’autres types définis dans MetaSchema.

3. **Piloté par MetaSchema + Catalogue.**
   - Le cockpit ne “connaît” pas les types en dur :
     - il lit la structure des types via MetaSchema,
     - il lit les définitions ERK via le Catalogue ERK,
     - il génère les formulaires dynamiquement à partir de ça.

4. **Langages / Patterns déjà posés :**
   - ERK pour les règles et validations.
   - GEVR pour la logique de scénario (Get / Execute / Validate / Render).
   - Fractale XFractal pour owned / inherited / injected.

---

## 🧱 CE QUE TU DOIS PRODUIRE

Tu dois produire un document **COCKPIT_V1_SPEC.md** décrivant :

### 1. L’architecture globale du cockpit

- Backend minimal (API) :
  - endpoints pour :
    - lister les types d’objets (depuis MetaSchema / Catalogue),
    - lister les instances existantes d’un type,
    - créer / mettre à jour / supprimer une instance,
    - valider une instance via ERK,
    - récupérer la vue fractale d’un objet (simulée / mock si nécessaire).

- Frontend (UI) :
  - sidebar / panneau pour choisir le type d’objet (ObjectType, CatalogueEntryType, etc.),
  - zone centrale pour :
    - l’éditeur de formulaire dynamique,
    - la vue fractale liée à l’objet sélectionné,
  - panneau secondaire (ou section) pour :
    - logs / résultats de validation ERK,
    - aperçu ERK brut si utile.

### 2. Le système de formulaires dynamiques

Tu dois expliquer **comment** le cockpit :

- lit la description d’un type d’objet (via MetaSchema / Catalogue),
- en déduit :
  - la liste des champs (label, type, required, etc.),
  - la nature du field (input / textarea / select / checkbox / radio),
- construit un formulaire **sans rien en dur**, à partir de cette description :
  - si un attribut a des options → select / radio / checkbox,
  - si c’est un texte long → textarea,
  - sinon → input text / number, etc.

⚠️ Tu n’as PAS besoin de lister tous les types de champs HTML ; il suffit de définir la logique et les quelques types principaux.

### 3. Le cycle GEVR pour la création / édition d’une instance

Décrire en détail (logique, pas forcément en code) :

- GET :
  - récupérer la structure du type (MetaSchema),
  - récupérer éventuellement les valeurs actuelles (si edition).

- EXECUTE :
  - créer / mettre à jour l’instance à partir des valeurs du formulaire.

- VALIDATE :
  - exécuter les règles ERK associées au type / instance,
  - renvoyer une liste d’erreurs / warnings.

- RENDER :
  - renvoyer au frontend :
    - l’instance mise à jour,
    - les résultats ERK,
    - la représentation fractale (même si au début elle est en version mock).

### 4. La vue fractale dans le cockpit

Tu dois décrire comment le cockpit :

- reçoit pour un objet :
  - la liste de ses attributs/méthodes/règles/relations,
  - la distinction owned / inherited / injected,
- affiche cette information :
  - par exemple : code couleur, icône, légende,
  - avec possibilité de filtrer / masquer certains niveaux,
- permet de naviguer dans la fractale :
  - cliquer sur un parent dans le fil d’Ariane,
  - descendre dans les enfants,
  - voir la source d’un élément non-owned.

Pour l’instant, tu peux supposer qu’un endpoint renverra un JSON déjà structuré ; ton rôle est de spécifier le format de ce JSON et comment l’UI l’affiche.

### 5. Intégration avec ERK

Tu dois expliquer :
- comment les règles ERK associées à un type ou à une instance sont :
  - affichées (nom, catégorie, erk_id),
  - exécutées (qui appelle quoi),
  - présentées à l’utilisateur (erreurs, warnings, suggestions),
- comment le cockpit permet éventuellement :
  - de voir le bloc ERK associé,
  - mais **pas encore** de l’éditer librement (ça pourra venir après).

---

## 🚫 CE QUE TU NE DOIS PAS FAIRE

- Ne pas injecter de données métiers concrètes.
- Ne pas créer d’objets spécifiques comme SuperCreate, Project:Website, etc.
- Ne pas “définir” à la place de MetaSchema ou du Catalogue ce qui doit rester piloté par moi.

Tu décris uniquement :
- la structure,
- les contrats d’API,
- les formats d’échange,
- les comportements génériques du cockpit v1.

---

## 📤 LIVRABLE ATTENDU

Un fichier unique **COCKPIT_V1_SPEC.md**, structuré comme une spécification fonctionnelle + technique légère, incluant :

1. Architecture globale (backend + frontend).
2. Cycle de vie complet d’une instance via formulaire (GEVR).
3. Logique de formulaire dynamique basé sur MetaSchema + Catalogue ERK.
4. Vue fractale (format de données + rendu UI).
5. Intégration avec ERK pour la validation.

Le tout pour une **version vierge** du cockpit (pas de seed métier), prête à être branchée sur des catalogues et un MetaSchema que je remplirai ensuite via l’UI.
