"""
Proof-of-concept rebalance notifier for the four-report alert suite —
reports 91, 92, 71 and 98 — same external scheduling, same six-calendar
windows, same three alerts (pre-close / after-close / morning-after) and
the same once-per-day lock as report 48's own notifier
(notify_rebalance.py), but each report's own live action:

  - report 91 — report 48's picks; during risk-off the hedge leg holds
    gold ONLY while gold passes both of its own 6-month strength checks
    (beats NIFTY AND positive); otherwise flat cash.
  - report 92 — the same guard checked across all six rebalance
    calendars; live action is calendar-independent, identical to 91's.
  - report 71 — always-on 70/30 core-satellite: 70% in the top-10, 30%
    in gold; a regime flip moves the WHOLE book into 100% gold.
  - report 98 — the max stack's fresh-review target: top-10 with
    keep-if 6m > 0 and exit rank 30 at reviews (stack B also requires new
    buys to be rising); regime OFF parks 100% in gold.

The momentum/regime math (and each report's action semantics) lives in
reports_signal.py, shared with notify_reports_email.py, so the two
channels can never drift apart — the same separation rebalance_signal.py
has for reports 48/91.

WHY A WINDOW, NOT ONE EXACT DAY / WHY THREE ALERTS: identical reasoning
to notify_rebalance.py's own docstring — each calendar's real rebalance
date is "the last trading day of its two months", which needs NSE's own
forward holiday calendar this project doesn't have (so this alerts every
day during the last ALERT_WINDOW_DAYS calendar days of a rebalance month,
a few extra reminders being a much safer failure mode than a missed
one); and the pre-close / morning-after pair bracket the confirmed
after-close message for exactly the same reasons. Read that file for the
full version rather than repeating it here.
"""
import os
import sys

import pandas as pd
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from backtest42 import EMA_SPAN
from rebalance_signal import TOP_N, GOLD_TICKER, MONTH_TO_CALENDAR, CALENDAR_LABELS, \
    days_until_next_rebalance, days_since_last_rebalance
from reports_signal import compute_state, build_report_csv

ALERT_WINDOW_DAYS = 3

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def in_alert_window(days_until: int) -> bool:
    return 0 <= days_until < ALERT_WINDOW_DAYS


def _picks_block(lines, picks, pct):
    for i, t in enumerate(picks, 1):
        lines.append(f"  {i}. {t} — {pct:.1f}%")


