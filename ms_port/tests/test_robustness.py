import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ms_port import robustness


def _pts(start, values):
    """monthly points starting at start='2020-01'"""
    y, m = int(start[:4]), int(start[5:7])
    out = []
    for v in values:
        out.append([f"{y:04d}-{m:02d}-01", v])
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def test_halves_pass_when_strategy_beats_bench_both_halves():
    strat = _pts("2020-01", [100, 110, 121, 133, 146, 161, 177, 195])
    bench = _pts("2020-01", [100, 101, 102, 103, 104, 105, 106, 107])
    out = robustness.halves_check(strat, bench)
    assert out["passed_both"] is True
    assert all(h["passed"] for h in out["halves"])


def test_halves_fail_when_one_half_loses():
    # good first half, weaker second half than bench
    strat = _pts("2020-01", [100, 150, 200, 250, 251, 252, 253, 254])
    bench = _pts("2020-01", [100, 100, 100, 100, 200, 300, 400, 500])
    out = robustness.halves_check(strat, bench)
    assert out["passed_both"] is False
    assert out["passed_any"] is True


def test_variants_verdicts():
    bench = _pts("2020-01", [100] + [100] * 7)
    good = {"label": "good", "points": _pts("2020-01", [100, 110, 120, 130, 140, 150, 160, 170])}
    bad = {"label": "bad", "points": _pts("2020-01", [100, 99, 98, 97, 96, 95, 94, 93])}
    out = robustness.variants_check(bench, [good, good])
    assert out["verdict"] == "pass" and out["n_pass"] == 2
    out2 = robustness.variants_check(bench, [good, bad])
    assert out2["verdict"] == "mixed"
    out3 = robustness.variants_check(bench, [bad, bad, good])
    assert out3["verdict"] == "fail"


def test_full_report():
    bench = _pts("2020-01", [100] + [100] * 7)
    strat = _pts("2020-01", [100, 110, 121, 133, 146, 161, 177, 195])
    rep = robustness.robustness_report(strat, bench, variants=[{"label": "v1", "points": strat}])
    assert rep["passed_overall"] is True
    assert rep["date_luck"]["verdict"] == "pass"
