#!/usr/bin/env python3
"""
BIG_BOFF Search — Relay Server
Phase 2 P2P : Serveur relay pour synchronisation entre utilisateurs.

Auth : Challenge/response avec signature Ed25519 (pas de login/password)
Sync : Différentielle timestamp-based (last-write-wins)
DB : ~/.bigboff/relay.db (users, challenges, sync_log)
"""

import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

try:
    import jwt
except ImportError:
    print("❌ Erreur : PyJWT non installé")
    print("   Exécuter : pip install PyJWT>=2.8.0")
    raise

# Import identity pour vérification signatures
try:
    from identity import verify_signature
except ImportError:
    print("❌ Erreur : module identity.py non trouvé")
    print("   Vérifier que identity.py existe dans le même dossier")
    raise


# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

RELAY_DB_PATH = Path.home() / ".bigboff" / "relay.db"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
CHALLENGE_EXPIRATION_SECONDS = 60
PORT = 8888
HOST = "127.0.0.1"

# JWT Secret (env var ou génération auto)
_JWT_SECRET = None

def _get_jwt_secret():
    """Récupère ou génère JWT secret."""
    global _JWT_SECRET
    if _JWT_SECRET:
        return _JWT_SECRET

    # Env var prioritaire
    env_secret = os.environ.get("JWT_SECRET")
    if env_secret:
        _JWT_SECRET = env_secret
        return _JWT_SECRET

    # Sinon générer et sauvegarder
    secret_file = Path.home() / ".bigboff" / ".jwt_secret"
    if secret_file.exists():
        _JWT_SECRET = secret_file.read_text().strip()
    else:
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        _JWT_SECRET = secrets.token_urlsafe(32)
        secret_file.write_text(_JWT_SECRET)
        secret_file.chmod(0o600)

    return _JWT_SECRET


# ═══════════════════════════════════════════════════════════════
#  HELPERS DATABASE
# ═══════════════════════════════════════════════════════════════

def get_relay_db():
    """Connexion relay database."""
    if not RELAY_DB_PATH.exists():
        setup_relay_db()

    conn = sqlite3.connect(str(RELAY_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def setup_relay_db():
    """Initialise tables relay (users, challenges, sync_log)."""
    RELAY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(RELAY_DB_PATH))
    c = conn.cursor()

    # Table users (registry identités)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            alias TEXT,
            public_key_rsa TEXT,
            public_key_ed25519 TEXT,
            registered_at TEXT,
            last_seen TEXT
        )
    """)

    # Table challenges (anti-replay)
    c.execute("""
        CREATE TABLE IF NOT EXISTS challenges (
            challenge_id TEXT PRIMARY KEY,
            user_id TEXT,
            challenge TEXT,
            created_at TEXT,
            expires_at TEXT,
            used INTEGER DEFAULT 0
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_challenges_expires ON challenges(expires_at)")

    # Table sync_log (changements différentiels)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            data TEXT,
            UNIQUE(user_id, entity_type, entity_id, timestamp)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_sync_user_ts ON sync_log(user_id, timestamp)")

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
#  HELPERS JWT
# ═══════════════════════════════════════════════════════════════

def _generate_id():
    """Génère ID aléatoire (16 hex chars)."""
    return secrets.token_hex(8)


def _create_jwt_token(user_id: str) -> str:
    """Crée JWT token avec expiration 24h."""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)


def _verify_jwt_token(token: str) -> str | None:
    """Vérifie JWT token → user_id ou None."""
    try:
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ═══════════════════════════════════════════════════════════════
#  ROUTE HANDLERS — AUTH
# ═══════════════════════════════════════════════════════════════

