import numpy as np

class SignalAPI:
    def __init__(self, mode: str = "random", p_random: float = 0.5, event_threshold_pct: float = 0.5, min_gap_min: int = 10):
        self.mode = mode
        self.p_random = p_random
        self.event_threshold_pct = event_threshold_pct
        self.min_gap_min = min_gap_min
        self._last_signal_ts = {}

    def _respect_gap(self, seed_id: str, ts) -> bool:
        if seed_id not in self._last_signal_ts:
            return True
        last = self._last_signal_ts[seed_id]
        if ts is None or last is None:
            return True
        mins = (ts - last).total_seconds() / 60.0
        return mins >= self.min_gap_min

    def next(self, seed_id: str, ts, df=None):
        if not self._respect_gap(seed_id, ts):
            return {"seed_id": seed_id, "signal_on": False, "reason": "cooldown"}
        if self.mode == "random":
            val = np.random.rand() < float(self.p_random)
            if val:
                self._last_signal_ts[seed_id] = ts
            return {"seed_id": seed_id, "signal_on": bool(val), "reason": "random"}
        elif self.mode == "event":
            if df is None or len(df) < 3:
                return {"seed_id": seed_id, "signal_on": False, "reason": "no_data"}
            ret_pct = (df["close"].iloc[-1] - df["close"].iloc[-3]) / df["close"].iloc[-3] * 100.0
            ok = abs(ret_pct) >= float(self.event_threshold_pct)
            if ok:
                self._last_signal_ts[seed_id] = ts
            return {"seed_id": seed_id, "signal_on": bool(ok), "reason": "event"}
        else:
            return {"seed_id": seed_id, "signal_on": False, "reason": "unknown_mode"}
