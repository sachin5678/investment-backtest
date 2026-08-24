"""Builds 29_smallcap250_momentum10_5.html from results28.json. Same
self-contained contract, smooth Catmull-Rom charts, dark palette as every
other report."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results28.json") as f:
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
    m10, m5 = R["momentum10"], R["momentum5"]
    nif, sci, mc = R["nifty"], R["smallcap_index"], R["midcap_etf"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Smallcap250 Momentum 10 &amp; Momentum 5, Head to Head</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same universe, formula, and June/December rebalance as report 16 — Momentum 10 recomputed fresh, plus a new, more concentrated Momentum 5 variant (top 5 instead of top 10), the same test as report 28 did for NIFTY 100.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_rebalances']} rebalances<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">The concentration question, and a DIFFERENT answer than report 28</h2>
          {pill('here, MORE concentration makes things worse on BOTH dimensions', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Report 28 found that concentrating NIFTY100 Momentum from 10 stocks down to 5 improved CAGR at the cost of a deeper drawdown — a
          classic trade-off. Smallcaps tell a different story: Momentum-5 compounded at only
          <span class="font-semibold">{pct(m5['cagr_pct'])}</span> versus Momentum-10's <span class="font-semibold">{pct(m10['cagr_pct'])}</span>
          — WORSE return — while its max drawdown ({pct(m5['max_drawdown_pct'],1,signed=False)}) is also deeper than Momentum-10's
          ({pct(m10['max_drawdown_pct'],1,signed=False)}). There is no trade-off here — concentration loses on both dimensions.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The likely reason: smallcap momentum leaders are the noisiest, most idiosyncratic corner of this project's entire universe — the same
          survivorship bias disclosed in every smallcap reconstruction here is at its strongest, and individual smallcap winners/blowups swing
          much harder than large or mid-cap ones. Concentrating into just 5 names amplifies that noise more than it captures a real signal —
          see the honesty note below.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for all five.",
                  [("Momentum-5 (new)", pct(m5["cagr_pct"]), win_loss_kind(m5["cagr_pct"])),
                   ("Momentum-10", pct(m10["cagr_pct"]), win_loss_kind(m10["cagr_pct"])),
                   ("Smallcap 250 (real index)", pct(sci["cagr_pct"]), win_loss_kind(sci["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Momentum-5 (new)", pct(m5["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Momentum-10", pct(m10["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Smallcap 250 (real index)", pct(sci["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Momentum-5 (new)", pct(m5["net_return_pct"]), win_loss_kind(m5["net_return_pct"])),
                   ("Momentum-10", pct(m10["net_return_pct"]), win_loss_kind(m10["net_return_pct"]))]),
        kpi_card("Longest underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("Momentum-5 (new)", f'{m5["longest_underwater_days"]:,}d', "neutral"),
                   ("Momentum-10", f'{m10["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All five, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — both momentum reconstructions against the real Smallcap 250 index, NIFTY 50, and the midcap ETF, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window (the real smallcap and midcap ETF benchmarks each have their own, later, available-history start dates).</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Smallcap250 Momentum 5 (new)", m5)}
          {row("Smallcap250 Momentum 10", m10)}
          {row("NIFTY Smallcap 250 (real index)", sci, "real-bench")}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("Midcap ETF, buy & hold", mc, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Momentum-10", "color": COL["positive"], "points": m10["equity_curve"]},
        {"name": "Momentum-5 (new)", "color": COL["negative"], "points": m5["equity_curve"]},
        {"name": "Smallcap 250 (real index)", "color": ACCENT_2, "points": sci["equity_curve"], "dash": True},
        {"name": "NIFTY 50", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_29")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — Momentum-10 (green) pulls decisively ahead of Momentum-5 (red) for almost the whole window — the reverse of report 28's NIFTY100 finding.</p>
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
        {"name": "Momentum-10", "color": COL["positive"], "points": dd_points(m10["equity_curve"])},
        {"name": "Momentum-5 (new)", "color": COL["negative"], "points": dd_points(m5["equity_curve"])},
        {"name": "Smallcap 250 (real index)", "color": ACCENT_2, "points": dd_points(sci["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_29")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — Momentum-5's drawdown ({pct(m5['max_drawdown_pct'],1,signed=False)}) is deeper than Momentum-10's ({pct(m10['max_drawdown_pct'],1,signed=False)}) at multiple points — concentration adds risk here without the return payoff seen in report 28's NIFTY100 test.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_row(s):
        return f"""<tr><td>{esc(s['date'])}</td><td style="text-align:left">{esc(', '.join(t.replace('.NS','') for t in s['tickers']))}</td></tr>"""

    selections_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample rebalances — the actual picks</h3>
        {pill('first 3 and last 3 shown for each', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — which smallcap names the formula actually selected, earliest and most recent rebalances, for both portfolio sizes.</p>
      <div class="mb-4">
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">Momentum-10</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['momentum10_selections_sample'])}</tbody></table>
      </div>
      <div>
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">Momentum-5</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 5 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['momentum5_selections_sample'])}</tbody></table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why concentration helped NIFTY100 but hurt Smallcap250</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Report 28 concentrated a large-cap universe (NIFTY 100) and the payoff was real: fewer, higher-conviction large-cap momentum leaders
        tend to keep leading for a while, because large-cap trends are driven by genuinely persistent factors (earnings momentum, institutional
        flows) that don't reverse as violently. Smallcaps behave differently — this project's own smallcap reconstructions (report 16) already
        carry the strongest disclosed survivorship bias of any universe here, and individual smallcap "momentum leaders" are far more prone to
        being one-off news-driven spikes (a small stock up 80% in 6 months on a single contract win or promoter announcement) that don't persist.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Concentrating a 250-name universe's picks down to just 5 stocks means each one is 20% of the book — for a universe already this noisy,
        that amplifies idiosyncratic blowups more than it captures a repeatable trend, which is exactly why Momentum-5 loses to Momentum-10 on
        BOTH return and risk here, unlike the large-cap case in report 28.
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
        <li class="mb-1.5">Today's fixed NIFTY Smallcap 250 constituent list is applied retroactively across the whole window for both portfolio sizes equally — the strongest survivorship bias of any universe in this project (smallcap membership churns fastest).</li>
        <li class="mb-1.5">2 of the 250 smallcap tickers (SONACOMS.NS, KIMS.NS) have no price data available at all and are excluded — a data-availability gap, not a judgment call, same as report 16.</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score), same as every other reconstruction here — for a 5-stock book this makes each position's weight (20%) far more consequential.</li>
        <li class="mb-1.5">No F&O-eligibility screen, and June/December rebalance dates borrowed from the NIFTY200 Momentum convention (smallcap has no real momentum index to anchor a calendar to).</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled on either variant — smallcap stocks are typically less liquid than midcap/largecap, so real-world costs would likely be highest here of any universe tested in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding.</li>
        <li class="mb-1.5">This is a single, fixed 18-year historical path — a different window could show a different result; smallcap concentration's poor showing here should not be read as a universal law.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Smallcap250 Momentum 10 &amp; 5</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("29_smallcap250_momentum10_5.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 29_smallcap250_momentum10_5.html")
