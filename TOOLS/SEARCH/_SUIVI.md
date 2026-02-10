# BIG_BOFF Search — Suivi
 claude --resume search 

 
> Extension Chrome + serveur local — moteur de recherche universel par tags.
> Noyau du système de gestion BIG_BOFF / EURKAI.
> **Pour lancer** : `python3 TOOLS/SEARCH/src/server.py` puis extension Chrome.
> **Page pleine** : http://127.0.0.1:7777/

**Statut** : 🟢 actif
**Cree** : 2026-02-08
**Derniere MAJ** : 2026-02-10 21:00

---

## Ce que fait l'extension — Resume complet

### Recherche universelle

- **Recherche par tags** avec autocompletion instantanee (debounce 150ms)
- **Tags co-occurrents** : suggestion des tags les plus associes aux resultats
- **Inclusion / exclusion** : clic = ajouter (+vert), long clic = exclure (-rouge), double clic = supprimer
- **Filtres par type** (radio, un seul actif) : Tous / Fichiers / Emails / Notes / Videos / Evenements / Vault / Favoris

### 9 types de contenus indexes

| Type | Quantite | Ce qu'on peut faire |
|---|---|---|
| **Fichiers** | 63 662 | Clic = ouvrir, bouton Finder, miniatures images/videos |
| **Emails** | 19 234 | Clic = accordeon (fetch IMAP complet, HTML ou texte), snippets 150 chars |
| **Notes Apple** | 1 233 | Clic = accordeon (titre, date, body), liens cliquables, videos en rouge |
| **Vault** | 257 | Coffre-fort AES-256-CBC, mot de passe maitre, voir/copier le mdp |
| **Videos** | 403+ | Extraites des notes + ajout manuel (clic droit), clic = ouvre l'URL |
| **Evenements** | illimite | CRUD, recurrence, sous-types (anniversaire, RDV), formulaire d'ajout |
| **Contacts** | illimite | Personne/entreprise, tel/email multiples, naissance, photo, liens |
| **Lieux** | illimite | Nom, adresse, lien Google Maps, contact lie, description |
| **Favoris** | sur tout | Coeur sur n'importe quel resultat, filtre dedie |

### Menu contextuel Chrome (nouveau)

- **Clic droit sur un lien video** (YouTube, TikTok, Facebook, Instagram, Vimeo, Dailymotion) → "Ajouter cette video a BIG_BOFF"
- **Clic droit sur la page** (si page video) → "Ajouter cette page video a BIG_BOFF"
- **Clic droit sur une image** → "Enregistrer et tagger cette image"
- Page tagger avec :
  - Titre auto (oEmbed YouTube, noembed.com pour les autres)
  - Tags pre-remplis (`video` + plateforme, ou `image`)
  - Champ de saisie avec **autocompletion + co-occurrence**
  - Option **"Creer 'xxx'"** si le tag n'existe pas encore
  - Apercu de l'image
- Images sauvegardees dans `.saved_images/` (SHA256, indexees comme fichiers)

### Interfaces

| Interface | Acces |
|---|---|
| **Popup Chrome** | Clic sur l'icone BIG_BOFF dans la barre Chrome |
| **Page pleine** | http://127.0.0.1:7777/ ou bouton ⛶ dans le popup |
| **Menu contextuel** | Clic droit sur video/image dans n'importe quel site |

---

## Chiffres actuels

| Metrique | Valeur |
|---|---|
| Fichiers indexes | 63 662 |
| Emails indexes | 19 234 (5 Sublym + 1 Gmail) |
| Notes Apple indexees | 1 233 |
| Coffre-fort (mots de passe) | 257 |
| Videos extraites | 403 (352 Facebook, 43 YouTube, 5 TikTok, 2 Instagram, 1 Dailymotion) |
| **Total elements** | **84 423+** |
| Tags uniques | ~46 700 |
| Associations tag/item | ~982 600 |

---

## Architecture

### Scripts d'indexation (`src/`)

