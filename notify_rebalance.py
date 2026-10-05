"""
Proof-of-concept rebalance notifier for report 48 (Midcap150 Momentum 10,
200-day EMA regime filter, gold instead of cash) — sends a Telegram
message + a CSV of the current picks whenever today falls inside a small
"rebalance is imminent" window for ANY of the six semi-annual calendars
report 85/87 tested (Jan/Jul, Feb/Aug, Mar/Sep, Apr/Oct, May/Nov,
Jun/Dec). Since those six pairs between them cover every calendar month
exactly once, this now fires once per month, each time tagged with which
calendar's rebalance it is.

WHY A WINDOW, NOT ONE EXACT DAY: each calendar's rebalance date is
defined as "the LAST TRADING DAY of its two months" (rebalance_dates()
in backtest10.py) — which trading day that turns out to be depends on
NSE's own holiday calendar, and this project has no forward-looking
holiday calendar to know that in advance. Rather than guess wrong and
miss the real day, this alerts every day during the last
ALERT_WINDOW_DAYS calendar days of a rebalance month (which already
includes the estimated rebalance day itself) — a few extra reminders is
a much safer failure mode than a missed one.

THREE DIFFERENT ALERTS AROUND THE REBALANCE DAY ITSELF:
  - `--pre-close` (meant to run ~3 PM IST, before the 3:30 PM close) only
    fires on the exact estimated rebalance day, using yfinance's current
    (delayed ~15 min) snapshot as a provisional "final call" — the only
    way to get a same-day heads-up while there's still time to trade.
  - The normal window alert still fires that same day too, scheduled
    after the 15:30 IST close, reporting the CONFIRMED close-based picks
    (the authoritative version, per report 48's own methodology).
  - `--morning-after` (meant to run ~9 AM IST the CALENDAR day right
    after the rebalance day, not necessarily the next weekday) is a
    safety net in case BOTH alerts above were missed — e.g. GitHub's own
    scheduled-workflow queue has been observed delaying a run past
    midnight IST on this repo, which the retry windows in the workflow
    YAML can't recover from (see rebalance_notify.yml). Run before NSE's
    9:15 AM open, yfinance's "latest" daily bar is still YESTERDAY's
    confirmed close, so this needs no separate fetch logic.

The momentum/regime math itself lives in rebalance_signal.py, shared
with notify_email.py, so both channels can never drift apart.
"""
import os
import sys

import pandas as pd
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from backtest42 import EMA_SPAN
from rebalance_signal import compute_current_picks, build_csv, TOP_N, GOLD_TICKER, \
    MONTH_TO_CALENDAR, CALENDAR_LABELS, days_until_next_rebalance, days_since_last_rebalance

ALERT_WINDOW_DAYS = 3

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def in_alert_window(days_until: int) -> bool:
    return 0 <= days_until < ALERT_WINDOW_DAYS


def build_message(result, today, target_date, days_until, mode):
    calendar_label = CALENDAR_LABELS[MONTH_TO_CALENDAR[target_date.month]]
    if mode == "pre_close":
        headline = f"⏰ Report 48 FINAL CALL — {calendar_label} calendar — TODAY is the estimated rebalance day ({today.strftime('%Y-%m-%d')})"
    elif mode == "morning_after":
        headline = f"⏰ Report 48 MORNING-AFTER REMINDER — {calendar_label} calendar — YESTERDAY ({target_date.strftime('%Y-%m-%d')}) was the estimated rebalance day"
    elif days_until == 0:
        headline = f"📅 Report 48 rebalance reminder — {calendar_label} calendar — TODAY is the estimated rebalance day ({today.strftime('%Y-%m-%d')})"
    else:
        headline = f"📅 Report 48 rebalance reminder — {calendar_label} calendar — {today.strftime('%Y-%m-%d')} ({days_until}d until {target_date.strftime('%Y-%m-%d')})"

    lines = [headline, f"(prices as of {result['as_of'].strftime('%Y-%m-%d')} close)", ""]
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
    lines.append("🛡️ Report 91 (gold-strength guard on the same regime filter):")
    if result["regime_on"]:
        lines.append("  Regime is ON, so report 91 holds the exact same top-10 picks as report 48 above.")
    elif result["guard_passes"] is None:
        lines.append("  Not enough live history yet to compute the 6-month gold/NIFTY guard check.")
    elif result["guard_passes"]:
        lines.append(f"  PASSES — gold's 6m return ({result['guard_gold_6m_pct']:+.1f}%) beats NIFTY's "
                      f"({result['guard_nifty_6m_pct']:+.1f}%) and is positive, so report 91 ALSO holds "
                      f"100% {GOLD_TICKER} right now — same as report 48.")
    else:
        lines.append(f"  FAILS — gold's 6m return ({result['guard_gold_6m_pct']:+.1f}%) vs. NIFTY's "
                      f"({result['guard_nifty_6m_pct']:+.1f}%): report 91 says hold 100% FLAT CASH instead of gold.")
    lines.append("")
    if mode == "pre_close":
        lines.append("⚠️ This is a ~3 PM PROVISIONAL list (yfinance's current, delayed ~15 min snapshot), NOT the")
        lines.append("confirmed 3:30 PM close — meant to give you time to trade before the market shuts. A borderline")
        lines.append("stock's rank could still change in the last ~30 minutes. The confirmed after-close version of")
        lines.append("this same list arrives in a separate message once the market closes.")
    elif mode == "morning_after":
        lines.append("⚠️ SAFETY-NET reminder sent before today's 9:15 AM open, in case you missed both yesterday's")
        lines.append("~3 PM final call and the after-close confirmed message. The market hasn't opened yet today, so")
        lines.append("this is still yesterday's own confirmed close — acting on it only now means starting a day late.")
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
    days_until, target_date = days_until_next_rebalance(today)

    force = "--force" in sys.argv
    pre_close = "--pre-close" in sys.argv
    morning_after = "--morning-after" in sys.argv

    if morning_after:
        days_since, last_target = days_since_last_rebalance(today)
        if not force and days_since != 1:
            print(f"{today.date()}: {days_since} days since the last estimated rebalance ({last_target.date()}) — "
                  f"--morning-after only fires the day after, nothing to do.")
            return
        target_date = last_target
        mode = "morning_after"
    elif pre_close:
        if not force and days_until != 0:
            print(f"{today.date()}: {days_until} days until estimated rebalance ({target_date.date()}) — "
                  f"--pre-close only fires on the rebalance day itself, nothing to do.")
            return
        mode = "pre_close"
    else:
        if not force and not in_alert_window(days_until):
            print(f"{today.date()}: {days_until} days until estimated rebalance ({target_date.date()}) — "
                  f"not in the alert window (last {ALERT_WINDOW_DAYS} days), nothing to do.")
            return
        mode = "normal"

    result = compute_current_picks()
    message = build_message(result, today, target_date, days_until, mode)
    print(message)

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\nTELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — printed only, nothing sent.", file=sys.stderr)
        return

    send_telegram_message(message)
    send_telegram_document(build_csv(result), f"report48_picks_{today.date()}.csv")
    print("Sent to Telegram.")


if __name__ == "__main__":
    main()
