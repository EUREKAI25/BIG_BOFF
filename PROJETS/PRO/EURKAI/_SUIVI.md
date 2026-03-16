# EURKAI — Suivi

pis> Écosystème autonome d'orchestration de projets — Architecture fractale, auto-optimisant, langage propriétaire

**Statut** : 🟢 actif — construction progressive, approche pragmatique
**Créé** : 2026-02-10 (refonte complète, ancien historique dans ARCHIVES/)
**Dernière MAJ** : 2026-03-16 21:45

---

## Vision

EURKAI est un écosystème entièrement autonome, capable de s'auto-évaluer et de s'auto-optimiser.

### Architecture fondamentale

**TOUT est objet** : `env`, `function`, `method`, `class`, `module`, `scenario`, `user`, `facture`...

**Principes EURKAI** :
1. **Atome = function** (fait UNE chose, réutilisable)
2. **Method = import function** (flexibilité totale)
3. **Scenario = orchestration** (articule methods, ne fait rien lui-même)
4. **Toute method est scenario** (même si n'appelle qu'une function)
5. **Héritage universel** : tout hérite d'`Object` (ident, created_at, version, validate(), test())
6. **Injection dynamique** : methods transversales injectées selon contexte

**Architecture fractale** : la même structure orchestrateur/agents/validator se répète à toutes les échelles (projet, étape, tâche, action).

À terme, le système sera **full dynamique** avec un **langage propriétaire** simplifiant le développement pour les IA comme pour les humains.

**Philosophie** : construction par le bas, modularité maximale, amélioration continue, apprentissage pas à pas.

---

## Objectif immédiat

**Idée → Artefacts actionnables**

Permettre de transformer une idée (export ChatGPT) en projet déployable avec des artefacts concrets :
- BRIEF structuré
- CDC (Cahier des Charges)
- SPECS techniques
- Code fonctionnel
- Déploiement

**Sans sur-ingénierie.** Approche pragmatique d'abord, sophistication ensuite.

---

## Architecture

### Structure fractale de base

```
ORCHESTRATOR
  ├─ Définit étapes + rôles + priorités
  ├─ Délègue aux AGENTS (outputs standardisés)
  └─ Transmet à VALIDATOR

AGENTS (n)
  └─ Produisent outputs selon MANIFEST (interface standard)

VALIDATOR
  └─ Vérifie conformité au MANIFEST
```

Cette structure s'applique :
- **Niveau projet** : orchestrator projet → agents étapes → validator livrable
- **Niveau étape** : orchestrator étape → agents tâches → validator étape
- **Niveau tâche** : orchestrator tâche → agents actions → validator action

**Avantage** : toute optimisation à une échelle se répercute instantanément sur l'ensemble du système.

---

## Agents prévus

| Agent | Rôle | Modèle | Statut |
|---|---|---|---|
| **INTAKE** | Parse idées, crée brief | Haiku | ⚪ à créer |
| **ARCHITECT** | Produit CDC, specs | Haiku | ⚪ à créer |
| **BUILDER** | Compose seeds/schemas/manifests selon règles | Aucun (règles) | ⚪ futur |
| **DEPLOYER** | Exécute déploiement selon plan | Aucun (règles) | ⚪ futur |
| **CURATOR** | Ménage, tags, doublons | Haiku | 🟡 partiel (Pulse) |
| **VALIDATOR** | Vérifie conformité MANIFEST | Aucun (règles) | ⚪ à créer |
| **META** | Auto-évaluation, optimisation | Aucun (métriques) | ⚪ futur |

**Note importante** : BUILDER, DEPLOYER, CURATOR, META ne raisonnent pas — ce sont des **exécutants** suivant des règles imposées. Seuls INTAKE et ARCHITECT utilisent des LLMs.

---

## Modularité

### Bibliothèque de modules (`MODULES/`)

Tout code réutilisable est extrait en **module standalone** :
- Login / Register
- Auth (JWT, session, OAuth)
- Payment (Stripe, PayPal)
- Upload (images, fichiers)
- Email (templates, envoi)
- etc.

**Format** :
```
MODULES/<nom_module>/
├── MANIFEST.json      # Interface standard (inputs, outputs, config)
├── README.md          # Documentation
├── src/               # Code agnostique (pas de dépendance projet)
├── tests/             # Tests
└── examples/          # Exemples d'utilisation
```

**Avantage** : chaque nouveau projet qui nécessite une brique existante la réutilise. EURKAI se construit peu à peu par accumulation.

---

## Connexion au CORE

**Principe** : tout projet est "branché" sur le core EURKAI.

Le core fournit :
- Orchestration (planning, rôles, priorités)
- État partagé (base centralisée)
- Métriques (temps, coût, qualité)
- Optimisation continue
- APIs communes (auth, notifs, storage)

**Détachement** : possible mais coupe le projet de toute la puissance du système (scalabilité, optimisation, modules partagés).

---

## Approche actuelle (pas à pas)

### Phase 1 : Workflow manuel optimisé ✅ en cours

```
1. Nathalie : Export ChatGPT → CLAUDE/TODO/
2. Claude (Sonnet) : Produit BRIEF, CDC, SPECS (session interactive)
3. Nathalie : Validation à chaque étape
4. Claude : Génère code, réutilise MODULES/ si applicable
5. Claude : Déploiement + push GitHub
```

**Coût** : inclus dans abonnement Max (90€/mois), pas de surcoût.

### Phase 2 : Automatisation partielle ⚪ futur proche

- Agent INTAKE autonome (parse TODO/, génère brief sans intervention)
- Agent ARCHITECT autonome (CDC + specs depuis brief validé)
- VALIDATOR basique (checks syntaxe, structure, conformité)

