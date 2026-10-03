"""Regenerates the gitignored raw price caches (universe_raw.pkl,
quality50_extra_raw.pkl, midcap150_extra_raw.pkl) that backtest13 and
friends expect. Mirrors the format the original caches used: a single
DataFrame from yf.download(tickers, group_by="ticker"), giving
MultiIndex columns (ticker, OHLCV...)."""
import json
import pickle
import time

import pandas as pd
import yfinance as yf

from nifty200_symbols import NIFTY_200_SYMBOLS
from niftymidcap150_symbols import NIFTY_MIDCAP150_SYMBOLS

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


def main():
    nifty200 = [s + ".NS" for s in NIFTY_200_SYMBOLS]
    midcap150 = [s + ".NS" for s in NIFTY_MIDCAP150_SYMBOLS]
    quality = [row["ticker"] for row in json.load(open("quality50_selection.json"))]

    raw200 = download_all(nifty200)
    with open("universe_raw.pkl", "wb") as f:
        pickle.dump(raw200, f)
    print("universe_raw.pkl:", raw200.shape)

    extra_q = download_all(quality)
    with open("quality50_extra_raw.pkl", "wb") as f:
        pickle.dump(extra_q, f)
    print("quality50_extra_raw.pkl:", extra_q.shape)

    extra_m = download_all(midcap150)
    with open("midcap150_extra_raw.pkl", "wb") as f:
        pickle.dump(extra_m, f)
    print("midcap150_extra_raw.pkl:", extra_m.shape)


if __name__ == "__main__":
    main()
