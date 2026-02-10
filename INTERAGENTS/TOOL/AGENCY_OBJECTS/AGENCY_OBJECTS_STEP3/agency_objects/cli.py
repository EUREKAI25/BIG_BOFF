from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from .mrg import MRG, MRGContext
from .method import Method, PermissionGate
from .scenario import GetOrCreateScenario


def _load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return json.loads(p.read_text(encoding="utf-8"))


def _ensure_workspace(ws: Path) -> None:
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "runs").mkdir(exist_ok=True)
    (ws / "outputs").mkdir(exist_ok=True)
    (ws / "sandbox").mkdir(exist_ok=True)


def cmd_apply(args: argparse.Namespace) -> int:
    ws = Path(args.workspace)
    _ensure_workspace(ws)

    what = _load_json(args.what)

    if args.how == "noop":
        how = Method(name="noop")
    elif args.how == "getOrCreate":
        def get_exec(node, ctx):
            if node.get("missing") is True:
                return False, {"missing": True}
            return True, {"found": True}

        def create_exec(node, ctx):
            node["created"] = True
            node.pop("missing", None)
            return True, {"created": True}

        get_m = Method(name="get", hook_execute=get_exec)
        create_m = Method(
            name="create",
            permission=PermissionGate(allowed=not args.create_forbidden, reason="forbidden by CLI flag"),
            hook_execute=create_exec,
        )
        how = GetOrCreateScenario(name="getOrCreate", get_method=get_m, create_method=create_m)
    else:
        print(f"Unknown how: {args.how}", file=sys.stderr)
        return 2

    run_id = str(uuid.uuid4())
    ctx = MRGContext(run_id=run_id)
    ok, payload = MRG().apply(what=what, how=how, ctx=ctx)

    run_file = ws / "runs" / f"{run_id}.json"
    run_file.write_text(json.dumps({"run_id": run_id, "ok": ok, "payload": payload}, indent=2), encoding="utf-8")

    print(run_id)
    return 0 if ok else 1


def cmd_show(args: argparse.Namespace) -> int:
    ws = Path(args.workspace)
    run_file = ws / "runs" / f"{args.run_id}.json"
    if not run_file.exists():
        print(f"Run not found: {args.run_id}", file=sys.stderr)
        return 1
    print(run_file.read_text(encoding="utf-8"))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agency-objects", description="AGENCY_OBJECTS step3 CLI")
    p.add_argument("--workspace", default="./workspace", help="workspace directory")
    sp = p.add_subparsers(dest="cmd", required=True)

    ap = sp.add_parser("apply", help="apply HOW over WHAT using MRG")
    ap.add_argument("--what", required=True, help="path to JSON what")
    ap.add_argument("--how", default="noop", choices=["noop", "getOrCreate"], help="how method/scenario")
    ap.add_argument("--create-forbidden", action="store_true", help="block create step for getOrCreate")
    ap.set_defaults(func=cmd_apply)

    sh = sp.add_parser("show", help="print run json")
    sh.add_argument("run_id", help="run id")
    sh.set_defaults(func=cmd_show)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
