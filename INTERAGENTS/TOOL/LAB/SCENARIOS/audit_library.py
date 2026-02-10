import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE = Path("/Users/nathalie/Dropbox/____BIG_BOFF___/INTERAGENTS/TOOL")
LIB = BASE / "LIBRARY"
VALDIR = LIB / "RULES" / "VALIDATORS"
AUD = BASE / "LAB" / "AUDITS"
AUD.mkdir(parents=True, exist_ok=True)

validators = sorted(VALDIR.glob("validator_*.py"))
# Registry-first: audit declared modules first (MRG), then fallback scan for orphans
catalog_path = LIB / "REGISTRY" / "library_catalog.json"
declared = []
if catalog_path.exists():
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    mods_bucket = next((e for e in catalog.get("elementlist", []) if e.get("id") == "modules"), None)
    refs = mods_bucket.get("elementlist", []) if mods_bucket else []
    for r in refs:
        v = (r or {}).get("value", {})
        rel = v.get("path")
        if rel:
            declared.append(BASE / rel)

declared = [m for m in declared if m.exists()]

# Fallback scan: discover any module.json present on disk
scanned = sorted((LIB / "MODULES").glob("**/module.json"))

declared_set = {str(m.resolve()) for m in declared}
scanned_set = {str(m.resolve()) for m in scanned}

orphan_modules = [Path(x) for x in sorted(scanned_set - declared_set)]
missing_declared = [Path(x) for x in sorted(declared_set - scanned_set)]

# Audit targets = declared first, then orphans
modules = declared + orphan_modules

report = {
    "id": "audit_library",
    "type": "AuditReport",
    "at": datetime.utcnow().isoformat() + "Z",
    "validators": [v.name for v in validators],
    "modules_found": [str(m.relative_to(BASE)) for m in modules],
    "declared_modules": [str(m.relative_to(BASE)) for m in declared],
    "orphan_modules": [str(m.relative_to(BASE)) for m in orphan_modules],
    "missing_declared": [str(m.relative_to(BASE)) for m in missing_declared],
    "results": []
}

for m in modules:
    entry = {
        "module": str(m.relative_to(BASE)),
        "validator_results": []
    }
    for v in validators:
        p_run = subprocess.run(
            [sys.executable, str(v), str(m)],
            capture_output=True,
            text=True
        )
        output = (p_run.stdout or "") + (p_run.stderr or "")
        entry["validator_results"].append({
            "validator": v.name,
            "ok": p_run.returncode == 0 and "VALIDATION: OK" in output,
            "returncode": p_run.returncode,
            "output_tail": output.strip().splitlines()[-5:]
        })
    report["results"].append(entry)

out = AUD / f"audit_library_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("wrote:", out)
print("modules:", len(modules), "declared:", len(declared), "orphans:", len(orphan_modules), "validators:", len(validators))
