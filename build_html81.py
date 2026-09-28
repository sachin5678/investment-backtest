"""Builds 81_midcap150_momentum10_averaging_down.html from results80.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

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
    plain, comp_avg = R["plain_compounding"], R["compounding_with_averaging"]
    base, avg, nif = R["baseline"], R["averaged"], R["nifty"]
    sym = R["currency_symbol"]
    drop1, drop2 = R["drop_1_pct"], R["drop_2_pct"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Averaging Down Within the Holding Period</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same top-10 momentum picks, same June/December rebalance, ONE continuous compounding portfolio — but instead of buying once and holding untouched, each stock's peak price since entry is tracked daily; the first time it falls {drop1:.0f}% below that peak, an equal-sized top-up is bought, and if it falls {drop2:.0f}% below peak, a second equal top-up follows. No new external money is used — every averaging buy is funded by trimming the OTHER 9 holdings proportionally, so the whole portfolio still compounds forward through every rebalance exactly like every other report here, and both variants get a single, directly comparable CAGR.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('averaging is basically a wash on CAGR, and makes the drawdown WORSE, not better', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          CAGR barely moves: <span class="font-semibold">{pct(plain['cagr_pct'])}</span> without averaging vs.
          <span class="font-semibold">{pct(comp_avg['cagr_pct'])}</span> with it — a difference of
          {abs(comp_avg['cagr_pct']-plain['cagr_pct']):.2f} percentage points, functionally noise over 18 years. Max
          drawdown, though, gets meaningfully WORSE: {pct(plain['max_drawdown_pct'],1,signed=False)} without averaging vs.
          <span class="font-semibold">{pct(comp_avg['max_drawdown_pct'],1,signed=False)}</span> with it.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The mechanism is exactly what you'd expect once you look at where the money for each top-up actually comes from:
          since no new cash enters this portfolio, buying more of a stock that's already down {drop1:.0f}-{drop2:.0f}% means
          SELLING a slice of the other 9 holdings — on average, the stocks that are doing BETTER — to fund it. That's
          selling strength to buy weakness, concentrating more of the portfolio into the position that's currently
          struggling, right when it's struggling. It roughly breaks even on return and makes the worst days worse.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — one compounding portfolio, no new capital", "Same picks, same prices — only the mid-period averaging rule differs.",
                  [("No averaging", pct(plain["cagr_pct"]), win_loss_kind(plain["cagr_pct"])),
                   (f"With averaging ({drop1:.0f}%/{drop2:.0f}%)", pct(comp_avg["cagr_pct"]), win_loss_kind(comp_avg["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown — one compounding portfolio", "Largest peak-to-trough decline, identical window for every series.",
                  [("No averaging", pct(plain["max_drawdown_pct"], 1, signed=False), "positive"),
                   (f"With averaging ({drop1:.0f}%/{drop2:.0f}%)", pct(comp_avg["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    unified_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All four numbers together — CAGR and XIRR, averaging on and off</h3>
        {pill('two different capital structures — not four independent results', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the compounding columns (main comparison above) and the periodic new-capital columns (appendix below), side by side in one place. Compare DOWN each column (averaging's effect within one capital structure) — comparing ACROSS from CAGR to XIRR mixes two different money-management rules, not just two metrics.</p>
      <table class="data-table">
        <thead><tr><th>Averaging</th><th>Compounding — CAGR</th><th>Compounding — Max DD</th><th>New capital — XIRR</th><th>New capital — money multiple</th></tr></thead>
        <tbody>
          <tr><td>Off</td><td>{pct(plain['cagr_pct'])}</td><td>{pct(plain['max_drawdown_pct'],1,signed=False)}</td>
              <td>{pct(base['xirr_pct'])}</td><td>{base['money_multiple']:.2f}x</td></tr>
          <tr><td>On ({drop1:.0f}%/{drop2:.0f}%)</td><td>{pct(comp_avg['cagr_pct'])}</td><td>{pct(comp_avg['max_drawdown_pct'],1,signed=False)}</td>
              <td>{pct(avg['xirr_pct'])}</td><td>{avg['money_multiple']:.2f}x</td></tr>
        </tbody>
      </table>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mt-3">
        Reading down the CAGR column: averaging is a wash ({pct(plain['cagr_pct'])} → {pct(comp_avg['cagr_pct'])}). Reading
        down the XIRR column: averaging looks like a clear win ({pct(base['xirr_pct'])} → {pct(avg['xirr_pct'])}). Both are
        computed correctly; they disagree because they're answering different questions — CAGR asks "does this rule help
        a single portfolio that never gets new money," XIRR asks "how efficiently was capital used, given that this
        version keeps receiving new money to fund each top-up." Reading ACROSS a row (e.g. comparing {pct(plain['cagr_pct'])}
        to {pct(base['xirr_pct'])} directly) isn't meaningful — those two numbers describe different strategies with the
        same stock picks, not the same strategy measured two ways.
      </p>
    </div>
    """

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
          {row("Midcap150 Momentum 10 — no averaging (flagship)", plain)}
          {row(f"Midcap150 Momentum 10 — averaging ({drop1:.0f}%/{drop2:.0f}%, funded by trimming other 9)", comp_avg)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No averaging", "color": COL["positive"], "points": plain["equity_curve"]},
        {"name": f"With averaging ({drop1:.0f}%/{drop2:.0f}%)", "color": COL["negative"], "points": comp_avg["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_81")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each version, linear axis, not log-scaled. The two lines track each other closely almost throughout.</p>
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
        {"name": "No averaging", "color": COL["positive"], "points": dd_points(plain["equity_curve"])},
        {"name": f"With averaging ({drop1:.0f}%/{drop2:.0f}%)", "color": COL["negative"], "points": dd_points(comp_avg["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_81")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — averaging's line dips visibly deeper at the worst points, exactly where concentrating more capital into an already-falling stock hurts most.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">How often the triggers actually fired</h3>{pill('mechanism', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — out of {avg['total_positions']} total stock-holding-periods (10 stocks × {R['num_rebalances']} rebalances). Trigger counts are identical between the compounding and periodic versions of this report — same signal, same picks, same prices.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The {drop1:.0f}%-from-peak trigger fired <span class="font-semibold text-[#E6EDF0]">{avg['trigger_once']}</span> times
        ({avg['trigger_once']/avg['total_positions']*100:.1f}% of all stock-periods) — a momentum pick pulling back
        {drop1:.0f}% from its own peak-since-entry within a single 6-month window is common, not rare, for these volatile
        midcap names. The deeper {drop2:.0f}% trigger fired <span class="font-semibold text-[#E6EDF0]">{avg['trigger_twice']}</span> times
        ({avg['trigger_twice']/avg['total_positions']*100:.1f}%) — a real minority of positions, but still frequent enough
        to matter for how much gets trimmed from the winners.
      </p>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why "sell winners to buy the loser" roughly breaks even, but hurts on the worst days</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        This project's momentum formula tends to pick stocks BECAUSE they've already risen a lot — that's the entire
        selection criterion. A pick that then falls {drop1:.0f}% from its post-purchase peak was, in this dataset, more
        often a pause within a continuing uptrend than the start of a real breakdown ({avg['trigger_once']} triggers out
        of {avg['total_positions']} positions is a LOT) — which is exactly why the CAGR effect nets out close to zero:
        money moved OUT of winners that mostly kept winning, and INTO a "loser" that mostly recovered anyway. Two
        roughly-offsetting costs, not a free lunch and not a disaster.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The drawdown cost is less forgiving: on the genuinely bad stretches — the ones that actually drive the portfolio's
        WORST days — concentrating more capital into the stock that's falling, funded by trimming the ones holding up
        better, is precisely the wrong trade at precisely the wrong moment. That's why max drawdown gets worse
        ({pct(plain['max_drawdown_pct'],1,signed=False)} → {pct(comp_avg['max_drawdown_pct'],1,signed=False)}) even though
        the average outcome (CAGR) barely changes — the cost of averaging down shows up disproportionately in the tail,
        not in the typical case.
      </p>
    </div>
    """

    appendix_note = f"""
    <div class="{PANEL} mt-6 border-[#8B5CF6]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Appendix — the same idea, funded with new capital instead</h3>{pill('secondary framing, XIRR-based', 'neutral')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — an earlier version of this analysis funded the averaging buys with fresh EXTERNAL capital each time (never trimming the other 9 holdings), which breaks compounding — no single CAGR applies, since new money keeps entering. That version is kept here for reference, measured the only way that's valid for a growing-capital-base structure: XIRR (money-weighted return), the same convention this project's report 4/20 already use for capital-injection strategies.</p>
      <table class="data-table">
        <thead><tr><th>Variant (new capital, periodic {money(R['base_alloc'],sym)}/stock calls)</th><th>Called</th><th>Returned</th><th>Multiple</th><th>XIRR</th><th>Worst cycle</th><th>Best cycle</th></tr></thead>
        <tbody>
          <tr><td>No averaging</td><td>{money(base['total_invested'],sym)}</td><td>{money(base['total_returned'],sym)}</td>
              <td>{base['money_multiple']:.2f}x</td><td>{pct(base['xirr_pct'])}</td>
              <td>{pct(base['worst_cycle_return_pct'])}</td><td>{pct(base['best_cycle_return_pct'])}</td></tr>
          <tr><td>With averaging ({drop1:.0f}% / {drop2:.0f}%)</td><td>{money(avg['total_invested'],sym)}</td><td>{money(avg['total_returned'],sym)}</td>
              <td>{avg['money_multiple']:.2f}x</td><td>{pct(avg['xirr_pct'])}</td>
              <td>{pct(avg['worst_cycle_return_pct'])}</td><td>{pct(avg['best_cycle_return_pct'])}</td></tr>
        </tbody>
      </table>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mt-3">
        Note this tells a DIFFERENT story from the main comparison above — XIRR goes up with averaging here
        ({pct(base['xirr_pct'])} → {pct(avg['xirr_pct'])}) instead of roughly flat. That's not a contradiction: with new
        capital, averaging never costs the other 9 positions anything, so there's no "sell winners to buy the loser" drag
        to offset the benefit of buying a dip. The main comparison above is the more realistic one if you're not planning
        to keep injecting fresh cash specifically to fund dip-buys — most real portfolios aren't.
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
        <li class="mb-1.5">Each averaging top-up is sized equal to the stock's ORIGINAL per-stock allocation at that
        rebalance (confirmed with the user before building) — a different sizing rule (e.g. half-sized top-ups) would
        change how much gets trimmed from the other 9 holdings and the resulting drag.</li>
        <li class="mb-1.5">When a top-up is triggered, the OTHER 9 holdings are trimmed proportionally to their current
        value to fund it — a different trimming rule (e.g. always sell the single biggest winner) would spread the cost
        differently across the portfolio.</li>
        <li class="mb-1.5">Zero transaction costs on any buy, sell, or trim — same disclosed omission as every other
        reconstruction here, but the averaging variant makes strictly more trades (every top-up is an extra buy AND an
        extra sell across the other 9 positions), so real-world costs would erode it more than the baseline.</li>
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
      {unified_table}
      {full_table}
      {eq_panel}
      {dd_panel}
      {mechanism_note}
      {honesty_note}
      {appendix_note}
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
