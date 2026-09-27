"""Builds 71_midcap_momentum10_core_satellite_gold.html from results70.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results70.json") as f:
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
    orig, combo, nif, gb = R["original"], R["combo"], R["nifty"], R["gold_benchmark"]
    sym = R["currency_symbol"]
    mw, hw = R["on_momentum_weight_pct"], R["on_hedge_weight_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — {mw:.0f}/{hw:.0f} Core-Satellite with Gold, Full Flight-to-Gold on Regime Change</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Every earlier gold report (14, 20, 48, 68) only used gold as a substitute for CASH — a hedge that only shows up when the 200-EMA filter is already risk-off. This report tests something structurally different: gold as a PERMANENT {hw:.0f}% satellite sleeve sitting alongside the momentum portfolio at all times, even in a healthy bull market, plus a full 100%-to-gold switch (selling the entire {mw:.0f}% momentum sleeve too, not just topping up the satellite) the moment NIFTY 50 closes below its own 200-day EMA. Same immediate-switch signal as report 42 — no confirmation delay, no wider span, no breadth check.</p>
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
          {pill('by far the shallowest drawdown of any variant tested — at a real CAGR cost', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Permanently parking {hw:.0f}% in gold cuts max drawdown to <span class="font-semibold">{pct(combo['max_drawdown_pct'],1,signed=False)}</span> —
          shallower than every other combination tested on Midcap150, including report 48's binary filter+gold ({pct(-23.42,1,signed=False)})
          and report 68's smooth-exposure+gold ({pct(-26.69,1,signed=False)}). That protection is not free: CAGR comes in at
          <span class="font-semibold">{pct(combo['cagr_pct'])}</span>, below the unfiltered {pct(orig['cagr_pct'])} AND below every
          other filtered variant on this universe — the permanent {hw:.0f}% gold sleeve drags on returns in ordinary bull years too,
          not just during crashes, which a binary or smooth-exposure filter (100% momentum whenever the market is healthy) doesn't do.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          This is a genuine trade-off, not a strictly-worse or strictly-better result: pick this design over the others only if
          shaving the drawdown further matters more to you than the CAGR given up to get there.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for every series.",
                  [("No filter", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   (f"{mw:.0f}/{hw:.0f} core-satellite", pct(combo["cagr_pct"]), win_loss_kind(combo["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral"),
                   ("Gold alone", pct(gb["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline, identical window for every series.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   (f"{mw:.0f}/{hw:.0f} core-satellite", pct(combo["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Gold alone", pct(gb["max_drawdown_pct"], 1, signed=False), "neutral")]),
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
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Midcap150 Momentum 10 — no filter", orig)}
          {row(f"Midcap150 Momentum 10 — {mw:.0f}/{hw:.0f} core-satellite + full gold switch", combo)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    other_combos_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">How this stacks up against every other gold/filter design tried so far</h3>
        {pill('quoted from reports 42/48/68, not recomputed here', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all on the same Midcap150 universe, same 200-EMA signal, same 2008-2026 window.</p>
      <table class="data-table">
        <thead><tr><th>Design</th><th>CAGR</th><th>Max drawdown</th></tr></thead>
        <tbody>
          <tr><td>No filter</td><td>{pct(orig['cagr_pct'])}</td><td>{pct(orig['max_drawdown_pct'],1,signed=False)}</td></tr>
          <tr><td>Report 42 — binary 200-EMA filter + cash</td><td>{pct(38.55)}</td><td>{pct(-23.49,1,signed=False)}</td></tr>
          <tr><td>Report 48 — binary 200-EMA filter + gold</td><td>{pct(43.27)}</td><td>{pct(-23.42,1,signed=False)}</td></tr>
          <tr><td>Report 68 — smooth exposure (15% band) + gold</td><td>{pct(42.10)}</td><td>{pct(-26.69,1,signed=False)}</td></tr>
          <tr class="real-bench"><td>Report 71 — {mw:.0f}/{hw:.0f} core-satellite + full gold switch (this report)</td><td>{pct(combo['cagr_pct'])}</td><td>{pct(combo['max_drawdown_pct'],1,signed=False)}</td></tr>
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
        {"name": f"{mw:.0f}/{hw:.0f} core-satellite + full gold switch", "color": COL["positive"], "points": combo["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_71")
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
        {"name": "No filter", "color": COL["muted"], "points": dd_points(orig["equity_curve"]), "dash": True},
        {"name": f"{mw:.0f}/{hw:.0f} core-satellite + full gold switch", "color": COL["positive"], "points": dd_points(combo["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_71")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the permanent {hw:.0f}% gold sleeve visibly shallows every dip, not just the ones the regime filter catches.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    periods_rows = "".join(
        f"<tr><td>{esc(p['start'])} → {esc(p['end'])}</td><td>{p['days']:,}d</td></tr>"
        for p in R["gold_periods"]
    )
    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">How the switch behaves</h3>{pill('mechanism', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the plumbing behind the headline numbers.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Across the full window, the strategy spent <span class="font-semibold text-[#E6EDF0]">{R['pct_time_full_gold']:.1f}%</span> of
        its days in the full-gold state, switching regimes <span class="font-semibold text-[#E6EDF0]">{R['num_regime_reentries']}</span> times
        back into the {mw:.0f}/{hw:.0f} split — the exact same NIFTY 50 / 200-EMA signal and switch count as report 42's binary
        cash filter, so the timing of every switch here is already independently verified by that report. Between regime
        transitions, the {mw:.0f}/{hw:.0f} split is only re-targeted at the {R['num_scheduled_rebalances']} scheduled June/December
        rebalance dates that fell inside an "on" period — otherwise the momentum and gold sleeves are left to drift with their own
        returns, same convention as every other rebalance-based report here.
      </p>
      <p class="{WHAT_THIS_SHOWS} mb-1">Longest full-gold periods</p>
      <table class="data-table">
        <thead><tr><th>Period</th><th>Length</th></tr></thead>
        <tbody>{periods_rows}</tbody>
      </table>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why this design trades CAGR for a shallower drawdown</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Every earlier filter design (reports 42, 48, 68) is 100% momentum whenever the market is healthy, and only reaches for
        gold when the 200-EMA signal says risk-off. This design gives up some of that upside on purpose: {hw:.0f}% sits in gold
        EVEN during a strong bull run, so it participates less in the momentum portfolio's best years. That's exactly why its
        CAGR ({pct(combo['cagr_pct'])}) trails report 48's binary filter+gold ({pct(43.27)}) despite using the identical regime
        signal and an even more aggressive full-gold switch during risk-off — the cost shows up in the "on" years, not the "off" ones.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The payoff is a drawdown that is shallower in EVERY regime, not just the filtered ones — a genuinely different risk
        profile from "same upside, better downside," which is closer to what reports 48/68 offer. Whether that's a good trade
        depends entirely on whether the extra ~{orig['cagr_pct'] - combo['cagr_pct']:.1f} percentage points of CAGR given up here is worth
        the extra ~{combo['max_drawdown_pct'] - (-26.69):.1f} percentage points of drawdown protection over report 68's design — a
        judgment call this report can't make for you.
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
        <li class="mb-1.5">Zero transaction costs on any rebalance, regime switch, or the flight-to-gold liquidation itself — a real
        execution would pay brokerage + STT + slippage on selling the ENTIRE momentum sleeve at every regime change, which this
        design triggers more often (via the full liquidation) than a design that just tops up an existing gold sleeve.</li>
        <li class="mb-1.5">Only ONE split (70/30) and ONE EMA span (200 days, immediate switch, no confirmation delay) were tested here —
        the 70/30 ratio was specified directly, not optimized; a different split would trade CAGR against drawdown differently.</li>
        <li class="mb-1.5">GOLDBEES.NS tracks domestic gold prices in INR, which also move with the rupee's own exchange rate — a INR
        depreciation can lift GOLDBEES.NS even if USD gold is flat, a real but separate driver from "gold as a crisis hedge."</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively across the whole window (survivorship bias).
        Equal weighting within the momentum sleeve, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as
        every other reconstruction here.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    <div class="px-10 py-6">
      {kpi_grid}
      {full_table}
      {other_combos_table}
      {eq_panel}
      {dd_panel}
      {mechanism_note}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Core-Satellite + Gold</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("71_midcap_momentum10_core_satellite_gold.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 71_midcap_momentum10_core_satellite_gold.html")
