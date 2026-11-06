"""
Regime-flip alert for the whole alert suite — reports 48, 71, 91, 92 and 98.

The month-end reminders (notify_*.py) only fire in the last days of a
rebalance month, but every one of these strategies ALSO switches mid-month
the moment NIFTY 50 closes on the other side of its 200-day EMA (the
backtests act on that same day's close, confirm_days=1 — see
backtest42.build_index_regime_filtered_with_hedge). This script sends the
alert for that event: one message, with what each report does on the flip.

STATELESS: a flip is "the latest bar's regime differs from the previous
bar's regime", both recomputed from live prices (reports_signal), so no
saved state is needed. Duplicate suppression is the workflow's
once-per-mode-per-day lock; the script itself refuses stale data (the
after-close/pre-close modes need today's bar, morning-after needs the
previous weekday's bar), so holidays and weekends can't replay an old flip.

MODES (same three as the month-end alerts):
  pre_close      ~3 PM IST, provisional — today's bar is still forming, so a
                 flip here can revert by the close.
  after_close    confirmed flip on today's closed bar.
  morning_after  safety net before the 9:15 open for yesterday's flip.
"""
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from backtest42 import EMA_SPAN
from rebalance_signal import TOP_N, GOLD_TICKER
from reports_signal import compute_state


def env_or(name, default=None):
    value = os.environ.get(name)
    return value if value else default