def handle_auth_register(handler, data):
    """
    POST /api/auth/register
    Body: {"user_id": "bigboff_...", "alias": "...", "public_key_rsa": "...", "public_key_ed25519": "..."}
    Response: {"success": true, "user_id": "..."}
    """
    required = ["user_id", "public_key_rsa", "public_key_ed25519"]
    if not all(k in data for k in required):
        return {"success": False, "error": "Missing required fields"}

    user_id = data["user_id"]
    alias = data.get("alias", "")
    public_key_rsa = data["public_key_rsa"]
    public_key_ed25519 = data["public_key_ed25519"]

    # Vérifier format user_id
    if not user_id.startswith("bigboff_") or len(user_id) != 24:
        return {"success": False, "error": "Invalid user_id format"}

    conn = get_relay_db()
    c = conn.cursor()

    # Vérifier si déjà enregistré
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    existing = c.fetchone()

    if existing:
        # Mettre à jour last_seen
        c.execute(
            "UPDATE users SET last_seen = ? WHERE user_id = ?",
            (datetime.utcnow().isoformat(), user_id)
        )
        conn.commit()
        conn.close()
        return {"success": True, "user_id": user_id, "status": "already_registered"}

    # Enregistrer nouveau user
    now = datetime.utcnow().isoformat()
    c.execute(
        """INSERT INTO users (user_id, alias, public_key_rsa, public_key_ed25519, registered_at, last_seen)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, alias, public_key_rsa, public_key_ed25519, now, now)
    )
    conn.commit()
    conn.close()

    return {"success": True, "user_id": user_id, "status": "registered"}


def handle_auth_challenge(handler, data):
    """
    POST /api/auth/challenge
    Body: {"user_id": "bigboff_..."}
    Response: {"challenge_id": "...", "challenge": "base64...", "expires_in": 60}
    """
    user_id = data.get("user_id")
    if not user_id:
        return {"success": False, "error": "Missing user_id"}

    # Vérifier que user existe
    conn = get_relay_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        conn.close()
        return {"success": False, "error": "User not registered"}

    # Générer challenge aléatoire (32 bytes)
    challenge_bytes = secrets.token_bytes(32)
    challenge_b64 = base64.b64encode(challenge_bytes).decode()

    challenge_id = _generate_id()
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=CHALLENGE_EXPIRATION_SECONDS)

    # Stocker challenge
    c.execute(
        """INSERT INTO challenges (challenge_id, user_id, challenge, created_at, expires_at, used)
           VALUES (?, ?, ?, ?, ?, 0)""",
        (challenge_id, user_id, challenge_b64, now.isoformat(), expires_at.isoformat())
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "challenge_id": challenge_id,
        "challenge": challenge_b64,
        "expires_in": CHALLENGE_EXPIRATION_SECONDS
    }


def handle_auth_verify(handler, data):
    """
    POST /api/auth/verify
    Body: {"challenge_id": "...", "signature": "base64..."}
    Response: {"success": true, "token": "JWT...", "expires_in": 86400}
    """
    challenge_id = data.get("challenge_id")
    signature_b64 = data.get("signature")

    if not challenge_id or not signature_b64:
        return {"success": False, "error": "Missing challenge_id or signature"}

    conn = get_relay_db()
    c = conn.cursor()

    # Récupérer challenge
    c.execute(
        "SELECT user_id, challenge, expires_at, used FROM challenges WHERE challenge_id = ?",
        (challenge_id,)
    )
    row = c.fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": "Challenge not found"}

    user_id = row["user_id"]
    challenge = row["challenge"]
    expires_at_str = row["expires_at"]
    used = row["used"]

    # Vérifier expiration
    expires_at = datetime.fromisoformat(expires_at_str)
    if datetime.utcnow() > expires_at:
        conn.close()
        return {"success": False, "error": "Challenge expired"}

    # Vérifier anti-replay (pas déjà utilisé)
    if used:
        conn.close()
        return {"success": False, "error": "Challenge already used"}

    # Récupérer clé publique Ed25519
    c.execute("SELECT public_key_ed25519 FROM users WHERE user_id = ?", (user_id,))
    user_row = c.fetchone()
    if not user_row:
        conn.close()
        return {"success": False, "error": "User not found"}

    public_key = user_row["public_key_ed25519"]

    # Vérifier signature
    try:
        valid = verify_signature(challenge, signature_b64, public_key, key_type="ed25519")
    except Exception as e:
        conn.close()
        return {"success": False, "error": f"Signature verification failed: {str(e)}"}

    if not valid:
        conn.close()
        return {"success": False, "error": "Invalid signature"}

    # Marquer challenge comme utilisé
    c.execute("UPDATE challenges SET used = 1 WHERE challenge_id = ?", (challenge_id,))

    # Mettre à jour last_seen
    c.execute(
        "UPDATE users SET last_seen = ? WHERE user_id = ?",
        (datetime.utcnow().isoformat(), user_id)
    )

    conn.commit()
    conn.close()

    # Générer JWT token
    token = _create_jwt_token(user_id)

    return {
        "success": True,
        "token": token,
        "expires_in": JWT_EXPIRATION_HOURS * 3600
    }


# ═══════════════════════════════════════════════════════════════
#  ROUTE HANDLERS — SYNC
# ═══════════════════════════════════════════════════════════════

def handle_sync_changes(handler, params):
    """
    GET /api/sync/changes?since=<timestamp>
    Headers: Authorization: Bearer <JWT>
    Response: {"changes": [...], "count": N}
    """
    # Vérifier JWT
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing or invalid Authorization header"}

    token = auth_header[7:]  # Remove "Bearer "
    user_id = _verify_jwt_token(token)

    if not user_id:
        return {"success": False, "error": "Invalid or expired token"}

    # Récupérer paramètre since
    since = params.get("since", ["1970-01-01T00:00:00"])[0]

    conn = get_relay_db()
    c = conn.cursor()

    # Phase 3 : Récupérer permissions accordées au user
    c.execute(
        """SELECT owner_user_id, scope_type, scope_value, mode
           FROM permissions
           WHERE target_user_id = ? AND revoked_at IS NULL""",
        (user_id,)
    )
    permissions = c.fetchall()

    # Construire liste des users autorisés et leurs scopes
    allowed_sources = {}  # {owner_user_id: {scope_type: [scope_values]}}
    for perm in permissions:
        owner = perm["owner_user_id"]
        scope_type = perm["scope_type"]
        scope_value = perm["scope_value"]

        if owner not in allowed_sources:
            allowed_sources[owner] = {}
        if scope_type not in allowed_sources[owner]:
            allowed_sources[owner][scope_type] = []

        if scope_value:
            allowed_sources[owner][scope_type].append(scope_value)
        else:
            # scope_value NULL = all
            allowed_sources[owner][scope_type] = None

    # Récupérer changements depuis timestamp (tous users sauf soi-même)
    c.execute(
        """SELECT id, user_id, entity_type, entity_id, action, timestamp, data
           FROM sync_log
           WHERE timestamp > ? AND user_id != ?
           ORDER BY timestamp ASC
           LIMIT 1000""",
        (since, user_id)
    )

    rows = c.fetchall()
    conn.close()

    changes = []
    for row in rows:
        owner = row["user_id"]
        entity_type = row["entity_type"]
        entity_data = json.loads(row["data"]) if row["data"] else {}

        # Vérifier permissions
        if owner not in allowed_sources:
            continue  # Pas de permission pour ce owner

        owner_perms = allowed_sources[owner]

        # Vérifier scope_type 'all'
        if "all" in owner_perms:
            # Permission 'all' = accès à tout
            pass
        elif entity_type in owner_perms:
            # Permission pour ce type d'entité
            allowed_values = owner_perms[entity_type]
            if allowed_values is None:
                # Toutes les valeurs autorisées
                pass
            else:
                # Vérifier scope_value (ex: tag spécifique)
                # Pour l'instant, on suppose que entity_data contient les tags
                entity_tags = entity_data.get("tags", [])
                if not any(tag in allowed_values for tag in entity_tags):
                    continue  # Aucun tag autorisé
        else:
            continue  # Type d'entité non autorisé

        # Changement autorisé
        changes.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "entity_type": row["entity_type"],
            "entity_id": row["entity_id"],
            "action": row["action"],
            "timestamp": row["timestamp"],
            "data": entity_data
        })

    return {
        "success": True,
        "changes": changes,
        "count": len(changes)
    }


def handle_sync_push(handler, data):
    """
    POST /api/sync/push
    Headers: Authorization: Bearer <JWT>
    Body: {"changes": [{"entity_type": "tag", "entity_id": 123, "action": "create", "timestamp": "...", "data": {...}}, ...]}
    Response: {"success": true, "pushed": N}
    """
    # Vérifier JWT
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing or invalid Authorization header"}

    token = auth_header[7:]
    user_id = _verify_jwt_token(token)

    if not user_id:
        return {"success": False, "error": "Invalid or expired token"}

    changes = data.get("changes", [])
    if not changes:
        return {"success": True, "pushed": 0}

    conn = get_relay_db()
    c = conn.cursor()

    pushed_count = 0
    for change in changes:
        entity_type = change.get("entity_type")
        entity_id = change.get("entity_id")
        action = change.get("action")
        timestamp = change.get("timestamp")
        change_data = change.get("data")

        if not all([entity_type, entity_id, action, timestamp]):
            continue  # Skip invalid changes

        # Insérer changement (UNIQUE constraint évite duplicatas)
        try:
            c.execute(
                """INSERT INTO sync_log (user_id, entity_type, entity_id, action, timestamp, data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, entity_type, entity_id, action, timestamp, json.dumps(change_data) if change_data else None)
            )
            pushed_count += 1
        except sqlite3.IntegrityError:
            # Duplicate, skip
            pass

    conn.commit()
    conn.close()

    return {
        "success": True,
        "pushed": pushed_count
    }


