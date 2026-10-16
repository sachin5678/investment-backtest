"""Regression gate for ms_builder.py: the hero configuration (default_config)
must reproduce report 93's results92.json before any lab experiment is
trusted. Compares the key numbers side by side and prints PASS/FAIL.

Run:  py -3 check_builder_regression.py
"""
import json
import sys

import ms_builder


def get(d, *keys, default=None):
    for k in keys:
        if d is None:
            return default
        d = d.get(k) if isinstance(d, dict) else None
    return d if d is not None else default


def close(a, b, tol_pct=0.05):
    """Relative tolerance in percent (default 0.05%)."""
    if a is None or b is None:
        return False
    if a == b:
        return True
    scale = max(abs(a), abs(b), 1e-9)
    return abs(a - b) / scale * 100.0 <= tol_pct


def main():
    print("== loading report 93's results92.json ...")
    with open("results92.json", encoding="utf-8") as f:
        ref = json.load(f)

    print("== running the hero config through ms_builder ...")
    market = ms_builder.load_market()
    closes = market["closes"]
    dates = closes.index
    print(f"   window: {dates[0].date()} -> {dates[-1].date()} ({len(dates)} days)")

    rank_df, fit_df, _score = ms_builder.build_ranks(closes)
    feats = ms_builder.build_features(market)

    fmv_idx = closes.index[closes.index <= ms_builder.FMV_DATE]
    fmv_map = {}
    if len(fmv_idx):
        row = closes.loc[fmv_idx[-1]]
        fmv_map = {str(t).replace(".NS", "").upper(): float(v) for t, v in row.items() if v == v}

    cfg = ms_builder.default_config()
    variant, run = ms_builder.evaluate_variant("hero", cfg, market, feats, rank_df, fit_df, fmv_map)

    checks = []

    def add(name, mine, theirs, tol=0.05, fmt="{}"):
        ok = close(mine, theirs, tol) if isinstance(mine, (int, float)) else (mine == theirs)
        checks.append((name, ok, mine, theirs))

    add("start_date", dates[0].strftime("%Y-%m-%d"), ref["start_date"])
    add("end_date", dates[-1].strftime("%Y-%m-%d"), ref["end_date"])
    add("after_costs.cagr_pct", variant["cagr_pct"], ref["after_costs"]["cagr_pct"])
    add("after_costs.max_drawdown_pct", variant["max_drawdown_pct"], ref["after_costs"]["max_drawdown_pct"])
    add("after_costs.net_return_pct", variant["net_return_pct"], ref["after_costs"]["net_return_pct"])
    add("before_costs.cagr_pct", variant["before_costs"]["cagr_pct"], ref["before_costs"]["cagr_pct"])
    add("after_tax.cagr_pct", variant["after_tax"]["cagr_pct"], ref["after_tax"]["cagr_pct"])

    nifty_m = ms_builder.metrics_only(market["nifty"], market["common"])
    add("nifty.cagr_pct", nifty_m["cagr_pct"], ref["nifty"]["cagr_pct"])

    ref_closed = [t for t in ref["trades"] if t.get("status") == "closed"]
    mine_closed = [t for t in run["trades"] if t["status"] == "closed"]
    add("closed trades", len(mine_closed), len(ref_closed), tol=0)

    add("tax.total_tax", variant["tax"]["total_tax"], ref["tax_report"]["totals"]["total_tax"], tol=0.1)
    add("health.score", variant["health"]["score"], ref["health_check"]["score"], tol=0)

    # curve spot check: last equity point
    ref_curve = ref["after_costs"]["equity_curve"]
    my_curve = variant["equity_curve"]
    add("curve length", len(my_curve), len(ref_curve), tol=0)
    add("curve first value", my_curve[0][1], ref_curve[0][1], tol=0.01)
    add("curve last value", my_curve[-1][1], ref_curve[-1][1], tol=0.01)
    add("curve last date", my_curve[-1][0], ref_curve[-1][0])

    print()
    print("== regression report ==")
    all_ok = True
    for name, ok, mine, theirs in checks:
        flag = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"  [{flag}] {name:28s} mine={mine!r:>22}  report93={theirs!r}")

    print()
    print("ALL PASS" if all_ok else "SOME CHECKS FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
