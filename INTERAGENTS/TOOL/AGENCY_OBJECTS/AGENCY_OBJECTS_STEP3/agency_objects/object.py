from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Object:
    name: str
    elementlist: List[Dict[str, Any]] = field(default_factory=list)
    taglist: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "elementlist": self.elementlist,
            "taglist": self.taglist,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Object":
        return cls(
            name=str(data.get("name", "")),
            elementlist=list(data.get("elementlist") or []),
            taglist=list(data.get("taglist") or []),
        )
