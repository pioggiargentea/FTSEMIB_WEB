
# -*- coding: utf-8 -*-
"""
FTSEMIB NEXT-DAY OPEN — 🏆 MODELLO FINALE CONGELATO
Volumi (OR 10) + SPX_ret >= 0.0%
Basato sulla logica del file originale "Nearer My God to Thee 2.py",
adattato per funzionare sia come script standalone sia come modulo importabile.
"""

import pandas as pd
import numpy as np
import yfinance as yf

# ================= PARAMETRI =================
MAIN_TICKER = "FTSEMIB.MI"
START_DATE  = "2000-01-01"
SPX_TICKER  = "^GSPC"
AUTO_ADJUST = True

TICKERS = {
    "POSTE": "PST.MI",
    "UNIPOL": "UNI.MI",
    "PIRELLI": "PIRC.MI",
    "STELLANTIS": "STLAM.MI",
    "ITALGAS": "IG.MI",
    "ENEL": "ENEL.MI",
    "NEXI": "NEXI.MI",
}

# Fattori volume (come da versione allegata)
VOL_MA10_FACTOR = 0.90
VOL_MA5_FACTOR  = 0.90

# ================= FUNZIONI BASE =================
def download_ohlcv(ticker: str) -> pd.DataFrame | None:
    df = yf.download(
        ticker,
        start=START_DATE,
        interval="1d",
        auto_adjust=AUTO_ADJUST,
        progress=False
    )
    if df is None or df.empty:
        print(f"[WARN] Nessun dato per {ticker}")
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    need = ["Open", "High", "Low", "Close", "Volume"]
    if not all(c in df.columns for c in need):
        print(f"[WARN] Colonne mancanti per {ticker}: {df.columns}")
        return None
    return df[need].dropna()

def bool_series(x, idx):
    s = pd.Series(x, index=idx)
    return s.fillna(False).astype(bool)

def max_dd(equity: np.ndarray) -> float:
    if equity.size == 0:
        return 0.0
    roll_max = np.maximum.accumulate(equity)
    dd = equity / roll_max - 1.0
    return float(dd.min() * 100.0)

def slope_log_equity(equity: np.ndarray) -> float:
    eq = np.asarray(equity, float)
    if len(eq) < 10:
        return 0.0
    eq = np.where(eq <= 0, np.nan)
    s = pd.Series(eq).dropna()
    if len(s) < 10:
        return 0.0
    y = np.log(s.values)
    x = np.arange(len(y))
    b1, _ = np.polyfit(x, y, 1)
    return float(b1)

def sharpe_sortino(returns: np.ndarray) -> tuple[float, float]:
    if returns.size == 0:
        return 0.0, 0.0
    mean = returns.mean()
    std = returns.std()
    if std == 0:
        sharpe = 0.0
    else:
        sharpe = mean / std * np.sqrt(252)
    downside_arr = returns[returns < 0]
    if downside_arr.size == 0:
        sortino = 0.0
    else:
        downside = downside_arr.std()
        sortino = mean / (downside + 1e-9) * np.sqrt(252)
    return float(sharpe), float(sortino)

def eval_next_open(ret_next: pd.Series,
                   signal: pd.Series,
                   idx: pd.DatetimeIndex) -> dict:
    """
    Strategia:
      - signal[t] True => trade su Open[t+1]
      - ret_next[t] = Open[t+1] / Close[t] - 1
    """
    sig = bool_series(signal, idx)
    valid = ~ret_next.isna()
    trade_mask = sig & valid

    if trade_mask.sum() == 0:
        equity = np.ones(len(idx))
        return {
            "n_trades": 0,
            "winrate_%": 0.0,
            "avg_trade_%": 0.0,
            "avg_trade_pts": 0.0,
            "total_ret_%": 0.0,
            "sharpe": 0.0,
            "sortino": 0.0,
            "max_dd_%": 0.0,
            "slope": 0.0,
            "cagr_%": 0.0,
            "equity": equity,
            "daily_returns": np.zeros(len(idx)),
        }

    # Ritorni solo nelle date con trade, 0 altrove
    daily_returns = np.where(trade_mask.values,
                             ret_next.fillna(0.0).values,
                             0.0)
    equity = np.cumprod(1.0 + daily_returns)
    trade_rets = ret_next[trade_mask].values

    winrate = float((trade_rets > 0).mean() * 100.0)
    avg_trade_pct = float(trade_rets.mean() * 100.0)
    avg_trade_pts = float(trade_rets.mean() * 40000.0)  # size future indicativo
    total_ret_pct = float((np.prod(1.0 + trade_rets) - 1.0) * 100.0)
    sharpe, sortino = sharpe_sortino(trade_rets)
    mdd = max_dd(equity)
    slp = slope_log_equity(equity)

    # CAGR
    n_days = (idx[-1] - idx[0]).days
    if n_days <= 0 or equity[-1] <= 0:
        cagr_pct = 0.0
    else:
        years = n_days / 365.25
        cagr = equity[-1] ** (1.0 / years) - 1.0
        cagr_pct = float(cagr * 100.0)

    return {
        "n_trades": int(trade_mask.sum()),
        "winrate_%": winrate,
        "avg_trade_%": avg_trade_pct,
        "avg_trade_pts": avg_trade_pts,
        "total_ret_%": total_ret_pct,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_dd_%": mdd,
        "slope": slp,
        "cagr_%": cagr_pct,
        "equity": equity,
        "daily_returns": daily_returns,
    }

