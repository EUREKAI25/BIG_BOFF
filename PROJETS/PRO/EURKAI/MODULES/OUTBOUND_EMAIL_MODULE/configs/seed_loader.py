"""
Load a seed JSON config into the OEM database.
Usage:
    python -m outbound_email_module.configs.seed_loader configs/presence_ia_seed.json
"""
import json
import sys
from pathlib import Path

# Ensure package is importable when run as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from outbound_email_module.database import (
    SessionLocal, db_create_domain, db_create_mailbox, db_create_rotation,
    db_create_rule, db_create_warmup, db_get_domain_by_name, init_db,
)


def load_seed(path: str):
    data = json.loads(Path(path).read_text())
    init_db()
    db = SessionLocal()

    try:
        # 1. Domains
        domain_map = {}  # name → id
        for d in data.get("domains", []):
            existing = db_get_domain_by_name(db, d["name"])
            if existing:
                print(f"  [skip] Domain already exists: {d['name']}")
                domain_map[d["name"]] = existing.id
            else:
                obj = db_create_domain(db, d)
                domain_map[d["name"]] = obj.id
                print(f"  [+] Domain: {d['name']} ({obj.id})")

        # 2. Warmup strategy
        warmup_id = None
        ws = data.get("warmup_strategy")
        if ws:
            obj = db_create_warmup(db, ws)
            warmup_id = obj.id
            print(f"  [+] Warmup strategy: {obj.name} ({obj.id})")

        # 3. Rotation strategy
        rotation_id = None
        rs = data.get("rotation_strategy")
        if rs:
            obj = db_create_rotation(db, rs)
            rotation_id = obj.id
            print(f"  [+] Rotation strategy: {obj.name} ({obj.id})")

        # 4. Mailboxes
        for mb in data.get("mailboxes", []):
            domain_name = mb.pop("domain")
            domain_id = domain_map.get(domain_name)
            if not domain_id:
                print(f"  [!] Domain not found for mailbox: {domain_name}")
                continue
            mb["domain_id"] = domain_id
            mb["email"] = f"{mb['local_part']}@{domain_name}"
            if warmup_id:
                mb.setdefault("meta", {})["warmup_strategy_id"] = warmup_id
            obj = db_create_mailbox(db, mb)
            print(f"  [+] Mailbox: {obj.email} ({obj.id})")

        # 5. Compliance rules
        for rule in data.get("compliance_rules", []):
            obj = db_create_rule(db, rule)
            print(f"  [+] Compliance rule: {obj.name} ({obj.id})")

        print("\nSeed loaded successfully.")
        print(f"  Warmup strategy ID:   {warmup_id}")
        print(f"  Rotation strategy ID: {rotation_id}")
        print(f"  Domain IDs: {domain_map}")

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_loader.py <seed_file.json>")
        sys.exit(1)
    load_seed(sys.argv[1])
