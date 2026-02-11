# Journal des mouvements de fichiers

> Tout déplacement, renommage ou archivage est consigné ici.
> Ce fichier est nettoyé régulièrement une fois les mouvements confirmés.

**Dernière MAJ** : 2026-02-11

---

## Mouvements en attente de validation

### 2026-02-11 — Archivage fichiers TODO TIP_CALCULATOR

| # | Source | Destination | Raison |
|---|---|---|---|
| T1 | `CLAUDE/TODO/BRIEF_TIP_CALCULATOR.md` | `PROJETS/PRO/TIP_CALCULATOR/PIPELINE/` | Projet terminé — archivé dans son pipeline |
| T2 | `CLAUDE/TODO/test_bidon.json` | `PROJETS/PRO/TIP_CALCULATOR/PIPELINE/` | Export ChatGPT source — archivé dans son pipeline |

### 2026-02-08 — Suppression BIGBOFF par Nathalie

| # | Action | Raison |
|---|---|---|
| N1 | `PROJETS/PRO/BIGBOFF/` supprimé entièrement | Décision Nathalie — projet abandonné |
| N2 | `PROJETS/PRO/BBOFF/` supprimé entièrement | Décision Nathalie — projet abandonné |

### 2026-02-08 — Nettoyage doublons exacts SUBLYM_APP_PUB

| # | Action | Taille | Raison |
|---|---|---|---|
| D1 | Supprimé `SUBLYM_APP_PUB/michael/SublymTest.mp4` | 28 Mo | Doublon exact (SHA256) de `SUBLYM_APP_PUB/SublymTest.mp4` |
| D2 | Supprimé `SUBLYM_APP_PUB/Avatars/Julien36/Julien/mp4/` (48 fichiers) | ~42 Mo | 48/48 fichiers = doublons exacts des originaux dans `output/dreams/` |
| — | **NON touché** : `Living in a moment` (3 copies) | — | Les footages sont identiques mais les projets Premiere Pro sont différents (travail de montage) |

### 2026-02-08 — Suppression zips SUBLYM redondants (~348 Mo libérés)

| # | Fichier supprimé | Taille | Raison |
|---|---|---|---|
| S1 | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/SUBLYM24.zip` | 0,2 Mo | Dossier SUBLYM24/ existe (500+ fichiers) |
| S2 | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/SUBLYM24 2.zip` | 22,6 Mo | Copie numérotée, dossier SUBLYM24/ existe |
| S3 | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/SUBLYM24 3.zip` | 125,1 Mo | Copie numérotée, dossier SUBLYM24/ existe |
| S4 | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/SUBLYM241.zip` | 33,5 Mo | Dossier SUBLYM241/ existe (500+ fichiers) |
| S5 | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/SUBLYM72.zip` | 53,7 Mo | Dossier SUBLYM72/ existe (500+ fichiers) |
| S6 | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/SUBLYM72 2.zip` | 52,6 Mo | Copie numérotée, dossier SUBLYM72/ existe |
| S7 | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/SUBLYM_APP copie.zip` | 33,7 Mo | Dossier SUBLYM_APP copie/ existe (500+ fichiers) |
| S8 | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/SUBLYM_MVP.zip` | 0,1 Mo | Dossier SUBLYM_MVP/ existe (500+ fichiers) |
| S9 | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/SUBLYM_MVP 2.zip` | 26,3 Mo | Copie numérotée, dossier SUBLYM_MVP/ existe |
| S10 | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/front24.zip` | 0 Mo | Dossier front24/ existe (500+ fichiers) |

---

## Historique (mouvements confirmés)

### 2026-02-07 — Consolidation SUBLYM + Création bibliothèque EURKAI/MODULES/

#### Migration des modules vers EURKAI/MODULES/

