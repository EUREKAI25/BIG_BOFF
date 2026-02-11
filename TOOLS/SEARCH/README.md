# BIG_BOFF Search

Extension Chrome + serveur local — moteur de recherche universel par tags.
Indexe et recherche dans : fichiers, emails, notes, vidéos, événements, contacts, vault, etc.

## Installation rapide

```bash
# 1. Installer dépendances Python
pip install -r requirements.txt

# 2. Initialiser configuration
python src/config_loader.py --init
# → Crée ~/.bigboff/config.json

# 3. Éditer la config (chemins personnalisés)
nano ~/.bigboff/config.json
# Adapter db_path, dropbox_root, email_accounts_file

# 4. Créer la base de données
python src/setup_db.py

# 5. Indexer vos données (selon ce que vous avez)
python src/generate_tags.py        # Fichiers
python src/index_notes.py          # Apple Notes
python src/index_emails.py         # Emails IMAP
python src/index_content.py        # Contenu code/texte

# 6. Lancer le serveur
python src/server.py
# → http://127.0.0.1:7777
```

### Installer l'extension Chrome

1. Ouvrir Chrome → `chrome://extensions`
2. Activer le **Mode développeur** (toggle en haut à droite)
3. Cliquer **Charger l'extension non empaquetée**
4. Sélectionner le dossier : `extension/`
5. L'icône apparaît dans la barre Chrome

## Utilisation

1. Cliquer sur l'icône BIG_BOFF Search
2. Taper un mot-clef → autocomplétion instantanée
3. Sélectionner un tag → résultats affichés
4. **Tags associés** apparaissent :
   - **Clic** : ajouter (+vert)
   - **Long clic** : exclure (-rouge)
   - **Double clic** : retirer
5. **Filtres par type** : Fichiers, Emails, Notes, Vidéos, etc.
6. **Bouton +** : Ajouter événement, contact, lieu
7. **Bouton ⛶** : Ouvrir en pleine page

## Configuration

Fichier `~/.bigboff/config.json` (créé par `--init`)

**Chemins principaux :**
- `db_path` : Base de données SQLite
- `dropbox_root` : Racine fichiers à indexer
- `export_dir` : Export Apple Notes temporaire
- `email_accounts_file` : Comptes IMAP
- `thumbnails_dir`, `saved_images_dir` : Caches

**Afficher config actuelle :**
```bash
python src/config_loader.py --show
```

## Structure projet

```
SEARCH/
├── config.default.json      # Config par défaut (template)
├── requirements.txt          # Dépendances Python
├── README.md                 # Ce fichier
├── _SUIVI.md                 # Suivi détaillé du projet
├── DISTRIBUTION_TODO.md      # Checklist distribution
├── src/
│   ├── config_loader.py     # Chargeur config centralisée
│   ├── setup_db.py          # Initialisation base de données
│   ├── config.py            # Constantes, helpers partagés
│   ├── server.py            # Serveur API local (port 7777)
│   ├── generate_tags.py     # Indexation fichiers
│   ├── index_notes.py       # Indexation Apple Notes + URLs
│   ├── index_emails.py      # Indexation emails IMAP
│   ├── index_content.py     # Indexation contenu code/texte
│   ├── events.py            # Module événements (CRUD, CLI)
│   ├── contacts.py          # Module contacts (CRUD, CLI)
│   ├── lieux.py             # Module lieux (CRUD, CLI)
│   ├── relations.py         # Liens entre éléments
│   ├── import_vault.py      # Import coffre-fort
│   └── ...
└── extension/               # Extension Chrome
    ├── manifest.json
    ├── popup.html
    ├── popup.js
    ├── background.js
    └── fa/                  # FontAwesome 6.5.1
```

## API Endpoints

### Recherche & Catalogue

| Endpoint | Description |
|----------|-------------|
| `/api/autocomplete?q=` | Tags commençant par le préfixe |
| `/api/search?include=&exclude=&types=` | Recherche par tags (+/-) + filtres type |
| `/api/cooccurrence?include=` | Tags associés aux résultats |
| `/api/stats` | Statistiques générales |
| `/api/open?id=` | Ouvrir fichier |
| `/api/reveal?id=` | Montrer dans Finder |
| `/api/email?id=` | Contenu email (fetch IMAP) |
| `/api/note?id=` | Contenu note Apple |
| `/api/thumbnail?id=&size=` | Miniature image/vidéo |

