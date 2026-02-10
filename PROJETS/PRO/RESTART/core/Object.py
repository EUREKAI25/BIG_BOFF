import json
import time
from dataclasses import is_dataclass, asdict

class Object:
    SCHEMA = None  # override in subclasses

    def get(self, key, default=None):
        return getattr(self, key, default)

    @classmethod
    def schema(cls) -> dict:
        return cls.SCHEMA or {}

    def to_dict(self) -> dict:
        if is_dataclass(self):
            return asdict(self)
        return dict(self.__dict__)

    @classmethod
    def _apply_schema(cls, data: dict) -> dict:
        s = cls.schema()
        fields = (s.get("fields") or {})
        out = dict(data or {})

        for k, spec in fields.items():
            required = bool(spec.get("required", False))
            default = spec.get("default", None)
            if k not in out or out[k] is None:
                if required and default is None:
                    raise RuntimeError(f"SCHEMA_MISSING_REQUIRED:{cls.__name__}.{k}")
                if k not in out:
                    out[k] = default

        return out

    @classmethod
    def create(cls, data: dict, system=None):
        # 1) schema -> validate/fill
        filled = cls._apply_schema(data)

        # 2) instantiate
        obj = cls(**filled)

        # 3) save if schema.storage + system provided
        s = cls.schema()
        storage_cfg = s.get("storage")
        if storage_cfg and system is not None:
            saved = system.save(obj, storage_cfg)
            return obj, saved

        return obj

    @classmethod
    def create_mock(cls, data: dict, system=None):
        return cls.create(data, system=system)