| Script | Role | Donnees |
|---|---|---|
| `generate_tags.py` | Tags depuis chemins, noms, extensions | 63 662 items |
| `index_content.py` | Contenu code/texte (fonctions, classes, imports) | 4 427 fichiers |
| `index_emails.py` | Emails IMAP (sujet, expediteur, domaine) | 19 234 emails |
| `index_notes.py` | Apple Notes via AppleScript + extraction videos | 1 233 notes, 403 videos |
| `import_vault.py` | Import CSV mots de passe → coffre chiffre | 257 entrees |
| `events.py` | Evenements (CRUD, recurrence, subtypes, tags) | standalone + CLI |
| `contacts.py` | Contacts personne/entreprise (CRUD, tags) | standalone + CLI |
| `lieux.py` | Lieux avec Google Maps (CRUD, tags) | standalone + CLI |
| `relations.py` | Liens entre elements (contact↔lieu, etc.) | standalone + CLI |
| `youtube_transcripts.py` | Transcriptions YouTube → tags | 25/27 videos |
| `config.py` | Configuration centralisee (DB, offsets, stop words) | module partage |
| `import_system_contacts.py` | Connecteur macOS Contacts.app (lecture SQLite directe) | suggestion formulaire |

### Serveur (`src/server.py`)

API locale `http://127.0.0.1:7777` — aucune dependance externe (Python stdlib).

| Endpoint | Role |
|---|---|
| `/api/autocomplete?q=` | Tags commencant par le prefixe |
| `/api/search?include=&exclude=` | Recherche par tags (+/-), filtre par type |
| `/api/cooccurrence?include=` | Tags associes aux resultats |
| `/api/stats` | Statistiques generales |
| `/api/open?id=` | Ouvrir un fichier (macOS `open`) |
| `/api/reveal?id=` | Montrer dans Finder |
| `/api/email?id=` | Contenu complet d'un email (fetch IMAP) |
| `/api/note?id=` | Contenu complet d'une note Apple |
| `/api/thumbnail?id=&size=` | Miniature image/video (base64, cache on-demand) |
| `POST /api/vault/unlock` | Deverrouiller le coffre |
| `/api/vault/get?id=` | Lire une entree (dechiffrement AES) |
| `/api/vault/copy?id=` | Copier le mot de passe dans presse-papiers |
| `POST /api/vault/add` | Ajouter une entree au coffre |
| `/api/vault/lock` | Verrouiller le coffre |
| `/api/vault/status` | Etat du coffre |
| `POST /api/favorite` | Toggle favori sur un item |
| `/api/favorite/check?ids=` | Verifier quels items sont favoris |
| `GET /api/event?id=` | Detail d'un evenement |
| `GET /api/events/upcoming?mode=` | Vue temporelle (day/week/month/year) |
| `POST /api/event` | Creer un evenement |
| `PUT /api/event` | Modifier un evenement |
| `DELETE /api/event` | Supprimer un evenement |
| `POST /api/video/add` | Ajouter une video (menu contextuel) |
| `POST /api/image/save` | Sauvegarder et tagger une image (menu contextuel) |
| `GET /api/contact?id=` | Detail d'un contact |
| `GET /api/contacts/search?q=` | Recherche contacts (autocomplete formulaires) |
| `POST /api/contact` | Creer un contact |
| `PUT /api/contact` | Modifier un contact |
| `DELETE /api/contact` | Supprimer un contact |
| `GET /api/lieu?id=` | Detail d'un lieu (avec lien Google Maps) |
| `GET /api/lieux/search?q=` | Recherche lieux (autocomplete formulaires) |
| `POST /api/lieu` | Creer un lieu |
| `PUT /api/lieu` | Modifier un lieu |
| `DELETE /api/lieu` | Supprimer un lieu |
| `GET /api/relations?type=&id=` | Elements lies a un element |
| `POST /api/relation` | Creer un lien entre elements |
| `DELETE /api/relation` | Supprimer un lien |
| `DELETE /api/email` | Supprimer email (mode: db_only/permanent, IMAP si permanent) |
| `DELETE /api/note` | Supprimer note (mode: db_only/permanent) |
| `DELETE /api/file` | Supprimer fichier (mode: db_only/permanent, corbeille si permanent) |
| `DELETE /api/vault` | Supprimer entree vault (mode: db_only/permanent) |
| `DELETE /api/video` | Supprimer video (mode: db_only/permanent) |
| `GET /api/system-contacts/list` | Suggestion contacts systeme (lecture seule, connecteur optionnel) |
| `/` | Page de recherche plein ecran |