def build_message(state, today, target_date, days_until, mode):
    report = state["report"]
    name = f"Report {report}"
    calendar_label = CALENDAR_LABELS[MONTH_TO_CALENDAR[target_date.month]]

    if mode == "pre_close":
        headline = (f"⏰ {name} FINAL CALL — {calendar_label} calendar — TODAY is the estimated rebalance day "
                    f"({today.strftime('%Y-%m-%d')})")
    elif mode == "morning_after":
        headline = (f"⏰ {name} MORNING-AFTER REMINDER — {calendar_label} calendar — YESTERDAY "
                    f"({target_date.strftime('%Y-%m-%d')}) was the estimated rebalance day")
    elif days_until == 0:
        headline = (f"📅 {name} rebalance reminder — {calendar_label} calendar — TODAY is the estimated "
                    f"rebalance day ({today.strftime('%Y-%m-%d')})")
    else:
        headline = (f"📅 {name} rebalance reminder — {calendar_label} calendar — {today.strftime('%Y-%m-%d')} "
                    f"({days_until}d until {target_date.strftime('%Y-%m-%d')})")

    lines = [headline, f"(prices as of {state['as_of'].strftime('%Y-%m-%d')} close)", ""]
    regime_on = state["regime_on"]
    n = state["nifty_close"]
    e = state["nifty_ema"]
    if regime_on:
        lines.append(f"Regime: ON — NIFTY 50 ({n:.0f}) is above its {EMA_SPAN}-day EMA ({e:.0f})")
    else:
        lines.append(f"Regime: OFF — NIFTY 50 ({n:.0f}) is below its {EMA_SPAN}-day EMA ({e:.0f})")

    if report in (91, 92):
        if regime_on:
            lines.append(f"Action: hold top-{TOP_N} Midcap150 momentum picks, equal-weighted")
            lines.append("")
            _picks_block(lines, state["picks"], 100 / TOP_N)
        elif state["guard_passes"] is None:
            lines.append(f"Action: 100% {GOLD_TICKER} by default — but not enough live history yet to compute the "
                         f"gold-strength guard check (see report 91).")
        elif state["guard_passes"]:
            lines.append(f"Guard check: PASSES — gold's 6m return ({state['guard_gold_6m_pct']:+.1f}%) beats NIFTY's "
                         f"({state['guard_nifty_6m_pct']:+.1f}%) and is positive.")
            lines.append(f"Action: 100% {GOLD_TICKER} (₹{state['gold_price']:.2f})")
        else:
            lines.append(f"Guard check: FAILS — gold's 6m return ({state['guard_gold_6m_pct']:+.1f}%) vs. NIFTY's "
                         f"({state['guard_nifty_6m_pct']:+.1f}%).")
            lines.append("Action: 100% FLAT CASH — the guard holds gold only while it passes both checks.")
        lines.append("")
        if report == 91:
            lines.append("ℹ️ Report 91's published testing used the Jun/Dec cadence; report 92 covers the other five.")
        else:
            lines.append("ℹ️ Report 92 tested this guard on all six rebalance calendars (edge ≈ +0.2pp CAGR, "
                         "near-uniform, report-99 corrected).")
    elif report == 71:
        if regime_on:
            lines.append(f"Action: 70% into the top-{TOP_N} (7.0% each) + 30% {GOLD_TICKER} "
                         f"(₹{state['gold_price']:.2f}) — always-on 70/30 split")
            lines.append("")
            _picks_block(lines, state["picks"], 7.0)
        else:
            lines.append(f"Action: 100% {GOLD_TICKER} (₹{state['gold_price']:.2f}) — full flight to gold: a regime "
                         f"flip moves the WHOLE book, not just the 30% sleeve.")
        lines.append("")
        lines.append(f"ℹ️ Report 71's published testing used the Jun/Dec cadence; this {calendar_label} window is "
                     "untested for it.")
    elif report == 98:
        if regime_on:
            a, b = state["stack_a"], state["stack_b"]
            lines.append(f"Action: top-{TOP_N} per the max-stack review rules, equal-weighted (10.0% each)")
            lines.append("")
            lines.append("Stack A (keep-if 6m>0 + exit rank 30) — fresh-review target:")
            for i, t in enumerate(a, 1):
                r = state["ret_6m_pct"].get(t)
                lines.append(f"  {i}. {t} — 6m {r:+.1f}%" if r is not None else f"  {i}. {t}")
            lines.append("")
            if b == a:
                lines.append("Stack B (also requires new buys' 6m > 0): identical to stack A right now.")
            else:
                lines.append("Stack B (also requires new buys' 6m > 0):")
                for i, t in enumerate(b, 1):
                    r = state["ret_6m_pct"].get(t)
                    lines.append(f"  {i}. {t} — 6m {r:+.1f}%" if r is not None else f"  {i}. {t}")
            lines.append("")
            lines.append("Review rules: a held name is KEPT while its rank ≤ 30 and its 6m return > 0; a name failing")
            lines.append("either is sold at the review and the slot refilled.")
        else:
            lines.append(f"Action: 100% {GOLD_TICKER} (₹{state['gold_price']:.2f}) — the max stack's protect layer: "
                         "daily 200-EMA on NIFTY 50.")
        lines.append("")
        lines.append("ℹ️ Headline stack is Jun/Dec; both stacks were date-luck-checked on all six calendars.")
    else:
        raise ValueError(f"unknown report {report!r}")

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


def parse_report():
    if "--report" in sys.argv:
        i = sys.argv.index("--report")
        if i + 1 < len(sys.argv):
            try:
                return int(sys.argv[i + 1])
            except ValueError:
                pass
    raise SystemExit("usage: notify_reports.py --report {71|91|92|98} [--pre-close | --morning-after] [--force]")


def main():
    today = pd.Timestamp.now(tz="Asia/Kolkata").normalize().tz_localize(None)
    days_until, target_date = days_until_next_rebalance(today)

    report = parse_report()
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

    state = compute_state(report)
    message = build_message(state, today, target_date, days_until, mode)
    print(message)

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\nTELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — printed only, nothing sent.", file=sys.stderr)
        return

    send_telegram_message(message)
    send_telegram_document(build_report_csv(state), f"report{report}_picks_{today.date()}.csv")
    print("Sent to Telegram.")


if __name__ == "__main__":
    main()
