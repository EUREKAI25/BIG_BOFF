#!/bin/bash
# PIPELINE COMPLET — SUBLYM
# Génère automatiquement images Flux Kontext + vidéos MiniMax

SCENARIO="scenario_v8_20260211_221456.json"
REFERENCE="/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/SUBLYM_APP_PUB/Avatars/Mickael/photos"
SCENES="1 2 3 4 5"
MAX_ATTEMPTS=7
IMAGE_GENERATOR="${1:-flux}"  # flux (défaut) ou gemini

# Créer répertoire de sortie daté
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="outputs/${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo ""
echo "🎬 PIPELINE COMPLET SUBLYM"
echo "================================"
echo "Scénario: $SCENARIO"
echo "Scènes: $SCENES"
echo "Générateur: $IMAGE_GENERATOR"
echo "Max tentatives: $MAX_ATTEMPTS"
echo "Output: $OUTPUT_DIR"
echo "================================"
echo ""

python -u src/pipeline_complete.py \
    "$SCENARIO" \
    --scenes $SCENES \
    --reference-images "$REFERENCE" \
    --images-output "$OUTPUT_DIR/images" \
    --videos-output "$OUTPUT_DIR/videos" \
    --max-attempts $MAX_ATTEMPTS \
    --image-generator "$IMAGE_GENERATOR"

echo ""
echo "✅ Pipeline terminé !"
echo "📁 Résultats dans: $OUTPUT_DIR"
echo ""
