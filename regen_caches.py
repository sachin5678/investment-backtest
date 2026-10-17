"""Regenerates the gitignored raw price caches (universe_raw.pkl,
quality50_extra_raw.pkl, midcap150_extra_raw.pkl, smallcap250_extra_raw.pkl)
that backtest13 and friends expect — backtest15/17 in particular hard-require
smallcap250_extra_raw.pkl, which was missing on this machine and blocked
build_master_comparison.py until it was refetched with this script. Mirrors
the format the original caches used: a single DataFrame from
yf.download(tickers, group_by="ticker"), giving MultiIndex columns
(ticker, OHLCV...).

Run with an optional single-cache argument to refetch just one (e.g.
`py -3 regen_caches.py smallcap250`); with no argument it refetches all four.
"""
import json
import pickle
import sys
import time

import pandas as pd
import yfinance as yf

from nifty200_symbols import NIFTY_200_SYMBOLS
from niftymidcap150_symbols import NIFTY_MIDCAP150_SYMBOLS
from niftysmallcap250_symbols import NIFTY_SMALLCAP250_SYMBOLS

BATCH = 40


def download_all(tickers):
    frames = []
    for i in range(0, len(tickers), BATCH):
        batch = tickers[i:i + BATCH]
        try:
            df = yf.download(batch, period="max", auto_adjust=False, progress=False,
                             group_by="ticker", threads=True)
            frames.append(df)
            print(f"batch {i//BATCH+1}: {len(df.columns.get_level_values(0).unique())} tickers")
        except Exception as e:
            print(f"batch {i//BATCH+1} failed: {e}")
        time.sleep(2)
    return pd.concat(frames, axis=1)


def main(only=None):
    if only in (None, "nifty200"):
        nifty200 = [s + ".NS" for s in NIFTY_200_SYMBOLS]
        raw200 = download_all(nifty200)
        with open("universe_raw.pkl", "wb") as f:
            pickle.dump(raw200, f)
        print("universe_raw.pkl:", raw200.shape)

    if only in (None, "quality"):
        quality = [row["ticker"] for row in json.load(open("quality50_selection.json"))]
        extra_q = download_all(quality)
        with open("quality50_extra_raw.pkl", "wb") as f:
            pickle.dump(extra_q, f)
        print("quality50_extra_raw.pkl:", extra_q.shape)

    if only in (None, "midcap150"):
        midcap150 = [s + ".NS" for s in NIFTY_MIDCAP150_SYMBOLS]
        extra_m = download_all(midcap150)
        with open("midcap150_extra_raw.pkl", "wb") as f:
            pickle.dump(extra_m, f)
        print("midcap150_extra_raw.pkl:", extra_m.shape)

    if only in (None, "smallcap250"):
        smallcap250 = [s + ".NS" for s in NIFTY_SMALLCAP250_SYMBOLS]
        extra_s = download_all(smallcap250)
        with open("smallcap250_extra_raw.pkl", "wb") as f:
            pickle.dump(extra_s, f)
        print("smallcap250_extra_raw.pkl:", extra_s.shape)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
