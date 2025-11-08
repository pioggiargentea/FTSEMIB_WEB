
import numpy as np
import pandas as pd

def compute_equity_from_daily_returns(daily_returns: np.ndarray) -> pd.Series:
    """
    Calcola equity normalizzata base=1 da un array di ritorni giornalieri.
    """
    if daily_returns is None or len(daily_returns) == 0:
        return pd.Series(dtype=float)
    equity = (1.0 + pd.Series(daily_returns).fillna(0.0)).cumprod()
    equity /= float(equity.iloc[0]) if len(equity) else 1.0
    return equity

def compute_metrics_from_equity(equity: pd.Series) -> dict:
    """
    Metriche base: Max Drawdown % e CAGR %.
    """
    if equity is None or equity.empty:
        return {"max_dd_%": 0.0, "cagr_%": 0.0}

    eq = equity.astype(float).values
    roll_max = np.maximum.accumulate(eq)
    dd = (eq / roll_max - 1.0).min() * 100.0

    # CAGR
    # Nota: l'indice dell'equity deve essere un DatetimeIndex
    idx = equity.index
    if not isinstance(idx, pd.DatetimeIndex) or len(idx) < 2:
        return {"max_dd_%": float(dd), "cagr_%": 0.0}
    n_days = (idx[-1] - idx[0]).days
    if n_days <= 0 or eq[-1] <= 0:
        cagr = 0.0
    else:
        years = n_days / 365.25
        cagr = (eq[-1] ** (1.0 / years) - 1.0) * 100.0

    return {"max_dd_%": float(dd), "cagr_%": float(cagr)}
