"""Builds 15_midcap_momentum20_quarterly.html from results14.json. Same
self-contained contract, smooth Catmull-Rom charts."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results14.json") as f:
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
      .scrollbox{max-height:260px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
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
      <div class="flex gap-4 flex-wrap">{''.join(col_html)}</div>
    </div>
    """


def build():
    q = R["momentum20_quarterly"]
    s = R["momentum20_semiannual"]
    nif, mid = R["nifty"], R["midcap"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum-20 — Quarterly vs. Semi-Annual Rebalancing</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same custom top-20 selection from the last report, rebalanced every 3 months (Feb/May/Aug/Nov) instead of the real index's May/November cadence.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: Yahoo Finance daily OHLC for {R['universe_size']} NIFTY Midcap 150 constituents + ^NSEI + MID150BEES.NS<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">This is now two steps removed from anything NSE publishes</h2>
          {pill('not a real NSE product', 'negative')}{pill('survivorship bias', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          The last report's "Momentum-20" was already a custom variant of the real Nifty Midcap150 Momentum 50 index (top 20 instead of top 50). This
          report changes a second thing on top of that: rebalancing every 3 months instead of the real index's actual May/November schedule. There is no
          official quarterly version of this index to compare against — this is purely "what if we turned the dial on this one custom setup," not a test
          of any product that exists.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The same survivorship bias as every reconstruction in this series still applies — today's NIFTY Midcap 150 roster, used retroactively back to
          2008.
        </p>
      </div>
    </div>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — exactly what changed, and what stayed identical.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          Same universe (today's NIFTY Midcap 150), same formula (6m/12m risk-adjusted momentum, z-scored, asymmetrically normalised), same top-20
          selection, same equal-weighting. Only the rebalance calendar changed: {pill('last trading day of Feb/May/Aug/Nov', 'assumption')} — four times a
          year — instead of just May/November. {R['num_rebalances']} rebalances computed ({R['num_rebalances']//4} years × 4), same
          {esc(R['start_date'])}–{esc(R['end_date'])} window as the last report. No transaction costs are modelled for either cadence, so the extra
          turnover from rebalancing twice as often is invisible here — a real cost this comparison doesn't charge for.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100. Midcap ETF only from {esc(R['midcap_start_date'])} — shorter window.",
                  [("Quarterly (this report)", pct(q["net_return_pct"]), win_loss_kind(q["net_return_pct"])),
                   ("Semi-annual (last report)", pct(s["net_return_pct"]), win_loss_kind(s["net_return_pct"])),
                   ("NIFTY 50", pct(nif["net_return_pct"]), win_loss_kind(nif["net_return_pct"])),
                   ("Midcap ETF (shorter)", pct(mid["net_return_pct"]), win_loss_kind(mid["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate — same window caveat as above.",
                  [("Quarterly (this report)", pct(q["cagr_pct"]), win_loss_kind(q["cagr_pct"])),
                   ("Semi-annual (last report)", pct(s["cagr_pct"]), win_loss_kind(s["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"])),
                   ("Midcap ETF (shorter)", pct(mid["cagr_pct"]), win_loss_kind(mid["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline — same window caveat as above.",
                  [("Quarterly (this report)", pct(q["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Semi-annual (last report)", pct(s["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap ETF (shorter)", pct(mid["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("Quarterly (this report)", f'{q["longest_underwater_days"]:,}d', "neutral"),
                   ("Semi-annual (last report)", f'{s["longest_underwater_days"]:,}d', "neutral"),
                   ("NIFTY 50", f'{nif["longest_underwater_days"]:,}d', "neutral"),
                   ("Midcap ETF (shorter)", f'{mid["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    eq_series = [
        {"name": "Quarterly rebalance (this report)", "color": COL["positive"], "points": q["equity_curve"]},
        {"name": "Semi-annual rebalance (last report)", "color": COL["assumption"], "points": s["equity_curve"], "dash": True},
        {"name": "NIFTY 50 (actual)", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_q")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — quarterly rebalancing pulls slightly ahead of semi-annual by the end, but the two lines track closely for most of the period; this is a modest effect, not a transformation.</p>
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
        {"name": "Quarterly rebalance", "color": COL["positive"], "points": dd_points(q["equity_curve"])},
        {"name": "Semi-annual rebalance", "color": COL["assumption"], "points": dd_points(s["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_q")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — rebalancing more often gave a very slightly shallower worst drawdown too ({pct(q['max_drawdown_pct'],1,signed=False)} vs. {pct(s['max_drawdown_pct'],1,signed=False)}) — faster reaction to changing momentum can trim some downside, at the (unmodelled) cost of double the turnover.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    rows = []
    for sel in R["selections_sample"]:
        rows.append(f"""<tr><td>{esc(sel['date'])}</td><td class="text-left" style="text-align:left">{esc(', '.join(t.replace('.NS','') for t in sel['tickers']))}</td></tr>""")
    sel_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Sample rebalances — first 3 and last 3 of {R['num_rebalances']}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all 20 selected tickers each time, at a quarterly cadence.</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Rebalance date</th><th class="text-left" style="text-align:left">All 20 selected tickers</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
      </div>
    </div>
    """

    xirr_note_pos = q["cagr_pct"] - s["cagr_pct"]
    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Was it worth turning the dial?</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the direct answer to "what if we rebalanced every 3 months," net of what this comparison can't see.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Quarterly rebalancing added {xirr_note_pos:+.2f} percentage points of CAGR ({pct(q['cagr_pct'])} vs. {pct(s['cagr_pct'])}) and trimmed the worst
        drawdown slightly, using {R['num_rebalances']} rebalances instead of {R['num_rebalances']//2} over the same span — twice the portfolio turnover.
        Since this reconstruction models zero transaction costs anywhere, that comparison is unfairly generous to the more frequent schedule: in reality,
        doubling the number of full-portfolio reshuffles would cost real commission and slippage on every trade, which this report doesn't charge for. On
        the actual numbers shown, the gain is small enough that realistic trading costs could plausibly erase it — this result should be read as
        "roughly a wash, tilted slightly toward quarterly," not as "quarterly clearly wins."
      </p>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every simplification carried over from the last report, plus the new ones from this comparison.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">No transaction costs modelled</span> — the quarterly schedule's small edge is shown before any commission, slippage, or market-impact cost from the doubled turnover; a cost-loaded version could easily flip the comparison.</li>
        <li class="mb-1.5">Not a real index, and now doubly so — neither the top-20 selection nor the quarterly calendar exist at NSE.</li>
        <li class="mb-1.5">Survivorship bias — today's Midcap 150 roster, applied retroactively, unchanged from the last report's caveat.</li>
        <li class="mb-1.5">Equal-weighted, not free-float-market-cap × score; no F&O-eligibility screen; Feb/Aug rebalance dates are an arbitrary evenly-spaced insertion between the real index's actual May/November anchors, not derived from any published rule.</li>
        <li class="mb-1.5">Midcap ETF's comparison figures cover only {esc(R['midcap_start_date'])}–{esc(R['end_date'])} (its real trading history), not the full window used for the momentum reconstructions and NIFTY 50.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for any series shown.</li>
        <li class="mb-1.5">Only two rebalancing frequencies were tested (semi-annual, quarterly) — this is not a sweep, and monthly or annual rebalancing could show a different pattern entirely.</li>
        <li class="mb-1.5">The report was generated while today's date (24 August) itself falls inside one of the quarterly rebalance months — so the very last "rebalance" in the {R['num_rebalances']}-count is really a mid-August snapshot using whatever data exists so far, not a genuinely completed month like every rebalance before it. This affects only that one final data point.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      {eq_panel}
      {dd_panel}
      {sel_table}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum-20 — Quarterly Rebalance</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("15_midcap_momentum20_quarterly.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 15_midcap_momentum20_quarterly.html")
