"""Capital-gains estimate for a trade log — the MomentumScore "Tax" tab,
ported: "An optional estimate. Every other number in the report is
before tax." Their reference card shows, for ₹1L → ₹4.43L over 2013-2026:
"Growth a year 10.4% after tax, vs 11.7% before tax · Tax paid ₹48,975 on
gains booked over the period, cess included."

Rules implemented (Indian equity delivery, as of FY 2026):

  * Holding period: > 365 days = long-term, else short-term.
  * Rate switch on 23 Jul 2024 — sales BEFORE that date: STCG 15%,
    LTCG 10% above a ₹1,00,000 exemption; sales ON/AFTER: STCG 20%,
    LTCG 12.5% above ₹1,25,000.
  * Health & Education cess 4% on the total tax.
  * s.112A grandfathering (Finance (No.2) Act 2024): for a LONG-TERM
    sale on/after 23 Jul 2024 of shares acquired BEFORE it, the cost is
    the higher of (a) actual cost, (b) the LOWER of the 31-Jan-2025 FMV
    and the actual sale price. Caller supplies fmv_by_ticker (the
    report-93 engine reads it straight off its own price data).
  * Set-off: short-term losses offset short-term gains first, then
    long-term gains; long-term losses only ever offset long-term gains.
    Unused losses carry forward up to 8 financial years.
  * Financial years run April-March.

Not modelled (disclosed in the returned notes): the pre-2018 31-Jan-2018
grandfathering for very old holdings (none of this repo's tradelog
reports have any), surcharge (incomes below ₹50L — all realistic cases
here), stamp duty/STT (already inside the backtest's cost model), and
advance-tax timing. This is an estimate for comparison, not filing.
"""
from __future__ import annotations

from datetime import date, timedelta

CESS = 0.04
RATE_SWITCH = date(2024, 7, 23)
OLD = {"stcg": 0.15, "ltcg": 0.10, "ltcg_exempt": 100_000.0}
NEW = {"stcg": 0.20, "ltcg": 0.125, "ltcg_exempt": 125_000.0}


def _parse(s):
    y, m, d = str(s)[:10].split("-")
    return date(int(y), int(m), int(d))


def fy_label(d):
    """Indian financial year label for a date: 2025-04-01 -> '2025-26'."""
    if d.month >= 4:
        return f"{d.year}-{str(d.year + 1)[2:]}"
    return f"{d.year - 1}-{str(d.year)[2:]}"


def rates_for(sale_date):
    return NEW if sale_date >= RATE_SWITCH else OLD


def normalize_trades(trades, alloc_scale=None):
    """Coerce results*.json trade dicts into a common shape:
    {ticker, entry_date, exit_date, entry_price, exit_price, qty, status}.

    Handles this repo's three schemas: engine trades with real
    qty/shares; per-rebalance alloc trades (report 26/31) where qty is
    derived as alloc * alloc_scale / entry_price; and pct-return-only
    rows (skipped - they cannot yield a rupee gain)."""
    out = []
    for t in trades:
        if t.get("status") == "open":
            continue
        entry = t.get("entry_date")
        exit_ = t.get("exit_date")
        ep, xp = t.get("entry_price"), t.get("exit_price")
        if not (entry and exit_ and ep and xp):
            continue
        qty = t.get("qty", t.get("shares"))
        if qty is None and t.get("alloc") is not None and alloc_scale:
            qty = t["alloc"] * alloc_scale / ep
        if qty is None:
            continue
        out.append({"ticker": str(t.get("ticker", "?")).replace(".NS", ""),
                    "entry_date": str(entry)[:10], "exit_date": str(exit_)[:10],
                    "entry_price": float(ep), "exit_price": float(xp), "qty": float(qty)})
    return out


