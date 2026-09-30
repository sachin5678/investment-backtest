"""Builds 88_midcap150_report48_execution_timing.html from results87.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results87.json") as f:
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
    same, next_ = R["same_day_close"], R["next_day_open"]
    nif, gb = R["nifty"], R["gold_benchmark"]
    span = R["ema_span"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Report 48, Execution Timing</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Two timing questions were asked; only one is actually testable with this project's data. Rebalancing at 3:00 PM instead of NSE's 3:30 PM close is NOT testable — every price in this project comes from yfinance's daily OHLC bars, and no intraday tick data exists anywhere here for an 18-year window; there's no honest way to conjure "the 3:00 PM price" from a daily Close, so that variant is skipped rather than faked. Filling the SCHEDULED semi-annual reselection at the next trading day's OPEN instead of the same day's close IS testable — real per-ticker Open prices are cached for the whole Midcap150 universe, confirmed directly before building this. Only the scheduled stock-pick refresh is delayed this way; the 200-EMA regime filter's own entries/exits into and out of gold are completely unchanged.</p>
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
          {pill('next-day-open execution costs a little CAGR, drawdown is unchanged', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Delaying the scheduled reselection to the next day's open drops CAGR from {pct(same['cagr_pct'])} to
          <span class="font-semibold">{pct(next_['cagr_pct'])}</span> — a real but small cost. Max drawdown is UNCHANGED:
          {pct(same['max_drawdown_pct'],1,signed=False)} either way.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The identical drawdown makes sense given what actually moved: only the SCHEDULED stock-pick refresh timing
          changed here — the 200-EMA regime filter's own switches into and out of gold, which every other report in this
          project has found to be the dominant driver of this design's drawdown protection, are completely unchanged.
          What's left to differ is purely which specific prices the twice-yearly stock refresh trades at, a smaller,
          CAGR-only lever — consistent with report 77's finding that this hero design's drawdown is mostly set by the
          regime signal, not by stock-selection timing details.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — execution timing", "Compound annual growth rate, identical window for every series.",
                  [("Same-day close (report 48)", pct(same["cagr_pct"]), win_loss_kind(same["cagr_pct"])),
                   ("Next-day open", pct(next_["cagr_pct"]), win_loss_kind(next_["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown — execution timing", "Largest peak-to-trough decline, identical window for every series.",
                  [("Same-day close (report 48)", pct(same["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("Next-day open", pct(next_["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
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
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window, {R['num_rebalances']} scheduled rebalance dates.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("200-EMA + gold — same-day close (report 48)", same)}
          {row("200-EMA + gold — scheduled refresh at next-day open", next_)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Same-day close (report 48)", "color": COL["positive"], "points": same["equity_curve"]},
        {"name": "Next-day open", "color": COL["negative"], "points": next_["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_88")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how ₹100 invested at the start of the window grew under each execution timing, linear axis, not log-scaled. The two lines track each other closely almost throughout.</p>
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
        {"name": "Same-day close (report 48)", "color": COL["positive"], "points": dd_points(same["equity_curve"])},
        {"name": "Next-day open", "color": COL["negative"], "points": dd_points(next_["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_88")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the two lines sit almost exactly on top of each other — the regime filter (unchanged in both) is doing all of the drawdown-shaping work here.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why the data can't answer the 3:00 PM question</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the honest limits of what a daily-bar backtest can and can't tell you.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Every single report in this project — 87 of them before this one — is built from yfinance's daily OHLC bars. A
        daily Close is exactly one number: NSE's actual closing print, decided by the exchange's closing auction around
        3:30 PM. There is no field anywhere in this project's cached data that represents "the price at 3:00 PM" or any
        other specific intraday moment — computing that would need real minute-level or tick-level historical data for
        ~150 stocks across 18 years, which isn't available from yfinance (its intraday endpoints only cover roughly the
        last 60 days) or any other source this project uses.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Rather than approximate "3:00 PM" with some invented rule (e.g. "average of high and close," which has no real
        basis), this report simply says so and moves on to the question that COULD be answered honestly with real data:
        next-day-open execution. If genuine intraday data becomes available for this project later, the 3:00 PM
        question would be straightforward to answer properly then.
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
        <li class="mb-1.5">Only the SCHEDULED semi-annual reselection's fill timing was delayed — regime entries/exits
        into and out of gold are completely unchanged (still same-day close), so this isolates one specific timing
        question rather than changing the whole strategy's execution model at once.</li>
        <li class="mb-1.5">If a regime exit/entry happens to fall on the exact day a scheduled rebalance was pending
        execution, the pending scheduled trade is simply cancelled (the regime switch takes priority) — a disclosed,
        reasonable but not the only possible tie-breaking rule.</li>
        <li class="mb-1.5">Zero transaction costs, no slippage beyond the close-vs-open price difference itself — same
        disclosed omission as every other reconstruction here.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Report 48 Execution Timing</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("88_midcap150_report48_execution_timing.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 88_midcap150_report48_execution_timing.html")
