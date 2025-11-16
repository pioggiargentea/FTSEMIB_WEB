
# FTSEMIB_WEB

Dashboard automatica del sistema "Nearer My God to Thee 2":
- Modello FTSEMIB NEXT-DAY OPEN basato su volumi paniere + filtro SPX_ret >= 0.0%
- Equity curve normalizzata (base = 1), scala logaritmica
- Segnale overnight aggiornato automaticamente

## Come usare

1. Crea un nuovo repository GitHub chiamato `FTSEMIB_WEB`.
2. Carica tutti i file di questa cartella nel repository (mantieni le cartelle).
3. Vai su **Settings → Pages** e imposta:
   - Source: `Deploy from branch`
   - Branch: `main` (o `master`), cartella `/ (root)`

4. GitHub Pages pubblicherà il sito a un URL tipo:
   `https://<tuonome>.github.io/FTSEMIB_WEB`

5. Il workflow GitHub Actions (`.github/workflows/update.yml`) eseguirà ogni giorno feriale alle 16:30 UTC (17:30 ora italiana):
   - `update_site.py`
   - Scarica i dati da Yahoo Finance
   - Aggiorna `equity.json` e `signals.json`
   - Esegue commit automatico con `GITHUB_TOKEN`

Non devi fare altro: il sito si aggiornerà da solo.

## Note

- Il modello usa esclusivamente dati daily (FTSEMIB.MI, ^GSPC e titoli del paniere).
- Nessuna garanzia di risultato. Uso solo informativo/didattico.


## 🚀 QUANT SUPERIOR LIVE - Sistema di Trading Online

Nuovo sistema completamente online con dashboard live per monitorare equity curve e metriche in tempo reale!

### 📊 Dashboard Live
- **URL**: `https://<yourname>.github.io/FTSEMIB_WEB/docs/dashboard.html`
- Visualizzazione in tempo reale di:
  - Equity curve
  - Drawdown
  - Metriche di performance (Win rate, CAGR, Max DD)
  - Storico trades
  - Segnali odierni

### 🔧 Componenti del Sistema

**1. Backend (Python):** `quant_superior_live.py`
- Scarica dati FTSEMIB, SPY, VIX
- Esegue backtest completo
- Esporta metriche in JSON
- Output: `docs/data/metrics.json`

**2. Frontend (HTML/CSS/JS):** `docs/dashboard.html`
- Dashboard responsivo e moderno
- Grafici live con Chart.js
- Auto-refresh ogni 30 minuti

**3. Automation (GitHub Actions):** `.github/workflows/update-metrics.yml`
- Aggiorna automaticamente ogni giorno feriale alle 17:30 UTC (18:30 CET)
- Esegue il backtest Python
- Commita i risultati

### 📋 Setup Iniziale

1. **Abilita GitHub Pages:**
   - Vai a Settings → Pages
   - Source: Deploy from branch
   - Branch: `main` / Folder: `docs`

2. **Configura il Workflow (opzionale):**
   - Il workflow è già pronto ma richiede che Python sia installato nell'ambiente GitHub
   - Per prima volta, esegui manualmente da: Actions → Update Metrics → Run workflow

3. **Accedi alla Dashboard:**
   - URL: `https://<username>.github.io/FTSEMIB_WEB/docs/dashboard.html`

### 📦 Files Importanti

```
FTSEMIB_WEB/
├── quant_superior_live.py      # Sistema di backtest con export JSON
├── docs/
│   ├── dashboard.html          # Dashboard live
│   └── data/
│       └── metrics.json        # Dati metriche (aggiornati automaticamente)
├── .github/
│   └── workflows/
│       └── update-metrics.yml  # GitHub Actions workflow
└── README.md
```

### 🔄 Flusso di Aggiornamento

1. GitHub Actions schedula l'esecuzione giornaliera
2. `quant_superior_live.py` viene eseguito
3. Scarica dati storici e genera `metrics.json`
4. Il file viene committato su GitHub
5. GitHub Pages carica il dashboard
6. Dashboard legge `metrics.json` e mostra i dati live

### 🎯 Prossimi Passi

- [ ] Testare manualmente il backtest
- [ ] Attivare GitHub Pages
- [ ] Verificare il workflow GitHub Actions
- [ ] Accedere al dashboard per la prima volta
- [ ] Configurare notifiche per gli aggiornamenti

### 📌 Note Importanti

- Il dashboard si auto-aggiorna ogni 30 minuti
- I dati storici risalgono al 2010
- Nessuna data look-ahead bias
- Sistema robusto per errori di connessione Yahoo
- Metriche complete: CAGR, Win Rate, Max DD, Equity Curve, etc.

---
**Ultima versione:** Nov 16, 2025 - Sistema Live Completo
