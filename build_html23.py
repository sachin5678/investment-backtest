"""Builds 23_gold_silver_momentum_rotation.html from results22.json. Same
self-contained contract, smooth Catmull-Rom charts, dark palette as every
other report in this project."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results22.json") as f:
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
ACCENT_2 = "#8B5CF6"


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
      tr.cash-row td{color:#7E97A0;}
      tr.both-row td{color:#37F083;}
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
    mom, gld, slv, static = R["gold_silver_momentum"], R["gld_buyhold"], R["slv_buyhold"], R["static_5050"]
    sym = R["currency_symbol"]
    mom_wins_return = mom["cagr_pct"] > static["cagr_pct"]
    mom_wins_dd = mom["max_drawdown_pct"] > static["max_drawdown_pct"]  # less negative = shallower

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Gold/Silver Absolute Momentum Rotation</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Hold gold and/or silver only while each metal's own risk-adjusted 6m/12m momentum is positive; exit that leg to cash the moment it turns negative. Checked and rebalanced monthly.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_rebalances']} monthly rebalances<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">The rule, and the honest result up front</h2>
          {pill('in cash ' + f"{R['cash_pct_of_months']:.0f}% of all months", 'neutral')}
          {pill('lags buy-and-hold gold on both return and drawdown', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Every month-end, gold (GLD) and silver (SLV) are each scored independently on the exact same risk-adjusted momentum formula used everywhere
          else in this project — 6-month and 12-month return divided by trailing 1-year volatility, averaged 0.5/0.5 — except here the score is judged
          against <span class="font-semibold">zero</span>, not against a broad universe's cross-sectional average (there are only two assets, too few
          for a cross-sectional Z-score to mean anything). A metal is held only while its own score is positive; the moment it turns negative, that
          leg exits fully to cash. Both can be held together (split 50/50 of invested capital), and both can be in cash together.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The honest result: this rule spent <span class="font-semibold">{R['cash_pct_of_months']:.1f}% of all months sitting in some cash</span>, yet
          still compounded at <span class="font-semibold">{pct(mom['cagr_pct'])}</span> — worse than simply buying and holding gold alone
          ({pct(gld['cagr_pct'])}), worse than a static 50/50 gold/silver blend rebalanced monthly ({pct(static['cagr_pct'])}), and its max drawdown
          ({pct(mom['max_drawdown_pct'],1,signed=False)}) is actually <span class="font-semibold">deeper</span> than gold's own buy-and-hold drawdown
          ({pct(gld['max_drawdown_pct'],1,signed=False)}). The exit-to-cash rule did not protect capital here — see the honesty note below for why.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Gold/Silver momentum (this idea)", pct(mom["net_return_pct"]), win_loss_kind(mom["net_return_pct"])),
                   ("GLD buy & hold", pct(gld["net_return_pct"]), win_loss_kind(gld["net_return_pct"])),
                   ("SLV buy & hold", pct(slv["net_return_pct"]), win_loss_kind(slv["net_return_pct"])),
                   ("Static 50/50 (monthly rebalance)", pct(static["net_return_pct"]), win_loss_kind(static["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate, identical window for all four.",
                  [("Gold/Silver momentum (this idea)", pct(mom["cagr_pct"]), win_loss_kind(mom["cagr_pct"])),
                   ("GLD buy & hold", pct(gld["cagr_pct"]), win_loss_kind(gld["cagr_pct"])),
                   ("SLV buy & hold", pct(slv["cagr_pct"]), win_loss_kind(slv["cagr_pct"])),
                   ("Static 50/50 (monthly rebalance)", pct(static["cagr_pct"]), win_loss_kind(static["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Gold/Silver momentum (this idea)", pct(mom["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("GLD buy & hold", pct(gld["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("SLV buy & hold", pct(slv["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Static 50/50 (monthly rebalance)", pct(static["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Time in cash / dual-held", "Share of all monthly rebalances spent fully in cash vs. holding both metals at once.",
                  [("Months fully in cash", f"{R['cash_pct_of_months']:.1f}%", "neutral"),
                   ("Months holding both metals", f"{R['both_pct_of_months']:.1f}%", "positive"),
                   ("Longest underwater (momentum)", f'{mom["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All four, side by side</h3>
        {pill('grey rows = single-asset reference lines, not the strategy', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the momentum rotation and the static 50/50 blend against the two underlying single assets, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Gold/Silver absolute momentum (this idea)", mom)}
          {row("GLD, bought once, buy & hold", gld, "real-bench")}
          {row("SLV, bought once, buy & hold", slv, "real-bench")}
          {row("Static 50/50, rebalanced monthly", static, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Gold/Silver momentum (this idea)", "color": COL["negative"], "points": mom["equity_curve"]},
        {"name": "GLD buy & hold", "color": COL["positive"], "points": gld["equity_curve"]},
        {"name": "SLV buy & hold", "color": ACCENT_2, "points": slv["equity_curve"], "dash": True},
        {"name": "Static 50/50 (monthly rebalance)", "color": COL["text"], "points": static["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_23")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — GLD buy-and-hold (green) pulls furthest ahead over the full window; the momentum rotation (red) spends long stretches visibly behind all three alternatives, not just at the end.</p>
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
        {"name": "Gold/Silver momentum (this idea)", "color": COL["negative"], "points": dd_points(mom["equity_curve"])},
        {"name": "GLD buy & hold", "color": COL["positive"], "points": dd_points(gld["equity_curve"])},
        {"name": "SLV buy & hold", "color": ACCENT_2, "points": dd_points(slv["equity_curve"]), "dash": True},
        {"name": "Static 50/50 (monthly rebalance)", "color": COL["text"], "points": dd_points(static["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_23")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the momentum rotation's drawdown ({pct(mom['max_drawdown_pct'],1,signed=False)}) is deeper than GLD's own buy-and-hold drawdown ({pct(gld['max_drawdown_pct'],1,signed=False)}), despite the exit-to-cash rule — the whipsaw cost during gold's choppy 2011-2019 stretch outweighed the cash protection.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_rows(sels):
        rows = []
        for s in sels:
            holding_label = " + ".join(s["holding"]) if s["holding"] != ["cash"] else "cash"
            cls = "cash-row" if s["holding"] == ["cash"] else ("both-row" if len(s["holding"]) == 2 else "")
            c = f' class="{cls}"' if cls else ""
            rows.append(f"""<tr{c}><td>{esc(s['date'])}</td><td>{s['gold_score']:+.2f}</td><td>{s['silver_score']:+.2f}</td><td style="text-align:left">{esc(holding_label)}</td></tr>""")
        return "".join(rows)

    selections_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample of monthly rebalances</h3>
        {pill('first 6 and last 6 of ' + str(R['num_rebalances']) + ' shown', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — each metal's momentum score at rebalance time (positive = held, negative = exited to cash) and the resulting position. Grey rows = fully in cash; green rows = holding both metals at once.</p>
      <div style="overflow-x:auto">
      <table class="data-table">
        <thead><tr><th>Date</th><th>Gold score</th><th>Silver score</th><th style="text-align:left">Position taken</th></tr></thead>
        <tbody>{sel_rows(R['selections_sample'])}</tbody>
      </table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why exiting to cash didn't protect capital here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Gold and silver are highly correlated — both are precious metals that mostly rise and fall together on the same macro drivers (real rates, the
        dollar, safe-haven demand). A momentum rule built for a broad, DIVERSE universe of 30-500+ stocks works because when one stock's trend breaks,
        dozens of others are usually still working — the portfolio rotates into what's left. With only two, highly correlated assets, there's rarely
        anywhere for the rule to rotate INTO; when momentum breaks, it mostly means both metals are entering a choppy patch together, and the
        rule's response is to sit in cash and wait rather than find a new leader.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        That shows up directly in the peak-to-trough dates: both the momentum rotation and GLD buy-and-hold peaked on the same day
        ({esc(mom['max_drawdown_peak_date'])}) — the start of gold's real 2011-2015 bear market. GLD's own drawdown bottomed and began recovering by
        {esc(gld['max_drawdown_trough_date'])}. The momentum rule's trough came much later, {esc(mom['max_drawdown_trough_date'])} — the monthly
        re-scoring kept flipping the position in and out of a genuinely choppy, directionless multi-year stretch (2015-2019) that a simple
        buy-and-hold just rode through without trading at all, each exit/re-entry realizing a small loss it didn't need to take.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The rule spent {R['cash_pct_of_months']:.1f}% of all months in some amount of cash — capital that earned zero return while it waited, on
        top of the whipsaw losses from re-entering. For two assets this
        correlated, being "always in whichever one is stronger" (relative momentum, never cash) or simply buying and holding both would very likely
        have beaten "get out and wait" — that's an untested alternative for a future report, not a claim proven here.
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
        <li class="mb-1.5">Only two assets are ever considered — there is no cash-substitute yield modeled (e.g. T-bill interest while sitting out), so every month in cash is treated as a flat 0% return, which flatters nothing and slightly understates any real-world cash allocation's return.</li>
        <li class="mb-1.5">GLD and SLV are USD-denominated, global spot-tracking ETFs — unlike every other report in this project, no INR conversion is applied anywhere; this is a USD strategy shown in USD terms, not a claim about what an Indian investor's rupee return would have been after FX movement.</li>
        <li class="mb-1.5">The momentum threshold is a fixed zero — untested alternatives (a small positive/negative buffer band to reduce whipsaw, or a longer lookback) could change how often the rule exits to cash and how the whipsaw cost above nets out.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, bid/ask spread, or taxes are modeled on any of the {R['num_rebalances']} monthly rebalance checks, even though many months triggered no actual trade (position unchanged from the prior month).</li>
        <li class="mb-1.5">SLV's own history only starts 2006-04-28, roughly 1.5 years after GLD's 2004-11-18 listing — the backtest window here starts once both have 12 full months of trailing history to score against (2007-05-31), not at either ETF's own inception.</li>
        <li class="mb-1.5">Prices are unadjusted close prices; GLD and SLV are physically-backed trusts with negligible dividend distributions, so this has minimal effect either way.</li>
        <li class="mb-1.5">This is a single, fixed 19-year historical path through one specific gold bull/bear/bull cycle — a different window could show the momentum rule performing very differently, in either direction.</li>
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
      {selections_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Gold/Silver Absolute Momentum Rotation</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("23_gold_silver_momentum_rotation.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 23_gold_silver_momentum_rotation.html")
