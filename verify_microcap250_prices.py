"""Rebuilds and verifies microcap250_raw.pkl after fetch_microcap250_prices.py.

The bulk-download pass (yf.download, 3 concurrent workers) came back with
CONTAMINATED column blocks for 113 of 246 tickers: their DataFrames held 2-3
different series under duplicated field labels (e.g. ABFRL carries a foreign
917-row series from 2023-01-30, its real 3268-row series, and a third
327-row series), because yf.download returned multi-ticker column groups and
the fetcher's droplevel(1) destroyed the ticker labels. Some blocks are also
silently truncated (ABFRL's real series is fine in smallcap250_extra, but
came back partial here). Nothing raised, so retries never fired.

Rebuild strategy (regardless of which block in the old cache is real):
  1. re-fetch EVERY ticker sequentially through yf.Ticker(t).history()
     — a single-symbol endpoint, structurally immune to multi-ticker
     column mixing; flat columns, no droplevel needed;
  2. GATE on ground truth: every ticker shared with the trusted earlier
     caches (smallcap250_extra_raw.pkl, universe_raw.pkl,
     quality50_extra_raw.pkl, midcap150_extra_raw.pkl,
     builder_extras_raw.pkl) must match span (±10d start, ±5 rows) and
     Close values on the overlap (<0.5%);
  3. tickers whose history() fails fall back to the old cache's block with
     the MOST non-null Close rows, flagged UNVERIFIED;
  4. write the cleaned (Ticker, Price) frame to microcap250_raw.pkl
     (previous download-pass cache kept as microcap250_raw_dl.bak.pkl).

Run AFTER fetch_microcap250_prices.py. Sequential and gentle on purpose —
the concurrent path is exactly what corrupted the first pass.
"""
import os
import pickle
import random
import time
from collections import Counter

import pandas as pd
import yfinance as yf

from microcap250_symbols import MICROCAP_250_SYMBOLS

CACHE = "microcap250_raw.pkl"
BAK = "microcap250_raw_dl.bak.pkl"
TRUSTED_SOURCES = ("smallcap250_extra_raw.pkl", "universe_raw.pkl",
                   "quality50_extra_raw.pkl", "midcap150_extra_raw.pkl",
                   "builder_extras_raw.pkl")
FIELDS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def fetch_history(ticker):
    time.sleep(random.uniform(0.3, 0.8))
    for attempt in range(3):
        try:
            h = yf.Ticker(ticker).history(period="max", auto_adjust=False)
            if h.empty:
                return None
            if h.index.tz is not None:
                h.index = h.index.tz_localize(None)
            h = h[~h.index.duplicated(keep="first")]
            h.columns = [str(c) for c in h.columns]
            have = [c for c in FIELDS if c in h.columns]
            if len(have) < 6:
                return None
            return h[FIELDS].astype("float64")
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None


def cache_blocks(raw, t):
    """Old cache may hold 1-3 series per field (contaminated). Return the
    block with the most non-null Close rows — for fallback + reporting only."""
    sub = raw[t]
    groups = {}
    for pos, label in enumerate(sub.columns):
        groups.setdefault(label, []).append(sub.iloc[:, pos])
    if "Close" not in groups:
        return None, 0
    best_i = max(range(len(groups["Close"])),
                 key=lambda i: int(groups["Close"][i].notna().sum()))
    block = pd.DataFrame({label: copies[best_i] if best_i < len(copies) else copies[0]
                          for label, copies in groups.items()})
    n_copies = len(groups["Close"])
    return block, n_copies


def load_trusted():
    trusted = {}
    for fname in TRUSTED_SOURCES:
        try:
            raw = pd.read_pickle(fname)
            uc = raw.xs("Close", axis=1, level=1)
        except FileNotFoundError:
            continue
        for t in uc.columns:
            col = uc[t]
            if isinstance(col, pd.DataFrame):
                col = col.iloc[:, 0]
            nn = col.dropna()
            if len(nn) and t not in trusted:
                trusted[t] = (int(len(nn)), nn.index[0], fname, nn)
    return trusted


