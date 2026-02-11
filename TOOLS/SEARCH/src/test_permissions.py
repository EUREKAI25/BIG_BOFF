#!/usr/bin/env python3
"""
Test Phase 3 - Permissions multi-user
Scénarios :
1. User A partage tag "notes" en consultation à User B
2. User B pull et voit les éléments de A
3. User A révoque la permission
4. User B pull et ne voit plus les éléments de A
5. User A partage tag "recettes" en mode partage à User B
6. Tests edge cases
"""

import json
import sys
import urllib.request
from identity import get_identity

RELAY_URL = "http://127.0.0.1:8888"


def http_request(method, endpoint, data=None, token=None):
    """Requête HTTP vers relay."""
    url = f"{RELAY_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req_data = json.dumps(data).encode() if data else None

    try:
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            return json.loads(error_body)
        except:
            return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_permissions_flow():
    """Test complet du flow permissions."""
    print("╔" + "═" * 58 + "╗")
    print("║  Test Phase 3 — Permissions + ACL (simulation)           ║")
    print("╚" + "═" * 58 + "╝\n")

    # Récupérer identité locale (User A)
    identity = get_identity()
    if not identity:
        print("❌ Identité locale non trouvée")
        print("   Créer : python3 identity.py init")
        return False

    user_a_id = identity["user_id"]
    print(f"👤 User A (moi) : {user_a_id}\n")

    # Simulation User B (on ne peut pas créer vraiment un 2ème user)
    user_b_id = "bigboff_test_user_b_000"
    print(f"👤 User B (test) : {user_b_id}")
    print(f"   ⚠️  Simulation : on teste l'API mais User B n'existe pas vraiment\n")

    print("=" * 60)
    print("Test 1 : Accorder permission 'consultation' sur tag 'notes'")
    print("=" * 60 + "\n")

    # Pour tester, on a besoin d'un token JWT
    # Normalement on ferait : auth challenge → sign → verify → token
    # Mais pour ce test, on simule juste les appels API

    print("📋 Simulation grant permission...")
    print(f"   Owner: {user_a_id}")
    print(f"   Target: {user_b_id}")
    print(f"   Scope: tag:notes")
    print(f"   Mode: consultation")

    # NOTE : Ce test nécessite d'être authentifié avec un token JWT
    # Pour l'instant, on affiche juste le flow attendu

    print("\n✅ Flow attendu :")
    print("   1. User A → POST /api/permissions/grant")
    print("      {\"target_user_id\": \"bigboff_...\", \"scope_type\": \"tag\", \"scope_value\": \"notes\", \"mode\": \"consultation\"}")
    print("   2. Relay → {\"success\": true, \"permission_id\": 1}")
    print("   3. User B → GET /api/sync/changes")
    print("   4. Relay vérifie permissions → filtre changements")
    print("   5. User B reçoit uniquement changements du tag 'notes' de User A")

    print("\n=" * 60)
    print("Test 2 : Révoquer permission")
    print("=" * 60 + "\n")

    print("📋 Simulation revoke permission...")
    print(f"   Permission ID: 1")

    print("\n✅ Flow attendu :")
    print("   1. User A → POST /api/permissions/revoke {\"permission_id\": 1}")
    print("   2. Relay → {\"success\": true}")
    print("   3. Relay met à jour : SET revoked_at = NOW()")
    print("   4. User B → GET /api/sync/changes")
    print("   5. Relay vérifie permissions → plus rien (révoqué)")
    print("   6. User B reçoit : {\"changes\": []}")

    print("\n=" * 60)
    print("Test 3 : Permission mode 'partage'")
    print("=" * 60 + "\n")

    print("📋 Simulation grant mode partage...")
    print(f"   Scope: tag:recettes")
    print(f"   Mode: partage (copie locale)")

    print("\n✅ Flow attendu :")
    print("   1. User A → POST /api/permissions/grant {..., \"mode\": \"partage\"}")
    print("   2. User B pull → reçoit copie complète des éléments")
    print("   3. User B stocke localement (marqueur \"Partagé par A\")")
    print("   4. Si User A révoque → User B garde sa copie (snapshot figé)")

    print("\n=" * 60)
    print("Test 4 : Lister permissions")
    print("=" * 60 + "\n")

    print("📋 Simulation list permissions...")

    print("\n✅ Flow attendu :")
    print("   1. User A → GET /api/permissions/list?as=owner")
    print("   2. Relay → {\"permissions\": [{\"target\": \"B\", \"scope\": \"tag:notes\", ...}]}")
    print("   3. User B → GET /api/permissions/list?as=target")
    print("   4. Relay → {\"permissions\": [{\"owner\": \"A\", \"scope\": \"tag:notes\", ...}]}")

    print("\n=" * 60)
    print("Tests edge cases")
    print("=" * 60 + "\n")

    print("📋 Cas limites à vérifier :")
    print("   ✓ Permission déjà accordée → UPDATE au lieu d'INSERT")
    print("   ✓ Révocation permission inexistante → erreur")
    print("   ✓ User tente d'accéder sans permission → 403 ou []")
    print("   ✓ Token expiré → ré-auth automatique")
    print("   ✓ Challenge expiré (>60s) → erreur")
    print("   ✓ Challenge déjà utilisé (anti-replay) → erreur")

    print("\n" + "=" * 60)
    print("✅ TESTS PHASE 3 — Flows documentés")
    print("=" * 60)

    print("\n💡 Pour tester réellement :")
    print("   1. python3 src/relay_server.py (terminal 1)")
    print("   2. python3 src/sync.py register")
    print("   3. python3 src/sync.py auth")
    print("   4. python3 src/permissions.py grant <user_b> tag notes")
    print("   5. python3 src/permissions.py list --as owner")
    print("   6. python3 src/permissions.py revoke <permission_id>")

    print("\n💡 Test multi-user réel :")
    print("   → Nécessite 2 machines ou 2 comptes ~/.bigboff/")
    print("   → User A et User B avec identités séparées")
    print("   → Relay server partagé (localhost ou VPS)")

    return True


def main():
    """Point d'entrée."""
    success = test_permissions_flow()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
