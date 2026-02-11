#!/usr/bin/env python3
"""
BIG_BOFF Search — Module Identité Décentralisée
Gestion de l'identité cryptographique de l'utilisateur (Phase 1 P2P).

Module autonome : importable + CLI.

Usage CLI :
    python3 identity.py init --alias "Nathalie"
    python3 identity.py show
    python3 identity.py protect --password
    python3 identity.py export --output ~/backup/identity.json
    python3 identity.py verify --signature <sig> --data <data>

API importable :
    from identity import init_identity, get_identity, sign_data, verify_signature
"""

import base64
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    print("❌ Erreur : librairie 'cryptography' manquante")
    print("   Installer avec : pip install cryptography>=41.0.0")
    CRYPTO_AVAILABLE = False
    sys.exit(1)


# ── Constantes ──────────────────────────────────────────────────

PBKDF2_ITERATIONS = 100000
KEY_SIZE = 32  # 256 bits pour AES-256


# ── Helpers Path ────────────────────────────────────────────────

def _identity_file_path() -> Path:
    """Retourne Path vers ~/.bigboff/identity.json"""
    try:
        from config_loader import CONFIG_DIR
        return CONFIG_DIR / "identity.json"
    except ImportError:
        # Fallback si config_loader pas disponible
        return Path.home() / ".bigboff" / "identity.json"


# ── Génération de clés ──────────────────────────────────────────

def _generate_rsa_keypair() -> tuple:
    """Génère une paire de clés RSA-4096.

    Returns:
        (private_key, public_key) : objets cryptography
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


def _generate_ed25519_keypair() -> tuple:
    """Génère une paire de clés Ed25519.

    Returns:
        (private_key, public_key) : objets cryptography
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


# ── Sérialisation clés ──────────────────────────────────────────

def _serialize_public_key_rsa(public_key) -> str:
    """Sérialise clé publique RSA en PEM."""
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')


def _serialize_private_key_rsa(private_key) -> bytes:
    """Sérialise clé privée RSA en bytes (pas de passphrase)."""
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return pem


def _serialize_public_key_ed25519(public_key) -> str:
    """Sérialise clé publique Ed25519 en base64."""
    raw_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return base64.b64encode(raw_bytes).decode('utf-8')


def _serialize_private_key_ed25519(private_key) -> bytes:
    """Sérialise clé privée Ed25519 en bytes."""
    raw_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    return raw_bytes


# ── Désérialisation clés ────────────────────────────────────────

def _deserialize_public_key_rsa(pem_str: str):
    """Charge clé publique RSA depuis PEM."""
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    return load_pem_public_key(pem_str.encode('utf-8'), backend=default_backend())


def _deserialize_private_key_rsa(pem_bytes: bytes):
    """Charge clé privée RSA depuis PEM."""
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    return load_pem_private_key(pem_bytes, password=None, backend=default_backend())


def _deserialize_public_key_ed25519(b64_str: str):
    """Charge clé publique Ed25519 depuis base64."""
    raw_bytes = base64.b64decode(b64_str)
    return ed25519.Ed25519PublicKey.from_public_bytes(raw_bytes)


def _deserialize_private_key_ed25519(raw_bytes: bytes):
    """Charge clé privée Ed25519 depuis bytes."""
    return ed25519.Ed25519PrivateKey.from_private_bytes(raw_bytes)


# ── Chiffrement clés privées (protection) ───────────────────────

def _encrypt_key(key_bytes: bytes, password: str, salt: bytes = None) -> dict:
    """Chiffre une clé privée avec mot de passe (PBKDF2 + AES-256-GCM).

    Returns:
        {
            "ciphertext": base64_string,
            "salt": base64_string,
            "nonce": base64_string
        }
    """
    if salt is None:
        salt = os.urandom(32)

    # Dériver clé depuis mot de passe
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    key = kdf.derive(password.encode('utf-8'))

    # Chiffrer avec AES-256-GCM
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, key_bytes, None)

    return {
        "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
        "salt": base64.b64encode(salt).decode('utf-8'),
        "nonce": base64.b64encode(nonce).decode('utf-8')
    }