### Extension Chrome (`extension/`)

| Fichier | Role |
|---|---|
| `manifest.json` | Manifest V3, permissions, service worker |
| `popup.html` / `popup.js` | Interface popup (recherche, filtres, resultats) |
| `background.js` | Service worker : menus contextuels, fetch image cross-origin |
| `tagger.html` / `tagger.js` | Page de tagging (titre auto, autocompletion, co-occurrence) |

### Config

| Fichier | Role |
|---|---|
| `email_accounts.json` | Identifiants IMAP (local uniquement) |
| `catalogue.db` | Base SQLite (dans `TOOLS/MAINTENANCE/`) |
| `.thumbnails/` | Cache miniatures images/videos |
| `.saved_images/` | Images sauvegardees via menu contextuel |

---

## Pivot P2P — Architecture de partage décentralisée

> **Date décision** : 2026-02-10
> **Vision** : Outil transmis viralement entre utilisateurs (QR code/SMS), sans authentification traditionnelle, partage granulaire par tags, freemium sur fonctionnalités (pas volume)

### Documentation créée

| Fichier | Contenu |
|---|---|
| **MOBILE_ROADMAP.md** | Stratégie PWA — 4 phases (PWA base, VPS, Auth, Optimisations), MVP 4-5j |
| **ARCHITECTURE_PARTAGE.md** | Architecture technique complète — identité décentralisée (RSA-4096), relay server, 2 modes partage (consultation/clone), permissions ACL, E2E encryption, 10 phases implémentation (8-10 semaines) |
| **DECISIONS_PRODUIT.md** | Décisions actées — données indexées mobile (tout), chiffrement E2E obligatoire, découverte QR/SMS, freemium features (illimité gratuit), design minimaliste, vues (Planning/Liste/Budget + premium Kanban/Timeline/Map/Graph) |

### Concepts clés

**Identité décentralisée** : Pas de login/pwd, clés pub/priv (RSA-4096) générées à l'install, User ID = hash(public_key)

**2 modes de partage** :
- **Consultation** : B voit données de A en temps réel, révocable instantanément
- **Partage** : Clone vers base de B, sync continue, snapshot figé si révoqué

**Permissions granulaires** : ACL par tag/élément/groupe, vérification côté relay

**Relay server** : Ne stocke QUE métadonnées (permissions, sync logs), PAS les données utilisateurs

**E2E encryption** : AES-256-GCM + RSA-4096, transparent pour l'utilisateur, relay ne peut pas déchiffrer

**Découverte** : QR code ou SMS avec tokens temporaires uniquement, pas d'annuaire public

**Freemium** : Basé sur fonctionnalités (multi-support, vues avancées, IA), PAS sur volume
- Gratuit : éléments illimités, 1 support, vues core (Liste/Planning/Budget)
- Premium 5€/mois : multi-support, vues premium, OCR, transcription, IA

**Coûts serveur** : Volume non limitant, relay léger (métadonnées uniquement), 100k users = 25€/mois VPS

### Timeline implémentation

| Phase | Durée | Description |
|---|---|---|
| Ph1 : Identité | 1 sem | Clés pub/priv, auth décentralisée |
| Ph2 : Relay | 1 sem | Serveur VPS Ionos, sync basique |
| Ph3 : Permissions | 1 sem | ACL par tag/élément/groupe |
| Ph4 : QR + SMS | 3j | QR code scan, liens token temporaire |
| Ph5 : Consultation | 3j | Voir données temps réel |
| Ph6 : Partage | 1 sem | Clone + sync continue |
| Ph7 : Groupes | 3j | Créer/gérer groupes |
| Ph8 : Multi-support | 3j | QR activation type WhatsApp Web |
| Ph9 : Freemium | 1 sem | Licences, paiement Stripe |
| Ph10 : E2E | 3j | Chiffrement obligatoire (libsodium) |
| Ph11 : Mobile UI | 1 sem | Responsive, gestes tactiles, PWA |
| Ph12 : Vues premium | 1 sem | Kanban, Timeline, Map, Graph |

**Total MVP P2P** : ~10 semaines (2.5 mois)

### Métriques succès post-launch

