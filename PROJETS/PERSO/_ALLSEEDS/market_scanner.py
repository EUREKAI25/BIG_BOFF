import ccxt
import math

def scan_top_usdt(exchange_name="binance", quote="USDT",
                  max_symbols=10, min_quote_volume_24h=3_000_000, min_amp_24h_pct=1.0):
    ex = getattr(ccxt, exchange_name)()
    ex.load_markets()
    tickers = ex.fetch_tickers()
    scored = []
    for sym, t in tickers.items():
        try:
            if not sym.endswith(f"/{quote}"):
                continue
            qv = t.get("quoteVolume") or t.get("info", {}).get("quoteVolume")
            if qv is None:
                continue
            qv = float(qv)
            if qv < float(min_quote_volume_24h):
                continue
            pct = t.get("percentage")
            if pct is None:
                pct = 0.0
            amp = abs(float(pct))
            if amp < float(min_amp_24h_pct):
                continue
            score = amp * math.log(qv + 1.0)
            scored.append((sym, score))
        except Exception:
            continue
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in scored[:max_symbols]]
