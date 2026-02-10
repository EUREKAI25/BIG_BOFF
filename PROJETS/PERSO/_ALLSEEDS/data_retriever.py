import ccxt
import pandas as pd
import os
from datetime import datetime, timedelta

CACHE_DIR = "data_cache"

def get_exchange(name: str = "binance"):
    name = name.lower()
    if not hasattr(ccxt, name):
        raise ValueError(f"Exchange '{name}' not supported in ccxt.")
    return getattr(ccxt, name)()

def cache_path(symbol: str, timeframe: str):
    safe = symbol.replace("/", "_")
    return os.path.join(CACHE_DIR, f"{safe}_{timeframe}.csv")

def load_cached(symbol: str, timeframe: str, max_age_hours: int):
    path = cache_path(symbol, timeframe)
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path, parse_dates=["ts"])
        if df.empty:
            return None
        age = datetime.utcnow() - df["ts"].iloc[-1].to_pydatetime()
        if age <= timedelta(hours=max_age_hours):
            return df
    except Exception:
        return None
    return None

def save_cache(symbol: str, timeframe: str, df: pd.DataFrame):
    path = cache_path(symbol, timeframe)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)

def fetch_ohlcv(symbol: str, timeframe: str = "1m", limit: int = 200, exchange_name: str = "binance",
                use_cache=True, cache_expiry_hours=12):
    if use_cache:
        cached = load_cached(symbol, timeframe, cache_expiry_hours)
        if cached is not None and len(cached) >= min(50, limit//2):
            return cached.tail(limit).copy()

    ex = get_exchange(exchange_name)
    ex.load_markets()
    sym = symbol
    if sym not in ex.markets and sym.replace("/", "") in ex.markets:
        sym = sym.replace("/", "")
    ohlcv = ex.fetch_ohlcv(sym, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    save_cache(symbol, timeframe, df)
    return df
