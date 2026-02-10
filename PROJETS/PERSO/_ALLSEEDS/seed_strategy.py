
def next_bet_amount(loss_accum: float, base: float, mode: str):
    if mode == "+10":
        return loss_accum + base
    if mode == "x2":
        return max(base, (loss_accum * 2.0) if loss_accum > 0 else base)
    if mode == "x2.5":
        return max(base, (loss_accum * 2.5) if loss_accum > 0 else base)
    return base

def run_seed(symbol: str, price_pairs, base: float, max_tours: int, rattrapage: str,
             payoff_mode: str = "binary", fees_pct_roundtrip: float = 0.0):
    tours = []
    loss_accum = 0.0
    for i in range(min(max_tours, len(price_pairs))):
        bet = next_bet_amount(loss_accum, base, rattrapage if loss_accum>0 else "+0")
        open_p, close_p = price_pairs[i]
        if payoff_mode == "binary":
            win = (close_p > open_p)
            pnl = bet if win else -bet
        else:
            pct = (close_p - open_p) / open_p
            pnl = bet * pct
            pnl -= bet * (fees_pct_roundtrip/100.0)
        tours.append({"tour": i+1, "bet": float(bet), "pnl": float(pnl)})
        if pnl < 0:
            loss_accum += -pnl
        else:
            loss_accum = 0.0
    total = sum(t["pnl"] for t in tours)
    return {"symbol": symbol, "tours": tours, "total_pnl": float(total)}
