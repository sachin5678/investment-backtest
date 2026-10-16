"""Builds webapp/public/data/ms_lab.json — the cross-report MomentumScore
review layer.

Scans every results*.json in webapp/public/data and, for each equity
series inside it, computes:

  * the 10-check Health score (ms_port.health) — trade-based checks only
    for series that carry a trade log, curve checks otherwise (the curve
    values come from the report's own downsampled <=1500-point chart
    series, a documented approximation; report 93's engine computes its
    own exact card on full-resolution data and embeds it in its results)
  * the robustness verdict (ms_port.robustness): both-halves vs the file's
    own NIFTY benchmark series, where one exists

and, for the files that carry closed-trade logs, a capital-gains
estimate (ms_port.tax). Tradelog files that store relative "alloc" units
(reports 24/26/31) are scaled linearly to a ₹1,00,000 starting position —
their original alloc unit is relative, not rupee — and that scaling is
disclosed in each file's tax notes. USD-denominated QQQ variants in
results.json are excluded from tax (this is an Indian capital-gains
estimate).

Run from the repo root:

    py -3 build_ms_lab.py

Writes webapp/public/data/ms_lab.json. Idempotent; safe to re-run after
any new report lands.
"""
from __future__ import annotations

import glob
import json
import os
import sys

from ms_port import health as ms_health
from ms_port import robustness as ms_robustness
from ms_port import tax as ms_tax

DATA_DIR = os.path.join("webapp", "public", "data")
OUT = os.path.join(DATA_DIR, "ms_lab.json")
CAPITAL_INR = 100_000.0
BENCHMARK_HINTS = ("nifty", "gold_benchmark", "midcap", "gold")


def looks_like_series(obj):
    if not isinstance(obj, dict):
        return False
    has_curve = isinstance(obj.get("equity_curve"), list) or isinstance(obj.get("value_curve"), list)
    has_metrics = isinstance(obj.get("max_drawdown_pct"), (int, float)) or \
        isinstance(obj.get("longest_underwater_days"), (int, float))
    return has_curve and has_metrics


def series_points(obj):
    """equity_curve straight up; for SIP-style value_curve + invested_curve
    pairs, the value/invested ratio (so the score judges the STRATEGY, not
    the ever-rising raw account value)."""
    if isinstance(obj.get("equity_curve"), list) and obj["equity_curve"]:
        return [[p[0], float(p[1])] for p in obj["equity_curve"]]
    vc = obj.get("value_curve")
    ic = obj.get("invested_curve")
    if isinstance(vc, list) and isinstance(ic, list) and vc and ic:
        ic_map = {p[0]: p[1] for p in ic}
        return [[p[0], float(p[1]) / ic_map[p[0]] * 100.0] for p in vc if ic_map.get(p[0])]
    return None


def find_trades(obj, depth=0):
    """First 'trades' list anywhere in this object's subtree (close to how
    ReportPage takes raw.trades at the top level)."""
    if depth > 6:
        return None
    if isinstance(obj, dict):
        t = obj.get("trades")
        if isinstance(t, list) and t:
            return t
        for v in obj.values():
            got = find_trades(v, depth + 1)
            if got:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = find_trades(v, depth + 1)
            if got:
                return got
    return None


def walk_series(obj, path=""):
    if looks_like_series(obj):
        yield path, obj
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_series(v, f"{path}/{k}" if path else k)


def _curve_value_at(curve, date_str):
    """Last curve value on or before date_str (curve = [[d, v], ...])."""
    val = None
    for d, v in curve:
        if d <= date_str:
            val = v
        else:
            break
    return val


def _find_main_curve(data):
    for key in ("momentum10", "original", "filtered", "gold_filtered"):
        v = data.get(key)
        if isinstance(v, dict) and isinstance(v.get("equity_curve"), list) and v["equity_curve"]:
            return v["equity_curve"]
    for v in data.values():
        if isinstance(v, dict) and isinstance(v.get("equity_curve"), list) and v["equity_curve"]:
            return v["equity_curve"]
    return None


def scale_trades_for_tax(trades, file_data=None):
    """Normalize a trade list to rupee trades; returns (trades, scale_note).

    Engine-style trades carry qty/shares already. Alloc-unit trades
    (reports 24/26/31) are in ABSOLUTE index units — base 100 at the
    project's 2008 origin, not rupees. They are scaled so that the
    report's own window START represents a Rs 1,00,000 position:

        alloc_at_window_start = batch_total(first full 10-batch, at t0)
                                x 100 / curve_value(t0)

    where curve_value(t0) is the file's own (window-renormalized to 100)
    strategy curve on that batch date — same index, so the ratio is
    exact. Falls back to "Rs 1L at t0" when no curve is available."""
    has_alloc = any(t.get("alloc") is not None for t in trades[:5])
    if not has_alloc:
        return ms_tax.normalize_trades(trades, alloc_scale=None), None
    batches = {}
    for t in trades:
        if t.get("alloc") is not None and t.get("entry_date"):
            batches.setdefault(t["entry_date"], []).append(float(t["alloc"]))
    if not batches:
        return [], None
    t0 = next((dt for dt in sorted(batches) if len(batches[dt]) >= 10), None)
    if t0 is None:
        t0 = max(batches, key=lambda dt: len(batches[dt]))
    batch_total = sum(batches[t0])
    curve = _find_main_curve(file_data or {})
    curve_at = _curve_value_at(curve, t0) if curve else None
    if curve and curve_at and curve_at > 0:
        units_at_start = batch_total * 100.0 / curve_at
        note = (f"Alloc units are absolute index units (base 100 at the project origin); scaled so "
                f"the report's window start = Rs 1,00,000. First full batch {t0}: {batch_total:.1f} units, "
                f"curve {curve_at:.1f} on that date -> {CAPITAL_INR:.0f}/{units_at_start:.1f} per unit.")
    else:
        units_at_start = batch_total
        note = (f"Alloc-unit trade log scaled so the first full batch ({t0}, {batch_total:.1f} units) "
                f"= Rs 1,00,000; no matching curve found for a window-start rebase.")
    scale = CAPITAL_INR / units_at_start
    norm = ms_tax.normalize_trades(trades, alloc_scale=scale)
    return norm, note


