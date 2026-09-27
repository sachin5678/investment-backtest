"""Builds 72_midcap_momentum10_core_satellite_5050_gold.html from results71.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results71.json") as f:
    R = json.load(f)
with open("results70.json") as f:
    R70 = json.load(f)

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
    combo70 = R70["combo"]
    sym = R["currency_symbol"]
    mw, hw = R["on_momentum_weight_pct"], R["on_hedge_weight_pct"]
    mw70, hw70 = R70["on_momentum_weight_pct"], R70["on_hedge_weight_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — {mw:.0f}/{hw:.0f} Core-Satellite with Gold, Full Flight-to-Gold on Regime Change</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same design as report 71 — a permanent gold satellite sleeve held at all times, plus a full 100%-to-gold switch on the same 200-EMA signal — but with an even {mw:.0f}/{hw:.0f} split instead of report 71's {mw70:.0f}/{hw70:.0f}. This isolates exactly one question: does putting MORE of the portfolio into the permanent gold sleeve keep buying more drawdown protection, or does it run out of room to help?</p>
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
          {pill('the extra 20 points of gold buys zero extra drawdown protection', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Moving from a {mw70:.0f}/{hw70:.0f} split (report 71) to {mw:.0f}/{hw:.0f} cuts CAGR further, from
          <span class="font-semibold">{pct(combo70['cagr_pct'])}</span> to <span class="font-semibold">{pct(combo['cagr_pct'])}</span> —
          but max drawdown does NOT improve at all: both splits bottom out at the same
          <span class="font-semibold">{pct(combo['max_drawdown_pct'],1,signed=False)}</span>, matching to three decimal places.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The reason is mechanical, not a coincidence: this strategy's single worst drawdown ({esc(combo['max_drawdown_peak_date'])} to
          {esc(combo['max_drawdown_trough_date'])}) falls entirely INSIDE one of the full-gold periods, where both splits are 100% gold
          and therefore identical — the 70/30-vs-50/50 choice only matters during the "on" periods, and this particular worst drawdown
          isn't one of them. Paying more CAGR for a bigger permanent gold sleeve only helps if a future worst-case drawdown happens to
          strike DURING an "on" period instead — something this backtest can't predict.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for every series.",
                  [("No filter", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   (f"{mw70:.0f}/{hw70:.0f} (report 71)", pct(combo70["cagr_pct"]), win_loss_kind(combo70["cagr_pct"])),
                   (f"{mw:.0f}/{hw:.0f} (this report)", pct(combo["cagr_pct"]), win_loss_kind(combo["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline, identical window for every series.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   (f"{mw70:.0f}/{hw70:.0f} (report 71)", pct(combo70["max_drawdown_pct"], 1, signed=False), "positive"),
                   (f"{mw:.0f}/{hw:.0f} (this report)", pct(combo["max_drawdown_pct"], 1, signed=False), "positive"),
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
        <h3 class="text-base font-bold text-[#E6EDF0]">All five, side by side</h3>
        {pill('grey rows = real benchmarks, not reconstructions', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Midcap150 Momentum 10 — no filter", orig)}
          {row(f"Report 71 — {mw70:.0f}/{hw70:.0f} core-satellite + full gold switch", combo70)}
          {row(f"Midcap150 Momentum 10 — {mw:.0f}/{hw:.0f} core-satellite + full gold switch (this report)", combo)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("GOLDBEES.NS, buy & hold (real ETF)", gb, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
        {"name": f"{mw70:.0f}/{hw70:.0f} (report 71)", "color": COL["assumption"], "points": combo70["equity_curve"], "dash": True},
        {"name": f"{mw:.0f}/{hw:.0f} (this report)", "color": COL["positive"], "points": combo["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_72")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each version, linear axis, not log-scaled. The bigger gold sleeve ({mw:.0f}/{hw:.0f}) visibly trails the smaller one ({mw70:.0f}/{hw70:.0f}) almost everywhere it matters — the bull-market years.</p>
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
        {"name": f"{mw70:.0f}/{hw70:.0f} (report 71)", "color": COL["assumption"], "points": dd_points(combo70["equity_curve"]), "dash": True},
        {"name": f"{mw:.0f}/{hw:.0f} (this report)", "color": COL["positive"], "points": dd_points(combo["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_72")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the two lines diverge during "on" periods (different split, different momentum-sleeve exposure) but converge to the SAME depth whenever both are fully in gold — including at the single worst point of the whole window.</p>
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
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — identical plumbing to report 71 (same signal, same switch dates), only the split ratio differs.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The switch timing is byte-for-byte identical to report 71: <span class="font-semibold text-[#E6EDF0]">{R['pct_time_full_gold']:.1f}%</span> of
        days in the full-gold state, <span class="font-semibold text-[#E6EDF0]">{R['num_regime_reentries']}</span> regime re-entries, the same
        {R['num_scheduled_rebalances']} scheduled rebalance dates — because the underlying NIFTY 50 / 200-EMA signal doesn't depend on the
        split ratio at all. Only what happens WITHIN each "on" period (70/30 vs. 50/50 momentum-to-gold exposure) differs.
      </p>
      <p class="{WHAT_THIS_SHOWS} mb-1">Longest full-gold periods (identical to report 71)</p>
      <table class="data-table">
        <thead><tr><th>Period</th><th>Length</th></tr></thead>
        <tbody>{periods_rows}</tbody>
      </table>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why more gold didn't buy more protection here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        A bigger permanent gold sleeve can only shrink a drawdown that happens DURING an "on" period (when the split ratio is actually
        in effect) — it can do nothing to a drawdown that happens during a full-gold period, since both splits are 100% gold there by
        construction. This backtest's single worst drawdown ({esc(combo['max_drawdown_peak_date'])} to {esc(combo['max_drawdown_trough_date'])})
        happened to fall inside a full-gold stretch, so raising the gold sleeve from {hw70:.0f}% to {hw:.0f}% bought nothing against
        THAT specific drawdown — while still giving up {orig['cagr_pct'] - combo['cagr_pct']:.1f} percentage points of CAGR relative to
        the unfiltered strategy, more than report 71's {orig['cagr_pct'] - combo70['cagr_pct']:.1f} points.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This is a genuinely useful negative result: past a certain point, a bigger permanent satellite sleeve is not a dial you can turn
        to keep buying drawdown protection — whether it helps AT ALL depends on where in the market cycle the next real drawdown happens
        to strike, which is exactly the kind of thing a single historical backtest can't promise about the future.
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
        <li class="mb-1.5">Zero transaction costs on any rebalance, regime switch, or the flight-to-gold liquidation itself — same
        disclosed omission as report 71.</li>
        <li class="mb-1.5">Only TWO splits (70/30, 50/50) and ONE EMA span (200 days, immediate switch) have now been tested — both were
        specified directly, not optimized; this is two data points on a spectrum, not a proof that 50/50 is a local minimum or maximum
        of anything.</li>
        <li class="mb-1.5">The "identical max drawdown" finding above is specific to THIS window's particular sequence of events — a
        different historical window (or the real future) could easily have its worst drawdown fall during an "on" period instead, in
        which case a bigger gold sleeve WOULD have helped more. Don't generalize "more gold never helps drawdown" beyond this test.</li>
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
      {eq_panel}
      {dd_panel}
      {mechanism_note}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — 50/50 Core-Satellite + Gold</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("72_midcap_momentum10_core_satellite_5050_gold.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 72_midcap_momentum10_core_satellite_5050_gold.html")
