#!/usr/bin/env python3
"""
BIG_BOFF Search — Sync Client
Module client pour synchronisation avec relay server (Phase 2 P2P).

Usage:
    python3 sync.py register        # Enregistrer sur relay
    python3 sync.py auth            # Authentifier (obtenir JWT token)
    python3 sync.py pull            # Pull changements relay → local
    python3 sync.py push            # Push changements local → relay
    python3 sync.py status          # Afficher statut sync
"""

import argparse
import getpass
import json
import sqlite3
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# Import local
try:
    from identity import get_identity, sign_data
    from config import DB_PATH
except ImportError:
    print("❌ Erreur : modules identity.py et config.py requis")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

RELAY_URL = "http://127.0.0.1:8888"  # Local par défaut (VPS futur)
SYNC_STATE_PATH = Path.home() / ".bigboff" / "sync_state.json"
TOKEN_EXPIRATION_BUFFER = 300  # 5 min avant expiration, re-auth


# ═══════════════════════════════════════════════════════════════
#  HELPERS SYNC STATE
# ═══════════════════════════════════════════════════════════════

def _load_sync_state():
    """Charge l'état de sync depuis sync_state.json."""
    if not SYNC_STATE_PATH.exists():
        return {
            "relay_url": RELAY_URL,
            "registered": False,
            "jwt_token": None,
            "token_expires_at": None,
            "last_sync_timestamp": "1970-01-01T00:00:00"
        }

    try:
        return json.loads(SYNC_STATE_PATH.read_text())
    except Exception as e:
        print(f"⚠️  Erreur lecture sync_state.json : {e}")
        return _load_sync_state.__defaults__[0]


def _save_sync_state(state):
    """Sauvegarde l'état de sync dans sync_state.json."""
    SYNC_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYNC_STATE_PATH.write_text(json.dumps(state, indent=2))
    SYNC_STATE_PATH.chmod(0o600)


# ═══════════════════════════════════════════════════════════════
#  HELPERS HTTP
# ═══════════════════════════════════════════════════════════════

def _http_request(method, endpoint, data=None, token=None):
    """Requête HTTP vers relay server."""
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
            error_json = json.loads(error_body)
            return error_json
        except:
            return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════════════

def sync_register(password=None):
    """Enregistre l'identité locale sur le relay server.

    Returns:
        bool: True si succès, False sinon
    """
    print("=== Enregistrement sur relay ===")

    # Récupérer identité locale
    identity = get_identity()
    if not identity:
        print("❌ Identité locale non trouvée")
        print("   Créer une identité : python3 identity.py init")
        return False

    # Préparer données
    data = {
        "user_id": identity["user_id"],
        "alias": identity.get("alias", ""),
        "public_key_rsa": identity["keys"]["rsa"]["public_key"],
        "public_key_ed25519": identity["keys"]["ed25519"]["public_key"]
    }

    print(f"User ID: {identity['user_id']}")
    print(f"Alias: {data['alias'] or '(non défini)'}")
    print(f"Relay: {RELAY_URL}\n")

    # Envoyer au relay
    result = _http_request("POST", "/api/auth/register", data)

    if result.get("success"):
        status = result.get("status", "registered")
        if status == "already_registered":
            print(f"✅ Déjà enregistré : {identity['user_id']}")
        else:
            print(f"✅ Enregistrement réussi : {identity['user_id']}")

        # Sauvegarder état
        state = _load_sync_state()
        state["registered"] = True
        state["relay_url"] = RELAY_URL
        _save_sync_state(state)

        return True
    else:
        print(f"❌ Erreur : {result.get('error', 'Unknown error')}")
        return False


