import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Dict, List

from core.Object import Object
from core.Env import Env
from core.Metrics import Usage, Metrics


@dataclass
class Model(Object):
    id: str
    type: str
    provider: str
    status: str                 # "active" | "inactive"
    name: Optional[str] = None

    currency: str = "EUR"
    cost_in_per_1k: float = 0.0
    cost_out_per_1k: float = 0.0

    usage: Usage = Usage()

    def estimate_cost_eur(self, tokens_in: int, tokens_out: int) -> float:
        return (tokens_in / 1000.0) * float(self.cost_in_per_1k) + (tokens_out / 1000.0) * float(self.cost_out_per_1k)

    def _record(self, ms: int, tokens_in: int, tokens_out: int):
        self.usage.calls += 1
        self.usage.ms_total += int(ms)
        self.usage.tokens_in += int(tokens_in)
        self.usage.tokens_out += int(tokens_out)
        self.usage.eur_total += float(self.estimate_cost_eur(tokens_in, tokens_out))

    def execute(self, prompt: str, datas: Optional[dict] = None) -> str:
        raise NotImplementedError

    def test_call(self) -> Dict[str, Any]:
        # test minimal standard : un appel + parse JSON
        start = Metrics.now_ms()
        raw = self.execute(prompt="ping", datas={"test": True})
        ms = Metrics.elapsed_ms(start)
        # tokens: mock simple
        tokens_in = len("ping") // 4
        tokens_out = len(raw) // 4
        self._record(ms, tokens_in, tokens_out)
        try:
            parsed = json.loads(raw)
            return {"ok": True, "ms": ms, "parsed": parsed}
        except Exception:
            return {"ok": False, "ms": ms, "error": "JSON_PARSE_ERROR", "raw": raw}


# ---- MOCK MODELS (1 par type) ----

class MockTextToText(Model):
    def execute(self, prompt: str, datas: Optional[dict] = None) -> str:
        # déterministe
        if "base project" in prompt:
            return json.dumps({"result": "base_project"})
        if prompt == "ping":
            return json.dumps({"result": "pong"})
        return json.dumps({"result": "NONE"})


class MockTextToImage(Model):
    def execute(self, prompt: str, datas: Optional[dict] = None) -> str:
        if prompt == "ping":
            return json.dumps({"result": "pong"})
        return json.dumps({"result": "MOCK_IMAGE_ID"})


class MockImageToImage(Model):
    def execute(self, prompt: str, datas: Optional[dict] = None) -> str:
        if prompt == "ping":
            return json.dumps({"result": "pong"})
        return json.dumps({"result": "MOCK_IMAGE_ID"})


class MockSpeechToText(Model):
    def execute(self, prompt: str, datas: Optional[dict] = None) -> str:
        if prompt == "ping":
            return json.dumps({"result": "pong"})
        return json.dumps({"result": "MOCK_TRANSCRIPT"})


class MockTextToSpeech(Model):
    def execute(self, prompt: str, datas: Optional[dict] = None) -> str:
        if prompt == "ping":
            return json.dumps({"result": "pong"})
        return json.dumps({"result": "MOCK_AUDIO_ID"})


MOCK_TYPE_MAP = {
    "text_to_text": MockTextToText,
    "text_to_image": MockTextToImage,
    "image_to_image": MockImageToImage,
    "speech_to_text": MockSpeechToText,
    "text_to_speech": MockTextToSpeech,
}


class ModelRegistry(Object):
    def __init__(self, models: List[Model], env: Env):
        self.models = models
        self.env = env

    @classmethod
    def from_catalog(cls, base_dir: str, env: Env):
        p = Path(base_dir).resolve() / "catalogs" / "models.json"
        raw = json.loads(p.read_text(encoding="utf-8"))
        items = raw.get("models", [])
        models: List[Model] = []

        for it in items:
            provider = it.get("provider", "mock")
            mtype = it.get("type")
            status = it.get("status", "inactive")

            common = dict(
                id=it.get("id"),
                type=mtype,
                provider=provider,
                status=status,
                name=it.get("name"),
                currency=it.get("currency", "EUR"),
                cost_in_per_1k=float(it.get("cost_in_per_1k", 0.0)),
                cost_out_per_1k=float(it.get("cost_out_per_1k", 0.0)),
                usage=Usage(),
            )

            if provider == "mock":
                cls_ = MOCK_TYPE_MAP.get(mtype, Model)
                models.append(cls_(**common))
            else:
                # providers réels -> plus tard
                models.append(Model(**common))

        return cls(models=models, env=env)

    def execute(self, model_type: str, prompt: str, datas: Optional[dict] = None, expect_json: bool = True) -> Dict[str, Any]:
        m = next((x for x in self.models if x.type == model_type and x.status == "active"), None)
        if not m:
            raise RuntimeError(f"NO_ACTIVE_MODEL_FOR_TYPE:{model_type}")

        start = Metrics.now_ms()
        raw = m.execute(prompt, datas)
        ms = Metrics.elapsed_ms(start)

        # tokens: mock simple (on remplacera par vrais chiffres provider)
        tokens_in = len(prompt) // 4
        tokens_out = len(raw) // 4
        m._record(ms, tokens_in, tokens_out)

        if not expect_json:
            return {"raw": raw, "ms": ms}

        try:
            parsed = json.loads(raw)
            # inclure un mini résumé conso
            return {"data": parsed, "usage": {"ms": ms, "tokens_in": tokens_in, "tokens_out": tokens_out, "eur": m.estimate_cost_eur(tokens_in, tokens_out)}}
        except Exception:
            return {"error": "JSON_PARSE_ERROR", "raw": raw, "usage": {"ms": ms}}

    def self_test(self) -> Dict[str, Any]:
        # 1 test_call par modèle ACTIF
        report: Dict[str, Any] = {"ok": True, "models": [], "totals": {"calls": 0, "ms": 0, "tokens_in": 0, "tokens_out": 0, "eur": 0.0}}
        for m in [x for x in self.models if x.status == "active"]:
            r = m.test_call()
            report["models"].append({"id": m.id, "type": m.type, "provider": m.provider, "status": m.status, "ok": r.get("ok"), "ms": r.get("ms")})
            if not r.get("ok"):
                report["ok"] = False

            report["totals"]["calls"] += m.usage.calls
            report["totals"]["ms"] += m.usage.ms_total
            report["totals"]["tokens_in"] += m.usage.tokens_in
            report["totals"]["tokens_out"] += m.usage.tokens_out
            report["totals"]["eur"] += float(m.usage.eur_total)

        return report


def bootstrap_registry(base_dir: str = ".") -> ModelRegistry:
    env = Env()
    env.load()
    return ModelRegistry.from_catalog(base_dir=base_dir, env=env)


def model_execute(model_type: str, prompt: str, datas: Optional[dict] = None) -> Dict[str, Any]:
    reg = bootstrap_registry(base_dir=".")
    return reg.execute(model_type=model_type, prompt=prompt, datas=datas, expect_json=True)