def capital_gains_report(trades, fmv_by_ticker=None, fmv_date="2025-01-31"):
    """trades: normalized dicts (see normalize_trades) — one per CLOSED
    position (an open position books no gain yet).

    fmv_by_ticker: {TICKER: price on fmv_date} for s.112A grandfathering;
    pass None to fall back to actual cost (conservative for winners).
    """
    fmv_date_d = _parse(fmv_date)
    events = []
    for t in trades:
        entry_d, exit_d = _parse(t["entry_date"]), _parse(t["exit_date"])
        days = (exit_d - entry_d).days
        long_term = days > 365
        rates = rates_for(exit_d)
        buy_value = t["entry_price"] * t["qty"]
        sell_value = t["exit_price"] * t["qty"]
        cost_price = t["entry_price"]
        grandfathered = False
        if long_term and entry_d < RATE_SWITCH <= exit_d and fmv_by_ticker:
            fmv = fmv_by_ticker.get(t["ticker"])
            if fmv and exit_d >= fmv_date_d and exit_d >= RATE_SWITCH:
                # deemed cost = max(actual, min(FMV on 31-Jan-2025, sale price))
                cost_price = max(t["entry_price"], min(float(fmv), t["exit_price"]))
                grandfathered = cost_price != t["entry_price"]
        gain = (t["exit_price"] - cost_price) * t["qty"]
        events.append({
            "ticker": t["ticker"], "entry_date": t["entry_date"], "exit_date": t["exit_date"],
            "holding_days": days, "kind": "LTCG" if long_term else "STCG",
            "buy_value": buy_value, "sell_value": sell_value, "gain": gain,
            "grandfathered": grandfathered, "fy": fy_label(exit_d),
        })

    # group by FY, process chronologically with 8-year loss carry
    by_fy = {}
    for e in events:
        by_fy.setdefault(e["fy"], []).append(e)
    order = sorted(by_fy.keys())

    losses = []  # {"kind": "STCL"|"LTCL", "amount": x, "origin_idx": i}
    years = []
    for idx, fy in enumerate(order):
        rows = by_fy[fy]
        stcg = sum(r["gain"] for r in rows if r["kind"] == "STCG" and r["gain"] > 0)
        stcl = -sum(r["gain"] for r in rows if r["kind"] == "STCG" and r["gain"] < 0)
        ltcg = sum(r["gain"] for r in rows if r["kind"] == "LTCG" and r["gain"] > 0)
        ltcl = -sum(r["gain"] for r in rows if r["kind"] == "LTCG" and r["gain"] < 0)

        carried_in_stcl = sum(l["amount"] for l in losses if l["kind"] == "STCL")
        carried_in_ltcl = sum(l["amount"] for l in losses if l["kind"] == "LTCL")

        # current-year set-off
        stcg_net = stcg - stcl
        ltcg_net = ltcg - ltcl
        new_carry_stcl = 0.0
        if stcg_net < 0:
            new_carry_stcl = -stcg_net
            stcg_net = 0.0
            used = min(new_carry_stcl, ltcg_net)
            ltcg_net -= used
            new_carry_stcl -= used
        new_carry_ltcl = 0.0
        if ltcg_net < 0:
            new_carry_ltcl = -ltcg_net
            ltcg_net = 0.0

        # brought-forward set-off (only vintage within 8 years)
        alive = [l for l in losses if idx - l["origin_idx"] <= 8]
        for l in alive:
            if l["amount"] <= 0:
                continue
            if l["kind"] == "STCL":
                use = min(l["amount"], stcg_net)
                stcg_net -= use
                l["amount"] -= use
                if l["amount"] > 0:
                    use = min(l["amount"], ltcg_net)
                    ltcg_net -= use
                    l["amount"] -= use
            else:
                use = min(l["amount"], ltcg_net)
                ltcg_net -= use
                l["amount"] -= use
        if new_carry_stcl > 0:
            losses.append({"kind": "STCL", "amount": new_carry_stcl, "origin_idx": idx})
        if new_carry_ltcl > 0:
            losses.append({"kind": "LTCL", "amount": new_carry_ltcl, "origin_idx": idx})

        # rates: FY may span the 23-Jul-2024 switch; use the LATER sale's
        # rate set for the year if any sale is on/after the switch (the
        # engine's semi-annual cadence makes a mixed-FY case rare, and the
        # 2024-25 FY is the only one that can ever be mixed).
        rates = max((rates_for(_parse(r["exit_date"])) for r in rows), key=lambda r: r["stcg"])
        exempt = rates["ltcg_exempt"]
        taxable_stcg = stcg_net
        taxable_ltcg = max(0.0, ltcg_net - exempt)
        tax_stcg = taxable_stcg * rates["stcg"]
        tax_ltcg = taxable_ltcg * rates["ltcg"]
        cess = (tax_stcg + tax_ltcg) * CESS
        total_tax = tax_stcg + tax_ltcg + cess

        years.append({
            "fy": fy,
            "n_trades_closed": len(rows),
            "stcg_gains": round(stcg, 2), "stcg_losses": round(stcl, 2),
            "ltcg_gains": round(ltcg, 2), "ltcg_losses": round(ltcl, 2),
            "carried_in_stcl": round(carried_in_stcl, 2), "carried_in_ltcl": round(carried_in_ltcl, 2),
            "taxable_stcg": round(taxable_stcg, 2), "taxable_ltcg": round(taxable_ltcg, 2),
            "exemption_used": round(min(exempt, max(0.0, ltcg_net)), 2),
            "tax_stcg": round(tax_stcg, 2), "tax_ltcg": round(tax_ltcg, 2),
            "cess": round(cess, 2), "total_tax": round(total_tax, 2),
            "realised_pnl": round(sum(r["gain"] for r in rows), 2),
            "carry_out_stcl": round(sum(l["amount"] for l in losses if l["kind"] == "STCL" and idx - l["origin_idx"] < 8), 2),
            "carry_out_ltcl": round(sum(l["amount"] for l in losses if l["kind"] == "LTCL" and idx - l["origin_idx"] < 8), 2),
            "stcg_rate_pct": rates["stcg"] * 100, "ltcg_rate_pct": rates["ltcg"] * 100,
        })

    total_tax = sum(y["total_tax"] for y in years)
    total_pnl = sum(y["realised_pnl"] for y in years)
    n_grandf = sum(1 for e in events if e["grandfathered"])
    notes = [
        "Rates: 15%/10% (LTCG above Rs 1,00,000) for sales before 23 Jul 2024; "
        "20%/12.5% (LTCG above Rs 1,25,000) on/after. Cess 4% included.",
        "Short-term losses offset short-term gains first, then long-term gains; "
        "long-term losses only offset long-term gains; unused losses carry forward 8 years.",
        "Not modelled: pre-2018 grandfathering, surcharge, advance-tax timing.",
    ]
    if fmv_by_ticker:
        notes.append(f"s.112A grandfathering applied via the {fmv_date} FMV map "
                     f"({n_grandf} trade(s) affected); otherwise actual cost is used.")
    else:
        notes.append("No FMV map supplied - grandfather-eligible trades are taxed on actual cost "
                     "(overstates tax when the position had unrealised gains by 31 Jan 2025).")

    return {
        "n_closed_trades": len(events),
        "first_entry": min((e["entry_date"] for e in events), default=None),
        "last_exit": max((e["exit_date"] for e in events), default=None),
        "years": years,
        "totals": {
            "total_tax": round(total_tax, 2),
            "total_realised_pnl": round(total_pnl, 2),
            "tax_pct_of_realised_pnl": round(total_tax / total_pnl * 100, 1) if total_pnl > 0 else None,
            "n_grandfathered_trades": n_grandf,
        },
        "notes": notes,
    }


