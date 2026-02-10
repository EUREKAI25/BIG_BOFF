#!/usr/bin/env python3
"""
BIG_BOFF Search — Indexation des emails
Lit les comptes IMAP, indexe les emails dans catalogue.db avec tags.
"""

import imaplib
import email
import email.header
import email.utils
import json
import sqlite3
import sys
import re
from pathlib import Path
from datetime import datetime

DB_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db"
ACCOUNTS_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH/src/email_accounts.json"

STOP_WORDS = {
    "", "a", "an", "the", "de", "du", "le", "la", "les", "un", "une", "des",
    "et", "ou", "en", "au", "aux", "par", "pour", "sur", "dans", "avec",
    "is", "it", "to", "of", "in", "on", "at", "by", "for", "and", "or",
    "re", "fwd", "fw", "tr", "ref", "objet", "subject",
    "http", "https", "www", "com", "org", "net", "fr",
    "pas", "que", "qui", "est", "sont", "ont", "fait", "mais", "plus",
    "mon", "ton", "son", "mes", "tes", "ses", "notre", "votre", "leur",
    "cette", "ces", "tout", "tous", "toute", "toutes",
    "bon", "bien", "merci", "bonjour", "cordialement", "bonne",
    "big", "boff", "big_boff",
}


def decode_header(raw):
    """Décode un header email (peut être encodé en base64/quoted-printable)."""
    if not raw:
        return ""
    parts = email.header.decode_header(raw)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="ignore"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def extract_email_tags(subject, from_addr, to_addr, folder, has_attachments, account_email=None):
    """Génère les tags pour un email."""
    tags = set()

    # Tag type
    tags.add("email")

    # Tag dossier
    folder_clean = folder.lower().strip('"')
    folder_map = {
        "inbox": "inbox",
        "spam": "spam",
        "corbeille": "corbeille",
        "brouillons": "brouillons",
        "archive": "archive",
    }
    for key, tag in folder_map.items():
        if key in folder_clean:
            tags.add(tag)

    # Envoyé ou reçu — basé sur from_addr si account_email disponible
    sent_by_header = False
    if account_email and from_addr:
        from_match = re.search(r'[\w.-]+@[\w.-]+', from_addr.lower())
        if from_match and from_match.group(0) == account_email.lower():
            sent_by_header = True

    sent_by_folder = any(ind in folder_clean for ind in ["envoy", "sent", "objets envoy"])

    if sent_by_header or sent_by_folder:
        tags.add("envoyé")
    else:
        tags.add("reçu")

    # Tags depuis l'expéditeur
    if from_addr:
        # Domaine de l'expéditeur
        match = re.search(r'@([\w.-]+)', from_addr)
        if match:
            domain = match.group(1).lower()
            # Extraire les parties significatives du domaine
            parts = domain.split('.')
            for p in parts:
                if len(p) >= 3 and p not in STOP_WORDS:
                    tags.add(p)

        # Nom de l'expéditeur
        name_match = re.match(r'^(.*?)\s*<', from_addr)
        if name_match:
            name = name_match.group(1).strip('" ')
            for word in re.split(r'[\s\-_.]+', name):
                word = word.lower().strip()
                if len(word) >= 3 and word not in STOP_WORDS:
                    tags.add(word)

    # Tags depuis le sujet
    if subject:
        # Retirer Re: Fwd: etc.
        clean = re.sub(r'^(?:Re|Fwd|Fw|TR|Ref)\s*:\s*', '', subject, flags=re.IGNORECASE)
        for word in re.split(r'[\s\-_.,;:!?()[\]{}"/\']+', clean):
            word = word.lower().strip()
            if len(word) >= 3 and word not in STOP_WORDS and word.isalpha():
                tags.add(word)

    # Pièces jointes
    if has_attachments:
        tags.add("attachments")

    return tags


