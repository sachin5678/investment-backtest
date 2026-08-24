"""Fetches ~5-year annual fundamentals (balance sheet, income statement,
current market cap) for all 500 NIFTY 500 constituents, via yfinance,
threaded for speed. Saves to fundamentals_raw.pkl for the quality-score
computation step (backtest12.py) — kept as a separate cached step since
each of the 500 tickers needs its own yfinance.Ticker() object (fundamentals
aren't batchable the way price history is), and re-fetching is slow.
"""
import pickle
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf
from nifty500_symbols import NIFTY_500_SYMBOLS


def fetch_one(symbol):
    ticker = symbol + ".NS"
    tk = yf.Ticker(ticker)
    try:
        bs = tk.balance_sheet
        fin = tk.financials
        mcap = tk.fast_info.market_cap
        return ticker, {"balance_sheet": bs, "financials": fin, "market_cap": mcap}
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

    with open("fundamentals_raw.pkl", "wb") as f:
        pickle.dump(results, f)

    print(f"\nDone in {time.time()-t0:.0f}s. {len(results)} fetched, {len(errors)} errors.")
    if errors:
        print("Errors:")
        for t, e in errors[:20]:
            print(" ", t, e[:100])


if __name__ == "__main__":
    main()
