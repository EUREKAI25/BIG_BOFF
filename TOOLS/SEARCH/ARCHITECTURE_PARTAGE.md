# BIG_BOFF Search — Architecture Partage P2P

## Vision produit

### Modèle de distribution virale
- ✅ Pas de marketing, transmission organique
- ✅ QR code / SMS / Partage de données
- ✅ Installation = accès fonctionnalités gratuites de base
- ✅ Freemium : abonnement pour fonctionnalités avancées

### Concept central
> "Je centralise toute ma vie et mes datas, je choisis ce que je rends visible et pour qui"

**Exemples use cases :**
- Ma mère peut consulter mes notes
- Le groupe "collègues" peut accéder à mes éléments tagués "travail"
- Je partage un document ponctuel à quelqu'un

---

## 🔑 Concepts clés

### 1. Identité décentralisée (pas de login/pwd)
**Chaque utilisateur = paire de clés cryptographiques**
```
User ID = hash(public_key)  # ex: "bigboff_a7f3c2..."
```

**Fichier local `~/.bigboff/identity.json` :**
```json
{
  "user_id": "bigboff_a7f3c2e1d9...",
  "public_key": "-----BEGIN PUBLIC KEY-----...",
  "private_key_encrypted": "...",  // Chiffré par mot de passe optionnel
  "alias": "Nathalie",
  "created_at": "2026-02-10"
}
```

**Pas d'auth traditionnelle :**
- Pas de serveur qui stocke users/passwords
- Optionnel : mot de passe local pour déverrouiller private_key

### 2. Modes de partage

#### Mode CONSULTATION (lecture seule, révocable)
```
A partage tag "notes" en consultation à B
→ B voit les éléments de A en temps réel
→ A peut révoquer instantanément
→ Si révoqué, B ne voit plus rien
```

**Implémentation :**
- B a juste un "lien" vers les données de A
- Requête à chaque accès : "A, donne-moi tes notes"
- A vérifie permissions avant de répondre

#### Mode PARTAGE (copie, persistent)
```
A partage tag "recettes" en mode partage à B
→ B reçoit une copie des éléments
→ Sync continue tant que permission active
→ Si A révoque, B garde sa copie (snapshot figé)
```

**Implémentation :**
- Clone des données dans la base de B
- Marqué comme "partagé par A"
- Sync différentielle (CRDTs ou timestamp-based)

### 3. Permissions granulaires (ACL)

**Table `permissions` :**
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

**Exemples :**
```json
// Ma mère peut consulter mes notes
{
  "owner_user_id": "bigboff_nathalie",
  "target_user_id": "bigboff_maman",
  "scope_type": "tag",
  "scope_value": "notes",
  "mode": "consultation",
  "permissions": ["read"]
}

// Groupe collègues peut accéder à mes éléments "travail"
{
  "owner_user_id": "bigboff_nathalie",
  "target_group_id": "group_collegues",
  "scope_type": "tag",
  "scope_value": "travail",
  "mode": "partage",
  "permissions": ["read"]
}
```

### 4. Groupes

**Table `groups` :**
```sql
CREATE TABLE groups (
    id TEXT PRIMARY KEY,        -- 'group_famille', 'group_collegues'
    name TEXT,
    owner_user_id TEXT,
    created_at TEXT
);

CREATE TABLE group_members (
    group_id TEXT,
    user_id TEXT,
    role TEXT,                  -- 'admin', 'member'
    joined_at TEXT,
    UNIQUE(group_id, user_id)
);
```

---

## 📱 Flux utilisateur

### Flux 1 : Partager l'outil (onboarding viral)

```
A génère QR code "Installer BIG_BOFF"
  ↓
B scanne QR code
  ↓
Redirigé vers https://bigboff.app/install?ref=a7f3c2
  ↓
PWA installée sur mobile/desktop de B
  ↓
Génération auto de l'identité de B (clés pub/priv)
  ↓
B a accès aux fonctionnalités gratuites
```

**QR code encode :**
```
https://bigboff.app/install?ref=bigboff_a7f3c2&name=Nathalie
```

### Flux 2 : Partager des données (tag)

```
A dans son app : "Partager" → Sélectionne tag "recettes"
  ↓
A choisit : Mode consultation ou partage
  ↓
A génère QR code ou lien SMS
  ↓
B scanne/clique
  ↓
B voit preview : "Nathalie partage 'recettes' (23 éléments)"
  ↓
B accepte ou refuse
  ↓
Si accepté :
  - Mode consultation : B voit en temps réel
  - Mode partage : Clone vers base de B
```

**QR code encode (partage tag) :**
```json
{
  "type": "share_tag",
  "from_user_id": "bigboff_a7f3c2",
  "from_name": "Nathalie",
  "tag": "recettes",
  "mode": "partage",
  "signature": "..." // Signé par private_key de A
}
```

### Flux 3 : Partager un élément ponctuel