def sync_authenticate(password=None):
    """Authentification challenge/response → JWT token.

    Args:
        password: Mot de passe si identité protégée

    Returns:
        str: JWT token si succès, None sinon
    """
    print("=== Authentification relay ===")

    # Vérifier enregistrement
    state = _load_sync_state()
    if not state.get("registered"):
        print("❌ Pas encore enregistré sur relay")
        print("   Exécuter : python3 sync.py register")
        return None

    identity = get_identity()
    if not identity:
        print("❌ Identité locale non trouvée")
        return None

    user_id = identity["user_id"]

    # Étape 1 : Demander challenge
    print("1. Demande challenge...")
    challenge_result = _http_request("POST", "/api/auth/challenge", {"user_id": user_id})

    if not challenge_result.get("success"):
        print(f"❌ Erreur challenge : {challenge_result.get('error')}")
        return None

    challenge_id = challenge_result["challenge_id"]
    challenge = challenge_result["challenge"]
    expires_in = challenge_result["expires_in"]
    print(f"   ✓ Challenge reçu (expire dans {expires_in}s)")

    # Étape 2 : Signer challenge
    print("2. Signature challenge...")

    # Demander mot de passe si nécessaire
    if password is None and identity.get("protection", {}).get("enabled"):
        password = getpass.getpass("   Mot de passe: ")

    try:
        signature = sign_data(challenge, key_type="ed25519", password=password)
        print("   ✓ Signature générée")
    except Exception as e:
        print(f"   ❌ Erreur signature : {e}")
        return None

    # Étape 3 : Vérifier signature → JWT
    print("3. Vérification signature...")
    verify_result = _http_request("POST", "/api/auth/verify", {
        "challenge_id": challenge_id,
        "signature": signature
    })

    if not verify_result.get("success"):
        print(f"   ❌ Erreur verify : {verify_result.get('error')}")
        return None

    token = verify_result["token"]
    expires_in = verify_result["expires_in"]
    print(f"   ✓ JWT token reçu (valide {expires_in // 3600}h)")

    # Sauvegarder token
    state["jwt_token"] = token
    state["token_expires_at"] = time.time() + expires_in
    _save_sync_state(state)

    print(f"\n✅ Authentification réussie")
    return token


def _get_valid_token(password=None):
    """Récupère un token JWT valide (cache ou ré-auth).

    Args:
        password: Mot de passe si identité protégée

    Returns:
        str: JWT token valide, None si échec
    """
    state = _load_sync_state()
    token = state.get("jwt_token")
    expires_at = state.get("token_expires_at")

    # Vérifier si token encore valide
    if token and expires_at:
        remaining = expires_at - time.time()
        if remaining > TOKEN_EXPIRATION_BUFFER:
            return token

    # Token expiré ou absent, ré-authentifier
    print("⏰ Token expiré, ré-authentification...")
    return sync_authenticate(password)


# ═══════════════════════════════════════════════════════════════
#  SYNC
# ═══════════════════════════════════════════════════════════════

def sync_pull(password=None):
    """Pull changements relay → local.

    Args:
        password: Mot de passe si identité protégée

    Returns:
        bool: True si succès
    """
    print("=== Pull changements (relay → local) ===")

    # Obtenir token valide
    token = _get_valid_token(password)
    if not token:
        print("❌ Authentification échouée")
        return False

    # Récupérer dernier timestamp sync
    state = _load_sync_state()
    since = state.get("last_sync_timestamp", "1970-01-01T00:00:00")
    print(f"📥 Pull depuis {since}...")

    # Requête changements
    result = _http_request(
        "GET",
        f"/api/sync/changes?since={urllib.parse.quote(since)}",
        token=token
    )

    if not result.get("success"):
        print(f"❌ Erreur pull : {result.get('error')}")
        return False

    changes = result.get("changes", [])
    count = len(changes)

    if count == 0:
        print("✓ Aucun changement à récupérer")
        return True

    print(f"📦 {count} changement(s) récupéré(s)")

    # Appliquer changements
    applied = _apply_remote_changes(changes)
    print(f"✅ {applied} changement(s) appliqué(s)")

    # Mettre à jour timestamp
    if changes:
        last_timestamp = max(c["timestamp"] for c in changes)
        state["last_sync_timestamp"] = last_timestamp
        _save_sync_state(state)

    return True


def sync_push(password=None):
    """Push changements local → relay.

    Args:
        password: Mot de passe si identité protégée

    Returns:
        bool: True si succès
    """
    print("=== Push changements (local → relay) ===")

    # Obtenir token valide
    token = _get_valid_token(password)
    if not token:
        print("❌ Authentification échouée")
        return False

    # Récupérer changements locaux
    state = _load_sync_state()
    since = state.get("last_sync_timestamp", "1970-01-01T00:00:00")
    changes = _get_local_changes_since(since)

    if not changes:
        print("✓ Aucun changement local à pousser")
        return True

    print(f"📤 Push {len(changes)} changement(s)...")

    # Envoyer au relay
    result = _http_request(
        "POST",
        "/api/sync/push",
        {"changes": changes},
        token=token
    )

    if not result.get("success"):
        print(f"❌ Erreur push : {result.get('error')}")
        return False

    pushed = result.get("pushed", 0)
    print(f"✅ {pushed} changement(s) poussé(s)")

    return True


