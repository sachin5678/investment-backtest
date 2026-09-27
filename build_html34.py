"""Builds 34_midcap_momentum10_relative_momentum.html from results33.json.
Same self-contained contract, smooth Catmull-Rom charts, dark palette as
every other report."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results33.json") as f:
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
ACCENT_2 = "#8B5CF6"


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


def win_loss_kind(v):
    if v is None:
        return "neutral"
    return "positive" if v > 0 else ("negative" if v < 0 else "neutral")


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
      .kpi-val{font-size:24px;font-weight:700;letter-spacing:-0.01em;}
      tr.real-bench td{color:#9FB4BB;}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1 min-w-[120px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
            f'<div class="kpi-val mono" style="color:{color}">{value_str}</div></div>'
        )
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
      <div class="{MUTED} mb-3">{definition}</div>
      <div class="flex gap-4 flex-wrap">{''.join(col_html)}</div>
    </div>
    """


def build():
    orig, rel, nif = R["original"], R["relative"], R["nifty"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — Relative Momentum (Excess Return over NIFTY 50)</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same top-10, equal-weight, June/December strategy — but ranked on EXCESS return over NIFTY 50 (stock's 6m/12m return minus NIFTY 50's own 6m/12m return over the identical window) instead of the original's absolute return. Isolates stocks beating the market, not just riding it up with everything else.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_rebalances']} rebalances<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#6AE4FF]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill(f"{R['avg_overlap_pct']:.1f}% average pick overlap with the original — far higher than report 33's skip-month variant", 'neutral')}
          {pill('near-identical result to the original formula', 'neutral')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Subtracting NIFTY 50's own return from every stock's return before ranking shifts every stock's number by the SAME amount that day —
          which, on its own, wouldn't change the ranking at all (subtracting a constant preserves rank order). What actually changes the outcome
          is that this shift happens BEFORE dividing by each stock's own (different) volatility — so the same constant shift affects a
          low-volatility stock's ratio more than a high-volatility stock's. That's a real mechanism, just a much gentler one than report 33's
          skip-month change, which is exactly why the overlap here ({R['avg_overlap_pct']:.1f}%) is so much higher than there (59.3%).
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The honest result: relative momentum lands within a hair of the original — CAGR {pct(rel['cagr_pct'])} vs.
          {pct(orig['cagr_pct'])}, identical {pct(rel['max_drawdown_pct'],1,signed=False)} max drawdown to one decimal place. Both comfortably
          beat NIFTY 50 itself ({pct(nif['cagr_pct'])} CAGR / {pct(nif['max_drawdown_pct'],1,signed=False)} DD) by a wide margin — see the
          honesty note below for why this particular reformulation was always likely to be a near-equivalent, not a genuinely different bet.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for all three.",
                  [("Original (absolute)", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("Relative (vs NIFTY)", pct(rel["cagr_pct"]), win_loss_kind(rel["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Original (absolute)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Relative (vs NIFTY)", pct(rel["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Original (absolute)", pct(orig["net_return_pct"]), win_loss_kind(orig["net_return_pct"])),
                   ("Relative (vs NIFTY)", pct(rel["net_return_pct"]), win_loss_kind(rel["net_return_pct"]))]),
        kpi_card("How different are the actual picks", "Average % of each rebalance's top 10 that's the SAME stock under both formulas.",
                  [("Avg overlap", f"{R['avg_overlap_pct']:.1f}%", "assumption"),
                   ("Rebalances compared", f"{R['num_overlap_rebalances']}", "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All three, side by side</h3>
        {pill('grey row = real benchmark, not a reconstruction', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — both formulas against the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Original formula (absolute return)", orig)}
          {row("Relative momentum (excess over NIFTY 50)", rel)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Original (absolute)", "color": COL["positive"], "points": orig["equity_curve"]},
        {"name": "Relative (vs NIFTY)", "color": ACCENT_2, "points": rel["equity_curve"], "dash": True},
        {"name": "NIFTY 50", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_34")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each formula, linear axis, not log-scaled. The two momentum lines track each other closely for almost the entire window.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
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
        {"name": "Original (absolute)", "color": COL["positive"], "points": dd_points(orig["equity_curve"])},
        {"name": "Relative (vs NIFTY)", "color": ACCENT_2, "points": dd_points(rel["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_34")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the two formulas' drawdowns are nearly indistinguishable ({pct(orig['max_drawdown_pct'],1,signed=False)} vs. {pct(rel['max_drawdown_pct'],1,signed=False)}) — consistent with the high pick-overlap between them.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_row(s):
        return f"""<tr><td>{esc(s['date'])}</td><td style="text-align:left">{esc(', '.join(s['tickers']))}</td></tr>"""

    selections_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample rebalances — same dates, mostly the same picks</h3>
        {pill('first 3 and last 3 of ' + str(R['num_rebalances']) + ' shown for each', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the actual top-10 selected by each formula at the same rebalance dates — with {R['avg_overlap_pct']:.1f}% average overlap, expect most rows to differ by only 1-2 names, not the whole list.</p>
      <div class="mb-4">
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">Original formula (absolute return)</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['original']['selections_sample'])}</tbody></table>
      </div>
      <div>
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">Relative momentum (excess over NIFTY 50)</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['relative']['selections_sample'])}</tbody></table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why this reformulation barely moved the needle</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Subtracting the SAME benchmark return from every stock that day is mathematically a shared, constant shift — it cannot, by itself,
        reorder which stock has the higher or lower raw return. The only reason relative momentum picks a DIFFERENT top 10 at all is that this
        shift happens before dividing by each stock's OWN volatility, which differs stock to stock: a low-volatility stock's score moves more
        (in ratio terms) from the same absolute shift than a high-volatility stock's does. That's a real effect, but a second-order one — which
        is exactly why {R['avg_overlap_pct']:.1f}% of picks stay the same, versus only 59.3% for report 33's skip-month variant, which changes
        the entire reference date every calculation is anchored to (a first-order effect, not a second-order one).
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This is a useful negative result in its own right: it shows that "absolute vs. relative momentum" — a distinction that sounds
        conceptually important, and IS important in a genuinely divergent market (a crash where relative winners fall less, or a narrow rally
        where only some stocks participate) — doesn't necessarily produce a materially different portfolio in a market where midcap winners and
        the broad index have moved in the same general direction most of the time. A market regime with a sharper divergence between NIFTY 50
        and midcap leadership (a narrow large-cap-only rally, for instance) would very plausibly separate these two formulas much more than this
        18-year window happened to.
      </p>
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
        <li class="mb-1.5">NIFTY 50 (a large-cap index) is used as the benchmark for a MIDCAP strategy, purely because it's the only benchmark with full history back to 2008 — MID150BEES.NS (the real, tradable midcap ETF used elsewhere in this project) only starts 2019-02-04. A midcap-specific benchmark could plausibly change this result, especially in periods where midcap and large-cap leadership diverge.</li>
        <li class="mb-1.5">The stock's own absolute volatility is still used as the risk-adjustment denominator for the relative-return version — an alternative would use TRACKING ERROR (volatility of the stock's return minus the benchmark's return) instead, which is the more theoretically "pure" relative-momentum risk adjustment; that variant was not tested here.</li>
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window for both formulas equally (survivorship bias) — same disclosed approximation as every other reconstruction here.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled — same as reports 11-19/24-33's frictionless numbers (see report 32 for what real Kotak Neo charges do to a similar strategy).</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding. This is a single, fixed 18-year historical path — a different window with sharper NIFTY-vs-midcap divergence could separate these two formulas far more than shown here.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    <div class="px-10 py-6">
      {kpi_grid}
      {full_table}
      {eq_panel}
      {dd_panel}
      {selections_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — Relative Momentum vs. NIFTY 50</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("34_midcap_momentum10_relative_momentum.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 34_midcap_momentum10_relative_momentum.html")
