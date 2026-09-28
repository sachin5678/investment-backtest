"""
Proof-of-concept rebalance notifier for report 48 (Midcap150 Momentum 10,
200-day EMA regime filter, gold instead of cash, semi-annual June/
December rebalance) — sends a Telegram message + a CSV of the current
picks whenever today falls inside a small "rebalance is imminent" window.

WHY A WINDOW, NOT ONE EXACT DAY: report 48's rebalance date is defined as
"the LAST TRADING DAY of June/December" (rebalance_dates() in
backtest10.py) — which trading day that turns out to be depends on NSE's
own holiday calendar, and this project has no forward-looking holiday
calendar to know that in advance. Rather than guess wrong and miss the
real day, this alerts every day during the last ALERT_WINDOW_DAYS
calendar days of a rebalance month — a few extra reminders is a much
safer failure mode than a missed one.

DATA FRESHNESS: unlike report 48 itself (which uses a locally cached
Midcap150 price history for reproducibility), this script fetches ALL
prices LIVE via yfinance on every run — the whole point of a same-day
alert is that it reflects today's actual close, not a stale cache. This
is slower (~150 individual ticker fetches) but correctness matters more
than speed for something that runs once a day, unattended.

Reuses this project's own already-tested formula (select_top_original,
build_index's EMA_SPAN convention) rather than re-deriving the momentum
math — see backtest33.py / backtest42.py for the canonical versions this
mirrors.
"""
import calendar
import io
import os
import sys

import numpy as np
import pandas as pd
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from backtest10 import fetch, CURRENCY_SYMBOL
from backtest33 import select_top_original, MIN_ELIGIBLE, LOOKBACK_12M
from backtest42 import EMA_SPAN
from niftymidcap150_symbols import NIFTY_MIDCAP150_SYMBOLS

REBALANCE_MONTHS = (6, 12)
ALERT_WINDOW_DAYS = 3
TOP_N = 10
GOLD_TICKER = "GOLDBEES.NS"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def in_alert_window(today: pd.Timestamp) -> bool:
    if today.month not in REBALANCE_MONTHS:
        return False
    last_day = calendar.monthrange(today.year, today.month)[1]
    return today.day > last_day - ALERT_WINDOW_DAYS


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


def build_message(result, today):
    as_of = result["as_of"].strftime("%Y-%m-%d")
    lines = [
        f"📅 Report 48 rebalance reminder — {today.strftime('%Y-%m-%d')}",
        f"(prices as of {as_of} close)",
        "",
    ]
    if result["regime_on"]:
        lines.append(f"Regime: ON — NIFTY 50 ({result['nifty_close']:.0f}) is above its {EMA_SPAN}-day EMA ({result['nifty_ema']:.0f})")
        lines.append(f"Action: hold top-{TOP_N} Midcap150 momentum picks, equal-weighted")
        lines.append("")
        for i, t in enumerate(result["picks"], 1):
            lines.append(f"  {i}. {t} — {100/TOP_N:.1f}%")
    else:
        lines.append(f"Regime: OFF — NIFTY 50 ({result['nifty_close']:.0f}) is below its {EMA_SPAN}-day EMA ({result['nifty_ema']:.0f})")
        lines.append(f"Action: 100% {GOLD_TICKER} (₹{result['gold_price']:.2f})")
    lines.append("")
    lines.append("⚠️ Proof-of-concept alert — verify independently before acting. Not investment advice.")
    return "\n".join(lines)


def build_csv(result):
    buf = io.StringIO()
    if result["regime_on"]:
        pd.DataFrame({"ticker": result["picks"], "weight_pct": [100 / TOP_N] * len(result["picks"])}).to_csv(buf, index=False)
    else:
        pd.DataFrame({"ticker": [GOLD_TICKER.replace(".NS", "")], "weight_pct": [100.0]}).to_csv(buf, index=False)
    buf.seek(0)
    return buf.getvalue()


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=30)
    r.raise_for_status()


def send_telegram_document(csv_text, filename):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    files = {"document": (filename, csv_text.encode("utf-8"), "text/csv")}
    r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID}, files=files, timeout=30)
    r.raise_for_status()


def main():
    today = pd.Timestamp.now(tz="Asia/Kolkata").normalize().tz_localize(None)

    force = "--force" in sys.argv
    if not force and not in_alert_window(today):
        print(f"{today.date()} is not in the rebalance alert window ({REBALANCE_MONTHS}, last {ALERT_WINDOW_DAYS} days) — nothing to do.")
        return

    result = compute_current_picks()
    message = build_message(result, today)
    print(message)

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\nTELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — printed only, nothing sent.", file=sys.stderr)
        return

    send_telegram_message(message)
    send_telegram_document(build_csv(result), f"report48_picks_{today.date()}.csv")
    print("Sent to Telegram.")


if __name__ == "__main__":
    main()
