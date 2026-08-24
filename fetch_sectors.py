"""Fetches Yahoo Finance's own sector/industry classification for every
NIFTY 500 constituent, via yfinance, threaded for speed. Saves to
sectors_raw.json for the sector-momentum-rotation backtest (backtest19.py).

This is Yahoo's own present-day GICS-like tag (Ticker.info['sector']), not
NSE's official sector taxonomy — used because it's the only sector
classification available in this project's data sources, and because — like
the quality-score fundamentals in fetch_quality_fundamentals.py — no
point-in-time-historical version of it exists, so it's applied retroactively
as a FIXED, present-day label (see backtest19.py's docstring for the full
disclosure on what that assumes)."""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf
from nifty500_symbols import NIFTY_500_SYMBOLS


def fetch_one(symbol):
    ticker = symbol + ".NS"
    tk = yf.Ticker(ticker)
    try:
        info = tk.info
        return ticker, {"sector": info.get("sector"), "industry": info.get("industry")}
    except Exception as e:
        return ticker, {"error": str(e)}


def main():
    t0 = time.time()
    results = {}
    errors = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(fetch_one, s): s for s in NIFTY_500_SYMBOLS}
        done = 0
        for f in as_completed(futs):
            symbol = futs[f]
            try:
                ticker, data = f.result()
                results[ticker] = data
                if "error" in data:
                    errors.append((ticker, data["error"]))
            except Exception as e:
                errors.append((symbol, str(e)))
            done += 1
            if done % 50 == 0:
                print(f"  {done}/{len(NIFTY_500_SYMBOLS)} done, {time.time()-t0:.0f}s elapsed")

    with open("sectors_raw.json", "w") as f:
        json.dump(results, f, indent=1)

    have_sector = sum(1 for v in results.values() if v.get("sector"))
    print(f"\nDone in {time.time()-t0:.0f}s. {len(results)} fetched, {have_sector} with a sector, {len(errors)} errors.")
    if errors:
        print("Errors:")
        for t, e in errors[:20]:
            print(" ", t, e[:100])

    from collections import Counter
    counts = Counter(v["sector"] for v in results.values() if v.get("sector"))
    print("\nSector counts:")
    for sector, n in counts.most_common():
        print(f"  {sector}: {n}")


if __name__ == "__main__":
    main()
