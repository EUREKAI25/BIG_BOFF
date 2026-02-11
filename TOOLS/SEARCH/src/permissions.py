#!/usr/bin/env python3
"""
BIG_BOFF Search — Permissions Client
Module client pour gérer les permissions de partage (Phase 3 P2P).

Usage:
    python3 permissions.py grant <target_user_id> <scope_type> <scope_value> [--mode consultation|partage]
    python3 permissions.py revoke <permission_id>
    python3 permissions.py list [--as owner|target]
    python3 permissions.py show <permission_id>
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
from pathlib import Path

# Import local
try:
    from sync import _load_sync_state, _get_valid_token, _http_request
    from identity import get_identity
except ImportError:
    print("❌ Erreur : modules sync.py et identity.py requis")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

RELAY_URL = "http://127.0.0.1:8888"  # TODO: lire depuis sync_state


def _ensure_authenticated():
    """Vérifie que l'utilisateur est authentifié."""
    token = _get_valid_token()
    if not token:
        print("❌ Non authentifié")
        print("   Exécuter : python3 sync.py auth")
        sys.exit(1)
    return token


# ═══════════════════════════════════════════════════════════════
#  FONCTIONS PERMISSIONS
# ═══════════════════════════════════════════════════════════════

def grant_permission(target_user_id, scope_type, scope_value, mode="consultation", permissions=None):
    """Accorde une permission de partage.

    Args:
        target_user_id: User ID du destinataire
        scope_type: Type de scope ('tag', 'item', 'all')
        scope_value: Valeur du scope (nom du tag, item_id, ou None pour all)
        mode: Mode de partage ('consultation' ou 'partage')
        permissions: Liste de permissions (['read', 'write', 'delete'])

    Returns:
        dict: Résultat de l'API
    """
    token = _ensure_authenticated()

    if permissions is None:
        permissions = ["read"]

    data = {
        "target_user_id": target_user_id,
        "scope_type": scope_type,
        "scope_value": scope_value,
        "mode": mode,
        "permissions": permissions
    }

    return _http_request("POST", "/api/permissions/grant", data, token)


def revoke_permission(permission_id):
    """Révoque une permission de partage.

    Args:
        permission_id: ID de la permission à révoquer

    Returns:
        dict: Résultat de l'API
    """
    token = _ensure_authenticated()

    data = {"permission_id": permission_id}

    return _http_request("POST", "/api/permissions/revoke", data, token)


def list_permissions(as_param="owner"):
    """Liste les permissions accordées ou reçues.

    Args:
        as_param: 'owner' (accordées par moi) ou 'target' (reçues)

    Returns:
        dict: Résultat de l'API avec liste permissions
    """
    token = _ensure_authenticated()

    return _http_request("GET", f"/api/permissions/list?as={as_param}", token=token)


# ═══════════════════════════════════════════════════════════════
#  COMMANDES CLI
# ═══════════════════════════════════════════════════════════════

def cmd_grant(args):
    """Commande : accorder permission."""
    print(f"=== Accorder permission ===")
    print(f"Target: {args.target_user_id}")
    print(f"Scope: {args.scope_type} = {args.scope_value}")
    print(f"Mode: {args.mode}\n")

    result = grant_permission(
        args.target_user_id,
        args.scope_type,
        args.scope_value,
        args.mode
    )

    if result.get("success"):
        status = result.get("status", "created")
        perm_id = result.get("permission_id")
        print(f"✅ Permission {status} (ID: {perm_id})")
        print(f"\n💡 {args.target_user_id} peut maintenant accéder aux éléments '{args.scope_value}'")
        if args.mode == "consultation":
            print(f"   Mode consultation : accès temps réel, révocable instantanément")
        else:
            print(f"   Mode partage : copie locale, snapshot figé si révoqué")
        return 0
    else:
        print(f"❌ Erreur : {result.get('error')}")
        return 1


def cmd_revoke(args):
    """Commande : révoquer permission."""
    print(f"=== Révoquer permission #{args.permission_id} ===\n")

    result = revoke_permission(args.permission_id)

    if result.get("success"):
        print(f"✅ Permission révoquée")
        print(f"\n💡 L'accès a été immédiatement coupé")
        return 0
    else:
        print(f"❌ Erreur : {result.get('error')}")
        return 1