```
A clic-droit sur un fichier : "Partager cet élément"
  ↓
QR code ou lien généré
  ↓
B scanne
  ↓
B voit l'élément + peut télécharger/sauvegarder
```

### Flux 4 : Activer multi-support (type WhatsApp Web)

```
A sur mobile : Déjà installé et connecté
  ↓
A ouvre extension Chrome sur desktop : "Se connecter"
  ↓
Extension affiche QR code
  ↓
A scanne avec mobile
  ↓
QR code encode session_token
  ↓
Extension desktop maintenant connectée au même user_id
  ↓
Sync automatique via serveur relay
```

---

## 🏗️ Architecture technique

### Option recommandée : Hybride (serveur relay + local)

```
┌──────────────────┐
│  User A (mobile) │  SQLite local + clés
└────────┬─────────┘
         │ HTTPS API
         ↓
┌──────────────────┐
│  Relay Server    │  Gère permissions + sync
│  (VPS Ionos)     │  Ne stocke PAS les données
└────────┬─────────┘
         │ HTTPS API
         ↓
┌──────────────────┐
│  User B (desktop)│  SQLite local + clés
└──────────────────┘
```

**Serveur relay (VPS Ionos) :**
- Gère les permissions (qui peut voir quoi)
- Relay messages entre users
- Sync différentielle
- **Ne stocke PAS les données utilisateur** (juste métadonnées)

**Données locales (desktop/mobile) :**
- SQLite complète de l'utilisateur
- Chiffrement E2E pour partages sensibles

### API Relay (nouvelles routes)

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | Créer identité (envoie public_key) |
| `POST /api/auth/challenge` | Auth par signature (pas de password) |
| `GET /api/user/profile` | Profil public d'un user |
| `POST /api/share/tag` | Partager un tag |
| `POST /api/share/item` | Partager un élément |
| `POST /api/share/accept` | Accepter un partage |
| `POST /api/share/revoke` | Révoquer un partage |
| `GET /api/sync/changes` | Récupérer changements depuis timestamp |
| `POST /api/sync/push` | Pousser changements locaux |
| `GET /api/permissions/list` | Mes permissions accordées |
| `POST /api/group/create` | Créer un groupe |
| `POST /api/group/invite` | Inviter dans groupe |

### Chiffrement E2E (optionnel, pour données sensibles)

**Partage chiffré :**
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

**Relay ne peut PAS lire** (E2E).

---

## 💰 Modèle Freemium

### Fonctionnalités GRATUITES (de base)
- ✅ 1 000 éléments max
- ✅ 3 partages actifs simultanés
- ✅ 2 groupes max
- ✅ Recherche locale
- ✅ 1 support (mobile OU desktop)

### Fonctionnalités PREMIUM (abonnement 5€/mois ou 50€/an)
- ✅ Éléments illimités
- ✅ Partages illimités
- ✅ Groupes illimités
- ✅ Multi-support simultané (mobile + desktop + extension)
- ✅ Historique de modifications
- ✅ Backup automatique cloud
- ✅ Chiffrement E2E
- ✅ Support prioritaire
- ✅ Fonctionnalités avancées :
  - OCR automatique sur images
  - Transcription audio
  - IA pour auto-tagging
  - Recherche sémantique

**Vérification licence :**
- Token de licence stocké dans identity.json
- Vérification serveur à chaque sync
- Mode dégradé si expirée (lecture seule)

---

## 🎯 Phases d'implémentation

### Phase 1 : Identité + Auth décentralisée (1 semaine)
**Livrable :** Système clés pub/priv, pas de login/pwd
- [x] Génération clés à l'install
- [x] Table `identity` locale
- [x] Auth par signature (challenge/response)
- [x] API `/api/auth/*`

### Phase 2 : Relay server + Sync basique (1 semaine)
**Livrable :** Serveur relay sur VPS Ionos, sync 2 users
- [x] Deploy serveur Python sur Ionos
- [x] API `/api/sync/*`
- [x] Table `sync_log` (track changements)
- [x] Sync différentielle timestamp-based

### Phase 3 : Permissions + ACL (1 semaine)
**Livrable :** Système de permissions par tag
- [x] Table `permissions`
- [x] API `/api/permissions/*`
- [x] Vérification permissions côté serveur
- [x] UI : "Partager ce tag..."

### Phase 4 : QR code génération/scan (3 jours)
**Livrable :** Partage par QR code
- [x] Génération QR (qrcode.js)
- [x] Scan QR (jsQR ou WebRTC camera)
- [x] Deep links : `bigboff://share/...`
- [x] Fallback web : `https://bigboff.app/s/abc123`

### Phase 5 : Mode consultation (3 jours)
**Livrable :** B voit données de A en temps réel
- [x] Requêtes dynamiques via relay
- [x] Cache local temporaire
- [x] Révocation instantanée

