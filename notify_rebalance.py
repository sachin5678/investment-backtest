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

The momentum/regime math itself lives in rebalance_signal.py, shared
with notify_email.py, so both channels can never drift apart.
"""
import calendar
import os
import sys

import pandas as pd
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from backtest42 import EMA_SPAN
from rebalance_signal import compute_current_picks, build_csv, REBALANCE_MONTHS, TOP_N, GOLD_TICKER

ALERT_WINDOW_DAYS = 3

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def in_alert_window(today: pd.Timestamp) -> bool:
    if today.month not in REBALANCE_MONTHS:
        return False
    last_day = calendar.monthrange(today.year, today.month)[1]
    return today.day > last_day - ALERT_WINDOW_DAYS


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
