#!/usr/bin/env bash
set -euo pipefail

ZIP_PATH="${1:-}"
TARGET_DIR="${2:-}"

if [[ -z "$ZIP_PATH" || -z "$TARGET_DIR" ]]; then
  echo "Usage: ./install_chantier.sh <path/to/zip> <target_dir>"
  exit 1
fi

if [[ ! -f "$ZIP_PATH" ]]; then
  echo "ERROR: zip not found: $ZIP_PATH"
  exit 2
fi

mkdir -p "$TARGET_DIR"
TMP_DIR="$(mktemp -d)"

# 1) Extract to temp
unzip -oq "$ZIP_PATH" -d "$TMP_DIR"

# 2) Detect single top-level folder
TOP_DIRS="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d)"
TOP_COUNT="$(echo "$TOP_DIRS" | sed '/^\s*$/d' | wc -l | tr -d ' ')"
SRC_DIR="$TMP_DIR"
if [[ "$TOP_COUNT" == "1" ]]; then
  SRC_DIR="$(echo "$TOP_DIRS" | head -n 1)"
fi

# 3) Clean unwanted artifacts before copy
find "$SRC_DIR" -name ".pytest_cache" -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$SRC_DIR" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$SRC_DIR" -name "*.pyc" -type f -delete 2>/dev/null || true
find "$SRC_DIR" -name "*.pyo" -type f -delete 2>/dev/null || true
find "$SRC_DIR" -name "*.egg-info" -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$SRC_DIR" -name ".DS_Store" -type f -delete 2>/dev/null || true

# 4) Copy/merge into target (macOS-compatible)
cp -R "$SRC_DIR"/. "$TARGET_DIR"/

rm -rf "$TMP_DIR"
echo "[OK] Installed: $(basename "$ZIP_PATH") -> $TARGET_DIR"