### Phase 6 : Mode partage (1 semaine)
**Livrable :** Clone données vers B
- [x] Copy sur acceptation
- [x] Marqueur "Partagé par A"
- [x] Sync continue
- [x] Snapshot figé si révoqué

### Phase 7 : Groupes (3 jours)
**Livrable :** Créer groupes, inviter membres
- [x] Tables `groups` + `group_members`
- [x] UI création groupe
- [x] Permissions par groupe

### Phase 8 : Multi-support activation (3 jours)
**Livrable :** QR code type WhatsApp Web
- [x] Session token partagée
- [x] Scan depuis mobile → active desktop
- [x] Sync temps réel

### Phase 9 : Freemium + Licences (1 semaine)
**Livrable :** Système d'abonnement
- [x] Limitations features (gratuit vs premium)
- [x] Payment gateway (Stripe/Paddle)
- [x] Vérification licence côté serveur
- [x] UI upgrade prompt

### Phase 10 : Chiffrement E2E (optionnel, 1 semaine)
**Livrable :** Partages chiffrés bout-en-bout
- [x] Chiffrement asymétrique
- [x] Clé symétrique par partage
- [x] Relay ne peut pas déchiffrer

---

## ⏱️ Timeline total

| Phase | Durée | Cumulé |
|-------|-------|--------|
| Ph1 : Identité | 1 sem | 1 sem |
| Ph2 : Relay + Sync | 1 sem | 2 sem |
| Ph3 : Permissions | 1 sem | 3 sem |
| Ph4 : QR code | 3j | ~4 sem |
| Ph5 : Consultation | 3j | ~4.5 sem |
| Ph6 : Partage | 1 sem | ~5.5 sem |
| Ph7 : Groupes | 3j | ~6 sem |
| Ph8 : Multi-support | 3j | ~6.5 sem |
| Ph9 : Freemium | 1 sem | ~7.5 sem |
| Ph10 : E2E (opt.) | 1 sem | ~8.5 sem |

**MVP partage (Ph1-6) : ~5-6 semaines**
**MVP complet (Ph1-9) : ~7-8 semaines**

---

## 💻 Technologies

### Frontend (PWA)
- Vanilla JS (actuel) ou Vue.js/React (si refonte UI)
- sql.js (SQLite en browser)
- qrcode.js (génération QR)
- jsQR (scan QR via caméra)

### Backend (Relay Server)
- Python 3.9+ (actuel)
- Flask ou FastAPI (plus moderne)
- SQLite (métadonnées relay)
- nginx + HTTPS

### Crypto
- `crypto` module natif Python/JS
- libsodium (crypto moderne) ou Web Crypto API

### Serveur
- VPS Ionos (déjà payé) ✅
- Domaine : bigboff.app (~10€/an)

---

## 📊 Coûts

| Item | Coût |
|------|------|
| VPS Ionos | 0€ (déjà payé) |
| Domaine bigboff.app | ~10€/an |
| SSL (Let's Encrypt) | Gratuit |
| **Total** | **~10€/an** |

---

## ❓ Questions critiques à clarifier

### 1. Découverte utilisateurs
**Question :** Comment A trouve B pour le première fois ?
- Option 1 : QR code uniquement (privé)
- Option 2 : Annuaire public optionnel (chercher par alias)
- Option 3 : Invitation par lien unique

### 2. Données sensibles
**Question :** Chiffrement E2E obligatoire ou optionnel ?
- Option 1 : Tout chiffré (max sécurité, complexe)
- Option 2 : Optionnel par partage (user décide)
- Option 3 : Pas de chiffrement (relay peut voir)

### 3. Mobile vs Desktop
**Question :** Quel support prioriser ?
- Option 1 : Mobile first (PWA)
- Option 2 : Desktop first (extension Chrome)
- Option 3 : Les 2 simultanément

### 4. Offline
**Question :** Les données doivent être accessibles offline ?
- Option 1 : Tout en local, sync à la reconnexion
- Option 2 : Nécessite connexion

### 5. Stockage mobile
**Question :** Que récupère-t-on depuis le mobile ?
- Photos/vidéos de la galerie
- Contacts du téléphone
- Calendrier
- Localisation (checkins)
- SMS/iMessage (macOS/iOS uniquement)
- Emails (via IMAP comme desktop)
- Notes natives

### 6. Freemium splits
**Question :** Où placer le curseur gratuit/premium ?
- Combien d'éléments max gratuit ? (1000 ? 5000 ?)
- Combien de partages simultanés gratuit ? (3 ? 5 ?)
- Fonctionnalités premium exactes ?

---

## 🚀 Prochaine étape

**Pour démarrer Phase 1 (Identité décentralisée) :**
1. Créer module `identity.py` (génération clés)
2. Créer endpoint `/api/auth/register`
3. Modifier `setup_db.py` pour tables identity/permissions
4. UI : Écran premier lancement (génération identité)

**Voulez-vous qu'on commence Phase 1 maintenant ?**
