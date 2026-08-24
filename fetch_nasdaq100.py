"""Fetches full daily OHLC history for all 102 Nasdaq-100 constituents via a
single batched yfinance call (US tickers don't need the per-ticker threaded
approach used for the ~500-name NSE universe — yfinance's multi-ticker
download handles this fine in one request). Saves to nasdaq100_raw.pkl for
backtest20.py. auto_adjust=False, same convention as fetch() in backtest4.py
used throughout this project (raw Close, no dividend adjustment)."""
import pickle
import yfinance as yf
from nasdaq100_symbols import NASDAQ_100_SYMBOLS


def main():
    print(f"Downloading {len(NASDAQ_100_SYMBOLS)} tickers...")
    raw = yf.download(NASDAQ_100_SYMBOLS, period="max", auto_adjust=False, progress=False, group_by="ticker")
    with open("nasdaq100_raw.pkl", "wb") as f:
        pickle.dump(raw, f)

    tickers_present = sorted(set(c[0] for c in raw.columns))
    missing = sorted(set(NASDAQ_100_SYMBOLS) - set(tickers_present))
    print(f"Got data for {len(tickers_present)} of {len(NASDAQ_100_SYMBOLS)} tickers.")
    if missing:
        print("Missing entirely:", missing)

    usable = 0
    for t in tickers_present:
        s = raw[(t, "Close")].dropna()
        if len(s) > 252:
            usable += 1
    print(f"{usable} tickers have >1 year of price history.")


if __name__ == "__main__":
    main()
