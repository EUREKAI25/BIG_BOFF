from core.Model import bootstrap_models
from core.Prompts import PromptStore
from core.Agent import AIAgent

bootstrap_models()

store = PromptStore("./prompts")
agent = AIAgent("core_agent", prompt_store=store, type_model="text")

res = agent.choose(
    options=[{"id": "a", "label": "Option A"}, {"id": "b", "label": "Option B"}],
    rules={"goal": "pick the best", "constraints": ["simple", "stable"]}
)

print(res)
