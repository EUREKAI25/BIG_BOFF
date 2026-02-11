# SPEC 00 — Vue d’ensemble

Cet outil web interne (HTML/JS) s’appelle **Object Fractal Tool**.

Objectif général :
- Gérer la **généalogie** (lineages) des **ObjectTypes**.
- Visualiser la **fractale** (complète ou partielle) de n’importe quel ObjectType sélectionné.
- Distinguer, pour chaque élément de XFractal :
  - ce qui est **owned** (défini à ce niveau),
  - ce qui est **inherited** (hérité d’un ancêtre),
  - ce qui est **injected** (logiques transversales, tags, providers…).
- Manipuler et inspecter, pour chaque objet :
  - les attributs,
  - les méthodes secondaires,
  - les règles ERK,
  - les relations (3 relations fondamentales, le reste en alias).
- Gérer les **tags**, **catégories** et **alias**.
- Éditer les **schémas de Bundle** (types d’éléments attendus, quantité, required).
- Instancier des exemples pour alimenter un **catalogue** (vecteurs).
- Tester des expressions simples du type : `methodA(inputs).result.message` dans une mini console.

Cible technique V1 :
- Front : HTML + JavaScript (framework léger possible mais non obligatoire).
- Données : un ou plusieurs fichiers JSON (backend à venir plus tard si besoin).

Concepts de base :
- Chaque objet est un **Bundle** : une liste d’éléments, chaque élément étant lui-même un objet (Bundle).
- Pour tout objet `X`, il existe `XFractal` qui décrit à un instant donné :
  - les attributs,
  - les méthodes secondaires,
  - les règles ERK,
  - les relations.
- Les ObjectTypes sont organisés en **lineages** (chaînes d’héritage).
- Pour chaque objet, l’outil doit permettre de voir, pour chaque élément de son XFractal :
  - s’il est owned / inherited / injected,
  - et, si non-owned, sa **source exacte** (ancêtre ou logique transversale).