def fmv_map_from_prices():
    """31-Jan-2025 FMV per ticker for s.112A grandfathering, straight from
    the regenerated midcap150 price cache; empty when the cache is absent."""
    try:
        import pandas as pd  # noqa: F401 (pickle needs pandas imported)
        from backtest13 import load_midcap150_closes
        closes = load_midcap150_closes()
        # nearest trading day on/before 2025-01-31
        idx = closes.index[closes.index <= "2025-01-31"]
        if len(idx) == 0:
            return {}
        row = closes.loc[idx[-1]]
        return {str(t).replace(".NS", "").upper(): float(v) for t, v in row.items() if v == v}
    except Exception:
        return {}


def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "results*.json")))
    out = {
        "generated": None,
        "method_note": (
            "Health = share of the 10 MomentumScore target ranges met; trade-based checks only "
            "when the report carries a trade log, otherwise the score is met/available out of the "
            "curve checks. Curve checks here run on each report's own downsampled chart series "
            "(<=1500 points) - close, not bit-exact; report 93's engine computes its own exact "
            "card on full-resolution data. Robustness = beats the benchmark in BOTH halves of the "
            "(common) window. Tax = capital-gains estimate, 23 Jul 2024 regime + cess + set-off."
        ),
        "checks_definition": [
            {"id": cid, "label": label, "target": target}
            for cid, label, target in ms_health.CHECK_DEFS
        ],
        "reports": {},
        "taxes": {},
        "skipped_tax": [],
    }

    fmv = fmv_map_from_prices()
    n_series = 0
    n_scored = 0

    for p in files:
        name = os.path.basename(p)
        if name == "ms_lab.json":
            continue
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print(f"  !! {name}: unreadable ({e})")
            continue

        entries = list(walk_series(data))
        if not entries:
            continue

        # benchmark series for this file: prefer an exact 'nifty' key
        bench_pts = None
        for path, obj in entries:
            last = path.split("/")[-1].lower()
            if last == "nifty":
                bench_pts = series_points(obj)
                break
        if bench_pts is None:
            for path, obj in entries:
                last = path.split("/")[-1].lower()
                if "nifty" in last:
                    bench_pts = series_points(obj)
                    break

        series_out = []
        for path, obj in entries:
            pts = series_points(obj)
            if not pts or len(pts) < 3:
                continue
            n_series += 1
            trades = find_trades(obj)
            if trades is None:
                # top-level files put the log beside the series
                trades = None
            h = ms_health.health_check(pts, trades)
            last = path.split("/")[-1].lower()
            kind = "benchmark" if any(hint in last for hint in BENCHMARK_HINTS) else "strategy"
            rob = None
            if bench_pts and path.split("/")[-1].lower() != "nifty":
                rob = ms_robustness.halves_check(pts, bench_pts)
            if h["score"] is not None:
                n_scored += 1
            series_out.append({
                "path": path or "(root)",
                "kind": kind,
                "health": h,
                "robustness": {"halves": rob} if rob else None,
            })

        if series_out:
            out["reports"][name] = {"series": series_out}

        # ---- taxes: every 'trades' array in the file (skip USD QQQ) ----
        def tax_arrays(o, path=""):
            found = []
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "trades" and isinstance(v, list) and v:
                        found.append((path or "trades", v))
                    else:
                        found += tax_arrays(v, f"{path}/{k}" if path else k)
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    found += tax_arrays(v, f"{path}/{i}")
            return found

        for path, trades in tax_arrays(data):
            if "QQQ" in path:
                out["skipped_tax"].append({"file": name, "path": path,
                                           "reason": "USD-denominated (Nasdaq) trades - not an Indian tax case"})
                continue
            norm, note = scale_trades_for_tax(trades, data)
            if not norm:
                continue
            rep = ms_tax.capital_gains_report(norm, fmv_by_ticker=fmv)
            if note:
                rep["notes"].append(note)
            rep["trades_path"] = path
            rep["n_trades_closed"] = len(norm)
            out["taxes"].setdefault(name, []).append({"label": path, **rep})
            print(f"  tax {name} [{path}]: {rep['n_closed_trades']} closed trades, "
                  f"total tax Rs {rep['totals']['total_tax']:,.0f}")

    from datetime import datetime
    out["generated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Strictly-valid JSON only: Python happily writes bare NaN/Infinity, but
    # the webapp's JSON.parse rejects them (caught by a live smoke test on
    # results_find_etf.json's monthly-std checks). allow_nan=False makes any
    # future leak fail loudly here instead of silently in the browser.
    def _safe(o):
        if isinstance(o, float):
            return o if (o == o and abs(o) != float("inf")) else None
        if isinstance(o, dict):
            return {k: _safe(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_safe(v) for v in o]
        return o

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(_safe(out), f, indent=1, allow_nan=False)

    size_kb = os.path.getsize(OUT) / 1024
    print(f"\nms_lab.json written: {len(out['reports'])} files, {n_series} series "
          f"({n_scored} scored), {len(out['taxes'])} tax reports, {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