# ═══════════════════════════════════════════════════════════════
#  ROUTE HANDLERS — PERMISSIONS (Phase 3)
# ═══════════════════════════════════════════════════════════════

def handle_permissions_grant(handler, data):
    """
    POST /api/permissions/grant
    Headers: Authorization: Bearer <JWT>
    Body: {"target_user_id": "bigboff_...", "scope_type": "tag", "scope_value": "notes", "mode": "consultation", "permissions": ["read"]}
    Response: {"success": true, "permission_id": 123}
    """
    # Vérifier JWT
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing or invalid Authorization header"}

    token = auth_header[7:]
    owner_user_id = _verify_jwt_token(token)

    if not owner_user_id:
        return {"success": False, "error": "Invalid or expired token"}

    # Récupérer paramètres
    target_user_id = data.get("target_user_id")
    target_group_id = data.get("target_group_id")
    scope_type = data.get("scope_type")  # 'tag', 'item', 'all'
    scope_value = data.get("scope_value")  # Nom du tag ou item_id
    mode = data.get("mode", "consultation")  # 'consultation' ou 'partage'
    permissions = data.get("permissions", ["read"])  # ['read', 'write', 'delete']

    # Validation
    if not scope_type:
        return {"success": False, "error": "Missing scope_type"}

    if not target_user_id and not target_group_id:
        return {"success": False, "error": "Missing target_user_id or target_group_id"}

    if mode not in ["consultation", "partage"]:
        return {"success": False, "error": "Invalid mode (must be 'consultation' or 'partage')"}

    # Vérifier que target existe
    conn = get_relay_db()
    c = conn.cursor()

    if target_user_id:
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (target_user_id,))
        if not c.fetchone():
            conn.close()
            return {"success": False, "error": "Target user not found"}

    # Vérifier si permission existe déjà
    c.execute(
        """SELECT id FROM permissions
           WHERE owner_user_id = ? AND target_user_id = ? AND scope_type = ? AND scope_value = ? AND revoked_at IS NULL""",
        (owner_user_id, target_user_id, scope_type, scope_value)
    )
    existing = c.fetchone()

    if existing:
        # Mettre à jour permission existante
        c.execute(
            """UPDATE permissions SET mode = ?, permissions = ?, granted_at = ?
               WHERE id = ?""",
            (mode, json.dumps(permissions), datetime.utcnow().isoformat(), existing["id"])
        )
        permission_id = existing["id"]
    else:
        # Créer nouvelle permission
        c.execute(
            """INSERT INTO permissions (owner_user_id, target_user_id, target_group_id, scope_type, scope_value, mode, permissions, granted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (owner_user_id, target_user_id, target_group_id, scope_type, scope_value, mode, json.dumps(permissions), datetime.utcnow().isoformat())
        )
        permission_id = c.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "permission_id": permission_id,
        "status": "updated" if existing else "created"
    }


def handle_permissions_revoke(handler, data):
    """
    POST /api/permissions/revoke
    Headers: Authorization: Bearer <JWT>
    Body: {"permission_id": 123}
    Response: {"success": true}
    """
    # Vérifier JWT
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing or invalid Authorization header"}

    token = auth_header[7:]
    user_id = _verify_jwt_token(token)

    if not user_id:
        return {"success": False, "error": "Invalid or expired token"}

    permission_id = data.get("permission_id")
    if not permission_id:
        return {"success": False, "error": "Missing permission_id"}

    conn = get_relay_db()
    c = conn.cursor()

    # Vérifier que la permission appartient au user
    c.execute(
        "SELECT owner_user_id FROM permissions WHERE id = ?",
        (permission_id,)
    )
    row = c.fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": "Permission not found"}

    if row["owner_user_id"] != user_id:
        conn.close()
        return {"success": False, "error": "Not authorized to revoke this permission"}

    # Révoquer (soft delete avec timestamp)
    c.execute(
        "UPDATE permissions SET revoked_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), permission_id)
    )

    conn.commit()
    conn.close()

    return {"success": True}


def handle_permissions_list(handler, params):
    """
    GET /api/permissions/list?as=owner|target
    Headers: Authorization: Bearer <JWT>
    Response: {"success": true, "permissions": [...]}
    """
    # Vérifier JWT
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing or invalid Authorization header"}

    token = auth_header[7:]
    user_id = _verify_jwt_token(token)

    if not user_id:
        return {"success": False, "error": "Invalid or expired token"}

    # Paramètre as=owner ou as=target
    as_param = params.get("as", ["owner"])[0]

    conn = get_relay_db()
    c = conn.cursor()

    if as_param == "owner":
        # Permissions accordées par moi
        c.execute(
            """SELECT id, target_user_id, target_group_id, scope_type, scope_value, mode, permissions, granted_at, revoked_at
               FROM permissions
               WHERE owner_user_id = ?
               ORDER BY granted_at DESC""",
            (user_id,)
        )
    elif as_param == "target":
        # Permissions accordées à moi
        c.execute(
            """SELECT id, owner_user_id, scope_type, scope_value, mode, permissions, granted_at, revoked_at
               FROM permissions
               WHERE target_user_id = ?
               ORDER BY granted_at DESC""",
            (user_id,)
        )
    else:
        conn.close()
        return {"success": False, "error": "Invalid 'as' parameter (must be 'owner' or 'target')"}

    rows = c.fetchall()
    conn.close()

    permissions = []
    for row in rows:
        perm = {
            "id": row["id"],
            "scope_type": row["scope_type"],
            "scope_value": row["scope_value"],
            "mode": row["mode"],
            "permissions": json.loads(row["permissions"]) if row["permissions"] else [],
            "granted_at": row["granted_at"],
            "revoked_at": row["revoked_at"],
            "active": row["revoked_at"] is None
        }

        if as_param == "owner":
            perm["target_user_id"] = row["target_user_id"]
            perm["target_group_id"] = row["target_group_id"]
        else:
            perm["owner_user_id"] = row["owner_user_id"]

        permissions.append(perm)

    return {
        "success": True,
        "permissions": permissions,
        "count": len(permissions)
    }


# ═══════════════════════════════════════════════════════════════
#  CONSULTATION HANDLERS (Phase 5)
# ═══════════════════════════════════════════════════════════════

def handle_consult_check(handler, params):
    """
    GET /api/consult/check?owner_user_id=X&scope_type=Y&scope_value=Z
    Headers: Authorization: Bearer <JWT>
    Response: {"success": true, "allowed": true/false, "reason": "...", "expires_at": "..."}

    Vérifier permission consultation sans retourner données.
    """
    # Vérifier JWT
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing or invalid Authorization header"}

    token = auth_header[7:]
    target_user_id = _verify_jwt_token(token)

    if not target_user_id:
        return {"success": False, "error": "Invalid or expired token"}

    # Params
    owner_user_id = params.get("owner_user_id", [""])[0]
    scope_type = params.get("scope_type", [""])[0]
    scope_value = params.get("scope_value", [""])[0]

    if not owner_user_id or not scope_type or not scope_value:
        return {"success": False, "error": "Missing params (owner_user_id, scope_type, scope_value)"}

    # Vérifier permission dans relay.db
    conn = get_relay_db()
    c = conn.cursor()

    c.execute("""
        SELECT mode, permissions, revoked_at
        FROM permissions
        WHERE owner_user_id = ?
          AND target_user_id = ?
          AND scope_type = ?
          AND scope_value = ?
          AND mode = 'consultation'
          AND (revoked_at IS NULL OR revoked_at = '')
    """, (owner_user_id, target_user_id, scope_type, scope_value))

    perm = c.fetchone()
    conn.close()

    if not perm:
        return {
            "success": True,
            "allowed": False,
            "reason": "no_permission"
        }

    if perm["revoked_at"]:  # revoked_at non NULL
        return {
            "success": True,
            "allowed": False,
            "reason": "revoked"
        }

    # Permission valide
    expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    return {
        "success": True,
        "allowed": True,
        "expires_at": expires_at
    }


def handle_consult_query(handler, params):
    """
    GET /api/consult/query?owner_user_id=X&scope_type=Y&scope_value=Z&q=search
    Headers: Authorization: Bearer <JWT>
    Response: {"success": true, "results": [...], "count": N, "expires_at": "..."}

    Récupérer snapshots filtrés pour consultation.
    """
    # 1. Vérifier permission (réutilise handle_consult_check)
    check_result = handle_consult_check(handler, params)
    if not check_result.get("allowed"):
        return {
            "success": False,
            "error": "Permission denied",
            "reason": check_result.get("reason")
        }

    # 2. Params
    owner_user_id = params.get("owner_user_id", [""])[0]
    scope_type = params.get("scope_type", [""])[0]
    scope_value = params.get("scope_value", [""])[0]
    search_query = params.get("q", [""])[0]  # Optionnel

    # 3. Récupérer snapshots depuis sync_log
    conn = get_relay_db()
    c = conn.cursor()

    # Snapshots avec expires_at valide (non expiré)
    c.execute("""
        SELECT entity_type, entity_id, data, timestamp
        FROM sync_log
        WHERE user_id = ?
          AND (expires_at IS NULL OR expires_at > datetime('now'))
        ORDER BY timestamp DESC
        LIMIT 1000
    """, (owner_user_id,))

    all_snapshots = c.fetchall()
    conn.close()

    # 4. Filtrer par scope
    results = []
    for row in all_snapshots:
        entity_type = row["entity_type"]
        entity_id = row["entity_id"]
        data_json = row["data"]
        timestamp = row["timestamp"]

        data = json.loads(data_json) if data_json else {}

        # Vérifier scope
        if scope_type == "all":
            include = True
        elif scope_type == "tag":
            # Vérifier si scope_value dans tags de cet élément
            tags = data.get("tags", [])
            include = scope_value in tags
        elif scope_type == "item":
            # Scope spécifique item
            include = (entity_type == "item" and str(entity_id) == scope_value)
        else:
            include = False

        if include:
            # Filtrer par search_query si fourni
            if search_query:
                # Simple search dans data JSON
                data_str = json.dumps(data).lower()
                if search_query.lower() not in data_str:
                    continue

            results.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "data": data,
                "timestamp": timestamp,
                "fetched_at": datetime.utcnow().isoformat() + "Z"
            })

    expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    return {
        "success": True,
        "results": results,
        "count": len(results),
        "expires_at": expires_at
    }


def handle_consult_snapshot(handler, data):
    """
    POST /api/consult/snapshot
    Headers: Authorization: Bearer <JWT>
    Body: {"changes": [...], "ttl_hours": 1}
    Response: {"success": true, "inserted": N, "expires_at": "..."}

    Appelé par client A pour pousser snapshots avec TTL.
    """
    # 1. Auth
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing or invalid Authorization header"}

    token = auth_header[7:]
    user_id = _verify_jwt_token(token)

    if not user_id:
        return {"success": False, "error": "Invalid or expired token"}

    # 2. Parse data
    changes = data.get("changes", [])
    ttl_hours = data.get("ttl_hours", 1)

    if not changes:
        return {"success": False, "error": "No changes provided"}

    # 3. Calculer expires_at
    expires_at = (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat() + "Z"

    # 4. Insérer dans sync_log avec expires_at
    conn = get_relay_db()
    c = conn.cursor()

    inserted = 0
    for change in changes:
        entity_type = change.get("entity_type")
        entity_id = change.get("entity_id")
        action = change.get("action", "update")
        change_data = json.dumps(change.get("data", {}))
        timestamp = datetime.utcnow().isoformat() + "Z"

        try:
            c.execute("""
                INSERT INTO sync_log
                (user_id, entity_type, entity_id, action, timestamp, data, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, entity_type, entity_id, action, timestamp, change_data, expires_at))
            inserted += 1
        except sqlite3.IntegrityError:
            # Déjà existant (UNIQUE constraint)
            # Update expires_at au lieu de fail
            c.execute("""
                UPDATE sync_log
                SET data = ?, expires_at = ?, timestamp = ?
                WHERE user_id = ? AND entity_type = ? AND entity_id = ?
            """, (change_data, expires_at, timestamp, user_id, entity_type, entity_id))
            inserted += 1

    conn.commit()
    conn.close()

    return {
        "success": True,
        "inserted": inserted,
        "expires_at": expires_at
    }


