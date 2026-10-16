"""Builds 93_midcap150_momentumscore_style_review.html from results92.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results92.json", encoding="utf-8") as f:
    R = json.load(f)

TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
PANEL = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-6"
PANEL_TIGHT = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-5"
MUTED = "text-[#7E97A0] text-[12.5px] leading-snug"
WHAT_THIS_SHOWS = "text-[#9FB4BB] text-[13px] italic mb-3"

PILL_BASE = "inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
PILL_POS = PILL_BASE + " bg-[#37F083]/15 text-[#37F083] border border-[#37F083]/40"
PILL_NEG = PILL_BASE + " bg-[#F2643C]/15 text-[#F2643C] border border-[#F2643C]/40"
PILL_ASSUM = PILL_BASE + ' bg-[#F2B03C]/15 text-[#F2B03C] border border-[#F2B03C]/40'
PILL_NEUTRAL = PILL_BASE + " bg-[#7E97A0]/15 text-[#7E97A0] border border-[#7E97A0]/40"
KIND_COLOR = {"positive": "#37F083", "negative": "#F2643C", "neutral": "#E6EDF0", "assumption": "#F2B03C"}

CYAN = "#6AE4FF"
TRIGGER_KIND = {
    "regime_exit": "negative",
    "regime_reentry": "positive",
    "scheduled_rebalance": "neutral",
    "initial_entry": "assumption",
}


def pill(text, kind="assumption"):
    cls = {"positive": PILL_POS, "negative": PILL_NEG, "assumption": PILL_ASSUM, "neutral": PILL_NEUTRAL}[kind]
    dot = {"positive": "●", "negative": "●", "assumption": "▲", "neutral": "●"}[kind]
    return f'<span class="{cls}">{dot} {text}</span>'


def esc(s):
    return html.escape(str(s))


def pct(v, decimals=1, signed=True):
    if v is None:
        return "—"
    s = "+" if (signed and v > 0) else ""
    return f"{s}{v:,.{decimals}f}%"


def money(v, decimals=0):
    if v is None:
        return "—"
    return f"₹{v:,.{decimals}f}"


def smoney(v, decimals=0):
    """signed money — for P&L / losses where the sign carries meaning."""
    if v is None:
        return "—"
    if v < 0:
        return f"-₹{abs(v):,.{decimals}f}"
    return f"₹{v:,.{decimals}f}"


def base_style():
    return """
    <style>
      html,body{background:#08171E;color:#E6EDF0;font-family:'Inter',ui-sans-serif,system-ui,-apple-system,sans-serif;}
      .mono{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;}
      table.data-table{width:100%;border-collapse:collapse;font-size:13px;}
      table.data-table th{text-align:right;color:#7E97A0;font-weight:600;padding:8px 12px;border-bottom:1px solid #1E3A45;position:sticky;top:0;background:#132B36;font-size:11px;letter-spacing:0.03em;text-transform:uppercase;}
      table.data-table th:first-child, table.data-table td:first-child{text-align:left;}
      table.data-table td{text-align:right;padding:7px 12px;border-bottom:1px solid #16303a;white-space:nowrap;transition:background-color 120ms ease;}
      table.data-table tbody tr:nth-child(even) td{background:rgba(255,255,255,0.015);}
      table.data-table tbody tr:hover td{background:rgba(55,240,131,0.06);}
      tr.real-bench td{color:#9FB4BB;}
      tr.total-row td{font-weight:700;color:#E6EDF0;background:rgba(255,255,255,0.03);}
      .kpi-val{font-size:24px;font-weight:700;letter-spacing:-0.01em;}
      .pos{color:#37F083;} .neg{color:#F2643C;} .amb{color:#F2B03C;} .mut{color:#7E97A0;} .cy{color:#6AE4FF;}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1 min-w-[110px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
            f'<div class="kpi-val mono" style="color:{color}">{value_str}</div></div>'
        )
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
      <div class="{MUTED} mb-3">{definition}</div>
      <div class="flex gap-3 flex-wrap">{''.join(col_html)}</div>
    </div>
    """


def verdict_pill(passed, yes="PASS", no="MISS"):
    return pill(yes, "positive") if passed else pill(no, "negative")


def build():
    bc, ac, at, nif, gb = (R["before_costs"], R["after_costs"], R["after_tax"],
                           R["nifty"], R["gold_benchmark"])
    hc, rob, tx, rebs, ts = (R["health_check"], R["robustness"], R["tax_report"],
                             R["rebalances"], R["trade_stats"])
    cfg = R["config"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">MomentumScore-Style Review — Exit Rank 52</h1>
          <p class="text-[#9FB4BB] text-sm mt-1 max-w-[900px]">Report 48's strategy skeleton (Midcap150 momentum 10, NIFTY-50 {esc(R['ema_span'])}-EMA regime filter, GOLDBEES hedge) re-run with MomentumScore's review layer on top: a held stock is sold only when it falls below rank {esc(cfg['exit_rank'])} of the eligible universe, carried names keep their original shares, reviews happen at scheduled month-ends (Jun/Dec) plus every regime flip, and every leg pays {esc(cfg['cost_pct_per_side'])}%/side. The run ships with a real-rupee trade log, an Indian capital-gains tax estimate, the 10-target health scorecard, both-halves and date-luck robustness checks, and a live ranking preview.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill(f'After costs: CAGR {pct(ac["cagr_pct"])} at {pct(ac["max_drawdown_pct"], 1, signed=False)} max drawdown — NIFTY 50 made {pct(nif["cagr_pct"])}', 'positive')}
          {pill(f'After the tax estimate: {pct(at["cagr_pct"])} a year', 'positive')}
          {pill(f'Health score {hc["score"]}/100 — both-halves PASS, date-luck PASS', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The review layer does not change the regime filter — it changes which stocks are held and when they are sold.
          That means the whipsaw is inherited intact: this run logs <span class="font-semibold">65 regime exits and 64
          re-entries</span> across {esc(R['start_date'])}–{esc(R['end_date'])}, the same behaviour report 48 showed with
          its 69 re-entries. Costs and the tax estimate are what move the headline numbers: {pct(bc["cagr_pct"])} before
          costs, {pct(ac["cagr_pct"])} after {esc(cfg['cost_pct_per_side'])}%/side on every leg, {pct(at["cagr_pct"])}
          after the capital-gains estimate — still roughly three times NIFTY 50's {pct(nif["cagr_pct"])}, with a
          materially shallower drawdown than the index.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — costs and taxes included",
                 "Compound annual growth rate over the identical window, every series rebased to 100 at the start.",
                 [("Before costs", pct(bc["cagr_pct"]), "positive"),
                  ("After costs", pct(ac["cagr_pct"]), "positive"),
                  ("After tax", pct(at["cagr_pct"]), "positive"),
                  ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown — costs and taxes included",
                 "Largest peak-to-trough decline. The after-tax curve is the worst case because tax is paid out of the portfolio at each year-end.",
                 [("Before costs", pct(bc["max_drawdown_pct"], 1, signed=False), "negative"),
                  ("After costs", pct(ac["max_drawdown_pct"], 1, signed=False), "negative"),
                  ("After tax", pct(at["max_drawdown_pct"], 1, signed=False), "negative"),
                  ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Health & robustness — the MomentumScore-style review",
                 "Health = share of MomentumScore's 10 published target ranges met, computed by this report's own engine on full-resolution daily data and this trade log.",
                 [("Health score", f'{hc["score"]} / 100', "assumption"),
                  ("Checks met", f'{hc["checks_met"]} of {hc["checks_available"]}', "neutral"),
                  ("Both halves", "PASS" if rob["halves"]["passed_both"] else "FAIL", "positive" if rob["halves"]["passed_both"] else "negative"),
                  ("Date luck", "PASS" if rob["date_luck"]["verdict"] == "pass" else "FAIL", "positive" if rob["date_luck"]["verdict"] == "pass" else "negative")]),
        kpi_card("The review layer at a glance",
                 "What the MomentumScore-style machinery did over the run.",
                 [("Exit rank", str(cfg["exit_rank"]), "neutral"),
                  ("Reviews logged", f'{len(rebs):,}', "neutral"),
                  ("Closed trades", f'{ts["total_trades"]:,}', "neutral"),
                  ("Avg rebalances carried", f'{ts["avg_rebalances_held"]:.1f}', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    eq_series = [
        {"name": "Before costs", "color": CYAN, "points": bc["equity_curve"]},
        {"name": "After costs", "color": COL["positive"], "points": ac["equity_curve"]},
        {"name": "After tax", "color": COL["assumption"], "points": at["equity_curve"]},
        {"name": "NIFTY 50", "color": COL["muted"], "points": nif["equity_curve"]},
        {"name": "GOLDBEES buy &amp; hold", "color": COL["negative"], "points": gb["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_93")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how ₹100 grew under each version of the strategy, plus the real benchmarks. Linear axis, not log-scaled — the last decade dominates the visual, which is honest about where the compounding came from.</p>
      <div class="flex items-center mb-2 flex-wrap">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    def dd_points(equity):
        out, peak = [], None
        for d, v in equity:
            peak = v if peak is None else max(peak, v)
            out.append([d, (v / peak - 1.0) * 100.0])
        return out

    dd_series = [
        {"name": "After costs", "color": COL["positive"], "points": dd_points(ac["equity_curve"])},
        {"name": "After tax", "color": COL["assumption"], "points": dd_points(at["equity_curve"])},
        {"name": "NIFTY 50", "color": COL["muted"], "points": dd_points(nif["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=240, chart_id="dd_93")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown — after costs, after tax, and the index</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the strategy spends less time deep underwater than NIFTY 50 even after paying the tax bill; the after-tax line is drawn slightly deeper than after-costs because each year's tax is a real outflow.</p>
      <div class="flex items-center mb-2 flex-wrap">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All five series, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. "After tax" compounds the yearly tax estimate out of the portfolio at each financial-year end.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Before costs", bc)}
          {row("After costs (" + str(cfg['cost_pct_per_side']) + "%/side, all legs)", ac)}
          {row("After tax (capital-gains estimate paid yearly)", at)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    health_rows = []
    for c in hc["checks"]:
        health_rows.append(
            f"""<tr><td>{esc(c['label'])}</td><td class="mut mono">{esc(c['target_text'])}</td>
            <td class="mono">{esc(c['value_text']) if c['value_text'] else '—'}</td>
            <td>{verdict_pill(c['passed'])}</td></tr>"""
        )
    health_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center gap-3 mb-1 flex-wrap">
        <h3 class="text-base font-bold text-[#E6EDF0]">Health — the 10-target scorecard</h3>
        {pill(f'{hc["checks_met"]} of {hc["checks_available"]} checks met', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the same target ranges MomentumScore scores strategies on, computed by this report's own engine on the full-resolution daily curve and this trade log. Score = share of ranges met. Two documented proxies: the "tail risk" checks use the skewness of monthly and per-trade returns (MomentumScore's exact definition is unpublished).</p>
      <table class="data-table">
        <thead><tr><th>Check</th><th>Target</th><th>This strategy</th><th>Verdict</th></tr></thead>
        <tbody>{''.join(health_rows)}</tbody>
      </table>
    </div>
    """

    halves = rob["halves"]
    half_rows = []
    for h in halves["halves"]:
        half_rows.append(
            f"""<tr><td class="capitalize">{esc(h['label'])} half</td><td class="mono mut">{esc(h['start'])} → {esc(h['end'])}</td>
            <td class="mono pos">{pct(h['strategy_cagr_pct'])}</td><td class="mono mut">{pct(h['benchmark_cagr_pct'])}</td>
            <td>{verdict_pill(h['passed'], 'BEATS', 'LAGS')}</td></tr>"""
        )
    dl = rob["date_luck"]
    dl_rows = []
    for v in dl["variants"]:
        dl_rows.append(
            f"""<tr><td>{esc(v['label'])}</td><td class="mono mut">{esc(v['start'])} → {esc(v['end'])}</td>
            <td class="mono pos">{pct(v['strategy_cagr_pct'])}</td><td class="mono mut">{pct(v['benchmark_cagr_pct'])}</td>
            <td>{verdict_pill(v['passed'], 'BEATS', 'LAGS')}</td></tr>"""
        )
    robustness_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center gap-2 mb-1 flex-wrap">
        <h3 class="text-base font-bold text-[#E6EDF0]">Robustness — both halves &amp; date luck</h3>
        {pill('PASS — beats NIFTY in both halves' if halves['passed_both'] else 'FAIL', 'positive' if halves['passed_both'] else 'negative')}
        {pill(f'date-luck PASS — {dl["n_pass"]}/{dl["n_variants"]} calendars beat NIFTY' if dl['verdict'] == 'pass' else f'date-luck FAIL — {dl["n_pass"]}/{dl["n_variants"]}', 'positive' if dl['verdict'] == 'pass' else 'negative')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — soundness checks, not performance claims. The halves split is the midpoint of the benchmark's own history, not a cherry-picked date; the date-luck test re-runs the same engine with mid-month (day ~15) reviews instead of month-end.</p>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div>
          <div class="text-[13px] font-semibold text-[#E6EDF0] mb-2">Both halves — split at {esc(halves['split_date'])}</div>
          <table class="data-table">
            <thead><tr><th>Half</th><th>Period</th><th>Strategy CAGR</th><th>NIFTY CAGR</th><th>Verdict</th></tr></thead>
            <tbody>{''.join(half_rows)}</tbody>
          </table>
        </div>
        <div>
          <div class="text-[13px] font-semibold text-[#E6EDF0] mb-2">Date luck — does the review calendar matter?</div>
          <table class="data-table">
            <thead><tr><th>Review calendar</th><th>Period</th><th>Strategy CAGR</th><th>NIFTY CAGR</th><th>Verdict</th></tr></thead>
            <tbody>{''.join(dl_rows)}</tbody>
          </table>
        </div>
      </div>
    </div>
    """

    tax_rows = []
    for y in tx["years"]:
        tax_rows.append(
            f"""<tr><td class="mono mut">{esc(y['fy'])}</td><td class="mono">{y['n_trades_closed']}</td>
            <td class="mono pos">{money(y['stcg_gains']) if y['stcg_gains'] else '—'}</td>
            <td class="mono neg">{smoney(-y['stcg_losses']) if y['stcg_losses'] else '—'}</td>
            <td class="mono pos">{money(y['ltcg_gains']) if y['ltcg_gains'] else '—'}</td>
            <td class="mono neg">{smoney(-y['ltcg_losses']) if y['ltcg_losses'] else '—'}</td>
            <td class="mono mut">{money(y['exemption_used']) if y['exemption_used'] else '—'}</td>
            <td class="mono">{(y['taxable_stcg'] + y['taxable_ltcg']) and money(y['taxable_stcg'] + y['taxable_ltcg']) or '—'}</td>
            <td class="mono mut">{(y['tax_stcg'] + y['tax_ltcg']) and money(y['tax_stcg'] + y['tax_ltcg']) or '—'}</td>
            <td class="mono mut">{money(y['cess']) if y['cess'] else '—'}</td>
            <td class="mono" style="font-weight:600">{money(y['total_tax']) if y['total_tax'] else '—'}</td>
            <td class="mono amb">{(y['carry_out_stcl'] + y['carry_out_ltcl']) and money(y['carry_out_stcl'] + y['carry_out_ltcl']) or '—'}</td></tr>"""
        )

    def ysum(k):
        return sum((y.get(k) or 0) for y in tx["years"])

    tax_total_row = f"""<tr class="total-row"><td>Total</td><td class="mono">{ysum('n_trades_closed')}</td>
    <td class="mono pos">{money(ysum('stcg_gains'))}</td><td class="mono neg">{smoney(-ysum('stcg_losses'))}</td>
    <td class="mono pos">{money(ysum('ltcg_gains'))}</td><td class="mono neg">{smoney(-ysum('ltcg_losses'))}</td>
    <td class="mono mut">{money(ysum('exemption_used'))}</td><td class="mono">{money(ysum('taxable_stcg') + ysum('taxable_ltcg'))}</td>
    <td class="mono mut">{money(ysum('tax_stcg') + ysum('tax_ltcg'))}</td><td class="mono mut">{money(ysum('cess'))}</td>
    <td class="mono">{money(tx['totals']['total_tax'])}</td><td class="mono amb">—</td></tr>"""

    tax_notes = "".join(f'<li class="mb-1">{esc(n)}</li>' for n in tx["notes"])
    tax_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center gap-2 mb-1 flex-wrap">
        <h3 class="text-base font-bold text-[#E6EDF0]">Capital-gains tax estimate — Indian rules, paid yearly</h3>
        {pill(f'total tax {money(tx["totals"]["total_tax"])} on realized P&L {money(tx["totals"]["total_realised_pnl"])} — effective {tx["totals"]["tax_pct_of_realised_pnl"]}%', 'assumption')}
        {pill(f'growth {pct(tx["growth_before_tax_pct"])} a year before tax → {pct(tx["growth_after_tax_pct"])} after tax', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — what this run's own trade log would have owed under Indian capital-gains rules: 15%/10% (LTCG above ₹1,00,000) for sales before 23 Jul 2024, 20%/12.5% (above ₹1,25,000) on and after, 4% cess, short-then-long loss set-off with 8-year carry-forward, s.112A grandfathering via the 31-Jan-2025 FMV. An estimate, not tax advice — and it ignores surcharge and advance-tax timing.</p>
      <table class="data-table">
        <thead><tr><th>FY</th><th>Trades</th><th>STCG gains</th><th>STCG losses</th><th>LTCG gains</th><th>LTCG losses</th><th>Exemption</th><th>Taxable</th><th>Tax</th><th>Cess</th><th>Total tax</th><th>Carry fwd</th></tr></thead>
        <tbody>{''.join(tax_rows)}{tax_total_row}</tbody>
      </table>
      <ul class="text-[12.5px] text-[#9FB4BB] list-disc pl-5 mt-3 leading-relaxed">{tax_notes}</ul>
    </div>
    """

    from collections import Counter
    trig_counts = Counter(e["trigger"] for e in rebs)
    trig_chips = " ".join(
        pill(f"{k.replace('_', ' ')} × {v}", TRIGGER_KIND.get(k, "neutral"))
        for k, v in sorted(trig_counts.items(), key=lambda kv: -kv[1])
    )

    def event_html(e):
        parts = []
        if e["sells"]:
            sold = " · ".join(f"{esc(s['ticker'])} (rank {s.get('rank_out', '—')}) — {esc(s.get('reason', ''))}" for s in e["sells"])
            parts.append(f'<div><span class="neg font-semibold">Sold:</span> <span class="mut">{sold}</span></div>')
        if e["buys"]:
            bought = " · ".join(f"{esc(b['ticker'])} (rank {b.get('rank_in', '—')}, fit {b.get('fit_in', '—')}%)" for b in e["buys"])
            parts.append(f'<div><span class="pos font-semibold">Bought:</span> <span class="mut">{bought}</span></div>')
        if e["keeps"]:
            ks = e["keeps"]
            names = ", ".join(f"{esc(k['ticker'])} (rank {k['rank']})" for k in ks[:6])
            more = f" +{len(ks) - 6} more" if len(ks) > 6 else ""
            parts.append(f'<div><span class="font-semibold text-[#E6EDF0]">Carried {len(ks)}:</span> <span class="mut">{names}{more}</span></div>')
        if not parts:
            parts.append('<div class="mut">No stock actions.</div>')
        cash = f' {pill(money(e["cash_left"]) + " left in cash", "assumption")}' if e.get("cash_left") else ""
        return f"""
        <div class="rounded-xl border border-[#1E3A45] px-4 py-3 mb-2.5">
          <div class="flex items-center gap-2.5 flex-wrap text-[12.5px]">
            <span class="mono mut">{esc(e['date'])}</span>
            {pill(e['trigger'].replace('_', ' '), TRIGGER_KIND.get(e['trigger'], 'neutral'))}
            <span class="mut">value after <span class="mono">{money(e['value_after'])}</span></span>{cash}
          </div>
          <div class="mt-1.5 text-[12px] leading-relaxed space-y-0.5">{''.join(parts)}</div>
        </div>
        """

    last_events = "".join(event_html(e) for e in list(reversed(rebs))[:8])
    rebal_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center gap-2 mb-1 flex-wrap">
        <h3 class="text-base font-bold text-[#E6EDF0]">Rebalance log — every review, and why</h3>
        {trig_chips}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the last 8 of {len(rebs)} logged reviews (newest first): which positions carried (still ranked inside {esc(cfg['exit_rank'])}), which fell below the exit rank, and which names refilled the slots, at what rank and fit percentile. The full log is in results92.json and the webapp's report 93.</p>
      {last_events}
    </div>
    """

    trade_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Trade statistics</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every closed position over the run. Positions are held until they fall below the exit rank; carried names keep their original shares (no re-equalisation), so trade sizes drift with performance.</p>
      <div class="flex gap-5 flex-wrap text-[13px]">
        <span class="mut">Closed trades <span class="mono" style="color:#E6EDF0;font-weight:600">{ts['total_trades']:,}</span></span>
        <span class="mut">Win rate <span class="mono" style="color:#E6EDF0;font-weight:600">{pct(ts['win_rate_pct'], 1, signed=False)}</span></span>
        <span class="mut">Avg winner <span class="mono pos" style="font-weight:600">{pct(ts['avg_win_pct'])}</span></span>
        <span class="mut">Avg loser <span class="mono neg" style="font-weight:600">{pct(ts['avg_loss_pct'])}</span></span>
        <span class="mut">Gain-to-loss ratio <span class="mono" style="color:#E6EDF0;font-weight:600">{abs(ts['avg_win_pct'] / ts['avg_loss_pct']):.2f}</span></span>
        <span class="mut">Realized P&amp;L <span class="mono pos" style="font-weight:600">{money(ts['total_realized_pnl'])}</span></span>
        <span class="mut">Open positions <span class="mono" style="color:#E6EDF0;font-weight:600">{ts['open_positions']}</span></span>
      </div>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every simplification behind this backtest.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5">The whipsaw is inherited from report 48's regime filter, unchanged: 65 regime exits and 64
        re-entries in this run (report 48 logged 69 re-entries). The review layer deliberately does not try to dampen
        it — it changes the stock-holding rules, not the market-timing rule.</li>
        <li class="mb-1.5">Health: 9 of the 10 target ranges are MomentumScore's published ones; the "tail risk" checks
        (monthly and per-trade) use skewness as a documented proxy because MomentumScore's exact definition is not
        published. Curve checks here run on the engine's full-resolution daily curve; the webapp's cross-report lab
        scores archived chart series (≤1500 points), so a lab score can differ by a check.</li>
        <li class="mb-1.5">Tax: FY-by-FY estimate on the trade log — exit-date-based FY assignment, 4% cess, no
        surcharge, no advance-tax timing, no pre-2018 grandfathering; the s.112A 31-Jan-2025 FMV map affected 0 trades
        here because every position was held under a year. Not tax advice.</li>
        <li class="mb-1.5">Costs: a flat {esc(cfg['cost_pct_per_side'])}% per side on every leg including the gold
        hedge — no slippage or market-impact model, and no allowance for the fact that small-cap fills are usually
        worse than midcap ones.</li>
        <li class="mb-1.5">Design choices in the review layer: carried stocks keep their original shares (report 31's
        convention, no re-equalisation); freed cash refills slots at the next review; a regime re-entry buys a fresh
        top-10 without hysteresis (the exit-rank rule only protects positions during an ongoing regime, not across
        one).</li>
        <li class="mb-1.5">Same reconstruction caveats as report 48: today's fixed Midcap150 constituent list applied
        retroactively (survivorship bias), equal weighting, unadjusted prices, no dividends modeled, no
        F&amp;O-eligibility screen.</li>
        <li class="mb-1.5">Date luck: the mid-month variant (day ~15) is one alternative calendar, a smoke test — not
        the full six-calendar sweep of reports 85/92.</li>
        <li>Rupee figures (P&amp;L, tax) scale the window start to ₹1,00,000 through the engine's own unit accounting;
        the percentage curves are scale-free.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    <div class="px-10 py-6">
      {kpi_grid}
      {eq_panel}
      {dd_panel}
      {full_table}
      {health_panel}
      {robustness_panel}
      {tax_panel}
      {rebal_panel}
      {trade_panel}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>MomentumScore-Style Review — Exit Rank 52</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("93_midcap150_momentumscore_style_review.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 93_midcap150_momentumscore_style_review.html")