# ═══════════════════════════════════════════════════════════════
#  DB HELPERS
# ═══════════════════════════════════════════════════════════════

def _get_local_changes_since(timestamp):
    """Récupère changements locaux depuis timestamp.

    Phase 2 : Retourne [] (sync unidirectionnel relay → client)

    Args:
        timestamp: ISO timestamp depuis lequel récupérer changements

    Returns:
        List[Dict]: Liste de changements
    """
    # TODO Phase 2 : Sync unidirectionnel seulement (relay → client)
    # Phase 3 : Implémenter détection changements locaux
    return []


def _apply_remote_changes(changes):
    """Applique changements distants à la DB locale.

    Args:
        changes: Liste de changements [{entity_type, entity_id, action, data}, ...]

    Returns:
        int: Nombre de changements appliqués
    """
    if not changes:
        return 0

    # TODO Phase 2 : Implémenter application changements
    # Pour l'instant, juste afficher
    for change in changes:
        entity_type = change.get("entity_type")
        entity_id = change.get("entity_id")
        action = change.get("action")
        user_id = change.get("user_id")
        timestamp = change.get("timestamp")

        print(f"  • [{action}] {entity_type}#{entity_id} par {user_id[:16]}... ({timestamp})")

    # Phase 3 : Vraie implémentation avec sqlite
    # conn = sqlite3.connect(DB_PATH)
    # c = conn.cursor()
    # for change in changes:
    #     if change["action"] == "create":
    #         # INSERT INTO ...
    #     elif change["action"] == "update":
    #         # UPDATE ...
    #     elif change["action"] == "delete":
    #         # DELETE ...
    # conn.commit()
    # conn.close()

    return len(changes)


# ═══════════════════════════════════════════════════════════════
#  CONSULTATION (Phase 5)
# ═══════════════════════════════════════════════════════════════

def sync_consult_query(owner_user_id, scope_type, scope_value, search_query="", password=None):
    """Interroger données de owner via relay (mode consultation).

    Args:
        owner_user_id: User ID du propriétaire (ex: "bigboff_...")
        scope_type: "tag", "item", "all"
        scope_value: Nom du tag ou item_id
        search_query: Recherche texte optionnelle
        password: Mot de passe pour déverrouiller clés (si protégé)

    Returns:
        List[Dict] : Snapshots récupérés
    """
    # 1. Récupérer token valide
    token = _get_valid_token(password)
    if not token:
        print("❌ Authentification requise")
        return []

    # 2. Construire URL
    state = _load_sync_state()
    relay_url = state.get("relay_url", RELAY_URL)

    params = {
        "owner_user_id": owner_user_id,
        "scope_type": scope_type,
        "scope_value": scope_value
    }
    if search_query:
        params["q"] = search_query

    query_string = urllib.parse.urlencode(params)
    url = f"{relay_url}/api/consult/query?{query_string}"

    # 3. HTTP GET
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())

            if not result.get("success"):
                error = result.get("error", "Erreur inconnue")
                reason = result.get("reason", "")
                if reason:
                    print(f"❌ Erreur : {error} ({reason})")
                else:
                    print(f"❌ Erreur : {error}")
                return []

            results = result.get("results", [])
            print(f"✅ {len(results)} éléments récupérés")
            return results

    except urllib.error.HTTPError as e:
        print(f"❌ Erreur HTTP {e.code} : {e.reason}")
        return []
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return []


