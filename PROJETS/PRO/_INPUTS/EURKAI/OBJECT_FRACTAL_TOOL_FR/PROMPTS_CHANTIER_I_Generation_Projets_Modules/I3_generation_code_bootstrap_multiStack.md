
# I3 — Génération de code & bootstrap multi-stack à partir du manifest

## Objectif
Prendre un manifest de projet EURKAI (produit par I1) et :
- générer le squelette de code correspondant (stack(s) choisie(s)),
- organiser les modules dans une arborescence de fichiers,
- préparer un projet exécutable (mais encore minimal) côté technique.

## Ce que tu dois produire
- Une stratégie de mapping manifest → fichiers (par stack : ex. Node/React, Python, etc.).
- Un modèle de `fileTree` standard, aligné avec les choix de structure d’EURKAI.
- La définition d’un pipeline :
  - choix de stack(s),
  - génération des fichiers,
  - ajout de README / docs minimales,
  - préparation de scripts (install, run, test basique).

## Contraintes
- Respecter la distinction :
  - code généré vs code humain (zones à ne pas écraser).
- S’appuyer sur ce qui a été posé en F2/F3, en l’enrichissant.
