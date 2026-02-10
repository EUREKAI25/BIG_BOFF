from pathlib import Path
from core.Object import Object
from core.Storage import FileStorage

class System(Object):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.prompts_dir = self.base_dir / "prompts"
        self._filestorage = FileStorage()

    def render(self, template_id: str, vars: dict) -> str:
        p = self.prompts_dir / f"{template_id}.txt"
        tpl = p.read_text(encoding="utf-8")
        return tpl.format(**vars)

    def render_mock(self, template_id: str, vars: dict) -> str:
        return f"[MOCK_TEMPLATE:{template_id}] " + str(vars)

    def save(self, obj, storage_cfg: dict):
        stype = storage_cfg.get("type", "filesystem")
        if stype == "filesystem":
            cfg = dict(storage_cfg)
            # base_dir relatif -> storage/
            cfg.setdefault("base_dir", str(self.base_dir / "storage"))
            return self._filestorage.save(obj, cfg)
        raise RuntimeError(f"STORAGE_NOT_SUPPORTED:{stype}")

    def save_mock(self, obj, storage_cfg: dict):
        return {"storage": "mock", "path": "MOCK://save"}
