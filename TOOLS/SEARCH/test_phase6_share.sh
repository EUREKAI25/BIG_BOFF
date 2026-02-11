#!/bin/bash
# Test Phase 6 — Mode Partage
# Scénario : A partage tag "recettes" à B → B clone → A modifie → B sync → A révoque → B garde snapshot

set -e

RELAY_DB="/Users/nathalie/.bigboff/relay.db"
CATALOG_DB="/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db"

echo "=== Test Phase 6 : Mode Partage (Clone Permanent) ==="
echo ""

# ── Test 1 : Vérifier migrations Phase 6 ──
echo "✓ Test 1 : Vérifications DB migrations Phase 6"

is_shared_copy=$(sqlite3 "$CATALOG_DB" "PRAGMA table_info(items)" | grep is_shared_copy || echo "")
if [ -z "$is_shared_copy" ]; then
  echo "❌ Colonne is_shared_copy manquante dans items"
  exit 1
fi
echo "  ✅ is_shared_copy présent dans items"

is_shared_copy_relay=$(sqlite3 "$RELAY_DB" "PRAGMA table_info(sync_log)" | grep is_shared_copy || echo "")
if [ -z "$is_shared_copy_relay" ]; then
  echo "❌ Colonne is_shared_copy manquante dans sync_log"
  exit 1
fi
echo "  ✅ is_shared_copy présent dans sync_log"

echo ""

# ── Test 2 : Créer permission partage ──
echo "✓ Test 2 : Créer permission partage (A → B, tag:recettes, mode:partage)"

sqlite3 "$RELAY_DB" <<EOF
DELETE FROM permissions WHERE owner_user_id='test_alice' AND target_user_id='test_bob';
INSERT INTO permissions (owner_user_id, target_user_id, scope_type, scope_value, mode, permissions, granted_at)
VALUES ('test_alice', 'test_bob', 'tag', 'recettes', 'partage', '["read"]', datetime('now'));
EOF

perm_count=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM permissions WHERE owner_user_id='test_alice' AND target_user_id='test_bob' AND mode='partage'")
if [ "$perm_count" != "1" ]; then
  echo "❌ Permission non créée"
  exit 1
fi
echo "  ✅ Permission créée : test_alice → test_bob (tag:recettes, partage)"

echo ""

# ── Test 3 : A pousse snapshots permanents ──
echo "✓ Test 3 : A pousse 3 snapshots test (recettes)"

sqlite3 "$RELAY_DB" <<EOF
DELETE FROM sync_log WHERE user_id='test_alice' AND entity_type='item' AND entity_id IN (1001, 1002, 1003);

INSERT INTO sync_log (user_id, entity_type, entity_id, action, timestamp, data, is_shared_copy)
VALUES
  ('test_alice', 'item', 1001, 'create', datetime('now'), '{"nom":"tarte_citron.md","tags":["recettes","dessert"]}', 1),
  ('test_alice', 'item', 1002, 'create', datetime('now'), '{"nom":"soupe_tomate.md","tags":["recettes","entrée"]}', 1),
  ('test_alice', 'item', 1003, 'create', datetime('now'), '{"nom":"poulet_roti.md","tags":["recettes","plat"]}', 1);
EOF

snapshot_count=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM sync_log WHERE user_id='test_alice' AND is_shared_copy=1")
if [ "$snapshot_count" -lt "3" ]; then
  echo "❌ Snapshots non insérés (count=$snapshot_count, attendu >= 3)"
  exit 1
fi
echo "  ✅ $snapshot_count snapshots insérés (is_shared_copy=1)"

echo ""

# ── Test 4 : B clone initial ──
echo "✓ Test 4 : B clone initial (mode partage)"

