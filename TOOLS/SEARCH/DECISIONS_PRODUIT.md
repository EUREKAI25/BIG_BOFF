# BIG_BOFF Search — Décisions Produit

## Date : 2026-02-10
## Décisions actées pour le pivot "Partage P2P"

---

## 1. Données indexées (Mobile)

### ✅ TOUT récupérer automatiquement
- Photos/vidéos galerie
- Contacts téléphone
- Calendrier natif
- Géolocalisation (checkins)
- SMS/iMessage (iOS)
- Emails (IMAP multi-comptes)
- Notes natives
- Fichiers cloud (Dropbox, iCloud Drive)
- Historique navigation (optionnel, consentement)
- Musique/podcasts métadonnées

**Permissions requises :**
- iOS : Photos, Contacts, Calendrier, Localisation, Messages
- Android : idem
- Demande à l'install, activation module par module

---

## 2. Chiffrement E2E

### ✅ OBLIGATOIRE sur tous les partages

**Workflow transparent :**
```
User A partage à User B
  ↓
1. App génère clé symétrique K (AES-256)
2. App chiffre données avec K
3. App chiffre K avec public_key de B (RSA-4096)
4. Envoie : encrypted_data + encrypted_K
  ↓
Relay transmet (ne peut PAS déchiffrer)
  ↓
App B déchiffre K avec private_key de B
App B déchiffre données avec K
  ↓
User B voit données en clair
```

**User ne voit RIEN de tout ça** = Expérience fluide

