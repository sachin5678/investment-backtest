"""Builds 22_rsi70_monthly_rotation.html from results21.json. Same
self-contained contract, smooth Catmull-Rom charts, plus a participation
breakdown panel (cash/partial/full months) since this strategy can go to
100% cash in a given month if nothing qualifies."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results21.json") as f:
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
      .scrollbox{max-height:280px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
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
    rr, nif, midetf = R["rsi_rotation"], R["nifty"], R["midcap_etf"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Monthly RSI-70 Crossover Rotation</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Filter NIFTY 500 by market cap, catch stocks whose monthly RSI crosses above 70, hold the top 5 by RSI for a month, repeat — a classic technical-analysis signal, not the risk-adjusted momentum formula used elsewhere in this project.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {R['universe_size']}-stock universe, {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">Read this before the numbers below</h2>
          {pill('the market-cap filter turned out to be a no-op', 'negative')}{pill('crossing, not "is above"', 'assumption')}{pill('strong return, deep drawdown', 'neutral')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          The rule as described: filter Indian stocks by market cap above {sym}{R['min_cap_cr']:,.0f} Cr, then take stocks whose monthly RSI crosses
          above 70. This project's standing proxy for "the Indian market" is the NIFTY 500 (used in every earlier report needing a broad universe) —
          and it turns out <span class="font-semibold">every single one of the 500 constituents already has a market cap above
          {sym}{R['min_cap_cr']:,.0f} Cr today</span> ({R['eligible_after_mcap_filter']} of {R['universe_size']} passed the filter, {R['excluded_by_mcap_filter']} excluded).
          NIFTY 500 is already "the 500 largest listed companies" by construction, so a {sym}2,000 Cr floor doesn't bind on it at all — this filter would
          only matter on a universe that also included true small/micro-caps below the NIFTY 500 cutoff, which isn't available here. The result below is
          effectively "RSI-70 crossover across the whole NIFTY 500," not a large-cap-specific strategy.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          "RSI crossing above 70" is implemented as a genuine crossover event — RSI ends one month at or below 70, then ends the next month above 70 —
          not merely "RSI is currently above 70" (a much less selective, and different, condition). Where more than 5 stocks cross in a month, the top 5
          are picked by RSI value (highest first); the request's exact wording ("top five any random stocks") was ambiguous between ranking and random
          selection, and ranking by RSI value was the more decision-relevant reading.
        </p>
      </div>
    </div>
    """

    methodology_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — the exact rule being tested.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          {pill(f'RSI({R["rsi_period"]}), Wilder-smoothed, on MONTH-END closing prices', 'assumption')} — a slower-moving signal than daily RSI, deliberately.
          {pill('genuine crossover (¬above → above 70)', 'assumption')}, {pill(f'top {R["top_n"]} by RSI value', 'assumption')}, equal-weighted,
          bought at the close of each month's first trading day, held to the day before the next month's first trading day. If fewer than {R['top_n']}
          stocks cross in a month, however many did are held; if none cross, the account sits in {pill('100% cash that month', 'assumption')} (a judgment
          call — not specified in the request).
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("RSI-70 Rotation", pct(rr["net_return_pct"]), win_loss_kind(rr["net_return_pct"])),
                   ("NIFTY 50", pct(nif["net_return_pct"]), win_loss_kind(nif["net_return_pct"])),
                   ("Midcap 150 ETF", pct(midetf["net_return_pct"]), win_loss_kind(midetf["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate, identical window for all three.",
                  [("RSI-70 Rotation", pct(rr["cagr_pct"]), win_loss_kind(rr["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"])),
                   ("Midcap 150 ETF", pct(midetf["cagr_pct"]), win_loss_kind(midetf["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("RSI-70 Rotation", pct(rr["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap 150 ETF", pct(midetf["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("RSI-70 Rotation", f'{rr["longest_underwater_days"]:,}d', "neutral"),
                   ("NIFTY 50", f'{nif["longest_underwater_days"]:,}d', "neutral"),
                   ("Midcap 150 ETF", f'{midetf["longest_underwater_days"]:,}d', "neutral")]),
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
        {pill('grey rows = real, un-reconstructed benchmarks', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the RSI-70 rotation against NIFTY 50 and the real Midcap 150 ETF, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("RSI-70 Crossover Rotation (custom rule)", rr)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row("Midcap 150 ETF (real, tradable)", midetf, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "RSI-70 Rotation", "color": COL["positive"], "points": rr["equity_curve"]},
        {"name": "NIFTY 50 (real)", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
        {"name": "Midcap 150 ETF (real)", "color": COL["assumption"], "points": midetf["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_22")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the RSI rotation pulls well ahead of both passive benchmarks over the full window, but see the drawdown chart below before reading that as a clean win.</p>
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
        {"name": "RSI-70 Rotation", "color": COL["positive"], "points": dd_points(rr["equity_curve"])},
        {"name": "NIFTY 50 (real)", "color": COL["text"], "points": dd_points(nif["equity_curve"]), "dash": True},
        {"name": "Midcap 150 ETF (real)", "color": COL["assumption"], "points": dd_points(midetf["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_22")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the RSI rotation's worst drawdown ({pct(rr['max_drawdown_pct'],1,signed=False)}) is meaningfully deeper than both passive benchmarks' — chasing a technical breakout signal concentrates risk into whichever 5 names are currently hot, with no volatility- or trend-strength-adjustment the way this project's other momentum formula has.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    total = R["num_rebalances"]
    cash_pct = R["cash_months"] / total * 100
    partial_pct = R["partial_months"] / total * 100
    full_pct = R["full_months"] / total * 100

    participation_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">How often did the signal actually fire?</h3>
        {pill('this strategy can go to 100% cash', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — across all {total} monthly rebalances, how many stocks actually had a fresh RSI-70 crossover to invest in.</p>
      <div class="grid grid-cols-3 gap-4 mt-4">
        <div class="{PANEL_TIGHT}">
          <div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Full months (5 stocks)</div>
          <div class="kpi-val mono" style="color:{KIND_COLOR['positive']}">{R['full_months']} <span class="text-[13px] text-[#7E97A0] font-normal">({full_pct:.0f}%)</span></div>
        </div>
        <div class="{PANEL_TIGHT}">
          <div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Partial months (1-4 stocks)</div>
          <div class="kpi-val mono" style="color:{KIND_COLOR['assumption']}">{R['partial_months']} <span class="text-[13px] text-[#7E97A0] font-normal">({partial_pct:.0f}%)</span></div>
        </div>
        <div class="{PANEL_TIGHT}">
          <div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Cash months (0 stocks)</div>
          <div class="kpi-val mono" style="color:{KIND_COLOR['negative']}">{R['cash_months']} <span class="text-[13px] text-[#7E97A0] font-normal">({cash_pct:.1f}%)</span></div>
        </div>
      </div>
      <p class="text-[13px] text-[#C9D6DA] leading-relaxed mt-4">
        Average stocks held per month: <span class="font-semibold text-[#E6EDF0]">{R['avg_stocks_held']}</span> of {R['top_n']}. A fresh RSI-70 crossover
        somewhere in a 498-stock universe is common enough that the strategy is fully invested {full_pct:.0f}% of the time — cash months are rare, but
        the holding LIST itself can still turn over completely from one month to the next, since a "fresh crossover" this month says nothing about
        whether last month's picks still qualify.
      </p>
    </div>
    """

    def sel_rows(sample):
        rows = []
        for s in sample:
            tickers = ", ".join(f"{t.replace('.NS','')} ({s['rsi_values'].get(t,'—')})" for t in s["tickers"]) if s["tickers"] else "— (cash month)"
            rows.append(f"""<tr><td>{esc(s['date'])}</td><td>{s['num_crossed']}</td>
            <td class="text-left" style="text-align:left">{esc(tickers)}</td></tr>""")
        return "".join(rows)

    sel_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Sample rebalances — first 4 and last 4</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — which stocks crossed, how many qualified, and their RSI value at signal time (in parentheses), at the start and end of this backtest's history.</p>
      <div class="scrollbox"><table class="data-table">
        <thead><tr><th>Date</th><th>Stocks crossed</th><th style="text-align:left">Selected (RSI at signal)</th></tr></thead>
        <tbody>{sel_rows(R['selections_sample'])}</tbody></table></div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">How this compares to this project's best momentum result</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — RSI-70 crossover against the strongest reconstruction found so far in this project (Midcap150 Momentum 10, +40.6% CAGR, same NIFTY-adjacent Indian market).</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        RSI-70 crossover landed at {pct(rr['cagr_pct'])} CAGR here — a real, substantial edge over both passive benchmarks, but well short of the
        6m/12m risk-adjusted momentum formula's {pct(40.6)} on Midcap150 Momentum-10, and with a deeper max drawdown
        ({pct(rr['max_drawdown_pct'],1,signed=False)} vs. -35.1%). The mechanism difference is instructive: the risk-adjusted formula ranks stocks by
        how much they've moved RELATIVE TO THEIR OWN VOLATILITY over 6-12 months, cross-sectionally — a continuous, comparative measure. RSI-70
        crossover is a binary trigger on a single stock's own recent price oscillation, with no cross-sectional ranking, no explicit trend-strength
        measure beyond the 0-100 oscillator band, and no volatility adjustment at all — a much blunter signal that can just as easily catch a stock
        in a short-lived spike as one in a durable uptrend.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        None of that makes RSI-70 crossover a bad rule on this data — it clearly beat doing nothing, by a wide margin. It just isn't the sharpest tool
        this project has tested for finding momentum in Indian equities.
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
        <li class="mb-1.5">The {sym}2,000 Cr market-cap filter is a NO-OP on the NIFTY 500 universe used here — it excludes 0 of 498 stocks (see the lead disclosure). This is effectively an unfiltered NIFTY 500 RSI screen, not a large-cap-specific one.</li>
        <li class="mb-1.5">Market cap itself is a single present-day snapshot (no historical point-in-time market cap data exists in this project) — moot here since the filter doesn't bind, but the same limitation as every quality/sector report in this series.</li>
        <li class="mb-1.5">"Crossing above 70" was interpreted as a genuine crossover event, not "RSI is currently above 70" — a materially different, and more selective, reading of the request.</li>
        <li class="mb-1.5">RSI period (14) was not specified in the request — 14 is the near-universal default for RSI, used here as the most defensible assumption, but untested against other lengths.</li>
        <li class="mb-1.5">"Top five any random stocks" was ambiguous — resolved here as "top 5 ranked by RSI value," not literal random selection.</li>
        <li class="mb-1.5">Survivorship bias — today's fixed NIFTY 500 constituent list, applied retroactively to 2008, same as every reconstruction in this project.</li>
        <li class="mb-1.5">Equal-weighted; no F&O-eligibility screen.</li>
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Zero transaction costs, slippage, or taxes modeled</span> — worth flagging given up to 5 positions can turn over completely every single month across {R['num_rebalances']} rebalances.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for any series shown.</li>
        <li class="mb-1.5">This is a single, fixed historical path — no out-of-sample validation of the RSI(14)/70 threshold combination specifically.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    {methodology_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      {full_table}
      {eq_panel}
      {dd_panel}
      {participation_panel}
      {sel_table}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Monthly RSI-70 Crossover Rotation</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("22_rsi70_monthly_rotation.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 22_rsi70_monthly_rotation.html")
