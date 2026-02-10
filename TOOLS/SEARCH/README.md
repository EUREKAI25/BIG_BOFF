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
| `POST /api/vault/unlock` | Déverrouiller coffre-fort |
| `POST /api/favorite` | Toggle favori |
| `DELETE /api/{type}` | Supprimer élément (modal 2 modes) |
| `POST /api/event` | Créer événement |
| `POST /api/contact` | Créer contact |
| `POST /api/lieu` | Créer lieu |
| ... | Voir _SUIVI.md pour liste complète |

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

**Système :**
- macOS 10.15+ (ou Windows/Linux avec adaptations)
- Python 3.9+
- Chrome ou Edge
- ffmpeg (optionnel, pour miniatures vidéo)
