#!/bin/bash
# Test Phase 7 — Groupes
# Scénario : A crée groupe "Famille" → Invite B et C → Partage tag → Kick B

set -e

RELAY_DB="/Users/nathalie/.bigboff/relay.db"

echo "=== Test Phase 7 : Groupes (1-to-many) ==="
echo ""

# ── Test 1 : Vérifier tables groups ──
echo "✓ Test 1 : Vérifications tables groups"

groups_table=$(sqlite3 "$RELAY_DB" "SELECT name FROM sqlite_master WHERE type='table' AND name='groups'" || echo "")
if [ -z "$groups_table" ]; then
  echo "❌ Table groups manquante"
  exit 1
fi
echo "  ✅ Table groups présente"

members_table=$(sqlite3 "$RELAY_DB" "SELECT name FROM sqlite_master WHERE type='table' AND name='group_members'" || echo "")
if [ -z "$members_table" ]; then
  echo "❌ Table group_members manquante"
  exit 1
fi
echo "  ✅ Table group_members présente"

echo ""

# ── Test 2 : Créer groupe ──
echo "✓ Test 2 : Créer groupe 'Famille' (owner=test_alice)"

sqlite3 "$RELAY_DB" <<EOF
DELETE FROM groups WHERE id='grp_test123';
DELETE FROM group_members WHERE group_id='grp_test123';

INSERT INTO groups (id, name, owner_user_id, created_at)
VALUES ('grp_test123', 'Famille', 'test_alice', datetime('now'));

INSERT INTO group_members (group_id, user_id, role, joined_at)
VALUES ('grp_test123', 'test_alice', 'admin', datetime('now'));
EOF

group_count=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM groups WHERE id='grp_test123'")
if [ "$group_count" != "1" ]; then
  echo "❌ Groupe non créé"
  exit 1
fi
echo "  ✅ Groupe 'Famille' créé (grp_test123)"

echo ""

# ── Test 3 : Ajouter membres ──
echo "✓ Test 3 : Ajouter membres Bob et Charlie"

sqlite3 "$RELAY_DB" <<EOF
INSERT INTO group_members (group_id, user_id, role, joined_at)
VALUES
  ('grp_test123', 'test_bob', 'member', datetime('now')),
  ('grp_test123', 'test_charlie', 'member', datetime('now'));
EOF

members_count=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM group_members WHERE group_id='grp_test123'")
if [ "$members_count" -lt "3" ]; then
  echo "❌ Membres non ajoutés (count=$members_count, attendu >= 3)"
  exit 1
fi
echo "  ✅ $members_count membres dans le groupe (Alice admin, Bob, Charlie)"

echo ""

# ── Test 4 : Vérifier rôles ──
echo "✓ Test 4 : Vérifier rôles (admin vs member)"

alice_role=$(sqlite3 "$RELAY_DB" "SELECT role FROM group_members WHERE group_id='grp_test123' AND user_id='test_alice'")
if [ "$alice_role" != "admin" ]; then
  echo "❌ Alice devrait être admin (role=$alice_role)"
  exit 1
fi
echo "  ✅ Alice est admin"

bob_role=$(sqlite3 "$RELAY_DB" "SELECT role FROM group_members WHERE group_id='grp_test123' AND user_id='test_bob'")
if [ "$bob_role" != "member" ]; then
  echo "❌ Bob devrait être member (role=$bob_role)"
  exit 1
fi
echo "  ✅ Bob est member"

echo ""

# ── Test 5 : Kick membre ──
echo "✓ Test 5 : Kick Bob du groupe"

sqlite3 "$RELAY_DB" "DELETE FROM group_members WHERE group_id='grp_test123' AND user_id='test_bob'"

members_after_kick=$(sqlite3 "$RELAY_DB" "SELECT COUNT(*) FROM group_members WHERE group_id='grp_test123'")
if [ "$members_after_kick" != "2" ]; then
  echo "❌ Kick échoué (count=$members_after_kick, attendu 2)"
  exit 1
fi
echo "  ✅ Bob kicked, reste 2 membres (Alice, Charlie)"

echo ""

# ── Test 6 : Vérifier permissions groupe ──
echo "✓ Test 6 : Vérifier colonne target_group_id dans permissions"

target_group_col=$(sqlite3 "$RELAY_DB" "PRAGMA table_info(permissions)" | grep target_group_id || echo "")
if [ -z "$target_group_col" ]; then
  echo "❌ Colonne target_group_id manquante dans permissions"
  exit 1
fi
echo "  ✅ Colonne target_group_id présente (prête pour partage groupe)"

echo ""

# ── Cleanup ──
echo "✓ Cleanup test"

sqlite3 "$RELAY_DB" "DELETE FROM groups WHERE id='grp_test123'"
sqlite3 "$RELAY_DB" "DELETE FROM group_members WHERE group_id='grp_test123'"

echo "  ✅ Cleanup effectué"

echo ""
echo "=== ✅ TOUS LES TESTS Phase 7 PASSENT ==="