def sync_consult_apply(results, source_user_id):
    """Appliquer snapshots consultés au cache local.

    Args:
        results: Liste de snapshots depuis sync_consult_query()
        source_user_id: User ID du propriétaire (pour colonne source_user_id)

    Returns:
        int : Nombre d'éléments appliqués
    """
    if not results:
        print("ℹ️  Aucun élément à appliquer")
        return 0

    # 1. Connexion DB locale (via config_loader)
    try:
        from config_loader import get_db_path
        db_path = get_db_path()
    except ImportError:
        print("⚠️  config_loader non disponible, utilisation chemin par défaut")
        db_path = Path.home().parent / "Dropbox" / "____BIG_BOFF___" / "TOOLS" / "MAINTENANCE" / "catalogue.db"

    if not Path(db_path).exists():
        print(f"❌ Base de données non trouvée : {db_path}")
        return 0

    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    applied = 0
    for snapshot in results:
        entity_type = snapshot["entity_type"]
        entity_id = snapshot["entity_id"]
        data = snapshot["data"]
        fetched_at = snapshot["fetched_at"]

        # 2. Appliquer selon entity_type
        if entity_type == "item":
            # Insérer/Update dans items avec source_user_id
            try:
                c.execute("""
                    INSERT OR REPLACE INTO items
                    (id, nom, extension, chemin, chemin_relatif, taille, date_modif, est_dossier, source_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    data.get("nom", ""),
                    data.get("extension", ""),
                    data.get("chemin", ""),
                    data.get("chemin_relatif", ""),
                    data.get("taille", 0),
                    data.get("date_modif", ""),
                    data.get("est_dossier", 0),
                    source_user_id
                ))

                # Tags associés
                tags = data.get("tags", [])
                for tag in tags:
                    c.execute("""
                        INSERT OR IGNORE INTO tags (item_id, tag)
                        VALUES (?, ?)
                    """, (entity_id, tag))

                applied += 1
            except Exception as e:
                print(f"⚠️  Erreur apply item {entity_id} : {e}")

        elif entity_type == "contact":
            # Insérer/Update dans contacts avec source_user_id
            try:
                c.execute("""
                    INSERT OR REPLACE INTO contacts
                    (id, nom, prenom, type, telephones, emails, date_naissance, source_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    data.get("nom", ""),
                    data.get("prenom", ""),
                    data.get("type", "personne"),
                    data.get("telephones", "[]"),
                    data.get("emails", "[]"),
                    data.get("date_naissance", ""),
                    source_user_id
                ))
                applied += 1
            except Exception as e:
                print(f"⚠️  Erreur apply contact {entity_id} : {e}")

        elif entity_type == "lieu":
            # Insérer/Update dans lieux avec source_user_id
            try:
                c.execute("""
                    INSERT OR REPLACE INTO lieux
                    (id, nom, adresse, description, source_user_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    data.get("nom", ""),
                    data.get("adresse", ""),
                    data.get("description", ""),
                    source_user_id
                ))
                applied += 1
            except Exception as e:
                print(f"⚠️  Erreur apply lieu {entity_id} : {e}")

        elif entity_type == "event":
            # Insérer/Update dans events avec source_user_id
            try:
                c.execute("""
                    INSERT OR REPLACE INTO events
                    (id, title, date, time, description, source_user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    data.get("title", ""),
                    data.get("date", ""),
                    data.get("time", ""),
                    data.get("description", ""),
                    source_user_id
                ))
                applied += 1
            except Exception as e:
                print(f"⚠️  Erreur apply event {entity_id} : {e}")

    conn.commit()
    conn.close()

    print(f"✅ {applied} éléments appliqués au cache local")
    return applied


# ═══════════════════════════════════════════════════════════════
#  PHASE 6 — MODE PARTAGE (Clone permanent + Sync continu)
# ═══════════════════════════════════════════════════════════════

def sync_share_clone(owner_user_id, scope_type, scope_value, password=None):
    """Clone initial : récupérer tous les éléments partagés (mode partage).

    Args:
        owner_user_id: User ID du propriétaire
        scope_type: "tag", "item", "all"
        scope_value: Nom du tag ou item_id
        password: Mot de passe pour déverrouiller clés

    Returns:
        List[Dict] : Snapshots récupérés
    """
    # 1. Récupérer token valide
    token = _get_valid_token(password)
    if not token:
        print("❌ Authentification requise")
        return []

    # 2. Construire requête POST
    state = _load_sync_state()
    relay_url = state.get("relay_url", RELAY_URL)
    url = f"{relay_url}/api/share/clone"

    payload = {
        "owner_user_id": owner_user_id,
        "scope_type": scope_type,
        "scope_value": scope_value
    }

    # 3. HTTP POST
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())

            if not result.get("success"):
                error = result.get("error", "Erreur inconnue")
                reason = result.get("reason", "")
                if reason:
                    print(f"❌ Erreur : {error} ({reason})")
                else:
                    print(f"❌ Erreur : {error}")
                return []

            snapshots = result.get("snapshots", [])
            print(f"✅ {len(snapshots)} éléments récupérés (clone partage)")
            return snapshots

    except urllib.error.HTTPError as e:
        print(f"❌ Erreur HTTP {e.code} : {e.reason}")
        return []
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return []


