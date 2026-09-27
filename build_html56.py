"""Builds 56_nifty100_momentum10_own_index_trend_filter.html from results55.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results55.json") as f:
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
    orig, nsig, osig, nif = R["original"], R["nifty_signal"], R["own_signal"], R["nifty"]
    ticker = R["universe_ticker"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">NIFTY100 Momentum 10 — Universe-Specific Trend Filter</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Reports 54-55 tested a universe-specific 200-day EMA signal on Midcap150 (inconclusive, short ETF history) and Smallcap250 (a genuine trade-off, full history). This report uses {esc(ticker)} — the REAL NIFTY 100 index itself, fetchable directly from Yahoo Finance with full history back to 2005 — as the trend signal instead of NIFTY 50, applied to report 12's NIFTY100 Momentum 10 config. This is the third and final universe-specific-signal test.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2B03C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('the same trade-off as Smallcap250 (report 55)', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          On NIFTY100, using the strategy's own index ({esc(ticker)}) as the signal again gives a SHALLOWER drawdown —
          {pct(nsig['max_drawdown_pct'],1,signed=False)} improves to <span class="font-semibold">{pct(osig['max_drawdown_pct'],1,signed=False)}</span> —
          at a modest CAGR cost: {pct(nsig['cagr_pct'])} to <span class="font-semibold">{pct(osig['cagr_pct'])}</span>.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Two of the three universe-specific-signal tests with full historical data (Smallcap250 and NIFTY100 here) now show
          the SAME shape of trade-off: a more relevant signal protects better but costs some return, likely for the same
          reason in both cases — see report 55's honesty note on lagged peaks and troughs. Midcap150's own test (report 54)
          remains the outlier, but its much shorter data window makes that comparison the least reliable of the three.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for every series.",
                  [("No filter", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("NIFTY 50 signal", pct(nsig["cagr_pct"]), win_loss_kind(nsig["cagr_pct"])),
                   (f"Own index ({esc(ticker)})", pct(osig["cagr_pct"]), win_loss_kind(osig["cagr_pct"])),
                   ("NIFTY 50 (bench)", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline, identical window for every series.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50 signal", pct(nsig["max_drawdown_pct"], 1, signed=False), "positive"),
                   (f"Own index ({esc(ticker)})", pct(osig["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("NIFTY 50 (bench)", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("How active is each filter", "Time in cash and re-entries for each signal source.",
                  [("NIFTY50-signal: time in cash", f"{nsig['pct_time_in_cash']:.1f}%", "assumption"),
                   ("NIFTY50-signal: re-entries", f"{nsig['num_regime_reentries']}", "assumption"),
                   ("Own-signal: time in cash", f"{osig['pct_time_in_cash']:.1f}%", "assumption"),
                   ("Own-signal: re-entries", f"{osig['num_regime_reentries']}", "assumption")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All four, side by side</h3>
        {pill('grey row = real benchmark, not a reconstruction', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("NIFTY100 Momentum 10 — no filter", orig)}
          {row("NIFTY100 Momentum 10 — NIFTY 50 signal", nsig)}
          {row(f"NIFTY100 Momentum 10 — own index signal ({esc(ticker)})", osig)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
        {"name": "NIFTY 50 signal", "color": COL["negative"], "points": nsig["equity_curve"]},
        {"name": f"Own index ({esc(ticker)})", "color": COL["positive"], "points": osig["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_56")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {R['currency_symbol']}100 invested at the start of the window grew under each signal source, linear axis, not log-scaled.</p>
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
        {"name": "NIFTY 50 signal", "color": COL["negative"], "points": dd_points(nsig["equity_curve"])},
        {"name": f"Own index ({esc(ticker)})", "color": COL["positive"], "points": dd_points(osig["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_56")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the own-index signal's drawdown ({pct(osig['max_drawdown_pct'],1,signed=False)}) is shallower than the NIFTY-50 signal's ({pct(nsig['max_drawdown_pct'],1,signed=False)}).</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Two of three full-history tests agree</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        NIFTY 100 and NIFTY 50 are closely related indices — NIFTY 100 IS NIFTY 50 plus the next 50 large/mid-cap names — so
        it might be expected that a NIFTY100-based signal would barely differ from a NIFTY-50-based one. It doesn't barely
        differ: {osig['num_regime_reentries']} re-entries (own-signal) vs. {nsig['num_regime_reentries']} (NIFTY50-signal) over
        the same window shows the two indices genuinely cross their own 200-EMAs at different times, and that timing
        difference is enough to produce the same shape of trade-off seen on Smallcap250 — better drawdown protection, some
        CAGR cost — even between two closely related large-cap indices.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Combined with report 55, this is now two independent, full-18-year-history tests pointing the same direction, against
        one shorter, less reliable test (report 54) pointing the other way. The most defensible reading: a universe-specific
        trend signal probably DOES trade some return for better protection versus a NIFTY-50 signal, though "probably" is
        doing real work in that sentence — three data points across one set of formula choices is still not a lot.
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
        <li class="mb-1.5">Zero transaction costs on ANY regime switch — same disclosed omission as reports 42-55.</li>
        <li class="mb-1.5">Only ONE EMA span (200 days) and immediate-switch (no confirmation delay) were tested here for either signal source.</li>
        <li class="mb-1.5">^CNX100 is not previously used elsewhere in this project — it was newly identified for this report specifically because it's directly fetchable with full history, unlike the Midcap150 ETF proxy that broke (report 54).</li>
        <li class="mb-1.5">Today's fixed NIFTY100 constituent list (report 12's config) is applied retroactively (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other reconstruction here. This is a single, fixed historical path.</li>
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
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>NIFTY100 Momentum 10 — Universe-Specific Trend Filter</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("56_nifty100_momentum10_own_index_trend_filter.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 56_nifty100_momentum10_own_index_trend_filter.html")
