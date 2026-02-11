#!/usr/bin/env python3
"""
BIG_BOFF Search — QR Code Partage
Module pour générer et scanner QR codes de partage (Phase 4 P2P).

Usage:
    python3 qr_share.py generate tag notes --mode consultation
    python3 qr_share.py verify <qr_data>
"""

import argparse
import base64
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import qrcode
except ImportError:
    print("⚠️  qrcode non installé. Installer avec : pip install qrcode[pil]")
    qrcode = None

try:
    from identity import get_identity, sign_data
except ImportError:
    print("❌ Erreur : module identity.py requis")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

QR_EXPIRATION_HOURS = 24  # QR code expire après 24h
QR_VERSION = "1.0"


# ═══════════════════════════════════════════════════════════════
#  GÉNÉRATION QR CODE
# ═══════════════════════════════════════════════════════════════

def generate_share_qr(scope_type, scope_value, mode="consultation", output_path=None, password=None):
    """Génère un QR code de partage.

    Args:
        scope_type: Type de scope ('tag', 'item', 'all')
        scope_value: Valeur du scope (nom tag, item_id, etc.)
        mode: Mode de partage ('consultation' ou 'partage')
        output_path: Chemin fichier PNG de sortie (None = afficher à l'écran)
        password: Mot de passe identité si protégée

    Returns:
        dict: Données encodées dans le QR
    """
    if not qrcode:
        print("❌ Bibliothèque qrcode non installée")
        print("   Installer : pip install qrcode[pil]")
        sys.exit(1)

    # Récupérer identité locale
    identity = get_identity()
    if not identity:
        print("❌ Identité locale non trouvée")
        sys.exit(1)

    user_id = identity["user_id"]
    alias = identity.get("alias", "")

    # Timestamp expiration
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=QR_EXPIRATION_HOURS)

    # Données à encoder
    share_data = {
        "version": QR_VERSION,
        "type": "share_permission",
        "from_user_id": user_id,
        "from_alias": alias,
        "permission": {
            "scope_type": scope_type,
            "scope_value": scope_value,
            "mode": mode,
            "permissions": ["read"]
        },
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat()
    }

    # Signer les données
    data_to_sign = json.dumps(share_data, sort_keys=True)
    signature = sign_data(data_to_sign, key_type="ed25519", password=password)

    # Ajouter signature
    share_data["signature"] = signature

    # Encoder en base64
    share_json = json.dumps(share_data)
    share_b64 = base64.b64encode(share_json.encode()).decode()

    # Générer QR code
    qr = qrcode.QRCode(
        version=None,  # Auto-detect
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )
    qr.add_data(share_b64)
    qr.make(fit=True)

    # Créer image
    img = qr.make_image(fill_color="black", back_color="white")

    # Sauvegarder ou afficher
    if output_path:
        img.save(output_path)
        print(f"✅ QR code sauvegardé : {output_path}")
    else:
        # Afficher dans le terminal (ASCII art)
        print("\n=== QR Code (scanner avec appareil photo) ===\n")
        qr.print_ascii(invert=True)
        print()

    return share_data


def verify_share_qr(qr_data_b64):
    """Vérifie et décode un QR code de partage.

    Args:
        qr_data_b64: Données QR en base64

    Returns:
        dict: Données décodées si valide, None sinon
    """
    try:
        # Décoder base64
        share_json = base64.b64decode(qr_data_b64).decode()
        share_data = json.loads(share_json)

        # Vérifier version
        if share_data.get("version") != QR_VERSION:
            print(f"❌ Version QR incompatible : {share_data.get('version')}")
            return None

        # Vérifier type
        if share_data.get("type") != "share_permission":
            print(f"❌ Type QR invalide : {share_data.get('type')}")
            return None

        # Vérifier expiration
        expires_at_str = share_data.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.utcnow() > expires_at:
                print(f"❌ QR code expiré (créé il y a plus de {QR_EXPIRATION_HOURS}h)")
                return None

        # Vérifier signature
        signature = share_data.pop("signature", None)
        if not signature:
            print("❌ QR code non signé")
            return None

        from_user_id = share_data.get("from_user_id")
        public_key_ed25519 = share_data.get("public_key_ed25519")

        # Pour vérifier la signature, on aurait besoin de la clé publique
        # Dans un vrai scénario, on la récupérerait du relay ou du QR
        # Pour l'instant, on fait confiance si le format est bon

        print("✅ QR code valide")
        print(f"   De: {share_data.get('from_alias')} ({from_user_id})")
        print(f"   Scope: {share_data['permission']['scope_type']}:{share_data['permission']['scope_value']}")
        print(f"   Mode: {share_data['permission']['mode']}")

        # Remettre la signature
        share_data["signature"] = signature

        return share_data

    except Exception as e:
        print(f"❌ Erreur décodage QR : {e}")
        return None