def _decrypt_key(encrypted_dict: dict, password: str) -> bytes:
    """Déchiffre une clé privée (PBKDF2 + AES-256-GCM).

    Args:
        encrypted_dict: dict avec ciphertext, salt, nonce (base64)
        password: mot de passe de déchiffrement

    Returns:
        bytes: clé privée déchiffrée

    Raises:
        Exception si mot de passe incorrect
    """
    ciphertext = base64.b64decode(encrypted_dict["ciphertext"])
    salt = base64.b64decode(encrypted_dict["salt"])
    nonce = base64.b64decode(encrypted_dict["nonce"])

    # Dériver clé depuis mot de passe
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    key = kdf.derive(password.encode('utf-8'))

    # Déchiffrer
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    return plaintext


# ── User ID ─────────────────────────────────────────────────────

def get_user_id_from_public_key(public_key_pem: str) -> str:
    """Calcule user_id depuis clé publique RSA.

    User ID = "bigboff_" + premiers 16 caractères du SHA-256(public_key)

    Returns:
        str: "bigboff_a7f3c2e1d9f8b5c4"
    """
    # Hash SHA-256 de la clé publique
    digest = hashlib.sha256(public_key_pem.encode('utf-8')).hexdigest()

    # Prendre les 16 premiers caractères
    short_hash = digest[:16]

    return f"bigboff_{short_hash}"


# ── Fonctions principales ───────────────────────────────────────

def init_identity(alias: str = "User", password: str = None) -> dict:
    """Génère nouvelle identité (clés RSA-4096 + Ed25519).

    Args:
        alias: Nom ou pseudo de l'utilisateur
        password: Mot de passe optionnel pour protéger clés privées

    Returns:
        dict: identité complète {user_id, alias, public_key_rsa, public_key_ed25519, ...}

    Raises:
        FileExistsError: si identité existe déjà
    """
    identity_file = _identity_file_path()

    # Vérifier si identité existe déjà
    if identity_file.exists():
        raise FileExistsError(f"Identité existe déjà : {identity_file}")

    # Créer dossier parent si nécessaire
    identity_file.parent.mkdir(parents=True, exist_ok=True)

    print("🔐 Génération de l'identité cryptographique...")
    print("   (Cela peut prendre 2-3 secondes)")

    # Générer clés RSA-4096
    print("   → Génération RSA-4096...")
    rsa_private, rsa_public = _generate_rsa_keypair()

    # Générer clés Ed25519
    print("   → Génération Ed25519...")
    ed_private, ed_public = _generate_ed25519_keypair()

    # Sérialiser clés publiques
    rsa_public_pem = _serialize_public_key_rsa(rsa_public)
    ed_public_b64 = _serialize_public_key_ed25519(ed_public)

    # Calculer User ID depuis clé publique RSA
    user_id = get_user_id_from_public_key(rsa_public_pem)

    # Sérialiser clés privées
    rsa_private_bytes = _serialize_private_key_rsa(rsa_private)
    ed_private_bytes = _serialize_private_key_ed25519(ed_private)

    # Chiffrer clés privées si mot de passe fourni
    if password:
        print("   → Protection par mot de passe...")
        rsa_encrypted = _encrypt_key(rsa_private_bytes, password)
        ed_encrypted = _encrypt_key(ed_private_bytes, password)

        rsa_private_stored = None
        ed_private_stored = None
        rsa_private_encrypted = rsa_encrypted
        ed_private_encrypted = ed_encrypted
        protection_enabled = True
    else:
        # Stocker en clair (base64 pour JSON)
        rsa_private_stored = base64.b64encode(rsa_private_bytes).decode('utf-8')
        ed_private_stored = base64.b64encode(ed_private_bytes).decode('utf-8')
        rsa_private_encrypted = None
        ed_private_encrypted = None
        protection_enabled = False

    # Construire structure identity
    identity = {
        "version": "1.0",
        "user_id": user_id,
        "alias": alias,
        "created_at": datetime.now().isoformat(),

        "keys": {
            "rsa": {
                "public_key": rsa_public_pem,
                "private_key": rsa_private_stored,
                "private_key_encrypted": rsa_private_encrypted,
                "algorithm": "RSA-4096"
            },
            "ed25519": {
                "public_key": ed_public_b64,
                "private_key": ed_private_stored,
                "private_key_encrypted": ed_private_encrypted,
                "algorithm": "Ed25519"
            }
        },

        "protection": {
            "enabled": protection_enabled,
            "iterations": PBKDF2_ITERATIONS if protection_enabled else None
        }
    }

    # Sauvegarder
    _save_identity(identity)

    print(f"✅ Identité créée : {user_id}")
    print(f"   Alias : {alias}")
    print(f"   Fichier : {identity_file}")
    print(f"   Protection : {'Oui' if protection_enabled else 'Non'}")

    return {
        "user_id": user_id,
        "alias": alias,
        "public_key_rsa": rsa_public_pem,
        "public_key_ed25519": ed_public_b64,
        "created_at": identity["created_at"]
    }