def sync_share_apply(snapshots, source_user_id):
    """Appliquer snapshots partagés au clone local permanent.

    Args:
        snapshots: Liste de snapshots depuis sync_share_clone()
        source_user_id: User ID du propriétaire

    Returns:
        int : Nombre d'éléments appliqués
    """
    if not snapshots:
        print("ℹ️  Aucun élément à appliquer")
        return 0

    # 1. Connexion DB locale
    try:
        from config_loader import get_db_path
        db_path = get_db_path()
    except ImportError:
        print("⚠️  config_loader non disponible, utilisation chemin par défaut")
        db_path = Path.home().parent / "Dropbox" / "____BIG_BOFF___" / "TOOLS" / "MAINTENANCE" / "catalogue.db"

    if not Path(db_path).exists():
        print(f"❌ Base de données non trouvée : {db_path}")
        return 0

    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    applied = 0
    for snapshot in snapshots:
        entity_type = snapshot["entity_type"]
        entity_id = snapshot["entity_id"]
        data = snapshot["data"]
        is_shared_copy = snapshot.get("is_shared_copy", 1)  # Force 1 pour partage

        # 2. Appliquer selon entity_type avec is_shared_copy=1
        if entity_type == "item":
            try:
                c.execute("""
                    INSERT OR REPLACE INTO items
                    (id, nom, extension, chemin, chemin_relatif, taille, date_modif, est_dossier, source_user_id, is_shared_copy)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    data.get("nom", ""),
                    data.get("extension", ""),
                    data.get("chemin", ""),
                    data.get("chemin_relatif", ""),
                    data.get("taille", 0),
                    data.get("date_modif", ""),
                    data.get("est_dossier", 0),
                    source_user_id,
                    is_shared_copy
                ))

                # Tags associés
                tags = data.get("tags", [])
                for tag in tags:
                    c.execute("""
                        INSERT OR IGNORE INTO tags (item_id, tag)
                        VALUES (?, ?)
                    """, (entity_id, tag))

                applied += 1
            except Exception as e:
                print(f"⚠️  Erreur apply item {entity_id} : {e}")

        elif entity_type == "contact":
            try:
                c.execute("""
                    INSERT OR REPLACE INTO contacts
                    (id, nom, prenom, type, telephones, emails, date_naissance, source_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    data.get("nom", ""),
                    data.get("prenom", ""),
                    data.get("type", "personne"),
                    data.get("telephones", "[]"),
                    data.get("emails", "[]"),
                    data.get("date_naissance", ""),
                    source_user_id
                ))
                applied += 1
            except Exception as e:
                print(f"⚠️  Erreur apply contact {entity_id} : {e}")

        elif entity_type == "lieu":
            try:
                c.execute("""
                    INSERT OR REPLACE INTO lieux
                    (id, nom, adresse, description, source_user_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    data.get("nom", ""),
                    data.get("adresse", ""),
                    data.get("description", ""),
                    source_user_id
                ))
                applied += 1
            except Exception as e:
                print(f"⚠️  Erreur apply lieu {entity_id} : {e}")

        elif entity_type == "event":
            try:
                c.execute("""
                    INSERT OR REPLACE INTO events
                    (id, title, date, time, description, source_user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    data.get("title", ""),
                    data.get("date", ""),
                    data.get("time", ""),
                    data.get("description", ""),
                    source_user_id
                ))
                applied += 1
            except Exception as e:
                print(f"⚠️  Erreur apply event {entity_id} : {e}")

    conn.commit()
    conn.close()

    # 3. Sauvegarder last_share_sync
    now = datetime.utcnow().isoformat() + "Z"
    state = _load_sync_state()
    if "last_share_sync" not in state:
        state["last_share_sync"] = {}
    if source_user_id not in state["last_share_sync"]:
        state["last_share_sync"][source_user_id] = {}

    scope_key = f"{snapshots[0]['scope_type']}:{snapshots[0]['scope_value']}" if snapshots else "unknown"
    state["last_share_sync"][source_user_id][scope_key] = now
    _save_sync_state(state)

    print(f"✅ {applied} éléments appliqués (clone permanent)")
    return applied


