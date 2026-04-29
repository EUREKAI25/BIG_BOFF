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

## Architecture module EURKAI

```
training_generator
├── Input  : topic, level, objectives, logics, format, catalog
├── Output : training { training_title, level, modules[], summary, next_steps }
├── Logiques disponibles : editorial, technical, strategic, operational,
│                          cognitive, collaborative, creative
├── Modes  : LLM (avec catalog) | déterministe (fallback)
└── Sections par format : short=2 | standard=3 | long=5
```

## Historique

### 2026-04-29 — Session création

- [x] Brief issu de conversation ChatGPT analysée
- [x] Module `training_generator.py` créé dans EURKAI modules (agnostique, MVP)
- [x] Fichier `training_generator.erk` créé
- [x] Smoke test validé (mode déterministe : 3 logiques × 3 sections)
- [x] Projet FORMATION_IA créé (structure standard)
- [x] Démo : formation "Utiliser l'IA dans son travail quotidien" générée
- [x] Output démo : JSON + HTML consultable
- [x] Commit + push GitHub
- [ ] Manifests offre A/B/C (prochaine session)
- [ ] Scénario EURKAI pour l'offre (prochaine session)
- [ ] Stratégie d'acquisition / prospection (selon nouveaux prompts Nathalie)

## Prochaines étapes

1. Créer les 3 manifests (offres A, B, C)
2. Créer un scénario EURKAI `scenario_generate_training.py`
3. Définir l'offre commerciale (pricing, page de vente)
4. Lancer la prospection (Nathalie fournira les prompts)
