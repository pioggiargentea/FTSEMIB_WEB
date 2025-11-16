# -*- coding: utf-8 -*-
"""
QUANT SUPERIOR LIVE - Sistema di Trading con Export Real-time
Crea dashboard live per monitorare equity curve e metriche del sistema.
Esporta dati in JSON per web app
"""

import numpy as np
import pandas as pd
import yfinance as yf
import json
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

START_DATE = '2010-01-01'
ALLOWED_DAYS = [0, 1, 2, 3]  # Lun-Gio
OUTPUT_FILE = 'docs/data/metrics.json'

def ensure_output_dir():
    os.makedirs('docs/data', exist_ok=True)

def fix_yahoo_df(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = '.'.join(str(x) for x in col for col in df.columns)
    else:
        df.columns = str(c) for c in df.columns
    return df

def extract_single_close(df):
    cols_low = [c.lower() for c in df.columns]
    for t in ['close', 'adj close']:
        if t in cols_low:
            return df[df.columns[cols_low.index(t)]]
    for i, c in enumerate(cols_low):
        if 'close' in c:
            return df[df.columns[i]]
    for c in df.columns:
        if np.issubdtype(df[c].dtype, np.number):
            return df[c]
    raise RuntimeError('Nessuna colonna Close trovata')

def load_ftsemib():
    print('[DOWNLOAD] FTSEMIB.MI...')
    df = yf.download('FTSEMIB.MI', start=START_DATE, interval='1d',
                     auto_adjust=False, progress=False)
    if df is None or df.empty:
        raise RuntimeError('Errore nessun dato FTSEMIB da Yahoo')
    df = fix_yahoo_df(df)
    df = df.sort_index()
    close = extract_single_close(df)
    
    def find_word(words):
        for w in words:
            for col in df.columns:
                if w in col.lower():
                    return col
        return None
    
    o = find_word(['open'])
    h = find_word(['high'])
    l = find_word(['low'])
    v = find_word(['volume'])
    
    if o and h and l:
        out = pd.DataFrame(index=df.index)
        out['Open'] = df[o]
        out['High'] = df[h]
        out['Low'] = df[l]
        out['Close'] = close
        out['Volume'] = df[v] if v else 0
        return out.dropna()
    else:
        print('WARN: OHLC non trovati, uso sintetici')
        out = pd.DataFrame(index=df.index)
        out['Close'] = close
        out['Open'] = close.shift(1)
        out['High'] = pd.concat([out['Open'], close], axis=1).max(axis=1)
        out['Low'] = pd.concat([out['Open'], close], axis=1).min(axis=1)
        out['Volume'] = 0
        return out.dropna()

def load_aux_symbol(symbol):
    df = yf.download(symbol, start=START_DATE, interval='1d',
                     auto_adjust=False, progress=False)
    if df is None or df.empty:
        return None
    df = fix_yahoo_df(df)
    df = df.sort_index()
    c = extract_single_close(df)
    return pd.DataFrame({'Close': c})

def build_dataset():
    ftse = load_ftsemib()
    df = ftse.copy()
    
    spy = load_aux_symbol('SPY')
    vix = load_aux_symbol('^VIX')
    
    if spy is not None:
        df = df.join(spy.rename(columns={'Close': 'SPY_Close'}))
        df['spy_ret'] = df['SPY_Close'].pct_change()
    
    if vix is not None:
        df = df.join(vix.rename(columns={'Close': 'VIX_Close'}))
        df['vix_ret'] = df['VIX_Close'].pct_change()
    
    df['Close_prev'] = df['Close'].shift(1)
    df['gap_open'] = df['Open'] / df['Close_prev'] - 1
    df['vol_ma'] = df['Volume'].rolling(20).mean()
    df['vol_std'] = df['Volume'].rolling(20).std()
    df['vol_z'] = (df['Volume'] - df['vol_ma']) / df['vol_std']
    df['Open_next'] = df['Open'].shift(-1)
    df['overnight_ret'] = df['Open_next'] / df['Close'] - 1
    df['dow'] = df.index.dayofweek
    
    return df.dropna()

def match_top3(r):
    cond = False
    if not pd.isna(r.get('spy_ret')):
        cond = 0 < r['gap_open'] < 0.01 and 0 < r['spy_ret'] < 0.01
    if not pd.isna(r.get('vix_ret')):
        cond = -0.10 < r['vix_ret'] < -0.05 and cond and -1.5 < r['vol_z'] < -0.5
    return cond

def filter_s(r):
    if not pd.isna(r.get('spy_ret')):
        if r['spy_ret'] < -0.005:
            return False
    if r['dow'] not in ALLOWED_DAYS:
        return False
    return True

def run_backtest(df):
    df['signal'] = df.apply(lambda r: match_top3(r) and filter_s(r), axis=1)
    trades = df[df['signal']].copy()
    
    if trades.empty:
        return trades, pd.Series(dtype=float), 0, 0, 0, 0, 0
    
    trades['pnl'] = trades['overnight_ret']
    trades['pnl_points'] = trades['overnight_ret'] * trades['Close']
    trades['raw_points'] = trades['Open_next'] - trades['Close']
    
    equity = 1 + trades['pnl'].cumprod()
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = equity.iloc[-1] ** (1 / years) - 1 if years > 0 else 0
    avg = trades['pnl'].mean()
    avg_points = trades['pnl_points'].mean()
    win = (trades['pnl'] > 0).mean()
    
    return trades, equity, cagr, avg, win, avg_points, trades['raw_points'].mean()

class System:
    def __init__(self, trades):
        self.initial_capital = 100000
        self.trades = trades.copy()
        self.trades_pnl = self.trades['pnl'] * self.initial_capital
        self.trades_cumpnl = self.trades_pnl.cumsum()
        self.equity_curve = [self.initial_capital] + list(self.initial_capital + self.trades_cumpnl)
        
        peaks = np.maximum.accumulate(self.equity_curve)
        self.drawdown = (peaks - np.array(self.equity_curve)) / peaks * 100
        
        self.trades['result'] = ['WIN' if x > 0 else 'LOSS' for x in self.trades_pnl]
        self.trades['trade'] = list(range(len(self.trades)))
        self.trades['position_pct'] = 100

def export_metrics(df, system, trades, equity, cagr, avg, winrate, avg_points):
    """Esporta metriche in JSON per web dashboard"""
    
    metrics = {
        'last_update': datetime.now().isoformat(),
        'system_info': {
            'name': 'QUANT SUPERIOR',
            'description': 'FTSEMIB Overnight Top3 Pattern Strategy',
            'status': 'LIVE'
        },
        'performance': {
            'total_trades': len(trades),
            'winning_trades': (trades['pnl'] > 0).sum() if not trades.empty else 0,
            'losing_trades': (trades['pnl'] < 0).sum() if not trades.empty else 0,
            'win_rate': float(winrate * 100) if not pd.isna(winrate) else 0,
            'avg_trade': float(avg * 100) if not pd.isna(avg) else 0,
            'avg_points': float(avg_points) if not pd.isna(avg_points) else 0,
            'cagr': float(cagr * 100) if not pd.isna(cagr) else 0,
            'total_return': float((system.equity_curve[-1] / system.initial_capital - 1) * 100) if system.equity_curve else 0,
            'max_drawdown': float(np.max(system.drawdown)) if len(system.drawdown) > 0 else 0
        },
        'equity_curve': [float(x) for x in system.equity_curve[-252:]],  # Ultimi 252 giorni
        'drawdown_curve': [float(x) for x in system.drawdown[-252:]],
        'last_signal': 'FLAT',
        'trades_history': []
    }
    
    # Ultime 10 trades
    if not trades.empty:
        last_trades = trades.tail(10)
        for idx, (_, trade) in enumerate(last_trades.iterrows()):
            metrics['trades_history'].append({
                'date': str(idx.date()),
                'entry': float(trade['Close']),
                'exit': float(trade['Open_next']),
                'pnl_pct': float(trade['pnl'] * 100),
                'result': trade['result']
            })
    
    # Segnale per oggi
    if len(df) > 0:
        last = df.iloc[-1]
        sig = match_top3(last) and filter_s(last)
        metrics['last_signal'] = 'LONG' if sig else 'FLAT'
    
    return metrics

def main():
    ensure_output_dir()
    print('[INIT] Caricamento dati...')
    df = build_dataset()
    
    print('[BACKTEST] Esecuzione backtest...')
    trades, equity, cagr, avg, winrate, avg_points, avg_raw = run_backtest(df)
    
    print('[SYSTEM] Inizializzazione sistema...')
    system = System(trades)
    
    print('[EXPORT] Creazione metriche...')
    metrics = export_metrics(df, system, trades, equity, cagr, avg, winrate, avg_points)
    
    print('[SAVE] Salvataggio JSON...')
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    
    print(f'\n=== METRICHE SISTEMA ===')
    print(f'Trades: {metrics["performance"]["total_trades"]}')
    print(f'Win rate: {metrics["performance"]["win_rate"]:.2f}%')
    print(f'CAGR: {metrics["performance"]["cagr"]:.2f}%')
    print(f'Max DD: {metrics["performance"]["max_drawdown"]:.2f}%')
    print(f'Ultimo segnale: {metrics["last_signal"]}')
    print(f'Export: {OUTPUT_FILE}')
    print(f'Aggiornamento: {metrics["last_update"]}')

if __name__ == '__main__':
    main()
