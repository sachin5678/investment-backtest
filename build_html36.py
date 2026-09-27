"""Builds 36_midcap_momentum10_52wk_high.html from results35.json. Same
self-contained contract, smooth Catmull-Rom charts, dark palette as every
other report."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results35.json") as f:
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
    orig, high52, nif = R["original"], R["high52"], R["nifty"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — 52-Week-High Proximity</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">A genuinely different momentum proxy, not a tweak of the existing one: rank by how close today's price is to its own trailing 52-week high (George &amp; Hwang, 2004), instead of 6m/12m risk-adjusted return. Same top-10, equal-weight, June/December rebalance, Midcap150 universe.</p>
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
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill(f"only {R['avg_overlap_pct']:.1f}% average pick overlap — a genuinely different portfolio", 'neutral')}
          {pill('underperforms the original formula on both return and drawdown', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          52-week-high proximity is well-documented US academic literature — a stock trading near its own 52-week high is argued to behave
          differently than the same total return achieved while still well below it, because the high itself is a salient, widely-watched
          reference price. It's a real reformulation, not a parameter tweak: only <span class="font-semibold">{R['avg_overlap_pct']:.1f}%</span>
          of each rebalance's top 10 overlaps with the original formula's picks — the most divergent variant tested in this comparison series so
          far (vs. 59.3% for the skip-month variant and 92.2% for relative momentum).
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The honest result: on this strategy, this window, this universe, 52-week-high proximity clearly underperforms — CAGR
          {pct(high52['cagr_pct'])} vs. the original's {pct(orig['cagr_pct'])}, and a deeper max drawdown
          ({pct(high52['max_drawdown_pct'],1,signed=False)} vs. {pct(orig['max_drawdown_pct'],1,signed=False)}). It still comfortably beats NIFTY
          50 ({pct(nif['cagr_pct'])} CAGR) — so it's not a broken signal, just a weaker one here than the project's existing formula. See the
          honesty note below for why.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for all three.",
                  [("Original (6m/12m return)", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("52-week-high proximity", pct(high52["cagr_pct"]), win_loss_kind(high52["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Original (6m/12m return)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("52-week-high proximity", pct(high52["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Original (6m/12m return)", pct(orig["net_return_pct"]), win_loss_kind(orig["net_return_pct"])),
                   ("52-week-high proximity", pct(high52["net_return_pct"]), win_loss_kind(high52["net_return_pct"]))]),
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
          {row("Original formula (6m/12m risk-adjusted return)", orig)}
          {row("52-week-high proximity", high52)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Original (6m/12m return)", "color": COL["positive"], "points": orig["equity_curve"]},
        {"name": "52-week-high proximity", "color": ACCENT_2, "points": high52["equity_curve"], "dash": True},
        {"name": "NIFTY 50", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_36")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each formula, linear axis, not log-scaled. The gap between the two momentum lines widens steadily, not just at one point in the window.</p>
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
        {"name": "Original (6m/12m return)", "color": COL["positive"], "points": dd_points(orig["equity_curve"])},
        {"name": "52-week-high proximity", "color": ACCENT_2, "points": dd_points(high52["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_36")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — 52-week-high proximity's drawdown ({pct(high52['max_drawdown_pct'],1,signed=False)}) is meaningfully deeper than the original's ({pct(orig['max_drawdown_pct'],1,signed=False)}).</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_row(s):
        return f"""<tr><td>{esc(s['date'])}</td><td style="text-align:left">{esc(', '.join(s['tickers']))}</td></tr>"""

    selections_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample rebalances — how different the picks really are</h3>
        {pill('first 3 and last 3 of ' + str(R['num_rebalances']) + ' shown for each', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the actual top-10 selected by each formula at the same rebalance dates. With only {R['avg_overlap_pct']:.1f}% average overlap, expect most rows to share just 1-3 names, not most of the list.</p>
      <div class="mb-4">
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">Original formula (6m/12m return)</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['original']['selections_sample'])}</tbody></table>
      </div>
      <div>
        <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2">52-week-high proximity</div>
        <table class="data-table"><thead><tr><th>Date</th><th style="text-align:left">Top 10 selected</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in R['high52']['selections_sample'])}</tbody></table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why a real academic signal underperforms this project's formula here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        A stock can sit at 100% of its own 52-week high while having barely moved over the past 6-12 months — a slow, low-volatility grinder
        that hasn't drawn down much simply because it hasn't done much at all, and hasn't been particularly volatile either way. The 6m/12m
        risk-adjusted return formula specifically REWARDS large, sustained moves (adjusted for how volatile the stock normally is); 52-week-high
        proximity doesn't distinguish "just made a new high after a huge run" from "never fell much from a high set a while ago and has been
        flat since." In a concentrated top-10 book, picking several names in the second category instead of the first is a real, structural
        reason to underperform a return-based momentum score — not a fluke of this particular window.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This doesn't mean 52-week-high proximity is a bad signal in general — the George &amp; Hwang research it's based on is real and widely
        cited, typically studied on US large-cap universes with different rebalancing conventions than this project's twice-a-year Indian midcap
        setup. It means that, specifically as a drop-in replacement for THIS project's existing 6m/12m formula, on THIS strategy, it's a weaker
        choice — a useful, disclosed negative result about combining two things (a different signal, a different market/cadence) that weren't
        necessarily meant to be interchangeable.
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
        <li class="mb-1.5">No volatility adjustment or cross-sectional Z-scoring is applied to the 52-week-high ratio — the module docstring explains why this is a reasonable simplification (the ratio is already naturally comparable across stocks, and Z-scoring a single factor is rank-preserving), but it does mean this variant's construction differs slightly in KIND from the project's usual Z-score+combine approach, not just in which factor is used.</li>
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window for both formulas equally (survivorship bias) — same disclosed approximation as every other reconstruction here.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled — same as reports 11-19/24-35's frictionless numbers (see report 32 for what real Kotak Neo charges do to a similar strategy).</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — 52-Week-High Proximity</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("36_midcap_momentum10_52wk_high.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 36_midcap_momentum10_52wk_high.html")