| Objectif | 6 mois | 1 an | 2 ans |
|---|---|---|---|
| Users actifs | 1 000 | 10 000 | 100 000 |
| Conversion premium | 10% (100) | 15% (1 500) | 20% (20 000) |
| Revenus/mois | 500€ | 7 500€ | 100 000€ |

---

## A faire

### Court terme

- [] Epurer la bdd (5 tags max par objet)
- [~] **Backfill snippets Gmail** : 2 660 / 19 234 faits. Relancer : `python3 src/index_emails.py --snippets`
- [~] **Re-fetch transcriptions YouTube** : IP bloquee temporairement. Relancer : `python3 src/youtube_transcripts.py`
- [ ] **2 comptes Gmail restants** : activer 2FA sur nathaliecbrigitte et nbrigitte45 pour mots de passe d'app
- [ ] **Formulaire ajout vault dans l'UI** : endpoint POST existe deja, manque le formulaire
- [x] **Lancement automatique** : serveur au demarrage du Mac (LaunchAgent com.bigboff.search)

### Moyen terme

- [ ] **Tags manuels** : ajouter ses propres tags a un element existant depuis l'UI
- [ ] **Actions en masse emails** : selection multiple → supprimer / marquer spam
- [ ] **Videos YouTube** : indexer les playlists et favoris (en plus des videos deja extraites des notes)
- [ ] **Comptes bancaires** : consultation et operations via Open Banking (GoCardless/Nordigen)

### Long terme (produit)

- [ ] **Version Windows** : installeur, backup GitHub, interface de transition
- [ ] **Agent IA integre** : menage intelligent avec validation utilisateur
- [ ] **Indexation full-text** : contenu complet des fichiers texte (pas juste les mots frequents)

---

## Cahier des charges — Version distribuable

### Fonctionnalites en place

| # | Fonctionnalite | Detail technique | Statut |
|---|---|---|---|
| F01 | **Indexation fichiers** | Scan arborescence, tags atomiques depuis chemin/nom/extension | fait |
| F02 | **Indexation contenu code** | Extracteurs Python, JS/TS, HTML, CSS, PHP, Shell, SQL | fait |
| F03 | **Indexation contenu texte** | Mots-clefs frequents dans MD, TXT, JSON, CSV | fait |
| F04 | **Indexation emails IMAP** | Headers, multi-comptes, tags auto (domaine, dossier, envoye/recu) | fait |
| F05 | **Indexation Apple Notes** | Export AppleScript, tags titre + corps + videos + URLs | fait |
| F06 | **Recherche par tags** | Inclusion/exclusion, co-occurrence, autocompletion | fait |
| F07 | **Extension Chrome** | Popup + page pleine + menu contextuel, tags cliquables, resultats types | fait |
| F08 | **Ouverture directe** | Clic fichier = ouvre avec app par defaut, bouton Finder | fait |
| F09 | **Lecture email** | Clic email = fetch IMAP complet, affichage HTML ou texte | fait |
| F10 | **Serveur local** | Python pur, zero dependance, port 7777, CORS | fait |
| F11 | **Coffre mots de passe** | AES-256-CBC, master password, voir/copier, import CSV | fait |
| F12 | **Miniatures** | PIL pour images, ffmpeg pour videos, cache on-demand, base64 | fait |
| F20 | **Evenements** | CRUD, recurrence, vue temporelle, tags auto, CLI | fait |
| F21 | **Menu contextuel** | Ajout video/image depuis n'importe quel site, autocompletion tags | fait |
| F22 | **Favoris** | Coeur toggle sur tout element, filtre dedie | fait |
| F23 | **Contacts** | Personne/entreprise, tel/email multiples, naissance, tags auto, CLI | fait |
| F24 | **Lieux** | Nom, adresse, Google Maps, contact lie, tags auto, CLI | fait |
| F25 | **Relations** | Liens entre elements (contact↔lieu, contact↔event, etc.) | fait |
| F26 | **Sous-types events** | Anniversaire (contact oblig.), RDV (contact+lieu oblig.) | fait |
| F27 | **Formulaire ajout** | Bouton +, 6 types, champs dynamiques, tags herites, autocomplete | fait |
| F28 | **Lancement auto** | LaunchAgent macOS, RunAtLoad + KeepAlive | fait |
| F29 | **Suggestion contacts systeme** | Connecteur macOS (SQLite), autocomplete formulaire contact | fait |
| F30 | **Icones FontAwesome** | FA 6.5.1 local (extension) + CDN (fullpage), couleurs par type | fait |
| F31 | **Nettoyage tags 3 lettres** | Whitelist 121 tags utiles, suppression 1 197 tags bruit | fait |
| F32 | **Suppression avec modal** | Modal 2 options (DB seule/Définitive), tous types, IMAP pour emails | fait |
| F33 | **Transfert état popup→fullpage** | Paramètres URL (include/exclude/types), restauration auto | fait |
| F34 | **Fetch métadonnées URL** | BeautifulSoup, OpenGraph/meta tags, gratuit/scalable | fait |
| F35 | **Cache métadonnées URL** | Table SQLite, évite refetch, 98% succès | fait |
| F36 | **Nettoyage tags URL parasites** | Suppression fbclid/mibextid/utm_* (191 tags), STOP_WORDS étendu | fait |
| F37 | **Configuration centralisée** | config_loader.py, ~/.bigboff/config.json, expansion ~ et $VAR | fait |
| F38 | **Setup DB automatisé** | setup_db.py idempotent (12 tables), création indexes | fait |
| F39 | **Config par défaut** | config.default.json template, paths personnalisables | fait |
| F40 | **Dépendances Python** | requirements.txt (beautifulsoup4, requests, Pillow) | fait |
| F41 | **Documentation distribution** | README.md mis à jour, DISTRIBUTION_TODO.md (P0-P3) | fait |
| F42 | **Architecture P2P documentée** | MOBILE_ROADMAP.md, ARCHITECTURE_PARTAGE.md, DECISIONS_PRODUIT.md | fait |

