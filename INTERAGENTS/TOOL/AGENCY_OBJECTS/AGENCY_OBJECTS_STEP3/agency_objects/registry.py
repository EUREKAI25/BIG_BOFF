from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .method import Method
from .scenario import Scenario


@dataclass
class Registry:
    methods: Dict[str, Method] = field(default_factory=dict)
    scenarios: Dict[str, Scenario] = field(default_factory=dict)

    def register_method(self, m: Method) -> None:
        self.methods[m.name] = m

    def register_scenario(self, s: Scenario) -> None:
        self.scenarios[s.name] = s

    def get(self, name: str) -> Optional[Method]:
        if name in self.scenarios:
            return self.scenarios[name]
        return self.methods.get(name)
