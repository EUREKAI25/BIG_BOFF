
# I1 — Génération de projet EURKAI complet à partir d’un brief

## Objectif
Prendre en entrée :
- une phrase,
- un brief,
- un cahier des charges,
- un document structuré (JSON / manifest / schéma),
et produire automatiquement un **Projet EURKAI** structuré :
- objets,
- lineages,
- scénarios,
- modules,
- manifest de projet.

## Ce que tu dois produire
- La définition précise des inputs acceptés (formats supportés).
- La logique d’analyse d’intention (type de projet, domaine, usages).
- Le pipeline de génération :
  - mapping vers ObjectTypes / Modules / Scénarios,
  - création d’un squelette de projet complet,
  - production du manifest projet.

## Contraintes
- S’appuyer sur le MetaScénario “Projet EURKAI” + Orchestrate + GEVR.
- Ne pas générer de code ici : seulement la structure fractale + manifest.
