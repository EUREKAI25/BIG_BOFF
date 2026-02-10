# WEB2APP — Convertisseur Universel Site Web → App Mobile

## VISION

Transformer n'importe quel site web en application mobile native (iOS/Android) en quelques minutes grâce à l'IA.

```
INPUT                           OUTPUT
═════                           ══════
URL d'un site web               Projet Expo complet
   ou                              ↓
Code source React/HTML          App iOS + Android
```

## FONCTIONNEMENT

```
┌─────────────────────────────────────────────────────────────────┐
│                         WEB2APP                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   [Site Web] ──► [Parser] ──► [Analyzer] ──► [Mapper]           │
│                                                   │              │
│                                                   ▼              │
│   [App Native] ◄── [Preview] ◄── [Generator] ◄───┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## CHANTIERS

| # | Nom | Description | Durée | Prérequis |
|---|-----|-------------|-------|-----------|
| C01 | Parser | Extraction HTML/CSS/JS du site source | 3h | ∅ |
| C02 | Analyzer | IA analyse et comprend la structure UI | 4h | C01 |
| C03 | Mapper | Règles de conversion Web → Native | 4h | ∅ |
| C04 | Generator | Génère le code React Native | 5h | C02, C03 |
| C05 | Native Components | Bibliothèque composants natifs | 6h | ∅ |
| C06 | Navigation | Génère la navigation Expo Router | 3h | C02 |
| C07 | Assets | Extraction et optimisation assets | 2h | C01 |
| C08 | Preview | Prévisualisation live de l'app | 4h | C04, C05 |
| C09 | API Backend | API REST pour le service | 4h | C01-C08 |
| C10 | Frontend | Interface web du service | 4h | C09 |
| C11 | Deploy | Déploiement automatique | 2h | C09, C10 |
| C00 | Final Assembly | Assemblage et tests | 3h | TOUS |

**Total : ~44h | 4 agents parallèles : ~15h**

## INSTALLATION

```bash
# 1. Télécharger et extraire
cd ~/Downloads
unzip WEB2APP_CHANTIERS.zip
mv WEB2APP_CHANTIERS ~/Dropbox/____BIG_BOFF___/PROJETS/PRO/DAPPR/CHANTIERS/

# 2. Après avoir complété tous les chantiers
cd ~/Dropbox/____BIG_BOFF___/PROJETS/PRO/DAPPR/CHANTIERS/WEB2APP_CHANTIERS
chmod +x build.sh
./build.sh

# 3. Ouvrir
open http://localhost:3000
```

## UTILISATION

### Via l'interface web
1. Coller l'URL du site à convertir
2. Cliquer "Analyser"
3. Prévisualiser le résultat
4. Télécharger le projet Expo

### Via l'API
```bash
curl -X POST http://localhost:8000/api/convert \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Via CLI
```bash
./web2app convert https://example.com --output ./my-app
```

## ARCHITECTURE

```
web2app/
├── backend/
│   ├── app/
│   │   ├── parser/        # C01 - Extraction
│   │   ├── analyzer/      # C02 - Analyse IA
│   │   ├── mapper/        # C03 - Règles conversion
│   │   ├── generator/     # C04 - Génération code
│   │   ├── components/    # C05 - Composants natifs
│   │   ├── navigation/    # C06 - Navigation
│   │   ├── assets/        # C07 - Assets
│   │   └── api/           # C09 - Endpoints
│   └── tests/
├── frontend/              # C10 - Interface web
├── preview/               # C08 - Preview
└── deploy/                # C11 - Déploiement
```

## STACK TECHNIQUE

- **Backend** : Python 3.11+, FastAPI, Anthropic Claude API
- **Frontend** : React, TypeScript, Tailwind
- **Parser** : Playwright (scraping), BeautifulSoup (HTML), esprima (JS)
- **Preview** : Expo Snack / Appetize.io
- **Output** : Expo SDK 50+, React Native

## LICENCE

Propriétaire — Usage interne agence DAPPR