**Sécurité :**
- Clés RSA-4096 (génération 1x à l'install)
- AES-256-GCM pour données
- Signature numérique (vérification identité)
- Relay server ne peut JAMAIS déchiffrer

**Impact utilisateur :**
- Install : +2 secondes (génération clés)
- Partage : +0 seconde visible (chiffrement en arrière-plan)
- Optionnel : Mot de passe pour protéger clé privée locale

**Impact dev :**
- +2-3 jours (Phase 10)
- Librairies : libsodium (Python) + Web Crypto API (JS)

---

## 3. Découverte utilisateurs

### ✅ QR code ou SMS uniquement (pas d'annuaire)

**QR code :**
```
A génère QR → B scanne → Partage établi
```

**SMS :**
```
A envoie SMS avec lien
  ↓
https://bigboff.app/i/{token}
  ↓
Token = UUID unique, durée limitée (config : 24h-7j)
  ↓
B clique, install app, token vérifié
  ↓
Permission établie automatiquement
```

**Config globale (admin) :**
```json
{
  "invite_token_duration_hours": 48,
  "max_invites_per_user": 100
}
```

**Pas d'annuaire public** = Confidentialité maximale

---

## 4. Modèle Freemium

### ✅ Basé sur FONCTIONNALITÉS, pas volume

**GRATUIT (illimité) :**
- ✅ Éléments illimités (pas de limite stockage)
- ✅ Partages illimités
- ✅ Groupes illimités
- ✅ Recherche par tags
- ✅ Vues : Liste, Planning, Budget
- ✅ 1 support simultané (mobile OU desktop)
- ✅ Sync basique

**PREMIUM (5€/mois ou 50€/an) :**
- ✅ Multi-support (mobile + desktop + extension simultanés)
- ✅ Vues avancées : Kanban, Timeline, Map, Graph, Gallery, Stats
- ✅ Widgets personnalisables
- ✅ Backup automatique cloud
- ✅ Historique illimité (vs 30j gratuit)
- ✅ Fonctionnalités IA :
  - OCR automatique (photos → texte searchable)
  - Transcription audio/vidéo
  - Auto-tagging intelligent
  - Recherche sémantique (similitude)
  - Résumés automatiques
- ✅ Export avancé (PDF, JSON, CSV)
- ✅ API développeur
- ✅ Thèmes personnalisés
- ✅ Support prioritaire

**Pourquoi pas de limite volume ?**

**Calcul coûts serveur (10,000 users actifs) :**
```
Relay stocke UNIQUEMENT métadonnées (pas les données) :
- Users registry : 10,000 × 1 KB = 10 MB
- Permissions ACL : 10,000 × 10 partages × 1 KB = 100 MB
- Sync log (30j) : 10,000 × 100 changes/j × 100 bytes × 30j = 3 GB
Total stockage : ~3.2 GB

Bande passante (sync différentielle + compression) :
- 10,000 users × 10 MB/mois = 100 GB/mois
- VPS Ionos : généralement illimité ou 1-10 TB/mois inclus

Coût VPS (100k users) :
- CPU/RAM : VPS €20/mois suffit (relay léger)
- Stockage : €5/mois (100 GB SSD)
Total : €25/mois pour 100,000 users
```

**Revenus potentiels (10% conversion premium) :**
```
10,000 users × 10% premium × 5€/mois = 5,000€/mois
Coût serveur : €25/mois
Marge : 99.5% 🚀
```

→ **Volume n'est PAS un problème économique**
→ **Données stockées localement** (chez users)
→ **Serveur = simple relay** (léger)

---

## 5. Support & Design

### ✅ Mobile first, optimisé pour tout

**Priorités :**
1. **PWA mobile** (installable iOS/Android)
2. **Desktop responsive** (même code)
3. **Extension Chrome** (bonus)

**Design system :**
- Sobre, minimaliste, rapide
- Palette : Noir/blanc + 1 accent (personnalisable)
- Typography : System fonts (SF Pro iOS, Roboto Android)
- Spacing : Grille 8px
- Animations : Subtiles, 200-300ms
- Accessibilité : WCAG 2.1 AA

---

## 6. Vues par défaut

### Core (gratuit)
1. **Liste** - Recherche actuelle (tags)
2. **Planning** - Calendrier (événements, deadlines)
3. **Budget** - Finances (dépenses, revenus, catégories)

### Premium
4. **Kanban** - Projets/tâches (colonnes drag & drop)
5. **Timeline** - Chronologie horizontale (axe temps)
6. **Map** - Carte géo (lieux, checkins, photos localisées)
7. **Graph** - Réseau de relations (contacts ↔ projets ↔ lieux)
8. **Gallery** - Grille photos/vidéos (type Instagram)
9. **Stats** - Dashboard métriques (compteurs, graphiques)
10. **Inbox** - Non triés (nouveaux éléments à organiser)
11. **Archive** - Condensé temporel (années → mois → jours)

**Autres vues possibles :**
- **Habits** - Tracker habitudes (type Streaks)
- **Journal** - Chronologie personnelle (type Day One)
- **Contacts CRM** - Relations enrichies (notes, historique)
- **Recettes** - Cuisine (ingrédients, instructions, photos)
- **Bibliothèque** - Livres/films/séries (ratings, notes)
- **Santé** - Poids, sport, sommeil (si intégration HealthKit)

### Système de vues personnalisables

**Table `user_views` :**
```sql
CREATE TABLE user_views (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    name TEXT,
    type TEXT,              -- 'list', 'kanban', 'calendar', 'map', etc.
    config TEXT,            -- JSON : filtres, colonnes, widgets
    layout TEXT,            -- JSON : positions, tailles
    is_default INTEGER,
    created_at TEXT
);
```

**Exemple config vue Kanban :**
```json
{
  "columns": [
    {"id": "todo", "title": "À faire", "filter": {"tag": "todo"}},
    {"id": "doing", "title": "En cours", "filter": {"tag": "doing"}},
    {"id": "done", "title": "Fait", "filter": {"tag": "done"}}
  ],
  "card_fields": ["title", "date", "tags"],
  "sort": "date_desc"
}
```

**UI création vue :**
```
Bouton "+" → "Nouvelle vue"
  ↓
Choisir type : Liste / Kanban / Map / Timeline / ...
  ↓
Configurer : Filtres, affichage, widgets
  ↓
Sauvegarder
  ↓
Accessible depuis menu latéral
```

---

## 7. Personnalisation

### Niveaux de personnalisation

**Niveau 1 : Thèmes (gratuit)**
- Couleur accent
- Mode sombre/clair
- Taille police

**Niveau 2 : Layouts (premium)**
- Positions widgets
- Tailles colonnes
- Raccourcis clavier custom

**Niveau 3 : Vues custom (premium)**
- Créer vues illimitées
- Filtres avancés
- Scripts custom (safe sandboxed JS)

**Niveau 4 : Plugins (premium + dev)**
- API pour développeurs
- Intégrations tierces (Zapier, IFTTT)
- Webhooks

---

## 8. Timeline révisée

### MVP Partage P2P (8 semaines)

| Phase | Durée | Détails |
|-------|-------|---------|
| **Ph1 : Identité** | 1 sem | Clés pub/priv, auth décentralisée |
| **Ph2 : Relay** | 1 sem | Serveur Ionos, sync basique |
| **Ph3 : Permissions** | 1 sem | ACL par tag/élément/groupe |
| **Ph4 : QR + SMS** | 3j | QR code scan, liens token temporaire |
| **Ph5 : Consultation** | 3j | Voir données temps réel |
| **Ph6 : Partage** | 1 sem | Clone + sync continue |
| **Ph7 : Groupes** | 3j | Créer/gérer groupes |
| **Ph8 : Multi-support** | 3j | QR activation type WhatsApp Web |
| **Ph9 : Freemium** | 1 sem | Licences, paiement Stripe |
| **Ph10 : E2E** | 3j | Chiffrement obligatoire (libsodium) |
| **Ph11 : Mobile UI** | 1 sem | Responsive, gestes tactiles, PWA |
| **Ph12 : Vues premium** | 1 sem | Kanban, Timeline, Map, Graph |

**Total : ~10 semaines (2.5 mois)**

### Post-MVP (fonctionnalités avancées)

| Feature | Durée | Premium ? |
|---------|-------|-----------|
| OCR automatique | 1 sem | ✅ |
| Transcription audio | 1 sem | ✅ |
| Auto-tagging IA | 2 sem | ✅ |
| Recherche sémantique | 1 sem | ✅ |
| Widgets personnalisables | 1 sem | ✅ |
| API développeur | 1 sem | ✅ |
| Backup cloud automatique | 3j | ✅ |
| Export avancé | 3j | ✅ |

---

## 9. Prochaines actions

### Immédiat (aujourd'hui)
- [x] Documenter décisions produit ✅
- [ ] Mettre à jour `_SUIVI.md`
- [ ] Commit + push GitHub

### Phase 1 (semaine prochaine)
- [ ] Créer module `identity.py`
- [ ] Génération clés RSA-4096 (libsodium)
- [ ] Table `users` locale
- [ ] API `/api/auth/register`
- [ ] UI premier lancement

### Phase 2 (semaine 2)
- [ ] Deploy serveur relay sur VPS Ionos
- [ ] Nginx + HTTPS (Let's Encrypt)
- [ ] Table `sync_log` relay
- [ ] API `/api/sync/*`

---

## 10. Métriques de succès (post-launch)

### Objectifs 6 mois
- 1,000 utilisateurs actifs
- 10% conversion premium (100 payants)
- Revenus : 500€/mois
- NPS > 50

### Objectifs 1 an
- 10,000 utilisateurs actifs
- 15% conversion premium (1,500 payants)
- Revenus : 7,500€/mois
- Croissance virale : 30% users via partages

### Objectifs 2 ans
- 100,000 utilisateurs actifs
- 20% conversion premium (20,000 payants)
- Revenus : 100,000€/mois
- Reconnaissance internationale

---

**Validé par : Nathalie**
**Date : 2026-02-10**
