# HUB — Vue d'ensemble

> Carte centrale de tous les projets et domaines.
> Chaque entrée renvoie vers son propre `_SUIVI.md`.

**Dernière MAJ** : 2026-02-08

---

## Projet central

| Projet | Description | Statut | Dernière modif | Lien |
|---|---|---|---|---|
| **EURKAI** | Écosystème modulaire — tout converge ici | 🟢 | 2026-02-07 | [_SUIVI.md](PROJETS/PRO/EURKAI/_SUIVI.md) |

---

## Projets PRO

### Écosystème SUBLYM (actif)

> 3 frontends + 1 backend partagé + 1 backoffice campagnes MKG + modules dans EURKAI/MODULES/

| Composant | Description | Emplacement | Statut | Dernière modif |
|---|---|---|---|---|
| **Backend** | API Python partagée (génération, scénarios) | `PRO/CLAUDE/backend/` | 🟢 | 2026-02-07 |
| **Frontend classique** | sublym.org — vidéo background, vitrine + création | `PRO/CLAUDE/frontend/` | 🟢 | 2026-02-07 |
| **Frontend app-like** | Expérience immersive (DreamViewer, PIN, hors ligne) | `PRO/CLAUDE/sublym-dream-app/` | 🟢 | 2026-02-07 |
| **Frontend LovLov** | Produit St-Valentin (offrir/recevoir des rêves) | `PRO/LOVLOV/lovlov-app/` | 🟢 | 2026-02-07 |
| **Backoffice** | Gestion campagnes MKG réseaux sociaux | `PRO/CLAUDE/backoffice/` | 🟡 | 2026-02-07 |
| **Modules** | campaign_manager, etsy, pinterest, campagnes | `PRO/EURKAI/MODULES/` | 🟢 | 2026-02-07 |
| **Médias / Publication** | Assets vidéo, avatars, outputs publiés | `PRO/SUBLYM_APP_PUB/` | 🟡 | 2026-02-07 |

### Autres projets PRO

| Projet | Description | Statut | Dernière modif | Lien |
|---|---|---|---|---|
| ~~BIGBOFF~~ | Projet full-stack moderne (Flask+Node) | ⚫ supprimé | 2026-02-08 | Supprimé par Nathalie |
| ~~BBOFF~~ | App PHP/Slim 4 | ⚫ supprimé | 2026-02-08 | Supprimé par Nathalie |
| RESTART | Moteur Python (engine, scenarios, pipelines) | 🟡 | 2026-02-01 | [_SUIVI.md](PROJETS/PRO/RESTART/_SUIVI.md) |
| WEB2APP | Conversion web vers app | 🟡 | 2026-01-09 | [_SUIVI.md](PROJETS/PRO/WEB2APP/_SUIVI.md) |
| RÉSONANCES | Idea Fusion / Agence | ⚫ | 2025-11-14 | [_SUIVI.md](PROJETS/PRO/RÉSONANCES/_SUIVI.md) |
| ROSE TOMATE | Recettes / site | ⚫ | 2025-11-19 | [_SUIVI.md](PROJETS/PRO/ROSE%20TOMATE/_SUIVI.md) |
| SACRED PLACES | Géolocalisation sacrée | ⚫ | 2025-11-14 | [_SUIVI.md](PROJETS/PRO/SACRED%20PLACES/_SUIVI.md) |
| TROKADECO | — | ⚫ | 2015-04-29 | [_SUIVI.md](PROJETS/PRO/TROKADECO/_SUIVI.md) |
| KDP | Kindle Direct Publishing | ⚫ | 2023-01-15 | [_SUIVI.md](PROJETS/PRO/KDP/_SUIVI.md) |

### Ressources transversales PRO

