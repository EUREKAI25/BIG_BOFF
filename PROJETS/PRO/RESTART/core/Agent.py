import json
from typing import Optional
from core.Object import Object
from core.System import System
from core.Model import ModelRegistry, bootstrap_registry

class Agent(Object):
    def __init__(self, system: System, registry: Optional[ModelRegistry] = None):
        self.system = system
        self.registry = registry or bootstrap_registry(base_dir=".")

    def choose(self, options: list, context: Optional[dict] = None) -> dict:
        context = context or {}
        prompt = self.system.render(
            "choose",
            {
                "options_json": json.dumps(options, ensure_ascii=False),
                "context_json": json.dumps(context, ensure_ascii=False),
            },
        )
        res = self.registry.execute(
            model_type="text_to_text",
            prompt=prompt,
            datas={"options": options, "context": context},
            expect_json=True,
        )
        # standard: on renvoie le dict "data"
        data = res.get("data", {})
        return data

    def choose_mock(self, options: list, context: Optional[dict] = None) -> dict:
        return {"result": "NONE"}