### Vault, Événements, Contacts

| Endpoint | Description |
|----------|-------------|
| `POST /api/vault/unlock` | Déverrouiller coffre-fort |
| `POST /api/favorite` | Toggle favori |
| `DELETE /api/{type}` | Supprimer élément (modal 2 modes) |
| `POST /api/event` | Créer événement |
| `POST /api/contact` | Créer contact |
| `POST /api/lieu` | Créer lieu |

### Identity P2P (Phase 1)

| Endpoint | Description |
|----------|-------------|
| `GET /api/identity/status` | Statut identité |
| `GET /api/identity/public_key` | Clés publiques |
| `POST /api/identity/init` | Créer identité |
| `POST /api/identity/sign` | Signer données |
| `POST /api/identity/verify` | Vérifier signature |
| `POST /api/identity/protect` | Protéger avec mot de passe |
| `POST /api/identity/unlock` | Déverrouiller session |

**Voir _SUIVI.md pour liste complète**

## Fonctionnalités

- ✅ Recherche par tags (inclusion/exclusion)
- ✅ 9 types de contenus (fichiers, emails, notes, vidéos, events, contacts, lieux, vault, favoris)
- ✅ Autocomplétion instantanée
- ✅ Tags co-occurrents
- ✅ Filtres par type (radio)
- ✅ Miniatures images/vidéos
- ✅ Fetch métadonnées URL (BeautifulSoup, cache SQLite)
- ✅ Suppression avec modal (DB seule / Définitive)
- ✅ Menu contextuel (ajout vidéo/image depuis n'importe quel site)
- ✅ Coffre-fort AES-256
- ✅ Événements avec récurrence
- ✅ Contacts & lieux avec Google Maps
- ✅ Favoris (cœur sur tout élément)
- ✅ Page pleine + popup Chrome
- ✅ LaunchAgent macOS (démarrage auto)

## Phase 1 P2P — Identité décentralisée

**⚡ Nouveau** : Système d'identité cryptographique pour le partage P2P (Phase 1/11)

### Présentation

- **User ID unique** : dérivé du hash SHA-256 de la clé publique → `bigboff_[16 hex]`
- **Double algorithme crypto** :
  - RSA-4096 : chiffrement asymétrique (compatibility, E2E)
  - Ed25519 : signatures rapides (auth, challenges)
- **Stockage local** : `~/.bigboff/identity.json` (hors Dropbox, chmod 600)
- **Protection optionnelle** : mot de passe + PBKDF2 + AES-256-GCM
- **Génération transparente** : ~2 secondes, automatique au premier lancement

### CLI identity.py

```bash
# Générer nouvelle identité
python src/identity.py init --alias "Votre nom"

# Afficher identité
python src/identity.py show

# Protéger avec mot de passe
python src/identity.py protect --password

# Exporter (backup)
python src/identity.py export --output ~/backup_identity.json

# Vérifier une signature
python src/identity.py verify --signature <sig> --data <data>
```

### API Endpoints Identity

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/identity/status` | GET | Statut identité (initialized, user_id, protected) |
| `/api/identity/public_key` | GET | Clés publiques RSA + Ed25519 |
| `/api/identity/init` | POST | Créer nouvelle identité (`{"alias": "...", "password": "..."}`) |
| `/api/identity/sign` | POST | Signer données (`{"data": "...", "key_type": "ed25519"}`) |
| `/api/identity/verify` | POST | Vérifier signature (`{"data": "...", "signature": "...", "public_key": "..."}`) |
| `/api/identity/protect` | POST | Protéger avec mot de passe (`{"password": "..."}`) |
| `/api/identity/unlock` | POST | Déverrouiller session (`{"password": "..."}`) |

### Onboarding UI

Au premier lancement de l'extension, un modal s'affiche automatiquement si aucune identité n'existe :

1. **Étape 1** : Formulaire (alias optionnel, protection mot de passe)
2. **Étape 2** : Loading (génération clés ~2s)
3. **Étape 3** : Succès (User ID affiché, backup disponible)

Fichiers : `extension/onboarding.html`, `extension/onboarding.js`

### Format identity.json

```json
{
  "version": "1.0",
  "user_id": "bigboff_a7f3c2e1d9f8b5c4",
  "alias": "Nathalie",
  "created_at": "2026-02-10T15:30:00",
  "keys": {
    "rsa": {
      "public_key": "-----BEGIN PUBLIC KEY-----...",
      "private_key_encrypted": null,
      "algorithm": "RSA-4096"
    },
    "ed25519": {
      "public_key": "base64_32_bytes",
      "private_key_encrypted": null,
      "algorithm": "Ed25519"
    }
  },
  "protection": {
    "enabled": false,
    "salt": null,
    "iterations": 100000
  }
}
```

### Sécurité

- **Permissions fichier** : 600 (lecture/écriture propriétaire uniquement)
- **Clés privées** : jamais exposées par API (uniquement signatures)
- **Session timeout** : 1h d'inactivité
- **Hors cloud** : `~/.bigboff/` non synchronisé (pas de Dropbox/iCloud)
- **Chiffrement clés** : AES-256-GCM + PBKDF2-SHA256 (100 000 itérations)

### Prochaines phases P2P

Voir `ARCHITECTURE_PARTAGE.md` pour architecture complète 11 phases.

---

## Phase 2 P2P — Relay Server + Sync

**⚡ Nouveau** : Serveur relay pour synchronisation P2P entre utilisateurs (Phase 2/11)

### Présentation

- **Serveur relay séparé** : Port 8888 (local) / 443 HTTPS (VPS futur)
- **Auth challenge/response** : Pas de login/password, signatures Ed25519
- **JWT tokens** : Expiration 24h, auto-refresh
- **Sync différentielle** : Timestamp-based, last-write-wins
- **Base de données relay** : `~/.bigboff/relay.db` (metadata uniquement)
- **Pas de chiffrement E2E** : Phase 2 = sync en clair (E2E sera Phase 10)

### Installation Phase 2

```bash
# 1. Installer dépendances
pip install -r requirements.txt

# 2. Initialiser relay DB
python src/relay_db_setup.py

# 3. Démarrer relay server (terminal 1)
python src/relay_server.py --port 8888

# 4. Enregistrer identité sur relay (terminal 2)
python src/sync.py register

# 5. Tester sync
python src/sync.py auth
python src/sync.py status
python src/sync.py pull
```

### CLI sync.py

```bash
# Enregistrer sur relay
python src/sync.py register

# Authentifier (obtenir JWT token)
python src/sync.py auth

# Afficher statut sync
python src/sync.py status

# Pull changements relay → local
python src/sync.py pull

# Push changements local → relay
python src/sync.py push
```

### API Relay (5 endpoints)

| Endpoint | Méthode | Auth | Description |
|----------|---------|------|-------------|
| `/api/auth/register` | POST | Non | Enregistrer identité (user_id, alias, public_keys) |
| `/api/auth/challenge` | POST | Non | Demander challenge aléatoire (60s expiration) |
| `/api/auth/verify` | POST | Non | Vérifier signature challenge → JWT token (24h) |
| `/api/sync/changes?since=<ts>` | GET | JWT | Récupérer changements depuis timestamp |
| `/api/sync/push` | POST | JWT | Pousser changements locaux |

**Authentification** : Challenge/response avec signature Ed25519, pas de login/password.

### Flow auth challenge/response

```
1. Client → POST /api/auth/challenge {"user_id": "bigboff_..."}
2. Relay → {"challenge_id": "abc123", "challenge": "base64...", "expires_in": 60}
3. Client signe challenge avec clé privée Ed25519
4. Client → POST /api/auth/verify {"challenge_id": "abc123", "signature": "base64..."}
5. Relay vérifie signature avec clé publique
6. Relay → {"success": true, "token": "JWT...", "expires_in": 86400}
7. Client utilise token pour sync : Header "Authorization: Bearer JWT..."
```

### Architecture Phase 2

```
┌───────────────────────────────────────┐
│  CLIENT LOCAL (server.py)             │
│  Port: 7777                           │
│  DB: ~/.bigboff/catalogue.db          │
│  - Indexation locale                  │
│  - Extension Chrome                   │
│  - Module sync.py (client relay)      │
└──────────────┬────────────────────────┘
               │ HTTP (local test)
               │ HTTPS (VPS futur)
               ↓
┌───────────────────────────────────────┐
│  RELAY SERVER (relay_server.py)       │
│  Port: 8888 (local) / 443 (VPS)       │
│  DB: ~/.bigboff/relay.db              │
│  - Auth challenge/response            │
│  - JWT tokens                         │
│  - Sync différentielle                │
│  - NE stocke PAS données users        │
└───────────────────────────────────────┘
```

### Tables relay.db

```sql
-- Registry identités
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    alias TEXT,
    public_key_rsa TEXT,
    public_key_ed25519 TEXT,
    registered_at TEXT,
    last_seen TEXT
);

