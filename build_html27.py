"""Builds 27_midcap_momentum10_stoploss_compare.html from results26.json.
Same self-contained contract, smooth Catmull-Rom charts, dark palette as
every other report."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results26.json") as f:
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
      tr.stop-row td{color:#F2643C;}
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
    orig, stop = R["original"], R["with_stop_loss"]
    ts = R["trade_stats"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — With a {R['stop_loss_pct']:.0f}% Stop-Loss, vs. the Original</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same exact selection/weighting as reports 11-19, 24, 25 — but the moment a position falls {R['stop_loss_pct']:.0f}% below its own entry price, it's exited immediately instead of waiting for the next June/December rebalance.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {ts['total_positions']} total positions<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">The rule, and the honest result up front</h2>
          {pill(f"{ts['stop_loss_pct_of_positions']}% of all positions got stopped out", 'neutral')}
          {pill('the stop-loss makes this strategy meaningfully WORSE', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Everything about the strategy stays identical — same top-10 selection by 6m/12m risk-adjusted momentum, same equal weighting, same
          June/December rebalance — except now each position is watched every trading day. The moment its price touches {R['stop_loss_pct']:.0f}%
          below where it was bought, it's sold immediately (using the day's intraday LOW to detect the breach, filled at the day's open if the
          stock gapped straight through the stop overnight — the same realistic-fill methodology as report 22's RSI rotation), and the proceeds
          sit in cash, uninvested, until the next scheduled rebalance.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window, adding the stop-loss cut CAGR from
          <span class="font-semibold">{pct(orig['cagr_pct'])}</span> down to <span class="font-semibold">{pct(stop['cagr_pct'])}</span> — while
          only trimming max drawdown from {pct(orig['max_drawdown_pct'],1,signed=False)} to {pct(stop['max_drawdown_pct'],1,signed=False)}. Of
          {ts['total_positions']} total positions taken, <span class="font-semibold">{ts['stop_loss_exits']} ({ts['stop_loss_pct_of_positions']}%)
          were stopped out</span> at an average {pct(ts['avg_stop_loss_return'])}, while the {ts['rebalance_exits']} that rode through to their
          scheduled rebalance averaged <span class="font-semibold">{pct(ts['avg_rebalance_exit_return'])}</span> — see the honesty note below for
          why cutting losers early here also cut off the strategy's own biggest winners.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window.",
                  [("Original (no stop-loss)", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   (f"With {R['stop_loss_pct']:.0f}% stop-loss", pct(stop["cagr_pct"]), win_loss_kind(stop["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Original (no stop-loss)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   (f"With {R['stop_loss_pct']:.0f}% stop-loss", pct(stop["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Original (no stop-loss)", pct(orig["net_return_pct"]), win_loss_kind(orig["net_return_pct"])),
                   (f"With {R['stop_loss_pct']:.0f}% stop-loss", pct(stop["net_return_pct"]), win_loss_kind(stop["net_return_pct"]))]),
        kpi_card("Position outcomes", "How every position taken over 18 years actually ended.",
                  [("Stopped out", f"{ts['stop_loss_exits']} ({ts['stop_loss_pct_of_positions']}%)", "negative"),
                   ("Rode to rebalance", f"{ts['rebalance_exits']}", "positive"),
                   ("Still open", f"{ts['still_open']}", "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Original vs. with stop-loss</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the exact same strategy, identical {esc(R['start_date'])}–{esc(R['end_date'])} window, only the exit rule changes.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Original — no stop-loss, hold to rebalance", orig)}
          {row(f"With {R['stop_loss_pct']:.0f}% intra-period stop-loss", stop)}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Original (no stop-loss)", "color": COL["positive"], "points": orig["equity_curve"]},
        {"name": f"With {R['stop_loss_pct']:.0f}% stop-loss", "color": COL["negative"], "points": stop["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_27")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the original strategy (green) pulls decisively ahead of the stop-loss version (red) for almost the entire 18-year window, not just at the very end.</p>
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
        {"name": "Original (no stop-loss)", "color": COL["positive"], "points": dd_points(orig["equity_curve"])},
        {"name": f"With {R['stop_loss_pct']:.0f}% stop-loss", "color": COL["negative"], "points": dd_points(stop["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_27")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the stop-loss version's drawdown ({pct(stop['max_drawdown_pct'],1,signed=False)}) is only modestly shallower than the original's ({pct(orig['max_drawdown_pct'],1,signed=False)}) — a small risk reduction bought at a very large cost in return.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def trade_row(t):
        return f"""<tr class="stop-row"><td>{esc(t['ticker'])}</td><td>{esc(t['entry_date'])}</td><td>{sym}{t['entry_price']:,.2f}</td>
        <td>{esc(t['exit_date'])}</td><td>{sym}{t['exit_price']:,.2f}</td><td>{pct(t['pct_return'])}</td></tr>"""

    sample = R["stop_loss_trades_sample"]
    stoploss_sample_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample of stop-loss exits</h3>
        {pill(f"first 10 and last 10 of {ts['stop_loss_exits']} shown", 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every row here is a position that touched -{R['stop_loss_pct']:.0f}% intraday and was exited immediately, rather than being given until the next rebalance to recover. Note how tightly clustered the returns are right around -15% — that's the stop mechanism working exactly as designed, not noise.</p>
      <div style="overflow-x:auto">
      <table class="data-table">
        <thead><tr><th style="text-align:left">Stock</th><th>Bought</th><th>Buy price</th><th>Stopped out</th><th>Exit price</th><th>Return</th></tr></thead>
        <tbody>{''.join(trade_row(t) for t in sample)}</tbody>
      </table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why cutting losers early also cut the strategy's winners</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Midcap momentum picks are, by construction, already-volatile stocks that just had a strong 6-12 month run — the kind of names that can
        easily give back 15% in a sharp pullback WITHOUT that pullback meaning the underlying trend is actually over. A {R['stop_loss_pct']:.0f}%
        stop on a 6-month holding period is tight enough to get triggered by ordinary volatility, not just genuine trend reversals — which is why
        {ts['stop_loss_pct_of_positions']}% of all {ts['total_positions']} positions taken over 18 years ended up stopped out.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The asymmetry is the whole story: positions that rode through to their scheduled rebalance averaged
        <span class="font-semibold">{pct(ts['avg_rebalance_exit_return'])}</span> — the strategy's real edge lives almost entirely in these
        multi-month winners. The stop-loss rule has no way to distinguish "this stock is about to keep falling" from "this stock is about to dip
        15% and then rally to +50% by the next rebalance" — it exits both identically at -15%. Every position removed from the "rode to
        rebalance" bucket and moved into "stopped out" trades away a chance at that {pct(ts['avg_rebalance_exit_return'])} average outcome for a
        guaranteed {pct(ts['avg_stop_loss_return'])} loss, which is exactly why total CAGR fell so much more than drawdown improved.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This doesn't mean stop-losses never work — report 22's RSI rotation uses one successfully on a very different, shorter-holding-period
        strategy. It means a tight per-position stop is a poor fit specifically for a momentum strategy that already only checks in twice a
        year: it converts many of the ordinary swings a 6-month holding period is supposed to ride out into locked-in losses, without a
        correspondingly large reduction in the strategy's actual tail risk.
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
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window for both variants equally (survivorship bias) — same disclosed approximation as every other reconstruction here.</li>
        <li class="mb-1.5">Cash freed by a stop-loss exit sits idle (0% return) until the next scheduled rebalance — there is no rule tested here for immediately reinvesting it into another stock or the next-best momentum candidate mid-period, which could meaningfully change this result in either direction.</li>
        <li class="mb-1.5">Only ONE stop-loss threshold (-15%) was tested — a wider stop (giving more room before exiting) or a narrower one were not tried; report 22's own -15% choice for a very different strategy is not evidence this specific number is optimal here.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes are modeled on either variant — the stop-loss version trades far more often ({ts['stop_loss_exits']} extra exits beyond the {ts['rebalance_exits']} the original strategy would have made anyway), so real-world costs would widen this gap further, not narrow it.</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding.</li>
        <li class="mb-1.5">This is a single, fixed 18-year historical path — a different window, or a market regime with more genuine (non-recovering) crashes, could make the stop-loss look considerably better relative to the original than it does here.</li>
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
      {stoploss_sample_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — Stop-Loss Overlay Compared</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("27_midcap_momentum10_stoploss_compare.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 27_midcap_momentum10_stoploss_compare.html")
