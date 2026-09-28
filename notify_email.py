"""
Email rebalance reminder for report 48 (Midcap150 Momentum 10, 200-day
EMA regime filter, gold instead of cash, semi-annual June/December
rebalance) — sends at 5, 3, and 1 CALENDAR days before the estimated
rebalance date, each with the current live picks/regime state and a CSV
attachment.

"ESTIMATED" REBALANCE DATE: report 48's real rebalance date is "the LAST
TRADING DAY of June/December" (rebalance_dates() in backtest10.py),
which depends on NSE's own holiday calendar — this project has no
forward-looking holiday list, so the estimate here is simply the last
CALENDAR day of the month, walked back to the nearest weekday (Mon-Fri).
In a year where NSE has a holiday in the final week, the real last
trading day could be 1-2 days earlier than this estimate — the 5/3/1
reminders are a spread specifically so a small estimation error doesn't
turn into a missed reminder.

The momentum/regime math itself lives in rebalance_signal.py, shared
with notify_rebalance.py (Telegram), so both channels can never drift
apart.
"""
import calendar
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
from rebalance_signal import compute_current_picks, build_csv, REBALANCE_MONTHS, TOP_N, GOLD_TICKER

REMINDER_DAYS = (5, 3, 1)


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


def estimated_rebalance_date(year, month):
    last_day = calendar.monthrange(year, month)[1]
    d = pd.Timestamp(year, month, last_day)
    while d.weekday() >= 5:  # Saturday=5, Sunday=6
        d -= pd.Timedelta(days=1)
    return d


def days_until_next_rebalance(today):
    candidates = []
    for month in REBALANCE_MONTHS:
        for year in (today.year, today.year + 1):
            d = estimated_rebalance_date(year, month)
            if d >= today:
                candidates.append(d)
    target = min(candidates)
    return (target - today).days, target


def build_email_body(result, today, days_until, target_date):
    lines = [
        f"Report 48 rebalance reminder — {days_until} day{'s' if days_until != 1 else ''} until the estimated rebalance date ({target_date.strftime('%Y-%m-%d')})",
        f"(live prices as of {result['as_of'].strftime('%Y-%m-%d')} close)",
        "",
    ]
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
    if not force and days_until not in REMINDER_DAYS:
        print(f"{today.date()}: {days_until} days until estimated rebalance ({target_date.date()}) — "
              f"not one of {REMINDER_DAYS}, nothing to do.")
        return

    result = compute_current_picks()
    subject = f"Report 48 rebalance reminder — {days_until}d to go ({target_date.strftime('%Y-%m-%d')})"
    body = build_email_body(result, today, days_until, target_date)
    print(subject)
    print(body)

    if not SMTP_USER or not SMTP_PASS or not EMAIL_TO:
        print("\nSMTP_USER / SMTP_PASS / EMAIL_TO not set — printed only, nothing sent.", file=sys.stderr)
        return

    send_email(subject, body, build_csv(result), f"report48_picks_{today.date()}.csv")
    print(f"\nSent to {EMAIL_TO}.")


if __name__ == "__main__":
    main()
