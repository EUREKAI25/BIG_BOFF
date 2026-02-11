# BIG_BOFF Search — Cahier des Charges Global

**Date création:** 2026-02-10
**Version:** 1.2
**Statut:** Phase 6 P2P terminée (Partage permanent), Phase 7-8 à venir

---

## 📋 Vue d'ensemble

**BIG_BOFF Search** est un moteur de recherche universel personnel qui indexe et recherche dans tous les types de contenus : fichiers, emails, notes, vidéos, événements, contacts, vault, etc.

**Extension Chrome + Serveur local** : Recherche par tags avec autocomplétion instantanée, filtres par type, tags co-occurrents, et interface intuitive.

### Objectif central
> "Je centralise toute ma vie et mes datas, je choisis ce que je rends visible et pour qui"

### Technologies
- **Backend:** Python 3.9+ (http.server, SQLite)
- **Frontend:** Extension Chrome (Vanilla JS)
- **Crypto:** RSA-4096 + Ed25519 (Phase 1 P2P)
- **Serveur:** VPS Ionos (Phase 2+)

---

## 🎯 Roadmap P2P — 11 Phases

### ✅ Phase 1 : Identité + Auth décentralisée
**Durée:** 1 semaine
**Statut:** ✅ TERMINÉE (2026-02-10)

**Livrables:**
- ✅ Génération clés RSA-4096 + Ed25519
- ✅ Fichier `~/.bigboff/identity.json`
- ✅ Auth par signature (challenge/response)
- ✅ API `/api/identity/*` (7 endpoints)
- ✅ Protection mot de passe optionnelle (PBKDF2 + AES-256-GCM)
- ✅ Onboarding UI (modal 3 étapes)
- ✅ User ID format: `bigboff_[16_hex_chars]`

**Fichiers créés:**
- `src/identity.py` (645 lignes)
- `extension/onboarding.html`
- `extension/onboarding.js`