def after_tax_curve(points, tax_by_fy):
    """Fold each FY's total tax into the equity curve at that FY's last
    data point (tax presumed paid then, out of the portfolio — the same
    simplification MomentumScore's "growth a year after tax" headline
    implies). points: [[date, value], ...]; tax_by_fy: {fy_label: rupees}.

    Returns (adjusted_points, taxes_applied) with taxes_applied =
    [{fy, date, tax}]. Values before the first taxed FY-end are
    unchanged; each tax is deducted proportionally so the curve stays
    continuous-through-event, exactly like a real end-of-year tax bill."""
    if not tax_by_fy:
        return [list(p) for p in points], []
    out = []
    scale = 1.0
    applied = []
    for i, (d, v) in enumerate(points):
        out.append([d, v * scale])
        fy = fy_label(_parse(d))
        if i + 1 < len(points):
            next_fy = fy_label(_parse(points[i + 1][0]))
        else:
            next_fy = None
        if next_fy and next_fy != fy and fy in tax_by_fy and tax_by_fy[fy] > 0:
            value_now = v * scale
            if value_now > 0:
                scale *= max(0.0, 1.0 - tax_by_fy[fy] / value_now)
                applied.append({"fy": fy, "date": d, "tax": round(tax_by_fy[fy], 2)})
    return out, applied
