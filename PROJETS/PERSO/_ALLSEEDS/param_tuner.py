import yaml, itertools
from copy import deepcopy
from backtester import backtest_once

GRID = {
    "base_investment": [5, 10, 20],
    "max_tours": [5, 10],
    "rattrapage": ["+10", "x2", "x2.5"],
}

def product_dict(d):
    keys = list(d.keys())
    import itertools
    for values in itertools.product(*d.values()):
        yield dict(zip(keys, values))

def tune(cfg_path="config.yaml"):
    with open(cfg_path,"r") as f:
        cfg = yaml.safe_load(f)
    results = []
    for combo in product_dict(GRID):
        local = deepcopy(cfg)
        for k,v in combo.items():
            local[k] = v
        out = backtest_once(local)
        total = out["summary"].get("total_pnl",0.0)
        results.append({"params": combo, "total_pnl": total, "summary": out["summary"]})
    results.sort(key=lambda x: x["total_pnl"], reverse=True)
    return results
