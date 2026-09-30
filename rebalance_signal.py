"""
Shared logic for report 48's live rebalance signal — used by BOTH
notify_rebalance.py (Telegram) and notify_email.py (email), so the
momentum/regime math lives in exactly one place rather than being copied
into each notification channel's script.

DATA FRESHNESS: fetches ALL prices LIVE via yfinance on every call — not
the locally cached Midcap150 price history report 48 itself uses for
reproducibility (checked directly: that cache is over a month stale as
of this writing). A same-day alert needs today's actual close.

Reuses this project's own already-tested formula (select_top_original,
the EMA_SPAN convention) rather than re-deriving the momentum math — see
backtest33.py / backtest42.py for the canonical versions this mirrors.

CALENDARS: report 85 tested all six semi-annual rebalance-month offsets
(Jan/Jul through Jun/Dec) and report 87 found that BLENDING all six as
equal sleeves beats picking just one calendar — so both notification
channels now track all six, not only Jun/Dec. Because the six pairs
between them cover every calendar month exactly once, this is equivalent
to "remind me at every month-end," each one tagged with which of the six
sleeves it belongs to.
"""
import io
import sys

import pandas as pd

from backtest10 import fetch
from backtest33 import select_top_original, MIN_ELIGIBLE, LOOKBACK_12M
from backtest42 import EMA_SPAN
from niftymidcap150_symbols import NIFTY_MIDCAP150_SYMBOLS

TOP_N = 10
GOLD_TICKER = "GOLDBEES.NS"

CALENDAR_PAIRS = [(1, 7), (2, 8), (3, 9), (4, 10), (5, 11), (6, 12)]
CALENDAR_LABELS = {pair: f"{pd.Timestamp(2000, pair[0], 1).strftime('%b')}/{pd.Timestamp(2000, pair[1], 1).strftime('%b')}"
                    for pair in CALENDAR_PAIRS}
MONTH_TO_CALENDAR = {m: pair for pair in CALENDAR_PAIRS for m in pair}
REBALANCE_MONTHS = tuple(range(1, 13))


def fetch_midcap150_closes_live():
    tickers = [s + ".NS" for s in NIFTY_MIDCAP150_SYMBOLS]
    cols = {}
    failed = []
    for t in tickers:
        try:
            df = fetch(t)
        except Exception:
            failed.append(t)
            continue
        if df is not None and not df.empty:
            cols[t] = df["Close"]
        else:
            failed.append(t)
    if failed:
        print(f"WARNING: {len(failed)} of {len(tickers)} Midcap150 tickers failed to fetch live: {failed[:10]}"
              f"{'...' if len(failed) > 10 else ''}", file=sys.stderr)
    return pd.DataFrame(cols).sort_index().ffill()


def compute_current_picks():
    closes = fetch_midcap150_closes_live()
    nifty = fetch("^NSEI")
    gold = fetch(GOLD_TICKER)

    common = closes.index.intersection(nifty.index)
    closes = closes.loc[common]
    nifty_close = nifty.loc[common, "Close"]

    if len(common) < LOOKBACK_12M + 1:
        raise RuntimeError(f"Not enough live history yet ({len(common)} days) to compute momentum — need {LOOKBACK_12M}+.")

    ema = nifty_close.ewm(span=EMA_SPAN, adjust=False).mean()
    t_idx = len(common) - 1
    as_of = common[-1]

    regime_on = bool(nifty_close.iloc[-1] > ema.iloc[-1])
    picks = select_top_original(closes, t_idx, top_n=TOP_N, min_eligible=MIN_ELIGIBLE) if regime_on else None

    return {
        "as_of": as_of, "regime_on": regime_on,
        "nifty_close": float(nifty_close.iloc[-1]), "nifty_ema": float(ema.iloc[-1]),
        "picks": [p.replace(".NS", "") for p in picks] if picks else None,
        "gold_price": float(gold["Close"].iloc[-1]) if not gold.empty else None,
    }


def build_csv(result):
    buf = io.StringIO()
    if result["regime_on"]:
        pd.DataFrame({"ticker": result["picks"], "weight_pct": [100 / TOP_N] * len(result["picks"])}).to_csv(buf, index=False)
    else:
        pd.DataFrame({"ticker": [GOLD_TICKER.replace(".NS", "")], "weight_pct": [100.0]}).to_csv(buf, index=False)
    buf.seek(0)
    return buf.getvalue()