-- Anti-replay (challenge unique)
CREATE TABLE challenges (
    challenge_id TEXT PRIMARY KEY,
    user_id TEXT,
    challenge TEXT,
    created_at TEXT,
    expires_at TEXT,
    used INTEGER DEFAULT 0
);

-- Changements différentiels
CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT,
    UNIQUE(user_id, entity_type, entity_id, timestamp)
);
```

### Fichier sync_state.json

```json
{
  "relay_url": "http://127.0.0.1:8888",
  "registered": true,
  "jwt_token": "eyJ...",
  "token_expires_at": 1739270400.0,
  "last_sync_timestamp": "2026-02-10T15:30:00"
}
```

### Sécurité Phase 2

- **JWT Secret** : Variable d'env `JWT_SECRET` (auto-généré si absent)
- **Challenge anti-replay** : Challenge utilisé 1 seule fois, expire après 60s
- **Token expiration** : JWT expire après 24h (re-auth nécessaire)
- **HTTPS obligatoire** en production (Let's Encrypt, Phase future)
- **Pas de chiffrement E2E** Phase 2 (données transitent en clair relay)

### Limitations Phase 2

- Sync unidirectionnel : Relay → Client uniquement (push vide)
- Last-write-wins : Conflits résolus par timestamp (CRDTs Phase future)

---

## Phase 3 P2P — Permissions + ACL

**⚡ Nouveau** : Système de permissions granulaires pour partage P2P (Phase 3/11)

### Présentation

- **Permissions granulaires** : Partage par tag, item ou all
- **2 modes de partage** : Consultation (temps réel, révocable) ou Partage (copie locale)
- **ACL côté relay** : Vérification permissions avant sync
- **Table permissions** : owner, target, scope, mode, granted_at, revoked_at
- **CLI complet** : grant, revoke, list, show

### CLI permissions.py

```bash
# Accorder accès au tag "notes" en consultation
python src/permissions.py grant bigboff_abc123 tag notes