### Fonctionnalites prevues

| # | Fonctionnalite | Priorite | Complexite |
|---|---|---|---|
| F13 | **Actions en masse emails** | haute | haute |
| F14 | **Tags manuels** | moyenne | faible |
| F15 | **Indexation YouTube playlists** | moyenne | moyenne |
| F16 | **Lancement automatique** | moyenne | faible |
| F17 | **Comptes bancaires** | basse | haute |
| F18 | **Agent IA integre** | basse | haute |
| F19 | **Indexation full-text** | basse | moyenne |

---

## Historique

| Date | Action |
|---|---|
| 2026-02-08 | Creation du projet, conventions, structure |
| 2026-02-08 | `generate_tags.py` — 726 649 tags, 9 909 uniques |
| 2026-02-08 | `server.py` — micro-serveur, 4 endpoints |
| 2026-02-08 | Extension Chrome — popup, autocompletion, co-occurrence |
| 2026-02-08 | Liens cliquables : ouvrir fichier + Finder |
| 2026-02-08 | `index_content.py` — 4 427 fichiers → 37 921 tags |
| 2026-02-08 | `index_emails.py` — 5 comptes Sublym + 1 Gmail = 19 234 emails |
| 2026-02-08 | Page pleine (bouton ⛶) |
| 2026-02-08 | UX tags refondue (clic/long clic/double clic) |
| 2026-02-08 | `index_notes.py` — 1 233 Apple Notes |
| 2026-02-08 | Affichage email au clic — fetch IMAP complet, accordeon UI |
| 2026-02-08 | Coffre-fort — 257 entrees, AES-256-CBC, master password |
| 2026-02-08 | Miniatures images/videos — PIL + ffmpeg, cache, base64 |
| 2026-02-08 | Tags envoye/recu corriges (543 envoyes, 18 722 recus) |
| 2026-02-08 | Snippets email — 150 chars du body dans les resultats |
| 2026-02-08 | Affichage notes au clic — accordeon, liens cliquables |
| 2026-02-08 | Extraction videos des notes — 403 videos (YouTube, Facebook, TikTok, Instagram, Dailymotion) |
| 2026-02-08 | Titres YouTube via oEmbed (25/27 recuperes) |
| 2026-02-08 | Filtres par type + favoris (coeur) |
| 2026-02-08 | Module `config.py` — constantes centralisees, stop words, helpers |
| 2026-02-08 | Transcriptions YouTube — 25/27 videos, 750 tags extraits |
| 2026-02-08 | Re-export Apple Notes (body complet) — 289 tronquees corrigees |
| 2026-02-08 | Module `events.py` — standalone (CRUD, recurrence, get_upcoming, CLI) |
| 2026-02-08 | Evenements integres — 5 endpoints API, filtre, vue upcoming, formulaire |
| 2026-02-08 | Menu contextuel Chrome — clic droit video/image, tagger avec autocompletion |
| 2026-02-08 | Fix CSP Manifest V3 — suppression event handlers inline |
| 2026-02-08 | Filtres type en mode radio (un seul actif a la fois) |
| 2026-02-08 | LaunchAgent com.bigboff.search — serveur auto au demarrage |
| 2026-02-08 | Module `contacts.py` — personne/entreprise, tel/email multiples, naissance, tags auto |
| 2026-02-08 | Module `lieux.py` — nom, adresse, Google Maps, contact lie, tags auto |
| 2026-02-08 | Module `relations.py` — liens bidirectionnels entre elements |
| 2026-02-08 | Extension events.py — sous-types (anniversaire, rendez_vous), contact_id, lieu_id |
| 2026-02-08 | 15 nouveaux endpoints API (CRUD contacts, lieux, relations) |
| 2026-02-08 | Filtres type Contact (orange) + Lieu (teal) — popup + fullpage |
| 2026-02-08 | Panneaux detail contact/lieu — accordeon, liens, Google Maps |
| 2026-02-08 | Bouton + et formulaire generique — 6 types, champs dynamiques, tags herites |
| 2026-02-08 | UI : bouton + a cote du champ (flex), calendrier date on focus sans icone |
| 2026-02-08 | Connecteur contacts systeme (import_system_contacts.py) — export AppleScript par blocs |
| 2026-02-08 | Suggestion semi-auto contacts systeme dans formulaire ajout + import en masse |
| 2026-02-08 | Réécriture connecteur contacts : SQLite directe (instantané), suppression import en masse |
| 2026-02-08 | Nettoyage tags : whitelist 3 lettres (121 utiles), suppression 1 197 tags bruit (30 116 assoc.) |
| 2026-02-08 | Migration icones : tous les emoji → FontAwesome 6.5.1 (local + CDN), couleurs par type |
| 2026-02-10 | Modal suppression — 2 modes (DB seule/Définitive), tous types, IMAP emails, corbeille fichiers |
| 2026-02-10 | Transfert état popup→fullpage — URL params (include/exclude/types), restauration automatique |
| 2026-02-10 | Analyse origine tags parasites — fbclid, mibextid, utm_* extraits depuis corps notes |
| 2026-02-10 | Suppression extraction tags depuis URLs — domaines principaux uniquement (facebook, youtube...) |
| 2026-02-10 | Fetch métadonnées URL — BeautifulSoup, OpenGraph/Twitter/meta tags, gratuit/scalable |
| 2026-02-10 | Cache métadonnées URL — Table SQLite, 49 URLs cachées, 98% succès, évite refetch |
| 2026-02-10 | Nettoyage base existante — 191 tags URL parasites supprimés (campaign:128, mibextid:34...) |
| 2026-02-10 | Extension STOP_WORDS — fbclid, mibextid, gclid, igshid, utm_* (config.py + index_notes.py) |
| 2026-02-10 | **P0 Distribution** — config_loader.py (load/merge/expand), setup_db.py (12 tables) |
| 2026-02-10 | Configuration centralisée — config.default.json + ~/.bigboff/config.json override |
| 2026-02-10 | Dépendances formalisées — requirements.txt (beautifulsoup4, requests, Pillow) |
| 2026-02-10 | README.md mis à jour — installation avec config_loader --init, setup_db.py |
| 2026-02-10 | DISTRIBUTION_TODO.md — checklist P0-P3, P0 ✅ (centralisation config) |
| 2026-02-10 | **Pivot P2P** — MOBILE_ROADMAP.md (PWA, 4 phases, VPS, 4-5j MVP) |
| 2026-02-10 | Architecture partage — ARCHITECTURE_PARTAGE.md (identité décentralisée, relay, E2E) |
| 2026-02-10 | Décisions produit — DECISIONS_PRODUIT.md (données, chiffrement, découverte, freemium) |
