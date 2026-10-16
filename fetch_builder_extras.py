"""One-time fetch of the builder-lab extras (reports 94+): India VIX, the
NIFTY 500 index, the park-basket ETFs, plus cached copies of NIFTY 50 and
GOLDBEES so every lab run is fully offline and reproducible.

-> builder_extras_raw.pkl, same (symbol, field) column layout as
universe_raw.pkl so the loaders stay uniform.

GOLDBEES.NS here is raw Yahoo data; the engines keep using
fetch_gold_cleaned()'s cleaning convention (drop the two 2019-12-19/20
glitch rows) on this same series.
"""
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import yfinance as yf

TICKERS = [
    "^INDIAVIX",      # India VIX — the "volatility filter" signal
    "^CRSLDX",        # NIFTY 500 — the alternate trend index
    "^NSEI",          # NIFTY 50 (cached so runs don't hit Yahoo)
    "GOLDBEES.NS",    # gold park (raw — cleaned by the loader)
    "SILVERBEES.NS",  # silver park (listed Feb 2022)
    "LIQUIDBEES.NS",  # liquid ETF (returns as extra units, price ~1000)
    "NIFTYBEES.NS",   # broad-index park option
]

FIELDS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

frames = {}
for t in TICKERS:
    df = yf.download(t, period="max", auto_adjust=False, progress=False)
    if df.empty:
        print("FAILED:", t)
        continue
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    have = [f for f in FIELDS if f in df.columns]
    df = df[have]
    df.index = pd.to_datetime(df.index)
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)
    df = df.sort_index()
    for c in df.columns:
        frames[(t, c)] = df[c]
    print(f"{t:15s} {len(df):5d} rows  {df.index[0].date()} -> {df.index[-1].date()}")

out = pd.DataFrame(frames).sort_index()
out.to_pickle("builder_extras_raw.pkl")
print("saved builder_extras_raw.pkl", out.shape)
