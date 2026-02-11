#!/usr/bin/env python3
"""
Test de signature et vérification Ed25519
"""

import sys
from identity import (
    get_identity, load_private_keys, sign_data,
    verify_signature
)

def main():
    print("=== Test Signature Ed25519 ===\n")

    # 1. Charger l'identité
    identity = get_identity()
    if not identity:
        print("❌ Identité non trouvée")
        sys.exit(1)

    print(f"✅ Identité chargée : {identity['user_id']}")

    # 2. Charger les clés privées
    try:
        rsa_key, ed25519_key = load_private_keys()
        print("✅ Clés privées chargées")
    except Exception as e:
        print(f"❌ Erreur chargement clés : {e}")
        sys.exit(1)

    # 3. Signer des données
    data = "test_challenge_12345_phase1_p2p"
    print(f"\nDonnées à signer : {data}")

    try:
        signature = sign_data(data, key_type="ed25519")
        print(f"✅ Signature générée : {signature[:40]}...")
    except Exception as e:
        print(f"❌ Erreur signature : {e}")
        sys.exit(1)

    # 4. Vérifier la signature
    public_key = identity["keys"]["ed25519"]["public_key"]
    try:
        valid = verify_signature(data, signature, public_key, key_type="ed25519")
        if valid:
            print("✅ Signature valide !")
        else:
            print("❌ Signature invalide")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur vérification : {e}")
        sys.exit(1)

    # 5. Tester avec des données modifiées (doit échouer)
    print("\n--- Test signature avec données modifiées ---")
    modified_data = data + "_modified"
    try:
        valid = verify_signature(modified_data, signature, public_key, key_type="ed25519")
        if not valid:
            print("✅ Signature correctement rejetée pour données modifiées")
        else:
            print("❌ ERREUR : Signature acceptée pour données modifiées !")
            sys.exit(1)
    except Exception as e:
        print(f"✅ Exception attendue : {e}")

    print("\n✅ Tous les tests de signature réussis !")


if __name__ == "__main__":
    main()
