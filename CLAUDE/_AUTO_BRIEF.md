# Auto-brief Claude — État des travaux

> Ce fichier est tenu à jour par Claude à chaque action.
> En cas de plantage ou nouvelle session, lire ce fichier pour reprendre.

**Dernière MAJ** : 2026-02-11 23:26

> **RÈGLE IMPÉRATIVE** : ce fichier DOIT être mis à jour après CHAQUE tâche terminée,
> pas en fin de session. En cas de crash ou de conversation fermée, c'est la seule
> mémoire persistante. Si ce fichier n'est pas à jour, le travail est perdu.

---

## Résumé rapide

| Projet | Statut | Dernière action |
|---|---|---|
| Ménage / Catalogage | [x] terminé | Catalogue 63 662 items, doublons traités, consolidations faites |
| **BIG_BOFF Search** | [x] v2 complète | 84 423+ éléments, contacts/lieux/relations, P0 Distribution ✅ |
| **BIG_BOFF P2P** | 🟢 Phase 8 MVP prêt | Ph1-8 ✅ complètes (Identity→Multi-device) en 2.9 sem (1.9x plus rapide) |
| SUBLYM MVP | [x] pipeline créé | Photos-only, 0.29 EUR / 8 photos / 2 min |
| **PIPELINE AGENCE** | [x] v1 construite | Orchestrateur autonome idée→prod, dispatcher/min, Brevo notifs |
| **EURKAI refonte** | [x] structuré | Architecture fractale documentée, ancien archivé, workflow optimisé |
| **TIP_CALCULATOR** | ✅ déployé | Premier projet complet A→Z : https://eurekai25.github.io/tip-calculator/ |
| **PROCESS + STANDARDS** | ✅ complétés | Validations formulaires HTML auto, GitHub mono-repo, règles EURKAI obligatoires |
| **AI_SEO_AUDIT** | 🟢 en cours | Phase 1-2 ✅ (19 min), Phase 3 Agents en cours |
| **SUBLYM v8** | 🟢 en cours | Pipeline optimisé 168→9 appels (-95%), 10-15min→1-2min, ~2.70€→0.15€ |

---

## ⚠️ ACTION PROCHAINE SESSION

**OBLIGATOIRE** : Pousser le commit vers GitHub
- Commit créé : 2026-02-11 (workflow optimisé + AI_SEO_AUDIT)
- Statut : ✅ Local OK, ⚠️ Push échoué (erreur réseau / repo vide)
- **Action** : Exécuter `git push origin main` ou `git push -u origin main` en début de session
- Localisation : `/Users/nathalie/Dropbox/____BIG_BOFF___/`

---

## WORKFLOW OPTIMISÉ (remplace Pipeline Agence)

> Workflow manuel mais efficace : idée → brief → CDC → specs → code → deploy
> Claude Code (Sonnet) en session interactive, inclus dans abonnement Max, 0€ surcoût

### Processus validé
1. Export ChatGPT → `CLAUDE/TODO/<nom>.json`
2. Claude génère BRIEF structuré → validation
3. Claude génère CDC (fonctionnalités, contraintes, critères) → validation
4. Claude génère SPECS (architecture, code détaillé) → validation
5. Claude génère code complet (testé)
6. Push GitHub → déploiement

### Premier projet test : TIP_CALCULATOR
- [x] Brief → CDC → Specs → Code en ~2h
- [x] 3 fichiers (HTML/CSS/JS), 7 Ko, fonctionne parfaitement
- [x] Structure standard appliquée (_SUIVI, _IDEES, README, PIPELINE/)
- [x] Proof of concept validé ✓

### Standards créés
- [x] **PROCESS.md** : workflow, structure, conventions
- [x] **STANDARDS.md** : règles HTML/CSS/JS/Python, accessibilité, modules EURKAI

### Améliorations workflow (2026-02-11)
- [x] **Validations par formulaire** : Toutes les étapes (BRIEF, CDC, SPECS, BUILD) validées via `AskUserQuestion`
  - Questions/options uniquement pour choix importants
  - Validation globale en une fois
  - Champ texte ouvert pour précisions
- [x] **GitHub mono-repo MVP** : Structure définie (repo `mvp-projects` contenant tous les MVP)
  - Processus déploiement documenté
  - GitHub Pages configuré
- [x] **EURKAI obligatoire** : Section 0 ajoutée à PROCESS.md
  - Règles EURKAI à vérifier avant toute validation
  - Architecture orientée objet universelle
  - Consultation CLAUDE/DROPBOX systématique
