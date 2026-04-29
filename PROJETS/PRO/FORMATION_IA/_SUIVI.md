# FORMATION_IA — Suivi

## Identité

| Champ | Valeur |
|---|---|
| **Nom** | FORMATION_IA |
| **Statut** | 🟢 actif |
| **Priorité** | haute |
| **Démarré** | 2026-04-29 |
| **Projet parent** | EURKAI |
| **Module EURKAI** | `training_generator` |

## Contexte

Opportunité marché : obligation légale de formation à l'IA pour les entreprises françaises d'ici août 2026.  
Offre en 3 niveaux construite sur le module EURKAI `training_generator` (agnostique, réutilisable).

### 3 offres

| Offre | Description |
|---|---|
| **A — Catalogue** | Formations standard sur les grandes thématiques IA, modules prêts à l'emploi |
| **B — Secteur** | Offre A personnalisée par secteur d'activité via manifest EURKAI |
| **C — Sur mesure** | Modules définis à partir des besoins précis de chaque client/poste |

### Affiliation (cerise sur le gâteau)

Recommandation contextuelle d'outils intégrée dans les modules avancés (Offres B et C).  
Jamais au centre — toujours contextuelle.

## Liens GitHub

| Ressource | Lien |
|---|---|
| **Module training_generator** | https://github.com/EUREKAI25/BIG_BOFF/blob/main/PROJETS/PRO/EURKAI/CODE/eurkai_core/modules/training_generator.py |
| **ERK descriptor** | https://github.com/EUREKAI25/BIG_BOFF/blob/main/PROJETS/PRO/EURKAI/CODE/eurkai_core/modules/training_generator.erk |
| **Démo (script)** | https://github.com/EUREKAI25/BIG_BOFF/blob/main/PROJETS/PRO/FORMATION_IA/demo/run_demo.py |
| **Démo (output JSON)** | https://github.com/EUREKAI25/BIG_BOFF/blob/main/PROJETS/PRO/FORMATION_IA/demo/output_demo.json |
| **Démo (HTML)** | https://github.com/EUREKAI25/BIG_BOFF/blob/main/PROJETS/PRO/FORMATION_IA/demo/output_demo.html |

## Architecture module EURKAI v2.0.0

```
training_generator v2.0.0
├── Input  : topic, level, objectives, logics, format, catalog
├── Output : training {
│     training_title, level, estimated_duration,
│     progression { total_chapters, total_lessons, total_tasks },
│     chapters [
│       chapter_id, order, title, logic_type, objective, status,
│       lessons [
│         lesson_id, order, title, objective, status,
│         content_blocks [ type, title, content ]
│         interactive_tasks [ task_id, type, instruction, ... ]
│         completion_rules
│       ],
│       chapter_validation
│     ],
│     final_validation,
│     certificate_data
│   }
├── Logiques : editorial, technical, strategic, operational,
│              cognitive, collaborative, creative
├── Modes   : LLM (avec catalog) | déterministe (fallback)
└── Format  : short=2 leçons/ch | standard=3 | long=5
```

## Historique

### 2026-04-29 — Session création v1.0.0

- [x] Brief issu de conversation ChatGPT analysée
- [x] Module `training_generator.py` v1.0.0 créé (agnostique, modules/sections)
- [x] Fichier `training_generator.erk` créé
- [x] Smoke test validé (mode déterministe : 3 logiques × 3 sections)
- [x] Projet FORMATION_IA créé (structure standard)
- [x] Démo : formation "Utiliser l'IA dans son travail quotidien" générée
- [x] Output démo : JSON + HTML statique
- [x] Commit + push GitHub

### 2026-04-29 — Session refactoring v2.0.0 (formation interactive)

- [x] `training_generator.py` → v2.0.0 : structure chapitres > leçons > tâches interactives
  - 7 templates de chapitres (editorial, technical, strategic, operational, cognitive, collaborative, creative)
  - Chaque leçon : content_blocks (theory/example/method/warning/prompt/checklist) + interactive_tasks
  - Smoke test validé : 3 ch / 9 leçons / 18 tâches (format standard)
- [x] `run_demo.py` → mini-LMS interactif complet
  - Sidebar chapitres avec statuts + barre de progression
  - Déverrouillage progressif des leçons
  - Tâches interactives (textarea, rating, checklist, copie de prompt)
  - Sauvegarde localStorage
  - Validation de chapitre + validation finale + attestation
- [x] `training_generator.erk` → v2.0.0 : nouveaux schémas documentés
- [x] output_demo.html généré : 4 ch / 12 leçons / 24 tâches — formation 2h30

## Prochaines étapes

1. Créer les 3 manifests (offres A, B, C)
2. Créer un scénario EURKAI `scenario_generate_training.py`
3. Définir l'offre commerciale (pricing, page de vente)
4. Lancer la prospection (Nathalie fournira les prompts)
