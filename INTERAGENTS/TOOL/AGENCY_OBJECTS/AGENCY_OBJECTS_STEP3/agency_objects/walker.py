from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class Walker:
    def walk(self, node: Dict[str, Any], fn: Callable[[Dict[str, Any], List[str]], None], path: List[str] | None = None) -> None:
        if path is None:
            path = []
        fn(node, path)

        el = node.get("elementlist")
        if isinstance(el, list):
            for i, child in enumerate(el):
                if isinstance(child, dict):
                    self.walk(child, fn, path + [f"elementlist[{i}]"])
