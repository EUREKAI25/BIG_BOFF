import time
from dataclasses import dataclass

@dataclass
class Usage:
    calls: int = 0
    ms_total: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    eur_total: float = 0.0

class Metrics:
    @staticmethod
    def now_ms() -> int:
        return int(time.perf_counter() * 1000)

    @staticmethod
    def elapsed_ms(start_ms: int) -> int:
        return Metrics.now_ms() - start_ms
