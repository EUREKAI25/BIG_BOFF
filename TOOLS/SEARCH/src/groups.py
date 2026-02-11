#!/usr/bin/env python3
"""
BIG_BOFF Search — Groups Client
Module client pour gérer les groupes de partage 1-to-many (Phase 7 P2P).

Usage:
    python3 groups.py create <name>
    python3 groups.py invite <group_id> <user_id>
    python3 groups.py list
    python3 groups.py members <group_id>
    python3 groups.py kick <group_id> <user_id>
    python3 groups.py leave <group_id>
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
#  FONCTIONS GROUPES
# ═══════════════════════════════════════════════════════════════

def create_group(name):
    """Crée un nouveau groupe.

    Args:
        name: Nom du groupe

    Returns:
        dict: Résultat de l'API avec group_id
    """
    token = _ensure_authenticated()

    data = {"name": name}

    return _http_request("POST", "/api/groups/create", data, token)


def invite_member(group_id, user_id):
    """Invite un membre dans le groupe.

    Args:
        group_id: ID du groupe
        user_id: User ID à inviter

    Returns:
        dict: Résultat de l'API
    """
    token = _ensure_authenticated()

    data = {
        "group_id": group_id,
        "user_id": user_id
    }

    return _http_request("POST", "/api/groups/invite", data, token)


def join_group(group_id):
    """Rejoint un groupe (après scan QR).

    Args:
        group_id: ID du groupe

    Returns:
        dict: Résultat de l'API
    """
    token = _ensure_authenticated()

    data = {"group_id": group_id}

    return _http_request("POST", "/api/groups/join", data, token)


def list_groups():
    """Liste tous les groupes dont je suis membre.

    Returns:
        dict: Résultat de l'API avec liste groupes
    """
    token = _ensure_authenticated()

    return _http_request("GET", "/api/groups/list", token=token)


def list_members(group_id):
    """Liste les membres d'un groupe.

    Args:
        group_id: ID du groupe

    Returns:
        dict: Résultat de l'API avec liste membres
    """
    token = _ensure_authenticated()

    return _http_request("GET", f"/api/groups/members?group_id={group_id}", token=token)


def kick_member(group_id, user_id):
    """Expulse un membre du groupe (admin uniquement).

    Args:
        group_id: ID du groupe
        user_id: User ID à expulser

    Returns:
        dict: Résultat de l'API
    """
    token = _ensure_authenticated()

    data = {
        "group_id": group_id,
        "user_id": user_id
    }

    return _http_request("DELETE", "/api/groups/kick", data, token)


def leave_group(group_id):
    """Quitte un groupe.

    Args:
        group_id: ID du groupe

    Returns:
        dict: Résultat de l'API
    """
    token = _ensure_authenticated()

    data = {"group_id": group_id}

    return _http_request("DELETE", "/api/groups/leave", data, token)


# ═══════════════════════════════════════════════════════════════
#  COMMANDES CLI
# ═══════════════════════════════════════════════════════════════

def cmd_create(args):
    """Commande : créer groupe."""
    print(f"=== Créer groupe ===")
    print(f"Nom: {args.name}\n")

    result = create_group(args.name)

    if result.get("success"):
        print(f"✅ Groupe créé !")
        print(f"   ID: {result['group_id']}")
        print(f"   Nom: {result['name']}")
        print(f"   Créé: {result['created_at']}")
        return 0
    else:
        print(f"❌ Erreur : {result.get('error', 'Unknown')}")
        return 1


def cmd_invite(args):
    """Commande : inviter membre."""
    print(f"=== Inviter membre ===")
    print(f"Groupe: {args.group_id}")
    print(f"User: {args.user_id}\n")

    result = invite_member(args.group_id, args.user_id)

    if result.get("success"):
        print(f"✅ Membre invité !")
        print(f"   User: {result['user_id']}")
        print(f"   Rejoint: {result['joined_at']}")
        return 0
    else:
        print(f"❌ Erreur : {result.get('error', 'Unknown')}")
        return 1


def cmd_join(args):
    """Commande : rejoindre groupe."""
    print(f"=== Rejoindre groupe ===")
    print(f"Groupe: {args.group_id}\n")

    result = join_group(args.group_id)

    if result.get("success"):
        print(f"✅ Groupe rejoint !")
        print(f"   Groupe: {result['group_id']}")
        print(f"   Rejoint: {result['joined_at']}")
        return 0
    else:
        print(f"❌ Erreur : {result.get('error', 'Unknown')}")
        return 1


def cmd_list(args):
    """Commande : lister groupes."""
    print(f"=== Mes groupes ===\n")

    result = list_groups()

    if result.get("success"):
        groups = result.get("groups", [])
        if not groups:
            print("Aucun groupe")
            return 0

        for g in groups:
            role_icon = "👑" if g["role"] == "admin" else "👤"
            print(f"{role_icon} {g['name']}")
            print(f"   ID: {g['group_id']}")
            print(f"   Propriétaire: {g['owner_user_id']}")
            print(f"   Rôle: {g['role']}")
            print(f"   Créé: {g['created_at']}")
            print()

        print(f"Total : {len(groups)} groupe(s)")
        return 0
    else:
        print(f"❌ Erreur : {result.get('error', 'Unknown')}")
        return 1


def cmd_members(args):
    """Commande : lister membres."""
    print(f"=== Membres du groupe {args.group_id} ===\n")

    result = list_members(args.group_id)

    if result.get("success"):
        members = result.get("members", [])
        if not members:
            print("Aucun membre")
            return 0

        for m in members:
            role_icon = "👑" if m["role"] == "admin" else "👤"
            print(f"{role_icon} {m['user_id']}")
            print(f"   Rôle: {m['role']}")
            print(f"   Rejoint: {m['joined_at']}")
            print()

        print(f"Total : {len(members)} membre(s)")
        return 0
    else:
        print(f"❌ Erreur : {result.get('error', 'Unknown')}")
        return 1


def cmd_kick(args):
    """Commande : expulser membre."""
    print(f"=== Expulser membre ===")
    print(f"Groupe: {args.group_id}")
    print(f"User: {args.user_id}\n")

    result = kick_member(args.group_id, args.user_id)

    if result.get("success"):
        print(f"✅ Membre expulsé !")
        print(f"   {result['message']}")
        return 0
    else:
        print(f"❌ Erreur : {result.get('error', 'Unknown')}")
        return 1


def cmd_leave(args):
    """Commande : quitter groupe."""
    print(f"=== Quitter groupe ===")
    print(f"Groupe: {args.group_id}\n")

    result = leave_group(args.group_id)

    if result.get("success"):
        print(f"✅ Groupe quitté !")
        print(f"   {result['message']}")
        return 0
    else:
        print(f"❌ Erreur : {result.get('error', 'Unknown')}")
        return 1


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Point d'entrée CLI."""
    parser = argparse.ArgumentParser(
        description="BIG_BOFF Search — Groups Client (Phase 7 P2P)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python3 groups.py create "Famille"
  python3 groups.py invite grp_abc123 bigboff_xyz789
  python3 groups.py list
  python3 groups.py members grp_abc123
  python3 groups.py kick grp_abc123 bigboff_xyz789
  python3 groups.py leave grp_abc123
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Commande")

    # create
    create_parser = subparsers.add_parser("create", help="Créer un nouveau groupe")
    create_parser.add_argument("name", help="Nom du groupe")

    # invite
    invite_parser = subparsers.add_parser("invite", help="Inviter un membre (admin uniquement)")
    invite_parser.add_argument("group_id", help="ID du groupe")
    invite_parser.add_argument("user_id", help="User ID à inviter")

    # join
    join_parser = subparsers.add_parser("join", help="Rejoindre un groupe (après QR)")
    join_parser.add_argument("group_id", help="ID du groupe")

    # list
    subparsers.add_parser("list", help="Lister mes groupes")

    # members
    members_parser = subparsers.add_parser("members", help="Lister membres d'un groupe")
    members_parser.add_argument("group_id", help="ID du groupe")

    # kick
    kick_parser = subparsers.add_parser("kick", help="Expulser un membre (admin uniquement)")
    kick_parser.add_argument("group_id", help="ID du groupe")
    kick_parser.add_argument("user_id", help="User ID à expulser")

    # leave
    leave_parser = subparsers.add_parser("leave", help="Quitter un groupe")
    leave_parser.add_argument("group_id", help="ID du groupe")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatcher
    commands = {
        "create": cmd_create,
        "invite": cmd_invite,
        "join": cmd_join,
        "list": cmd_list,
        "members": cmd_members,
        "kick": cmd_kick,
        "leave": cmd_leave
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        return cmd_func(args)
    else:
        print(f"❌ Commande inconnue : {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
