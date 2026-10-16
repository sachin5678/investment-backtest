"""MomentumScore-style "Health check" — 10 rules of thumb, score = the
share of the target ranges the result meets.

The card's checks and exact target ranges were transcribed from a live
MomentumScore review page (reference strategy "hawda", 2026-10-16):

    Winning trades            target >= 50%      50.00%
    Average gain per winner   target >= 30%      29.12%
    Average loss per loser    target <= 15% loss -9.94%
    Gain-to-loss ratio        target >= 2        2.93
    Worst fall · daily        target <= 20%      -21.20%
    Annual growth (CAGR)      target >= 40%      11.67%
    Tail risk · monthly       target -2 to +2     1.79
    Tail risk · trade         target -2 to +2     53.99
    Monthly swing (std dev)   target <= 15       3.45
    Growth per unit of fall   target >= 2.5      0.55

TWO DISCLOSED PROXIES (MomentumScore's own definitions are not published;
these are the closest reproducible readings of the numbers above):

  * "Tail risk" is implemented as the SKEWNESS of the return
    distribution (monthly returns / per-trade returns). It is the only
    textbook statistic that is dimensionless, plausibly ~1.8 for monthly
    equity returns, and allows the stated "-2 to +2" band to apply
    equally to trades and months.
  * All prices here come from the report's own equity curve. Unless the
    caller passes full-resolution data, that curve is the downsampled
    (<=1500 points) chart series embedded in every results*.json — so
    "worst daily fall" is the worst fall across the SAMPLED days, a
    documented approximation for archived reports. The report-93 engine
    computes this helper on its own full-resolution series.

Trade-based checks (win rate, avg winner/loser, gain-to-loss ratio, tail
risk · trade) are only scored when a trade log is available; otherwise
the score is reported as met/available out of the checks that COULD be
evaluated, and `checks_available` is set accordingly.
"""
from __future__ import annotations

import math


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def _std(xs):
    if len(xs) < 2:
        return None
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def _skew(xs):
    if len(xs) < 3:
        return None
    m = _mean(xs)
    s = _std(xs)
    if not s:
        return None
    return sum((x - m) ** 3 for x in xs) / len(xs) / (s ** 3)


def _finite(v):
    """None for NaN/±inf — keeps every downstream JSON strictly valid
    (Python emits bare NaN by default; the webapp's JSON.parse does not
    accept it)."""
    if v is None:
        return None
    try:
        return float(v) if math.isfinite(float(v)) else None
    except (TypeError, ValueError):
        return None


def daily_returns(points):
    """points: [[date_str, value], ...] -> list of daily pct returns (as %)"""
    out = []
    for i in range(1, len(points)):
        p0, p1 = points[i - 1][1], points[i][1]
        if p0:
            out.append((p1 / p0 - 1.0) * 100.0)
    return out


def monthly_returns(points):
    """Last value of each calendar month -> month-over-month pct returns (%)."""
    month_end = []
    for d, v in points:
        key = d[:7]
        if month_end and month_end[-1][0] == key:
            month_end[-1] = (key, v)
        else:
            month_end.append((key, v))
    out = []
    for i in range(1, len(month_end)):
        p0, p1 = month_end[i - 1][1], month_end[i][1]
        if p0:
            out.append((p1 / p0 - 1.0) * 100.0)
    return out


def max_drawdown_pct(points):
    peak = None
    mdd = 0.0
    for _, v in points:
        peak = v if peak is None or v > peak else peak
        if peak:
            mdd = min(mdd, (v - peak) / peak * 100.0)
    return mdd


def cagr_pct(points):
    if len(points) < 2:
        return None
    from datetime import date

    def parse(s):
        y, m, d = s.split("-")
        return date(int(y), int(m), int(d))

    days = (parse(points[-1][0]) - parse(points[0][0])).days
    years = days / 365.25
    if years <= 0 or not points[0][1]:
        return None
    return ((points[-1][1] / points[0][1]) ** (1.0 / years) - 1.0) * 100.0


def trade_return_pcts(trades):
    out = []
    for t in trades:
        if t.get("status") == "open":
            continue
        r = t.get("pct_return", t.get("return_pct", t.get("pct_return_on_capital")))
        if r is not None:
            out.append(float(r))
    return out


def traded_stats(trades):
    rets = trade_return_pcts(trades)
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    return {
        "n_closed": len(rets),
        "win_pct": (len(wins) / len(rets) * 100.0) if rets else None,
        "avg_win_pct": _mean(wins) if wins else None,
        "avg_loss_pct": _mean(losses) if losses else None,
        "gain_loss_ratio": (abs(_mean(wins) / _mean(losses))
                            if wins and losses and _mean(losses) else None),
        "tail_skew": _skew(rets),
    }


