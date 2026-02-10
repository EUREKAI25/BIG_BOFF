def estimate_p_win(vol_score: float) -> float:
    base = 0.5
    boost = min(0.15, vol_score/800.0)
    return base + boost

def route(symbol_scores, cfg_router: dict):
    min_ev = float(cfg_router.get("min_ev", 0.0))
    p_floor = float(cfg_router.get("p_win_floor", 0.48))
    gain_pct = float(cfg_router.get("est_gain_pct", 0.5))
    loss_pct = float(cfg_router.get("est_loss_pct", 0.4))
    fees_pct = float(cfg_router.get("fees_pct_roundtrip", 0.05))

    candidates = []
    for sym, score in symbol_scores:
        p_win = estimate_p_win(score)
        ev = p_win*gain_pct - (1-p_win)*loss_pct - fees_pct
        if p_win >= p_floor and ev >= min_ev:
            candidates.append((sym, p_win, ev))
    candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)

    if not candidates and symbol_scores:
        top = sorted(symbol_scores, key=lambda x: x[1], reverse=True)[:5]
        candidates = [(sym, 0.51, -fees_pct) for sym, _ in top]
    return candidates
