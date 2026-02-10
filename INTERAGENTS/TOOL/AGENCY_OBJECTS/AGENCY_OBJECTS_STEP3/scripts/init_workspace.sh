#!/usr/bin/env bash
set -euo pipefail

WS="${1:-./workspace}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TPL="${ROOT_DIR}/workspace_template"

rm -rf "${WS}"
mkdir -p "${WS}"
cp -R "${TPL}/." "${WS}/"
echo "OK: workspace=${WS}"
