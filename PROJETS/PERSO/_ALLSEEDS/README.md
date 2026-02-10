
# _ALLSEEDS_STREAMLIT_ALGO_PUR

Interface Streamlit pour valider la stratégie "roulette" **avec pause après perte** (algo pur 50/50).

## Lancer
```bash
pip install streamlit pyyaml pandas numpy
streamlit run interface_dashboard.py
```

## Ce que ça fait
- 50/50 aléatoire, payoff **binaire**, **sans frais**
- Règle **pause après perte** (attente du trigger puis remise au tour suivant)
- Rattrapage configurable : `+10`, `x2`, `x2.5`
- Export CSV automatique : `ALGO_PUR_export.csv`