def cmd_list(args):
    """Commande : lister permissions."""
    as_param = args.as_param

    if as_param == "owner":
        print(f"=== Permissions accordées par moi ===\n")
    else:
        print(f"=== Permissions reçues ===\n")

    result = list_permissions(as_param)

    if not result.get("success"):
        print(f"❌ Erreur : {result.get('error')}")
        return 1

    permissions = result.get("permissions", [])
    count = result.get("count", 0)

    if count == 0:
        print("Aucune permission")
        return 0

    # Afficher tableau
    print(f"{'ID':<6} {'Target/Owner':<20} {'Scope':<15} {'Mode':<15} {'Statut':<10}")
    print("-" * 76)

    for perm in permissions:
        perm_id = perm["id"]
        scope = f"{perm['scope_type']}:{perm['scope_value']}"
        mode = perm["mode"]
        active = "✅ Active" if perm["active"] else "❌ Révoquée"

        if as_param == "owner":
            target = perm.get("target_user_id", "")[:20]
        else:
            target = perm.get("owner_user_id", "")[:20]

        print(f"{perm_id:<6} {target:<20} {scope:<15} {mode:<15} {active:<10}")

    print(f"\n📊 Total : {count} permission(s)")
    return 0


def cmd_show(args):
    """Commande : afficher détails permission."""
    print(f"=== Permission #{args.permission_id} ===\n")

    # Pour show, on liste toutes les permissions et on filtre par ID
    result_owner = list_permissions("owner")
    result_target = list_permissions("target")

    all_perms = []
    if result_owner.get("success"):
        all_perms.extend(result_owner.get("permissions", []))
    if result_target.get("success"):
        all_perms.extend(result_target.get("permissions", []))

    perm = next((p for p in all_perms if p["id"] == args.permission_id), None)

    if not perm:
        print(f"❌ Permission #{args.permission_id} non trouvée")
        return 1

    # Afficher détails
    print(f"ID: {perm['id']}")
    if "owner_user_id" in perm:
        print(f"Accordée par: {perm['owner_user_id']}")
    if "target_user_id" in perm:
        print(f"Accordée à: {perm['target_user_id']}")
    if perm.get("target_group_id"):
        print(f"Groupe: {perm['target_group_id']}")

    print(f"\nScope:")
    print(f"  Type: {perm['scope_type']}")
    print(f"  Valeur: {perm['scope_value']}")

    print(f"\nMode: {perm['mode']}")
    print(f"Permissions: {', '.join(perm['permissions'])}")

    print(f"\nAccordée le: {perm['granted_at']}")
    if perm['revoked_at']:
        print(f"Révoquée le: {perm['revoked_at']}")

    print(f"\nStatut: {'✅ Active' if perm['active'] else '❌ Révoquée'}")

    return 0


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Point d'entrée CLI."""
    parser = argparse.ArgumentParser(
        description="BIG_BOFF Search — Permissions Client (Phase 3 P2P)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Accorder accès au tag "notes" en consultation
  python3 permissions.py grant bigboff_abc123 tag notes

  # Accorder accès au tag "recettes" en mode partage
  python3 permissions.py grant bigboff_abc123 tag recettes --mode partage

  # Révoquer permission
  python3 permissions.py revoke 42

  # Lister permissions accordées
  python3 permissions.py list --as owner

  # Lister permissions reçues
  python3 permissions.py list --as target

  # Afficher détails permission
  python3 permissions.py show 42
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Commande")

    # Sous-commande grant
    parser_grant = subparsers.add_parser("grant", help="Accorder permission")
    parser_grant.add_argument("target_user_id", help="User ID destinataire")
    parser_grant.add_argument("scope_type", choices=["tag", "item", "all"], help="Type de scope")
    parser_grant.add_argument("scope_value", nargs="?", help="Valeur du scope (nom tag, item_id, ou vide pour all)")
    parser_grant.add_argument("--mode", choices=["consultation", "partage"], default="consultation", help="Mode de partage")

    # Sous-commande revoke
    parser_revoke = subparsers.add_parser("revoke", help="Révoquer permission")
    parser_revoke.add_argument("permission_id", type=int, help="ID de la permission")

    # Sous-commande list
    parser_list = subparsers.add_parser("list", help="Lister permissions")
    parser_list.add_argument("--as", dest="as_param", choices=["owner", "target"], default="owner", help="owner (accordées) ou target (reçues)")

    # Sous-commande show
    parser_show = subparsers.add_parser("show", help="Afficher détails permission")
    parser_show.add_argument("permission_id", type=int, help="ID de la permission")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatcher
    commands = {
        "grant": cmd_grant,
        "revoke": cmd_revoke,
        "list": cmd_list,
        "show": cmd_show
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        return cmd_func(args)
    else:
        print(f"❌ Commande inconnue : {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
