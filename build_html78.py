"""Builds 78_midcap150_report48_basket_size.html from results77.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results77.json") as f:
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
    o5, o10, o15 = R["original_top5"], R["original_top10"], R["original_top15"]
    f5, f10, f15 = R["filtered_top5"], R["filtered_top10"], R["filtered_top15"]
    nif, gb = R["nifty"], R["gold_benchmark"]
    sym = R["currency_symbol"]
    span = R["ema_span"]

    def filter_benefit_dd(o, f):
        return o["max_drawdown_pct"] - f["max_drawdown_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum — Report 48's Design at 5 and 15 Stocks</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 48's exact design — the {span}-day EMA regime filter, gold instead of cash — replicated at top-5 (more concentrated) and top-15 (a bit broader), either side of the top-10 hero design. Not the same question as report 73's top-50 test: this stays close enough to top-10 that either size could plausibly be an improvement, not an obvious break from "buy the strongest names."</p>
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
          {pill('the gold-hedge filter barely helps a 5-stock basket, but helps MORE than the hero design at 15 stocks', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          At top-5, the filter is nearly a non-event: drawdown goes from {pct(o5['max_drawdown_pct'],1,signed=False)} unfiltered to
          {pct(f5['max_drawdown_pct'],1,signed=False)} filtered — actually a hair WORSE, not better — and CAGR barely moves
          ({pct(o5['cagr_pct'])} to {pct(f5['cagr_pct'])}). At top-10 (report 48's own hero design) the filter earns its keep
          clearly: drawdown improves from {pct(o10['max_drawdown_pct'],1,signed=False)} to {pct(f10['max_drawdown_pct'],1,signed=False)}
          and CAGR actually goes UP ({pct(o10['cagr_pct'])} to {pct(f10['cagr_pct'])}). At top-15 the filter helps MORE still —
          drawdown improves from {pct(o15['max_drawdown_pct'],1,signed=False)} to {pct(f15['max_drawdown_pct'],1,signed=False)},
          the shallowest drawdown of all three basket sizes, filtered or not.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Likely reason: a 5-stock basket's worst drawdowns are driven more by stock-SPECIFIC blowups (a couple of names going
          badly wrong) than by the broad market regime NIFTY 50's own 200-EMA is built to detect — the filter can't protect
          against a risk it isn't watching for. A 10-15 stock basket's drawdowns are more diversified across names, so what's
          left over is closer to genuine market-wide risk, which is exactly what this filter is designed to catch.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — no filter vs. 200-EMA + gold, by basket size", "Compound annual growth rate, identical window for every series.",
                  [("Top-5 (no filter)", pct(o5["cagr_pct"]), win_loss_kind(o5["cagr_pct"])),
                   ("Top-5 + gold filter", pct(f5["cagr_pct"]), win_loss_kind(f5["cagr_pct"])),
                   ("Top-10 (no filter)", pct(o10["cagr_pct"]), win_loss_kind(o10["cagr_pct"])),
                   ("Top-10 + gold filter (report 48)", pct(f10["cagr_pct"]), win_loss_kind(f10["cagr_pct"])),
                   ("Top-15 (no filter)", pct(o15["cagr_pct"]), win_loss_kind(o15["cagr_pct"])),
                   ("Top-15 + gold filter", pct(f15["cagr_pct"]), win_loss_kind(f15["cagr_pct"]))]),
        kpi_card("Max drawdown — no filter vs. 200-EMA + gold, by basket size", "Largest peak-to-trough decline, identical window for every series.",
                  [("Top-5 (no filter)", pct(o5["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Top-5 + gold filter", pct(f5["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Top-10 (no filter)", pct(o10["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Top-10 + gold filter (report 48)", pct(f10["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("Top-15 (no filter)", pct(o15["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Top-15 + gold filter", pct(f15["max_drawdown_pct"], 1, signed=False), "positive")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All eight, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Top-5 — no filter", o5)}
          {row("Top-5 — 200-EMA + gold", f5)}
          {row("Top-10 — no filter", o10)}
          {row("Top-10 — 200-EMA + gold (report 48)", f10)}
          {row("Top-15 — no filter", o15)}
          {row("Top-15 — 200-EMA + gold", f15)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Top-5 + gold filter", "color": COL["negative"], "points": f5["equity_curve"]},
        {"name": "Top-10 + gold filter (report 48)", "color": COL["positive"], "points": f10["equity_curve"]},
        {"name": "Top-15 + gold filter", "color": "#8B5CF6", "points": f15["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_78")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each basket size, all filtered, linear axis, not log-scaled.</p>
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
        {"name": "Top-5 + gold filter", "color": COL["negative"], "points": dd_points(f5["equity_curve"])},
        {"name": "Top-10 + gold filter (report 48)", "color": COL["positive"], "points": dd_points(f10["equity_curve"])},
        {"name": "Top-15 + gold filter", "color": "#8B5CF6", "points": dd_points(f15["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_78")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison — all three filtered</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — top-5's line sits visibly deeper than top-10 and top-15's, despite all three sharing the exact same regime signal and switch timing.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why the filter's benefit depends on basket size</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The 200-EMA regime filter watches NIFTY 50 — a broad, 50-stock market barometer — and switches to gold when THAT
        signal says risk-off. This protects well against drawdowns that are actually driven by broad market conditions. A
        5-stock basket concentrates the portfolio enough that a single name (or two) having its own bad run — unrelated to
        whether the broad market is healthy — can drive a big chunk of the drawdown, and the filter has no way to see that
        coming: NIFTY 50 can be perfectly calm while one of your 5 stocks is falling apart on its own news.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Widening to 10 or 15 names dilutes any single stock's ability to dominate the drawdown, so what's LEFT over after
        diversification is increasingly the kind of broad, market-wide risk the filter is actually built to catch — which is
        exactly why the filter's benefit gets bigger, not smaller, from top-10 to top-15 here. This doesn't mean "always use
        more stocks" — report 73 already showed CAGR keeps falling well before top-50, since the formula's edge comes from
        concentrating in the strongest-ranked names. It means the regime filter's OWN benefit and the basket's own
        concentration trade off against each other in a way that isn't obvious from either number alone.
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
        <li class="mb-1.5">Only two basket sizes (5, 15) were tested either side of the top-10 hero design — this doesn't map
        the full CAGR/drawdown curve between them (e.g. top-7, top-12 weren't tested), and report 73 already covers the
        much-wider top-50 case separately.</li>
        <li class="mb-1.5">Equal weighting within each basket (each of the 5, 10, or 15 names gets an equal share at every
        rebalance) — a 5-stock basket is meaningfully more concentrated per-name (20% each) than a 15-stock one (~6.7% each),
        which is itself part of why their risk profiles differ, separate from the momentum-ranking effect discussed above.</li>
        <li class="mb-1.5">Zero transaction costs on any regime switch or scheduled rebalance — same disclosed omission as
        every other reconstruction here.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively across the whole window
        (survivorship bias). No F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other
        reconstruction here.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum — Report 48 Basket Size</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("78_midcap150_report48_basket_size.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 78_midcap150_report48_basket_size.html")