def cleanup_expired_snapshots():
    """Supprime les snapshots expirés de sync_log."""
    conn = get_relay_db()
    c = conn.cursor()

    c.execute("""
        DELETE FROM sync_log
        WHERE expires_at IS NOT NULL
          AND expires_at < datetime('now')
    """)

    deleted = c.rowcount
    conn.commit()
    conn.close()

    if deleted > 0:
        print(f"🗑️  Cleanup : {deleted} snapshots expirés supprimés")

    return deleted


# ─────────────────────────────────────────────────────────────────
# PHASE 6 : MODE PARTAGE (Clone permanent + Sync continue)
# ─────────────────────────────────────────────────────────────────

def handle_share_clone(handler, data):
    """
    POST /api/share/clone
    Headers: Authorization: Bearer <JWT>
    Body: {"owner_user_id": "...", "scope_type": "tag", "scope_value": "recettes"}
    Response: {"success": true, "snapshots": [...], "count": N}

    Clone initial : B récupère tous les éléments de A (mode partage).
    """
    # 1. Auth target user
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing Authorization header"}

    token = auth_header.replace("Bearer ", "")
    target_user_id = _verify_jwt_token(token)
    if not target_user_id:
        return {"success": False, "error": "Invalid token"}

    # 2. Parse params
    owner_user_id = data.get("owner_user_id")
    scope_type = data.get("scope_type")
    scope_value = data.get("scope_value")

    if not owner_user_id or not scope_type or not scope_value:
        return {"success": False, "error": "Missing params"}

    # 3. Vérifier permission mode='partage'
    conn = get_relay_db()
    c = conn.cursor()

    c.execute("""
        SELECT mode, permissions, revoked_at
        FROM permissions
        WHERE owner_user_id = ?
          AND target_user_id = ?
          AND scope_type = ?
          AND scope_value = ?
          AND mode = 'partage'
          AND (revoked_at IS NULL OR revoked_at = '')
    """, (owner_user_id, target_user_id, scope_type, scope_value))

    perm = c.fetchone()
    if not perm:
        conn.close()
        return {"success": False, "error": "Permission denied (no partage permission)"}

    if perm[2]:  # revoked_at
        conn.close()
        return {"success": False, "error": "Permission revoked"}

    # 4. Récupérer snapshots de owner depuis sync_log
    c.execute("""
        SELECT entity_type, entity_id, data, timestamp
        FROM sync_log
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 5000
    """, (owner_user_id,))

    all_snapshots = c.fetchall()
    conn.close()

    # 5. Filtrer par scope
    results = []
    for row in all_snapshots:
        entity_type, entity_id, data_json, timestamp = row
        data = json.loads(data_json) if data_json else {}

        # Vérifier scope
        include = False
        if scope_type == "all":
            include = True
        elif scope_type == "tag":
            tags = data.get("tags", [])
            include = scope_value in tags
        elif scope_type == "item":
            include = (entity_type == "item" and str(entity_id) == scope_value)

        if include:
            results.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "data": data,
                "timestamp": timestamp,
                "is_shared_copy": 1,  # Phase 6 marker
                "source_user_id": owner_user_id
            })

    return {
        "success": True,
        "snapshots": results,
        "count": len(results),
        "owner_user_id": owner_user_id
    }