# Accorder accès au tag "recettes" en mode partage (copie)
python src/permissions.py grant bigboff_abc123 tag recettes --mode partage

# Révoquer permission
python src/permissions.py revoke 42

# Lister permissions accordées par moi
python src/permissions.py list --as owner

# Lister permissions reçues
python src/permissions.py list --as target

# Afficher détails permission
python src/permissions.py show 42
```

### API Relay Phase 3 (3 nouveaux endpoints)

| Endpoint | Méthode | Auth | Description |
|----------|---------|------|-------------|
| `/api/permissions/grant` | POST | JWT | Accorder permission (target, scope, mode) |
| `/api/permissions/revoke` | POST | JWT | Révoquer permission (permission_id) |
| `/api/permissions/list?as=owner\|target` | GET | JWT | Lister permissions accordées ou reçues |

**Modification :** `/api/sync/changes` filtre maintenant par permissions ACL

### Modes de partage

**Mode CONSULTATION (lecture seule, révocable):**
```
A partage tag "notes" en consultation à B
→ B voit les éléments de A en temps réel
→ A peut révoquer instantanément
→ Si révoqué, B ne voit plus rien
```

**Mode PARTAGE (copie, persistent):**
```
A partage tag "recettes" en mode partage à B
→ B reçoit une copie des éléments
→ Sync continue tant que permission active
→ Si A révoque, B garde sa copie (snapshot figé)
```

### Table permissions

```sql
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_user_id TEXT NOT NULL,        -- Qui partage
    target_user_id TEXT,                 -- Avec qui (user individuel)
    target_group_id TEXT,                -- Ou groupe (Phase 7)
    scope_type TEXT NOT NULL,            -- 'tag', 'item', 'all'
    scope_value TEXT,                    -- Nom du tag ou item_id
    mode TEXT DEFAULT 'consultation',    -- 'consultation' ou 'partage'
    permissions TEXT DEFAULT '["read"]', -- ['read', 'write', 'delete']
    granted_at TEXT,
    revoked_at TEXT,                     -- Soft delete (NULL = active)
    UNIQUE(owner_user_id, target_user_id, scope_type, scope_value)
);
```

### Exemples d'utilisation

```bash
# Scénario 1 : Partager tag "notes" en consultation
python3 src/permissions.py grant bigboff_abc123 tag notes
# → User B peut voir les notes de A en temps réel

