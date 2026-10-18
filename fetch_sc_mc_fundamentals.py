"""Fetches annual fundamentals (balance sheet + income statement) for all
NIFTY Smallcap 250 and NIFTY Midcap 150 constituents via yfinance, threaded
gently, saving to fundamentals_sc_mc_raw.pkl.

Purpose: report 101's clean-room ProPicks-India reconstruction needs the VALUE
and GROWTH pillars (P/E, P/B, revenue/EBITDA YoY) alongside momentum. Price
history alone can't supply those.

Why this is a separate cached step: fundamentals aren't batchable the way price
history is — each ticker needs its own yfinance.Ticker() object — and re-
fetching is slow.

CONCURRENCY: deliberately gentle (6 workers, jittered sleep, pause every 60).
Aggressive fetching (20+ workers) gets the whole account blocked such that even
single-ticker requests start failing — see ONBOARDING.md "Known gotchas".
The older fetch_quality_fundamentals.py uses 16 workers against that guidance;
do not copy it.
"""
import pickle
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf

from niftymidcap150_symbols import NIFTY_MIDCAP150_SYMBOLS
from niftysmallcap250_symbols import NIFTY_SMALLCAP250_SYMBOLS

MAX_WORKERS = 6
PAUSE_EVERY = 60


def fetch_one(symbol):
    ticker = symbol + ".NS"
    tk = yf.Ticker(ticker)
    try:
        bs = tk.balance_sheet
        fin = tk.financials
        shares = None
        if bs is not None and not bs.empty and "Ordinary Shares Number" in bs.index:
            shares = bs.loc["Ordinary Shares Number"].dropna()
        return ticker, {
            "balance_sheet": bs,
            "financials": fin,
            "shares": shares,
        }
    except Exception as e:  # noqa: BLE001 - one bad ticker must not kill the batch
        return ticker, {"error": str(e)}


def main():
    t0 = time.time()
    symbols = sorted(set(NIFTY_SMALLCAP250_SYMBOLS) | set(NIFTY_MIDCAP150_SYMBOLS))
    print(f"Fetching fundamentals for {len(symbols)} tickers "
          f"(smallcap250 + midcap150 union)")

    results, errors = {}, []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(fetch_one, s): s for s in symbols}
        done = 0
        for f in as_completed(futs):
            symbol = futs[f]
            try:
                ticker, data = f.result()
                results[ticker] = data
                if "error" in data:
                    errors.append((ticker, data["error"]))
            except Exception as e:  # noqa: BLE001
                errors.append((symbol, str(e)))
            done += 1
            if done % 10 == 0:
                print(f"  {done}/{len(symbols)} done, {time.time()-t0:.0f}s elapsed",
                      flush=True)
            if done % PAUSE_EVERY == 0:
                time.sleep(random.uniform(1.5, 3.5))

    with open("fundamentals_sc_mc_raw.pkl", "wb") as f:
        pickle.dump(results, f)

    print(f"\nDone in {time.time()-t0:.0f}s. {len(results)} fetched, "
          f"{len(errors)} errors.")
    if errors:
        print("Errors (first 20):")
        for t, e in errors[:20]:
            print(" ", t, e[:100])


if __name__ == "__main__":
    main()
