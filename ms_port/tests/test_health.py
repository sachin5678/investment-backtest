import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ms_port import health


def test_curve_only_check_count():
    # a varying series across 8 month-ends so every curve-based check is
    # evaluable (monthly std, monthly skew, a real drawdown, finite daily)
    vals = [100, 105, 95, 120, 118, 140, 135, 150]
    pts = [[f"2020-{m:02d}-01", v] for m, v in enumerate(vals, start=1)]
    h = health.health_check(pts)
    # no trades -> the 4 trade checks plus tail_trades are unavailable;
    # the 5 curve checks (worst daily, CAGR, tail monthly, monthly std,
    # growth per fall) are all scored
    assert h["checks_available"] == 5
    # +50% over 8 months annualises well above the 40% target
    assert [c for c in h["checks"] if c["id"] == "cagr"][0]["passed"] is True
    assert [c for c in h["checks"] if c["id"] == "worst_daily"][0]["passed"] is True
    assert [c for c in h["checks"] if c["id"] == "winning_trades"][0]["passed"] is None


def test_daily_and_monthly_returns():
    pts = [["2020-01-02", 100.0], ["2020-01-03", 110.0], ["2020-01-31", 121.0],
           ["2020-02-03", 121.0], ["2020-02-28", 133.1]]
    dr = health.daily_returns(pts)
    assert math.isclose(dr[0], 10.0)
    mr = health.monthly_returns(pts)
    assert len(mr) == 1  # month-over-month: Jan end 121 -> Feb end 133.1
    assert math.isclose(mr[0], 10.0, abs_tol=0.01)


def test_trades_checks():
    trades = [
        {"pct_return": 20.0, "status": "closed"},
        {"pct_return": 40.0, "status": "closed"},
        {"pct_return": -10.0, "status": "closed"},
        {"pct_return": -10.0, "status": "closed"},
        {"pct_return": 99.0, "status": "open"},  # excluded
    ]
    ts = health.traded_stats(trades)
    assert ts["n_closed"] == 4
    assert ts["win_pct"] == 50.0
    assert math.isclose(ts["avg_win_pct"], 30.0)
    assert math.isclose(ts["avg_loss_pct"], -10.0)
    assert math.isclose(ts["gain_loss_ratio"], 3.0)


def test_health_with_trades():
    # wiggly rising series: monthly variation + at least one drawdown
    vals = [100 + m + (5 if m % 3 == 0 else 0) for m in range(24)]
    pts = [[f"2021-{(m % 12) + 1:02d}-01", v] for m, v in enumerate(vals)]
    trades = [{"pct_return": 50.0}, {"pct_return": 30.0}, {"pct_return": -5.0}]
    h = health.health_check(pts, trades)
    assert h["checks_available"] == 10
    win = [c for c in h["checks"] if c["id"] == "winning_trades"][0]
    assert win["passed"] is True  # 2/3 = 66%


def test_skew_needs_three_points():
    assert health._skew([1.0, 2.0]) is None
    s = health._skew([1.0, 1.0, 1.0])
    assert s is None or abs(s) < 1e-9