# User B pull changements
python3 src/sync.py pull
# → Reçoit uniquement changements autorisés (tag "notes")

# Révoquer accès
python3 src/permissions.py list --as owner  # Trouver permission_id
python3 src/permissions.py revoke 1
# → User B ne voit plus rien immédiatement

# Scénario 2 : Partager tag "recettes" en mode copie
python3 src/permissions.py grant bigboff_abc123 tag recettes --mode partage
# → User B reçoit copie locale des recettes
# → Si révoqué, User B garde sa copie
```

### Sécurité Phase 3

- **Vérification ACL** : Relay vérifie permissions avant chaque sync
- **Soft delete** : revoked_at timestamp (historique conservé)
- **Filtrage côté relay** : Client ne reçoit que changements autorisés
- **Pas d'UI encore** : Phase 3 = backend + CLI uniquement

### Limitations Phase 3

- Pas de groupes : 1-to-1 uniquement (groupes Phase 7)
- Pas d'UI web/extension : CLI uniquement (UI Phase future)
- Mode partage = copie simple (pas de marqueur "Partagé par" encore)

---

## Phase 4 P2P — QR Codes Partage

**⚡ Nouveau** : QR codes pour partage P2P sans saisir user_id (Phase 4/11)

### Présentation

- **Génération QR** : CLI + signature Ed25519, expiration 24h
- **Scan QR caméra** : html5-qrcode dans extension Chrome
- **Modal preview** : Accept/refuse partage avec détails
- **Endpoint local** : /api/share/accept intégré
- **Format QR** : JSON base64 (user_id, scope, mode, signature, timestamp)

### CLI qr_share.py

```bash
# Générer QR code pour partager tag "notes"
python src/qr_share.py generate tag notes

# Générer avec mode partage et sauvegarder PNG
python src/qr_share.py generate tag recettes --mode partage --output share.png

