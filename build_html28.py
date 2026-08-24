"""Builds 28_nifty100_momentum5.html from results27.json. Same
self-contained contract, smooth Catmull-Rom charts, dark palette as every
other report."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results27.json") as f:
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
    m5, m10, nif, mc = R["momentum5"], R["momentum10"], R["nifty"], R["midcap"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">"NIFTY100 Momentum 5" — A More Concentrated Variant</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same universe, formula, and June/December rebalance as report 12's "NIFTY100 Momentum 10" — just top 5 instead of top 10, equal-weighted. Not a real NSE index; a custom, clearly-labelled variant.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_rebalances']} rebalances<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    cagr_diff = m5["cagr_pct"] - m10["cagr_pct"]
    dd_diff = m10["max_drawdown_pct"] - m5["max_drawdown_pct"]  # positive = 5 is worse (more negative)

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2B03C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">The concentration question, and the honest result up front</h2>
          {pill(f"Momentum-5 beats Momentum-10 by {cagr_diff:.1f}pp CAGR", 'positive')}
          {pill(f"but with a {abs(dd_diff):.1f}pp deeper drawdown and longer underwater stretch", 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Halving the portfolio from 10 stocks to 5, with no other change to the selection formula or rebalance schedule, is a direct test of
          whether concentrating a momentum bet into fewer, higher-conviction names pays off. Over {esc(R['start_date'])}–{esc(R['end_date'])},
          Momentum-5 compounded at <span class="font-semibold">{pct(m5['cagr_pct'])}</span> versus Momentum-10's
          <span class="font-semibold">{pct(m10['cagr_pct'])}</span> — a real, meaningful edge from concentration.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          That edge is not free: Momentum-5's max drawdown ({pct(m5['max_drawdown_pct'],1,signed=False)}) is deeper than Momentum-10's
          ({pct(m10['max_drawdown_pct'],1,signed=False)}), and it spent longer underwater ({m5['longest_underwater_days']:,} days vs.
          {m10['longest_underwater_days']:,} days) — exactly what basic diversification math predicts: fewer positions means each one's
          idiosyncratic move (good or bad) has twice the impact on the whole portfolio.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for all four.",
                  [("Momentum-5 (this idea)", pct(m5["cagr_pct"]), win_loss_kind(m5["cagr_pct"])),
                   ("Momentum-10 (report 12)", pct(m10["cagr_pct"]), win_loss_kind(m10["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"])),
                   ("Midcap ETF", pct(mc["cagr_pct"]), win_loss_kind(mc["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Momentum-5 (this idea)", pct(m5["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Momentum-10 (report 12)", pct(m10["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap ETF", pct(mc["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Momentum-5 (this idea)", pct(m5["net_return_pct"]), win_loss_kind(m5["net_return_pct"])),
                   ("Momentum-10 (report 12)", pct(m10["net_return_pct"]), win_loss_kind(m10["net_return_pct"]))]),
        kpi_card("Longest underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("Momentum-5 (this idea)", f'{m5["longest_underwater_days"]:,}d', "neutral"),
                   ("Momentum-10 (report 12)", f'{m10["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All four, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the two momentum reconstructions against NIFTY 50 and the real midcap ETF, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window (midcap's own history starts {esc(R['midcap_start_date'])}, later than the rest).</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("NIFTY100 Momentum 5 (this idea)", m5)}
          {row("NIFTY100 Momentum 10 (report 12)", m10)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("Midcap ETF, buy & hold", mc, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Momentum-5 (this idea)", "color": COL["positive"], "points": m5["equity_curve"]},
        {"name": "Momentum-10 (report 12)", "color": ACCENT_2, "points": m10["equity_curve"], "dash": True},
        {"name": "NIFTY 50", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
        {"name": "Midcap ETF", "color": COL["assumption"], "points": mc["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_28")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — Momentum-5 (green) pulls ahead of Momentum-10 (dashed violet) for most of the window, both dwarfing NIFTY 50 and the midcap ETF — the familiar reconstruction-survivorship-bias caveat below applies to both momentum lines equally.</p>
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
        {"name": "Momentum-5 (this idea)", "color": COL["positive"], "points": dd_points(m5["equity_curve"])},
        {"name": "Momentum-10 (report 12)", "color": ACCENT_2, "points": dd_points(m10["equity_curve"]), "dash": True},
        {"name": "NIFTY 50", "color": COL["text"], "points": dd_points(nif["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_28")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — Momentum-5's drawdown ({pct(m5['max_drawdown_pct'],1,signed=False)}) is visibly deeper than Momentum-10's ({pct(m10['max_drawdown_pct'],1,signed=False)}) at multiple points, not just once — the concentration cost shows up repeatedly across the 18-year window, not as a single unlucky event.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_row(s):
        return f"""<tr><td>{esc(s['date'])}</td><td style="text-align:left">{esc(', '.join(t.replace('.NS','') for t in s['tickers']))}</td></tr>"""

    selections_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample rebalances — the actual top 5 picked</h3>
        {pill('first 3 and last 3 of ' + str(R['num_rebalances']) + ' shown', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — exactly which 5 NIFTY 100 stocks the formula selected at a few sample rebalances, earliest and most recent.</p>
      <table class="data-table">
        <thead><tr><th>Date</th><th style="text-align:left">Top 5 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['selections_sample'])}</tbody>
      </table>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why concentration cuts both ways</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Both portfolios use the identical formula to rank the same 100 stocks — Momentum-5 simply keeps only the top half of what Momentum-10
        would have held. On average, whatever made those top 5 rank above positions 6-10 continued to be true often enough over 18 years for the
        extra concentration to pay off ({pct(cagr_diff,1,signed=False)} points of extra CAGR). But that same logic means Momentum-5 has no
        cushion at all if even ONE of its 5 picks turns out to be a momentum trap (a stock whose recent strength was about to reverse) — a single
        bad pick is 20% of the book, versus 10% in the 10-stock version.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        That's exactly the trade-off visible in the numbers: better average return, worse worst-case, and a longer stretch spent recovering from
        that worst case ({m5['longest_underwater_days']:,} days vs. {m10['longest_underwater_days']:,} days). Neither number is "wrong" — this is
        the standard concentration-vs-diversification trade-off showing up in a real backtest, not a flaw in either construction.
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
        <li class="mb-1.5">Today's fixed NIFTY 100 constituent list is applied retroactively across the whole window (survivorship bias) — same disclosed approximation as report 12 and every other reconstruction in this project.</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score), same as report 12 — for a 5-stock book this makes each position's weight (20%) even more consequential than in the 10-stock version (10%).</li>
        <li class="mb-1.5">No F&O-eligibility screen and June/December rebalance dates approximated as the last trading day of the month, same as report 12.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled — a 5-stock book turning over completely at each rebalance is a more concentrated trading cost exposure per rupee invested than the 10-stock version, though the NUMBER of rebalances (36) is identical for both.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding.</li>
        <li class="mb-1.5">This is a single, fixed 18-year historical path — a different window could easily flip which of Momentum-5 or Momentum-10 comes out ahead; concentration amplifies whatever the underlying momentum signal did over THIS specific history, for better or worse.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>"NIFTY100 Momentum 5"</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("28_nifty100_momentum5.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 28_nifty100_momentum5.html")
