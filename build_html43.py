"""Builds 43_nifty500_momentum10_200ema_regime_filter.html from
results42.json. Same self-contained contract as report 42, smooth
Catmull-Rom charts, dark palette."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results42.json") as f:
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
    orig, fl, nif = R["original"], R["filtered"], R["nifty"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">NIFTY500 Momentum 10 — 200-Day EMA Regime Filter on NIFTY 50</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 42 tested holding a top-10 momentum portfolio only while NIFTY 50 is above its own 200-day EMA, sitting fully in cash otherwise. This applies the IDENTICAL filter mechanics to report 18's NIFTY500 Momentum 10 (500-stock universe) — a second, much broader data point on whether the filter's small-CAGR-cost-for-big-drawdown-cut pattern generalizes.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#37F083]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('same shape of result as Midcap150 (report 42)', 'positive')}
          {pill(f"{R['pct_time_in_cash']:.1f}% of trading days spent in cash", 'assumption')}
          {pill(f"{R['num_regime_reentries']} regime re-entries over 18 years", 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          On NIFTY500 Momentum 10, the filter again costs a little CAGR — {pct(orig['cagr_pct'])} to
          <span class="font-semibold">{pct(fl['cagr_pct'])}</span> — for a large drawdown improvement, from
          {pct(orig['max_drawdown_pct'],1,signed=False)} to <span class="font-semibold">{pct(fl['max_drawdown_pct'],1,signed=False)}</span>,
          about 8 percentage points shallower.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The regime signal itself is identical to report 42 — it's computed purely from NIFTY 50's own price, independent of
          which universe the momentum portfolio is drawn from — so the time-in-cash and re-entry counts are exactly the same
          ({R['pct_time_in_cash']:.1f}%, {R['num_regime_reentries']} re-entries) as Midcap150. Only the underlying portfolio being
          protected changes. See reports 44-45 for Smallcap250 and NIFTY100.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for all three.",
                  [("No filter (always invested)", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("200-EMA regime filter", pct(fl["cagr_pct"]), win_loss_kind(fl["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("No filter (always invested)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("200-EMA regime filter", pct(fl["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("No filter", pct(orig["net_return_pct"]), win_loss_kind(orig["net_return_pct"])),
                   ("200-EMA filter", pct(fl["net_return_pct"]), win_loss_kind(fl["net_return_pct"]))]),
        kpi_card("How active is the filter", "Time spent in cash, and how many times it switched back in without waiting for the schedule.",
                  [("Time in cash", f"{R['pct_time_in_cash']:.1f}%", "assumption"),
                   ("Regime re-entries", f"{R['num_regime_reentries']}", "assumption"),
                   ("Scheduled rebalances skipped (in cash)", f"{R['num_scheduled_rebalances_skipped_in_cash']} / {R['num_scheduled_rebalances_total']}", "neutral")]),
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
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the unfiltered and 200-EMA-filtered NIFTY500 Momentum 10 formulas against the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("NIFTY500 Momentum 10 — no filter (always invested)", orig)}
          {row("NIFTY500 Momentum 10 — 200-EMA regime filter", fl)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter (always invested)", "color": COL["negative"], "points": orig["equity_curve"]},
        {"name": "200-EMA regime filter", "color": COL["positive"], "points": fl["equity_curve"], "dash": True},
        {"name": "NIFTY 50", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_43")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each version, linear axis, not log-scaled.</p>
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
        {"name": "No filter (always invested)", "color": COL["negative"], "points": dd_points(orig["equity_curve"])},
        {"name": "200-EMA regime filter", "color": COL["positive"], "points": dd_points(fl["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_43")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the filtered strategy's drawdown ({pct(fl['max_drawdown_pct'],1,signed=False)}) is far shallower than the unfiltered version's ({pct(orig['max_drawdown_pct'],1,signed=False)}).</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def cash_row(b):
        return f"""<tr><td>{esc(b['start'])}</td><td>{esc(b['end'])}</td><td>{b['days']:,}d</td></tr>"""

    cash_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Longest stretches spent in cash</h3>
        {pill('periods of 10+ trading days shown', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — identical to report 42's list, since the regime signal is computed purely from NIFTY 50's own price, independent of the momentum universe being protected.</p>
      <table class="data-table">
        <thead><tr><th>Cash from</th><th>Cash until</th><th>Duration</th></tr></thead>
        <tbody>{''.join(cash_row(b) for b in R['cash_periods'])}</tbody>
      </table>
    </div>
    """

    def sel_row(s):
        trig_label = {"initial_entry": "initial entry", "scheduled_rebalance": "scheduled", "regime_reentry": "regime re-entry"}.get(s.get("trigger"), s.get("trigger", ""))
        return f"""<tr><td>{esc(s['date'])}</td><td>{pill(trig_label, 'assumption' if trig_label == 'regime re-entry' else 'neutral')}</td><td style="text-align:left">{esc(', '.join(s['tickers']))}</td></tr>"""

    selections_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample entries — first 3 and last 3</h3>
        {pill('note the "regime re-entry" rows — off the June/December schedule', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every time the filtered strategy actually bought a fresh top-10 out of NIFTY500's 500-stock universe.</p>
      <table class="data-table"><thead><tr><th>Date</th><th>Trigger</th><th style="text-align:left">Top 10 selected</th></tr></thead>
      <tbody>{''.join(sel_row(s) for s in R['filtered']['selections_sample'])}</tbody></table>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">A second universe, the same trade-off</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Unlike the front-loaded-momentum reformulation tested in reports 37-41 — which HELPED on broad universes and HURT on
        narrow ones — this regime filter doesn't depend on the momentum universe at all. It's a pure market-timing overlay on
        NIFTY 50's own price, so it protects whatever portfolio sits underneath it in roughly the same way: a modest CAGR give-up
        for a large cut to max drawdown. NIFTY500's slightly smaller drawdown improvement here (8 points vs. Midcap150's ~12) is
        mostly because NIFTY500 Momentum 10's OWN unfiltered drawdown ({pct(orig['max_drawdown_pct'],1,signed=False)}) already
        overlaps more with NIFTY 50's own decline pattern than Midcap150's does.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The same {R['num_regime_reentries']}-re-entries-vs-{R['num_scheduled_rebalances_total']}-scheduled-rebalances whipsaw cost
        from report 42 applies here unchanged — this backtest still charges zero for every one of those switches, and the real
        gap between filtered and unfiltered CAGR would be smaller once realistic transaction costs are included.
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
        <li class="mb-1.5">Zero transaction costs on ANY regime switch — {R['num_regime_reentries']} re-entries over 18 years, all free in this model (see report 42's honesty note).</li>
        <li class="mb-1.5">Cash earns exactly 0% while the filter is out of the market, same convention as reports 03 and 42.</li>
        <li class="mb-1.5">The regime signal and the strategy's own execution both act on the SAME day's close — no next-day execution lag modeled.</li>
        <li class="mb-1.5">Only ONE EMA span (200 trading days) is tested here — see report 46 for a span-sensitivity comparison.</li>
        <li class="mb-1.5">Today's fixed NIFTY500 constituent list is applied retroactively across the whole window (survivorship bias), same disclosed approximation as report 18 and every other reconstruction here.</li>
        <li class="mb-1.5">Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other reconstruction in this project. This is a single, fixed 18-year historical path.</li>
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
      {cash_panel}
      {selections_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>NIFTY500 Momentum 10 — 200-EMA Regime Filter</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("43_nifty500_momentum10_200ema_regime_filter.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 43_nifty500_momentum10_200ema_regime_filter.html")