# Vérifier QR code
python src/qr_share.py verify --data <base64_data>
```

### Extension Chrome - Scan QR

1. Cliquer icône QR dans header extension
2. Autoriser accès caméra
3. Pointer vers QR code
4. Preview : "X partage 'Y' en mode Z"
5. Accept → Permission créée automatiquement
6. Refuse → Rien ne se passe

**Fichier test :** `extension/qr_scan_test.html`

### Format QR encodé

```json
{
  "version": "1.0",
  "type": "share_permission",
  "from_user_id": "bigboff_abc123",
  "from_alias": "Alice",
  "permission": {
    "scope_type": "tag",
    "scope_value": "notes",
    "mode": "consultation",
    "permissions": ["read"]
  },
  "created_at": "2026-02-11T00:00:00",
  "expires_at": "2026-02-12T00:00:00",
  "signature": "base64_ed25519_signature"
}
```

### Sécurité Phase 4

- **Signature Ed25519** : QR signé avec clé privée
- **Expiration 24h** : QR invalide après 24h
- **Vérification** : Signature vérifiée avant accept
- **Format JSON** : Base64 encode pour QR compact

### Limitations Phase 4

- **Pas de deep links** : bigboff:// custom protocol (Phase future)
- **Scan caméra seulement** : Pas d'upload image QR
- **Extension Chrome** : Pas encore PWA mobile (Phase 11)

---

## Phase 5 P2P — Mode Consultation

**⚡ Nouveau** : Consultation temps réel avec révocation instantanée (Phase 5/11)

**Fonctionnalités :**
- **Cache temporaire** : B voit données de A sans copie locale persistante
- **TTL 1h** : Snapshots expirés supprimés automatiquement du relay
- **Révocation instantanée** : A révoque → B perd accès immédiatement
- **Badge source** : UI affiche "📡 Partagé par bigboff_..."
- **Filtre source** : Local / Consultés / Tous

### Différence Consultation vs Partage

| Aspect | Consultation (Ph5) | Partage (Ph6) |
|--------|-------------------|---------------|
| **Copie locale** | Cache temporaire (TTL 1h) | Clone permanent |
| **Révocation** | Immédiate (cache invalidé) | Snapshot figé |
| **Sync** | À la demande | Continu |
| **Offline** | Nécessite connexion | Fonctionne offline |

### Usage consultation

```bash
# B consulte tag "notes" de A (interactif)
python3 src/sync.py consult bigboff_abc123 tag notes

# Avec recherche texte
python3 src/sync.py consult bigboff_abc123 tag notes "recette"

# A révoque permission
python3 src/permissions.py revoke bigboff_abc123 tag notes
```

**Extension Chrome :**
1. Ouvrir popup extension
2. Filtre "Source" → "Consultés uniquement"
3. Badge 📡 visible sur résultats partagés
4. Si révoqué → disparaît instantanément

### Architecture Phase 5

**Flow consultation :**
```
┌─────────────────────────┐
│  A (propriétaire)       │
│  Pousse snapshots relay │  ← TTL 1h
│  avec expires_at        │
└────────────┬────────────┘
             │ HTTP
             ↓
┌─────────────────────────┐
│  RELAY SERVER           │
│  - sync_log (TTL)       │  ← Cleanup auto
│  - Vérifie permissions  │
└────────────┬────────────┘
             │ HTTP
             ↓
┌─────────────────────────┐
│  B (consultation)       │
│  - Cache local temp     │  ← source_user_id="bigboff_..."
│  - Vérifie permission   │  ← À chaque accès
│  - Supprime si révoqué  │
└─────────────────────────┘
```

**Tables modifiées :**
- `relay.db/sync_log` : +expires_at (TTL)
- `catalogue.db/items` : +source_user_id (NULL=local, bigboff_...=consulté)
- `catalogue.db/contacts`, `lieux`, `events` : idem source_user_id

### Sécurité Phase 5

- **Vérification ACL** : Relay vérifie permission à chaque requête
- **TTL automatique** : Snapshots expirés supprimés (cleanup périodique)
- **Révocation passive** : B vérifie permission à chaque accès
- **Pas de copie persistante** : Cache local invalidé si révoqué

### Limitations Phase 5

- **Révocation passive** : Pas de notification push (vérification à la demande)
- **Nécessite connexion** : Pas de mode offline pour données consultées
- **TTL fixe 1h** : Pas configurable pour MVP
- **UI basique** : Badge simple, pas de modal consultation avancé

### Prochaines phases

- **Phase 6** : Mode partage (clone permanent, sync continue)
- **Phase 7** : Groupes (partage 1-to-many, roles admin/member)
- **Phase 10** : E2E encryption (chiffrer sync_log.data)
- **Phase 11** : Mobile PWA (scan QR mobile, même relay)

Voir `CAHIER_DES_CHARGES_SEARCH.md` pour roadmap complète.

---

## Phase 6 P2P — Mode Partage

**⚡ Nouveau** : Partage permanent avec sync continu (Phase 6/11)

**Fonctionnalités :**
- **Clone permanent** : B reçoit copie locale qui persiste après révocation
- **Sync continu** : Changements de A synchronisés automatiquement chez B
- **Snapshot figé** : Si A révoque, B garde snapshot au moment de la révocation
- **Badge vert** : UI affiche "📡 Partagé par bigboff_..." (vert vs bleu consultation)
- **Mode offline** : Clone local fonctionne sans connexion relay

### Différence Consultation vs Partage

| Aspect | Consultation (Ph5) | Partage (Ph6) |
|--------|-------------------|---------------|
| **Copie locale** | Cache temporaire (TTL 1h) | Clone permanent (is_shared_copy=1) |
| **Révocation** | Immédiate (cache invalidé) | Snapshot figé (garde données) |
| **Sync** | À la demande | Continu (polling 30s) |
| **Offline** | Nécessite connexion | Fonctionne offline |
| **Suppression** | Suit propriétaire | B garde copie |
| **Badge UI** | 📡 Bleu (#E3F2FD) | 📡 Vert (#C8E6C9) |

### Usage partage

```bash
# A génère QR de partage (mode partage)
python3 src/permissions.py grant bigboff_bob123 tag recettes --mode partage

