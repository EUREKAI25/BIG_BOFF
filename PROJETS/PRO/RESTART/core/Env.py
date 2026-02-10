import os
from core.Object import Object

try:
    from dotenv import load_dotenv as _load_dotenv
except Exception:
    _load_dotenv = None


class Env(Object):
    def load(self):
        if _load_dotenv:
            _load_dotenv()
        return True

    def load_mock(self):
        return True

    def get(self, key: str, default=None):
        return os.getenv(key, default)

    def get_mock(self, key: str, default=None):
        return default

    def require(self, key: str) -> str:
        v = os.getenv(key)
        if not v:
            raise RuntimeError(f"ENV_MISSING:{key}")
        return v

    def require_mock(self, key: str) -> str:
        return "MOCK_VALUE"