| # | Source | Destination | Raison |
|---|---|---|---|
| M1 | `PRO/SUBLYM_APP/modules/campaign_manager/` | `PRO/EURKAI/MODULES/campaign_manager/` | Module réutilisable — bibliothèque EURKAI |
| M2 | `PRO/SUBLYM_APP/modules/etsy_module/` | `PRO/EURKAI/MODULES/etsy_module/` | Module réutilisable — bibliothèque EURKAI |
| M3 | `PRO/SUBLYM_APP/modules/pinterest_module/` | `PRO/EURKAI/MODULES/pinterest_module/` | Module réutilisable — bibliothèque EURKAI |
| M4 | `PRO/SUBLYM_APP/modules/sublym_campaigns/` | `PRO/EURKAI/MODULES/sublym_campaigns/` | Module réutilisable — bibliothèque EURKAI |
| M5 | `PRO/SUBLYM_APP/modules/sublym_etsy/` | `PRO/EURKAI/MODULES/sublym_etsy/` | Module réutilisable — bibliothèque EURKAI |
| M6 | `PRO/SUBLYM_APP/modules/sublym_pinterest/` | `PRO/EURKAI/MODULES/sublym_pinterest/` | Module réutilisable — bibliothèque EURKAI |
| M7 | `PRO/SUBLYM_APP/modules/campaigns_data/` | `PRO/EURKAI/MODULES/_DATA/campaigns/` | Données de campagnes |
| M8 | `PRO/SUBLYM_APP/modules/lancer_formulaire.command` | `PRO/EURKAI/MODULES/lancer_formulaire.command` | Lanceur macOS formulaire Etsy |
| M9 | `PRO/SUBLYM_APP/_ONEPATH.md` | `PRO/CLAUDE/_ONEPATH.md` | Clés API et credentials — copié vers projet actif |

#### Archivage des anciennes versions SUBLYM