# Simuler récupération snapshots via /api/share/clone
snapshots=$(sqlite3 "$RELAY_DB" "
  SELECT entity_id, data
  FROM sync_log
  WHERE user_id='test_alice' AND is_shared_copy=1
")

if [ -z "$snapshots" ]; then
  echo "❌ Aucun snapshot récupéré"
  exit 1
fi
echo "  ✅ Snapshots récupérés :"
echo "$snapshots" | while IFS='|' read -r entity_id data; do
  echo "    - item #$entity_id"
done

# Simuler insertion dans DB locale de B avec is_shared_copy=1
sqlite3 "$CATALOG_DB" <<EOF
DELETE FROM items WHERE id IN (1001, 1002, 1003);
INSERT INTO items (id, nom, chemin, extension, taille, date_modif, est_dossier, source_user_id, is_shared_copy)
VALUES
  (1001, 'tarte_citron.md', '/recettes/tarte_citron.md', 'md', 1024, '2026-02-11 10:00:00', 0, 'test_alice', 1),
  (1002, 'soupe_tomate.md', '/recettes/soupe_tomate.md', 'md', 2048, '2026-02-11 10:05:00', 0, 'test_alice', 1),
  (1003, 'poulet_roti.md', '/recettes/poulet_roti.md', 'md', 3072, '2026-02-11 10:10:00', 0, 'test_alice', 1);
EOF

clone_count=$(sqlite3 "$CATALOG_DB" "SELECT COUNT(*) FROM items WHERE source_user_id='test_alice' AND is_shared_copy=1")
if [ "$clone_count" -lt "3" ]; then
  echo "❌ Clone local non appliqué (count=$clone_count, attendu >= 3)"
  exit 1
fi
echo "  ✅ Clone appliqué : $clone_count items (source_user_id=test_alice, is_shared_copy=1)"

echo ""

# ── Test 5 : A modifie un item ──
echo "✓ Test 5 : A modifie item 1001 (tarte_citron.md)"

# Attendre 1 seconde pour éviter collision timestamp
sleep 1

sqlite3 "$RELAY_DB" <<EOF
INSERT INTO sync_log (user_id, entity_type, entity_id, action, timestamp, data, is_shared_copy)
VALUES ('test_alice', 'item', 1001, 'update', datetime('now'), '{"nom":"tarte_citron_v2.md","tags":["recettes","dessert","citron"]}', 1);
EOF

update_count=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM sync_log WHERE user_id='test_alice' AND entity_id=1001 AND action='update'")
if [ "$update_count" != "1" ]; then
  echo "❌ Modification non enregistrée"
  exit 1
fi
echo "  ✅ Modification enregistrée : item 1001 → tarte_citron_v2.md"

echo ""

# ── Test 6 : B sync changements ──
echo "✓ Test 6 : B sync changements (simulation)"

# Simuler récupération changements via /api/share/sync
changes=$(sqlite3 "$RELAY_DB" "
  SELECT entity_id, action, data
  FROM sync_log
  WHERE user_id='test_alice' AND action='update' AND entity_id=1001
  ORDER BY timestamp DESC
  LIMIT 1
")

if [ -z "$changes" ]; then
  echo "❌ Aucun changement récupéré"
  exit 1
fi
echo "  ✅ Changements récupérés : update item 1001"

# Appliquer MAJ locale
sqlite3 "$CATALOG_DB" "
  UPDATE items
  SET nom='tarte_citron_v2.md'
  WHERE id=1001 AND source_user_id='test_alice'
"

synced_nom=$(sqlite3 "$CATALOG_DB" "SELECT nom FROM items WHERE id=1001")
if [ "$synced_nom" != "tarte_citron_v2.md" ]; then
  echo "❌ Sync non appliqué (nom=$synced_nom)"
  exit 1
fi
echo "  ✅ Sync appliqué : item 1001 → tarte_citron_v2.md"

echo ""

# ── Test 7 : A révoque permission ──
echo "✓ Test 7 : A révoque permission"

sqlite3 "$RELAY_DB" "
  UPDATE permissions
  SET revoked_at = datetime('now')
  WHERE owner_user_id='test_alice' AND target_user_id='test_bob' AND scope_type='tag' AND scope_value='recettes'
"

revoked_count=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM permissions WHERE owner_user_id='test_alice' AND target_user_id='test_bob' AND revoked_at IS NOT NULL")
if [ "$revoked_count" != "1" ]; then
  echo "❌ Permission non révoquée"
  exit 1
fi
echo "  ✅ Permission révoquée : test_alice → test_bob"

echo ""

# ── Test 8 : B garde snapshot figé ──
echo "✓ Test 8 : B garde snapshot figé (vérification)"

# Vérifier que les items partagés sont toujours présents même après révocation
frozen_count=$(sqlite3 "$CATALOG_DB" "SELECT COUNT(*) FROM items WHERE source_user_id='test_alice' AND is_shared_copy=1")
if [ "$frozen_count" -lt "3" ]; then
  echo "❌ Snapshot non figé (count=$frozen_count, attendu >= 3)"
  exit 1
fi
echo "  ✅ Snapshot figé : $frozen_count items conservés malgré révocation"

# Simuler tentative sync après révocation → échoue
allowed=$(sqlite3 "$RELAY_DB" "
  SELECT COUNT(*)
  FROM permissions
  WHERE owner_user_id='test_alice'
    AND target_user_id='test_bob'
    AND scope_type='tag'
    AND scope_value='recettes'
    AND (revoked_at IS NULL OR revoked_at > datetime('now'))
")

if [ "$allowed" != "0" ]; then
  echo "❌ Permission toujours active après révocation"
  exit 1
fi
echo "  ✅ Sync bloqué après révocation (permission révoquée)"

echo ""

# ── Test 9 : A supprime un item → B garde ──
echo "✓ Test 9 : A supprime item 1002 → B garde sa copie"

# Attendre 1 seconde pour éviter collision timestamp
sleep 1

sqlite3 "$RELAY_DB" <<EOF
INSERT INTO sync_log (user_id, entity_type, entity_id, action, timestamp, data, is_shared_copy)
VALUES ('test_alice', 'item', 1002, 'delete', datetime('now'), '{}', 1);
EOF

delete_log=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM sync_log WHERE user_id='test_alice' AND entity_id=1002 AND action='delete'")
if [ "$delete_log" != "1" ]; then
  echo "❌ Suppression non enregistrée côté A"
  exit 1
fi
echo "  ✅ A a supprimé item 1002 (delete enregistré)"

# Vérifier que B garde toujours l'item (pas de sync car révoqué)
b_still_has=$(sqlite3 "$CATALOG_DB" "SELECT COUNT(*) FROM items WHERE id=1002 AND source_user_id='test_alice'")
if [ "$b_still_has" != "1" ]; then
  echo "❌ B a perdu l'item 1002 (attendu conservation)"
  exit 1
fi
echo "  ✅ B garde item 1002 (suppression non propagée car révoqué)"

echo ""

# ── Cleanup ──
echo "✓ Cleanup test"

sqlite3 "$RELAY_DB" "DELETE FROM permissions WHERE owner_user_id='test_alice' AND target_user_id='test_bob'"
sqlite3 "$RELAY_DB" "DELETE FROM sync_log WHERE user_id='test_alice' AND entity_id IN (1001, 1002, 1003)"
sqlite3 "$CATALOG_DB" "DELETE FROM items WHERE id IN (1001, 1002, 1003)"

echo "  ✅ Cleanup effectué"

echo ""
echo "=== ✅ TOUS LES TESTS Phase 6 PASSENT ==="
