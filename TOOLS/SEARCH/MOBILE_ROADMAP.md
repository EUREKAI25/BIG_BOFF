# BIG_BOFF Search — Roadmap Mobile

## Vision
App mobile PWA installable, accessible depuis n'importe où, avec sync serveur distant.

---

## Phase 1 : PWA de base (2-3 jours)

### 1.1 Interface responsive
**Fichiers à modifier :**
- `src/server.py` (HTML fullpage)
- Ajouter CSS media queries pour mobile

**Actions :**
```css
/* Dans le <style> de server.py */
@media (max-width: 768px) {
  .container { padding: 10px; }
  .search-bar input { font-size: 16px; } /* Évite zoom iOS */
  .result-item { padding: 12px; }
  .type-filters { overflow-x: auto; white-space: nowrap; }
}
```

### 1.2 Manifest PWA
**Créer `extension/manifest.webmanifest` :**
```json
{
  "name": "BIG_BOFF Search",
  "short_name": "BIG_BOFF",
  "description": "Moteur de recherche universel par tags",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a1a1a",
  "theme_color": "#4a90d9",
  "orientation": "portrait",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Ajouter dans `<head>` de server.py :**
```html
<link rel="manifest" href="/manifest.webmanifest">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<meta name="theme-color" content="#4a90d9">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="/icon-192.png">
```

### 1.3 Service Worker (offline-first)
**Créer `extension/sw.js` :**
```javascript
const CACHE_NAME = 'bigboff-v1';
const ASSETS = [
  '/',
  '/manifest.webmanifest',
  '/icon-192.png',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css'
];

// Install
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
});

