# PIPELINE AGENCE — Suivi

> Système d'orchestration autonome : idée → brief → CDC → specs → output → déploiement.
> Fonctionne via API Anthropic (pas Claude Code) pour une exécution sans intervention.

**Statut** : 🟢 actif — construction en cours
**Créé** : 2026-02-08
**Dernière MAJ** : 2026-02-08

---

## Objectif

Permettre à Nathalie de déposer une idée (export ChatGPT, texte, note vocale) et que le système produise automatiquement, étape par étape avec validation, tous les livrables jusqu'au déploiement.

## Pipeline

```
TODO/ (dépôt) → BRIEF → GATE → CDC → GATE → SPECS → GATE → BUILD → GATE → DEPLOY+MKG → GATE
```

Chaque GATE = fichier partagé où Claude écrit son résumé et Nathalie valide (GO / AJUSTER / KILL).

## Composants

| Fichier | Rôle | Statut |
|---|---|---|
| `config.py` | Configuration centralisée (clés, chemins, notifs) | [x] fait |
| `parser.py` | Parse les exports ChatGPT JSON → brief structuré | [x] fait |
| `notifier.py` | Email + SMS via Brevo à chaque GATE | [x] fait |
| `orchestrator.py` | Chef d'orchestre — scan, transitions, API Anthropic | [x] fait |
| `dispatcher.py` | Heartbeat toutes les minutes — lance l'orchestrateur si besoin | [x] fait |
| `templates/` | Modèles de documents (BRIEF, CDC, SPECS, GATE) | [x] fait |
| `state.json` | État de tous les projets en cours (généré auto) | [x] créé au 1er run |
| LaunchAgent `.plist` | `com.bigboff.dispatcher` — toutes les 60s | [x] fait |

## Dépendances

- Python 3.12 (pyenv)
- Clé API Anthropic (dans `CLAUDE/env.txt`) ✓
- Clé API Brevo (dans `CLAUDE/env.txt`) ✓
- Package `requests` (pip)

## Structure projet généré

Chaque idée traitée crée un dossier dans `PROJETS/PRO/` :

```
PROJETS/PRO/<NOM>/
├── _SUIVI.md
├── README.md
├── PIPELINE/
│   ├── 00_SOURCE.json       # Input original
│   ├── 01_BRIEF.md          # Brief structuré
│   ├── 02_CDC.md            # Cahier des charges
│   ├── 03_SPECS.md          # Spécifications techniques
│   ├── 04_BUILD_REPORT.md   # Rapport de construction
│   └── 05_DEPLOY.md         # Plan déploiement + MKG
├── VALIDATION/
│   ├── GATE_1_BRIEF.md      # Validation brief
│   ├── GATE_2_CDC.md        # Validation CDC
│   ├── GATE_3_SPECS.md      # Validation specs
│   ├── GATE_4_BUILD.md      # Validation build
│   └── GATE_5_LAUNCH.md     # Validation lancement
├── src/
├── tests/
└── dist/
```

## Historique

- 2026-02-08 : Création du projet, cadrage avec Nathalie
- 2026-02-08 : Construction complète — config, parser, notifier, orchestrateur, dispatcher, templates, LaunchAgent
