"""Builds 24_midcap_momentum10_last2yr_tradelog.html from results23.json.
Same self-contained contract, smooth Catmull-Rom charts, dark palette as
every other report — plus the full buy/sell trade log this report exists
to show."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results23.json") as f:
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
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Last 2 Years, Full Trade Log</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">The exact same reconstruction as reports 16/17 (top 10 by 6m/12m risk-adjusted momentum, equal-weighted, rebalanced June/December), windowed to the trailing 2 years, with every single buy and sell shown.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['num_rebalances_in_window']} rebalances in window<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">The last 2 years, and the honest result up front</h2>
          {pill(f"{ts['closed_trades']} closed trades, {ts['open_positions']} still open", 'neutral')}
          {pill('underperforms the plain midcap ETF over this specific 2-year window', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Every June and December, the strategy fully re-splits its capital equally across whichever 10 midcap stocks currently rank highest on
          6-month/12-month risk-adjusted momentum — so even a stock that stays in the list for two rebalances running is, in this accounting, sold
          and bought again at the same price at every rebalance date, then genuinely exited the moment it drops out of the top 10. That means every
          row in the trade log below is a real buy at one rebalance's price and a real sell at the next rebalance's price (or "still open" for the
          most recent picks that haven't hit their next rebalance yet).
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Over {esc(R['start_date'])}–{esc(R['end_date'])}, that produced <span class="font-semibold">{pct(mom['cagr_pct'])} CAGR</span> with a
          <span class="font-semibold">{pct(mom['max_drawdown_pct'],1,signed=False)}</span> max drawdown — behind simply buying and holding the midcap
          ETF over the identical window ({pct(bench['cagr_pct'])} CAGR / {pct(bench['max_drawdown_pct'],1,signed=False)} drawdown). Win rate across
          all {ts['closed_trades']} closed positions was <span class="font-semibold">{ts['win_rate_pct']}%</span> — see the honesty note below for why
          a specific 2-year slice can look very different from this same strategy's 18-year track record (+40.6% CAGR) in report 16/17.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Momentum-10 (this idea)", pct(mom["net_return_pct"]), win_loss_kind(mom["net_return_pct"])),
                   ("Midcap ETF buy & hold", pct(bench["net_return_pct"]), win_loss_kind(bench["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate, identical 2-year window.",
                  [("Momentum-10 (this idea)", pct(mom["cagr_pct"]), win_loss_kind(mom["cagr_pct"])),
                   ("Midcap ETF buy & hold", pct(bench["cagr_pct"]), win_loss_kind(bench["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Momentum-10 (this idea)", pct(mom["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap ETF buy & hold", pct(bench["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Trade log summary", "Every stock bought at one rebalance, sold at the next.",
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
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the momentum rotation against a plain buy-and-hold of the real midcap ETF, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
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
        {"name": "Momentum-10 (this idea)", "color": COL["negative"], "points": mom["equity_curve"]},
        {"name": "Midcap ETF buy & hold", "color": COL["positive"], "points": bench["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_24")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each approach, linear axis, not log-scaled.</p>
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
        {"name": "Momentum-10 (this idea)", "color": COL["negative"], "points": dd_points(mom["equity_curve"])},
        {"name": "Midcap ETF buy & hold", "color": COL["positive"], "points": dd_points(bench["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_24")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the momentum rotation's drawdown vs. the benchmark's, same window.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    # group trades by rebalance period for the detailed log
    by_period = {}
    for t in R["trades"]:
        by_period.setdefault((t["entry_date"], t["exit_date"], t["status"]), []).append(t)

    def trade_row(t):
        cls = "open-row" if t["status"] == "open" else ("win-row" if t["pct_return"] > 0 else "loss-row")
        carried = ' <span class="text-[10px] text-[#7E97A0]">(carried in)</span>' if t.get("carried_in") else ""
        status_label = "Still held" if t["status"] == "open" else "Closed"
        return f"""<tr class="{cls}"><td>{esc(t['ticker'])}{carried}</td><td>{esc(t['entry_date'])}</td><td>{sym}{t['entry_price']:,.2f}</td>
        <td>{esc(t['exit_date'])}</td><td>{sym}{t['exit_price']:,.2f}</td><td>{pct(t['pct_return'])}</td>
        <td>{sym}{t['pnl']:,.2f}</td><td style="text-align:left">{status_label}</td></tr>"""

    period_blocks = []
    for (entry_d, exit_d, status), rows in sorted(by_period.items(), key=lambda kv: kv[0][0]):
        period_label = f"{entry_d} → {exit_d}" + (" (open, marked to latest price)" if status == "open" else "")
        rows_sorted = sorted(rows, key=lambda t: -t["pct_return"])
        period_blocks.append(f"""
        <div class="mb-5">
          <div class="text-[13px] font-semibold text-[#C9D6DA] mb-2 mono">{esc(period_label)}</div>
          <div style="overflow-x:auto">
          <table class="data-table">
            <thead><tr><th style="text-align:left">Stock</th><th>Bought</th><th>Buy price</th><th>Sold / as-of</th><th>Sell price</th><th>Return</th><th>P&amp;L ({sym})</th><th style="text-align:left">Status</th></tr></thead>
            <tbody>{''.join(trade_row(t) for t in rows_sorted)}</tbody>
          </table>
          </div>
        </div>
        """)

    tradelog_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Full buy/sell trade log — every stock, every rebalance</h3>
        {pill(f"{ts['total_trades']} rows total", 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — one row per stock per holding period, grouped by rebalance date. Green = closed winner, red = closed loser, amber = still open (marked to the latest available price, unrealized). "(carried in)" marks a position bought at the rebalance just before this report's 2-year window started.</p>
      {''.join(period_blocks)}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why 2 years can look so different from 18</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Report 16/17's headline number for this exact strategy — {sym}100 growing at roughly 40.6% CAGR — is an AVERAGE over 18 years and 36+
        rebalances spanning multiple bull and bear midcap cycles (2008-09 crash and recovery, 2013 taper tantrum, 2020 COVID crash and V-recovery,
        the 2022 correction, and more). Any single 2-year slice, including this one, samples just {R['num_rebalances_in_window']} rebalances out of
        that much longer run — enough for one bad or choppy stretch to dominate the window's own number even though the strategy's long-run edge is
        real. With only {ts['closed_trades']} closed trades to judge a {ts['win_rate_pct']}% win rate by, this window alone is not a large enough
        sample to conclude the strategy has stopped working.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Momentum strategies are also mechanically exposed to sharp reversals: a stock that ranked in the top 10 on trailing 6m/12m strength can
        (and did, see the trade log above) give back a large chunk of that gain in the very next 6 months if the trend it was chasing reverses —
        that is the concentrated, "buy strength, get whipsawed sometimes" nature of momentum investing, not a bug in this specific window.
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
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window (survivorship bias) — same disclosed approximation as reports 11-19.</li>
        <li class="mb-1.5">Every rebalance is modeled as a full sell-and-rebuy of the ENTIRE portfolio at that date's closing prices, even for stocks that stay in the top 10 — zero transaction costs, slippage, or taxes are modeled on any of these trades, which in reality would be a real cost on every single row of the trade log above (not just the ones that actually change holdings).</li>
        <li class="mb-1.5">The "carried in" position(s) at the top of the log were bought at the rebalance BEFORE this report's 2-year window technically starts — included because their holding period runs into the window, but their entry price predates the window's own start date.</li>
        <li class="mb-1.5">The final period's positions are marked "open" at whatever the latest available close price is (not a live/real-time market price) — their eventual real exit, at the next actual rebalance, will differ from this snapshot.</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for either the strategy's stock holdings or the benchmark ETF.</li>
        <li class="mb-1.5">This is a single, fixed 2-year historical path — a very small sample ({ts['closed_trades']} closed trades) to draw strong conclusions from; see report 16/17 for this same strategy's much longer 18-year track record.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Last 2 Years Trade Log</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("24_midcap_momentum10_last2yr_tradelog.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 24_midcap_momentum10_last2yr_tradelog.html")
