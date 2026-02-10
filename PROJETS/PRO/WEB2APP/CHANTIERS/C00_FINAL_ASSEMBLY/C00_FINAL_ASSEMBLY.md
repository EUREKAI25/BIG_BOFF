/    # C06
│       ├── assets/       # C07
│       ├── preview/      # C08
│       └── models/
│
├── frontend/             # C10
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│
├── components/           # C05 (shared native components)
│
└── deploy/               # C11
```

---

## BUILD.SH

```bash
#!/bin/bash
set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    WEB2APP — BUILD                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Vérifications
echo "[1/5] Vérifications..."
command -v docker >/dev/null 2>&1 || { echo "Docker requis"; exit 1; }
echo "✓ Docker"

# Vérifier les OUTPUTS
CHANTIERS_DIR="./WEB2APP_CHANTIERS"
for i in 01 02 03 04 05 06 07 08 09 10 11; do
    dir=$(ls -d "$CHANTIERS_DIR"/C${i}_*/OUTPUTS 2>/dev/null | head -1)
    if [ ! -d "$dir" ]; then
        echo "✗ C${i} OUTPUTS manquant"
        exit 1
    fi
done
echo "✓ Tous les OUTPUTS présents"

# Assemblage
echo "[2/5] Assemblage..."

mkdir -p web2app/backend/app
mkdir -p web2app/frontend/src
mkdir -p web2app/components

# Backend
cp -r "$CHANTIERS_DIR"/C01_PARSER/OUTPUTS/* web2app/backend/app/ 2>/dev/null || true
cp -r "$CHANTIERS_DIR"/C02_ANALYZER/OUTPUTS/* web2app/backend/app/ 2>/dev/null || true
cp -r "$CHANTIERS_DIR"/C03_MAPPER/OUTPUTS/* web2app/backend/app/ 2>/dev/null || true
cp -r "$CHANTIERS_DIR"/C04_GENERATOR/OUTPUTS/* web2app/backend/app/ 2>/dev/null || true
cp -r "$CHANTIERS_DIR"/C06_NAVIGATION/OUTPUTS/* web2app/backend/app/ 2>/dev/null || true
cp -r "$CHANTIERS_DIR"/C07_ASSETS/OUTPUTS/* web2app/backend/app/ 2>/dev/null || true
cp -r "$CHANTIERS_DIR"/C08_PREVIEW/OUTPUTS/* web2app/backend/app/ 2>/dev/null || true
cp -r "$CHANTIERS_DIR"/C09_API/OUTPUTS/* web2app/backend/ 2>/dev/null || true

# Native components
cp -r "$CHANTIERS_DIR"/C05_NATIVE_COMPONENTS/OUTPUTS/* web2app/components/ 2>/dev/null || true

# Frontend
cp -r "$CHANTIERS_DIR"/C10_FRONTEND/OUTPUTS/* web2app/frontend/ 2>/dev/null || true

# Deploy
cp -r "$CHANTIERS_DIR"/C11_DEPLOY/OUTPUTS/* web2app/ 2>/dev/null || true

echo "✓ Assemblage terminé"

# Configuration
echo "[3/5] Configuration..."
cd web2app
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠ .env créé - Ajoutez votre ANTHROPIC_API_KEY"
fi

# Build
echo "[4/5] Build Docker..."
docker-compose build

# Start
echo "[5/5] Démarrage..."
docker-compose up -d

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    WEB2APP — PRÊT ✓                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Commandes:"
echo "  make logs   Voir les logs"
echo "  make down   Arrêter"
```

---

## LIVRABLES

```
web2app/
├── build.sh
├── docker-compose.yml
├── Makefile
├── .env.example
├── README.md
├── backend/
├── frontend/
└── components/
```

## CRITÈRES DE VALIDATION

- [ ] ./build.sh s'exécute sans erreur
- [ ] Tous les services démarrent
- [ ] http://localhost:3000 accessible
- [ ] http://localhost:8000/health retourne OK
- [ ] Conversion d'un site de test fonctionne

## TEMPS ESTIMÉ
3 heures
