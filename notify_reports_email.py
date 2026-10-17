"""
Email rebalance reminder for the four-report alert suite — reports 91,
92, 71 and 98 — sends at 5, 3, 1 and 0 calendar days before the estimated
rebalance date of ANY of the six semi-annual calendars (same windows
report 48's own email reminder uses), plus the ~3 PM pre-close FINAL CALL
and the morning-after safety net, each with the report's current live
action and a CSV attachment.

The four reports' live actions (also documented in reports_signal.py, the
shared module this file renders):

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

"ESTIMATED" REBALANCE DATE / WHY A SPREAD OF REMINDERS: identical
reasoning to notify_email.py's own docstring (each calendar's real
rebalance date is "the last trading day of its two months", which needs
NSE's forward holiday calendar this project doesn't have — the 5/3/1/0
spread exists so a small estimation error can't turn into a missed
reminder). Read that file for the full version rather than repeating it.
"""
import os
import smtplib
import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from backtest42 import EMA_SPAN
from rebalance_signal import TOP_N, GOLD_TICKER, MONTH_TO_CALENDAR, CALENDAR_LABELS, \
    days_until_next_rebalance, days_since_last_rebalance
from reports_signal import compute_state, build_report_csv

REMINDER_DAYS = (5, 3, 1, 0)


def env_or(name, default=None):
    """os.environ.get(name, default), but also falls back to `default`
    when the variable is PRESENT but empty — which is exactly what a
    GitHub Actions secret becomes when it isn't actually set (the env
    var still gets created, just with an empty string value, so a plain
    os.environ.get(..., default) never falls back)."""
    value = os.environ.get(name)
    return value if value else default