def setup_email_table(conn):
    """Crée la table emails si elle n'existe pas."""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT,
            folder TEXT,
            uid TEXT,
            message_id TEXT,
            subject TEXT,
            from_addr TEXT,
            to_addr TEXT,
            date_sent TEXT,
            date_received TEXT,
            has_attachments INTEGER DEFAULT 0,
            size INTEGER DEFAULT 0,
            UNIQUE(account, folder, uid)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_email_account ON emails(account)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_email_uid ON emails(account, folder, uid)")
    # Ajouter colonne snippet si absente
    try:
        c.execute("ALTER TABLE emails ADD COLUMN snippet TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    conn.commit()


def extract_snippet(raw_body_bytes, max_chars=150):
    """Extrait un snippet texte depuis les premiers octets du body email."""
    if not raw_body_bytes:
        return ""
    text = ""
    for enc in ("utf-8", "latin-1", "ascii"):
        try:
            text = raw_body_bytes.decode(enc, errors="ignore")
            break
        except Exception:
            continue
    if not text:
        return ""
    # Décoder quoted-printable (=XX)
    import quopri
    try:
        text = quopri.decodestring(text.encode("latin-1", errors="ignore")).decode("utf-8", errors="ignore")
    except Exception:
        pass
    # Nettoyer HTML
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    # Nettoyer headers MIME résiduels et boundaries
    text = re.sub(r'(?i)content-type:[^\n]*', '', text)
    text = re.sub(r'(?i)content-transfer-encoding:[^\n]*', '', text)
    text = re.sub(r'(?i)content-disposition:[^\n]*', '', text)
    text = re.sub(r'(?i)charset="?[a-z0-9_-]+"?', '', text)
    text = re.sub(r'--[a-zA-Z0-9_/=.-]+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_chars]


def index_account(conn, account):
    """Indexe tous les emails d'un compte."""
    name = account["name"]
    email_addr = account["email"]
    password = account["password"]
    server = account["imap_server"]
    port = account.get("imap_port", 993)

    print(f"\n--- Compte : {name} ({email_addr}) ---")

    imap = imaplib.IMAP4_SSL(server, port)
    imap.login(email_addr, password)

    # Lister les dossiers
    status, folders_raw = imap.list()
    folders = []
    for f in folders_raw:
        # Parser le nom du dossier
        match = re.match(r'\(.*?\)\s+"(.*)"\s+"?(.*?)"?\s*$', f.decode())
        if match:
            folders.append(match.group(2).strip('"'))
        else:
            # Fallback
            parts = f.decode().split('" ')
            if len(parts) >= 2:
                folders.append(parts[-1].strip('"'))

    print(f"  Dossiers : {folders}")

    c = conn.cursor()
    total_indexed = 0
    total_skipped = 0
    tag_batch = []

    for folder in folders:
        try:
            status, _ = imap.select(f'"{folder}"', readonly=True)
            if status != "OK":
                print(f"  [{folder}] Impossible d'ouvrir")
                continue
        except Exception as e:
            print(f"  [{folder}] Erreur : {e}")
            continue

        # Récupérer tous les UIDs
        status, data = imap.uid('search', None, 'ALL')
        if status != "OK" or not data[0]:
            print(f"  [{folder}] Vide")
            continue

        uids = data[0].split()
        print(f"  [{folder}] {len(uids)} emails", end="", flush=True)

        # Vérifier les UIDs déjà indexés
        existing_uids = set()
        c.execute("SELECT uid FROM emails WHERE account = ? AND folder = ?", (email_addr, folder))
        for row in c.fetchall():
            existing_uids.add(row[0])

        new_count = 0
        for uid in uids:
            uid_str = uid.decode()
            if uid_str in existing_uids:
                total_skipped += 1
                continue

            try:
                # Récupérer headers + premiers 500 octets du body
                status, msg_data = imap.uid('fetch', uid, '(BODY.PEEK[HEADER] BODY.PEEK[TEXT]<0.500> RFC822.SIZE)')
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                # Parser les tuples (header vs body partiel)
                raw_headers = None
                raw_body_partial = None
                msg_size = 0
                for part in msg_data:
                    if isinstance(part, tuple):
                        info = part[0].decode() if isinstance(part[0], bytes) else str(part[0])
                        if "BODY[HEADER]" in info:
                            raw_headers = part[1]
                        elif "BODY[TEXT]" in info:
                            raw_body_partial = part[1]
                        size_match = re.search(r'RFC822\.SIZE\s+(\d+)', info)
                        if size_match:
                            msg_size = int(size_match.group(1))

                if not raw_headers:
                    continue

                msg = email.message_from_bytes(raw_headers)

                subject = decode_header(msg.get("Subject", ""))
                from_raw = decode_header(msg.get("From", ""))
                to_raw = decode_header(msg.get("To", ""))
                date_raw = msg.get("Date", "")
                message_id = msg.get("Message-ID", "")

                # Parser la date
                date_sent = ""
                if date_raw:
                    try:
                        parsed = email.utils.parsedate_to_datetime(date_raw)
                        date_sent = parsed.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        date_sent = date_raw[:16]

                # Vérifier pièces jointes (approximation depuis headers)
                content_type = msg.get("Content-Type", "")
                has_attach = 1 if "multipart/mixed" in content_type else 0

                # Extraire le snippet
                snippet = extract_snippet(raw_body_partial) if raw_body_partial else ""

                # Insérer dans la base
                c.execute("""
                    INSERT OR IGNORE INTO emails
                    (account, folder, uid, message_id, subject, from_addr, to_addr,
                     date_sent, has_attachments, size, snippet)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (email_addr, folder, uid_str, message_id, subject,
                      from_raw, to_raw, date_sent, has_attach, msg_size, snippet))

                email_db_id = c.lastrowid
                if email_db_id:
                    # Générer et stocker les tags
                    tags = extract_email_tags(subject, from_raw, to_raw, folder, has_attach, account_email=email_addr)
                    # Utiliser un ID négatif pour distinguer des items fichiers
                    # Convention : email_id négatif = -(email.id + 100000)
                    tag_id = -(email_db_id + 100000)
                    for tag in tags:
                        tag_batch.append((tag_id, tag))

                    new_count += 1
                    total_indexed += 1

            except Exception as e:
                continue

        print(f" → {new_count} nouveaux")

        # Flush par dossier
        if tag_batch:
            c.executemany("INSERT INTO tags (item_id, tag) VALUES (?, ?)", tag_batch)
            conn.commit()
            tag_batch = []

    imap.logout()
    print(f"\n  Total : {total_indexed} indexés, {total_skipped} déjà en base")
    return total_indexed


def retag_emails(conn, accounts):
    """Recalcule les tags pour tous les emails (corrige envoyé/reçu)."""
    c = conn.cursor()

    # Dict account_email -> email
    account_emails = {}
    for a in accounts:
        account_emails[a["email"]] = a["email"]

    # Supprimer les anciens tags email (range -200000..-100001)
    c.execute("DELETE FROM tags WHERE item_id < -100000 AND item_id >= -200000")
    conn.commit()
    print("Tags email supprimés")

    # Relire tous les emails
    c.execute("SELECT id, account, folder, subject, from_addr, to_addr, has_attachments FROM emails")
    rows = c.fetchall()

    batch = []
    for row in rows:
        email_db_id, account, folder = row[0], row[1], row[2]
        subject = row[3] or ""
        from_raw = row[4] or ""
        to_raw = row[5] or ""
        has_attach = row[6]
        acct_email = account_emails.get(account, account)
        tags = extract_email_tags(subject, from_raw, to_raw, folder, has_attach, account_email=acct_email)
        tag_id = -(email_db_id + 100000)
        for tag in tags:
            batch.append((tag_id, tag))

    c.executemany("INSERT INTO tags (item_id, tag) VALUES (?, ?)", batch)
    conn.commit()

    # Compter envoyé/reçu
    c.execute("SELECT tag, COUNT(*) FROM tags WHERE tag IN ('envoyé', 'reçu') AND item_id < -100000 AND item_id >= -200000 GROUP BY tag")
    counts = {row[0]: row[1] for row in c.fetchall()}
    print(f"Re-tagging terminé : {len(batch)} tags pour {len(rows)} emails")
    print(f"  envoyé : {counts.get('envoyé', 0)}")
    print(f"  reçu : {counts.get('reçu', 0)}")


def backfill_snippets(conn, accounts):
    """Récupère les snippets IMAP pour les emails existants sans snippet."""
    c = conn.cursor()
    total_updated = 0

    for account in accounts:
        email_addr = account["email"]
        server = account["imap_server"]
        port = account.get("imap_port", 993)
        password = account["password"]

        print(f"\n--- Snippets : {account['name']} ({email_addr}) ---")

        # Emails sans snippet pour ce compte
        c.execute("SELECT id, folder, uid FROM emails WHERE account = ? AND (snippet IS NULL OR snippet = '')",
                  (email_addr,))
        to_update = c.fetchall()
        print(f"  {len(to_update)} emails sans snippet")

        if not to_update:
            continue

        try:
            imap = imaplib.IMAP4_SSL(server, port)
            imap.login(email_addr, password)
        except Exception as e:
            print(f"  ERREUR connexion : {e}")
            continue

        # Grouper par dossier
        by_folder = {}
        for eid, folder, uid in to_update:
            by_folder.setdefault(folder, []).append((eid, uid))

        for folder, items in by_folder.items():
            try:
                status, _ = imap.select(f'"{folder}"', readonly=True)
                if status != "OK":
                    print(f"  [{folder}] Impossible d'ouvrir")
                    continue
            except Exception:
                continue

            count = 0
            for eid, uid_str in items:
                try:
                    uid_bytes = uid_str.encode()
                    status, data = imap.uid('fetch', uid_bytes, '(BODY.PEEK[TEXT]<0.500>)')
                    if status != "OK" or not data or not data[0]:
                        continue
                    for part in data:
                        if isinstance(part, tuple):
                            snippet = extract_snippet(part[1])
                            if snippet:
                                c.execute("UPDATE emails SET snippet = ? WHERE id = ?", (snippet, eid))
                                count += 1
                            break
                except Exception:
                    continue

            conn.commit()
            total_updated += count
            print(f"  [{folder}] {count}/{len(items)} snippets")

        try:
            imap.logout()
        except Exception:
            pass

    print(f"\nTotal snippets ajoutés : {total_updated}")


def main():
    print("=== BIG_BOFF Search — Indexation des emails ===")
    print(f"Base : {DB_PATH}\n")

    # Charger les comptes
    with open(ACCOUNTS_PATH) as f:
        accounts = json.load(f)

    print(f"Comptes configurés : {len(accounts)}")

    conn = sqlite3.connect(DB_PATH)
    setup_email_table(conn)

    # Modes spéciaux
    if "--retag" in sys.argv:
        retag_emails(conn, accounts)
        conn.close()
        print("\nTerminé !")
        return

    if "--snippets" in sys.argv:
        backfill_snippets(conn, accounts)
        conn.close()
        print("\nTerminé !")
        return

    # Mode normal : indexation
    total = 0
    for account in accounts:
        try:
            total += index_account(conn, account)
        except Exception as e:
            print(f"  ERREUR compte {account['name']}: {e}")

    # Stats
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM emails")
    total_emails = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tags WHERE item_id < -100000 AND item_id >= -200000")
    total_email_tags = c.fetchone()[0]

    print(f"\n=== RÉSULTAT ===")
    print(f"Emails en base : {total_emails}")
    print(f"Tags email : {total_email_tags}")
    print(f"Nouveaux indexés : {total}")

    conn.close()
    print("\nTerminé !")


if __name__ == "__main__":
    main()