CHECK_DEFS = [
    ("winning_trades", "Winning trades", "target >= 50%"),
    ("avg_winner", "Average gain per winner", "target >= 30%"),
    ("avg_loser", "Average loss per loser", "target <= 15% loss"),
    ("gain_loss_ratio", "Gain-to-loss ratio", "target >= 2"),
    ("worst_daily", "Worst fall · daily", "target <= 20%"),
    ("cagr", "Annual growth (CAGR)", "target >= 40%"),
    ("tail_monthly", "Tail risk · monthly returns", "target -2 to +2"),
    ("tail_trades", "Tail risk · trade returns", "target -2 to +2"),
    ("monthly_std", "Monthly swing (std. dev.)", "target <= 15"),
    ("growth_per_fall", "Growth per unit of fall", "target >= 2.5"),
]


def _fmt_pct(v):
    if v is None:
        return "—"
    s = "+" if v > 0 else ""
    return f"{s}{v:,.2f}%"


def health_check(points, trades=None):
    """Returns the full 10-check card for one equity curve (+ trade log).

    points: [[date_str, value], ...] — the series to judge.
    trades: optional trade log (results*.json trade dicts). When absent,
    the four trade-based checks are reported with passed=None and are
    excluded from the score denominator.
    """
    d_rets = [r for r in daily_returns(points) if math.isfinite(r)]
    m_rets = [r for r in monthly_returns(points) if math.isfinite(r)]
    ts = traded_stats(trades) if trades else None

    cagr = _finite(cagr_pct(points))
    mdd = _finite(max_drawdown_pct(points))
    worst_daily = min(d_rets) if d_rets else None
    monthly_std = _finite(_std(m_rets))
    monthly_skew = _finite(_skew(m_rets))
    growth_per_fall = _finite((cagr / abs(mdd)) if (cagr is not None and mdd) else None)

    rows = {
        "winning_trades": (ts["win_pct"] if ts else None, _fmt_pct(ts["win_pct"]) if ts else None,
                           (ts["win_pct"] >= 50.0) if ts and ts["win_pct"] is not None else None),
        "avg_winner": (ts["avg_win_pct"] if ts else None, _fmt_pct(ts["avg_win_pct"]) if ts else None,
                       (ts["avg_win_pct"] >= 30.0) if ts and ts["avg_win_pct"] is not None else None),
        "avg_loser": (ts["avg_loss_pct"] if ts else None, _fmt_pct(ts["avg_loss_pct"]) if ts else None,
                      (ts["avg_loss_pct"] >= -15.0) if ts and ts["avg_loss_pct"] is not None else None),
        "gain_loss_ratio": (ts["gain_loss_ratio"] if ts else None,
                            f"{ts['gain_loss_ratio']:,.2f}" if ts and ts["gain_loss_ratio"] is not None else None,
                            (ts["gain_loss_ratio"] >= 2.0) if ts and ts["gain_loss_ratio"] is not None else None),
        "worst_daily": (worst_daily, _fmt_pct(worst_daily), (worst_daily >= -20.0) if worst_daily is not None else None),
        "cagr": (cagr, _fmt_pct(cagr), (cagr >= 40.0) if cagr is not None else None),
        "tail_monthly": (monthly_skew, f"{monthly_skew:,.2f}" if monthly_skew is not None else None,
                         (abs(monthly_skew) <= 2.0) if monthly_skew is not None else None),
        "tail_trades": ((ts["tail_skew"] if ts else None),
                        f"{ts['tail_skew']:,.2f}" if ts and ts["tail_skew"] is not None else None,
                        (abs(ts["tail_skew"]) <= 2.0) if ts and ts["tail_skew"] is not None else None),
        "monthly_std": (monthly_std, f"{monthly_std:,.2f}" if monthly_std is not None else None,
                        (monthly_std <= 15.0) if monthly_std is not None else None),
        "growth_per_fall": (growth_per_fall, f"{growth_per_fall:,.2f}" if growth_per_fall is not None else None,
                            (growth_per_fall >= 2.5) if growth_per_fall is not None else None),
    }

    checks = []
    met = 0
    available = 0
    for cid, label, target in CHECK_DEFS:
        value, value_text, passed = rows[cid]
        if passed is not None:
            available += 1
            met += 1 if passed else 0
        checks.append({
            "id": cid, "label": label, "target_text": target,
            "value": value, "value_text": value_text, "passed": passed,
        })

    score = round(met / available * 100) if available else None
    return {
        "score": score,
        "checks_met": met,
        "checks_available": available,
        "checks_total": len(CHECK_DEFS),
        "checks": checks,
        "has_trades": bool(trades),
        "curve_metrics": {
            "cagr_pct": cagr,
            "max_drawdown_pct": mdd,
            "worst_daily_pct": worst_daily,
            "monthly_std_pct": monthly_std,
            "monthly_skew": monthly_skew,
        },
        "trade_metrics": ts,
        "note": ("Score is the share of the target ranges met. "
                 "Trade-based checks are excluded when the report has no trade log."),
    }
