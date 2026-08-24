"""Builds 03_dip_buying.html from results2.json. Same self-contained contract as
build_html.py: Tailwind Play CDN, inline SVG charts (svg_charts.py), no chart/
backtesting libraries, dark palette, honesty rules (source-tagged figures,
amber ASSUMPTION pills, non-empty LIMITATIONS panel, zero-based axes)."""
import json
import html
import pandas as pd
from svg_charts import line_chart, area_underwater_chart, COL

with open("results2.json") as f:
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


def money(v, symbol, decimals=0):
    if v is None:
        return "—"
    sign = "-" if v < 0 else ""
    return f"{sign}{symbol}{abs(v):,.{decimals}f}"


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
      .scrollbox{max-height:420px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
      .kpi-val{font-size:26px;font-weight:700;letter-spacing:-0.01em;}
      tr.no-trigger td{color:#5C737A;}
      tr.in-progress td{color:#F2B03C;}
    </style>
    """


def header():
    return f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Wait-for-the-Dip — Annual Cash/NIFTY 50 Switch</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Sit in cash from 1 Jan; deploy 100% only if NIFTY 50 closes 10% below its year-start price; withdraw back to cash on 31 Dec. Repeats every year, compounding.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: daily OHLC (^NSEI, unadjusted) price data<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
            f'<div class="kpi-val mono" style="color:{color}">{value_str}</div></div>'
        )
    return f"""
    <div class="{PANEL_TIGHT}">
      <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
      <div class="{MUTED} mb-3">{definition}</div>
      <div class="flex gap-4">{''.join(col_html)}</div>
    </div>
    """


def dd_points(points):
    out, peak = [], None
    for d, v in points:
        peak = v if peak is None else max(peak, v)
        out.append([d, (v / peak - 1.0) * 100.0])
    return out


def build():
    sym = R["currency_symbol"]
    fr = R["variants"]["frictionless"]
    cl = R["variants"]["cost_loaded"]
    bh = R["benchmark"]
    sf, sc = fr["stats"], cl["stats"]

    total_days_deployed = sum(y["days_deployed"] for y in fr["years"] if y["triggered"])
    span_days = (pd.Timestamp(R["data_end"]) - pd.Timestamp(fr["start_date"])).days
    exposure_pct = total_days_deployed / span_days * 100.0

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — plain-English recap of the rule being tested.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          Every 1 January, the account starts the year <span class="font-semibold text-[#E6EDF0]">entirely in cash</span> (the prior year's ending
          balance carries forward — returns compound year to year). That year's <span class="font-semibold text-[#E6EDF0]">reference price</span> is
          NIFTY 50's close on the first trading day of the year. If, on any later day that year, the close falls to
          {pill("10% below that reference price", "assumption")}, <span class="font-semibold text-[#E6EDF0]">100% of the cash</span> is deployed —
          filled at the next day's open. The position is then held until the year's last trading day, where it is
          {pill("withdrawn at that day's close", "assumption")} ("31 Dec"), regardless of price. If the -10% level is never touched that year, the
          account simply sits in cash all year and earns 0% for it. Only one entry/exit cycle per year — a second dip after a rebound is not re-bought.
        </p>
      </div>
    </div>
    """

    kpis = []
    kpis.append(kpi_card(
        "Years covered / years triggered",
        f'{sf["num_years_total"]} closed calendar years ({esc(fr["start_date"][:4])}–{int(R["data_end"][:4])-1}). Current year {esc(R["data_end"][:4])} is still in progress and excluded here — see the year-by-year log below. "Triggered" means NIFTY actually closed 10% below its year-start price at some point that year.',
        [("Both variants", f'{sf["num_years_triggered"]} of {sf["num_years_total"]} ({sf["pct_years_triggered"]:.0f}%)', "neutral")],
    ))
    kpis.append(kpi_card(
        "Win rate (triggered years only)",
        "Of the years the strategy actually deployed cash, the share that ended the year with a net profit on the amount deployed.",
        [("Frictionless", pct(sf["win_rate"], 1, signed=False), win_loss_kind(1)),
         ("Cost-loaded", pct(sc["win_rate"], 1, signed=False), win_loss_kind(1))],
    ))
    kpis.append(kpi_card(
        "Average win / average loss (per triggered year)",
        "Mean % return on the deployed amount, split across winning and losing triggered years.",
        [("Frict. win / loss", f'{pct(sf["avg_win_pct"])} / {pct(sf["avg_loss_pct"])}', "neutral"),
         ("Cost win / loss", f'{pct(sc["avg_win_pct"])} / {pct(sc["avg_loss_pct"])}', "neutral")],
    ))
    kpis.append(kpi_card(
        "Net return",
        "Total % change in account equity across all closed years, including every year spent fully in cash earning nothing.",
        [("Frictionless", pct(fr["net_return_pct"]), win_loss_kind(fr["net_return_pct"])),
         ("Cost-loaded", pct(cl["net_return_pct"]), win_loss_kind(cl["net_return_pct"]))],
    ))
    kpis.append(kpi_card(
        "CAGR",
        "Compound annual growth rate over the actual closed-year span.",
        [("Frictionless", pct(fr["cagr_pct"]), win_loss_kind(fr["cagr_pct"])),
         ("Cost-loaded", pct(cl["cagr_pct"]), win_loss_kind(cl["cagr_pct"]))],
    ))
    kpis.append(kpi_card(
        "Max drawdown",
        f"Largest peak-to-trough decline of the account's own equity curve (not NIFTY's), in %. Occurred {esc(fr['max_drawdown_peak_date'])} → {esc(fr['max_drawdown_trough_date'])}: the account entered right before the 2008 Lehman crash and rode it down further intra-year than the eventual year-end 2008 print (-43.1%) shows.",
        [("Frictionless", pct(fr["max_drawdown_pct"], 1, signed=False), "negative"),
         ("Cost-loaded", pct(cl["max_drawdown_pct"], 1, signed=False), "negative")],
    ))
    kpis.append(kpi_card(
        "Longest time underwater",
        "Longest stretch, in calendar days, the account's equity stayed below a prior peak before a new all-time high.",
        [("Frictionless", f'{fr["longest_underwater_days"]:,} days', "neutral"),
         ("Cost-loaded", f'{cl["longest_underwater_days"]:,} days', "neutral")],
    ))
    kpis.append(kpi_card(
        f"Top-{sf['top_n']} years' profit contribution",
        f"Sum of the {sf['top_n']} best triggered years' P&L, divided by total net profit across all triggered years. Above 100% means the remaining triggered years were a net loss overall.",
        [("Frictionless", pct(sf["top_n_pct_of_profit"], 0, signed=False), "assumption"),
         ("Cost-loaded", pct(sc["top_n_pct_of_profit"], 0, signed=False), "assumption")],
    ))
    kpis.append(kpi_card(
        "Time actually invested",
        f"Of the {span_days:,} calendar days in the closed-year backtest span, the number of days the account actually held NIFTY rather than cash.",
        [("Both variants", f'{total_days_deployed:,} days ({exposure_pct:.0f}%)', "assumption")],
    ))

    kpi_grid = f'<div class="grid grid-cols-3 gap-4 mt-6">{"".join(kpis)}</div>'

    # comparison vs buy & hold
    def calmar(ret_cagr, mdd):
        return None if mdd == 0 else ret_cagr / abs(mdd)
    cal_fr = calmar(fr["cagr_pct"], fr["max_drawdown_pct"])
    cal_cl = calmar(cl["cagr_pct"], cl["max_drawdown_pct"])
    cal_bh = calmar(bh["cagr_pct"], bh["max_drawdown_pct"])

    def cmp_card(label, definition, values):
        cols = "".join(
            f'<div class="flex-1"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(n)}</div>'
            f'<div class="kpi-val mono" style="color:{KIND_COLOR[k]}">{v}</div></div>'
            for n, v, k in values
        )
        return f"""
        <div class="{PANEL_TIGHT}">
          <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
          <div class="{MUTED} mb-3">{definition}</div>
          <div class="flex gap-4">{cols}</div>
        </div>
        """

    cmp_cards = [
        cmp_card("Net return", "Same start date and starting balance for all three.",
                  [("Strategy — frictionless", pct(fr["net_return_pct"]), win_loss_kind(fr["net_return_pct"])),
                   ("Strategy — cost-loaded", pct(cl["net_return_pct"]), win_loss_kind(cl["net_return_pct"])),
                   ("Buy & hold", pct(bh["net_return_pct"]), win_loss_kind(bh["net_return_pct"]))]),
        cmp_card("CAGR", "Compound annual growth rate, identical date range for all three.",
                  [("Strategy — frictionless", pct(fr["cagr_pct"]), win_loss_kind(fr["cagr_pct"])),
                   ("Strategy — cost-loaded", pct(cl["cagr_pct"]), win_loss_kind(cl["cagr_pct"])),
                   ("Buy & hold", pct(bh["cagr_pct"]), win_loss_kind(bh["cagr_pct"]))]),
        cmp_card("Max drawdown", "Smaller (closer to 0%) is a shallower worst-case loss.",
                  [("Strategy — frictionless", pct(fr["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Strategy — cost-loaded", pct(cl["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Buy & hold", pct(bh["max_drawdown_pct"], 1, signed=False), "negative")]),
        cmp_card("Longest time underwater", "Longest stretch below a prior equity peak, in calendar days.",
                  [("Strategy — frictionless", f'{fr["longest_underwater_days"]:,} days', "neutral"),
                   ("Strategy — cost-loaded", f'{cl["longest_underwater_days"]:,} days', "neutral"),
                   ("Buy & hold", f'{bh["longest_underwater_days"]:,} days', "neutral")]),
        cmp_card("CAGR ÷ Max drawdown (risk-adjusted, added metric)",
                  "Not one of the requested metrics — an ASSUMPTION-tagged extra: annual growth per 1% of worst-case drawdown. Higher is more return per unit of pain; it does not make a low absolute return \"good\" by itself.",
                  [("Strategy — frictionless", f"{cal_fr:.2f}" if cal_fr is not None else "—", win_loss_kind(cal_fr)),
                   ("Strategy — cost-loaded", f"{cal_cl:.2f}" if cal_cl is not None else "—", win_loss_kind(cal_cl)),
                   ("Buy & hold", f"{cal_bh:.2f}" if cal_bh is not None else "—", win_loss_kind(cal_bh))]),
    ]
    cmp_grid = f'<div class="grid grid-cols-3 gap-4 mt-6">{"".join(cmp_cards)}</div><div class="mt-2">{pill("CAGR/MDD ratio is an added, non-requested metric", "assumption")}</div>'

    eq_series = [
        {"name": "Strategy — frictionless", "color": COL["positive"], "points": fr["equity_curve"]},
        {"name": "Strategy — cost-loaded", "color": COL["assumption"], "points": cl["equity_curve"], "dash": True},
        {"name": "Buy & hold", "color": COL["text"], "points": bh["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, y_prefix=sym, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_dip")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Equity curve — strategy vs. buy &amp; hold, {sym}{R['initial_capital']:,.0f} start ({esc(fr['start_date'])} to {esc(R['data_end'])})</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the account is in cash (flat line) most of the time; it only starts moving with the market during a triggered year, then flattens again once it withdraws at that year's close.</p>
      <div class="flex items-center mb-2">{eq_legend}</div>
      {eq_svg}
      <div class="{MUTED} mt-2">Buy &amp; hold: {sym}{R['initial_capital']:,.0f} invested at the open of {esc(bh['start_date'])} (price {money(bh['entry_price'], sym, 2)}), held with no rebalancing, no dividends reinvested — same convention as the strategy.</div>
    </div>
    """

    dd_series = [
        {"name": "Strategy — frictionless", "color": COL["positive"], "points": dd_points(fr["equity_curve"])},
        {"name": "Buy & hold", "color": COL["negative"], "points": dd_points(bh["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, chart_id="dd_dip")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — buy-and-hold's deep drawdowns are the cost of always being 100% invested; the strategy avoids most of that pain simply by mostly not being in the market, not because it times exits well.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    # year-by-year table
    rows = []
    for i, yf in enumerate(fr["years"]):
        yc = cl["years"][i]
        if yf["triggered"]:
            rows.append(f"""
            <tr>
              <td>{yf['year']}</td><td>Yes — dip touched</td>
              <td>{esc(yf['entry_date'])}</td><td>{money(yf['entry_price'], sym, 2)}</td>
              <td>{esc(yf['exit_date'])}</td><td>{money(yf['exit_price'], sym, 2)}</td>
              <td>{yf['days_deployed']}</td>
              <td style="color:{'#37F083' if yf['pnl']>0 else '#F2643C'}">{money(yf['pnl'], sym, 0)}</td>
              <td style="color:{'#37F083' if yf['pnl']>0 else '#F2643C'}">{pct(yf['return_pct'])}</td>
              <td style="color:{'#37F083' if yc['pnl']>0 else '#F2643C'}">{money(yc['pnl'], sym, 0)}</td>
              <td style="color:{'#37F083' if yc['pnl']>0 else '#F2643C'}">{pct(yc['return_pct'])}</td>
            </tr>""")
        else:
            rows.append(f"""
            <tr class="no-trigger">
              <td>{yf['year']}</td><td>No — stayed in cash</td>
              <td>—</td><td>—</td><td>—</td><td>—</td><td>0</td><td>{sym}0</td><td>0.0%</td><td>{sym}0</td><td>0.0%</td>
            </tr>""")

    ip = fr.get("in_progress_year")
    in_progress_row = ""
    if ip:
        if "entry_date" in ip:
            in_progress_row = f"""
            <tr class="in-progress">
              <td>{ip['year']}</td><td>In progress — deployed, not yet withdrawn</td>
              <td>{esc(ip['entry_date'])}</td><td>{money(ip['entry_price'], sym, 2)}</td>
              <td colspan="2">mark-to-market as of {esc(ip['as_of'])}: {money(ip['mark_to_market_value'], sym, 0)}</td>
              <td>—</td><td colspan="4">not a closed year — excluded from all statistics above</td>
            </tr>"""
        else:
            in_progress_row = f"""
            <tr class="in-progress">
              <td>{ip['year']}</td><td>In progress — {esc(ip['status'])}</td>
              <td colspan="8">as of {esc(ip['as_of'])} — not a closed year, excluded from all statistics above</td>
            </tr>"""

    years_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Year-by-year log</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every calendar year in the backtest: whether the -10% dip ever triggered, when it entered/exited, and the P&amp;L under both cost variants.</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Year</th><th>Dip triggered?</th><th>Entry</th><th>Entry px</th><th>Exit</th><th>Exit px</th>
        <th>Days deployed</th><th>P&amp;L (frict.)</th><th>Return % (frict.)</th><th>P&amp;L (cost-loaded)</th><th>Return % (cost-loaded)</th></tr></thead>
        <tbody>{''.join(rows)}{in_progress_row}</tbody>
      </table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Read this before concluding "the strategy works"</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanical reasons behind the headline numbers, stated plainly.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The strategy only deployed cash in {sf['num_years_triggered']} of {sf['num_years_total']} years ({sf['pct_years_triggered']:.0f}%), and even then only for part of
        each year — across the whole {esc(fr['start_date'])}–{esc(R['data_end'])} span it held NIFTY for {exposure_pct:.0f}% of the days and sat in cash
        for the rest. Net return ({pct(fr['net_return_pct'])} frictionless) is far below buy-and-hold ({pct(bh['net_return_pct'])}) largely because of that —
        most of the time, this account earned nothing while the market moved. Its max drawdown is also far shallower ({pct(fr['max_drawdown_pct'], 1, signed=False)} vs.
        {pct(bh['max_drawdown_pct'], 1, signed=False)}), but that is mostly a side effect of rarely being invested, not evidence the -10% trigger is a skillful timing
        signal — a scattering of just {sf['num_years_triggered']} events (2 of them losses) is a very small sample to draw a conclusion from either way.
        Also note the profit is heavily concentrated: the top {sf['top_n']} triggered years account for {pct(sf['top_n_pct_of_profit'], 0, signed=False)} of total net profit.
      </p>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the concrete ways this backtest can mislead you if taken at face value.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5">Only {sf['num_years_triggered']} triggered years exist in 18 years of history — any win rate, average win/loss, or top-year concentration figure above is computed on a very small sample and can shift sharply with one more or fewer event.</li>
        <li class="mb-1.5">"Down 10% from the year-start close" and "one entry per year" were both judgment calls confirmed with you in chat — a peak-to-date trigger, an intraday-low trigger, or allowing re-entry after a rebound-then-redip would all change results, possibly a lot.</li>
        <li class="mb-1.5">The entry fills at the next day's open (a reactive signal); the year-end exit is modelled at that day's own close (a scheduled, known-in-advance liquidation) — this is an intentional asymmetry, not an inconsistency, but it does mean the exit is not lagged the way the entry is.</li>
        <li class="mb-1.5">NIFTY 50 is the raw index level (^NSEI), not directly tradable — a real position would need futures, options, or an ETF, each with its own costs and tracking error not modelled here.</li>
        <li class="mb-1.5">The cost-loaded variant models only a flat 0.05% commission and a fixed one-tick slippage per fill — no bid-ask spread widening, no market impact, no India-specific transaction taxes (STT, stamp duty, GST on brokerage), no financing/borrow cost.</li>
        <li class="mb-1.5">Idle cash (all the time the account is not deployed — the large majority of the period) is assumed to earn <span class="font-semibold text-[#E6EDF0]">zero</span> interest. A real cash balance earning even a modest risk-free rate would materially change net return and CAGR here.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for either the strategy or the buy-and-hold benchmark.</li>
        <li class="mb-1.5">2007 (partial year) is excluded entirely since NIFTY 50's available price history starts mid-September 2007, so there is no real "1 Jan" reference price for it. {esc(str(R['data_end']))}'s year (2026) is in progress and excluded from every statistic above — it is shown only in the year-by-year log, marked-to-market.</li>
        <li class="mb-1.5">This is a single fixed rule tested once over history — there is no out-of-sample test and no check for whether "10%" or "one entry per year" happens to be curve-fit to this particular history.</li>
      </ul>
    </div>
    """

    body = f"""
    {header()}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      <h2 class="text-lg font-bold text-[#E6EDF0] mt-8 mb-1">Strategy vs. buy-and-hold benchmark</h2>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — same instrument, same start date, same starting balance: net return, CAGR, max drawdown and longest time underwater side by side.</p>
      {cmp_grid}
      {eq_panel}
      {dd_panel}
      {years_table}
      {honesty_note}
      <div class="mt-6">{limitations}</div>
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Wait-for-the-Dip — NIFTY 50 vs. Buy-and-Hold</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("03_dip_buying.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 03_dip_buying.html")
