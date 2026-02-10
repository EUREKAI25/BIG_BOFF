class LiveTrader:
    def __init__(self, dry_run: bool = True, base_symbol: str = "USDT"):
        self.dry_run = dry_run
        self.base_symbol = base_symbol
        self.logs = []

    def simulate_order(self, symbol: str, notional: float):
        """Log d’intention d’ordre (market), utilisé quand dry_run=True."""
        self.logs.append({"symbol": symbol, "notional": notional, "status": "simulated"})

    # Exemple pour brancher de vrais ordres plus tard:
    # def place_market_order(self, client, symbol: str, side: str, quantity: float):
    #     if self.dry_run:
    #         self.logs.append({"symbol": symbol, "side": side, "qty": quantity, "status": "dry_run"})
    #         return {"dry_run": True}
    #     return client.new_order(symbol=symbol.replace("/", ""),
    #                             side=side, type="MARKET", quantity=quantity)
