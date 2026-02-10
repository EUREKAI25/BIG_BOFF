from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple


class HookResult(Protocol):
    ok: bool
    data: Dict[str, Any]


@dataclass(frozen=True)
class PermissionGate:
    allowed: bool = True
    reason: str = ""


HookFn = Callable[[Dict[str, Any], Dict[str, Any]], Tuple[bool, Dict[str, Any]]]
# Hook signature: hook(what_item, ctx) -> (ok, payload)


@dataclass
class Method:
    name: str
    tags: List[str] = field(default_factory=list)
    permission: PermissionGate = field(default_factory=PermissionGate)

    hook_before: Optional[HookFn] = None
    hook_execute: Optional[HookFn] = None
    hook_after: Optional[HookFn] = None
    hook_failure: Optional[HookFn] = None

    def before(self, what_item: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        if self.hook_before is None:
            return True, {}
        return self.hook_before(what_item, ctx)

    def execute(self, what_item: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        if self.hook_execute is None:
            return True, {"noop": True}
        return self.hook_execute(what_item, ctx)

    def after(self, what_item: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        if self.hook_after is None:
            return True, {}
        return self.hook_after(what_item, ctx)

    def failure(self, what_item: Dict[str, Any], ctx: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        if self.hook_failure is None:
            return False, {"error": "failure hook not defined"}
        return self.hook_failure(what_item, ctx)
