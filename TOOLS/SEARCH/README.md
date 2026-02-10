# BIG_BOFF Search

Extension Chrome + serveur local pour rechercher dans tous les fichiers Dropbox par tags.

## Installation

### 1. Lancer le serveur

```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH
python3 src/server.py
```

Le serveur demarre sur `http://127.0.0.1:7777`.

### 2. Installer l'extension Chrome

1. Ouvrir Chrome → `chrome://extensions`
2. Activer le **Mode developpeur** (toggle en haut a droite)
3. Cliquer **Charger l'extension non empaquetee**
4. Selectionner le dossier : `TOOLS/SEARCH/extension/`
5. L'icone apparait dans la barre Chrome

## Utilisation

1. Cliquer sur l'icone BIG_BOFF Search dans la barre Chrome
2. Taper un mot-clef → autocompletion instantanee
3. Selectionner un tag (Entree ou clic) → resultats affiches
4. Les **tags associes** apparaissent sous la barre de recherche
   - **Clic gauche** : ajouter le tag (+vert)
   - **Clic droit** : exclure le tag (-rouge)
5. Cliquer sur un tag selectionne pour basculer inclus/exclu
6. Cliquer sur le × pour retirer un tag

## Mise a jour des tags

Apres modification des fichiers, regenerer les tags :

```bash
python3 src/generate_tags.py
```

## Architecture

```
SEARCH/
├── _SUIVI.md           # Suivi du projet
├── README.md           # Ce fichier
├── src/
│   ├── generate_tags.py  # Generation des tags atomiques
│   └── server.py         # Micro-serveur API (port 7777)
├── extension/
│   ├── manifest.json     # Manifest Chrome v3
│   ├── popup.html        # Interface de recherche
│   ├── popup.js          # Logique de recherche
│   └── icon*.png         # Icones
└── tests/
```

## API

| Endpoint | Parametres | Description |
|---|---|---|
| `/api/autocomplete` | `q=py` | Tags commencant par le prefixe |
| `/api/search` | `include=code&include=python&exclude=test` | Recherche par tags (+/-) |
| `/api/cooccurrence` | `include=code&include=python` | Tags associes aux resultats |
| `/api/stats` | — | Statistiques generales |

## Dependances

- Python 3.x (aucune lib externe)
- Chrome (pour l'extension)
- `catalogue.db` (genere par `TOOLS/MAINTENANCE/catalogue.py`)