// Fetch (network first, cache fallback)
self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request)
      .then(res => {
        const clone = res.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
```

**Enregistrer dans server.py (avant `</body>`) :**
```javascript
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(() => console.log('SW registered'))
    .catch(err => console.error('SW error:', err));
}
```

### 1.4 Endpoint serveur pour Service Worker
**Ajouter dans `server.py` :**
```python
def do_GET(self):
    # ...
    elif self.path == '/manifest.webmanifest':
        self.send_json_response(manifest_content)
    elif self.path == '/sw.js':
        self.send_file('extension/sw.js', 'application/javascript')
```

---

## Phase 2 : Déploiement serveur distant (1 jour)

### 2.1 VPS Setup
**Fournisseurs recommandés :**
- Hetzner Cloud : 4.5€/mois (2 vCPU, 4GB RAM, Allemagne)
- DigitalOcean : $6/mois (US, EU)
- OVH VPS : 3.5€/mois (France)

**Specs recommandées :**
- 2 GB RAM minimum
- 20 GB SSD
- Ubuntu 22.04 LTS

### 2.2 Installation serveur
```bash
# Sur le VPS
sudo apt update
sudo apt install python3-pip nginx certbot python3-certbot-nginx

# Clone repo (ou rsync)
git clone https://github.com/votre-repo/bigboff-search.git
cd bigboff-search/TOOLS/SEARCH

# Install
pip3 install -r requirements.txt
python3 src/config_loader.py --init
nano ~/.bigboff/config.json  # Adapter chemins VPS
python3 src/setup_db.py
```

### 2.3 Nginx reverse proxy
**`/etc/nginx/sites-available/bigboff` :**
```nginx
server {
    listen 80;
    server_name bigboff.votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:7777;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/bigboff /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2.4 HTTPS avec Let's Encrypt
```bash
sudo certbot --nginx -d bigboff.votre-domaine.com
```

### 2.5 Systemd service (auto-start)
**`/etc/systemd/system/bigboff.service` :**
```ini
[Unit]
Description=BIG_BOFF Search Server
After=network.target

[Service]
Type=simple
User=bigboff
WorkingDirectory=/home/bigboff/bigboff-search/TOOLS/SEARCH
ExecStart=/usr/bin/python3 src/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable bigboff
sudo systemctl start bigboff
```

---

## Phase 3 : Auth & Sécurité (1 jour)

### 3.1 Authentification simple
**Ajouter dans `server.py` :**
```python
import hashlib
import secrets

# Token stocké dans cookie
SESSIONS = {}  # session_id -> user_id

def check_auth(self):
    """Vérifie si requête est authentifiée."""
    cookie = self.headers.get('Cookie', '')
    session_id = extract_session_id(cookie)
    return session_id in SESSIONS

def handle_login(self, data):
    """POST /api/login avec username + password."""
    username = data.get('username')
    password = data.get('password')

    # Hash password (bcrypt en prod)
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()

    # Vérifier (base users ou config)
    if verify_credentials(username, pwd_hash):
        session_id = secrets.token_urlsafe(32)
        SESSIONS[session_id] = username

        # Set cookie
        self.send_response(200)
        self.send_header('Set-Cookie', f'session={session_id}; HttpOnly; Secure; SameSite=Strict')
        self.end_headers()
        return {"success": True}

    return {"success": False, "error": "Invalid credentials"}
```

### 3.2 Page de login
**Créer `login.html` minimaliste :**
```html
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BIG_BOFF Login</title>
</head>
<body>
  <form id="login-form">
    <input type="password" id="password" placeholder="Mot de passe" autofocus>
    <button type="submit">Accéder</button>
  </form>
  <script>
    document.getElementById('login-form').onsubmit = async (e) => {
      e.preventDefault();
      const resp = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({password: document.getElementById('password').value})
      });
      if ((await resp.json()).success) location.href = '/';
    };
  </script>
</body>
</html>
```

### 3.3 CORS & CSP
```python
self.send_header('Access-Control-Allow-Origin', 'https://bigboff.votre-domaine.com')
self.send_header('Content-Security-Policy', "default-src 'self' https://cdnjs.cloudflare.com")
```

---

## Phase 4 : Optimisations mobile (1 semaine)

### 4.1 Interface tactile
- Swipe gauche/droite pour naviguer résultats
- Pull-to-refresh
- Boutons plus grands (44x44px minimum)
- Gestes long-press pour actions contextuelles

### 4.2 Fonctionnalités mobiles natives
**Via PWA APIs :**
- **Camera** : Scanner documents, QR codes
  ```javascript
  navigator.mediaDevices.getUserMedia({video: true})
  ```
- **Géolocalisation** : Auto-remplir adresse lieux
  ```javascript
  navigator.geolocation.getCurrentPosition()
  ```
- **Partage** : Partager résultats
  ```javascript
  navigator.share({title, text, url})
  ```
- **Notifications** : Rappels événements
  ```javascript
  Notification.requestPermission()
  ```

### 4.3 Mode offline avancé
- Cache SQLite local (sql.js)
- Sync queue pour actions offline
- Conflict resolution

---

## Phase 5 : Sync bidirectionnel (optionnel, long terme)

### Architecture
```
Mobile (SQLite local)  ←→  Serveur (SQLite central)
     ↓ Sync API
     - GET /api/sync/changes?since=timestamp
     - POST /api/sync/push (batch changes)
```

### Tables de sync
```sql
CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY,
    table_name TEXT,
    record_id INTEGER,
    action TEXT,  -- 'insert', 'update', 'delete'
    timestamp TEXT,
    synced INTEGER DEFAULT 0
);
```

---

## Alternatives

### Option 2 : App native (React Native)
**Avantages :**
- Meilleure UX
- Accès complet hardware

**Inconvénients :**
- Beaucoup plus de dev (3-4 semaines)
- Codebase séparée

### Option 3 : VPN privé (Tailscale)
**Avantages :**
- Données privées (pas d'exposition)
- Gratuit

**Inconvénients :**
- VPN requis pour accès mobile

---

## Coûts

| Service | Coût |
|---------|------|
| VPS Hetzner (4GB) | 4.5€/mois |
| Nom de domaine | 10€/an |
| **Total** | **~65€/an** |

---

## Estimation temps

| Phase | Durée |
|-------|-------|
| Phase 1 : PWA de base | 2-3 jours |
| Phase 2 : Déploiement VPS | 1 jour |
| Phase 3 : Auth & sécurité | 1 jour |
| Phase 4 : Optimisations mobile | 1 semaine |
| Phase 5 : Sync (optionnel) | 2-3 semaines |
| **MVP mobile (Ph1-3)** | **4-5 jours** |

---

## Prochaine étape

**Pour MVP mobile rapide :**
1. Rendre interface responsive (1 jour)
2. Ajouter manifest + SW (1 jour)
3. Déployer sur VPS avec HTTPS (1 jour)
4. Ajouter auth simple (1 jour)

→ **App mobile installable accessible partout en ~1 semaine**
