from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .method import Method, PermissionGate


@dataclass
class Scenario(Method):
    steps: List[Method] = field(default_factory=list)

    def execute(self, what_item: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        out: Dict[str, Any] = {"steps": []}
        for step in self.steps:
            ok_b, data_b = step.before(what_item, ctx)
            if not ok_b:
                ok_f, data_f = step.failure(what_item, ctx)
                out["steps"].append({"name": step.name, "ok": ok_f, "phase": "before", "data": {**data_b, **data_f}})
                if not ok_f:
                    return False, out
                continue

            ok_x, data_x = step.execute(what_item, ctx)
            if not ok_x:
                ok_f, data_f = step.failure(what_item, ctx)
                out["steps"].append({"name": step.name, "ok": ok_f, "phase": "execute", "data": {**data_x, **data_f}})
                if not ok_f:
                    return False, out
                continue

            ok_a, data_a = step.after(what_item, ctx)
            out["steps"].append({"name": step.name, "ok": ok_a, "phase": "after", "data": {**data_b, **data_x, **data_a}})
            if not ok_a:
                return False, out

        return True, out


@dataclass
class GetOrCreateScenario(Scenario):
    get_method: Method = field(default_factory=lambda: Method(name="get"))
    create_method: Method = field(default_factory=lambda: Method(name="create"))

    def __post_init__(self) -> None:
        if not self.steps:
            self.steps = [self.get_method]

    def execute(self, what_item: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        ok_b, data_b = self.get_method.before(what_item, ctx)
        if not ok_b:
            ok_f, data_f = self.get_method.failure(what_item, ctx)
            return ok_f, {"phase": "get.before", "data": {**data_b, **data_f}}

        ok_x, data_x = self.get_method.execute(what_item, ctx)
        if ok_x:
            ok_a, data_a = self.get_method.after(what_item, ctx)
            return ok_a, {"phase": "get.after", "data": {**data_b, **data_x, **data_a}}

        if not self.create_method.permission.allowed:
            return False, {
                "phase": "create.blocked",
                "data": {
                    "reason": self.create_method.permission.reason or "create not permitted",
                    "get_error": data_x,
                },
            }

        ok_cb, data_cb = self.create_method.before(what_item, ctx)
        if not ok_cb:
            ok_cf, data_cf = self.create_method.failure(what_item, ctx)
            return ok_cf, {"phase": "create.before", "data": {**data_cb, **data_cf}}

        ok_cx, data_cx = self.create_method.execute(what_item, ctx)
        if not ok_cx:
            ok_cf, data_cf = self.create_method.failure(what_item, ctx)
            return ok_cf, {"phase": "create.execute", "data": {**data_cx, **data_cf}}

        ok_ca, data_ca = self.create_method.after(what_item, ctx)
        return ok_ca, {"phase": "create.after", "data": {**data_cb, **data_cx, **data_ca}}
