from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .method import Method
from .walker import Walker


@dataclass
class MRGContext:
    run_id: str = ""
    logs: List[Dict[str, Any]] = field(default_factory=list)

    def log(self, event: str, data: Dict[str, Any]) -> None:
        self.logs.append({"event": event, "data": data})


@dataclass
class MRG:
    walker: Walker = field(default_factory=Walker)

    def apply(self, what: Dict[str, Any], how: Method, ctx: MRGContext) -> Tuple[bool, Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        ok_all = True

        def _fn(node: Dict[str, Any], path: List[str]) -> None:
            nonlocal ok_all
            ctx.log("STEP_EXECUTE", {"path": path, "method": how.name, "node_name": node.get("name", "")})

            ok_b, data_b = how.before(node, {"mrg": ctx})
            if not ok_b:
                ok_f, data_f = how.failure(node, {"mrg": ctx})
                results.append({"path": path, "ok": ok_f, "phase": "before", "data": {**data_b, **data_f}})
                ok_all = ok_all and ok_f
                return

            ok_x, data_x = how.execute(node, {"mrg": ctx})
            if not ok_x:
                ok_f, data_f = how.failure(node, {"mrg": ctx})
                results.append({"path": path, "ok": ok_f, "phase": "execute", "data": {**data_x, **data_f}})
                ok_all = ok_all and ok_f
                return

            ok_a, data_a = how.after(node, {"mrg": ctx})
            results.append({"path": path, "ok": ok_a, "phase": "after", "data": {**data_b, **data_x, **data_a}})
            ok_all = ok_all and ok_a

        self.walker.walk(what, _fn, [])
        return ok_all, {"results": results, "logs": ctx.logs}
