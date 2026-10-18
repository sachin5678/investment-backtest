"""Fetches full daily OHLC history for the NIFTY Microcap 250 constituents
(NSE official list, microcap250_symbols.py, fetched 2026-10-18) into
microcap250_raw.pkl — the new price cache for backtest103.py's study.

SEQUENTIAL single-symbol fetches through yf.Ticker().history():
an earlier version of this script used yf.download() with 3 concurrent
workers (the fetch_extra_nse_prices.py pattern) and came back with
CONTAMINATED column blocks for 113 of 246 tickers — yf.download returned
multi-ticker column groups and the droplevel(1) unwrapping destroyed the
ticker labels, baking foreign series into the cache (ABFRL carried two
foreign series besides its own), plus some silently truncated spans.
Nothing raised, so retries never fired. yf.Ticker(symbol).history() takes
one symbol and returns flat columns — structurally immune to that mix-up.

Deliberately gentle (single-symbol, real pauses, retries): an earlier fast
attempt elsewhere in this project tripped Yahoo's rate limit badly enough to
also block unrelated single-ticker requests for a while.

Run verify_microcap250_prices.py afterwards: it independently re-fetches
through the same endpoint and gates every ticker shared with the project's
earlier trusted caches (span + values) before the cache is accepted.
"""
import pickle
import random
import time
from collections import Counter

import pandas as pd
import yfinance as yf

from microcap250_symbols import MICROCAP_250_SYMBOLS

OUT_FILE = "microcap250_raw.pkl"
FIELDS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
PAUSE = (0.3, 0.8)


def fetch_one(ticker):
    time.sleep(random.uniform(*PAUSE))
    for attempt in range(3):
        try:
            h = yf.Ticker(ticker).history(period="max", auto_adjust=False)
            if h.empty:
                return ticker, None
            if h.index.tz is not None:
                h.index = h.index.tz_localize(None)
            h = h[~h.index.duplicated(keep="first")]
            h.columns = [str(c) for c in h.columns]
            if not all(c in h.columns for c in FIELDS):
                return ticker, None
            return ticker, h[FIELDS].astype("float64")
        except Exception:
            time.sleep(5 * (attempt + 1))
    return ticker, None


def main():
    to_fetch = sorted(s + ".NS" for s in MICROCAP_250_SYMBOLS)
    print(f"{len(to_fetch)} microcap tickers to fetch (sequential, single-symbol)")

    results = {}
    t0 = time.time()
    for i, t in enumerate(to_fetch, 1):
        ticker, h = fetch_one(t)
        if h is not None:
            results[ticker] = h
        if i % 40 == 0:
            print(f"  {i}/{len(to_fetch)} done ({time.time()-t0:.0f}s, "
                  f"{len(results)} ok so far)", flush=True)

    missing = sorted(set(to_fetch) - set(results))
    print(f"\nDone. {len(results)} of {len(to_fetch)} fetched successfully.")
    if missing:
        print(f"{len(missing)} missing (kept out of the universe, not silently guessed at):")
        print(missing)

    final = pd.concat(results, axis=1).sort_index()
    final.columns.names = ["Ticker", "Price"]
    with open(OUT_FILE, "wb") as f:
        pickle.dump(final, f)
    print(f"cache: {final.shape}  span {final.index[0].date()} -> {final.index[-1].date()}")
    dist = dict(Counter(Counter(final.columns.get_level_values(0)).values()))
    print("cols-per-ticker distribution:", dist, "(must be {6: N})")


if __name__ == "__main__":
    main()
