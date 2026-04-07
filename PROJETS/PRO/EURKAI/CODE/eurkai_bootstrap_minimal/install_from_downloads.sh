#!/bin/bash
set -e

ZIP_NAME="eurkai_bootstrap_minimal.zip"
SOURCE="$HOME/Downloads/$ZIP_NAME"
TARGET="/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/EURKAI/CODE"

if [ ! -f "$SOURCE" ]; then
  echo "Fichier introuvable : $SOURCE"
  exit 1
fi

mkdir -p "$TARGET"
unzip -o "$SOURCE" -d "$TARGET"
echo "Installation terminée dans : $TARGET"