def sync_share_sync(owner_user_id, password=None):
    """Sync continu : récupérer changements depuis last_sync (mode partage).

    Args:
        owner_user_id: User ID du propriétaire
        password: Mot de passe pour déverrouiller clés

    Returns:
        int : Nombre d'éléments synchronisés
    """
    # 1. Récupérer token valide
    token = _get_valid_token(password)
    if not token:
        print("❌ Authentification requise")
        return 0

    # 2. Récupérer last_share_sync
    state = _load_sync_state()
    relay_url = state.get("relay_url", RELAY_URL)

    last_syncs = state.get("last_share_sync", {}).get(owner_user_id, {})
    if not last_syncs:
        print(f"ℹ️  Aucun partage trouvé pour {owner_user_id}")
        print("   Utilisez d'abord : python3 sync.py share clone <owner> <scope_type> <scope_value>")
        return 0

    total_synced = 0

    # 3. Pour chaque scope partagé, sync incrémental
    for scope_key, last_sync in last_syncs.items():
        print(f"\n🔄 Sync {scope_key}...")

        params = {
            "owner_user_id": owner_user_id,
            "since": last_sync
        }
        query_string = urllib.parse.urlencode(params)
        url = f"{relay_url}/api/share/sync?{query_string}"

        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {token}")

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())

                if not result.get("success"):
                    error = result.get("error", "Erreur inconnue")
                    reason = result.get("reason", "")
                    if reason:
                        print(f"❌ Erreur : {error} ({reason})")
                    else:
                        print(f"❌ Erreur : {error}")
                    continue

                changes = result.get("changes", [])
                if changes:
                    # Appliquer changements
                    applied = sync_share_apply(changes, owner_user_id)
                    total_synced += applied
                else:
                    print("✅ Déjà à jour")

        except urllib.error.HTTPError as e:
            print(f"❌ Erreur HTTP {e.code} : {e.reason}")
        except Exception as e:
            print(f"❌ Erreur : {e}")

    return total_synced


# ═══════════════════════════════════════════════════════════════
#  COMMANDES CLI
# ═══════════════════════════════════════════════════════════════

def cmd_register(args):
    """Commande : enregistrer sur relay."""
    return 0 if sync_register() else 1


def cmd_auth(args):
    """Commande : authentifier."""
    token = sync_authenticate()
    return 0 if token else 1


def cmd_pull(args):
    """Commande : pull changements."""
    return 0 if sync_pull() else 1


def cmd_push(args):
    """Commande : push changements."""
    return 0 if sync_push() else 1


def cmd_status(args):
    """Commande : afficher statut sync."""
    print("=== Statut Sync ===")

    # Identité locale
    identity = get_identity()
    if identity:
        print(f"User ID: {identity['user_id']}")
        print(f"Alias: {identity.get('alias', '(non défini)')}")
    else:
        print("❌ Identité locale non trouvée")
        return 1

    # État sync
    state = _load_sync_state()
    print(f"\nRelay URL: {state.get('relay_url', RELAY_URL)}")
    print(f"Enregistré: {'✅ Oui' if state.get('registered') else '❌ Non'}")

    # Token
    token = state.get("jwt_token")
    expires_at = state.get("token_expires_at")
    if token and expires_at:
        remaining = expires_at - time.time()
        if remaining > 0:
            print(f"Token JWT: ✅ Valide ({int(remaining // 3600)}h {int((remaining % 3600) // 60)}m restantes)")
        else:
            print(f"Token JWT: ⏰ Expiré")
    else:
        print(f"Token JWT: ❌ Absent")

    # Dernier sync
    last_sync = state.get("last_sync_timestamp", "Jamais")
    print(f"Dernier sync: {last_sync}")

    return 0


def cmd_consult(args):
    """Commande : consulter données d'un user."""
    owner_user_id = args.owner_user_id
    scope_type = args.scope_type
    scope_value = args.scope_value
    search_query = args.query or ""

    print(f"=== Consultation de {owner_user_id} ===")
    print(f"Scope: {scope_type}:{scope_value}")
    if search_query:
        print(f"Recherche: {search_query}")
    print()

    # Récupérer snapshots
    results = sync_consult_query(owner_user_id, scope_type, scope_value, search_query)

    if results:
        # Appliquer au cache local
        applied = sync_consult_apply(results, owner_user_id)
        print(f"\n✅ Consultation terminée : {applied} éléments")
        return 0
    else:
        print("ℹ️  Aucun élément trouvé")
        return 1


