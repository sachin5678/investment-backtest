"""Builds 31_midcap_momentum10_carried_tradelog.html from results30.json.
Same self-contained contract, smooth Catmull-Rom charts, dark palette as
every other report — but the trade log merges every consecutive rebalance
a stock survives into ONE row (New / Carried / Exited tags) instead of a
fresh row per rebalance leg."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results30.json") as f:
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

TAG_BASE = "inline-flex items-center text-[10px] font-semibold px-1.5 py-0.5 rounded whitespace-nowrap ml-1"
TAG_NEW = TAG_BASE + " bg-[#6AE4FF]/15 text-[#6AE4FF]"
TAG_CARRIED = TAG_BASE + " bg-[#8B5CF6]/15 text-[#8B5CF6]"
TAG_EXITED = TAG_BASE + " bg-[#7E97A0]/15 text-[#7E97A0]"
TAG_OPEN = TAG_BASE + " bg-[#F2B03C]/15 text-[#F2B03C]"


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
      tr.win-row td{color:#37F083;}
      tr.loss-row td{color:#F2643C;}
      tr.open-row td{color:#F2B03C;}
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
    mom, bench = R["momentum10"], R["midcap_etf"]
    ts = R["trade_stats"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Carried-Position Trade Log, 2015 to Date</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same reconstruction as reports 24/26/27/30, but every stock's real continuous run in the top 10 is ONE row — New / Carried / Exited — instead of a fresh row at every rebalance it survives.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {ts['total_positions']} distinct positions<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#6AE4FF]">
        <div class="flex items-center gap-2 mb-3">
          {pill(f"{ts['closed_positions']} closed positions, {ts['still_open']} still open", 'neutral')}
          {pill(f"avg {ts['avg_rebalances_held']} rebalances held, longest {ts['longest_held_rebalances']}", 'neutral')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Reports 24 and 26 showed every rebalance-to-rebalance leg as its own trade row — technically accurate to how the strategy's equity
          curve is computed (the whole portfolio is re-split equally across the top 10 at every rebalance), but it makes a stock that survives
          3-4 rebalances running look like 3-4 separate trades. This report instead tracks each stock's real, uninterrupted tenure in the top 10
          as ONE row: it opens the first time the stock is picked (<span class="{TAG_NEW}">NEW</span>), stays open through every rebalance it's
          still selected (<span class="{TAG_CARRIED}">CARRIED</span> — tagged, not a new row), and closes the moment it's finally dropped
          (<span class="{TAG_EXITED}">EXITED</span>), with ONE entry price, ONE exit price, and the total gain/loss across the whole run.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Over {esc(R['start_date'])}–{esc(R['end_date'])}, that's <span class="font-semibold">{ts['total_positions']} distinct positions</span>
          instead of the much larger leg-count reports 24/26 would show for the same period — win rate
          <span class="font-semibold">{ts['win_rate_pct']}%</span>, average winner {pct(ts['avg_win_pct'])}, average loser
          {pct(ts['avg_loss_pct'])}. The strategy itself is unchanged: {pct(mom['cagr_pct'])} CAGR /
          {pct(mom['max_drawdown_pct'],1,signed=False)} drawdown vs. the midcap ETF's {pct(bench['cagr_pct'])} /
          {pct(bench['max_drawdown_pct'],1,signed=False)} over the same window — only how the trade log is PRESENTED changes; see the
          limitations panel below for the one bookkeeping simplification this requires.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Momentum-10 (this idea)", pct(mom["net_return_pct"]), win_loss_kind(mom["net_return_pct"])),
                   ("Midcap ETF buy & hold", pct(bench["net_return_pct"]), win_loss_kind(bench["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate, identical window.",
                  [("Momentum-10 (this idea)", pct(mom["cagr_pct"]), win_loss_kind(mom["cagr_pct"])),
                   ("Midcap ETF buy & hold", pct(bench["cagr_pct"]), win_loss_kind(bench["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Momentum-10 (this idea)", pct(mom["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap ETF buy & hold", pct(bench["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Carried-position trade log summary", "Every stock's full continuous tenure, merged into one row.",
                  [("Win rate", f"{ts['win_rate_pct']}%", "positive" if ts['win_rate_pct'] and ts['win_rate_pct'] > 50 else "negative"),
                   ("Avg winner", pct(ts['avg_win_pct']), "positive"),
                   ("Avg loser", pct(ts['avg_loss_pct']), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Strategy vs. benchmark</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the momentum rotation against a plain buy-and-hold of the real midcap ETF, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. Same underlying equity curve as report 26's 2020-2023 slice would show over its own window, just a longer 2015-to-date span here.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Midcap150 Momentum-10 (this idea)", mom)}
          {row("MID150BEES.NS, buy & hold", bench)}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Momentum-10 (this idea)", "color": COL["positive"], "points": mom["equity_curve"]},
        {"name": "Midcap ETF buy & hold", "color": COL["text"], "points": bench["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_31")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of 2015 grew under each approach, linear axis, not log-scaled.</p>
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
        {"name": "Momentum-10 (this idea)", "color": COL["positive"], "points": dd_points(mom["equity_curve"])},
        {"name": "Midcap ETF buy & hold", "color": COL["text"], "points": dd_points(bench["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_31")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the momentum rotation's drawdown vs. the benchmark's, same window.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def tags_for(t):
        n = len(t["carried_dates"])
        parts = [f'<span class="{TAG_NEW}">NEW</span>']
        if n > 0:
            parts.append(f'<span class="{TAG_CARRIED}">CARRIED ×{n}</span>')
        if t["status"] == "open":
            parts.append(f'<span class="{TAG_OPEN}">OPEN</span>')
        else:
            parts.append(f'<span class="{TAG_EXITED}">EXITED</span>')
        return "".join(parts)

    def trade_row(t):
        cls = "open-row" if t["status"] == "open" else ("win-row" if t["pct_return"] > 0 else "loss-row")
        carried_in = ' <span class="text-[10px] text-[#7E97A0]">(entered before window)</span>' if t.get("carried_in") else ""
        status_label = "Still held" if t["status"] == "open" else "Closed"
        return f"""<tr class="{cls}"><td>{esc(t['ticker'])}{tags_for(t)}{carried_in}</td><td>{esc(t['entry_date'])}</td><td>{sym}{t['entry_price']:,.2f}</td>
        <td>{esc(t['exit_date'])}</td><td>{sym}{t['exit_price']:,.2f}</td><td>{t['num_rebalances_held']}</td>
        <td>{pct(t['pct_return'])}</td><td>{sym}{t['pnl']:,.2f}</td><td style="text-align:left">{status_label}</td></tr>"""

    trades_sorted = sorted(R["trades"], key=lambda t: -t["pct_return"])
    tradelog_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Full carried-position trade log — every distinct holding, 2015 to date</h3>
        {pill(f"{ts['total_positions']} rows total", 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — one row per stock's real continuous tenure in the top 10, sorted by return. <span class="{TAG_NEW}">NEW</span> = first entered; <span class="{TAG_CARRIED}">CARRIED ×N</span> = survived N additional rebalances without exiting; <span class="{TAG_EXITED}">EXITED</span> / <span class="{TAG_OPEN}">OPEN</span> = how the position currently stands. "(entered before window)" marks a position whose real entry predates 2015-01-01 but which exits (or is still open) within this report's window.</p>
      <div style="overflow-x:auto">
      <table class="data-table">
        <thead><tr><th style="text-align:left">Stock</th><th>Entered</th><th>Entry price</th><th>Exited / as-of</th><th>Exit price</th><th>Rebalances held</th><th>Return</th><th>P&amp;L ({sym})</th><th style="text-align:left">Status</th></tr></thead>
        <tbody>{''.join(trade_row(t) for t in trades_sorted)}</tbody>
      </table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">What merging changes, and what it doesn't</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        A stock's total price return from the day it first entered to the day it finally exited is exactly the same number whether you compute
        it directly (exit price ÷ entry price) or by chaining together every intermediate rebalance-to-rebalance leg — the interim prices
        cancel out. So every % return figure in this trade log is identical to what you'd get by carefully chaining reports 24/26's per-leg
        numbers for the same stock; nothing about the actual price performance changes. What changes is READABILITY: {ts['total_positions']}
        rows instead of a much larger leg-count for the same 2015-to-date window, with each row telling the complete story of one holding.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The one place this report's numbers genuinely diverge from the strategy's real mechanics is DOLLAR P&amp;L: the real strategy resets
        every position back to an equal 1/10th share of the total portfolio at every single rebalance (even for a stock that's continuing), so
        a long-running winner's dollar weight in the real portfolio doesn't just keep compounding untouched the way it does in this report's
        "alloc × total % return" bookkeeping. That simplification is disclosed, not hidden — see the limitations panel — and it only affects the
        {sym} P&amp;L column, never the % return column, and never the strategy-level equity curve or KPI numbers above, which are computed
        exactly as in every other report in this project.
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
        <li class="mb-1.5">Dollar P&amp;L per row assumes the position's ORIGINAL equal-weight allocation (from the day it first entered) rode untouched for the whole tenure — the real strategy actually resets every position to a fresh 1/10th of total portfolio value at every rebalance, even continuing ones. The % return column is unaffected by this; only the {sym} P&amp;L column is a simplified "as if you never rebalanced this one position" view.</li>
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window (survivorship bias) — same disclosed approximation as reports 11-19/24/26.</li>
        <li class="mb-1.5">Positions whose real entry predates 2015-01-01 are included (tagged "entered before window") because their tenure runs into the window — their entry price and rebalance count reflect the FULL run, not just the part after 2015.</li>
        <li class="mb-1.5">Still-open positions are marked to the latest available close price (not a live/real-time market price) — their eventual real exit will differ from this snapshot.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled — a continuing position that survives multiple rebalances would, in reality, still incur the buy/sell mechanics report 24/26 describe (even if the net position size is unchanged), which isn't reflected in either trade-log style.</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled. This is a single, fixed historical path.</li>
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
      {tradelog_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — Carried-Position Trade Log</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("31_midcap_momentum10_carried_tradelog.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 31_midcap_momentum10_carried_tradelog.html")
