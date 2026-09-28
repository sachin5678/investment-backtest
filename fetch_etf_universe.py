"""
Fetches a candidate universe of DISTINCT NSE-listed ETFs (broad-index,
sectoral, smart-beta/factor, commodity, international — deliberately
avoiding multiple ETFs tracking the identical index) directly via
yfinance, and caches the result to etf_universe_raw.pkl.

This is exploratory: not every candidate ticker below is guaranteed to
resolve on yfinance (some NSE ETFs are thinly traded or have quirky
tickers) or to have enough history to be useful. Run this file directly
to see exactly which candidates succeeded, their real listing date, and
how many trading days of history each has, BEFORE building any backtest
on top of this cache — same "verify real data before trusting it"
discipline as every other data-fetch step in this project.
"""
import pickle

import pandas as pd
import yfinance as yf

CANDIDATES = {
    # Broad index
    "NIFTYBEES.NS": "Nifty 50",
    "JUNIORBEES.NS": "Nifty Next 50",
    "MIDCAPIETF.NS": "Nifty Midcap 150",
    "HDFCSML250.NS": "Nifty Smallcap 250",
    # Sectoral
    "BANKBEES.NS": "Nifty Bank",
    "ITBEES.NS": "Nifty IT",
    "PHARMABEES.NS": "Nifty Pharma",
    "PSUBNKBEES.NS": "PSU Bank",
    "CONSUMBEES.NS": "Nifty Consumption",
    "AUTOBEES.NS": "Nifty Auto",
    "FMCGIETF.NS": "Nifty FMCG",
    "METALIETF.NS": "Nifty Metal",
    "PVTBANIETF.NS": "Nifty Private Bank",
    "HEALTHIETF.NS": "Nifty Healthcare",
    "REALTYIETF.NS": "Nifty Realty",
    "CPSEETF.NS": "CPSE (PSU basket)",
    # Smart-beta / factor
    "ALPL30IETF.NS": "Nifty Alpha 50",
    "MOM30IETF.NS": "Nifty200 Momentum 30",
    "LOWVOLIETF.NS": "Nifty Low Volatility 50",
    "QUAL30IETF.NS": "Nifty200 Quality 30",
    "VAL30IETF.NS": "Nifty500 Value 50",
    # Commodity
    "GOLDBEES.NS": "Gold",
    "SILVERBEES.NS": "Silver",
    # International
    "MON100.NS": "Nasdaq 100",
    "MAFANG.NS": "FANG+",
    "MASPTOP50.NS": "S&P 500 Top 50",
}


def fetch_one(ticker):
    df = yf.download(ticker, period="max", auto_adjust=False, progress=False)
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    df = df[["Open", "High", "Low", "Close"]].dropna(how="all")
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def main():
    raw = {}
    print(f"Attempting {len(CANDIDATES)} candidate ETF tickers...\n")
    for ticker, label in CANDIDATES.items():
        try:
            df = fetch_one(ticker)
        except Exception as e:
            print(f"  {ticker:<16} [{label}] FAILED — {e}")
            continue
        if df is None or df.empty or len(df) < 60:
            n = 0 if df is None else len(df)
            print(f"  {ticker:<16} [{label}] SKIPPED — only {n} rows of data")
            continue
        raw[ticker] = df
        print(f"  {ticker:<16} [{label:<22}] OK — {df.index[0].date()} to {df.index[-1].date()}, {len(df)} rows")

    with open("etf_universe_raw.pkl", "wb") as f:
        pickle.dump(raw, f)
    print(f"\nCached {len(raw)} of {len(CANDIDATES)} candidates to etf_universe_raw.pkl")


if __name__ == "__main__":
    main()
