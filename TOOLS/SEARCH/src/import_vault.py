#!/usr/bin/env python3
"""
BIG_BOFF Search — Import du fichier de mots de passe
Parse le CSV, déduplique, chiffre et stocke dans le coffre-fort.
"""

import csv
import getpass
import hashlib
import os
import re
import sqlite3
import subprocess
from datetime import datetime

DB_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db"
CSV_PATH = "/Users/nathalie/Downloads/INFOS - INFOS.csv"

STOP_WORDS = {
    "", "a", "an", "the", "de", "du", "le", "la", "les", "un", "une", "des",
    "et", "ou", "en", "au", "aux", "par", "pour", "sur", "dans", "avec",
    "pro", "perso", "big", "boff", "big_boff",
}


def vault_encrypt(plaintext, master_pwd):
    """Chiffre avec AES-256-CBC via openssl."""
    env = os.environ.copy()
    env["VAULT_KEY"] = master_pwd
    r = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "100000",
         "-pass", "env:VAULT_KEY", "-base64", "-A"],
        input=plaintext.encode(), capture_output=True, env=env
    )
    return r.stdout.decode().strip()


def vault_decrypt(ciphertext, master_pwd):
    """Déchiffre AES-256-CBC via openssl."""
    env = os.environ.copy()
    env["VAULT_KEY"] = master_pwd
    r = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "100000",
         "-pass", "env:VAULT_KEY", "-base64", "-A"],
        input=ciphertext.encode(), capture_output=True, env=env
    )
    if r.returncode != 0:
        return None
    return r.stdout.decode()


def hash_master(master_pwd, salt=None):
    """PBKDF2-SHA256 du mot de passe maitre."""
    if salt is None:
        salt = os.urandom(32)
    h = hashlib.pbkdf2_hmac("sha256", master_pwd.encode(), salt, 100000)
    return salt, h


def categorize(service, login, notes):
    """Auto-catégorise une entrée."""
    s = (service + " " + notes).upper()
    if "BDD" in s or "SQL" in s or "DATABASE" in s:
        return "database"
    if "API" in s or "CLE API" in s or "KEY" in s:
        return "api_key"
    if "EMAIL" in s and "FTP" not in s:
        return "email"
    if "FTP" in s:
        return "ftp"
    if "IBAN" in s or "BANQUE" in s:
        return "bank"
    if "SIREN" in s or "SIRET" in s or "TVA" in s or "NAF" in s:
        return "admin"
    return "password"


def extract_tags(service, project, category):
    """Genere les tags pour une entree du coffre."""
    tags = {"pwd", "coffre"}

    # Mots du service
    for word in re.split(r'[\s\-_.,;:!?()[\]{}"/\'@]+', service):
        w = word.lower().strip()
        if len(w) >= 3 and w not in STOP_WORDS and w.isalpha():
            tags.add(w)

    # Mots du projet
    if project:
        for word in re.split(r'[\s\-_.,;:!?()[\]{}"/\'@]+', project):
            w = word.lower().strip()
            if len(w) >= 3 and w not in STOP_WORDS and w.isalpha():
                tags.add(w)

    # Categorie
    if category and len(category) >= 3:
        tags.add(category)

    return tags


def parse_csv(path):
    """Parse le CSV et retourne les entrees uniques."""
    entries = []
    seen = set()

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)  # Skip header

        for row in reader:
            # Colonnes : 0=?, 1=DOMAINE, 2=PROJET, 3=OUTIL, 4=ID, 5=PWD, 6+=DIV
            if len(row) < 6:
                continue

            service = (row[3] or "").strip()
            if not service:
                continue

            login = (row[4] or "").strip()
            password = (row[5] or "").strip()
            project = (row[2] or "").strip()

            # Collecter les notes (colonnes 6+)
            notes_parts = []
            for i in range(6, min(len(row), 12)):
                val = (row[i] or "").strip()
                if val and not val.replace(",", "").replace(".", "").replace(" ", "").isdigit():
                    # Ignorer les colonnes numeriques (donnees financieres)
                    notes_parts.append(val)
            notes = " | ".join(notes_parts) if notes_parts else ""

            # Extraire l'URL si presente dans les notes
            url = ""
            for part in notes_parts:
                if part.startswith("http"):
                    url = part
                    break

            # Deduplication : service + login (en minuscule)
            dedup_key = (service.lower(), login.lower())
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            # Ignorer les entrees sans mot de passe ET sans login
            if not password and not login:
                continue

            entries.append({
                "service": service,
                "login": login,
                "password": password,
                "project": project,
                "url": url,
                "notes": notes,
            })

    return entries


