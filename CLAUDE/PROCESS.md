# PROCESS — Création de projet

> Règles à suivre pour chaque création de projet via le workflow idée → artefacts.

**Dernière MAJ** : 2026-02-10

---

## 1. Structure de répertoire projet

Chaque projet est créé dans :
- `/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/` (professionnel)
- `/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PERSO/` (personnel)

### Arborescence standard

```
<NOM_PROJET>/
├── _SUIVI.md           # Suivi du projet (statut, historique, décisions)
├── _IDEES.md           # Notes d'idées futures pour ce projet
├── README.md           # Description, installation, utilisation
├── DROPBOX/            # Ressources externes (maquettes, PDFs, livres blancs)
├── PIPELINE/           # Artefacts de conception
│   ├── 00_SOURCE.json  # Export conversation initiale (si applicable)
│   ├── 01_BRIEF.md     # Brief structuré
│   ├── 02_CDC.md       # Cahier des charges
│   ├── 03_SPECS.md     # Spécifications techniques
│   └── 04_DEPLOY.md    # Plan de déploiement (si applicable)
├── src/                # Code source
├── tests/              # Tests
├── docs/               # Documentation complémentaire
└── dist/               # Build / livrable (si applicable)
```

---

## 2. Fichiers obligatoires

### _SUIVI.md

Template :

```markdown
# <NOM_PROJET> — Suivi

> [Description courte en une ligne]

**Statut** : 💡 idée | ⚪ à faire | 🟢 actif | 🟡 pause | 🔴 bloqué | 🟣 action requise | ⚫ archivé
**Créé** : AAAA-MM-JJ
**Dernière MAJ** : AAAA-MM-JJ

---

## Objectif

[Objectif clair et mesurable du projet]

## État actuel

[Où on en est, ce qui est fait, ce qui reste]

## Décisions

[Décisions importantes prises pendant le développement]

## Historique

- AAAA-MM-JJ : Création du projet
```

### _IDEES.md

Template :

```markdown
# Idées — <NOM_PROJET>

> Idées d'améliorations, de fonctionnalités futures, de variations.
> Pas d'engagement, juste un espace pour capturer les idées au fil de l'eau.

---

## Fonctionnalités

- [ ] Idée 1
- [ ] Idée 2

## Optimisations

- [ ] Idée 3

## Design

- [ ] Idée 4
```

### README.md

Template :

```markdown
# <NOM_PROJET>

> [Description courte]

## Installation

[Commandes ou étapes d'installation]

## Utilisation

[Comment lancer / utiliser le projet]

## Statut

Voir [_SUIVI.md](_SUIVI.md)
```

---

## 3. Workflow de création

### Étape 1 : Idée → BRIEF

1. Export conversation ChatGPT → `CLAUDE/TODO/<nom>.json`
2. Claude lit l'idée et produit `BRIEF_<NOM>.md` dans TODO/
3. Validation Nathalie

### Étape 2 : BRIEF → Projet structuré

1. Créer le répertoire projet dans `PROJETS/PRO/` ou `PROJETS/PERSO/`
2. Créer `_SUIVI.md`, `_IDEES.md`, `README.md`
3. Créer `PIPELINE/` et y copier le BRIEF (renommé `01_BRIEF.md`)
4. Copier la source originale dans `PIPELINE/00_SOURCE.json` si applicable
5. Enregistrer dans `CLAUDE/_PROJETS.md`

### Étape 3 : CDC

1. Claude produit `PIPELINE/02_CDC.md` (Cahier des Charges)
2. Validation Nathalie

### Étape 4 : SPECS

1. Claude produit `PIPELINE/03_SPECS.md` (Spécifications techniques)
2. Validation Nathalie

### Étape 5 : BUILD

1. Claude génère le code dans `src/`, `tests/`, etc.
2. Vérification des modules réutilisables dans `EURKAI/MODULES/`
3. Si code réutilisable → créer module standalone
4. Tests et validation

### Étape 6 : DEPLOY

1. Claude produit `PIPELINE/04_DEPLOY.md` (plan déploiement)
2. Déploiement effectif
3. Push GitHub
4. MAJ `_SUIVI.md` → statut 🟢 actif

---

## 4. Conventions

### Nommage
- Noms de projets : `UPPERCASE_SNAKE_CASE`
- Fichiers de suivi : toujours `_SUIVI.md` (jamais d'autre nom)
- Fichiers système : préfixe `_` (ex: `_IDEES.md`, `_TODO.md`)

### Git
- Un projet = un repository GitHub (ou un sous-dossier si mono-repo)
- Commit fréquents avec messages clairs
- Push après chaque jalon validé

### Modularité
- Tout code réutilisable → `EURKAI/MODULES/<nom_module>/`
- Format agnostique (pas de dépendance projet-spécifique)
- Chaque module a son `MANIFEST.json` définissant l'interface

---

## 5. Enregistrement centralisé

Chaque projet créé doit être ajouté dans :

1. **`CLAUDE/_PROJETS.md`** — ligne avec path, description, statut
2. **`_HUB.md`** (si projet significatif) — lien vers `_SUIVI.md`

---

## 6. Archivage

Quand un projet devient obsolète :

1. Statut → ⚫ archivé dans `_SUIVI.md`
2. Déplacer vers `PROJETS/PRO/ARCHIVES/<NOM>_HISTORIQUE/`
3. Logger le mouvement dans `CLAUDE/_MOVES_LOG.md`
4. MAJ `_PROJETS.md` et `_HUB.md`

---

## 7. Standards techniques

Consulter **[STANDARDS.md](STANDARDS.md)** pour les règles de génération de code :
- HTML/CSS/JS (sémantique, accessibilité, performance)
- Python (PEP 8, sécurité)
- Tests, Git, Sécurité, A11y
- **Modules EURKAI** (structure, MANIFEST.json)

---

## Notes

- Ce process est **vivant** — il s'améliore au fur et à mesure
- Toute optimisation ici se répercute sur tous les projets futurs
- Simplicité > Perfection
- Un projet non démarré vaut mieux qu'un process trop lourd
- **PROCESS.md** (structure projet) + **STANDARDS.md** (qualité code) = duo indissociable