**Coût estimé** : ~1-2€/projet avec Haiku.

### Phase 3 : EURKAI complet ⚪ vision long terme

- Orchestrateur maître
- Tous agents opérationnels
- Langage propriétaire
- Auto-optimisation
- Full autonomie

---

## Organisation actuelle

### Workflow de création projet

Voir [`CLAUDE/PROCESS.md`](../../../CLAUDE/PROCESS.md) pour le détail complet.

**Résumé** :
1. Idée → BRIEF (validation)
2. BRIEF → Projet structuré dans `PROJETS/PRO/<NOM>/`
3. CDC → SPECS → BUILD → DEPLOY
4. Extraction modules réutilisables → `EURKAI/MODULES/`
5. Push GitHub

### Fichiers de pilotage

| Fichier | Rôle |
|---|---|
| `CLAUDE/PROCESS.md` | Règles de création projet |
| `CLAUDE/_AUTO_BRIEF.md` | État global des travaux |
| `CLAUDE/_PROJETS.md` | Liste exhaustive projets |
| `CLAUDE/_CRON.md` | Tâches planifiées |
| `_HUB.md` | Carte centrale BIG_BOFF |

---

## Projets liés

| Projet | Rôle dans EURKAI |
|---|---|
| **BIG_BOFF Search** | Agent SEARCH — moteur recherche par tags (84k éléments) |
| **Pipeline Agence** | Preuve de concept orchestration autonome (à refondre) |
| **TIP_CALCULATOR** | Premier projet test du workflow optimisé |

---

## Prochaines étapes

### Immédiat (semaine 1)

- [x] Structurer EURKAI proprement
- [x] Archiver ancien EURKAI → ARCHIVES/
- [x] Documenter vision + approche dans `_SUIVI.md`
- [ ] Créer `MODULES/` avec premier module (formulaire simple)
- [ ] Terminer TIP_CALCULATOR (CDC → SPECS → BUILD)
- [ ] Push GitHub

### Court terme (mois 1)

- [ ] Créer 3-5 modules standalone (auth, email, upload)
- [ ] Refondre Pipeline Agence selon architecture fractale
- [ ] Documenter protocole inter-agents (`CORE/PROTOCOL.md`)
- [ ] Définir format MANIFEST standard (`CORE/MANIFEST_SPEC.md`)

### Moyen terme (trimestre 1)

- [ ] Agent INTAKE autonome
- [ ] Agent ARCHITECT autonome
- [ ] Agent VALIDATOR basique
- [ ] Orchestrateur léger (gestion d'état, métriques)
- [ ] 10+ projets générés via workflow EURKAI

---

## Métriques de succès

| Métrique | Cible | Actuel |
|---|---|---|
| Temps idée → déploiement | < 2h | ~4-6h (manuel) |
| Coût par projet | < 2€ | 0€ (inclus Max) |
| Taux de réutilisation modules | > 50% | 0% (démarrage) |
| Projets actifs | 10+ | 3 |
| Autonomie (% sans intervention) | 80%+ | 10% |

---

## Décisions

- **2026-02-10 19:00** : Architecture orientée objet universelle documentée (TOUT est objet)
- **2026-02-10 19:00** : Validation objets/héritage via formulaire GitHub Pages (étape SPECS)
- **2026-02-10 19:00** : Règles EURKAI formalisées (atome=function, method=import, scenario=orchestration)
- **2026-02-10 18:45** : TIP_CALCULATOR déployé — premier projet complet A→Z ✅
- **2026-02-10 18:30** : PROCESS.md + STANDARDS.md créés (règles standardisées)
- **2026-02-10 17:00** : Refonte complète EURKAI, approche pragmatique pas à pas
- **2026-02-10** : Workflow manuel optimisé d'abord, automatisation ensuite
- **2026-02-10** : Sonnet par défaut pour minimiser coût quota
- **2026-02-10** : Structure fractale dès le début, même si simple
- **2026-02-10** : Modules standalone prioritaires (construction par le bas)
- **2026-02-10** : Apprentissage pas à pas (règles révélées au fil des projets, pas tout d'un coup)

---

## Historique

- **2026-03-16 21:45** : `generate_brand_charter.py` — orchestrateur test pipeline design complet (5/5 modules OK, 3 briefs, HTML brand charter)
- **2026-03-16** : `scan_and_do` MVP complet (7/7 tests ✅) — moteur MRG générique
- **2026-03-16** : `theme_generator` phase 1 visuelle (StyleDNA, font_map, theme_translation, visual_analysis — 14/14 tests ✅)
- **2026-03-15** : `conversational_brief` extrait vers EURKAI/MODULES (injectable, agnostique)
- **2026-03-15** : `_ARCHITECTURE_MVP.md` + `_OBJECT_CONTRACT.md` — documents de référence EURKAI
- **2026-03-15** : `visual_consistency_validator` + `design_exploration_engine` complets
- **2026-02-10 19:00** : Architecture orientée objet EURKAI formalisée (atome/method/scenario/injection)
- **2026-02-10 18:45** : TIP_CALCULATOR déployé en production — https://eurekai25.github.io/tip-calculator/
- **2026-02-10 18:30** : PROCESS.md + STANDARDS.md créés, catalogue modules initialisé
- **2026-02-10 17:00** : Création nouveau EURKAI propre, ancien archivé dans `ARCHIVES/EURKAI_HISTORIQUE/`
- **2026-02-10 17:00** : Documentation vision complète, architecture fractale, approche progressive
- **2026-02-10 17:00** : Premier projet test TIP_CALCULATOR lancé avec workflow optimisé
