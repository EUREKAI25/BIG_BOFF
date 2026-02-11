# PROCESS — Création de projet

> Règles à suivre pour chaque création de projet via le workflow idée → artefacts.

**Dernière MAJ** : 2026-02-11

---

## 0. EURKAI — Métaprojet et règles obligatoires

### 0.1 Contexte

**EURKAI** est le **métaprojet** dans lequel s'inscrivent TOUS les projets BIG_BOFF.

Tout projet créé via ce process DOIT :
- Respecter l'architecture orientée objet EURKAI
- Être pensé comme un module potentiel EURKAI
- Suivre les principes fondamentaux EURKAI

### 0.2 Ressources EURKAI

**Consulter systématiquement** :
1. **`CLAUDE/DROPBOX/`** — Ressources EURKAI (en cours de remplissage par Nathalie)
2. **`PROJETS/PRO/EURKAI/_SUIVI.md`** — Vision, architecture, principes
3. **`PROJETS/PRO/EURKAI/CORE/`** — Protocoles, spécifications
4. **`PROJETS/PRO/EURKAI/MODULES/`** — Bibliothèque de modules réutilisables

### 0.3 Principes EURKAI (obligatoires)

**Architecture orientée objet universelle** :
- **TOUT est objet** : `env`, `function`, `method`, `class`, `module`, `scenario`, `user`, `facture`...
- **Héritage universel** : tout hérite d'`Object` (ident, created_at, version, parent, validate(), test())

**Règles de composition** :
1. **Atome = function** — Une function fait UNE chose, réutilisable
2. **Method = import function** — Flexibilité totale, interchangeabilité
3. **Scenario = orchestration** — Articule des methods, ne fait rien lui-même
4. **Toute method est scenario** — Même si n'appelle qu'une function
5. **Injection dynamique** — Methods transversales injectées selon contexte

**Architecture fractale** :
```
ORCHESTRATOR
  ├─ Définit étapes + rôles + priorités
  ├─ Délègue aux AGENTS (outputs standardisés)
  └─ Transmet à VALIDATOR
```

Cette structure s'applique à toutes les échelles (projet, étape, tâche, action).

### 0.4 Vérification obligatoire

**À l'étape SPECS** (avant génération de code) :
- [ ] Architecture conforme EURKAI
- [ ] Tous les objets identifiés et documentés
- [ ] Héritage défini (parent pour chaque objet)
- [ ] Modules réutilisables identifiés dans `EURKAI/MODULES/`
- [ ] Injection dynamique planifiée si applicable

**Tout projet non conforme EURKAI ne peut pas être validé.**

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
3. **Validation Nathalie via formulaire HTML** :
   - Claude crée `VALIDATION_BRIEF_<NOM>.html` dans TODO/
   - Claude ouvre automatiquement le formulaire dans le navigateur : `open "<chemin>.html"`
   - Questions/options UNIQUEMENT pour les choix importants nécessaires pour continuer
   - Validation globale en une fois (pas de micro-validations)
   - Toujours inclure un champ texte ouvert pour précisions/questions
   - Nathalie remplit le formulaire → copie le texte généré → colle dans le terminal Claude
   - Claude parse la réponse et continue automatiquement (création projet, CDC, etc.)
   - Exemple questions : "Valider ce BRIEF ?", "Nom projet OK ?", "Stack technique ?", "Scope MVP ?"

### Étape 2 : BRIEF → Projet structuré

1. Créer le répertoire projet dans `PROJETS/PRO/` ou `PROJETS/PERSO/`
2. Créer `_SUIVI.md`, `_IDEES.md`, `README.md`
3. Créer `PIPELINE/` et y copier le BRIEF (renommé `01_BRIEF.md`)
4. Copier la source originale dans `PIPELINE/00_SOURCE.json` si applicable
5. Enregistrer dans `CLAUDE/_PROJETS.md`

### Étape 3 : CDC

1. Claude produit `PIPELINE/02_CDC.md` (Cahier des Charges)
2. **Validation Nathalie via formulaire HTML** :
   - Claude crée `VALIDATION_CDC_<NOM>.html` dans le dossier projet
   - Claude ouvre automatiquement le formulaire : `open "<chemin>.html"`
   - Questions importantes uniquement (ex: choix techno si plusieurs options valables)
   - Validation globale du CDC
   - Champ texte pour ajustements/précisions
   - Nathalie remplit → copie texte → colle dans terminal Claude

### Étape 4 : SPECS

1. Claude produit `PIPELINE/03_SPECS.md` (Spécifications techniques)
2. **⚠️ VÉRIFICATION OBLIGATOIRE RÈGLES EURKAI** :
   - Consulter `CLAUDE/DROPBOX/` (ressources EURKAI)
   - Vérifier conformité architecture orientée objet EURKAI
   - S'assurer que TOUT est objet (env, function, method, class, module...)
   - Respecter principes : atome=function, method=import, scenario=orchestration
   - Vérifier héritage universel depuis Object
   - Identifier injection dynamique si applicable
3. **Validation Nathalie via formulaire HTML** :
   - Claude crée `VALIDATION_SPECS_<NOM>.html` dans le dossier projet
   - Claude ouvre automatiquement le formulaire : `open "<chemin>.html"`
   - **Objets à créer** pour le projet
   - **Parent proposé** pour chaque objet (avec justification)
   - **Attributs/méthodes** nécessaires
   - **Modules existants** à réutiliser vs nouveaux à créer
   - **Recommandations Claude** (pourquoi tel parent, alternatives)
   - **Conformité EURKAI** explicitement mentionnée
   - Champ texte pour ajustements/questions
   - Nathalie remplit → copie texte → colle dans terminal Claude
4. Claude applique les choix validés

### Étape 5 : BUILD