def handle_share_sync(handler, params):
    """
    GET /api/share/sync?owner_user_id=X&scope_type=Y&scope_value=Z&since=<timestamp>
    Headers: Authorization: Bearer <JWT>
    Response: {"success": true, "changes": [...], "count": N}

    Sync continu : B récupère changements de A depuis last_sync.
    """
    # 1. Auth target user
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing Authorization header"}

    token = auth_header.replace("Bearer ", "")
    target_user_id = _verify_jwt_token(token)
    if not target_user_id:
        return {"success": False, "error": "Invalid token"}

    # 2. Params
    owner_user_id = params.get("owner_user_id", [""])[0]
    scope_type = params.get("scope_type", [""])[0]
    scope_value = params.get("scope_value", [""])[0]
    since = params.get("since", [""])[0]  # ISO timestamp

    if not owner_user_id or not scope_type or not scope_value:
        return {"success": False, "error": "Missing params"}

    # 3. Vérifier permission mode='partage' active
    conn = get_relay_db()
    c = conn.cursor()

    c.execute("""
        SELECT mode, revoked_at
        FROM permissions
        WHERE owner_user_id = ?
          AND target_user_id = ?
          AND scope_type = ?
          AND scope_value = ?
          AND mode = 'partage'
    """, (owner_user_id, target_user_id, scope_type, scope_value))

    perm = c.fetchone()
    if not perm:
        conn.close()
        return {"success": False, "error": "Permission denied"}

    if perm[1]:  # revoked_at
        conn.close()
        return {"success": False, "error": "Permission revoked", "revoked": True}

    # 4. Récupérer changements depuis 'since' timestamp
    if since:
        c.execute("""
            SELECT entity_type, entity_id, action, data, timestamp
            FROM sync_log
            WHERE user_id = ?
              AND timestamp > ?
            ORDER BY timestamp ASC
            LIMIT 1000
        """, (owner_user_id, since))
    else:
        # Pas de since → tous les snapshots
        c.execute("""
            SELECT entity_type, entity_id, 'update' as action, data, timestamp
            FROM sync_log
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1000
        """, (owner_user_id,))

    all_changes = c.fetchall()
    conn.close()

    # 5. Filtrer par scope
    results = []
    for row in all_changes:
        entity_type, entity_id, action, data_json, timestamp = row
        data = json.loads(data_json) if data_json else {}

        # Vérifier scope
        include = False
        if scope_type == "all":
            include = True
        elif scope_type == "tag":
            tags = data.get("tags", [])
            include = scope_value in tags
        elif scope_type == "item":
            include = (entity_type == "item" and str(entity_id) == scope_value)

        if include:
            results.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "data": data,
                "timestamp": timestamp,
                "is_shared_copy": 1,
                "source_user_id": owner_user_id
            })

    return {
        "success": True,
        "changes": results,
        "count": len(results),
        "latest_timestamp": results[-1]["timestamp"] if results else since
    }


