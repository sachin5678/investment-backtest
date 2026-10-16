import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ms_port import tax


def _t(ticker, entry, exit_, ep, xp, qty=100.0):
    return {"ticker": ticker, "entry_date": entry, "exit_date": exit_,
            "entry_price": ep, "exit_price": xp, "qty": qty}


def test_fy_labels():
    assert tax.fy_label(tax._parse("2025-03-31")) == "2024-25"
    assert tax.fy_label(tax._parse("2025-04-01")) == "2025-26"


def test_simple_stcg_new_rates():
    # sold after 23 Jul 2024, held < 1 year: 20% + 4% cess
    r = tax.capital_gains_report([_t("X", "2025-01-10", "2025-06-10", 100.0, 600.0, qty=100.0)])
    assert r["years"][0]["fy"] == "2025-26"
    assert r["years"][0]["taxable_stcg"] == 50000.0
    assert abs(r["totals"]["total_tax"] - 50000 * 0.20 * 1.04) < 0.01


def test_ltcg_exemption_new_rates():
    r = tax.capital_gains_report([_t("X", "2023-01-10", "2025-06-10", 100.0, 2100.0, qty=100.0)])
    y = r["years"][0]
    assert y["taxable_ltcg"] == 200000.0 - 125000.0
    assert abs(r["totals"]["total_tax"] - (75000 * 0.125 * 1.04)) < 0.01


def test_old_rates_before_switch():
    # sold 2024-05-01 (before the 23 Jul 2024 switch), held ~11 months = STCG
    r = tax.capital_gains_report([_t("X", "2023-06-01", "2024-05-01", 100.0, 150.0, qty=100.0)])
    y = r["years"][0]
    assert y["stcg_rate_pct"] == 15.0
    assert abs(r["totals"]["total_tax"] - (5000 * 0.15 * 1.04)) < 0.01


def test_loss_setoff_and_carry_forward():
    trades = [
        _t("A", "2024-05-01", "2024-12-01", 100.0, 50.0, qty=1000.0),   # -50k STCL FY24-25
        _t("B", "2024-05-01", "2024-12-01", 100.0, 120.0, qty=1000.0),  # +20k STCG FY24-25
        _t("C", "2025-05-01", "2025-12-01", 100.0, 140.0, qty=1000.0),  # +40k STCG FY25-26
    ]
    r = tax.capital_gains_report(trades)
    y2425, y2526 = r["years"]
    assert y2425["taxable_stcg"] == 0.0
    assert y2425["carry_out_stcl"] == 30000.0
    assert abs(y2526["taxable_stcg"] - 10000.0) < 0.01
    assert abs(y2526["carry_out_stcl"]) < 0.01


def test_grandfathering_uses_fmv():
    # bought 2023 at 100, sold 2025 at 300, FMV on 31-Jan-2025 = 250
    trades = [_t("X", "2023-01-01", "2025-06-01", 100.0, 300.0, qty=100.0)]
    r = tax.capital_gains_report(trades, fmv_by_ticker={"X": 250.0})
    y = r["years"][0]
    # deemed cost 250 -> gain only 5000
    assert abs(y["realised_pnl"] - 5000.0) < 0.01
    assert r["totals"]["n_grandfathered_trades"] == 1
    # without FMV: full 20000 gain
    r2 = tax.capital_gains_report(trades)
    assert abs(r2["years"][0]["realised_pnl"] - 20000.0) < 0.01


def test_ltcl_only_offsets_ltcg():
    trades = [
        _t("A", "2020-01-01", "2025-06-01", 100.0, 50.0, qty=1000.0),   # -50k LTCL
        _t("B", "2025-05-01", "2025-12-01", 100.0, 130.0, qty=1000.0),  # +30k STCG
    ]
    r = tax.capital_gains_report(trades)
    y = r["years"][0]
    assert y["taxable_stcg"] == 30000.0  # LTCL may NOT offset STCG
    assert y["carry_out_ltcl"] == 50000.0


def test_after_tax_curve_deducts_at_fy_end():
    pts = [["2025-03-01", 100.0], ["2025-03-31", 100.0], ["2025-04-30", 110.0]]
    adj, applied = tax.after_tax_curve(pts, {"2024-25": 10.0})
    assert applied[0]["fy"] == "2024-25" and applied[0]["date"] == "2025-03-31"
    # tax is paid AT the 2025-03-31 close; history is unchanged, only
    # subsequent values are scaled by (1 - 10/100) = 0.9
    assert abs(adj[0][1] - 100.0) < 0.01
    assert abs(adj[1][1] - 100.0) < 0.01
    assert abs(adj[2][1] - 99.0) < 0.01


def test_normalize_trades_scales_alloc():
    raw = [{"ticker": "TCS.NS", "entry_date": "2020-01-01", "exit_date": "2020-06-01",
            "entry_price": 100.0, "exit_price": 110.0, "alloc": 500.0, "status": "closed"}]
    norm = tax.normalize_trades(raw, alloc_scale=2.0)  # qty = 500*2/100 = 10
    assert abs(norm[0]["qty"] - 10.0) < 1e-9
    assert norm[0]["ticker"] == "TCS"