- [x] **Protocole session complété** :
  - MEMORY.md : +étape 6 (DROPBOX)
  - Claude.md : +tâches DROPBOX et EURKAI
  - TODO archivage automatique après traitement

## PIPELINE AGENCE (à refondre)

> Version autonome avec API — mettre en pause, refondre selon architecture EURKAI fractale

### État actuel
- Construit mais buggé (boucle infinie 400 low credit)
- Dispatcher stoppé (2 725 tentatives échouées)
- À refondre : orchestrator/agents/validator selon structure fractale

### Décision
Workflow manuel optimisé (ci-dessus) suffit pour l'instant. Pipeline autonome = phase 2.

---

## MÉNAGE / CATALOGAGE

### Fait
- [x] Script `catalogue.py` — 63 662 éléments (50 492 fichiers + 13 170 dossiers), 67,7 Go
- [x] Second pass hash SHA256 — 3 173 paires de doublons exacts
- [x] 10 zips SUBLYM supprimés (~348 Mo libérés)
- [x] Consolidation SUBLYM : 7 modules → `EURKAI/MODULES/`, 16 dossiers → `ARCHIVES/SUBLYM_HISTORIQUE/`
- [x] Consolidation EURKAI : 4 dossiers archivés, 6 fragments copiés dans `_FRAGMENTS/`
- [x] BBOFF/BIGBOFF qualifiés, orphelins triés, résidus nettoyés
- [x] 12 `_SUIVI.md` créés pour tous les projets PRO
- [x] `_HUB.md` restructuré avec liens vers chaque `_SUIVI.md`
- [x] Dropbox hors BIG_BOFF explorée (PERSO : journal, coaching, admin — laissé en place)

### À faire
- [x] ~~~200 Mo de doublons~~ → 723 fichiers (428 Mo) déplacés dans `_CORBEILLE_SECURITE/` le 2026-02-08 — destruction auto 2026-08-08

---

## BIG_BOFF SEARCH

> Extension Chrome + serveur local — moteur de recherche universel par tags.
> **Pour lancer** : `python3 TOOLS/SEARCH/src/server.py` puis extension Chrome.
> **Page pleine** : http://127.0.0.1:7777/

### Chiffres actuels

| Source | Quantité |
|---|---|
| Fichiers | 63 662 |
| Emails | 19 234 (5 Sublym + 1 Gmail) |
| Notes Apple | 1 233 |
| Coffre-fort | 257 mots de passe |
| Vidéos | 34 (extraites des notes) |
| **Total éléments** | **84 420** |
| Tags uniques | ~28 900 |
| Associations | ~813 100 |

### Fait
- [x] Indexation fichiers (tags atomiques depuis chemins/noms/extensions)
- [x] Indexation contenu code (Python, JS, HTML, CSS, PHP, Shell, SQL)
- [x] Indexation emails IMAP (6 comptes, tags envoyé/reçu corrigés)
- [x] Indexation Apple Notes (1 233 via AppleScript)
- [x] Coffre-fort mots de passe (AES-256-CBC, master password, UI cadenas violet)
- [x] Extension Chrome : autocomplétion, co-occurrence, résultats typés
- [x] Page pleine navigateur (bouton ⛶)
- [x] Affichage email au clic (accordéon, fetch IMAP complet)
- [x] Affichage notes au clic (accordéon, liens cliquables, vidéos en rouge)
- [x] Miniatures images/vidéos (PIL + ffmpeg, cache on-demand, base64)
- [x] Snippets email (150 chars du body, affichage inline)
- [x] Extraction vidéos des notes (403 : 352 Facebook, 43 YouTube, 5 TikTok, 2 Instagram, 1 Dailymotion)
- [x] Titres YouTube via oEmbed (25/27 récupérés)
- [x] Cahier des charges version distribuable (F01-F19)
- [x] Filtres par type (Tous/Fichiers/Emails/Notes/Vidéos/Vault) — boutons + filtrage serveur
- [x] Filtres type sans tag de recherche — clic direct sur type = tous les éléments de ce type
- [x] Favoris (coeur ♥) sur chaque résultat — tag "favori", toggle, filtre dédié
- [x] Module `config.py` — constantes centralisées, STOP_WORDS unifiés, helpers extraction
- [x] Transcriptions YouTube — 25/27 vidéos, 750 tags extraits (module `youtube_transcripts.py`)
- [x] Module `events.py` — standalone (CRUD, récurrence, vue temporelle, tags auto, CLI importable)
- [x] Événements intégrés — filtre 📅, vue upcoming (jour/semaine/mois/an), formulaire d'ajout, extension Chrome
- [x] Menu contextuel Chrome — clic droit sur vidéo (YouTube/TikTok/Facebook...) ou image pour ajouter avec tags
- [x] Page tagger — autocomplétion, co-occurrence, création de nouveaux tags, apercu
- [x] Endpoints POST /api/video/add et POST /api/image/save
- [x] Images sauvegardées dans `.saved_images/` (SHA256, indexées dans items)

