
import streamlit as st
import pandas as pd
import yaml
from pathlib import Path
from backtester import run_from_config

CFG_PATH = Path("config.yaml")

def load_cfg():
    if CFG_PATH.exists():
        with open(CFG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_cfg(cfg: dict):
    with open(CFG_PATH, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)

st.set_page_config(page_title="ALLSEEDS — Algo Pur (pause)", layout="wide")
st.title("ALLSEEDS — Validation Algo Pur (pause après perte)")

cfg = load_cfg()

st.sidebar.header("🎛️ Preset")
if st.sidebar.button("ALGO PUR (pause) — appliquer"):
    cfg = {
        "engine": {"mode": "blind", "rng_seed": 42},
        "base_investment": 10.0,
        "rattrapage": "+10",
        "max_tours": 10,
        "backtest": {"seeds": 1000},
    }
    save_cfg(cfg)
    st.sidebar.success("Preset appliqué.")

st.sidebar.header("Paramètres")
cfg.setdefault("engine", {}).setdefault("rng_seed", 42)
cfg["engine"]["rng_seed"] = st.sidebar.number_input("rng_seed", 0, 10**9, int(cfg["engine"]["rng_seed"]))

cfg["base_investment"] = st.sidebar.number_input("Mise de base", 1.0, 10000.0, float(cfg.get("base_investment", 10.0)))
cfg["rattrapage"] = st.sidebar.selectbox("Rattrapage", ["+10","x2","x2.5"], index=["+10","x2","x2.5"].index(cfg.get("rattrapage","+10")))
cfg["max_tours"] = st.sidebar.number_input("Tours max par graine", 1, 50, int(cfg.get("max_tours", 10)))
cfg.setdefault("backtest", {})["seeds"] = st.sidebar.number_input("Nombre de graines", 1, 5000, int(cfg.get("backtest",{}).get("seeds", 1000)))

if st.sidebar.button("💾 Enregistrer"):
    save_cfg(cfg)
    st.sidebar.success("Config sauvegardée.")

st.caption("Mode courant : **ALGO PUR (pause)** — binaire, sans frais, 50/50")

if st.button("▶️ Lancer"):
    save_cfg(cfg)
    progress = st.progress(0, text="Préparation…")
    def cb(phase, i, total, info):
        if phase == "seeds" and total > 0:
            pct = min(100, int(100 * (i / max(1, total))))
            progress.progress(pct, text=f"Graines {i}/{total} — {info}")
    with st.spinner("Exécution en cours…"):
        out = run_from_config(str(CFG_PATH), progress_cb=cb)
        progress.progress(100, text="Terminé ✓")
        st.session_state["last_run"] = out

st.markdown("---")

if "last_run" in st.session_state:
    out = st.session_state["last_run"]
    st.subheader("Résumé")
    st.json(out.get("summary", {}))

    details = out.get("details", [])
    if details:
        rows = []
        for d in details:
            for t in d["tours"]:
                rows.append({"symbol": d["symbol"], **t})
        if rows:
            df = pd.DataFrame(rows)
            st.subheader("Détails tours")
            st.dataframe(df, use_container_width=True)

    export_path = out.get("export")
    if export_path:
        st.success(f"Export CSV prêt : {export_path}")
