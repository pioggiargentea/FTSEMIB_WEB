
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