def main():
    print("=== BIG_BOFF Search --- Import Coffre-Fort ===")
    print(f"CSV : {CSV_PATH}")
    print(f"Base : {DB_PATH}\n")

    # Verifier le CSV
    if not os.path.exists(CSV_PATH):
        print(f"ERREUR : fichier introuvable : {CSV_PATH}")
        return

    # Parser le CSV
    entries = parse_csv(CSV_PATH)
    print(f"Entrees trouvees : {len(entries)} (apres deduplication)\n")

    if not entries:
        print("Aucune entree a importer.")
        return

    # Apercu
    print("Apercu (10 premieres) :")
    for e in entries[:10]:
        pwd_display = "***" if e["password"] else "(vide)"
        print(f"  {e['service']:25s} | {e['login']:35s} | {pwd_display}")
    if len(entries) > 10:
        print(f"  ... et {len(entries) - 10} autres\n")

    # Mot de passe maitre
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Verifier si un master existe deja
    c.execute("SELECT value FROM vault_config WHERE key = 'master_hash'")
    existing = c.fetchone()

    if existing:
        print("Un mot de passe maitre existe deja.")
        master = getpass.getpass("Mot de passe maitre : ")
        # Verifier
        c.execute("SELECT value FROM vault_config WHERE key = 'master_salt'")
        salt_row = c.fetchone()
        salt = bytes.fromhex(salt_row["value"])
        _, h = hash_master(master, salt)
        if h.hex() != existing["value"]:
            print("ERREUR : mot de passe maitre incorrect !")
            conn.close()
            return
        print("Mot de passe maitre OK.\n")
    else:
        print("Premier lancement : definir un mot de passe maitre.")
        print("Ce mot de passe protegera tous vos identifiants.\n")
        master = getpass.getpass("Nouveau mot de passe maitre : ")
        confirm = getpass.getpass("Confirmer : ")
        if master != confirm:
            print("ERREUR : les mots de passe ne correspondent pas !")
            conn.close()
            return
        if len(master) < 4:
            print("ERREUR : mot de passe trop court (min 4 caracteres) !")
            conn.close()
            return
        # Stocker le hash
        salt, h = hash_master(master)
        c.execute("INSERT OR REPLACE INTO vault_config (key, value) VALUES ('master_hash', ?)",
                  (h.hex(),))
        c.execute("INSERT OR REPLACE INTO vault_config (key, value) VALUES ('master_salt', ?)",
                  (salt.hex(),))
        conn.commit()
        print("Mot de passe maitre enregistre.\n")

    # Verifier que le chiffrement fonctionne
    test_enc = vault_encrypt("test_ok", master)
    test_dec = vault_decrypt(test_enc, master)
    if test_dec != "test_ok":
        print("ERREUR : le chiffrement ne fonctionne pas correctement !")
        conn.close()
        return

    # Importer
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    imported = 0
    skipped = 0
    tag_batch = []

    for entry in entries:
        # Verifier si deja en base
        c.execute("SELECT id FROM vault WHERE service = ? AND login = ?",
                  (entry["service"], entry["login"]))
        if c.fetchone():
            skipped += 1
            continue

        # Chiffrer le mot de passe
        pwd_enc = ""
        if entry["password"]:
            pwd_enc = vault_encrypt(entry["password"], master)

        category = categorize(entry["service"], entry["login"], entry["notes"])

        c.execute("""
            INSERT INTO vault (service, login, password_enc, project, category, url, notes,
                               date_added, date_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry["service"], entry["login"], pwd_enc, entry["project"],
              category, entry["url"], entry["notes"], now, now))

        vault_id = c.lastrowid

        # Tags : convention -(id + 300000)
        tag_id = -(vault_id + 300000)
        tags = extract_tags(entry["service"], entry["project"], category)
        for tag in tags:
            tag_batch.append((tag_id, tag))

        imported += 1

    # Inserer les tags
    if tag_batch:
        c.executemany("INSERT INTO tags (item_id, tag) VALUES (?, ?)", tag_batch)

    conn.commit()
    conn.close()

    print(f"=== RESULTAT ===")
    print(f"Importes : {imported}")
    print(f"Ignores (deja en base) : {skipped}")
    print(f"Tags crees : {len(tag_batch)}")
    print(f"\nTermine ! Les mots de passe sont cherchables avec le tag 'pwd'.")


if __name__ == "__main__":
    main()
