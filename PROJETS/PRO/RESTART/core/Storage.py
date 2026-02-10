import json
import time
from pathlib import Path
from core.Object import Object

class FileStorage(Object):
    def save(self, obj, cfg: dict):
        base_dir = Path(cfg.get("base_dir", "storage")).resolve()
        collection = cfg.get("collection", obj.__class__.__name__)
        folder = base_dir / collection
        folder.mkdir(parents=True, exist_ok=True)

        d = obj.to_dict() if hasattr(obj, "to_dict") else dict(obj.__dict__)
        obj_id = d.get("id") or d.get("name") or str(int(time.time() * 1000))
        path = folder / f"{obj_id}.json"
        path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

        return {"storage": "filesystem", "path": str(path)}

    def save_mock(self, obj, cfg: dict):
        return {"storage": "mock", "path": "MOCK://filesystem"}