def handle_share_revoke(handler, data):
    """
    POST /api/share/revoke
    Headers: Authorization: Bearer <JWT>
    Body: {"target_user_id": "...", "scope_type": "tag", "scope_value": "recettes"}
    Response: {"success": true}

    Révocation partage : A révoque permission → B garde snapshot figé.
    """
    # 1. Auth owner user
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing Authorization header"}

    token = auth_header.replace("Bearer ", "")
    owner_user_id = _verify_jwt_token(token)
    if not owner_user_id:
        return {"success": False, "error": "Invalid token"}

    # 2. Parse body
    target_user_id = data.get("target_user_id")
    scope_type = data.get("scope_type")
    scope_value = data.get("scope_value")

    if not target_user_id or not scope_type or not scope_value:
        return {"success": False, "error": "Missing params"}

    # 3. Marquer permission comme révoquée
    conn = get_relay_db()
    c = conn.cursor()

    revoked_at = datetime.utcnow().isoformat() + "Z"

    c.execute("""
        UPDATE permissions
        SET revoked_at = ?
        WHERE owner_user_id = ?
          AND target_user_id = ?
          AND scope_type = ?
          AND scope_value = ?
          AND mode = 'partage'
    """, (revoked_at, owner_user_id, target_user_id, scope_type, scope_value))

    if c.rowcount == 0:
        conn.close()
        return {"success": False, "error": "Permission not found"}

    conn.commit()
    conn.close()

    return {
        "success": True,
        "revoked_at": revoked_at,
        "message": "Permission révoquée, snapshot figé chez target"
    }


# ═══════════════════════════════════════════════════════════════
#  PHASE 7 — GROUPES (1-to-many partage)
# ═══════════════════════════════════════════════════════════════

def handle_groups_create(handler, data):
    """
    POST /api/groups/create
    Headers: Authorization: Bearer <JWT>
    Body: {"name": "Famille"}
    Response: {"success": true, "group_id": "grp_abc123"}
    """
    # 1. Auth owner
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing Authorization header"}

    token = auth_header.replace("Bearer ", "")
    owner_user_id = _verify_jwt_token(token)
    if not owner_user_id:
        return {"success": False, "error": "Invalid token"}

    # 2. Parse body
    name = data.get("name")
    if not name:
        return {"success": False, "error": "Missing name"}

    # 3. Générer group_id
    import uuid
    group_id = "grp_" + uuid.uuid4().hex[:12]

    # 4. Créer groupe
    conn = get_relay_db()
    c = conn.cursor()

    created_at = datetime.utcnow().isoformat() + "Z"

    c.execute("""
        INSERT INTO groups (id, name, owner_user_id, created_at)
        VALUES (?, ?, ?, ?)
    """, (group_id, name, owner_user_id, created_at))

    # 5. Ajouter owner comme admin
    c.execute("""
        INSERT INTO group_members (group_id, user_id, role, joined_at)
        VALUES (?, ?, 'admin', ?)
    """, (group_id, owner_user_id, created_at))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "group_id": group_id,
        "name": name,
        "created_at": created_at
    }