# Ou via UI : Bouton "Partager" → Radio "Partage" → Générer QR

# B scanne QR et clone initial
python3 src/sync.py share clone bigboff_alice123 tag recettes

# B sync changements continus
python3 src/sync.py share sync

# A révoque permission
python3 src/permissions.py revoke bigboff_bob123 tag recettes
# → B garde snapshot figé (50 recettes conservées)
```

**Extension Chrome :**
1. Clic bouton "Partager" (📡) dans header
2. Sélectionner scope : Tag / Item / Tout
3. Radio "Partage" (clone permanent)
4. Générer QR → Affiche QR code
5. B scanne QR → Clone automatique
6. Badge vert "📡 Partagé par X" visible
7. Si révoqué → Badge reste, données conservées

### Architecture Phase 6

**Flow partage :**
```
┌─────────────────────────┐
│  A (propriétaire)       │
│  Pousse snapshots relay │  ← is_shared_copy=1
│  avec mode='partage'    │
└────────────┬────────────┘
             │ HTTP POST /api/share/clone
             ↓
┌─────────────────────────┐
│  RELAY SERVER           │
│  - sync_log permanent   │  ← Pas de TTL
│  - Vérifie permissions  │
│  - Filtre par mode      │
└────────────┬────────────┘
             │ HTTP GET /api/share/sync
             ↓
┌─────────────────────────┐
│  B (partage)            │
│  - Clone local          │  ← source_user_id + is_shared_copy=1
│  - Sync continu (30s)   │
│  - Garde si révoqué     │  ← Snapshot figé
└─────────────────────────┘
```

**Tables modifiées :**
- `relay.db/sync_log` : +is_shared_copy (0=consultation, 1=partage)
- `catalogue.db/items` : +is_shared_copy (0=local/consulté, 1=clone partage)
- API : `/api/share/clone`, `/api/share/sync`, `/api/share/revoke`

**Nouveaux endpoints relay :**
```python
POST /api/share/clone    # Clone initial avec is_shared_copy=1
GET  /api/share/sync     # Sync incrémental depuis timestamp
POST /api/share/revoke   # Révoque mais garde snapshot
POST /api/qr/generate    # Génère QR avec mode consultation/partage
```

### Sécurité Phase 6

- **Vérification ACL** : Relay vérifie permission mode='partage'
- **Clone permanent** : B garde données même après révocation
- **Snapshot figé** : Révocation stoppe sync mais garde état actuel
- **Pas de suppression propagée** : Si A supprime, B conserve copie

### Limitations Phase 6

- **Révocation passive** : Pas de notification push (vérification à la demande)
- **Sync polling** : 30s delay (pas WebSocket temps réel)
- **Pas de deux-sens** : B ne peut pas modifier et pousser à A
- **UI basique** : Modal simple, pas de gestion permissions avancée

### Tests Phase 6

```bash
# Exécuter tests automatisés
./test_phase6_share.sh

