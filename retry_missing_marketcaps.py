"""Retries market-cap fetch for just the tickers still missing after the
merge with the trusted NIFTY500 cache — much gentler pacing (small batches,
real pauses between batches, low concurrency) since faster attempts kept
tripping Yahoo Finance's rate limit."""
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf

MISSING_FILE = "nse_marketcaps_missing.json"
MERGED_FILE = "nse_marketcaps_merged.json"
BATCH_SIZE = 100
WORKERS = 3
PAUSE_BETWEEN_BATCHES = 25


def fetch_one(ticker):
    time.sleep(random.uniform(0.2, 0.6))
    try:
        return ticker, yf.Ticker(ticker).fast_info.market_cap
    except Exception:
        return ticker, None


def main():
    with open(MISSING_FILE) as f:
        missing = json.load(f)
    with open(MERGED_FILE) as f:
        merged = json.load(f)

    print(f"Retrying {len(missing)} tickers in batches of {BATCH_SIZE}, {WORKERS} workers, {PAUSE_BETWEEN_BATCHES}s between batches...")
    t0 = time.time()
    for i in range(0, len(missing), BATCH_SIZE):
        batch = missing[i:i + BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(fetch_one, t): t for t in batch}
            for f in as_completed(futs):
                ticker, mcap = f.result()
                if mcap:
                    merged[ticker] = mcap
        ok_so_far = sum(1 for v in merged.values() if v)
        print(f"  batch {i//BATCH_SIZE + 1}/{(len(missing)-1)//BATCH_SIZE + 1} done "
              f"({time.time()-t0:.0f}s elapsed, {ok_so_far} total have a value)")
        with open(MERGED_FILE, "w") as f:
            json.dump(merged, f)
        if i + BATCH_SIZE < len(missing):
            time.sleep(PAUSE_BETWEEN_BATCHES)

    have = sum(1 for v in merged.values() if v)
    above_2000cr = sum(1 for v in merged.values() if v and v / 1e7 > 2000)
    print(f"\nFINAL: {have} of {len(merged)} have a market cap.")
    print(f"{above_2000cr} of {have} are above Rs 2,000 Cr.")


if __name__ == "__main__":
    main()
