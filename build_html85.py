"""Builds 85_midcap150_report48_rebalance_month_offset.html from results84.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results84.json") as f:
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

MONTH_LABEL = {"june_dec": "June / December (report 48)", "july_jan": "July / January", "aug_feb": "August / February",
               "sept_mar": "September / March", "oct_apr": "October / April"}


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


def build():
    labels = list(R["month_names"].values())
    nif, gb = R["nifty"], R["gold_benchmark"]
    span = R["ema_span"]
    sym = R["currency_symbol"]

    filtered = {lbl: R[f"filtered_{lbl}"] for lbl in labels}
    original = {lbl: R[f"original_{lbl}"] for lbl in labels}

    best_cagr_lbl = max(labels, key=lambda l: filtered[l]["cagr_pct"])
    best_dd_lbl = max(labels, key=lambda l: filtered[l]["max_drawdown_pct"])  # least negative = shallowest

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Report 48, Rebalance Month Offset</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 48's exact design — the {span}-day EMA regime filter, gold instead of cash — tested across five different semi-annual rebalance calendars: June/December (report 48's own convention), July/January, August/February, September/March, and October/April. Report 25 already tested this exact idea on the plain (no-filter) strategy; this asks whether the calendar offset matters once the gold-hedged regime filter is layered on top. Same continuous daily {span}-EMA regime check throughout — only the stock-selection calendar changes between the five variants.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#6AE4FF]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill("report 48's own June/December calendar is the SAFEST of the five, not the highest-CAGR one", 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Among the five gold-hedged variants, June/December has the SHALLOWEST drawdown
          (<span class="font-semibold">{pct(filtered['june_dec']['max_drawdown_pct'],1,signed=False)}</span>) — but also the
          LOWEST CAGR (<span class="font-semibold">{pct(filtered['june_dec']['cagr_pct'])}</span>) of the five. The best CAGR
          belongs to {esc(MONTH_LABEL[best_cagr_lbl])} ({pct(filtered[best_cagr_lbl]['cagr_pct'])}), at the cost of a
          deeper drawdown ({pct(filtered[best_cagr_lbl]['max_drawdown_pct'],1,signed=False)}).
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The spread here is real but not huge — CAGR ranges about 2 percentage points across all five calendars, and
          drawdown ranges about 2.6 points. This is a genuinely different, smaller-magnitude question than report 25's
          finding on the plain strategy, since the 200-EMA regime filter (identical daily signal in all five variants) is
          doing most of the risk-reduction work regardless of which two months the stock picks happen to refresh in.
        </p>
      </div>
    </div>
    """

    kpi_cols = [(MONTH_LABEL[lbl], pct(filtered[lbl]["cagr_pct"]), win_loss_kind(filtered[lbl]["cagr_pct"])) for lbl in labels]
    dd_cols = [(MONTH_LABEL[lbl], pct(filtered[lbl]["max_drawdown_pct"], 1, signed=False),
                "positive" if lbl == best_dd_lbl else "neutral") for lbl in labels]
    kpis = [
        kpi_card("CAGR by rebalance calendar — 200-EMA + gold", "Same continuous daily regime signal in all five; only the stock-refresh calendar differs.", kpi_cols),
        kpi_card("Max drawdown by rebalance calendar — 200-EMA + gold", "Largest peak-to-trough decline, identical window for every series.", dd_cols),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    filtered_rows = "".join(row(f"{MONTH_LABEL[lbl]} — 200-EMA + gold", filtered[lbl]) for lbl in labels)
    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All variants, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {filtered_rows}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    palette = [COL["positive"], COL["negative"], "#8B5CF6", COL["assumption"], "#6AE4FF"]
    eq_series = [{"name": MONTH_LABEL[lbl], "color": palette[i % len(palette)], "points": filtered[lbl]["equity_curve"]}
                 for i, lbl in enumerate(labels)]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_85")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each rebalance calendar, all with the 200-EMA + gold filter applied, linear axis, not log-scaled.</p>
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

    dd_series = [{"name": MONTH_LABEL[lbl], "color": palette[i % len(palette)], "points": dd_points(filtered[lbl]["equity_curve"])}
                 for i, lbl in enumerate(labels)]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_85")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all five track each other fairly closely — the 200-EMA regime signal (identical across all five) is doing most of the work; the calendar offset only nudges the result.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why the offset matters less here than it did for the plain strategy</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Report 25 found the rebalance calendar mattered for the PLAIN momentum strategy because with no regime filter,
        the stock-selection calendar is the ONLY lever determining when the portfolio reacts to changing conditions. Here,
        the 200-EMA regime filter reacts to NIFTY 50's close EVERY SINGLE DAY, completely independent of which two months
        the stock picks happen to refresh in — the calendar only controls which specific 10 stocks are held DURING an
        "on" stretch, not whether the strategy is exposed to the market at all. That's a smaller lever, which is why the
        spread here (about 2 points of CAGR, 2.6 of drawdown) is real but modest.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Report 48's June/December choice was inherited from this project's original momentum-formula convention (NSE's
        own semi-annual reconstitution cadence), not chosen for its risk/return profile specifically. This report shows
        that choice happens to land on the safest end of the offset spectrum, not the highest-return end — a reasonable
        trade to have made, even if not deliberately optimized for.
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
        <li class="mb-1.5">Only five of the six possible semi-annual offsets were tested (November/May was left out) —
        this doesn't claim June/December is provably the best OR worst of all six, just where it sits among these five.</li>
        <li class="mb-1.5">The common comparison window starts a little later than report 48's own ({esc(R['start_date'])}
        vs. report 48's 2009-01-02) because five different calendars each take a slightly different number of days to
        first reach a valid 252-day-lookback rebalance — the intersection of all five pushes the shared start date out.</li>
        <li class="mb-1.5">Zero transaction costs on any regime switch or scheduled rebalance — same disclosed omission
        as every other reconstruction here.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively across the whole window
        (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same
        as every other reconstruction here.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Report 48 Rebalance Month Offset</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("85_midcap150_report48_rebalance_month_offset.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 85_midcap150_report48_rebalance_month_offset.html")
