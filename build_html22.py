"""Builds 22_rsi70_monthly_rotation.html from results21.json. Same
self-contained contract, smooth Catmull-Rom charts, plus a trade-level
stats panel (win rate, avg trade P&L, stop-loss vs. month-end exit split)
since this version trades at the position level, not in monthly batches."""
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
      tr.entry-row td{color:#37F083;}
      tr.exit-row td{color:#F2643C;}
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
          <p class="text-[#9FB4BB] text-sm mt-1">Any NSE stock above {sym}2,000 Cr market cap — enter the moment its monthly RSI crosses above 70, hold up to 5 positions at once, exit on a 15% stop or month-end, whichever comes first.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {R['universe_size']:,}-stock universe, {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">The rule, exactly as corrected</h2>
          {pill('real NSE universe, not NIFTY 500', 'positive')}{pill('any-day entry, per-position exit', 'assumption')}{pill('deep drawdown', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          {R['universe_note']}. Built from NSE's own official listed-equity list (2,296 EQ-series tickers), with today's market cap fetched per
          ticker — {R['universe_size']:,} qualify above {sym}{R['min_cap_cr']:,.0f} Cr, more than double the NIFTY 500's 498, because NIFTY 500 only
          ever holds the 500 largest names and misses a real population of smaller (but still {sym}2,000 Cr+) companies.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          "Monthly RSI" is checked EVERY trading day, not just once a month: it's Wilder(14) RSI on monthly closes, re-evaluated daily by treating
          each day's price as a stand-in for "this month's close so far." A stock enters the moment its RSI crosses above 70 — any day, no minimum
          pool required to start. Up to 5 positions are held at once; if more stocks cross on one day than there are open slots, the ones that fill
          the remaining slots are picked at random (not ranked). Each position exits independently on whichever comes first: a 15% drop from ITS OWN
          entry price, or the last trading day of the month it was entered in.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The stop-loss is checked against each day's LOW (not just the close) and fills at the day's OPEN if price already gapped past -15%
          overnight — an earlier version of this backtest checked only the close and let losses run to -80/-90% on gap days before the check ever
          fired. With this fix, the average stop-loss exit lands almost exactly on target (see the trade stats below).
        </p>
      </div>
    </div>
    """

    methodology_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — the exact rule being tested.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          {pill(f'RSI({R["rsi_period"]}), Wilder-smoothed, developing daily from monthly closes', 'assumption')},
          {pill('genuine crossover (¬above → above 70)', 'assumption')}, {pill(f'up to {R["max_positions"]} concurrent positions', 'assumption')},
          {pill('random pick among same-day multiple crossers', 'assumption')},
          {pill(f'{R["stop_loss_pct"]:.0f}% stop-loss OR month-end, whichever first', 'assumption')}. New entries are funded from whatever cash is
          currently uninvested, split equally among that day's new entries; existing positions are never rebalanced mid-flight.
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
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the RSI rotation pulls ahead of both passive benchmarks, but see the drawdown chart below before reading that as a clean win.</p>
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
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the RSI rotation's worst drawdown ({pct(rr['max_drawdown_pct'],1,signed=False)}) is nearly double both passive benchmarks' — expanding into smaller, more volatile companies (beyond NIFTY 500) brought in more opportunities but also meaningfully more tail risk.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    total_exits = R["num_exits"]
    stop_pct = R["stop_loss_exits"] / total_exits * 100 if total_exits else 0
    month_end_pct = R["month_end_exits"] / total_exits * 100 if total_exits else 0

    trade_stats_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Trade-level statistics</h3>
        {pill(f'{R["num_entries"]:,} entries over {esc(R["start_date"])}–{esc(R["end_date"])}', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every individual position's outcome, not just the portfolio-level equity curve above.</p>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
        <div class="{PANEL_TIGHT}">
          <div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Win rate</div>
          <div class="kpi-val mono" style="color:{KIND_COLOR['positive'] if R['win_rate_pct'] and R['win_rate_pct']>50 else KIND_COLOR['neutral']}">{R['win_rate_pct']}%</div>
        </div>
        <div class="{PANEL_TIGHT}">
          <div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Avg trade P&amp;L</div>
          <div class="kpi-val mono" style="color:{KIND_COLOR['positive'] if R['avg_trade_pnl_pct'] and R['avg_trade_pnl_pct']>0 else KIND_COLOR['negative']}">{pct(R['avg_trade_pnl_pct'],2)}</div>
        </div>
        <div class="{PANEL_TIGHT}">
          <div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Stop-loss exits</div>
          <div class="kpi-val mono" style="color:{KIND_COLOR['negative']}">{R['stop_loss_exits']:,} <span class="text-[13px] text-[#7E97A0] font-normal">({stop_pct:.0f}%)</span></div>
        </div>
        <div class="{PANEL_TIGHT}">
          <div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Month-end exits</div>
          <div class="kpi-val mono" style="color:{KIND_COLOR['neutral']}">{R['month_end_exits']:,} <span class="text-[13px] text-[#7E97A0] font-normal">({month_end_pct:.0f}%)</span></div>
        </div>
      </div>
      <p class="text-[13px] text-[#C9D6DA] leading-relaxed mt-4">
        A win rate just above 51% with a positive average trade — the strategy is right slightly more often than not, and its wins outweigh its
        losses on average. {R['stop_loss_exits']:,} of {total_exits:,} exits ({stop_pct:.0f}%) were stopped out at -15%; the rest ({month_end_pct:.0f}%)
        rode to their own month-end, for better or worse.
      </p>
    </div>
    """

    def sel_rows(sample):
        rows = []
        for e in sample:
            if e["event"] == "entry":
                rows.append(f"""<tr class="entry-row"><td>{esc(e['date'])}</td><td>Entry</td>
                <td class="text-left" style="text-align:left">{esc(e['ticker'].replace('.NS',''))} @ {sym}{e['entry_price']:,.2f} ({e['num_crossed_today']} crossed, {e['num_slots_open']} open slots)</td></tr>""")
            else:
                reason = "15% stop" if e["reason"] == "stop_loss_15pct" else "month-end"
                rows.append(f"""<tr class="exit-row"><td>{esc(e['date'])}</td><td>Exit ({reason})</td>
                <td class="text-left" style="text-align:left">{esc(e['ticker'].replace('.NS',''))} @ {sym}{e['exit_price']:,.2f} — {pct(e['pnl_pct'],2)}</td></tr>""")
        return "".join(rows)

    sel_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Sample trades — first 10 and last 10</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the earliest and most recent individual entries and exits, in chronological order.</p>
      <div class="scrollbox"><table class="data-table">
        <thead><tr><th>Date</th><th>Event</th><th style="text-align:left">Detail</th></tr></thead>
        <tbody>{sel_rows(R['events_sample'])}</tbody></table></div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why the drawdown got worse when the universe got bigger</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the trade-off behind expanding from NIFTY 500 to the full qualifying NSE universe.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Restricted to NIFTY 500, this same rule produced a {pct(29.6)} CAGR with a -53.9% max drawdown (an earlier version of this report). Opened up
        to the full {R['universe_size']:,}-stock qualifying universe, CAGR is {pct(rr['cagr_pct'])} and the drawdown deepens to
        {pct(rr['max_drawdown_pct'],1,signed=False)}. More candidate stocks means more RSI-70 crossings to catch, which is exactly why you asked for
        the wider universe — but it also means the strategy now regularly holds smaller, less liquid, more volatile names that NIFTY 500 would have
        screened out. The stop-loss is doing real work here (average exit almost exactly -15%), but a handful of month-end exits still catch positions
        mid-decline in a genuinely sharp-moving stock before the stop can trigger.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        One trade is worth naming directly: <span class="font-semibold text-[#E6EDF0]">Vedanta (VEDL)</span> was stopped out at -57.9% on 2026-04-30 —
        far beyond the intended -15% — because Vedanta's 2025/26 corporate demerger caused a genuine, real (not a data error) ~58% one-day drop in its
        own continuing share price as value split off into newly-listed entities. This backtest has no way to credit the value of shares received in a
        demerger, so a real event like this shows up as a pure loss here even though a real shareholder would also have received new shares elsewhere.
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
        <li class="mb-1.5">Market cap is a single present-day snapshot (no historical point-in-time market cap data exists in this project) — a stock that grew into or fell below the {sym}2,000 Cr line at some point in the past is still judged by TODAY's market cap for the whole 2008-2026 history.</li>
        <li class="mb-1.5">321 of 2,296 NSE EQ-series tickers never returned a market cap even after repeated retries and are excluded from the universe entirely, rather than guessed at — a small, disclosed coverage gap, not a judgment that they don't qualify.</li>
        <li class="mb-1.5">No adjustment for corporate actions (demergers, spin-offs, bonus issues) beyond whatever the raw price series already reflects — see the Vedanta example above. A handful of other extreme single-day moves in this dataset are very likely real corporate actions or crashes (e.g. the 2008 Bajaj Auto/Finserv/Holdings demerger, Yes Bank's 2020 moratorium) rather than data errors, but none were individually verified beyond the one named here.</li>
        <li class="mb-1.5">RSI period (14) was not specified in the original request — 14 is the near-universal default, used here as the most defensible assumption.</li>
        <li class="mb-1.5">Trade-to-trade surveillance segments (NSE series BE/BZ, 272 tickers) are excluded — different settlement mechanics this project doesn't model.</li>
        <li class="mb-1.5">New entries are funded only from currently-uninvested cash, split equally among that day's new entries; existing positions are never rebalanced to rejoin an equal-weight target.</li>
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Zero transaction costs, slippage, or taxes modeled</span> — worth flagging given {R['num_entries']:,} total entries over this backtest's history.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for any series shown.</li>
        <li class="mb-1.5">This is a single, fixed historical path — no out-of-sample validation of the RSI(14)/70/15%-stop combination specifically.</li>
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
      {trade_stats_panel}
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
