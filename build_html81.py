"""Builds 81_midcap150_momentum10_averaging_down.html from results80.json."""
import json
import html
from svg_charts import line_chart, COL

with open("results80.json") as f:
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


def money(v, sym):
    return f"{sym}{v:,.0f}"


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
    base, avg, nif = R["baseline"], R["averaged"], R["nifty"]
    sym = R["currency_symbol"]
    drop1, drop2 = R["drop_1_pct"], R["drop_2_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Averaging Down Within the Holding Period</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same top-10 momentum picks, same June/December rebalance — but instead of buying once and holding untouched, each stock's peak price since entry is tracked daily; the first time it falls {drop1:.0f}% below that peak, an equal-sized top-up is bought with NEW capital, and if it falls {drop2:.0f}% below peak, a second equal top-up follows. Each 6-month cycle calls a fresh {sym}10-per-stock allocation and returns whatever it's worth at the next rebalance — a periodic capital-call model, not a compounding one, so both variants are measured with XIRR (money-weighted return), not CAGR.</p>
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
          {pill('XIRR looks better with averaging — but the total money multiple is actually slightly worse', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Averaging pushed XIRR up from {pct(base['xirr_pct'])} to <span class="font-semibold">{pct(avg['xirr_pct'])}</span> —
          but it also required deploying nearly twice the capital ({money(base['total_invested'],sym)} → {money(avg['total_invested'],sym)}
          over the same 18 years), and the MONEY MULTIPLE — total returned per rupee called, not annualized — actually went
          the other way: <span class="font-semibold">{base['money_multiple']:.2f}x</span> for the plain baseline vs.
          <span class="font-semibold">{avg['money_multiple']:.2f}x</span> with averaging.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Both numbers are real, and they're not contradicting each other — they're measuring different things. Averaging
          buys typically go in partway through a 6-month cycle, closer to the exit than the entry, so the SAME dollar of
          profit on that late-arriving capital compounds to a higher ANNUALIZED rate (XIRR) even though it represents a
          smaller total gain in absolute terms. Read XIRR as "how efficiently capital was used while it was deployed," and
          the money multiple as "how much profit you actually banked per rupee committed" — this report shows both because
          picking only one would tell a one-sided story.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("XIRR (money-weighted, annualized)", "The standard metric for capital called and returned at irregular times.",
                  [("No averaging", pct(base["xirr_pct"]), win_loss_kind(base["xirr_pct"])),
                   ("With averaging", pct(avg["xirr_pct"]), win_loss_kind(avg["xirr_pct"])),
                   ("NIFTY 50 CAGR (loose reference only)", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Money multiple — total returned per rupee called, NOT annualized", "Total realized + current open value, divided by total capital called.",
                  [("No averaging", f"{base['money_multiple']:.2f}x", win_loss_kind(base['money_multiple']-1)),
                   ("With averaging", f"{avg['money_multiple']:.2f}x", win_loss_kind(avg['money_multiple']-1))]),
        kpi_card("Total capital called over 18 years", f"{R['num_rebalances']} rebalance cycles, {sym}{R['base_alloc']:.0f} per stock per call.",
                  [("No averaging", money(base["total_invested"], sym), "neutral"),
                   ("With averaging", money(avg["total_invested"], sym), "neutral")]),
        kpi_card("Best / worst single 6-month cycle", "Each cycle's own return on its own called capital — the fair way to compare volatility here.",
                  [("No averaging — worst", pct(base["worst_cycle_return_pct"]), "negative"),
                   ("No averaging — best", pct(base["best_cycle_return_pct"]), "positive"),
                   ("With averaging — worst", pct(avg["worst_cycle_return_pct"]), "negative"),
                   ("With averaging — best", pct(avg["best_cycle_return_pct"]), "positive")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Side by side</h3>
        {pill('capital-call model — see the lead disclosure for why XIRR + money multiple, not CAGR', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every figure over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window, {R['num_rebalances']} rebalance cycles.</p>
      <table class="data-table">
        <thead><tr><th>Variant</th><th>Called</th><th>Returned</th><th>Multiple</th><th>XIRR</th><th>Worst cycle</th><th>Best cycle</th></tr></thead>
        <tbody>
          <tr><td>No averaging</td><td>{money(base['total_invested'],sym)}</td><td>{money(base['total_returned'],sym)}</td>
              <td>{base['money_multiple']:.2f}x</td><td>{pct(base['xirr_pct'])}</td>
              <td>{pct(base['worst_cycle_return_pct'])}</td><td>{pct(base['best_cycle_return_pct'])}</td></tr>
          <tr><td>With averaging ({drop1:.0f}% / {drop2:.0f}%)</td><td>{money(avg['total_invested'],sym)}</td><td>{money(avg['total_returned'],sym)}</td>
              <td>{avg['money_multiple']:.2f}x</td><td>{pct(avg['xirr_pct'])}</td>
              <td>{pct(avg['worst_cycle_return_pct'])}</td><td>{pct(avg['best_cycle_return_pct'])}</td></tr>
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No averaging — capital called (cumulative)", "color": COL["muted"], "points": base["invested_curve"], "dash": True},
        {"name": "With averaging — capital called (cumulative)", "color": COL["assumption"], "points": avg["invested_curve"], "dash": True},
        {"name": "No averaging — open position value", "color": COL["positive"], "points": base["value_curve"]},
        {"name": "With averaging — open position value", "color": COL["negative"], "points": avg["value_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_81")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Cumulative capital called vs. currently-open position value</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the dashed lines only ever climb (capital called is cumulative and never comes back down); the solid lines are the mark-to-market value of whichever cycle is CURRENTLY open, resetting to a small number every rebalance since each cycle's proceeds are realized, not carried forward. The gap between a solid line and its dashed counterpart is NOT a "loss" — it's simply capital already returned in earlier cycles.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">How often the triggers actually fired</h3>{pill('mechanism', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — out of {avg['total_positions']} total stock-holding-periods (10 stocks × {R['num_rebalances']} rebalances).</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The {drop1:.0f}%-from-peak trigger fired <span class="font-semibold text-[#E6EDF0]">{avg['trigger_once']}</span> times
        ({avg['trigger_once']/avg['total_positions']*100:.1f}% of all stock-periods) — a momentum pick pulling back
        {drop1:.0f}% from its own peak-since-entry within a single 6-month window is common, not rare, for these volatile
        midcap names. The deeper {drop2:.0f}% trigger fired <span class="font-semibold text-[#E6EDF0]">{avg['trigger_twice']}</span> times
        ({avg['trigger_twice']/avg['total_positions']*100:.1f}%) — a real minority of positions, but still frequent enough
        to matter for the capital-required comparison above.
      </p>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why the worst cycle got better and the best cycle got worse</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Averaging did exactly what averaging is supposed to do at the position level: the worst single cycle improved from
        {pct(base['worst_cycle_return_pct'])} to {pct(avg['worst_cycle_return_pct'])} — buying more at a lower price
        reduces the blended cost basis, so a partial recovery by cycle-end turns a smaller loss into a smaller-still loss.
        The cost is on the upside: the best cycle fell from {pct(base['best_cycle_return_pct'])} to
        {pct(avg['best_cycle_return_pct'])} — money that goes in late, after a pick has already run up and then pulled
        back, buys in at a worse (higher) price than the ORIGINAL entry would have captured on a stock that just kept
        rising without ever triggering a dip-buy. Averaging smooths the distribution of outcomes; it doesn't shift the
        average outcome for free.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The most important caveat: this project's fixed Midcap150 momentum formula tends to pick stocks BECAUSE they've
        already risen a lot — a strong recent uptrend is the whole selection criterion. A stock like that pulling back 15%
        or 30% from its post-purchase peak within 6 months, in this specific dataset, was more often a pause within a
        continuing uptrend than the start of a real breakdown ({avg['trigger_once']} triggers out of {avg['total_positions']}
        positions is a LOT). That pattern won't hold in every market regime — a -30% pullback in a genuine bear market is a
        very different signal than the same number during 2009's historic recovery rally, which dominates this window's
        earliest cycles.
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
        <li class="mb-1.5">Averaging buys use NEW, external capital (confirmed with the user before building) — not money
        taken from the other 9 positions. A version funded by trimming winners instead would show a different, likely
        worse, result (selling strength to buy weakness is a real cost this version doesn't pay).</li>
        <li class="mb-1.5">Each averaging top-up is sized equal to the original per-stock allocation (also confirmed
        before building) — a different sizing rule (e.g. half-sized top-ups) would change both the capital required and
        the blended-cost-basis effect.</li>
        <li class="mb-1.5">This is a periodic capital-call model (fixed {sym}10/stock called fresh every cycle, proceeds
        realized not compounded forward) specifically so the averaging effect could be isolated via XIRR — it is NOT
        directly comparable to this project's other CAGR-based Midcap150 Momentum 10 reports, which let profits compound
        forward instead of returning capital every 6 months.</li>
        <li class="mb-1.5">Zero transaction costs on any buy or sell, including the averaging top-ups themselves (which
        are, by construction, extra trades the no-averaging baseline never makes) — same disclosed omission as every
        other reconstruction here, but the averaging variant's real-world cost drag would be proportionally larger.</li>
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
      {mechanism_note}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Averaging Down</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("81_midcap150_momentum10_averaging_down.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 81_midcap150_momentum10_averaging_down.html")
