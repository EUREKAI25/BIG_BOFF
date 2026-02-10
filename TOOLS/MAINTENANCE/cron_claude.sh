#!/bin/bash
# EURKAI — Cron automatique Claude
# Lance Claude Code pour exécuter les tâches planifiées
# Installé via launchd (voir com.eurkai.cron.plist)

LOG_DIR="/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cron_$(date +%Y%m%d_%H%M).log"

echo "=== EURKAI Cron — $(date) ===" > "$LOG_FILE"

# Lancer Claude en mode non-interactif avec le prompt cron
/Users/nathalie/.local/bin/claude --print \
  --working-directory "/Users/nathalie/Dropbox/____BIG_BOFF___" \
  "Tu es lancé automatiquement par le cron EURKAI. Lis /Users/nathalie/Dropbox/____BIG_BOFF___/CLAUDE/_CRON.md et exécute les tâches de maintenance échues. Mets à jour les fichiers de suivi. Ne fais aucune suppression. Résume ce que tu as fait dans _AUTO_BRIEF.md." \
  >> "$LOG_FILE" 2>&1

echo "=== Fin — $(date) ===" >> "$LOG_FILE"
