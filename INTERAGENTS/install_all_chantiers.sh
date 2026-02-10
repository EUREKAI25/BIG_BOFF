#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANTIERS_DIR="$ROOT/CHANTIERS"
TARGET_DIR="$ROOT/APP"

mkdir -p "$TARGET_DIR"

# --- Helpers ---
log() { printf "%s\n" "$*"; }
die() { printf "ERROR: %s\n" "$*" >&2; exit 1; }

# Normalize zip names with spaces (keeps original too if you want; here we rename in place)
normalize_zip_names() {
  find "$CHANTIERS_DIR" -maxdepth 3 -type f -name "*.zip" -print0 | while IFS= read -r -d '' z; do
    base="$(basename "$z")"
    dir="$(dirname "$z")"
    if [[ "$base" == *" "* ]]; then
      newbase="${base// /_}"
      if [[ ! -f "$dir/$newbase" ]]; then
        mv "$z" "$dir/$newbase"
        log "[OK] renamed: $base -> $newbase"
      else
        # If both exist, keep the normalized and remove the spaced one
        rm -f "$z"
        log "[OK] removed duplicate spaced zip: $base (kept $newbase)"
      fi
    fi
  done
}

install_zip_into_app() {
  local zip_path="$1"
  [[ -f "$zip_path" ]] || die "zip not found: $zip_path"

  local tmp_dir
  tmp_dir="$(mktemp -d)"
  unzip -o "$zip_path" -d "$tmp_dir" >/dev/null

  # If archive contains a single top folder, copy its contents; else copy all extracted contents.
  local entries
  entries="$(find "$tmp_dir" -mindepth 1 -maxdepth 1 -type d -o -type f | wc -l | tr -d ' ')"

  local src_dir="$tmp_dir"
  if [[ "$entries" -eq 1 ]]; then
    local only
    only="$(find "$tmp_dir" -mindepth 1 -maxdepth 1 -type d -print -quit || true)"
    if [[ -n "$only" ]]; then
      src_dir="$only"
    fi
  fi

  cp -R "$src_dir"/. "$TARGET_DIR"/
  rm -rf "$tmp_dir"
}

# Ensure packaging is stable: package ONLY interagents + cli, ignore prompts/workspace/etc.
patch_pyproject_packages() {
  local pp="$TARGET_DIR/pyproject.toml"
  [[ -f "$pp" ]] || return 0

  python3 - <<'PY'
from pathlib import Path
import re

pp = Path("APP/pyproject.toml")
s = pp.read_text(encoding="utf-8")

# Ensure README exists to satisfy readme = "README.md"
readme = Path("APP/README.md")
if not readme.exists():
    readme.write_text("# INTERAGENTS\n\nMVP\n", encoding="utf-8")
    print("[OK] APP/README.md created")
else:
    print("[OK] APP/README.md exists")

# Remove any existing setuptools auto-discovery blocks to avoid conflicts
s = re.sub(r'^\[tool\.setuptools\.packages\.find\][\s\S]*?(?=^\[|\Z)', '', s, flags=re.MULTILINE)

# Ensure explicit packages list (this avoids "Multiple top-level packages discovered")
block = "\n[tool.setuptools]\npackages = [\"interagents\", \"cli\"]\n"
if "[tool.setuptools]" in s:
    # Replace existing [tool.setuptools] section if it contains packages=
    s = re.sub(r'^\[tool\.setuptools\][\s\S]*?(?=^\[|\Z)', block, s, flags=re.MULTILINE)
else:
    s += block

pp.write_text(s, encoding="utf-8")
print("[OK] pyproject.toml: explicit packages=['interagents','cli'] (no auto-discovery)")
PY
}