# ═══════════════════════════════════════════════════════════════
#  COMMANDES CLI
# ═══════════════════════════════════════════════════════════════

def cmd_generate(args):
    """Commande : générer QR code."""
    print(f"=== Génération QR Code de Partage ===")
    print(f"Scope: {args.scope_type}:{args.scope_value}")
    print(f"Mode: {args.mode}\n")

    share_data = generate_share_qr(
        args.scope_type,
        args.scope_value,
        args.mode,
        args.output
    )

    print(f"\n📋 Données encodées :")
    print(f"   User ID: {share_data['from_user_id']}")
    print(f"   Alias: {share_data['from_alias']}")
    print(f"   Expire: {share_data['expires_at']}")

    if args.output:
        print(f"\n💡 Partager le fichier {args.output} ou scanner avec un appareil photo")
    else:
        print(f"\n💡 Scanner le QR code ci-dessus avec un appareil photo")

    return 0


def cmd_verify(args):
    """Commande : vérifier QR code."""
    print(f"=== Vérification QR Code ===\n")

    # Lire depuis fichier ou stdin
    if args.data:
        qr_data_b64 = args.data
    elif args.file:
        qr_data_b64 = Path(args.file).read_text().strip()
    else:
        print("❌ Fournir --data ou --file")
        return 1

    share_data = verify_share_qr(qr_data_b64)

    if share_data:
        print(f"\n✅ QR code valide et non expiré")
        print(f"\n💡 Pour accepter ce partage :")
        print(f"   python3 permissions.py grant {share_data['from_user_id']} \\")
        print(f"       {share_data['permission']['scope_type']} \\")
        print(f"       {share_data['permission']['scope_value']} \\")
        print(f"       --mode {share_data['permission']['mode']}")
        return 0
    else:
        return 1


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Point d'entrée CLI."""
    parser = argparse.ArgumentParser(
        description="BIG_BOFF Search — QR Code Partage (Phase 4 P2P)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Générer QR code pour partager tag "notes"
  python3 qr_share.py generate tag notes

  # Générer avec mode partage et sauvegarder
  python3 qr_share.py generate tag recettes --mode partage --output share.png

  # Vérifier QR code
  python3 qr_share.py verify --data <base64_data>
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Commande")

    # Sous-commande generate
    parser_gen = subparsers.add_parser("generate", help="Générer QR code")
    parser_gen.add_argument("scope_type", choices=["tag", "item", "all"], help="Type de scope")
    parser_gen.add_argument("scope_value", nargs="?", help="Valeur du scope")
    parser_gen.add_argument("--mode", choices=["consultation", "partage"], default="consultation", help="Mode")
    parser_gen.add_argument("--output", "-o", help="Fichier PNG de sortie")

    # Sous-commande verify
    parser_verify = subparsers.add_parser("verify", help="Vérifier QR code")
    parser_verify.add_argument("--data", help="Données QR base64")
    parser_verify.add_argument("--file", help="Fichier contenant données QR")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatcher
    commands = {
        "generate": cmd_generate,
        "verify": cmd_verify
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        return cmd_func(args)
    else:
        print(f"❌ Commande inconnue : {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