def handle_groups_invite(handler, data):
    """
    POST /api/groups/invite
    Headers: Authorization: Bearer <JWT>
    Body: {"group_id": "grp_abc123", "user_id": "bigboff_xyz"}
    Response: {"success": true}

    Note: L'invitation réelle se fait via QR code côté client.
    Cette API enregistre juste le membre dans le groupe.
    """
    # 1. Auth
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing Authorization header"}

    token = auth_header.replace("Bearer ", "")
    requester = _verify_jwt_token(token)
    if not requester:
        return {"success": False, "error": "Invalid token"}

    # 2. Parse body
    group_id = data.get("group_id")
    user_id = data.get("user_id")

    if not group_id or not user_id:
        return {"success": False, "error": "Missing params"}

    # 3. Vérifier que requester est admin du groupe
    conn = get_relay_db()
    c = conn.cursor()

    c.execute("""
        SELECT role FROM group_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, requester))

    row = c.fetchone()
    if not row or row[0] != 'admin':
        conn.close()
        return {"success": False, "error": "Not authorized (admin required)"}

    # 4. Ajouter user au groupe
    joined_at = datetime.utcnow().isoformat() + "Z"

    try:
        c.execute("""
            INSERT INTO group_members (group_id, user_id, role, joined_at)
            VALUES (?, ?, 'member', ?)
        """, (group_id, user_id, joined_at))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "error": "User already in group"}

    conn.close()

    return {
        "success": True,
        "group_id": group_id,
        "user_id": user_id,
        "joined_at": joined_at
    }


def handle_groups_join(handler, data):
    """
    POST /api/groups/join
    Headers: Authorization: Bearer <JWT>
    Body: {"group_id": "grp_abc123"}
    Response: {"success": true}

    Appelé après scan QR d'invitation.
    """
    # 1. Auth
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing Authorization header"}

    token = auth_header.replace("Bearer ", "")
    user_id = _verify_jwt_token(token)
    if not user_id:
        return {"success": False, "error": "Invalid token"}

    # 2. Parse body
    group_id = data.get("group_id")
    if not group_id:
        return {"success": False, "error": "Missing group_id"}

    # 3. Vérifier que groupe existe
    conn = get_relay_db()
    c = conn.cursor()

    c.execute("SELECT id FROM groups WHERE id = ?", (group_id,))
    if not c.fetchone():
        conn.close()
        return {"success": False, "error": "Group not found"}

    # 4. Ajouter user
    joined_at = datetime.utcnow().isoformat() + "Z"

    try:
        c.execute("""
            INSERT INTO group_members (group_id, user_id, role, joined_at)
            VALUES (?, ?, 'member', ?)
        """, (group_id, user_id, joined_at))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "error": "Already member"}

    conn.close()

    return {
        "success": True,
        "group_id": group_id,
        "joined_at": joined_at
    }


def handle_groups_list(handler, params):
    """
    GET /api/groups/list
    Headers: Authorization: Bearer <JWT>
    Response: {"success": true, "groups": [...]}

    Liste les groupes dont l'user est membre.
    """
    # 1. Auth
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing Authorization header"}

    token = auth_header.replace("Bearer ", "")
    user_id = _verify_jwt_token(token)
    if not user_id:
        return {"success": False, "error": "Invalid token"}

    # 2. Query groupes
    conn = get_relay_db()
    c = conn.cursor()

    c.execute("""
        SELECT g.id, g.name, g.owner_user_id, g.created_at, gm.role
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = ?
        ORDER BY g.created_at DESC
    """, (user_id,))

    groups = []
    for row in c.fetchall():
        groups.append({
            "group_id": row[0],
            "name": row[1],
            "owner_user_id": row[2],
            "created_at": row[3],
            "role": row[4]
        })

    conn.close()

    return {
        "success": True,
        "groups": groups
    }


def handle_groups_members(handler, params):
    """
    GET /api/groups/members?group_id=grp_abc123
    Headers: Authorization: Bearer <JWT>
    Response: {"success": true, "members": [...]}
    """
    # 1. Auth
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing Authorization header"}

    token = auth_header.replace("Bearer ", "")
    user_id = _verify_jwt_token(token)
    if not user_id:
        return {"success": False, "error": "Invalid token"}

    # 2. Parse params
    group_id = params.get("group_id", [None])[0]
    if not group_id:
        return {"success": False, "error": "Missing group_id"}

    # 3. Vérifier que user est membre
    conn = get_relay_db()
    c = conn.cursor()

    c.execute("""
        SELECT role FROM group_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, user_id))

    if not c.fetchone():
        conn.close()
        return {"success": False, "error": "Not a member"}

    # 4. Liste membres
    c.execute("""
        SELECT user_id, role, joined_at
        FROM group_members
        WHERE group_id = ?
        ORDER BY joined_at ASC
    """, (group_id,))

    members = []
    for row in c.fetchall():
        members.append({
            "user_id": row[0],
            "role": row[1],
            "joined_at": row[2]
        })

    conn.close()

    return {
        "success": True,
        "group_id": group_id,
        "members": members
    }


def handle_groups_kick(handler, data):
    """
    DELETE /api/groups/kick
    Headers: Authorization: Bearer <JWT>
    Body: {"group_id": "grp_abc123", "user_id": "bigboff_xyz"}
    Response: {"success": true}

    Seul admin peut kick.
    """
    # 1. Auth
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing Authorization header"}

    token = auth_header.replace("Bearer ", "")
    admin_id = _verify_jwt_token(token)
    if not admin_id:
        return {"success": False, "error": "Invalid token"}

    # 2. Parse body
    group_id = data.get("group_id")
    user_id = data.get("user_id")

    if not group_id or not user_id:
        return {"success": False, "error": "Missing params"}

    # 3. Vérifier que requester est admin
    conn = get_relay_db()
    c = conn.cursor()

    c.execute("""
        SELECT role FROM group_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, admin_id))

    row = c.fetchone()
    if not row or row[0] != 'admin':
        conn.close()
        return {"success": False, "error": "Not authorized (admin required)"}

    # 4. Supprimer member
    c.execute("""
        DELETE FROM group_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, user_id))

    if c.rowcount == 0:
        conn.close()
        return {"success": False, "error": "User not in group"}

    conn.commit()
    conn.close()

    return {
        "success": True,
        "group_id": group_id,
        "user_id": user_id,
        "message": "User kicked from group"
    }