def get_identity() -> dict | None:
    """Charge l'identité depuis ~/.bigboff/identity.json.

    Returns:
        dict: identité complète ou None si non initialisée
    """
    identity_file = _identity_file_path()

    if not identity_file.exists():
        return None

    with open(identity_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_private_keys(password: str = None) -> tuple:
    """Charge les clés privées (déchiffre si protégées).

    Args:
        password: Mot de passe si clés protégées

    Returns:
        (rsa_private_key, ed25519_private_key): objets cryptography

    Raises:
        FileNotFoundError: si identité non initialisée
        ValueError: si mot de passe incorrect ou manquant
    """
    identity = get_identity()

    if not identity:
        raise FileNotFoundError("Identité non initialisée. Exécuter : python3 identity.py init")

    # Charger clés RSA
    if identity["keys"]["rsa"]["private_key_encrypted"]:
        # Clés chiffrées
        if not password:
            raise ValueError("Mot de passe requis (clés protégées)")

        rsa_encrypted = identity["keys"]["rsa"]["private_key_encrypted"]
        rsa_bytes = _decrypt_key(rsa_encrypted, password)
    else:
        # Clés en clair
        if not identity["keys"]["rsa"]["private_key"]:
            raise ValueError("Clé privée RSA manquante")

        rsa_bytes = base64.b64decode(identity["keys"]["rsa"]["private_key"])

    # Charger clés Ed25519
    if identity["keys"]["ed25519"]["private_key_encrypted"]:
        if not password:
            raise ValueError("Mot de passe requis (clés protégées)")

        ed_encrypted = identity["keys"]["ed25519"]["private_key_encrypted"]
        ed_bytes = _decrypt_key(ed_encrypted, password)
    else:
        if not identity["keys"]["ed25519"]["private_key"]:
            raise ValueError("Clé privée Ed25519 manquante")

        ed_bytes = base64.b64decode(identity["keys"]["ed25519"]["private_key"])

    # Désérialiser
    rsa_private = _deserialize_private_key_rsa(rsa_bytes)
    ed_private = _deserialize_private_key_ed25519(ed_bytes)

    return rsa_private, ed_private


def sign_data(data: str, key_type: str = "ed25519", password: str = None) -> str:
    """Signe des données avec la clé privée.

    Args:
        data: Données à signer (string)
        key_type: "ed25519" (rapide) ou "rsa"
        password: Mot de passe si clés protégées

    Returns:
        str: signature base64
    """
    rsa_key, ed_key = load_private_keys(password)

    data_bytes = data.encode('utf-8') if isinstance(data, str) else data

    if key_type == "ed25519":
        signature = ed_key.sign(data_bytes)
    elif key_type == "rsa":
        from cryptography.hazmat.primitives.asymmetric import padding
        signature = rsa_key.sign(
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    else:
        raise ValueError(f"Type de clé inconnu : {key_type}")

    return base64.b64encode(signature).decode('utf-8')


def verify_signature(data: str, signature: str, public_key: str, key_type: str = "ed25519") -> bool:
    """Vérifie une signature.

    Args:
        data: Données signées
        signature: Signature base64
        public_key: Clé publique (PEM pour RSA, base64 pour Ed25519)
        key_type: "ed25519" ou "rsa"

    Returns:
        bool: True si signature valide
    """
    data_bytes = data.encode('utf-8') if isinstance(data, str) else data
    sig_bytes = base64.b64decode(signature)

    try:
        if key_type == "ed25519":
            pub_key = _deserialize_public_key_ed25519(public_key)
            pub_key.verify(sig_bytes, data_bytes)
            return True
        elif key_type == "rsa":
            pub_key = _deserialize_public_key_rsa(public_key)
            from cryptography.hazmat.primitives.asymmetric import padding
            pub_key.verify(
                sig_bytes,
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        else:
            return False
    except Exception:
        return False


def protect_identity(password: str) -> bool:
    """Chiffre les clés privées avec mot de passe.

    Args:
        password: Mot de passe de protection

    Returns:
        bool: True si succès
    """
    identity = get_identity()

    if not identity:
        print("❌ Identité non initialisée")
        return False

    if identity["protection"]["enabled"]:
        print("⚠️  Identité déjà protégée")
        return False

    print("🔐 Protection de l'identité...")

    # Charger clés privées (actuellement en clair)
    rsa_bytes = base64.b64decode(identity["keys"]["rsa"]["private_key"])
    ed_bytes = base64.b64decode(identity["keys"]["ed25519"]["private_key"])

    # Chiffrer
    rsa_encrypted = _encrypt_key(rsa_bytes, password)
    ed_encrypted = _encrypt_key(ed_bytes, password)

    # Mettre à jour structure
    identity["keys"]["rsa"]["private_key"] = None
    identity["keys"]["rsa"]["private_key_encrypted"] = rsa_encrypted

    identity["keys"]["ed25519"]["private_key"] = None
    identity["keys"]["ed25519"]["private_key_encrypted"] = ed_encrypted

    identity["protection"]["enabled"] = True
    identity["protection"]["iterations"] = PBKDF2_ITERATIONS

    # Sauvegarder
    _save_identity(identity)

    print("✅ Identité protégée par mot de passe")
    return True


def export_identity(output_path: str, include_private: bool = False) -> bool:
    """Exporte l'identité (backup).

    Args:
        output_path: Chemin fichier de sortie
        include_private: Si True, inclut clés privées (⚠️ DANGEREUX)

    Returns:
        bool: True si succès
    """
    identity = get_identity()

    if not identity:
        print("❌ Identité non initialisée")
        return False

    if include_private:
        export_data = identity
        print("⚠️  ATTENTION : Export avec clés privées (fichier sensible !)")
    else:
        # Export public uniquement
        export_data = {
            "version": identity["version"],
            "user_id": identity["user_id"],
            "alias": identity["alias"],
            "created_at": identity["created_at"],
            "keys": {
                "rsa": {
                    "public_key": identity["keys"]["rsa"]["public_key"],
                    "algorithm": "RSA-4096"
                },
                "ed25519": {
                    "public_key": identity["keys"]["ed25519"]["public_key"],
                    "algorithm": "Ed25519"
                }
            }
        }

    output_file = Path(output_path).expanduser()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Identité exportée : {output_file}")
    print(f"   Type : {'Complète (avec clés privées)' if include_private else 'Publique uniquement'}")

    return True


# ── Helpers internes ────────────────────────────────────────────

def _save_identity(identity_dict: dict):
    """Sauvegarde identity.json avec permissions 600."""
    identity_file = _identity_file_path()
    identity_file.parent.mkdir(parents=True, exist_ok=True)

    with open(identity_file, 'w', encoding='utf-8') as f:
        json.dump(identity_dict, f, indent=2, ensure_ascii=False)

    # Permissions restrictives (lecture/écriture propriétaire uniquement)
    os.chmod(identity_file, 0o600)


# ── CLI ─────────────────────────────────────────────────────────

def _cli_init(args):
    """CLI: identity.py init --alias "Nathalie" [--password]"""
    alias = "User"
    password = None

    i = 0
    while i < len(args):
        if args[i] == "--alias" and i + 1 < len(args):
            alias = args[i + 1]
            i += 2
        elif args[i] == "--password":
            import getpass
            password = getpass.getpass("Mot de passe de protection (optionnel) : ")
            confirm = getpass.getpass("Confirmer : ")
            if password != confirm:
                print("❌ Mots de passe différents")
                sys.exit(1)
            i += 1
        else:
            i += 1

    try:
        result = init_identity(alias, password)
    except FileExistsError as e:
        print(f"❌ {e}")
        sys.exit(1)


def _cli_show(args):
    """CLI: identity.py show"""
    identity = get_identity()

    if not identity:
        print("❌ Identité non initialisée")
        print("   Exécuter : python3 identity.py init --alias \"VotreNom\"")
        sys.exit(1)

    print("\n🔑 Identité BIG_BOFF")
    print("=" * 60)
    print(f"User ID     : {identity['user_id']}")
    print(f"Alias       : {identity['alias']}")
    print(f"Créé le     : {identity['created_at']}")
    print(f"Protégée    : {'Oui' if identity['protection']['enabled'] else 'Non'}")
    print()
    print("Clés publiques :")
    print(f"  RSA-4096  : {identity['keys']['rsa']['public_key'][:80]}...")
    print(f"  Ed25519   : {identity['keys']['ed25519']['public_key']}")
    print("=" * 60)
    print()


def _cli_protect(args):
    """CLI: identity.py protect --password"""
    import getpass
    password = getpass.getpass("Nouveau mot de passe : ")
    confirm = getpass.getpass("Confirmer : ")

    if password != confirm:
        print("❌ Mots de passe différents")
        sys.exit(1)

    if len(password) < 8:
        print("❌ Mot de passe trop court (minimum 8 caractères)")
        sys.exit(1)

    success = protect_identity(password)
    sys.exit(0 if success else 1)


def _cli_export(args):
    """CLI: identity.py export --output ~/backup.json [--include-private]"""
    output_path = None
    include_private = False

    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i] == "--include-private":
            include_private = True
            i += 1
        else:
            i += 1

    if not output_path:
        print("❌ Option --output requise")
        print("   Usage : python3 identity.py export --output ~/backup.json")
        sys.exit(1)

    success = export_identity(output_path, include_private)
    sys.exit(0 if success else 1)


def _cli_verify(args):
    """CLI: identity.py verify --signature <sig> --data <data> [--key-type ed25519]"""
    signature = None
    data = None
    key_type = "ed25519"

    i = 0
    while i < len(args):
        if args[i] == "--signature" and i + 1 < len(args):
            signature = args[i + 1]
            i += 2
        elif args[i] == "--data" and i + 1 < len(args):
            data = args[i + 1]
            i += 2
        elif args[i] == "--key-type" and i + 1 < len(args):
            key_type = args[i + 1]
            i += 2
        else:
            i += 1

    if not signature or not data:
        print("❌ Options --signature et --data requises")
        sys.exit(1)

    identity = get_identity()
    if not identity:
        print("❌ Identité non initialisée")
        sys.exit(1)

    public_key = identity["keys"][key_type]["public_key"]
    valid = verify_signature(data, signature, public_key, key_type)

    print(f"Signature : {'✅ VALIDE' if valid else '❌ INVALIDE'}")
    sys.exit(0 if valid else 1)


def main():
    """Point d'entrée CLI."""
    if not CRYPTO_AVAILABLE:
        sys.exit(1)

    args = sys.argv[1:]

    if not args:
        print("BIG_BOFF Search — Module Identité Décentralisée")
        print()
        print("Usage :")
        print("  python3 identity.py init --alias \"VotreNom\" [--password]")
        print("  python3 identity.py show")
        print("  python3 identity.py protect --password")
        print("  python3 identity.py export --output ~/backup.json [--include-private]")
        print("  python3 identity.py verify --signature <sig> --data <data> [--key-type ed25519]")
        print()
        print("Exemples :")
        print("  python3 identity.py init --alias \"Nathalie\"")
        print("  python3 identity.py show")
        print("  python3 identity.py protect --password")
        sys.exit(0)

    cmd = args[0]
    rest = args[1:]

    if cmd == "init":
        _cli_init(rest)
    elif cmd == "show":
        _cli_show(rest)
    elif cmd == "protect":
        _cli_protect(rest)
    elif cmd == "export":
        _cli_export(rest)
    elif cmd == "verify":
        _cli_verify(rest)
    else:
        print(f"❌ Commande inconnue : {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