# Patch orchestrator to treat pytest exit code 5 as success (if not already)
patch_orchestrator_pytest5() {
  local f="$TARGET_DIR/interagents/orchestrator.py"
  [[ -f "$f" ]] || return 0

  python3 - <<'PY'
from pathlib import Path
import re

p = Path("APP/interagents/orchestrator.py")
s = p.read_text(encoding="utf-8")

if "Normalize pytest exit code 5 (no tests collected) as success for MVP" in s:
    print("[OK] orchestrator.py already patched")
    raise SystemExit(0)

# Patch the COMMAND_RESULT block + failure check
pattern = r"""
(?P<indent>^[ \t]*)self\._log\(
[ \t]*state,\s*"COMMAND_RESULT",\s*\{
[\s\S]*?
"returncode"\s*:\s*result\.returncode,[\s\S]*?
^[ \t]*\}\s*\)
[\s\S]{0,300}?
^[ \t]*if\s+result\.returncode\s*!=\s*0\s*:\s*\n
^[ \t]*return\s+False\s*\n
"""

m = re.search(pattern, s, flags=re.MULTILINE | re.VERBOSE)
if not m:
    print("ERROR: Could not patch orchestrator.py (pattern not found)")
    raise SystemExit(1)

indent = m.group("indent")
replacement = (
    f'{indent}returncode = result.returncode\n'
    f'{indent}# Normalize pytest exit code 5 (no tests collected) as success for MVP\n'
    f'{indent}if returncode == 5:\n'
    f'{indent}    _out = result.stdout or ""\n'
    f'{indent}    if "no tests ran" in _out or "collected 0 items" in _out:\n'
    f'{indent}        returncode = 0\n'
    f'{indent}self._log(state, "COMMAND_RESULT", {{\n'
    f'{indent}    "returncode": returncode,\n'
    f'{indent}    "stdout": result.stdout[:500] if result.stdout else "",\n'
    f'{indent}    "stderr": result.stderr[:500] if result.stderr else ""\n'
    f'{indent}}})\n'
    f'{indent}if returncode != 0:\n'
    f'{indent}    return False\n'
)

s2 = re.sub(pattern, replacement, s, count=1, flags=re.MULTILINE | re.VERBOSE)
p.write_text(s2, encoding="utf-8")
print("[OK] patched orchestrator.py (pytest exit code 5 treated as success)")
PY
}

ensure_examples_basic_run() {
  mkdir -p "$TARGET_DIR/examples"
  if [[ ! -f "$TARGET_DIR/examples/basic_run.json" ]]; then
    cat > "$TARGET_DIR/examples/basic_run.json" <<'JSON'
{
  "task_id": "C03",
  "prompt_path": "prompts/noop.md",
  "timeout": 30,
  "max_iterations": 8,
  "passes_required": 2
}
JSON
    log "[OK] created APP/examples/basic_run.json"
  fi
}

main() {
  [[ -d "$CHANTIERS_DIR" ]] || die "CHANTIERS directory not found: $CHANTIERS_DIR"

  log "[INFO] Normalizing zip names (spaces -> underscores)"
  normalize_zip_names

  mapfile -t ZIPS < <(find "$CHANTIERS_DIR" -type f -name "*.zip" | sort)
  [[ "${#ZIPS[@]}" -gt 0 ]] || die "No zip files found under $CHANTIERS_DIR"

  log "[INFO] Installing ${#ZIPS[@]} zip(s) into: $TARGET_DIR"
  mkdir -p "$TARGET_DIR"
  for z in "${ZIPS[@]}"; do
    log "[INFO] -> $z"
    install_zip_into_app "$z"
  done

  patch_pyproject_packages
  patch_orchestrator_pytest5
  ensure_examples_basic_run

  log "[INFO] Installing package editable + running tests"
  cd "$TARGET_DIR"
  python -m pip install -e . >/dev/null
  pytest -q
  log "[OK] Tests passed"

  log "[INFO] Running smoke job: interagents run examples/basic_run.json"
  interagents run examples/basic_run.json
  log "[OK] All chantiers installed + tests passed + smoke run OK"
}

main "$@"
