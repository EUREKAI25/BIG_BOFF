import numpy as np
import pandas as pd

def simple_volatility_score(df: pd.DataFrame) -> float:
    if df is None or len(df) < 10:
        return 0.0
    closes = df["close"].values
    returns = np.diff(closes) / closes[:-1] * 100.0
    amp = np.mean(np.abs(returns))
    signs = np.sign(returns)
    inversions = np.sum(np.abs(np.diff(signs)) > 0)
    freq = inversions / max(1, len(returns))
    tr = df["high"] - df["low"]
    atr = tr.rolling(14).mean().iloc[-1] if len(tr) >= 14 else tr.mean()
    atr_pct = float(atr / df["close"].iloc[-1] * 100.0)
    score = float(0.5*amp + 0.3*freq*100 + 0.2*atr_pct)
    return score