def run_model() -> dict:
    """
    Esegue il modello completo e restituisce:
      - data: DataFrame con FTSE + titoli + SPX
      - idx: index date
      - sig_final: Serie booleana segnali
      - metrics: dict con metriche e equity
    """
    print("[INFO] Scarico FTSEMIB (master timeline)...")
    ftse = download_ohlcv(MAIN_TICKER)
    if ftse is None:
        raise SystemExit("Impossibile scaricare FTSEMIB.MI")
    ftse.columns = [f"FTSE_{c}" for c in ftse.columns]
    data = ftse.copy()

    print("[INFO] Scarico titoli per pattern volumi (LEFT JOIN su FTSE)...")
    used = []
    for name, ticker in TICKERS.items():
        d = download_ohlcv(ticker)
        if (d is None or d.empty) and name == "STELLANTIS":
            print("[INFO] Retry STELLANTIS con STLA.MI...")
            d = download_ohlcv("STLA.MI")
        if d is None or d.empty:
            print(f"[WARN] Escludo {name}")
            continue
        d = d.add_prefix(f"{name}_")
        data = data.join(d, how="left")
        used.append(name)

    print("[INFO] Scarico SPX (LEFT JOIN su FTSE)...")
    spx = download_ohlcv(SPX_TICKER)
    if spx is None:
        raise SystemExit("Impossibile scaricare SPX")
    spx = spx.rename(columns={"Close": "SPX_Close"})
    data = data.join(spx["SPX_Close"], how="left")

    # Pulisci solo righe con FTSE valido
    data = data.dropna(subset=["FTSE_Close"]).copy()
    idx = data.index
    if len(idx) == 0:
        raise SystemExit("Nessuna data valida dopo merge.")
    print(f"[INFO] Range dati FTSE: {idx[0].date()} -> {idx[-1].date()}")
    print(f"[INFO] Titoli effettivamente usati: {used}")

    # ================= PATTERN VOLUMI =================
    def vol_ma_le_factor(prefix, ma_window, factor):
        col = f"{prefix}_Volume"
        if col not in data.columns:
            return pd.Series(False, index=idx)
        v = data[col]
        ma = v.rolling(ma_window).mean()
        return bool_series(v <= factor * ma, idx)

    conds = {}
    if "POSTE" in used:
        conds["POSTE_VOL_MA10_LE_70"] = vol_ma_le_factor("POSTE", 10, VOL_MA10_FACTOR)
    if "UNIPOL" in used:
        conds["UNIPOL_VOL_MA10_LE_70"] = vol_ma_le_factor("UNIPOL", 10, VOL_MA10_FACTOR)
    if "PIRELLI" in used:
        conds["PIRELLI_VOL_MA10_LE_70"] = vol_ma_le_factor("PIRELLI", 10, VOL_MA10_FACTOR)
        conds["PIRELLI_VOL_MA5_LE_70"] = vol_ma_le_factor("PIRELLI", 5, VOL_MA5_FACTOR)
    if "STELLANTIS" in used:
        conds["STELLANTIS_VOL_MA10_LE_70"] = vol_ma_le_factor("STELLANTIS", 10, VOL_MA10_FACTOR)
    if "ITALGAS" in used:
        conds["ITALGAS_VOL_MA10_LE_70"] = vol_ma_le_factor("ITALGAS", 10, VOL_MA10_FACTOR)
    if "ENEL" in used:
        conds["ENEL_VOL_MA10_LE_70"] = vol_ma_le_factor("ENEL", 10, VOL_MA10_FACTOR)
    if "NEXI" in used:
        conds["NEXI_VOL_MA10_LE_70"] = vol_ma_le_factor("NEXI", 10, VOL_MA10_FACTOR)

    if "POSTE" in used and "UNIPOL" in used:
        conds["POSTE_AND_UNIPOL_VOL_MA10_LE_70"] = (
            conds["POSTE_VOL_MA10_LE_70"] & conds["UNIPOL_VOL_MA10_LE_70"]
        )

    # FTSE volume pattern
    ftse_vol = data["FTSE_Volume"]
    ma10_ftse = ftse_vol.rolling(10).mean()
    conds["FTSE_VOL_MA10_LE_70"] = bool_series(ftse_vol <= VOL_MA10_FACTOR * ma10_ftse, idx)

    # OR dei pattern
    sig_or = pd.concat(conds.values(), axis=1).any(axis=1)

    # ================= FILTRO SPX =================
    data["SPX_Ret_1d_%"] = data["SPX_Close"].pct_change(fill_method=None) * 100.0
    filtro_spx = bool_series(data["SPX_Ret_1d_%"] >= 0.0, idx)

    # ================= SEGNALE FINALE =================
    sig_final = sig_or & filtro_spx

    # ================= FTSE RET NEXT OPEN =================
    data["FTSE_Ret_NextOpen"] = data["FTSE_Open"].shift(-1) / data["FTSE_Close"] - 1.0
    ret_next = data["FTSE_Ret_NextOpen"]

    metrics = eval_next_open(ret_next, sig_final, idx)
    equity = metrics["equity"]

    return {
        "data": data,
        "idx": idx,
        "sig_final": sig_final,
        "metrics": metrics,
        "equity": equity,
    }

if __name__ == "__main__":
    res = run_model()
    m = res["metrics"]
    print("\n=== 🏆 MODELLO FINALE CONGELATO: VOLUMI (OR 10) + SPX_ret>=0.0% ===")
    for k, v in m.items():
        if k not in ("equity", "daily_returns"):
            print(f"{k}: {v:.4f}" if isinstance(v, (int, float)) else f"{k}: {v}")
    ld = res["idx"][-1]
    sig = bool(res["sig_final"].loc[ld])
    print("\n=== 🔔 SEGNALE PER LA PROSSIMA APERTURA FTSEMIB ===")
    print(f"Ultima data disponibile: {ld.date()}")
    print("Filtro SPX: SPX_ret>=0.0%")
    print(f"Segnale su prossima apertura: {'✅ LONG' if sig else '⛔ Nessun segnale'}")