SMTP_HOST = env_or("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(env_or("SMTP_PORT", "587"))
SMTP_USER = env_or("SMTP_USER")
SMTP_PASS = env_or("SMTP_PASS")
EMAIL_FROM = env_or("EMAIL_FROM", SMTP_USER)
EMAIL_TO = env_or("EMAIL_TO")


def build_email_body(state, mode, days_until, target_date, calendar_label):
    report = state["report"]
    name = f"Report {report}"

    if mode == "pre_close":
        headline = (f"{name} FINAL CALL — {calendar_label} calendar — TODAY is the estimated rebalance day "
                    f"({target_date.strftime('%Y-%m-%d')})")
    elif mode == "morning_after":
        headline = (f"{name} MORNING-AFTER REMINDER — {calendar_label} calendar — YESTERDAY "
                    f"({target_date.strftime('%Y-%m-%d')}) was the estimated rebalance day")
    elif days_until == 0:
        headline = (f"{name} rebalance reminder — {calendar_label} calendar — TODAY is the estimated "
                    f"rebalance day ({target_date.strftime('%Y-%m-%d')})")
    else:
        headline = (f"{name} rebalance reminder — {calendar_label} calendar — {days_until} "
                    f"day{'s' if days_until != 1 else ''} until the estimated rebalance date "
                    f"({target_date.strftime('%Y-%m-%d')})")

    lines = [headline, f"(live prices as of {state['as_of'].strftime('%Y-%m-%d')} close)", ""]
    regime_on = state["regime_on"]
    n = state["nifty_close"]
    e = state["nifty_ema"]
    if regime_on:
        lines.append(f"Regime: ON — NIFTY 50 ({n:.0f}) is above its {EMA_SPAN}-day EMA ({e:.0f})")
    else:
        lines.append(f"Regime: OFF — NIFTY 50 ({n:.0f}) is below its {EMA_SPAN}-day EMA ({e:.0f})")

    if report in (91, 92):
        if regime_on:
            lines.append(f"Current top-{TOP_N} Midcap150 momentum picks (equal-weighted {100 / TOP_N:.1f}% each):")
            lines.append("")
            for i, t in enumerate(state["picks"], 1):
                lines.append(f"  {i}. {t}")
        elif state["guard_passes"] is None:
            lines.append(f"Current signal: 100% {GOLD_TICKER} by default — but not enough live history yet to "
                         f"compute the gold-strength guard check (see report 91).")
        elif state["guard_passes"]:
            lines.append(f"Guard check: PASSES — gold's 6m return ({state['guard_gold_6m_pct']:+.1f}%) beats NIFTY's "
                         f"({state['guard_nifty_6m_pct']:+.1f}%) and is positive.")
            lines.append(f"Current signal: 100% {GOLD_TICKER} (₹{state['gold_price']:.2f})")
        else:
            lines.append(f"Guard check: FAILS — gold's 6m return ({state['guard_gold_6m_pct']:+.1f}%) vs. NIFTY's "
                         f"({state['guard_nifty_6m_pct']:+.1f}%).")
            lines.append("Current signal: 100% FLAT CASH — the guard holds gold only while it passes both checks.")
        lines.append("")
        if report == 91:
            lines.append("Note: report 91's published testing used the Jun/Dec cadence; report 92 covers the other five.")
        else:
            lines.append("Note: report 92 tested this guard on all six rebalance calendars (edge ≈ +0.2pp CAGR, "
                         "near-uniform, report-99 corrected).")
    elif report == 71:
        if regime_on:
            lines.append(f"Current split: 70% into the top-{TOP_N} (7.0% each) + 30% {GOLD_TICKER} "
                         f"(₹{state['gold_price']:.2f}) — always-on 70/30 core-satellite:")
            lines.append("")
            for i, t in enumerate(state["picks"], 1):
                lines.append(f"  {i}. {t} — 7.0%")
        else:
            lines.append(f"Current signal: 100% {GOLD_TICKER} (₹{state['gold_price']:.2f}) — full flight to gold: "
                         f"a regime flip moves the WHOLE book, not just the 30% sleeve.")
        lines.append("")
        lines.append(f"Note: report 71's published testing used the Jun/Dec cadence; this {calendar_label} window is "
                     "untested for it.")
    elif report == 98:
        if regime_on:
            a, b = state["stack_a"], state["stack_b"]
            lines.append(f"Current max-stack action: top-{TOP_N} per the review rules, equal-weighted (10.0% each)")
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
            lines.append(f"Current signal: 100% {GOLD_TICKER} (₹{state['gold_price']:.2f}) — the max stack's "
                         f"protect layer: daily 200-EMA on NIFTY 50.")
        lines.append("")
        lines.append("Note: headline stack is Jun/Dec; both stacks were date-luck-checked on all six calendars.")
    else:
        raise ValueError(f"unknown report {report!r}")

    lines.append("")
    if mode == "pre_close":
        lines.append("This is a ~3 PM PROVISIONAL list, built from yfinance's current (delayed ~15 min) snapshot,")
        lines.append("NOT the confirmed 3:30 PM close — meant to give you time to place trades before the market shuts.")
        lines.append("A borderline stock's rank could still change in the last ~30 minutes of trading. The confirmed,")
        lines.append("after-close version of this same list arrives in a separate email once the market closes.")
    elif mode == "morning_after":
        lines.append("This is a SAFETY-NET reminder sent before today's 9:15 AM open, in case you missed both")
        lines.append("yesterday's ~3 PM final call and the after-close confirmed email. Since the market hasn't")
        lines.append("opened yet today, this is still yesterday's own confirmed close — the same list you should")
        lines.append("already have rebalanced into yesterday. Acting on it only now means starting a day late.")
    else:
        lines.append("These are TODAY's picks, recomputed live — they may still change again before the real rebalance date,")
        lines.append("since the estimated date above is an approximation (see this script's own docstring for why).")
    lines.append("")
    lines.append("Proof-of-concept alert — verify independently before acting. Not investment advice.")
    return "\n".join(lines)


def send_email(subject, body, csv_text, csv_filename):
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(csv_text.encode("utf-8"), Name=csv_filename)
    attachment["Content-Disposition"] = f'attachment; filename="{csv_filename}"'
    msg.attach(attachment)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


def parse_report():
    if "--report" in sys.argv:
        i = sys.argv.index("--report")
        if i + 1 < len(sys.argv):
            try:
                return int(sys.argv[i + 1])
            except ValueError:
                pass
    raise SystemExit("usage: notify_reports_email.py --report {71|91|92|98} [--pre-close | --morning-after] [--force]")


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
        if not force and days_until not in REMINDER_DAYS:
            print(f"{today.date()}: {days_until} days until estimated rebalance ({target_date.date()}) — "
                  f"not one of {REMINDER_DAYS}, nothing to do.")
            return
        mode = "normal"

    calendar_label = CALENDAR_LABELS[MONTH_TO_CALENDAR[target_date.month]]
    state = compute_state(report)
    tag = {"pre_close": "FINAL CALL (~3 PM)", "morning_after": "MORNING-AFTER"}.get(
        mode, "TODAY" if days_until == 0 else f"{days_until}d to go")
    subject = f"Report {report} rebalance reminder — {calendar_label} — {tag} ({target_date.strftime('%Y-%m-%d')})"
    body = build_email_body(state, mode, days_until, target_date, calendar_label)
    print(subject)
    print(body)

    if not SMTP_USER or not SMTP_PASS or not EMAIL_TO:
        print("\nSMTP_USER / SMTP_PASS / EMAIL_TO not set — printed only, nothing sent.", file=sys.stderr)
        return

    send_email(subject, body, build_report_csv(state), f"report{report}_picks_{today.date()}.csv")
    print(f"\nSent to {EMAIL_TO}.")


if __name__ == "__main__":
    main()