def handle_groups_leave(handler, data):
    """
    DELETE /api/groups/leave
    Headers: Authorization: Bearer <JWT>
    Body: {"group_id": "grp_abc123"}
    Response: {"success": true}
    """
    # 1. Auth
    auth_header = handler.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"success": False, "error": "Missing Authorization header"}

    token = auth_header.replace("Bearer ", "")
    user_id = _verify_jwt_token(token)
    if not user_id:
        return {"success": False, "error": "Invalid token"}

    # 2. Parse body
    group_id = data.get("group_id")
    if not group_id:
        return {"success": False, "error": "Missing group_id"}

    # 3. Supprimer membership
    conn = get_relay_db()
    c = conn.cursor()

    c.execute("""
        DELETE FROM group_members
        WHERE group_id = ? AND user_id = ?
    """, (group_id, user_id))

    if c.rowcount == 0:
        conn.close()
        return {"success": False, "error": "Not a member"}

    conn.commit()
    conn.close()

    return {
        "success": True,
        "group_id": group_id,
        "message": "Left group"
    }


# ═══════════════════════════════════════════════════════════════
#  HTTP HANDLER
# ═══════════════════════════════════════════════════════════════

class RelayHandler(http.server.BaseHTTPRequestHandler):
    """Handler HTTP pour relay server."""

    def _send_json_response(self, data, status=200):
        """Envoie réponse JSON."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        """CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # Routes GET
        routes = {
            "/api/sync/changes": lambda: handle_sync_changes(self, params),
            "/api/permissions/list": lambda: handle_permissions_list(self, params),
            "/api/consult/check": lambda: handle_consult_check(self, params),
            "/api/consult/query": lambda: handle_consult_query(self, params),
            "/api/share/sync": lambda: handle_share_sync(self, params),  # Phase 6
            "/api/groups/list": lambda: handle_groups_list(self, params),  # Phase 7
            "/api/groups/members": lambda: handle_groups_members(self, params),  # Phase 7
        }

        if path in routes:
            try:
                result = routes[path]()
                self._send_json_response(result)
            except Exception as e:
                self._send_json_response({"success": False, "error": str(e)}, 500)
        else:
            self._send_json_response({"error": "Not found"}, 404)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Lire body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json_response({"success": False, "error": "Invalid JSON"}, 400)
            return

        # Routes POST
        routes = {
            "/api/auth/register": lambda: handle_auth_register(self, data),
            "/api/auth/challenge": lambda: handle_auth_challenge(self, data),
            "/api/auth/verify": lambda: handle_auth_verify(self, data),
            "/api/sync/push": lambda: handle_sync_push(self, data),
            "/api/permissions/grant": lambda: handle_permissions_grant(self, data),
            "/api/permissions/revoke": lambda: handle_permissions_revoke(self, data),
            "/api/consult/snapshot": lambda: handle_consult_snapshot(self, data),
            "/api/share/clone": lambda: handle_share_clone(self, data),  # Phase 6
            "/api/share/revoke": lambda: handle_share_revoke(self, data),  # Phase 6
            "/api/groups/create": lambda: handle_groups_create(self, data),  # Phase 7
            "/api/groups/invite": lambda: handle_groups_invite(self, data),  # Phase 7
            "/api/groups/join": lambda: handle_groups_join(self, data),  # Phase 7
        }

        if path in routes:
            try:
                result = routes[path]()
                self._send_json_response(result)
            except Exception as e:
                self._send_json_response({"success": False, "error": str(e)}, 500)
        else:
            self._send_json_response({"error": "Not found"}, 404)

    def do_DELETE(self):
        """Handle DELETE requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Lire body (pour kick qui a des params)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json_response({"success": False, "error": "Invalid JSON"}, 400)
            return

        # Routes DELETE
        routes = {
            "/api/groups/kick": lambda: handle_groups_kick(self, data),  # Phase 7
            "/api/groups/leave": lambda: handle_groups_leave(self, data),  # Phase 7
        }

        if path in routes:
            try:
                result = routes[path]()
                self._send_json_response(result)
            except Exception as e:
                self._send_json_response({"success": False, "error": str(e)}, 500)
        else:
            self._send_json_response({"error": "Not found"}, 404)

    def log_message(self, format, *args):
        """Override logging."""
        # Format: "127.0.0.1 - - [timestamp] "GET /api/sync/changes HTTP/1.1" 200 -"
        print(f"[{self.log_date_time_string()}] {args[0]}")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Point d'entrée relay server."""
    parser = argparse.ArgumentParser(description="BIG_BOFF Relay Server")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port (défaut: {PORT})")
    parser.add_argument("--host", default=HOST, help=f"Host (défaut: {HOST})")
    args = parser.parse_args()

    # Init DB
    if not RELAY_DB_PATH.exists():
        print("🔧 Initialisation relay.db...")
        setup_relay_db()

    # Init JWT secret
    jwt_secret = _get_jwt_secret()
    jwt_secret_preview = jwt_secret[:8] + "..." if len(jwt_secret) > 8 else jwt_secret

    print("=" * 50)
    print("🚀 BIG_BOFF Relay Server — Phase 2 P2P")
    print("=" * 50)
    print(f"Base    : {RELAY_DB_PATH}")
    print(f"URL     : http://{args.host}:{args.port}")
    print(f"JWT     : {jwt_secret_preview}")
    print(f"Expire  : {JWT_EXPIRATION_HOURS}h (token), {CHALLENGE_EXPIRATION_SECONDS}s (challenge)")
    print()
    print("Endpoints :")
    print("  POST /api/auth/register")
    print("  POST /api/auth/challenge")
    print("  POST /api/auth/verify")
    print("  GET  /api/sync/changes?since=<timestamp>")
    print("  POST /api/sync/push")
    print()
    print("Ctrl+C pour arrêter")
    print("=" * 50)

    # Démarrer serveur
    try:
        server = http.server.HTTPServer((args.host, args.port), RelayHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt relay server")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"\n❌ Erreur : Port {args.port} déjà utilisé")
            print(f"   Vérifier avec : lsof -i :{args.port}")
            print(f"   Ou utiliser un autre port : --port 8889")
        else:
            raise


if __name__ == "__main__":
    main()
