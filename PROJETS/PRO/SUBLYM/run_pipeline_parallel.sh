#!/bin/bash
# PIPELINE COMPLET PARALLÈLE — SUBLYM
# Génère images Gemini + vidéos MiniMax EN PARALLÈLE pour optimiser le temps

SCENARIO="scenario_v8_20260211_221456.json"
REFERENCE="/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/SUBLYM_APP_PUB/Avatars/Mickael/photos"
SCENES="1 2 3 4 5"
MAX_ATTEMPTS=7
MAX_WORKERS=5  # Nombre de tâches en parallèle

# Créer répertoire de sortie daté
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="outputs/${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo ""
echo "🚀 PIPELINE COMPLET PARALLÈLE SUBLYM"
echo "===================================="
echo "Scénario: $SCENARIO"
echo "Scènes: $SCENES"
echo "Générateur: gemini-native"
echo "Max tentatives: $MAX_ATTEMPTS"
echo "Workers parallèles: $MAX_WORKERS"
echo "Output: $OUTPUT_DIR"
echo "===================================="
echo ""

python -u src/pipeline_complete_parallel.py \
    "$SCENARIO" \
    --scenes $SCENES \
    --reference-images "$REFERENCE" \
    --images-output "$OUTPUT_DIR/images" \
    --videos-output "$OUTPUT_DIR/videos" \
    --max-attempts $MAX_ATTEMPTS \
    --max-workers $MAX_WORKERS

echo ""
echo "✅ Pipeline parallèle terminé !"
echo "📁 Résultats dans: $OUTPUT_DIR"
echo ""