def main():
    raw = pd.read_pickle(CACHE)
    old_tickers = sorted(set(c[0] for c in raw.columns))
    print(f"old cache: {raw.shape}, {len(old_tickers)} tickers")

    trusted = load_trusted()
    print(f"ground truth: {len(trusted)} trusted ticker series from {len(TRUSTED_SOURCES)} caches")

    blocks, unverified, empty = {}, [], []
    disagree = []
    for i, t in enumerate(old_tickers, 1):
        h = fetch_history(t)
        old_block, n_copies = cache_blocks(raw, t)
        if h is not None:
            blocks[t] = h
            # contamination report: does the old cache's best block agree?
            if old_block is not None and "Close" in old_block and n_copies >= 1:
                a = old_block["Close"].dropna()
                b = h["Close"].dropna()
                both = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
                if len(both) >= 30:
                    rel = float(((both["a"] - both["b"]).abs() / both["b"].abs()).max())
                    if rel > 0.005:
                        disagree.append((t, round(rel * 100, 1), n_copies,
                                         int(a.notna().sum()), int(b.notna().sum())))
        elif old_block is not None:
            blocks[t] = old_block
            unverified.append(t)
        else:
            empty.append(t)
        if i % 40 == 0:
            print(f"  {i}/{len(old_tickers)} fetched (unverified so far: {len(unverified)})",
                  flush=True)

    print(f"\nhistory() ok: {len(blocks) - len(unverified)}   "
          f"cache-fallback (UNVERIFIED): {len(unverified)}   no data at all: {len(empty)}")
    if unverified:
        print("  fallback tickers:", unverified)
    if disagree:
        print(f"\nold cache DISAGREES with history() on {len(disagree)} tickers "
              f"(contamination/truncation evidence):")
        for t, pct, nc, nrows_old, nrows_new in disagree[:20]:
            print(f"   {t:20s} diff {pct:>7}%  old {nc}x block {nrows_old} rows -> "
                  f"history {nrows_new} rows")

    # ---- ground-truth gate: compare final content vs trusted caches ----
    gate_fail, gate_n = [], 0
    for t, (want_rows, want_start, src, want_series) in trusted.items():
        if t not in blocks:
            continue
        gate_n += 1
        got = blocks[t]["Close"].dropna()
        ok_rows = abs(len(got) - want_rows) <= 5
        ok_start = abs((got.index[0] - want_start).days) <= 10
        both = pd.concat([got.rename("g"), want_series.rename("w")], axis=1).dropna()
        ok_val = True
        if len(both) >= 30:
            rel = float(((both["g"] - both["w"]).abs() / both["w"].abs()).max())
            ok_val = rel < 0.005
        if not (ok_rows and ok_start and ok_val):
            gate_fail.append((t, f"want {want_rows} rows from {want_start.date()} ({src}), "
                                 f"got {len(got)} rows from {got.index[0].date()}, "
                                 f"maxdiff {'' if len(both) < 30 else format(rel*100, '.2f')+'%'}"))
    if gate_fail:
        for t, why in gate_fail:
            print(f"GATE FAIL {t}: {why}")
        raise SystemExit(f"ground-truth gate FAILED on {len(gate_fail)}/{gate_n} trusted "
                         f"tickers — cache NOT overwritten")
    print(f"ground-truth gate passed on all {gate_n} trusted tickers")

    # ---- write clean frame ----
    for t in blocks:
        blocks[t] = blocks[t][[c for c in FIELDS if c in blocks[t].columns]]
        if len(blocks[t].columns) < 6:
            raise SystemExit(f"{t}: missing fields {[f for f in FIELDS if f not in blocks[t].columns]}")
    final = pd.concat(blocks, axis=1).sort_index()
    final.columns.names = ["Ticker", "Price"]

    os.replace(CACHE, BAK)
    with open(CACHE, "wb") as f:
        pickle.dump(final, f)
    print(f"\nwrote {CACHE}: {final.shape}  span {final.index[0].date()} -> {final.index[-1].date()}")

    # ---- self-checks ----
    l0 = final.columns.get_level_values(0)
    dist = dict(Counter(Counter(l0).values()))
    print("cols-per-ticker distribution:", dist, "(must be {6: N})")
    if set(dist) != {6}:
        raise SystemExit("NOT all tickers have exactly 6 fields!")
    present = set(l0)
    print(f"tickers present: {len(present)} of {len(MICROCAP_250_SYMBOLS)}")
    print("missing:", sorted(set(s + ".NS" for s in MICROCAP_250_SYMBOLS) - present))
    cl = final.xs("Close", axis=1, level=1)
    print("history-depth after repair:")
    depth = cl.notna().sum()
    for n, lab in ((252, "1y"), (504, "2y"), (1260, "5y"), (2520, "10y")):
        print(f"  >= {lab:3s}: {int((depth >= n).sum())}")
    last = cl.index[-1]
    not_current = int((cl.loc[last].isna()).sum())
    print(f"tickers missing data on last day {last.date()}: {not_current}")
    print("UNVERIFIED (kept from old cache):", unverified if unverified else "none")


if __name__ == "__main__":
    main()
