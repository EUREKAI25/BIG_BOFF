#!/usr/bin/env python3
"""
Test du flow auth complet relay server
1. Register
2. Challenge
3. Verify (signature)
"""

import json
import sys
import urllib.request
import urllib.parse
import getpass
from identity import get_identity, sign_data

RELAY_URL = "http://127.0.0.1:8888"

def test_register():
    """Test POST /api/auth/register"""
    print("=== Test 1: Register ===")

    identity = get_identity()
    if not identity:
        print("❌ Identité non trouvée")
        sys.exit(1)

    data = {
        "user_id": identity["user_id"],
        "alias": identity.get("alias", ""),
        "public_key_rsa": identity["keys"]["rsa"]["public_key"],
        "public_key_ed25519": identity["keys"]["ed25519"]["public_key"]
    }

    req = urllib.request.Request(
        f"{RELAY_URL}/api/auth/register",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"✅ Register: {result}")
            return result.get("success", False)
    except Exception as e:
        print(f"❌ Erreur register: {e}")
        return False


def test_challenge(user_id):
    """Test POST /api/auth/challenge"""
    print("\n=== Test 2: Challenge ===")

    data = {"user_id": user_id}

    req = urllib.request.Request(
        f"{RELAY_URL}/api/auth/challenge",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"✅ Challenge reçu: {result['challenge_id']}")
            print(f"   Expires in: {result['expires_in']}s")
            return result
    except Exception as e:
        print(f"❌ Erreur challenge: {e}")
        return None


def test_verify(challenge_id, challenge, password=None):
    """Test POST /api/auth/verify avec signature"""
    print("\n=== Test 3: Verify (signature) ===")

    # Signer le challenge avec clé privée Ed25519
    print("Signature du challenge...")
    try:
        signature = sign_data(challenge, key_type="ed25519", password=password)
        print(f"✅ Signature générée: {signature[:40]}...")
    except Exception as e:
        import traceback
        print(f"❌ Erreur signature: {e}")
        traceback.print_exc()
        return None

    # Envoyer la signature au relay
    data = {
        "challenge_id": challenge_id,
        "signature": signature
    }

    req = urllib.request.Request(
        f"{RELAY_URL}/api/auth/verify",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if result.get("success"):
                print(f"✅ Vérification réussie !")
                print(f"   JWT token: {result['token'][:40]}...")
                print(f"   Expires in: {result['expires_in']}s ({result['expires_in'] // 3600}h)")
                return result["token"]
            else:
                print(f"❌ Vérification échouée: {result.get('error')}")
                return None
    except Exception as e:
        print(f"❌ Erreur verify: {e}")
        return None


def main():
    """Flow auth complet"""
    print("╔════════════════════════════════════════════╗")
    print("║  Test Auth Relay Server (challenge/sign)  ║")
    print("╚════════════════════════════════════════════╝\n")

    # Vérifier si identité protégée
    identity = get_identity()
    password = None
    if identity and identity.get("protection", {}).get("enabled"):
        print("🔒 Identité protégée - mot de passe requis")
        password = getpass.getpass("Mot de passe: ")
        print()

    # 1. Register
    if not test_register():
        sys.exit(1)

    # 2. Challenge
    challenge_data = test_challenge(identity["user_id"])
    if not challenge_data:
        sys.exit(1)

    # 3. Verify
    token = test_verify(challenge_data["challenge_id"], challenge_data["challenge"], password)
    if not token:
        sys.exit(1)

    print("\n" + "="*50)
    print("✅ TOUS LES TESTS AUTH RÉUSSIS !")
    print("="*50)
    print(f"\n🔑 JWT Token stocké (utilisable pour sync)")
    print(f"   Valide pendant: 24h")


if __name__ == "__main__":
    main()
