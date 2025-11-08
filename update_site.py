
"""
update_site.py
Esegue il modello "Nearer_My_God_to_Thee_2", calcola equity normalizzata (base=1),
e aggiorna i file JSON usati dal sito statico:
 - equity.json
 - signals.json
Pensato per essere eseguito da GitHub Actions ogni giorno alle 17:30 italiane.
"""

import json
import pandas as pd
from Nearer_My_God_to_Thee_2 import run_model
from equity_calculator import compute_equity_from_daily_returns, compute_metrics_from_equity

def main():
    res = run_model()
    data = res["data"]
    idx = res["idx"]
    sig_final = res["sig_final"]
    metrics = res["metrics"]
    daily_returns = metrics.get("daily_returns")

    # Ricostruisci equity normalizzata base=1 dai daily_returns
    equity_series = compute_equity_from_daily_returns(daily_returns)
    equity_series.index = idx  # allinea a idx principale

    # Salva equity.json per Plotly
    equity_payload = [
        {"date": str(d.date()), "equity": float(e)}
        for d, e in zip(equity_series.index, equity_series.values)
    ]
    with open("equity.json", "w", encoding="utf-8") as f:
        json.dump(equity_payload, f, indent=2)

    # Ultimo segnale
    last_date = idx[-1]
    last_signal = bool(sig_final.loc[last_date])

    # Metriche compatte per il front-end
    eq_metrics = compute_metrics_from_equity(equity_series)

    signal_payload = {
        "ultima_data": str(last_date.date()),
        "signal": "LONG" if last_signal else "NONE",
        "n_trades": int(metrics.get("n_trades", 0)),
        "winrate_%": float(metrics.get("winrate_%", 0.0)),
        "avg_trade_%": float(metrics.get("avg_trade_%", 0.0)),
        "avg_trade_pts": float(metrics.get("avg_trade_pts", 0.0)),
        "total_ret_%": float(metrics.get("total_ret_%", 0.0)),
        "max_dd_%": float(eq_metrics.get("max_dd_%", 0.0)),
        "cagr_%": float(eq_metrics.get("cagr_%", 0.0)),
    }
    with open("signals.json", "w", encoding="utf-8") as f:
        json.dump(signal_payload, f, indent=2)

    print("[OK] equity.json e signals.json aggiornati.")

if __name__ == "__main__":
    main()