# Scénarios testés :
# ✅ Migration DB (is_shared_copy)
# ✅ Permission partage créée
# ✅ Clone initial (3 items, is_shared_copy=1)
# ✅ Sync modifications (A modifie → B reçoit MAJ)
# ✅ Révocation (B garde snapshot figé)
# ✅ Suppression (A supprime → B conserve copie)
```

### Prochaines phases

- **Phase 7** : Groupes (partage 1-to-many, roles admin/member)
- **Phase 8** : Multi-device activation (WhatsApp Web style)
- **Phase 9** : Freemium (limites relay gratuit vs payant)
- **Phase 10** : E2E encryption (chiffrer sync_log.data)

Voir `CAHIER_DES_CHARGES_SEARCH.md` pour roadmap complète.

---

## Phase 7 P2P — Groupes

**⚡ Nouveau** : Partage 1-to-many avec rôles admin/member (Phase 7/11)

**Fonctionnalités :**
- **Groupes** : Créer groupes avec nom et membres
- **Rôles** : Admin (peut inviter/kick) vs Member
- **Partage groupe** : Partager scope avec tout le groupe d'un coup
- **7 endpoints API** : create, invite, join, list, members, kick, leave

### Usage groupes

```bash
# Créer groupe
python3 src/groups.py create "Famille"
# → Retourne group_id: grp_abc123

# Inviter membre (admin uniquement)
python3 src/groups.py invite grp_abc123 bigboff_bob123

# Lister mes groupes
python3 src/groups.py list

# Lister membres
python3 src/groups.py members grp_abc123

# Expulser membre (admin uniquement)
python3 src/groups.py kick grp_abc123 bigboff_bob123

# Quitter groupe
python3 src/groups.py leave grp_abc123

# Partager avec groupe
python3 src/permissions.py grant --group grp_abc123 tag recettes
```

**Extension Chrome :**
1. Bouton "Groupes" (👥) dans header
2. Modal liste groupes + bouton "Créer"
3. Formulaire création groupe (nom)
4. UI basique MVP - APIs implémentées

### Architecture Phase 7

**Tables relay :**
- `groups` : (id, name, owner_user_id, created_at)
- `group_members` : (group_id, user_id, role, joined_at)

**Endpoints relay :**
```
POST   /api/groups/create   # Créer groupe
POST   /api/groups/invite   # Inviter membre (admin)
POST   /api/groups/join     # Rejoindre groupe
GET    /api/groups/list     # Lister mes groupes
GET    /api/groups/members  # Lister membres groupe
DELETE /api/groups/kick     # Expulser membre (admin)
DELETE /api/groups/leave    # Quitter groupe
```

### Tests Phase 7

```bash
./test_phase7_groups.sh
# ✅ Tables groups + group_members
# ✅ Créer groupe + ajouter membres
# ✅ Rôles admin vs member
# ✅ Kick membre
# ✅ Colonne target_group_id (permissions)
```

### Prochaines phases

- **Phase 8** : Multi-device activation (WhatsApp Web style)
- **Phase 9** : Freemium (limites gratuit vs payant)

Voir `CAHIER_DES_CHARGES_SEARCH.md` pour roadmap complète.

---

## Documentation complète

Voir `_SUIVI.md` pour :
- Fonctionnalités détaillées
- Architecture
- Historique complet
- Chiffres actuels

## Distribution

Pour installer sur une nouvelle machine :
1. Suivre "Installation rapide" ci-dessus
2. Voir `DISTRIBUTION_TODO.md` pour checklist complète P0-P3

## Dépendances

**Python (core) :**
- Aucune dépendance externe pour le serveur (stdlib uniquement)

**Python (fonctionnalités avancées) :**
- `beautifulsoup4` : Fetch métadonnées URL
- `requests` : HTTP client
- `Pillow` : Miniatures images
- `cryptography>=41.0.0` : Phase 1 P2P (RSA-4096, Ed25519, AES-256-GCM)

**Système :**
- macOS 10.15+ (ou Windows/Linux avec adaptations)
- Python 3.9+
- Chrome ou Edge
- ffmpeg (optionnel, pour miniatures vidéo)