1. Claude génère le code dans `src/`, `tests/`, etc.
2. Vérification des modules réutilisables dans `EURKAI/MODULES/`
3. Si code réutilisable → créer module standalone dans `EURKAI/MODULES/<nom>/`
4. Tests et validation
5. **Validation Nathalie via formulaire HTML** (si nécessaire) :
   - Uniquement si choix techniques importants pendant le build
   - Claude crée `VALIDATION_BUILD_<NOM>.html` si besoin
   - Claude ouvre automatiquement le formulaire : `open "<chemin>.html"`
   - Code généré présenté pour validation globale
   - Champ texte pour ajustements
   - Nathalie remplit → copie texte → colle dans terminal Claude

### Étape 6 : DEPLOY

1. Claude produit `PIPELINE/04_DEPLOY.md` (plan déploiement)
2. **GitHub — Mono-repo MVP** :

   **Structure repo** : Un repo `mvp-projects` contenant tous les projets MVP
   ```
   mvp-projects/
   ├── README.md              # Index de tous les MVP
   ├── tip-calculator/        # MVP 1
   │   ├── index.html
   │   ├── script.js
   │   └── style.css
   ├── autre-mvp/             # MVP 2
   └── encore-un-mvp/         # MVP 3
   ```

   **Processus de déploiement** :

   a. **Initialiser le repo si première fois** :
   ```bash
   cd /chemin/vers/workspace/mvp-projects
   git init
   git remote add origin https://github.com/eurekai25/mvp-projects.git
   ```

   b. **Ajouter le nouveau projet** :
   ```bash
   # Copier le projet dans le mono-repo
   cp -r /Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/<NOM>/* mvp-projects/<nom-projet>/

   # Mettre à jour le README.md racine avec lien vers nouveau MVP
   ```

   c. **Commit et push** :
   ```bash
   git add .
   git commit -m "feat: Add <nom-projet> MVP

   <description courte du projet>

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   git push origin main
   ```

   d. **Configurer GitHub Pages** (si première fois) :
   - Settings → Pages → Source: main branch / root
   - URL finale : `https://eurekai25.github.io/mvp-projects/<nom-projet>/`

   e. **Mettre à jour README.md projet local** :
   - Ajouter lien déploiement : `https://eurekai25.github.io/mvp-projects/<nom-projet>/`

3. **Validation déploiement** :
   - Tester l'URL en production
   - Vérifier fonctionnement complet

4. MAJ `_SUIVI.md` → statut 🟢 actif + URL déploiement
5. MAJ `_AUTO_BRIEF.md` avec nouveau projet déployé

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

**Règle des modules** :
- Créer un module **dès le 1er besoin réel** (pas "au cas où")
- Tout module = endpoint accessible par API
- Catalogue centralisé : `EURKAI/MODULES/catalogue.json`
- Process :
  ```
  Projet X a besoin de Y
    → Y existe dans catalogue.json ?
      OUI → utiliser l'endpoint existant
      NON → créer MODULES/Y/, ajouter au catalogue, utiliser
  ```
- Format agnostique (pas de dépendance projet-spécifique)
- Chaque module a son `MANIFEST.json` définissant l'interface
- Identifiant unique : `module_<slug>` (ex: `module_auth`)

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

## 7. Architecture orientée objet

**Principe fondamental** : TOUT est objet (`env`, `function`, `method`, `class`, `module`, `scenario`...)

### Hiérarchie

```
Object (racine universelle)
  ├─ attributes : ident, created_at, version, parent, etc.
  ├─ methods : validate(), test(), serialize()
  └─ [tous les objets héritent]
```

### Règles de création d'objet

**Process systématique** :
1. Besoin d'un objet X identifié
2. **Chercher** dans catalogue si X existe (exact match)
3. **Si non**, chercher parent potentiel (héritage)
4. **Si non**, créer :
   - Définir schéma (hérité d'Object + spécifique)
   - Attributs obligatoires
   - Méthodes (validation, test, métier)
   - Enregistrer dans catalogue approprié

### Principes EURKAI

- **Atome = function** (fait UNE chose)
- **Method = import function** (flexibilité, interchangeabilité)
- **Scenario = orchestration** (articule méthodes, ne fait rien lui-même)
- **Toute méthode est scenario** (même si n'appelle qu'une fonction)
- **Injection dynamique** : méthodes transversales injectées selon contexte

**Exemple** :
```javascript
// FiscalRule.calculer_tva() s'injecte dans Facture
// UNIQUEMENT si contexte fiscal applicable
if (facture.pays === 'FR') {
  inject(facture, FiscalRule.calculer_tva);
}
```

### Validation objets (étape SPECS)

Claude soumet via **formulaire HTML** (`VALIDATION_SPECS_<NOM>.html`) :
- Objets à créer
- Parents proposés (avec justification)
- Attributs/méthodes
- Recommandations

Nathalie ouvre le formulaire dans le navigateur → remplit → copie texte généré → colle dans terminal Claude → Claude applique.

---

## 8. Standards techniques

Consulter **[STANDARDS.md](STANDARDS.md)** pour les règles de génération de code :
- HTML/CSS/JS (sémantique, accessibilité, performance)
- Python (PEP 8, sécurité)
- Tests, Git, Sécurité, A11y
- **Architecture objet EURKAI** (héritage, injection, catalogues)
- **Modules EURKAI** (structure, MANIFEST.json)

---

## Notes

- Ce process est **vivant** — il s'améliore au fur et à mesure
- Toute optimisation ici se répercute sur tous les projets futurs
- Simplicité > Perfection
- Un projet non démarré vaut mieux qu'un process trop lourd
- **PROCESS.md** (structure projet) + **STANDARDS.md** (qualité code) = duo indissociable
