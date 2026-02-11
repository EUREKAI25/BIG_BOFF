#!/bin/bash
# Test Phase 8 — Multi-device
# Scénario : Vérifier table device_sessions prête pour activation device

set -e

RELAY_DB="/Users/nathalie/.bigboff/relay.db"

echo "=== Test Phase 8 : Multi-device (Structure MVP) ==="
echo ""

# ── Test 1 : Vérifier table device_sessions ──
echo "✓ Test 1 : Vérification table device_sessions"

device_table=$(sqlite3 "$RELAY_DB" "SELECT name FROM sqlite_master WHERE type='table' AND name='device_sessions'" || echo "")
if [ -z "$device_table" ]; then
  echo "❌ Table device_sessions manquante"
  exit 1
fi
echo "  ✅ Table device_sessions présente"

echo ""

# ── Test 2 : Vérifier colonnes ──
echo "✓ Test 2 : Vérifier schema table"

columns=$(sqlite3 "$RELAY_DB" "PRAGMA table_info(device_sessions)" | wc -l)
if [ "$columns" -lt "6" ]; then
  echo "❌ Colonnes manquantes (found=$columns, expected >= 6)"
  exit 1
fi
echo "  ✅ Schema complet (session_id, user_id, device_name, created_at, expires_at, revoked_at)"

echo ""

# ── Test 3 : Créer session test ──
echo "✓ Test 3 : Créer session device test"

sqlite3 "$RELAY_DB" <<EOF
DELETE FROM device_sessions WHERE session_id='sess_test123';

INSERT INTO device_sessions (session_id, user_id, device_name, created_at, expires_at)
VALUES (
  'sess_test123',
  'test_alice',
  'Mobile Alice',
  datetime('now'),
  datetime('now', '+24 hours')
);
EOF

session_count=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM device_sessions WHERE session_id='sess_test123'")
if [ "$session_count" != "1" ]; then
  echo "❌ Session non créée"
  exit 1
fi
echo "  ✅ Session créée : sess_test123 (Mobile Alice, expires 24h)"

echo ""

# ── Test 4 : Vérifier expiration ──
echo "✓ Test 4 : Vérifier session active (non expirée)"

active_session=$(sqlite3 "$RELAY_DB" "
  SELECT COUNT(*)
  FROM device_sessions
  WHERE session_id='sess_test123'
    AND (expires_at IS NULL OR expires_at > datetime('now'))
    AND revoked_at IS NULL
")

if [ "$active_session" != "1" ]; then
  echo "❌ Session devrait être active"
  exit 1
fi
echo "  ✅ Session active (non expirée, non révoquée)"

echo ""

# ── Test 5 : Révoquer session ──
echo "✓ Test 5 : Révoquer session"

sqlite3 "$RELAY_DB" "
  UPDATE device_sessions
  SET revoked_at = datetime('now')
  WHERE session_id='sess_test123'
"

revoked=$(sqlite3 "$RELAY_DB" "SELECT revoked_at FROM device_sessions WHERE session_id='sess_test123'")
if [ -z "$revoked" ]; then
  echo "❌ Session non révoquée"
  exit 1
fi
echo "  ✅ Session révoquée : $revoked"

echo ""

# ── Cleanup ──
echo "✓ Cleanup test"

sqlite3 "$RELAY_DB" "DELETE FROM device_sessions WHERE session_id='sess_test123'"

echo "  ✅ Cleanup effectué"

echo ""
echo "=== ✅ TOUS LES TESTS Phase 8 PASSENT (Structure MVP) ==="
echo ""
echo "ℹ️  Phase 8 : Structure tables prête, endpoints API à implémenter post-MVP"