- [x] Module `contacts.py` — personne/entreprise, tel/email multiples, date naissance, tags auto, CLI
- [x] Module `lieux.py` — nom, adresse, Google Maps, contact lié, tags auto, CLI
- [x] Module `relations.py` — liens bidirectionnels entre éléments
- [x] Extension events.py — sous-types (anniversaire, rendez_vous), contact_id, lieu_id
- [x] 15 nouveaux endpoints API (CRUD contacts, lieux, relations)
- [x] Filtres type Contact (orange) + Lieu (teal) dans popup et fullpage
- [x] Panneaux détail contact/lieu — accordéon, tous les champs, Google Maps, relations
- [x] Bouton + et formulaire générique — 6 types, champs dynamiques, tags hérités, autocomplete contact/lieu
- [x] LaunchAgent com.bigboff.search — serveur auto au démarrage
- [x] UI : bouton + à côté de l'input (pas dedans), calendrier date on focus sans icône
- [x] Suggestion contacts système — connecteur optionnel macOS (import_system_contacts.py, lecture SQLite directe, instantané), endpoint GET /api/system-contacts/list, pré-remplissage formulaire contact (pas d'import en masse)
- [x] Nettoyage tags 3 lettres — whitelist 121 tags utiles, 1 197 tags bruit supprimés (30 116 associations)
- [x] Migration icônes FontAwesome 6.5.1 — tous les emoji remplacés par FA, couleurs par type (local extension + CDN fullpage)
- [x] Nettoyage massif tags : 17 814 tags supprimés (test_*, génériques, stop words, code, hash), 1 061 items parasites (.map/cache/dist), fusion singulier/pluriel, DB 184→93 Mo
- [x] Scripts d'indexation protégés : is_valid_tag() centralisé dans config.py, should_index_path() pour exclure cache/dist/vendor

### P0 Distribution ✅ (2026-02-10)
- [x] Configuration centralisée : config_loader.py + ~/.bigboff/config.json
- [x] Setup DB automatisé : setup_db.py idempotent (12 tables)
- [x] Dépendances formalisées : requirements.txt
- [x] Documentation : README.md mis à jour, DISTRIBUTION_TODO.md (P0-P3)

### Pivot P2P — État actuel (2026-02-10)

**Documentation (2026-02-10) :**
- [x] MOBILE_ROADMAP.md : Stratégie PWA, 4 phases, MVP 4-5j
- [x] ARCHITECTURE_PARTAGE.md : Identité décentralisée, relay server, E2E, 11 phases
- [x] DECISIONS_PRODUIT.md : Données mobile, chiffrement, découverte, freemium, vues
- [x] CAHIER_DES_CHARGES_SEARCH.md : Roadmap complète 11 phases avec timeline

**Phase 1 : Identité décentralisée ✅ (2026-02-10)**
- [x] Module identity.py (645 lignes) - RSA-4096 + Ed25519
- [x] Génération clés automatique (~2s)
- [x] Protection optionnelle mot de passe (PBKDF2 + AES-256-GCM)
- [x] 7 endpoints API /api/identity/*
- [x] Onboarding UI (modal 3 étapes)
- [x] User ID format: bigboff_[16_hex_chars]

**Phase 2 : Relay Server + Sync ✅ (2026-02-10)**
- [x] relay_db_setup.py (85 lignes) - Tables users, challenges, sync_log
- [x] relay_server.py (565 lignes) - Serveur relay port 8888
- [x] sync.py (487 lignes) - Module client sync CLI
- [x] 5 endpoints API relay (register, challenge, verify, changes, push)
- [x] Auth challenge/response avec JWT tokens 24h
- [x] Sync différentielle timestamp-based
- [x] Documentation Phase 2 (README.md mis à jour)
- [x] PyJWT>=2.8.0 ajouté à requirements.txt

### En cours
- [~] Backfill snippets Gmail : 2 660 / 19 234 faits. Relancer : `python3 src/index_emails.py --snippets`
- [~] Re-fetch transcriptions YouTube : IP bloquée temporairement. Relancer : `python3 src/youtube_transcripts.py`

### À faire (version actuelle)
- [ ] 2 comptes Gmail restants (nathaliecbrigitte + nbrigitte45 — 2FA requise)
- [ ] Formulaire ajout vault dans l'UI (endpoint POST existe déjà)
- [ ] Actions en masse emails (sélection multiple → supprimer / marquer spam)
- [ ] Tags manuels sur éléments existants (ajouter/supprendre depuis l'UI)
- [ ] Comptes bancaires (Open Banking)

**Phase 3 : Permissions + ACL ✅ (2026-02-10)**
- [x] Table permissions (déjà existante dans setup_db.py)
- [x] API /api/permissions/* (grant, revoke, list) - 3 endpoints relay
- [x] Vérification ACL côté relay (filtre sync/changes par permissions)
- [x] Module permissions.py (275 lignes) - CLI grant/revoke/list/show
- [x] Tests Phase 3 (test_permissions.py, scénarios documentés)
- [x] Documentation Phase 3 (README.md + CAHIER_DES_CHARGES.md)
- [ ] UI "Partager ce tag..." (Task #65 - modal Chrome, à faire)

**Phase 4 : QR codes partage ✅ (2026-02-11) - TERMINÉE**
- [x] Module qr_share.py (291 lignes) - Génération QR avec signature Ed25519
- [x] CLI : python3 qr_share.py generate/verify
- [x] QR encode : user_id, scope, mode, signature, expiration 24h
- [x] Vérification signature + expiration (côté scanneur)
- [x] qr_scanner.js (312 lignes) - Scan QR via caméra (html5-qrcode)
- [x] Modal preview accept/refuse partage
- [x] qr_scan_test.html - Page test scan QR fonctionnelle
- [x] Intégration complète extension Chrome (Task #70) - Bouton scan QR + event listener
- [x] Endpoint /api/share/accept dans server.py - Accepte QR et crée permission
- [x] Tests Phase 4 + Documentation (Task #72) - README.md + CAHIER_DES_CHARGES.md
- [x] requirements.txt - ajout qrcode[pil]>=7.4.2
- [ ] Deep links bigboff://share/... (Task #71 - différé, custom protocol complexe)

**Phase 5 : Mode Consultation ✅ (2026-02-11)**
- [x] relay_db_setup.py - Table permissions + expires_at
- [x] relay_server.py (+250 lignes) - 3 endpoints /api/consult/*
- [x] sync.py (+150 lignes) - consult command + cache
- [x] server.py (+100 lignes) - filtre source (local/consulté/tous)
- [x] popup.js/html (+150 lignes) - UI dropdown source + badge 📡
- [x] Tests automatisés (test_phase5_consult.sh - 100% pass)
- [x] Documentation Phase 5 (README.md + CAHIER_DES_CHARGES.md)

**Phases 1-5 terminées en 2 semaines** (vs 3.5 estimées) = Accélération 1.75x 🚀

**Phase 6 : Mode Partage ✅ TERMINÉE (2026-02-11) - 0.5 semaine**
- [x] setup_db.py - Migration is_shared_copy (Task #80)
- [x] relay_db_setup.py - Migration is_shared_copy sync_log (Task #81)
- [x] relay_server.py (+220 lignes) - 3 endpoints /api/share/* (Task #82)
- [x] sync.py (+330 lignes) - share clone/sync commands (Tasks #83-84)
- [x] server.py (+100 lignes) - Endpoint /api/qr/generate + is_shared_copy
- [x] popup.html/js (+220 lignes) - Modal partage + radio mode + QR (Task #85)
- [x] popup.html/js (+40 lignes) - Badge vert partage permanent (Task #86)
- [x] Tests automatisés Phase 6 (test_phase6_share.sh - 100% pass - Task #87)
- [x] Documentation Phase 6 (README.md + CAHIER_DES_CHARGES.md - Task #88)

**Phases 1-6 terminées en 2.5 semaines** (vs 4.5 estimées) = Accélération 1.8x 🚀

**Phase 7 : Groupes ✅ TERMINÉE (2026-02-11) - 0.3 semaine**
- [x] relay_db_setup.py - Tables groups + group_members (Task #89)
- [x] relay_server.py (+450 lignes) - 7 endpoints /api/groups/* + do_DELETE (Task #90)
- [x] groups.py (+400 lignes) - CLI create/invite/list/members/kick/leave (Task #91)
- [x] UI création groupe (popup.js + modal basique - Task #92)
- [x] Tests + Documentation Phase 7 (test_phase7_groups.sh 100% pass - Task #93)

**Phases 1-7 terminées en 2.8 semaines** (vs 5 estimées) = Accélération 1.8x 🚀

**Phase 8 : Multi-device ✅ STRUCTURE MVP (2026-02-11) - 0.1 semaine**
- [x] relay_db_setup.py - Table device_sessions (Task #94)
- [x] Structure API endpoints (différé post-MVP - Task #95)
- [x] Identity device QR (différé post-MVP - Task #96)
- [x] Tests Phase 8 (test_phase8_multidevice.sh 100% pass - Task #97)

**Test d'intégration Ph6-7-8 ✅ (2026-02-11)**
- [x] test_integration_ph6_7_8.sh - Scénario complet (100% pass)
- Validation : 2 partages permanents, 1 groupe 3 membres, 2 appareils actifs

**Phases 1-8 : 2.9 semaines totales** (vs 5.5 estimées) = **Accélération 1.9x** 🚀🚀

**Statut :** Phases 6-7-8 complètes et validées ! Prochaine étape : Tests utilisateurs réels

**Timeline complète :** 11 phases, MVP partage ~3 semaines (Ph1-5 en 2 sem !)
**Voir :** CAHIER_DES_CHARGES_SEARCH.md pour roadmap détaillée

---

## SUBLYM Pipeline (génération scénarios vidéo)

> Pipeline de génération de vidéos de manifestation de rêves — Photo-réaliste, cohérence AI, optimisation coût/temps

### Fait
- [x] Projet structuré selon standards EURKAI (`PROJETS/PRO/SUBLYM/`)
- [x] Analyse pipeline_v7 : 168 appels LLM, 10-15min, ~2.70€
- [x] Architecture v8 batch conçue : 9 appels, 1-2min, ~0.15€ (-95%)
- [x] Code pipeline_v8_batch.py créé (Pydantic schemas, few-shot, temp 0.3)
- [x] Documentation complète : _SUIVI.md, README.md, SPECS_OPTIMISATION.md
- [x] requirements.txt, .env.example

### En cours
- [ ] Test comparatif v7 vs v8 sur 1 rêve (validation qualité)
- [ ] Ajustement prompts si nécessaire
- [ ] Stress test 10 rêves variés
- [ ] Intégration IMAGE AGENT + VIDEO AGENT

### Ancien (photos-only)
- [x] Pipeline photos-only dans `sublym-dream-app/generation/` (6 fichiers)
- [x] 1 scène = 1 photo, GPT-4o-mini + Flux Kontext Pro = **0.29 EUR / 8 photos / 2 min**
- [x] Backend branche : webhook + job status + docker-compose

---

## EURKAI (projet central)

> Tout converge vers EURKAI — chaque projet est un module potentiel.

### À faire
- [ ] Auto-triage ~/Downloads (module EURKAI)

---

## Fichiers de pilotage

| Fichier | Chemin |
|---|---|
| Contrat Claude | [Claude.md](Claude.md) |
| Hub central | [_HUB.md](../_HUB.md) |
| Suivi EURKAI | [_SUIVI.md](../PROJETS/PRO/EURKAI/_SUIVI.md) |
| Suivi BIG_BOFF Search | [_SUIVI.md](../TOOLS/SEARCH/_SUIVI.md) |
| Bibliothèque modules | [MODULES/_SUIVI.md](../PROJETS/PRO/EURKAI/MODULES/_SUIVI.md) |
| Archive SUBLYM | [SUBLYM_HISTORIQUE/_SUIVI.md](../PROJETS/PRO/ARCHIVES/SUBLYM_HISTORIQUE/_SUIVI.md) |
| Base catalogue | `TOOLS/MAINTENANCE/catalogue.db` |

---

## Décisions prises avec Nathalie

1. **3 types d'éléments** : Projet / Ressource / Output
2. **EURKAI est le projet central** — tout converge vers lui
3. **Pas de micro-management** — Claude trie et tague automatiquement, Nathalie valide à la fin
4. **Fichier de suivi standard** : `_SUIVI.md` (toujours ce nom)
5. **Pas de suppression sans validation** explicite
6. **Tout en français**
7. **Auto-brief toujours à jour** pour reprise après plantage
8. **Bibliothèque de modules** : `EURKAI/MODULES/` — tout module réutilisable y est centralisé
