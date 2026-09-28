"""Builds 82_midcap150_momentum10_averaging_wider_triggers.html from results81.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results81.json") as f:
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
    plain, nif = R["plain"], R["nifty"]
    a1530, a2540 = R["averaging_15_30"], R["averaging_25_40"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Averaging With Wider Triggers (25%/40%)</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 81's compounding-with-averaging design (top-up funded by trimming the OTHER 9 holdings, one continuous portfolio, single CAGR) found 15%/30% averaging was roughly a CAGR wash but made drawdown meaningfully worse — because most 15% pullbacks in this dataset were pauses within a continuing uptrend, not real breakdowns, so trimming winners to fund the top-up mostly cost something for nothing. This report widens the triggers to 25% and 40% off peak-since-entry to see whether firing less often, on more genuine dips, changes that trade-off.</p>
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
          {pill('wider triggers flip the result — CAGR improves, and the drawdown cost shrinks', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          At 25%/40%, CAGR actually goes UP to <span class="font-semibold">{pct(a2540['cagr_pct'])}</span> — better than
          both the no-averaging baseline ({pct(plain['cagr_pct'])}) AND the tighter 15%/30% version ({pct(a1530['cagr_pct'])}).
          Drawdown is still slightly worse than no averaging ({pct(a2540['max_drawdown_pct'],1,signed=False)} vs.
          {pct(plain['max_drawdown_pct'],1,signed=False)}), but meaningfully better than 15%/30%'s
          {pct(a1530['max_drawdown_pct'],1,signed=False)}.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The mechanism lines up with report 81's own explanation: the 25%-from-peak trigger fired on only
          {a2540['trigger_once']} of {a2540['total_positions']} stock-periods ({a2540['trigger_once']/a2540['total_positions']*100:.1f}%),
          less than half as often as 15%'s {a1530['trigger_once']} ({a1530['trigger_once']/a1530['total_positions']*100:.1f}%).
          Firing less often means trimming the OTHER 9 (better-performing, on average) holdings less often too — less of the
          "sell strength to buy weakness" drag that made 15%/30% a net negative on the worst days.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR by trigger width", "One compounding portfolio, no new capital — same picks, only the trigger width differs.",
                  [("No averaging", pct(plain["cagr_pct"]), win_loss_kind(plain["cagr_pct"])),
                   ("Averaging 15%/30%", pct(a1530["cagr_pct"]), win_loss_kind(a1530["cagr_pct"])),
                   ("Averaging 25%/40%", pct(a2540["cagr_pct"]), win_loss_kind(a2540["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown by trigger width", "Largest peak-to-trough decline, identical window for every series.",
                  [("No averaging", pct(plain["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("Averaging 15%/30%", pct(a1530["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Averaging 25%/40%", pct(a2540["max_drawdown_pct"], 1, signed=False), "negative"),
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
        {pill('grey row = real benchmark, not a reconstruction', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window, {R['num_rebalances']} rebalances, one continuous compounding portfolio throughout.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Midcap150 Momentum 10 — no averaging", plain)}
          {row("Midcap150 Momentum 10 — averaging 15%/30%", a1530)}
          {row("Midcap150 Momentum 10 — averaging 25%/40%", a2540)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No averaging", "color": COL["muted"], "points": plain["equity_curve"], "dash": True},
        {"name": "Averaging 15%/30%", "color": COL["negative"], "points": a1530["equity_curve"]},
        {"name": "Averaging 25%/40%", "color": COL["positive"], "points": a2540["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_82")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how ₹100 invested at the start of the window grew under each trigger width, linear axis, not log-scaled.</p>
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
        {"name": "No averaging", "color": COL["muted"], "points": dd_points(plain["equity_curve"]), "dash": True},
        {"name": "Averaging 15%/30%", "color": COL["negative"], "points": dd_points(a1530["equity_curve"])},
        {"name": "Averaging 25%/40%", "color": COL["positive"], "points": dd_points(a2540["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_82")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — 25%/40%'s line sits between the other two almost throughout, shallower than 15%/30%'s at the worst points.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">How often each trigger width actually fired</h3>{pill('mechanism', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — out of {a1530['total_positions']} total stock-holding-periods (10 stocks × {R['num_rebalances']} rebalances) in both variants.</p>
      <table class="data-table">
        <thead><tr><th>Trigger set</th><th>1st trigger fired</th><th>2nd trigger fired</th></tr></thead>
        <tbody>
          <tr><td>15% / 30%</td><td>{a1530['trigger_once']} ({a1530['trigger_once']/a1530['total_positions']*100:.1f}%)</td>
              <td>{a1530['trigger_twice']} ({a1530['trigger_twice']/a1530['total_positions']*100:.1f}%)</td></tr>
          <tr><td>25% / 40%</td><td>{a2540['trigger_once']} ({a2540['trigger_once']/a2540['total_positions']*100:.1f}%)</td>
              <td>{a2540['trigger_twice']} ({a2540['trigger_twice']/a2540['total_positions']*100:.1f}%)</td></tr>
        </tbody>
      </table>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why being more selective about WHICH dips to buy paid off</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Report 81's core finding still applies: this formula picks stocks BECAUSE they've already risen a lot, and a
        pullback from a post-purchase peak is, more often than not, a pause rather than a breakdown. The 15% trigger fires
        on {a1530['trigger_once']/a1530['total_positions']*100:.0f}% of positions — it's reacting to completely normal,
        routine volatility for these names, and every one of those top-ups costs a real trim from the other 9 holdings.
        The 25% trigger fires on only {a2540['trigger_once']/a2540['total_positions']*100:.0f}% of positions — rare enough
        that when it DOES fire, it's more likely catching something genuinely unusual, worth averaging into.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This doesn't mean wider is always better — push the trigger too wide (say, 60%/80%) and it would almost never
        fire, converging back toward the plain no-averaging baseline by construction. Somewhere between "fires on
        routine noise" (15%/30%) and "essentially never fires" there's a width where averaging has the best chance of
        adding value, and this result suggests 25%/40% sits closer to that zone than 15%/30% does — not proof it's the
        optimal width, just evidence the direction of the adjustment mattered.
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
        <li class="mb-1.5">Only two trigger-width pairs have now been tested (15%/30% and 25%/40%) — this doesn't map the
        full curve between them, or confirm 25%/40% is a local optimum rather than just a better point than 15%/30%.</li>
        <li class="mb-1.5">Same averaging mechanics as report 81 throughout: top-up sized equal to the original per-stock
        allocation, funded by trimming the other 9 holdings proportionally, no new external capital.</li>
        <li class="mb-1.5">Zero transaction costs on any buy, sell, or trim — same disclosed omission as every other
        reconstruction here; both averaging variants trade strictly more than the no-averaging baseline.</li>
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
      {mechanism_note}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Averaging Wider Triggers</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("82_midcap150_momentum10_averaging_wider_triggers.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 82_midcap150_momentum10_averaging_wider_triggers.html")
