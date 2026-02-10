
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from typing import Optional, Callable

from blind_engine import generate_pairs_with_wait
from seed_strategy import run_seed

def run_blind_wait(cfg, progress_cb: Optional[Callable[[str,int,int,str], None]] = None):
    seeds = int(cfg.get("backtest", {}).get("seeds", 10))
    base = float(cfg.get("base_investment", 10))
    max_tours = int(cfg.get("max_tours", 10))
    rattrapage = cfg.get("rattrapage", "+10")
    rng_seed = int(cfg.get("engine", {}).get("rng_seed", 42))

    rng = np.random.default_rng(rng_seed)

    if progress_cb:
        progress_cb("fetch", 0, 1, "blind-wait")
        progress_cb("rank", 0, 1, "n/a")
        progress_cb("seeds", 0, seeds, "start")

    details = []
    rows = []
    for s in range(seeds):
        pairs = generate_pairs_with_wait(max_bets=max_tours, rng=rng, trigger_color=1)
        res = run_seed(f"BLIND_{s+1}", pairs, base, max_tours, rattrapage,
                       payoff_mode="binary", fees_pct_roundtrip=0.0)
        details.append(res)
        for t in res["tours"]:
            rows.append({"symbol": res["symbol"], **t})
        if progress_cb:
            progress_cb("seeds", s+1, seeds, f"BLIND_{s+1}")

    total_pnl = float(sum(d["total_pnl"] for d in details))
    summary = {"mode": "blind_wait", "seeds": len(details), "total_pnl": total_pnl, "candidates": seeds}

    df = pd.DataFrame(rows)
    out_path = Path("ALGO_PUR_export.csv")
    df.to_csv(out_path, index=False)

    return {"summary": summary, "details": details, "export": str(out_path)}

def run_from_config(path: str = "config.yaml", progress_cb: Optional[Callable[[str,int,int,str], None]] = None):
    with open(path,"r") as f:
        cfg = yaml.safe_load(f) or {}
    return run_blind_wait(cfg, progress_cb)
