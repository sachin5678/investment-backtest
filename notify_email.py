"""
Email rebalance reminder for report 48 (Midcap150 Momentum 10, 200-day
EMA regime filter, gold instead of cash) — sends at 5, 3, 1, and 0
CALENDAR days before the estimated rebalance date of ANY of the six
semi-annual calendars report 85/87 tested (Jan/Jul, Feb/Aug, Mar/Sep,
Apr/Oct, May/Nov, Jun/Dec), each with the current live picks/regime state
and a CSV attachment, tagged with which calendar it's for.

"ESTIMATED" REBALANCE DATE: each calendar's real rebalance date is "the
LAST TRADING DAY of its two months" (rebalance_dates() in backtest10.py),
which depends on NSE's own holiday calendar — this project has no
forward-looking holiday list, so the estimate here is simply the last
CALENDAR day of the month, walked back to the nearest weekday (Mon-Fri).
In a year where NSE has a holiday in the final week, the real last
trading day could be 1-2 days earlier than this estimate — the 5/3/1/0
reminders are a spread specifically so a small estimation error doesn't
turn into a missed reminder.

THREE DIFFERENT ALERTS AROUND THE REBALANCE DAY ITSELF:
  - `--pre-close` (meant to run ~3 PM IST, before the 3:30 PM close, on
    the rebalance day, days_until == 0): fetches yfinance's CURRENT
    snapshot for today (delayed ~15 min, not the confirmed close) and
    sends it as a provisional "final call" list — the only way to get a
    same-day heads-up before you'd actually need to place the trade.
  - The normal run (no flag), still on days_until == 0: scheduled after
    the 15:30 IST close, reports the CONFIRMED close-based picks — the
    authoritative version, per report 48's own methodology.
  - `--morning-after` (meant to run ~9 AM IST, days_since_last_rebalance
    == 1, i.e. the calendar day right after the rebalance day): a safety
    net in case BOTH alerts above were missed — e.g. GitHub's own
    scheduled-workflow queue has been observed delaying a run past
    midnight IST on this repo, which the retry windows in the workflow
    YAML can't recover from (see email_rebalance_notify.yml). Run before
    NSE's 9:15 AM open, yfinance's "latest" daily bar is still
    YESTERDAY's confirmed close, so this needs no separate fetch logic —
    it's exactly the same compute_current_picks() call, just invoked the
    next morning instead.

The momentum/regime math itself lives in rebalance_signal.py, shared
with notify_rebalance.py (Telegram), so both channels can never drift
apart.
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
from rebalance_signal import compute_current_picks, build_csv, TOP_N, GOLD_TICKER, \
    MONTH_TO_CALENDAR, CALENDAR_LABELS, days_until_next_rebalance, days_since_last_rebalance

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


def build_email_body(result, mode, days_until, target_date, calendar_label):
    if mode == "pre_close":
        headline = (f"Report 48 FINAL CALL — {calendar_label} calendar — TODAY is the estimated rebalance day "
                    f"({target_date.strftime('%Y-%m-%d')})")
    elif mode == "morning_after":
        headline = (f"Report 48 MORNING-AFTER REMINDER — {calendar_label} calendar — YESTERDAY "
                    f"({target_date.strftime('%Y-%m-%d')}) was the estimated rebalance day")
    elif days_until == 0:
        headline = f"Report 48 rebalance reminder — {calendar_label} calendar — TODAY is the estimated rebalance day ({target_date.strftime('%Y-%m-%d')})"
    else:
        headline = (f"Report 48 rebalance reminder — {calendar_label} calendar — {days_until} "
                    f"day{'s' if days_until != 1 else ''} until the estimated rebalance date "
                    f"({target_date.strftime('%Y-%m-%d')})")

    lines = [headline, f"(live prices as of {result['as_of'].strftime('%Y-%m-%d')} close)", ""]
    if result["regime_on"]:
        lines.append(f"Regime: ON — NIFTY 50 ({result['nifty_close']:.0f}) is above its {EMA_SPAN}-day EMA ({result['nifty_ema']:.0f})")
        lines.append(f"Current top-{TOP_N} Midcap150 momentum picks (equal-weighted {100/TOP_N:.1f}% each):")
        lines.append("")
        for i, t in enumerate(result["picks"], 1):
            lines.append(f"  {i}. {t}")
    else:
        lines.append(f"Regime: OFF — NIFTY 50 ({result['nifty_close']:.0f}) is below its {EMA_SPAN}-day EMA ({result['nifty_ema']:.0f})")
        lines.append(f"Current signal: 100% {GOLD_TICKER} (₹{result['gold_price']:.2f})")
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
        if not force and days_until not in REMINDER_DAYS:
            print(f"{today.date()}: {days_until} days until estimated rebalance ({target_date.date()}) — "
                  f"not one of {REMINDER_DAYS}, nothing to do.")
            return
        mode = "normal"

    calendar_label = CALENDAR_LABELS[MONTH_TO_CALENDAR[target_date.month]]
    result = compute_current_picks()
    tag = {"pre_close": "FINAL CALL (~3 PM)", "morning_after": "MORNING-AFTER"}.get(
        mode, "TODAY" if days_until == 0 else f"{days_until}d to go")
    subject = f"Report 48 rebalance reminder — {calendar_label} — {tag} ({target_date.strftime('%Y-%m-%d')})"
    body = build_email_body(result, mode, days_until, target_date, calendar_label)
    print(subject)
    print(body)

    if not SMTP_USER or not SMTP_PASS or not EMAIL_TO:
        print("\nSMTP_USER / SMTP_PASS / EMAIL_TO not set — printed only, nothing sent.", file=sys.stderr)
        return

    send_email(subject, body, build_csv(result), f"report48_picks_{today.date()}.csv")
    print(f"\nSent to {EMAIL_TO}.")


if __name__ == "__main__":
    main()