def cmd_share_clone(args):
    """Commande : cloner données partagées (mode partage)."""
    owner_user_id = args.owner_user_id
    scope_type = args.scope_type
    scope_value = args.scope_value

    print(f"=== Clone Partage de {owner_user_id} ===")
    print(f"Scope: {scope_type}:{scope_value}")
    print()

    # Clone initial
    snapshots = sync_share_clone(owner_user_id, scope_type, scope_value)

    if snapshots:
        # Appliquer au clone local permanent
        applied = sync_share_apply(snapshots, owner_user_id)
        print(f"\n✅ Clone terminé : {applied} éléments (permanent)")
        return 0
    else:
        print("ℹ️  Aucun élément trouvé")
        return 1


def cmd_share_sync(args):
    """Commande : synchroniser partages existants."""
    owner_user_id = args.owner_user_id if hasattr(args, 'owner_user_id') else None

    if owner_user_id:
        print(f"=== Sync Partage de {owner_user_id} ===\n")
        synced = sync_share_sync(owner_user_id)
    else:
        # Sync tous les partages
        print("=== Sync Tous Partages ===\n")
        state = _load_sync_state()
        last_share_sync = state.get("last_share_sync", {})

        if not last_share_sync:
            print("ℹ️  Aucun partage configuré")
            return 1

        total_synced = 0
        for owner in last_share_sync.keys():
            print(f"\n📡 Sync {owner}...")
            synced = sync_share_sync(owner)
            total_synced += synced

        synced = total_synced

    if synced > 0:
        print(f"\n✅ Sync terminé : {synced} éléments mis à jour")
        return 0
    else:
        print("\n✅ Tous les partages sont à jour")
        return 0


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Point d'entrée CLI."""
    parser = argparse.ArgumentParser(
        description="BIG_BOFF Search — Sync Client (Phase 2-6 P2P)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python3 sync.py register        # Enregistrer sur relay
  python3 sync.py auth            # Authentifier (obtenir JWT)
  python3 sync.py pull            # Pull changements
  python3 sync.py push            # Push changements
  python3 sync.py status          # Afficher statut
  python3 sync.py consult bigboff_abc123 tag notes    # Consulter données d'un user (Phase 5)
  python3 sync.py share clone bigboff_abc123 tag recettes    # Clone partage (Phase 6)
  python3 sync.py share sync      # Sync tous les partages (Phase 6)
  python3 sync.py share sync bigboff_abc123    # Sync partage d'un user spécifique
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Commande")

    # Sous-commandes
    subparsers.add_parser("register", help="Enregistrer identité sur relay")
    subparsers.add_parser("auth", help="Authentifier et obtenir JWT token")
    subparsers.add_parser("pull", help="Pull changements relay → local")
    subparsers.add_parser("push", help="Push changements local → relay")
    subparsers.add_parser("status", help="Afficher statut sync")

    # Commande consult (Phase 5)
    consult_parser = subparsers.add_parser("consult", help="Consulter données d'un user (Phase 5)")
    consult_parser.add_argument("owner_user_id", help="User ID du propriétaire (ex: bigboff_abc123)")
    consult_parser.add_argument("scope_type", choices=["tag", "item", "all"], help="Type de scope")
    consult_parser.add_argument("scope_value", help="Valeur du scope (nom du tag ou item_id)")
    consult_parser.add_argument("-q", "--query", help="Recherche texte optionnelle")

    # Commande share (Phase 6)
    share_parser = subparsers.add_parser("share", help="Partage permanent (Phase 6)")
    share_subparsers = share_parser.add_subparsers(dest="share_action", help="Action partage")

    # share clone
    share_clone_parser = share_subparsers.add_parser("clone", help="Clone initial (mode partage)")
    share_clone_parser.add_argument("owner_user_id", help="User ID du propriétaire")
    share_clone_parser.add_argument("scope_type", choices=["tag", "item", "all"], help="Type de scope")
    share_clone_parser.add_argument("scope_value", help="Valeur du scope")

    # share sync
    share_sync_parser = share_subparsers.add_parser("sync", help="Sync continu des partages")
    share_sync_parser.add_argument("owner_user_id", nargs="?", help="User ID optionnel (sinon sync tous)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatcher
    commands = {
        "register": cmd_register,
        "auth": cmd_auth,
        "pull": cmd_pull,
        "push": cmd_push,
        "status": cmd_status,
        "consult": cmd_consult,
        "share": lambda a: cmd_share_clone(a) if a.share_action == "clone" else cmd_share_sync(a)
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        return cmd_func(args)
    else:
        print(f"❌ Commande inconnue : {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
