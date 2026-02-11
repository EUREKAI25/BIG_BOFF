#!/bin/bash
# Test Phase 5 — Mode Consultation
# Scénario : A partage tag "notes" à B → B consulte → A révoque → B perd accès

set -e

RELAY_DB="/Users/nathalie/.bigboff/relay.db"
CATALOG_DB="/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db"

echo "=== Test Phase 5 : Mode Consultation ==="
echo ""

# ── Test 1 : Vérifier migrations ──
echo "✓ Test 1 : Vérifications DB migrations"

expires_at=$(sqlite3 "$RELAY_DB" "PRAGMA table_info(sync_log)" | grep expires_at || echo "")
if [ -z "$expires_at" ]; then
  echo "❌ Colonne expires_at manquante dans sync_log"
  exit 1
fi
echo "  ✅ expires_at présent dans sync_log"

source_user=$(sqlite3 "$CATALOG_DB" "PRAGMA table_info(items)" | grep source_user_id || echo "")
if [ -z "$source_user" ]; then
  echo "❌ Colonne source_user_id manquante dans items"
  exit 1
fi
echo "  ✅ source_user_id présent dans items"

echo ""

# ── Test 2 : Créer permission consultation ──
echo "✓ Test 2 : Créer permission consultation (A → B, tag:notes)"

sqlite3 "$RELAY_DB" <<EOF
DELETE FROM permissions WHERE owner_user_id='test_alice' AND target_user_id='test_bob';
INSERT INTO permissions (owner_user_id, target_user_id, scope_type, scope_value, mode, permissions, granted_at)
VALUES ('test_alice', 'test_bob', 'tag', 'notes', 'consultation', '["read"]', datetime('now'));
EOF

perm_count=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM permissions WHERE owner_user_id='test_alice' AND target_user_id='test_bob' AND mode='consultation'")
if [ "$perm_count" != "1" ]; then
  echo "❌ Permission non créée"
  exit 1
fi
echo "  ✅ Permission créée : test_alice → test_bob (tag:notes, consultation)"

echo ""

# ── Test 3 : A pousse snapshot avec TTL ──
echo "✓ Test 3 : A pousse snapshot test avec TTL 1h"

expires_at_iso=$(date -u -v+1H '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -d '+1 hour' '+%Y-%m-%dT%H:%M:%SZ')

sqlite3 "$RELAY_DB" <<EOF
DELETE FROM sync_log WHERE user_id='test_alice' AND entity_type='item' AND entity_id=9999;
INSERT INTO sync_log (user_id, entity_type, entity_id, action, timestamp, data, expires_at)
VALUES (
  'test_alice',
  'item',
  9999,
  'create',
  datetime('now'),
  '{"path":"/test/note_phase5.txt","tags":["notes","test"],"date_modified":"2026-02-11T10:00:00Z"}',
  '$expires_at_iso'
);
EOF

snapshot_count=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM sync_log WHERE user_id='test_alice' AND entity_id=9999")
if [ "$snapshot_count" != "1" ]; then
  echo "❌ Snapshot non inséré"
  exit 1
fi
echo "  ✅ Snapshot inséré : test_alice, item 9999, expires_at=$expires_at_iso"

echo ""

# ── Test 4 : B consulte données de A ──
echo "✓ Test 4 : B consulte données de A (simulation)"

# Simuler query consultation
snapshots=$(sqlite3 "$RELAY_DB" "
  SELECT entity_type, entity_id, data
  FROM sync_log
  WHERE user_id='test_alice'
    AND (expires_at IS NULL OR expires_at > datetime('now'))
")

if [ -z "$snapshots" ]; then
  echo "❌ Aucun snapshot récupéré"
  exit 1
fi
echo "  ✅ Snapshots récupérés :"
echo "$snapshots" | while IFS='|' read -r entity_type entity_id data; do
  echo "    - $entity_type #$entity_id"
done

# Simuler insertion dans cache local de B
sqlite3 "$CATALOG_DB" <<EOF
DELETE FROM items WHERE id=9999;
INSERT INTO items (id, nom, chemin, extension, taille, date_modif, est_dossier, source_user_id)
VALUES (
  9999,
  'note_phase5.txt',
  '/test/note_phase5.txt',
  'txt',
  1024,
  '2026-02-11 10:00:00',
  0,
  'test_alice'
);
EOF

cache_count=$(sqlite3 "$CATALOG_DB" "SELECT COUNT(*) FROM items WHERE id=9999 AND source_user_id='test_alice'")
if [ "$cache_count" != "1" ]; then
  echo "❌ Cache local non appliqué"
  exit 1
fi
echo "  ✅ Cache local appliqué : item 9999 (source_user_id=test_alice)"

echo ""

# ── Test 5 : A révoque permission ──
echo "✓ Test 5 : A révoque permission"

sqlite3 "$RELAY_DB" "
  UPDATE permissions
  SET revoked_at = datetime('now')
  WHERE owner_user_id='test_alice' AND target_user_id='test_bob' AND scope_type='tag' AND scope_value='notes'
"

revoked_count=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM permissions WHERE owner_user_id='test_alice' AND target_user_id='test_bob' AND revoked_at IS NOT NULL")
if [ "$revoked_count" != "1" ]; then
  echo "❌ Permission non révoquée"
  exit 1
fi
echo "  ✅ Permission révoquée : test_alice → test_bob"

echo ""

# ── Test 6 : B perd accès (vérification permission) ──
echo "✓ Test 6 : B vérifie permission → refusé"

allowed=$(sqlite3 "$RELAY_DB" "
  SELECT COUNT(*)
  FROM permissions
  WHERE owner_user_id='test_alice'
    AND target_user_id='test_bob'
    AND scope_type='tag'
    AND scope_value='notes'
    AND mode='consultation'
    AND (revoked_at IS NULL OR revoked_at = '')
")

if [ "$allowed" != "0" ]; then
  echo "❌ Permission encore valide après révocation"
  exit 1
fi
echo "  ✅ Permission refusée (révoquée)"

# Simuler suppression du cache local de B
sqlite3 "$CATALOG_DB" "DELETE FROM items WHERE id=9999 AND source_user_id='test_alice'"

cache_after=$(sqlite3 "$CATALOG_DB" "SELECT COUNT(*) FROM items WHERE id=9999 AND source_user_id='test_alice'")
if [ "$cache_after" != "0" ]; then
  echo "❌ Cache local non supprimé"
  exit 1
fi
echo "  ✅ Cache local supprimé (révocation appliquée)"

echo ""
echo "=== ✅ Tous les tests Phase 5 réussis ==="
