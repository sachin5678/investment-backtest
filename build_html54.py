"""Builds 54_midcap_momentum10_own_index_trend_filter.html from results53.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results53.json") as f:
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
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Universe-Specific Trend Filter</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Reports 42-47 computed the 200-day EMA regime signal purely from NIFTY 50, even though this strategy trades midcaps. This report tests using {esc(ticker)} — an ETF tracking the SAME NIFTY Midcap 150 index this strategy trades, i.e. the strategy's own universe's own price — as the trend signal instead. Same 200-day EMA span, same immediate-switch mechanics, same Midcap150 Momentum 10 formula throughout.</p>
          <p class="{MUTED} mt-2">DATA NOTE — this project's usual Midcap 150 ETF proxy, MID150BEES.NS (Nippon India), no longer returns price history via Yahoo Finance as of this report; {esc(ticker)} (ICICI Prudential's NIFTY Midcap 150 ETF, same underlying index, still live) is used instead. Its history only starts 2021, so this window is much shorter than reports 42-47's — ALL THREE series below are recomputed fresh on this shorter, common window.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('using the strategy’s own index as the signal did NOT beat NIFTY 50 here', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Over this shorter, ETF-constrained window, the own-index signal is WORSE than the NIFTY-50 signal on both dimensions:
          CAGR falls from {pct(nsig['cagr_pct'])} to <span class="font-semibold">{pct(osig['cagr_pct'])}</span>, and max drawdown is
          actually DEEPER, {pct(nsig['max_drawdown_pct'],1,signed=False)} vs. <span class="font-semibold">{pct(osig['max_drawdown_pct'],1,signed=False)}</span>
          — the opposite of the intuition that a universe-specific signal should time that universe's own downturns better.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Read this result cautiously: the window here (2021 onward) is far shorter than the 2008-2026 window used elsewhere in
          this project, and does NOT include a genuinely severe midcap-specific crash — see the honesty note and report 55/56
          for the same test on universes with a longer, real index history available.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical (shorter) window for every series.",
                  [("No filter", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("NIFTY 50 signal", pct(nsig["cagr_pct"]), win_loss_kind(nsig["cagr_pct"])),
                   (f"Own index ({esc(ticker)})", pct(osig["cagr_pct"]), win_loss_kind(osig["cagr_pct"])),
                   ("NIFTY 50 (bench)", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline, identical window for every series.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50 signal", pct(nsig["max_drawdown_pct"], 1, signed=False), "positive"),
                   (f"Own index ({esc(ticker)})", pct(osig["max_drawdown_pct"], 1, signed=False), "negative"),
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
          {row("Midcap150 Momentum 10 — no filter", orig)}
          {row("Midcap150 Momentum 10 — NIFTY 50 signal", nsig)}
          {row(f"Midcap150 Momentum 10 — own index signal ({esc(ticker)})", osig)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
        {"name": "NIFTY 50 signal", "color": COL["positive"], "points": nsig["equity_curve"]},
        {"name": f"Own index ({esc(ticker)})", "color": COL["negative"], "points": osig["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_54")
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
        {"name": "NIFTY 50 signal", "color": COL["positive"], "points": dd_points(nsig["equity_curve"])},
        {"name": f"Own index ({esc(ticker)})", "color": COL["negative"], "points": dd_points(osig["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_54")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the own-index signal's drawdown ({pct(osig['max_drawdown_pct'],1,signed=False)}) is DEEPER than the NIFTY-50 signal's ({pct(nsig['max_drawdown_pct'],1,signed=False)}) over this window — the reverse of what the "specific signal should protect better" intuition would predict.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why the intuition didn't hold here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        There are two candidate explanations, and this report can't fully separate them. First, {esc(ticker)}'s short history
        (2021 onward) means this test never sees a genuinely severe, midcap-specific downturn distinct from a broad-market
        one — the exact scenario where a universe-specific signal should earn its keep. Second, midcap indices are often
        CHOPPIER than NIFTY 50 around their own moving averages (more frequent, smaller crossings), which this report's own
        re-entry counts show: {osig['num_regime_reentries']} re-entries for the own-index signal vs. {nsig['num_regime_reentries']}
        for the NIFTY-50 signal over the SAME shorter window — more whipsaw, not less, despite using a "more relevant" index.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Report 55 (Smallcap250, using the REAL NIFTY Smallcap 250 index with a full 2008-2026 history) and report 56 (NIFTY100,
        using the real ^CNX100 index, also full history) are the more decisive tests of this idea — Midcap150's result here
        should be read as inconclusive due to the short window, not as a verdict against universe-specific signals in general.
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
        <li class="mb-1.5">{esc(ticker)}'s history only starts 2021, so this window EXCLUDES the 2008 GFC, the 2020 COVID crash, and the 2015-16 slowdown — the three biggest stress tests reports 42-47's longer window covers. This is the weakest of the three universe-specific-signal reports (54-56) for exactly that reason.</li>
        <li class="mb-1.5">Zero transaction costs on ANY regime switch — same disclosed omission as reports 42-53.</li>
        <li class="mb-1.5">{esc(ticker)} is a different fund house (ICICI Prudential) from this project's usual midcap ETF (Nippon's MID150BEES.NS, no longer available) — both track the same underlying index, but real-world tracking error, expense ratios, and liquidity can differ between them.</li>
        <li class="mb-1.5">Only ONE EMA span (200 days) and immediate-switch (no confirmation delay) were tested here.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other reconstruction here.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Universe-Specific Trend Filter</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("54_midcap_momentum10_own_index_trend_filter.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 54_midcap_momentum10_own_index_trend_filter.html")