| # | Source | Destination | Raison |
|---|---|---|---|
| A1 | `PRO/SUBLYM/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM/` | Site PHP originel ~2015, inactif |
| A2 | `PRO/SUBLYM0118/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM0118/` | Version scando ~2024, inactif |
| A3 | `PRO/SUBLYM24/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM24/` | Tests modèles IA ~2024, inactif |
| A4 | `PRO/SUBLYM241/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM241/` | Variante SUBLYM24, inactif |
| A5 | `PRO/SUBLYM72/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM72/` | Version Docker ~2024, inactif |
| A6 | `PRO/SUBLYM_MVP/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM_MVP/` | MVP catalogue, inactif |
| A7 | `PRO/SUBLYM_DREAM/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM_DREAM/` | Fork APP, 85% identique |
| A8 | `PRO/SUBLYM_GITHUB/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM_GITHUB/` | Fork APP, 85% identique |
| A9 | `PRO/SUBLYM_APP copie/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM_APP copie/` | Copie manuelle |
| A10 | `PRO/SUBLYM_APP_ARCHIVE/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM_APP_ARCHIVE/` | Déjà une archive |
| A11 | `PRO/SUBLYM_ETSY/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM_ETSY/` | 1 fichier JSON |
| A12 | `PRO/CHANTIERS SUBLYM72/` | `ARCHIVES/SUBLYM_HISTORIQUE/CHANTIERS SUBLYM72/` | Chantiers WIP |
| A13 | `PRO/SUBLYM_CHANTIERS/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM_CHANTIERS/` | Chantiers WIP |
| A14 | `PRO/sublym_chantiers 4/` | `ARCHIVES/SUBLYM_HISTORIQUE/sublym_chantiers 4/` | Chantiers WIP |
| A15 | `PRO/sublym-ui 2/` | `ARCHIVES/SUBLYM_HISTORIQUE/sublym-ui 2/` | Fragment UI |
| A16 | `PRO/SUBLYM_APP/` | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM_APP/` | Version pré-CLAUDE (modules extraits) |

### 2026-02-07 — Consolidation EURKAI (12 incarnations)

#### Archivage des incarnations EURKAI

| # | Source | Destination | Raison |
|---|---|---|---|
| E1 | `PRO/EURKAI_FIRST_VERSIONS/` | `ARCHIVES/EURKAI_HISTORIQUE/EURKAI_FIRST_VERSIONS/` | Toutes les incarnations anciennes (~7,8 Go) |
| E2 | `PRO/EX NIHILO/` | `ARCHIVES/EURKAI_HISTORIQUE/EX NIHILO/` | Phase littéraire EURKAI (~1,6 Go) |
| E3 | `PRO/EUREKAI_EXNIHILO/` | `ARCHIVES/EURKAI_HISTORIQUE/EUREKAI_EXNIHILO/` | Spécifications (160 Ko) |
| E4 | `PRO/EURKAI_TEMPLATESCRAP/` | `ARCHIVES/EURKAI_HISTORIQUE/EURKAI_TEMPLATESCRAP/` | Templates récupérés (4,4 Mo) |

#### Copie des fragments éparpillés (originaux conservés en place)

| # | Source | Copie dans archive | Nature |
|---|---|---|---|
| F1 | `INTERAGENTS/TOOL/EURKAI_COCKPIT/` | `_FRAGMENTS/EURKAI_COCKPIT/` | Outil cockpit (8 versions) |
| F2 | `TOOLS/EXTENSIONS/EUREKAI_CHROME_BUTTON/` | `_FRAGMENTS/EUREKAI_CHROME_BUTTON/` | Extension Chrome |
| F3 | `PRO/_INPUTS/EURKAI/` | `_FRAGMENTS/_INPUTS_EURKAI/` | Inputs consolidés (126 Mo) |
| F4 | `PRO/_INPUTS/eurekai-modular/` | `_FRAGMENTS/_INPUTS_eurekai-modular/` | Fragment modulaire |
| F5 | `PRO/_TESTS/EURKAI/` | `_FRAGMENTS/_TESTS_EURKAI/` | Tests (46 fichiers) |
| F6 | `PRO/_OUTPUTS/__EUREKAI_CHAT_*.csv` | `_FRAGMENTS/` | 4 index CSV exportés |

### 2026-02-07 — Consolidation BBOFF + Orphelins

| # | Source | Destination | Raison |
|---|---|---|---|
| B1 | `PRO/BBOFF copie/` | `ARCHIVES/BBOFF_HISTORIQUE/BBOFF copie/` | Copie redondante de BBOFF (mars 2024) |
| O1 | `PRO/front24/` | `ARCHIVES/SUBLYM_HISTORIQUE/front24/` | Frontend Sublym 2024, supplanté par PRO/CLAUDE |
| O2 | `PRO/NEW/` | `ARCHIVES/NEW/` | 2 fichiers d'idées orphelins |

### 2026-02-07 — Nettoyage PRO/ (zips, résidus, orphelins)

| # | Source | Destination | Raison |
|---|---|---|---|
| Z1-Z10 | `PRO/*.zip` (10 SUBLYM zips) | `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/` | Sauvegardes manuelles (~350 Mo) |
| Z11 | `PRO/CLAUDE.zip` | `ARCHIVES/_ZIPS/` | Sauvegarde projet actif (286 Mo) |
| Z12-Z13 | `PRO/WEB2APP*.zip` (2 zips) | `ARCHIVES/_ZIPS/` | Sauvegardes WEB2APP |
| R1 | `PRO/SUBLYM_APP/` (résidu) | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM_APP_remnant/` | Reste après migration modules |
| R2 | `PRO/SUBLYM_GITHUB/` (résidu) | `ARCHIVES/SUBLYM_HISTORIQUE/SUBLYM_GITHUB_remnant/` | Reste après archivage |
| R3 | `PRO/files (1)/` | `ARCHIVES/SUBLYM_HISTORIQUE/files_1_react_fragments/` | Composants React Sublym orphelins |
| R4 | `PRO/traducteur cognitif...` | `ARCHIVES/NEW/` | Fichier texte idée orphelin |
| R5 | `PRO/tree-PRO.md` | `ARCHIVES/` | Ancien listing |
| R6 | `PRO/Mickael - projets.md` | `ARCHIVES/` | Fichier orphelin |
| R7 | `PRO/MOBILAPPR/` | (supprimé — vide) | Dossier vide |
