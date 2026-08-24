"""Fetches full daily OHLC history for NSE stocks that qualify for the
RSI-70 report's "any NSE stock above Rs 2,000 Cr" universe but aren't
already covered by this project's existing NIFTY 500 price cache
(universe_raw.pkl + quality50_extra_raw.pkl + midcap150_extra_raw.pkl +
smallcap250_extra_raw.pkl). Saved to rsi_universe_extra_raw.pkl.

Deliberately gentle (small batches, real pauses, low concurrency, retries)
— an earlier, faster attempt at fetching just market caps for ~2,300
tickers tripped Yahoo Finance's rate limit badly enough to also block
unrelated single-ticker requests for a while."""
import json
import pickle
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import yfinance as yf

from nifty500_symbols import NIFTY_500_SYMBOLS

MARKETCAP_FILE = "nse_marketcaps_merged.json"
MIN_CAP_CR = 2000.0
OUT_FILE = "rsi_universe_extra_raw.pkl"
BATCH_SIZE = 40
WORKERS = 3
PAUSE_BETWEEN_BATCHES = 20


def already_cached_tickers():
    cached = set()
    for fname in ("universe_raw.pkl", "quality50_extra_raw.pkl", "midcap150_extra_raw.pkl", "smallcap250_extra_raw.pkl"):
        try:
            raw = pd.read_pickle(fname)
            cached |= set(c[0] for c in raw.columns)
        except FileNotFoundError:
            pass
    return cached


def fetch_one(ticker):
    time.sleep(random.uniform(0.3, 0.8))
    try:
        df = yf.download(ticker, period="max", auto_adjust=False, progress=False, threads=False)
        if df.empty:
            return ticker, None
        df.columns = df.columns.droplevel(1) if isinstance(df.columns, pd.MultiIndex) else df.columns
        return ticker, df
    except Exception:
        return ticker, None


def main():
    with open(MARKETCAP_FILE) as f:
        mcaps = json.load(f)

    qualifying = {t for t, v in mcaps.items() if v and v / 1e7 > MIN_CAP_CR}
    already_have = already_cached_tickers()
    nifty500_set = {s + ".NS" for s in NIFTY_500_SYMBOLS}
    to_fetch = sorted(qualifying - already_have - nifty500_set)

    print(f"{len(mcaps)} tickers have a market cap, {len(qualifying)} qualify (> Rs {MIN_CAP_CR:.0f} Cr)")
    print(f"{len(already_have)} already cached from earlier reports, {len(nifty500_set)} in NIFTY 500")
    print(f"{len(to_fetch)} new tickers need fresh price history")

    results = {}
    t0 = time.time()
    for i in range(0, len(to_fetch), BATCH_SIZE):
        batch = to_fetch[i:i + BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(fetch_one, t): t for t in batch}
            for f in as_completed(futs):
                ticker, df = f.result()
                if df is not None:
                    results[ticker] = df
        print(f"  batch {i//BATCH_SIZE + 1}/{(len(to_fetch)-1)//BATCH_SIZE + 1} done "
              f"({time.time()-t0:.0f}s elapsed, {len(results)} succeeded so far)")
        with open(OUT_FILE, "wb") as f:
            combined = pd.concat({t: df for t, df in results.items()}, axis=1)
            pickle.dump(combined, f)
        if i + BATCH_SIZE < len(to_fetch):
            time.sleep(PAUSE_BETWEEN_BATCHES)

    print(f"\nDone. {len(results)} of {len(to_fetch)} fetched successfully.")
    missing = sorted(set(to_fetch) - set(results.keys()))
    if missing:
        print(f"{len(missing)} still missing (kept out of the universe, not silently guessed at):")
        print(missing[:30], "..." if len(missing) > 30 else "")
    with open("rsi_universe_missing.json", "w") as f:
        json.dump(missing, f)


if __name__ == "__main__":
    main()