TELEGRAM_BOT_TOKEN = env_or("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = env_or("TELEGRAM_CHAT_ID")
SMTP_HOST = env_or("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(env_or("SMTP_PORT", "587"))
SMTP_USER = env_or("SMTP_USER")
SMTP_PASS = env_or("SMTP_PASS")
EMAIL_FROM = env_or("EMAIL_FROM", SMTP_USER)
EMAIL_TO = env_or("EMAIL_TO")


def previous_weekday(d):
    d = d - pd.Timedelta(days=1)
    while d.weekday() >= 5:
        d -= pd.Timedelta(days=1)
    return d


def _picks(lines, tickers, pct=None):
    for i, t in enumerate(tickers, 1):
        lines.append(f"    {i}. {t}" + (f" — {pct:.1f}%" if pct else ""))


def build_message(state, mode, forced_test):
    regime_on = state["regime_on"]
    n, e = state["nifty_close"], state["nifty_ema"]
    gold = state["gold_price"]
    gold_txt = f"{GOLD_TICKER} (₹{gold:.2f})" if gold else GOLD_TICKER
    as_of = state["as_of"].strftime("%Y-%m-%d")
    direction = "ABOVE" if regime_on else "BELOW"

    if mode == "pre_close":
        tag = "PROVISIONAL (~3 PM snapshot, may revert by the close)"
    elif mode == "morning_after":
        tag = f"MORNING-AFTER safety net — the flip happened at {as_of}'s close"
    else:
        tag = f"CONFIRMED at {as_of}'s close"

    lines = []
    if forced_test:
        lines.append("🧪 TEST — no actual flip right now; showing what a flip to the current regime would say.")
    lines.append(f"🔔 REGIME FLIP — NIFTY 50 crossed {direction} its {EMA_SPAN}-day EMA")
    lines.append(tag)
    lines.append(f"NIFTY 50 {n:.0f} vs EMA {e:.0f} (was {'above' if state['prev_regime_on'] else 'below'} "
                 f"at the previous close).")
    lines.append("The backtests switch on the day of the cross, at that day's close — not at the next rebalance.")
    lines.append("")
    lines.append("What each report does now:")
    lines.append("")

    if not regime_on:
        lines.append(f"• Report 48 — SELL all stocks → 100% {gold_txt}")
        lines.append("• Reports 91 / 92 — SELL all stocks →")
        if state["guard_passes"] is None:
            lines.append(f"    100% {gold_txt} (not enough live history for the gold-strength guard check)")
        elif state["guard_passes"]:
            lines.append(f"    guard PASSES (gold 6m {state['guard_gold_6m_pct']:+.1f}% beats NIFTY "
                         f"{state['guard_nifty_6m_pct']:+.1f}% and is positive) → 100% {gold_txt}")
        else:
            lines.append(f"    guard FAILS (gold 6m {state['guard_gold_6m_pct']:+.1f}% vs NIFTY "
                         f"{state['guard_nifty_6m_pct']:+.1f}%) → 100% FLAT CASH")
        lines.append(f"• Report 71 — SELL the 70% stock sleeve; whole book → 100% {gold_txt}")
        lines.append(f"• Report 98 — SELL all stocks → 100% {gold_txt}")
    else:
        lines.append(f"• Reports 48 / 91 / 92 — SELL the gold/cash hedge → BUY the top-{TOP_N}, "
                     f"{100 / TOP_N:.1f}% each:")
        _picks(lines, state["picks"])
        lines.append(f"• Report 71 — back to 70/30: 7.0% each in the same top-{TOP_N}, keep 30% in {gold_txt}")
        a, b = state["stack_a"], state["stack_b"]
        lines.append(f"• Report 98 — fresh top-{TOP_N}, 10.0% each. Stack A:")
        _picks(lines, a)
        if b == a:
            lines.append("  Stack B (new buys need 6m > 0): identical to stack A.")
        else:
            lines.append("  Stack B (new buys need 6m > 0):")
            _picks(lines, b)

    lines.append("")
    lines.append("⚠️ Proof-of-concept alert — verify independently before acting. Not investment advice.")
    return "\n".join(lines)


def send_telegram(text):
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=30)
    r.raise_for_status()


def send_email(subject, body):
    msg = MIMEMultipart()
    msg["Subject"], msg["From"], msg["To"] = subject, EMAIL_FROM, EMAIL_TO
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


def main():
    today = pd.Timestamp.now(tz="Asia/Kolkata").normalize().tz_localize(None)
    force = "--force" in sys.argv
    mode = "pre_close" if "--pre-close" in sys.argv else "morning_after" if "--morning-after" in sys.argv else "after_close"

    state = compute_state(98)
    as_of = state["as_of"].normalize()

    if not force:
        if mode == "morning_after":
            if as_of != previous_weekday(today):
                print(f"{today.date()}: latest bar is {as_of.date()}, not the previous weekday — nothing to do.")
                return
        elif as_of != today:
            print(f"{today.date()}: latest bar is {as_of.date()}, not today's — market closed or data stale, nothing to do.")
            return

    flipped = state["regime_on"] != state["prev_regime_on"]
    if not flipped and not force:
        side = "above" if state["regime_on"] else "below"
        print(f"{today.date()}: no regime flip (NIFTY {state['nifty_close']:.0f} still {side} its EMA "
              f"{state['nifty_ema']:.0f}) — nothing to do.")
        return

    message = build_message(state, mode, forced_test=not flipped)
    direction = "above" if state["regime_on"] else "below"
    subject = f"Regime flip — NIFTY 50 crossed {direction} its {EMA_SPAN}-EMA ({as_of.strftime('%Y-%m-%d')})"
    print(subject)
    print(message)

    sent = []
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            send_telegram(message)
            sent.append("Telegram")
        except Exception as ex:
            print(f"Telegram send failed: {ex}", file=sys.stderr)
    if SMTP_USER and SMTP_PASS and EMAIL_TO:
        try:
            send_email(subject, message)
            sent.append(EMAIL_TO)
        except Exception as ex:
            print(f"Email send failed: {ex}", file=sys.stderr)

    if sent:
        print(f"Sent to {' + '.join(sent)}.")
    else:
        print("\nNo Telegram/SMTP secrets set (or all sends failed) — nothing sent.", file=sys.stderr)


if __name__ == "__main__":
    main()
