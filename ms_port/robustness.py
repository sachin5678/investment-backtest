"""MomentumScore-style robustness — "Is this result the rules, or luck?"

MomentumScore's robustness check re-runs the strategy two more ways:

  * Date luck — on every other rebalance day (days 15-25 of the month).
    "The day you picked should not be the only one that works."
  * Both halves — the first and the second half of the period separately.
    "A sound rule should beat the benchmark in both, not only in one
    lucky stretch."

This module implements the verdict logic for both, over plain
[[date, value], ...] point series (same shape as every results*.json
equity curve):

  halves_check(strategy, benchmark)      -> per-half CAGR vs benchmark
  variants_check(benchmark, variants)    -> N-variant spread (date luck)
  robustness_report(strategy, benchmark, variants=...)

For archived reports, variants come from rebalance-offset sibling
reports (e.g. reports 85/86's month-offset calendars, report 92's six
calendars). The report-93 engine generates its own variants directly
(same rules, day 15 vs month-end) and embeds the verdict in its
results JSON.
"""
from __future__ import annotations

from datetime import date

from .health import cagr_pct


def _parse(s):
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


def _by_date(points):
    return {p[0]: p[1] for p in points}


def align(strategy_points, benchmark_points):
    """Intersect two point series on date; returns (strat, bench) aligned."""
    bd = _by_date(benchmark_points)
    common = [(d, v) for d, v in strategy_points if d in bd]
    return common, [(d, bd[d]) for d, _ in common]


def _slice(points, start, end):
    return [p for p in points if start <= p[0] <= end]


def halves_check(strategy_points, benchmark_points):
    """Split the COMMON window in half by date; each half's CAGR for the
    strategy and the benchmark. passes = strategy beats benchmark in
    both halves."""
    strat, bench = align(strategy_points, benchmark_points)
    if len(strat) < 4:
        return None
    mid = strat[len(strat) // 2][0]
    out = {"benchmark_first_date": strat[0][0], "benchmark_last_date": strat[-1][0],
           "split_date": mid, "halves": []}
    for label, s_pts, b_pts in (
        ("first", _slice(strat, strat[0][0], mid), _slice(bench, strat[0][0], mid)),
        ("second", _slice(strat, mid, strat[-1][0]), _slice(bench, mid, strat[-1][0])),
    ):
        s_cagr = cagr_pct(s_pts)
        b_cagr = cagr_pct(b_pts)
        out["halves"].append({
            "label": label,
            "start": s_pts[0][0], "end": s_pts[-1][0],
            "strategy_cagr_pct": s_cagr, "benchmark_cagr_pct": b_cagr,
            "passed": (s_cagr > b_cagr) if (s_cagr is not None and b_cagr is not None) else None,
        })
    passed_flags = [h["passed"] for h in out["halves"] if h["passed"] is not None]
    out["passed_both"] = all(passed_flags) if passed_flags else None
    out["passed_any"] = any(passed_flags) if passed_flags else None
    return out


def variants_check(benchmark_points, variants):
    """variants: list of {"label": str, "points": [[d, v], ...], "kind": str?}.

    Each variant is compared to the benchmark over its OWN window (the
    natural reading of "the day you picked should not be the only one
    that works" — each calendar is judged on the stretch it actually
    covered). Verdict:
      pass  — every variant beats the benchmark
      mixed — at least half the variants beat the benchmark
      fail  — fewer than half do
    """
    bd = _by_date(benchmark_points)
    rows = []
    for v in variants:
        pts = [(d, val) for d, val in v["points"] if d in bd]
        b_pts = [(d, bd[d]) for d, _ in pts]
        s_cagr = cagr_pct(pts)
        b_cagr = cagr_pct(b_pts)
        rows.append({
            "label": v["label"], "kind": v.get("kind"),
            "start": pts[0][0] if pts else None, "end": pts[-1][0] if pts else None,
            "strategy_cagr_pct": s_cagr, "benchmark_cagr_pct": b_cagr,
            "passed": (s_cagr > b_cagr) if (s_cagr is not None and b_cagr is not None) else None,
        })
    flags = [r["passed"] for r in rows if r["passed"] is not None]
    n_pass = sum(1 for f in flags if f)
    if not flags:
        verdict = None
    elif n_pass == len(flags):
        verdict = "pass"
    elif n_pass * 2 >= len(flags):
        verdict = "mixed"
    else:
        verdict = "fail"
    cagrs = [r["strategy_cagr_pct"] for r in rows if r["strategy_cagr_pct"] is not None]
    return {
        "kind": "date_luck", "verdict": verdict,
        "n_variants": len(rows), "n_pass": n_pass,
        "min_cagr_pct": min(cagrs) if cagrs else None,
        "max_cagr_pct": max(cagrs) if cagrs else None,
        "variants": rows,
    }


def robustness_report(strategy_points, benchmark_points, variants=None):
    """The full robustness card: halves (+ optional date-luck variants)."""
    halves = halves_check(strategy_points, benchmark_points)
    dl = variants_check(benchmark_points, variants) if variants else None
    verdicts = []
    if halves and halves.get("passed_both") is not None:
        verdicts.append(halves["passed_both"])
    if dl and dl.get("verdict"):
        verdicts.append(dl["verdict"] == "pass")
    overall = None
    if verdicts:
        overall = all(verdicts) if len(verdicts) > 1 else verdicts[0]
    return {"halves": halves, "date_luck": dl, "passed_overall": overall}
