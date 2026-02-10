# EURKAI_COCKPIT — VERSIONING_POLICY (v1)

Objectif: éviter le "cockpit de cockpit" tout en permettant au cockpit de **s'enrichir lui-même**.

## 1) Un seul cockpit
- Ce dépôt est **le** cockpit.
- Toute évolution se fait **dans ce cockpit**, jamais via un "second cockpit".

## 2) Versioning (SemVer)
- `MAJOR.MINOR.PATCH`
- PATCH: bugfix / refactor interne (aucun changement de contrat)
- MINOR: ajout backward-compatible (nouveaux champs optionnels, nouveaux endpoints non destructifs)
- MAJOR: breaking changes (contrats, endpoints, schémas) — à éviter; si nécessaire: migration + compat.

## 3) Contracts-first
- Chaque module/brique expose un **contrat** (API + manifest + CLI).
- Tant que le contrat est respecté: l'implémentation peut évoluer.
- Tout changement de contrat => version bump + notes de migration.

## 4) Layers (socles)
- Un layer "verrouillé" = tests verts + release tag.
- Modif d'un layer: seulement via
  - migration DB (si nécessaire)
  - maintien de compat (MINOR) ou release MAJOR explicitement.

## 5) Self-enrichment (bootstrap)
- Le cockpit peut générer de nouvelles briques/modules **à condition**:
  - d'écrire dans un dossier/version ciblé
  - de produire tests + doc + manifest + CLI
  - de passer le pipeline de validation (C08)

## 6) Définition "stable"
Stable = tests verts + contrats versionnés + backup GitHub fonctionnel.