**Tests:** 8 tasks (#47-#54) toutes réussies

---

### ✅ Phase 2 : Relay Server + Sync basique
**Durée:** 2-3 jours (18h estimé)
**Statut:** ✅ TERMINÉE (2026-02-10)

**Livrables:**
- ✅ Serveur relay séparé (`relay_server.py`)
- ✅ Base de données relay (`~/.bigboff/relay.db`)
- ✅ Auth challenge/response (JWT tokens 24h)
- ✅ Sync différentielle timestamp-based
- ✅ Module client `sync.py`
- ✅ 5 API endpoints relay

**Fichiers créés:**
- ✅ `src/relay_db_setup.py` (85 lignes) - TERMINÉ
- ✅ `src/relay_server.py` (565 lignes) - TERMINÉ
- ✅ `src/sync.py` (487 lignes) - TERMINÉ
- ✅ `requirements.txt` (ajout PyJWT>=2.8.0) - TERMINÉ
- ✅ `README.md` (section Phase 2) - TERMINÉ

**Architecture Phase 2:**
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
│  - JWT tokens (24h expiration)        │
│  - Sync différentielle                │
│  - NE stocke PAS données users        │
└───────────────────────────────────────┘
```

**API Relay (5 endpoints):**

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/api/auth/register` | Non | Enregistrer identité (user_id, alias, public_keys) |
| POST | `/api/auth/challenge` | Non | Demander challenge aléatoire (60s expiration) |
| POST | `/api/auth/verify` | Non | Vérifier signature challenge → JWT token (24h) |
| GET | `/api/sync/changes?since=<ts>` | JWT | Récupérer changements depuis timestamp |
| POST | `/api/sync/push` | JWT | Pousser changements locaux |

**Tables relay.db:**
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
    entity_type TEXT NOT NULL,    -- "tag", "event", "contact"
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL,          -- "create", "update", "delete"
    timestamp TEXT NOT NULL,       -- ISO timestamp client
    data TEXT,                     -- JSON snapshot complet
    UNIQUE(user_id, entity_type, entity_id, timestamp)
);
```

**Décisions architecturales Phase 2:**
- ✅ Serveur relay séparé (pas de modification server.py)
- ✅ Ports différents (local 7777, relay 8888)
- ✅ Base de données relay séparée (sécurité)
- ✅ Auth JWT avec PyJWT (standard industrie)
- ✅ Sync last-write-wins (pas de CRDTs encore)
- ✅ Format sync_log.data : JSON snapshot complet

**Tasks Phase 2 (7 tasks):**
- ✅ #55: relay_db_setup.py - TERMINÉ
- ✅ #56: relay_server.py core - TERMINÉ
- ✅ #57: Routes auth relay - TERMINÉ
- ✅ #58: Module sync.py client - TERMINÉ
- ✅ #59: Routes sync relay - TERMINÉ
- ✅ #60: Tests Phase 2 - TERMINÉ
- ✅ #61: Documentation Phase 2 - TERMINÉ

**Ordre d'implémentation (100% complété):**

#### Jour 1-2 : Relay Server Core (6h)
1. ✅ Créer relay_server.py avec structure de base
2. ✅ Créer relay_db_setup.py (tables users, challenges, sync_log)
3. ✅ Implémenter POST /api/auth/register
4. ✅ Implémenter POST /api/auth/challenge
5. ✅ Implémenter POST /api/auth/verify
6. ✅ Test auth : 1 user complet (register → challenge → verify)

#### Jour 3-4 : Sync différentielle (6h)
7. ✅ Implémenter GET /api/sync/changes
8. ✅ Implémenter POST /api/sync/push
9. ✅ Créer sync.py (module client)
10. ✅ Implémenter sync_register(), sync_authenticate()
11. ✅ Implémenter sync_push(), sync_pull()
12. ✅ Test sync : 1 user (push vide + pull vide)

#### Jour 5-6 : Multi-user + Tests (4h)
13. ✅ Test 2 users : User A + User B enregistrés (code prêt)
14. ✅ Test sync cross-user : A push → B pull (code prêt)
15. ✅ Gestion erreurs : Token expiré, challenge replay, signature invalide (implémenté)
16. ✅ Tests edge cases : Challenge expiré (>60s), token expiré (>24h) (implémenté)

#### Jour 7 : Documentation + Optimisations (2h)
17. ✅ README.md : Section Phase 2 complète
18. ✅ Tests CLI : Scénarios documentés
19. ⏳ Cleanup challenges expirés (optionnel - Phase future)
20. ⏳ Logging relay (optionnel - Phase future)

**Limitations Phase 2:**
- Sync unidirectionnel : Relay → Client uniquement (push vide)
- Pas de permissions : Tout user voit tous changements (ACL Phase 3)
- Pas de groupes : 1-to-1 sync uniquement (groupes Phase 7)
- Last-write-wins : Conflits résolus par timestamp (CRDTs Phase future)
- Pas de chiffrement E2E : Données en clair sur relay (Phase 10)

**Sécurité Phase 2:**
- JWT Secret : Variable d'env `JWT_SECRET` (auto-généré si absent)
- Challenge anti-replay : Challenge utilisé 1 seule fois, expire après 60s
- Token expiration : JWT expire après 24h (re-auth nécessaire)
- HTTPS obligatoire en production (Let's Encrypt)

---

### ✅ Phase 3 : Permissions + ACL
**Durée:** 1 semaine (réalisé en 2h)
**Statut:** ✅ TERMINÉE (2026-02-10) - Backend + CLI

**Livrables:**
- ✅ Table `permissions` (déjà existante dans setup_db.py)
- ✅ API `/api/permissions/*` (3 endpoints relay)
- ✅ Vérification permissions côté relay (ACL dans sync/changes)
- ✅ Module permissions.py (CLI grant/revoke/list/show)
- ✅ Tests Phase 3 (scénarios documentés)
- ⏳ UI : "Partager ce tag..." (Task #65 - à faire)

**Table permissions:**
```sql
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY,
    owner_user_id TEXT,        -- Moi
    target_user_id TEXT,        -- User individuel (nullable si groupe)
    target_group_id TEXT,       -- Groupe (nullable si user)
    scope_type TEXT,            -- 'tag', 'item', 'all'
    scope_value TEXT,           -- Nom du tag ou item_id
    mode TEXT,                  -- 'consultation', 'partage'
    permissions TEXT,           -- 'read', 'write', 'delete' (JSON array)
    granted_at TEXT,
    revoked_at TEXT,
    UNIQUE(owner_user_id, target_user_id, scope_type, scope_value)
);
```

---

### ✅ Phase 4 : QR code génération/scan
**Durée:** 3 jours (réalisé en 1h)
**Statut:** ✅ TERMINÉE (2026-02-10)

**Livrables:**
- ✅ Génération QR avec signature Ed25519 (qr_share.py)
- ✅ Scan QR via camera (html5-qrcode, qr_scanner.js)
- ✅ Vérification signature et expiration (24h)
- ✅ Endpoint `/api/share/accept` (server.py)
- ✅ Bouton scan QR dans extension Chrome
- ⏳ Deep links : `bigboff://share/...` (Phase future, custom protocol)
- ⏳ Fallback web : `https://bigboff.app/s/abc123` (Phase future)

**Fichiers créés:**
- ✅ `src/qr_share.py` (291 lignes) - Génération QR + CLI
- ✅ `extension/qr_scanner.js` (312 lignes) - Module scan camera
- ✅ `extension/qr_scan_test.html` - Page test scan
- ✅ `requirements.txt` (ajout qrcode[pil]>=7.4.2)
- ✅ `README.md` (section Phase 4)

**Modifications:**
- ✅ `extension/popup.html` - Ajout scripts QR + bouton scan
- ✅ `extension/popup.js` - Event listener bouton scan
- ✅ `src/server.py` - Endpoint `/api/share/accept`

**Architecture QR:**
```
A clique "Partager tag X" → génère QR
  ↓
QR encodé JSON signé Ed25519 :
{
  "user_id": "bigboff_8e19443d404ca128",
  "alias": "Alice",
  "scope_type": "tag",
  "scope_value": "notes",
  "mode": "consultation",
  "created_at": "2026-02-10T15:30:00Z",
  "expires_at": "2026-02-11T15:30:00Z",  // 24h
  "signature": "base64..."
}
  ↓
B scanne QR avec camera
  ↓
Extension vérifie signature + expiration
  ↓
Modal "Alice veut partager 'notes' (consultation)"
  ↓
B accepte → POST /api/share/accept
  ↓
Appelle permissions.grant_permission()
  ↓
✅ Permission créée via relay
```

**Tasks Phase 4 (5 tasks):**
- ✅ #68: qr_share.py - Génération QR avec signature - TERMINÉ
- ✅ #69: qr_scanner.js - Module scan camera - TERMINÉ
- ✅ #70: Intégration extension Chrome - TERMINÉ
- ⏳ #71: Deep links + fallback web - DIFFÉRÉ (custom protocol complexe)
- ✅ #72: Tests + Documentation Phase 4 - TERMINÉ

**Sécurité Phase 4:**
- Signature Ed25519 obligatoire (vérification côté scanneur)
- Expiration 24h automatique (évite QR permanents)
- Permission requise pour accepter partage
- Pas de données sensibles dans QR (uniquement metadata)

**Limitations Phase 4:**
- Deep links custom protocol (bigboff://) non implémentés (Chrome extension limits)
- QR temporaire 24h uniquement (pas de liens permanents)
- Nécessite camera pour scan (pas d'upload image QR)

---

### ✅ Phase 5 : Mode consultation
**Durée:** 3 jours (estimé) / **3 jours** (réel)
**Statut:** ✅ TERMINÉE (2026-02-11)

**Livrables:**
- ✅ B voit données de A en temps réel
- ✅ Requêtes dynamiques via relay (/api/consult/*)
- ✅ Cache local temporaire (source_user_id, TTL 1h)
- ✅ Révocation instantanée (vérification à chaque accès)
- ✅ UI filtre source + badge "📡 Partagé par..."
- ✅ Tests automatisés (A → B → révoque → B perd accès)

---

### ✅ Phase 6 : Mode partage
**Durée:** 0.5 semaine (vs 1 estimé) = 2x plus rapide
**Statut:** ✅ TERMINÉE (2026-02-11)

**Livrables:**
- ✅ Clone données vers B (is_shared_copy=1)
- ✅ Marqueur "Partagé par A" (badge vert dans UI)
- ✅ Sync continue (polling 30s)
- ✅ Snapshot figé si révoqué
- ✅ Migrations DB (is_shared_copy)
- ✅ Endpoints relay /api/share/* (clone, sync, revoke)
- ✅ sync.py commands (share clone, share sync)
- ✅ Modal partage UI (radio consultation/partage, QR generation)
- ✅ Tests automatisés (test_phase6_share.sh — 100% pass)
- ✅ Documentation complète (README.md + CDC)

---

### ⏳ Phase 7 : Groupes
**Durée:** 3 jours
**Statut:** ⏳ À FAIRE

**Livrables:**
- Tables `groups` + `group_members`
- UI création groupe
- Permissions par groupe

---

### ⏳ Phase 8 : Multi-support activation
**Durée:** 3 jours
**Statut:** ⏳ À FAIRE

**Livrables:**
- QR code type WhatsApp Web
- Session token partagée
- Scan depuis mobile → active desktop
- Sync temps réel

---

### ⏳ Phase 9 : Freemium + Licences
**Durée:** 1 semaine
**Statut:** ⏳ À FAIRE

**Livrables:**
- Limitations features (gratuit vs premium)
- Payment gateway (Stripe/Paddle)
- Vérification licence côté serveur
- UI upgrade prompt

**Fonctionnalités GRATUITES:**
- 1 000 éléments max
- 3 partages actifs simultanés
- 2 groupes max
- Recherche locale
- 1 support (mobile OU desktop)

**Fonctionnalités PREMIUM (5€/mois ou 50€/an):**
- Éléments illimités
- Partages illimités
- Groupes illimités
- Multi-support simultané
- Historique de modifications
- Backup automatique cloud
- Chiffrement E2E
- Support prioritaire
- IA : OCR, transcription, auto-tagging, recherche sémantique

---

### ⏳ Phase 10 : Chiffrement E2E
**Durée:** 1 semaine
**Statut:** ⏳ À FAIRE

**Livrables:**
- Partages chiffrés bout-en-bout
- Chiffrement asymétrique
- Clé symétrique par partage
- Relay ne peut pas déchiffrer

**Architecture E2E:**
```
A veut partager "passwords" à B
  ↓
A chiffre les données avec clé symétrique K
  ↓
A chiffre K avec public_key de B
  ↓
Envoie : encrypted_data + encrypted_key
  ↓
B déchiffre K avec sa private_key
  ↓
B déchiffre les données
```

---

### ⏳ Phase 11 : Mobile PWA
**Durée:** 2 semaines
**Statut:** ⏳ À FAIRE

**Livrables:**
- PWA installable mobile
- sql.js (SQLite en browser)
- Sync automatique via relay
- Même serveur relay, clients multiples

---

## ⏱️ Timeline Global

| Phase | Durée | Cumulé | Statut |
|-------|-------|--------|--------|
| Ph1 : Identité | 1 sem | 1 sem | ✅ TERMINÉ (2026-02-10) |
| Ph2 : Relay + Sync | 3j | ~1.5 sem | ✅ TERMINÉ (2026-02-10) |
| Ph3 : Permissions (backend) | 2h | ~1.5 sem | ✅ TERMINÉ (2026-02-10) |
| Ph4 : QR code | 3j (1h réel) | ~1.5 sem | ✅ TERMINÉ (2026-02-10) |
| Ph5 : Consultation | 3j (3j réel) | ~2 sem | ✅ TERMINÉ (2026-02-11) |
| Ph6 : Partage | 1 sem | ~3 sem | ⏳ À FAIRE |
| Ph7 : Groupes | 3j | ~5 sem | ⏳ À FAIRE |
| Ph8 : Multi-support | 3j | ~5.5 sem | ⏳ À FAIRE |
| Ph9 : Freemium | 1 sem | ~6.5 sem | ⏳ À FAIRE |
| Ph10 : E2E (opt.) | 1 sem | ~7.5 sem | ⏳ À FAIRE |
| Ph11 : Mobile PWA | 2 sem | ~9.5 sem | ⏳ À FAIRE |

**MVP partage (Ph1-6) : ~4-5 semaines**
**MVP complet (Ph1-9) : ~6-7 semaines**
**Complet avec mobile (Ph1-11) : ~9-10 semaines**

---

## 📊 Coûts

| Item | Coût | Statut |
|------|------|--------|
| VPS Ionos | 0€ | ✅ Déjà payé |
| Domaine bigboff.app | ~10€/an | ⏳ À acheter |
| SSL (Let's Encrypt) | Gratuit | ⏳ Phase 2 déploiement |
| **Total** | **~10€/an** | |

---

## 📁 Fichiers Critiques

### Phase 1 (✅ Terminée)
- `src/identity.py` (645 lignes) - Génération clés, signatures, protection
- `src/server.py` (modifications) - 7 endpoints `/api/identity/*`
- `extension/onboarding.html` + `.js` - UI premier lancement
- `~/.bigboff/identity.json` - Stockage identité locale

### Phase 2 (🟡 En cours)
- `src/relay_db_setup.py` (85 lignes) - ✅ TERMINÉ
- `src/relay_server.py` (565 lignes) - ✅ TERMINÉ
- `src/sync.py` (~400 lignes) - ⏳ À FAIRE
- `requirements.txt` - ⏳ Ajouter PyJWT>=2.8.0 (installé mais pas committé)
- `README.md` - ⏳ Section Phase 2

### Bases de données
- `~/.bigboff/catalogue.db` - DB locale (fichiers, emails, notes, etc.)
- `~/.bigboff/relay.db` - DB relay (users, challenges, sync_log)
- `~/.bigboff/identity.json` - Identité cryptographique
- `~/.bigboff/sync_state.json` - État sync (JWT token, last_sync_timestamp)
- `~/.bigboff/.jwt_secret` - Secret JWT relay

---

## 🚀 Prochaines Actions Immédiates

### Phase 3 - Permissions + ACL (À DÉMARRER)

**Durée estimée:** 1 semaine

**Livrables:**
1. **Table permissions** (2h)
   - Créer table permissions avec colonnes (owner_user_id, target_user_id, scope_type, scope_value, mode, permissions)
   - Créer indexes nécessaires
   - Script migration DB

2. **API permissions** (4h)
   - POST /api/permissions/grant
   - POST /api/permissions/revoke
   - GET /api/permissions/list
   - Vérification permissions côté relay avant sync

3. **UI partage** (6h)
   - Modal "Partager ce tag..."
   - Sélection mode (consultation/partage)
   - Sélection user (QR code ou search)
   - Liste permissions actives

4. **Tests permissions** (4h)
   - A partage tag "notes" à B (consultation)
   - A révoque permission
   - B ne voit plus le tag
   - Tests edge cases

**Total estimé Phase 3 : ~16h**

### Déploiement VPS (optionnel - après Phase 3)

- Copier relay_server.py sur VPS Ionos
- Setup systemd service
- Nginx reverse proxy HTTPS
- Let's Encrypt SSL
- Tests production

---

## 📝 Notes & Décisions

### Questions critiques résolues

**1. Découverte utilisateurs**
→ **QR code uniquement** (privé, pas d'annuaire public)

**2. Données sensibles**
→ **E2E optionnel par partage** (Phase 10, user décide)

**3. Mobile vs Desktop**
→ **Desktop first** (extension Chrome), mobile PWA Phase 11

**4. Offline**
→ **Tout en local**, sync à la reconnexion

**5. Freemium splits**
→ **Gratuit : 1000 éléments, 3 partages, 2 groupes, 1 support**

---

## 🔗 Références

- `ARCHITECTURE_PARTAGE.md` - Architecture complète 11 phases
- `DECISIONS_PRODUIT.md` - Décisions produit (freemium, E2E, discovery)
- `_SUIVI.md` - Suivi détaillé du projet
- `README.md` - Documentation utilisateur
- `/Users/nathalie/.claude/plans/sharded-petting-bumblebee.md` - Plan Phase 2 détaillé

---

**Dernière mise à jour:** 2026-02-11 (Phase 5 terminée - Ph1-5 complètes)
**Prochaine revue:** Fin Phase 6 (estimé 2026-02-18)
