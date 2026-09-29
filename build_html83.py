"""Builds 83_midcap150_momentum10_pyramiding_up.html from results82.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results82.json") as f:
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
    plain, pyr, nif = R["plain"], R["pyramiding"], R["nifty"]
    up1, up2 = R["up_1_pct"], R["up_2_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Pyramiding Up Instead of Averaging Down</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Reports 81/82 tested buying MORE of a stock as it falls (15-40% below its own peak-since-entry). This report reverses the idea: buy more of a stock as it RISES — the first time it closes {up1:.0f}% above its own buy price, top up with an amount equal to the original allocation; the first time it closes {up2:.0f}% above buy price, a second equal top-up follows. Same funding mechanism as 81/82 (trim the other 9 holdings proportionally, no new external capital, one continuous compounding portfolio, single CAGR) — the only thing that changes is the direction of the trigger.</p>
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
          {pill('buying more of a winner while it keeps winning beats buying more of a loser hoping it recovers', 'positive')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Pyramiding up lifts CAGR from {pct(plain['cagr_pct'])} to <span class="font-semibold">{pct(pyr['cagr_pct'])}</span> —
          a real, if modest, improvement — for only a small drawdown cost: {pct(plain['max_drawdown_pct'],1,signed=False)}
          without it vs. <span class="font-semibold">{pct(pyr['max_drawdown_pct'],1,signed=False)}</span> with it. That's a
          meaningfully BETTER trade-off than either down-side design tested in reports 81/82 — report 81's 15%/30%
          averaging-down was a CAGR wash with a bigger drawdown cost (-37.2%), and report 82's wider 25%/40% down-trigger
          beat this on CAGR (+42.1%) but at a deeper drawdown (-36.0%) than pyramiding up's -35.6%.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The mechanism makes sense given what this formula actually selects for: these are picks chosen BECAUSE they
          already rose a lot over the past 6-12 months. Buying more as that same trend continues is betting WITH the
          selection criterion; buying more as it reverses is betting AGAINST it. Pyramiding up is the more
          momentum-consistent of the two ideas, and it performs like it.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — this report vs. reports 81/82", "One compounding portfolio, no new capital — same picks, only the trigger rule differs.",
                  [("No overlay", pct(plain["cagr_pct"]), win_loss_kind(plain["cagr_pct"])),
                   (f"Pyramid up +{up1:.0f}%/+{up2:.0f}%", pct(pyr["cagr_pct"]), win_loss_kind(pyr["cagr_pct"])),
                   ("Report 81 — avg down 15%/30%", "+40.6%", "neutral"),
                   ("Report 82 — avg down 25%/40%", "+42.1%", "neutral")]),
        kpi_card("Max drawdown — this report vs. reports 81/82", "Largest peak-to-trough decline, identical window for every series.",
                  [("No overlay", pct(plain["max_drawdown_pct"], 1, signed=False), "positive"),
                   (f"Pyramid up +{up1:.0f}%/+{up2:.0f}%", pct(pyr["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("Report 81 — avg down 15%/30%", "-37.2%", "neutral"),
                   ("Report 82 — avg down 25%/40%", "-36.0%", "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Side by side</h3>
        {pill('grey row = real benchmark, not a reconstruction', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window, {R['num_rebalances']} rebalances, one continuous compounding portfolio throughout.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Midcap150 Momentum 10 — no overlay (flagship)", plain)}
          {row(f"Midcap150 Momentum 10 — pyramiding up (+{up1:.0f}%/+{up2:.0f}%)", pyr)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No overlay", "color": COL["muted"], "points": plain["equity_curve"], "dash": True},
        {"name": f"Pyramiding up +{up1:.0f}%/+{up2:.0f}%", "color": COL["positive"], "points": pyr["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_83")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how ₹100 invested at the start of the window grew under each version, linear axis, not log-scaled.</p>
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
        {"name": "No overlay", "color": COL["muted"], "points": dd_points(plain["equity_curve"]), "dash": True},
        {"name": f"Pyramiding up +{up1:.0f}%/+{up2:.0f}%", "color": COL["positive"], "points": dd_points(pyr["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_83")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the two lines track each other closely almost throughout — pyramiding up costs very little on the downside.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">How often the triggers actually fired</h3>{pill('mechanism', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — out of {pyr['total_positions']} total stock-holding-periods (10 stocks × {R['num_rebalances']} rebalances).</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The +{up1:.0f}% trigger fired <span class="font-semibold text-[#E6EDF0]">{pyr['trigger_once']}</span> times
        ({pyr['trigger_once']/pyr['total_positions']*100:.1f}% of all stock-periods) — a Midcap150 momentum pick rising
        another {up1:.0f}% within the SAME 6-month holding period it was already bought for having risen a lot is common,
        not rare, here. The +{up2:.0f}% trigger fired <span class="font-semibold text-[#E6EDF0]">{pyr['trigger_twice']}</span> times
        ({pyr['trigger_twice']/pyr['total_positions']*100:.1f}%) — still a substantial share of positions, higher than
        either down-side trigger in reports 81/82 fired at their respective second thresholds.
      </p>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why "buy more of what's working" fits this formula better than "buy more of what isn't"</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Every top-up in this report, like reports 81/82, is funded by trimming the OTHER 9 holdings — there's no free
        lunch, capital always comes from somewhere. The difference is WHICH stock gets the extra capital. Averaging down
        (81/82) moves money INTO the stock that's currently underperforming, funded by trimming the ones that are doing
        better. Pyramiding up moves money INTO the stock that's currently outperforming, funded by trimming the ones
        doing relatively worse (or at least less spectacularly well) — which is a bet more aligned with the momentum
        formula's own premise: recent strength tends to persist more often than it reverses, in this specific dataset.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This doesn't mean pyramiding up is "safe" — it still concentrates more capital into fewer names (whichever ones
        happen to be running hardest), which is a real concentration risk if a big winner reverses sharply AFTER the
        top-up rather than before it. The relatively small drawdown cost here ({pct(plain['max_drawdown_pct'],1,signed=False)}
        → {pct(pyr['max_drawdown_pct'],1,signed=False)}) reflects what happened in THIS specific 18-year window, not a
        guarantee that concentrating into recent winners is always low-risk.
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
        <li class="mb-1.5">The trigger reference is the FIXED entry (buy) price throughout the holding period, not a
        trailing peak like reports 81/82 use for the down-side — a stock that rises 20%, pulls back, then rises again
        past 20% would NOT re-trigger here (each trigger only fires once per position), by construction.</li>
        <li class="mb-1.5">Only one width pair (+20%/+40%) has been tested — this doesn't map the full curve of possible
        thresholds, or confirm this is an optimal pair rather than just a better one than reports 81/82's down-side design.</li>
        <li class="mb-1.5">Each top-up is sized equal to the original per-stock allocation, funded by trimming the other 9
        holdings proportionally — same convention as reports 81/82, for direct comparability.</li>
        <li class="mb-1.5">Zero transaction costs on any buy, sell, or trim — same disclosed omission as every other
        reconstruction here; pyramiding trades strictly more than the no-overlay baseline.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Pyramiding Up</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("83_midcap150_momentum10_pyramiding_up.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 83_midcap150_momentum10_pyramiding_up.html")
