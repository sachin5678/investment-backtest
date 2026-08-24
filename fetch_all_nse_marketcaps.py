"""Fetches today's market cap for every NSE main-board EQ-series equity
(2,296 tickers, from EQUITY_L.csv — NSE's own official listed-securities
CSV, archives.nseindia.com/content/equities/EQUITY_L.csv, fetched
2026-08-24). Restricted to SERIES == "EQ" (normal equity settlement) —
BE/BZ (trade-to-trade surveillance segment, 234+38 tickers) are excluded,
since those have different settlement mechanics this project doesn't
model. Saves to nse_marketcaps.json for backtest22.py's "any NSE stock
above Rs 2,000 Cr" universe filter.

Gentler than the usual fetch_*.py pattern in this project on purpose: a
first pass at 24 threads across all 2,296 tickers hit Yahoo Finance's rate
limit hard (73% failed, including obviously-fetchable names like RELIANCE
and TCS) — this version uses fewer workers, small per-request jitter, and
retries failures in shrinking batches with pauses in between."""
import csv
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf

OUT_FILE = "nse_marketcaps.json"


def load_eq_symbols():
    with open("EQUITY_L.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return [r["SYMBOL"].strip() for r in rows if r[" SERIES"].strip() == "EQ"]


def fetch_one(symbol):
    ticker = symbol + ".NS"
    time.sleep(random.uniform(0, 0.15))
    try:
        mcap = yf.Ticker(ticker).fast_info.market_cap
        return ticker, mcap
    except Exception:
        return ticker, None


def fetch_batch(tickers_no_suffix, workers, label):
    print(f"{label}: fetching {len(tickers_no_suffix)} tickers with {workers} workers...")
    t0 = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch_one, s): s for s in tickers_no_suffix}
        done = 0
        for f in as_completed(futs):
            ticker, mcap = f.result()
            results[ticker] = mcap
            done += 1
            if done % 200 == 0:
                print(f"  {done}/{len(tickers_no_suffix)} done, {time.time()-t0:.0f}s elapsed")
    ok = sum(1 for v in results.values() if v)
    print(f"{label}: {ok}/{len(tickers_no_suffix)} succeeded in {time.time()-t0:.0f}s")
    return results


def main():
    symbols = load_eq_symbols()
    all_results = fetch_batch(symbols, workers=8, label="Pass 1")

    for attempt in (2, 3, 4):
        failed = [t.replace(".NS", "") for t, v in all_results.items() if not v]
        if not failed:
            break
        print(f"\n{len(failed)} still missing, waiting before retry pass {attempt}...")
        time.sleep(8)
        retry_results = fetch_batch(failed, workers=max(2, 8 - attempt), label=f"Pass {attempt}")
        all_results.update(retry_results)

    with open(OUT_FILE, "w") as f:
        json.dump(all_results, f)

    have_mcap = sum(1 for v in all_results.values() if v)
    above_2000cr = sum(1 for v in all_results.values() if v and v / 1e7 > 2000)
    still_missing = len(all_results) - have_mcap
    print(f"\nFINAL: {have_mcap} of {len(all_results)} have a market cap ({still_missing} still missing after retries).")
    print(f"{above_2000cr} of {have_mcap} are above Rs 2,000 Cr.")


if __name__ == "__main__":
    main()
