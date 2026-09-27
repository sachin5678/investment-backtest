"""Builds 33_midcap_momentum10_12_1_skip_month.html from results32.json.
Same self-contained contract, smooth Catmull-Rom charts, dark palette as
every other report."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results32.json") as f:
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
    orig, skip1 = R["original"], R["skip1"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — "12-1" Skip-Month Momentum</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same top-10, equal-weight, June/December strategy as every other Midcap150 Momentum 10 report — but every price/volatility reference point shifts back {R['skip_month_days']} trading days ("as of 1 month ago" instead of "as of today"), the standard academic momentum convention that excludes the short-term-reversal-prone most recent month.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_rebalances']} rebalances<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    better_cagr = skip1["cagr_pct"] > orig["cagr_pct"]
    better_dd = skip1["max_drawdown_pct"] > orig["max_drawdown_pct"]

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2B03C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill(f"only {R['avg_overlap_pct']:.1f}% average pick overlap between the two formulas", 'neutral')}
          {pill('the academic 1-month skip does NOT improve this strategy', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          The 1-month skip is real academic literature (Jegadeesh &amp; Titman 1993, and every standard "Mom" factor construction since) —
          motivated by short-term price reversal dominating the most recent month, muddying the multi-month trend-persistence signal the rest of
          the formula is trying to capture. It's a genuinely different portfolio, not a cosmetic tweak: on average only
          <span class="font-semibold">{R['avg_overlap_pct']:.1f}%</span> of each rebalance's top 10 picks are the same stock under both formulas.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          On THIS strategy, over THIS 18-year window, the honest result is that skipping the most recent month doesn't help:
          CAGR {pct(skip1['cagr_pct'])} vs. the original's {pct(orig['cagr_pct'])}, and max drawdown
          {pct(skip1['max_drawdown_pct'],1,signed=False)} vs. {pct(orig['max_drawdown_pct'],1,signed=False)} — slightly worse on both counts, not
          better on either. See the honesty note below for why a well-established academic edge doesn't automatically transfer to a different
          market, universe, and rebalance cadence than the one it was originally documented in.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for both.",
                  [("Original (as-of-today)", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("12-1 skip-month", pct(skip1["cagr_pct"]), win_loss_kind(skip1["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Original (as-of-today)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("12-1 skip-month", pct(skip1["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Original (as-of-today)", pct(orig["net_return_pct"]), win_loss_kind(orig["net_return_pct"])),
                   ("12-1 skip-month", pct(skip1["net_return_pct"]), win_loss_kind(skip1["net_return_pct"]))]),
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
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Both formulas, side by side</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — identical strategy, identical {esc(R['start_date'])}–{esc(R['end_date'])} window, only the formula's reference date changes.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Original formula (measured as of today)", orig)}
          {row("12-1 skip-month formula (measured as of 1 month ago)", skip1)}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Original formula", "color": COL["positive"], "points": orig["equity_curve"]},
        {"name": "12-1 skip-month", "color": COL["assumption"], "points": skip1["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_33")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each formula, linear axis, not log-scaled.</p>
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
        {"name": "Original formula", "color": COL["positive"], "points": dd_points(orig["equity_curve"])},
        {"name": "12-1 skip-month", "color": COL["assumption"], "points": dd_points(skip1["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_33")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the 12-1 skip-month formula's drawdown ({pct(skip1['max_drawdown_pct'],1,signed=False)}) is deeper than the original's ({pct(orig['max_drawdown_pct'],1,signed=False)}) — the 1-month skip doesn't cushion this strategy's worst stretch, it slightly deepens it.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_row(s):
        return f"""<tr><td>{esc(s['date'])}</td><td style="text-align:left">{esc(', '.join(s['tickers']))}</td></tr>"""

    selections_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample rebalances — same dates, different picks</h3>
        {pill('first 3 and last 3 of ' + str(R['num_rebalances']) + ' shown for each', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the actual top-10 selected by each formula at the same rebalance dates — compare row by row to see how much a 1-month shift in the reference date changes which stocks rank highest.</p>
      <div class="mb-4">
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">Original formula</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['original']['selections_sample'])}</tbody></table>
      </div>
      <div>
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">12-1 skip-month formula</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['skip1']['selections_sample'])}</tbody></table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why a real academic edge didn't transfer here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The 1-month skip was documented on US large-cap equities over a specific historical sample, with a specific (monthly) rebalance cadence.
        This strategy runs on Indian midcaps, rebalanced only twice a year, on a top-10 concentrated book — three real differences from the
        environment the original research was based on. Short-term reversal is itself a real, but WEAKER and noisier, effect in a smaller, less
        liquid universe than US large caps, and a June/December rebalance already only checks momentum twice a year — the "most recent month"
        problem the skip is designed to fix matters far less when you're not re-evaluating monthly in the first place.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The {R['avg_overlap_pct']:.1f}% average overlap confirms the skip is a real, substantial change to which stocks get picked — not a
        rounding error — so this isn't a case of the formula barely differing and unsurprisingly landing close to the original. It genuinely
        picks a different portfolio nearly every rebalance, and on this specific strategy and window, the different portfolio happens to be
        slightly worse on both return and drawdown. That's a legitimate, disclosed finding about THIS strategy — not evidence the skip-month
        convention is wrong in general, which a large body of research elsewhere still supports.
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
        <li class="mb-1.5">The skip is applied uniformly to both the 6-month AND 12-month legs (and the volatility window) — the classic "12-1" literature is specifically about the 12-month leg; this project's formula blends 6m+12m, so applying the skip consistently to both was a judgment call, not a literal reproduction of the original academic construction.</li>
        <li class="mb-1.5">{R['skip_month_days']} trading days is used as "1 month" — a fixed approximation, not a calendar-month-aware calculation.</li>
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window for both formulas equally (survivorship bias) — same disclosed approximation as every other reconstruction here.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled — same as reports 11-19/24-31's frictionless numbers (see report 32 for what real Kotak Neo charges do to a similar strategy).</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding. This is a single, fixed 18-year historical path — a different window or universe could rank these two formulas differently.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — 12-1 Skip-Month Momentum</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("33_midcap_momentum10_12_1_skip_month.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 33_midcap_momentum10_12_1_skip_month.html")