| Dossier | Nature | Dernière modif |
|---|---|---|
| _INPUTS | Ressources/docs EURKAI (126 Mo) | 2025-12-18 |
| _OUTPUTS | Règles de travail/méthodologie | 2025-11-20 |
| _RULES | Règles (possible doublon _OUTPUTS) | 2025-11-20 |
| _TESTS | Listes de tâches EURKAI | 2025-11-20 |
| _TODO | Listes de tâches | 2025-11-20 |

---

## Projets PERSO

| Projet | Description | Statut | Dernière modif | Lien |
|---|---|---|---|---|
| _ALLSEEDS | — | 💡 | 2025-11-14 | — |
| CESSION TWINGO | — | ⚫ | 2025-11-17 | — |
| MAISON | — | ⚫ | 2019-01-03 | — |
| TOMBE | — | ⚫ | 2024-07-30 | — |
| 02 ROULETTE | — | ⚫ | 2017-12-06 | — |

---

## Ressources

| Domaine | Contenu | Emplacement |
|---|---|---|
| IA | Ressources intelligence artificielle | [RESOURCES/IA](RESOURCES/IA/) |
| MEDIAS | Photos, vidéos, musique | [RESOURCES/MEDIAS](RESOURCES/MEDIAS/) |
| WEB | Ressources web | [RESOURCES/WEB](RESOURCES/WEB/) |

---

## Infrastructure

| Élément | Rôle | Emplacement |
|---|---|---|
| CLAUDE | Communication & règles Claude | [CLAUDE/](CLAUDE/) |
| TOOLS | Outils et extensions | [TOOLS/](TOOLS/) |
| INTERAGENTS | Coordination multi-agents | [INTERAGENTS/](INTERAGENTS/) |
| **PIPELINE AGENCE** | Orchestration autonome idée → production | [CLAUDE/PIPELINE/_SUIVI.md](CLAUDE/PIPELINE/_SUIVI.md) |
| CHATS | Historiques de conversations | [CHATS/](CHATS/) |

---

## Dropbox hors BIG_BOFF

> Ces dossiers existent à la racine de Dropbox, en dehors de `____BIG_BOFF___/`.
> À inventorier et intégrer dans le système.

| Dossier | Nature probable | Action |
|---|---|---|
| DOMAINES2/ | Anciens domaines/sites, vidéos, docs perso | ⚪ à explorer |
| ENVIES/ | Idées / wishlist ? | ⚪ à explorer |
| IMAGES/ | Ressources images | ⚪ à cataloguer |
| _INBOX/ | Boîte de réception | ⚪ à trier |
| pour Nathalie/ | Fichiers partagés | ⚪ à explorer |
| Mac/ | Sauvegardes Mac | ⚪ à explorer |

---

## Ménage de printemps — Avancement global

> Ce chantier est un module EURKAI. Suivi détaillé dans [EURKAI/_SUIVI.md](PROJETS/PRO/EURKAI/_SUIVI.md).

- [x] Fondations : conventions, Claude.md, _HUB.md
- [x] Cartographie de la généalogie EURKAI (12 incarnations identifiées)
- [x] Inventaire complet : 63 662 éléments, 67,7 Go, 47 125 doublons probables
- [x] **Consolidation SUBLYM** : 16 dossiers archivés, 7 modules migrés vers EURKAI/MODULES/
- [x] **Consolidation EURKAI** : 4 dossiers archivés + 6 fragments copiés dans ARCHIVES/EURKAI_HISTORIQUE/
- [x] **BBOFF** : BBOFF copie archivé, BBOFF et BIGBOFF qualifiés (projets distincts)
- [x] **Orphelins** : front24 archivé (Sublym), NEW archivé (idées), RESTART gardé (actif)
- [x] **Utilitaires transversaux** qualifiés (_INPUTS, _OUTPUTS, _RULES, _TESTS, _TODO)
- [x] Inventaire des .zip — 10 zips SUBLYM redondants identifiés, rapport généré
- [x] Détection des doublons exacts (hash SHA256) — 3 173 paires, ~553 Mo récupérables
- [ ] Catalogage et tagging des ressources
- [ ] Moteur de recherche
