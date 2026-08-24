"""Builds 27_midcap_momentum10_stoploss_compare.html from results26.json.
Same self-contained contract, smooth Catmull-Rom charts, dark palette as
every other report. Compares the original (no stop-loss) strategy against
TWO stop-loss thresholds (15% and 30%) side by side."""
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
VARIANT_COLOR = {"stop_15": "#F2643C", "stop_30": "#8B5CF6"}


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
    orig = R["original"]
    v15, v30 = R["variants"]["stop_15"], R["variants"]["stop_30"]
    m15, m30 = v15["metrics"], v30["metrics"]
    ts15, ts30 = v15["trade_stats"], v30["trade_stats"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — Stop-Loss Overlay: 15% vs. 30%, vs. the Original</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same exact selection/weighting as reports 11-19, 24, 25 — but the moment a position falls a fixed % below its own entry price, it's exited immediately instead of waiting for the next June/December rebalance. Tested at two thresholds.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {ts15['total_positions']} total positions<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          {pill(f"15%: {ts15['stop_loss_pct_of_positions']}% of positions stopped out", 'negative')}
          {pill(f"30%: {ts30['stop_loss_pct_of_positions']}% of positions stopped out", 'assumption')}
          {pill('a looser stop hurts less, but neither beats the original', 'neutral')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Everything about the strategy stays identical — same top-10 selection by 6m/12m risk-adjusted momentum, same equal weighting, same
          June/December rebalance — except each position is now watched every trading day, and exited the moment it touches a fixed % below its
          entry price (checked via intraday LOW, filled realistically at the day's open if it gapped through — same methodology as report 22's
          RSI rotation). Widening the stop from 15% to 30% cuts the CAGR damage roughly in half.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Original (no stop): <span class="font-semibold">{pct(orig['cagr_pct'])} CAGR / {pct(orig['max_drawdown_pct'],1,signed=False)} DD</span>.
          15% stop: <span class="font-semibold">{pct(m15['cagr_pct'])} CAGR / {pct(m15['max_drawdown_pct'],1,signed=False)} DD</span> —
          {ts15['stop_loss_pct_of_positions']}% of all positions stopped out. 30% stop: <span class="font-semibold">{pct(m30['cagr_pct'])} CAGR /
          {pct(m30['max_drawdown_pct'],1,signed=False)} DD</span> — only {ts30['stop_loss_pct_of_positions']}% stopped out. The looser 30% stop
          gives up much less return ({pct(orig['cagr_pct'] - m30['cagr_pct'], 1, signed=False)} points vs. 15%'s
          {pct(orig['cagr_pct'] - m15['cagr_pct'], 1, signed=False)} points) for a very similar drawdown improvement — see the honesty note below.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window.",
                  [("Original (no stop)", pct(orig["cagr_pct"]), win_loss_kind(orig["cagr_pct"])),
                   ("15% stop", pct(m15["cagr_pct"]), win_loss_kind(m15["cagr_pct"])),
                   ("30% stop", pct(m30["cagr_pct"]), win_loss_kind(m30["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Original (no stop)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("15% stop", pct(m15["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("30% stop", pct(m30["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Original (no stop)", pct(orig["net_return_pct"]), win_loss_kind(orig["net_return_pct"])),
                   ("15% stop", pct(m15["net_return_pct"]), win_loss_kind(m15["net_return_pct"])),
                   ("30% stop", pct(m30["net_return_pct"]), win_loss_kind(m30["net_return_pct"]))]),
        kpi_card("Stopped-out share of all positions", "How many of every position taken over 18 years got stopped out early.",
                  [("15% stop", f"{ts15['stop_loss_exits']} ({ts15['stop_loss_pct_of_positions']}%)", "negative"),
                   ("30% stop", f"{ts30['stop_loss_exits']} ({ts30['stop_loss_pct_of_positions']}%)", "assumption")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Original vs. both stop-loss thresholds</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the exact same strategy, identical {esc(R['start_date'])}–{esc(R['end_date'])} window, only the exit rule and threshold change.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Original — no stop-loss, hold to rebalance", orig)}
          {row("With 15% intra-period stop-loss", m15)}
          {row("With 30% intra-period stop-loss", m30)}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Original (no stop-loss)", "color": COL["positive"], "points": orig["equity_curve"]},
        {"name": "30% stop-loss", "color": VARIANT_COLOR["stop_30"], "points": m30["equity_curve"]},
        {"name": "15% stop-loss", "color": VARIANT_COLOR["stop_15"], "points": m15["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_27")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the original strategy (green) pulls ahead of both stop-loss versions; the 30% stop (violet) tracks it much more closely than the tighter 15% stop (red), which falls behind earliest and by the widest margin.</p>
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
        {"name": "30% stop-loss", "color": VARIANT_COLOR["stop_30"], "points": dd_points(m30["equity_curve"])},
        {"name": "15% stop-loss", "color": VARIANT_COLOR["stop_15"], "points": dd_points(m15["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_27")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — both stop-loss thresholds land in a similar place on drawdown ({pct(m15['max_drawdown_pct'],1,signed=False)} at 15%, {pct(m30['max_drawdown_pct'],1,signed=False)} at 30%) despite the 30% stop giving up far less return than the 15% stop — the tighter stop's extra return sacrifice buys almost no extra drawdown protection.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def trade_row(t):
        return f"""<tr class="stop-row"><td>{esc(t['ticker'])}</td><td>{esc(t['entry_date'])}</td><td>{sym}{t['entry_price']:,.2f}</td>
        <td>{esc(t['exit_date'])}</td><td>{sym}{t['exit_price']:,.2f}</td><td>{pct(t['pct_return'])}</td></tr>"""

    def sample_panel(variant_key, label, sample, ts):
        return f"""
        <div class="{PANEL} mt-6">
          <div class="flex items-center justify-between mb-1">
            <h3 class="text-base font-bold text-[#E6EDF0]">Sample of {label} stop-loss exits</h3>
            {pill(f"first 10 and last 10 of {ts['stop_loss_exits']} shown", 'neutral')}
          </div>
          <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every row is a position that touched -{v15['stop_loss_pct'] if variant_key=='stop_15' else v30['stop_loss_pct']:.0f}% intraday and was exited immediately. Returns cluster tightly around the threshold — that's the stop mechanism working as designed, not noise.</p>
          <div style="overflow-x:auto">
          <table class="data-table">
            <thead><tr><th style="text-align:left">Stock</th><th>Bought</th><th>Buy price</th><th>Stopped out</th><th>Exit price</th><th>Return</th></tr></thead>
            <tbody>{''.join(trade_row(t) for t in sample)}</tbody>
          </table>
          </div>
        </div>
        """

    stoploss_sample_panels = sample_panel("stop_15", "15%", v15["stop_loss_trades_sample"], ts15) + \
        sample_panel("stop_30", "30%", v30["stop_loss_trades_sample"], ts30)

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why the looser 30% stop is the better trade-off</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Midcap momentum picks are, by construction, already-volatile stocks that just had a strong 6-12 month run — the kind of names that can
        easily give back 15% in an ordinary pullback WITHOUT the underlying trend actually being over. A 15% stop on a 6-month holding period is
        tight enough to get triggered by routine volatility, which is why {ts15['stop_loss_pct_of_positions']}% of all
        {ts15['total_positions']} positions taken over 18 years ended up stopped out at 15% — versus only {ts30['stop_loss_pct_of_positions']}%
        at 30%, where the stop is wide enough to mostly let ordinary swings play out and only fire on genuinely severe breakdowns.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        That difference shows up directly in what each threshold gives up: positions stopped out at 15% averaged
        <span class="font-semibold">{pct(ts15['avg_stop_loss_return'])}</span> versus the {ts15['rebalance_exits']} that rode to rebalance
        averaging <span class="font-semibold">{pct(ts15['avg_rebalance_exit_return'])}</span> — a huge gap between what got cut short and what
        the strategy's real edge lives in. At 30%, far fewer positions ({ts30['stop_loss_exits']} vs. {ts15['stop_loss_exits']}) get caught in
        that trade-off, which is exactly why 30%'s CAGR ({pct(m30['cagr_pct'])}) sits so much closer to the original's ({pct(orig['cagr_pct'])})
        than 15%'s does ({pct(m15['cagr_pct'])}).
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Yet both thresholds land in almost the same place on drawdown ({pct(m15['max_drawdown_pct'],1,signed=False)} vs.
        {pct(m30['max_drawdown_pct'],1,signed=False)}) — meaning the EXTRA tail-risk protection the tighter 15% stop is supposedly buying, over
        and above what 30% already provides, turns out to be worth very little. For this specific strategy, a looser stop (or arguably no stop
        at all, per the original report 27 finding) is the better risk/reward trade-off than a tight one.
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
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window for all three variants equally (survivorship bias) — same disclosed approximation as every other reconstruction here.</li>
        <li class="mb-1.5">Cash freed by a stop-loss exit sits idle (0% return) until the next scheduled rebalance for both thresholds — there is no rule tested here for immediately reinvesting it mid-period.</li>
        <li class="mb-1.5">Only these two thresholds (15% and 30%) were tested — the true optimum could sit anywhere in between, above 30%, or the original "no stop at all" could remain best; this is not an exhaustive search.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes are modeled on any variant — both stop-loss versions trade more often than the original, so real-world costs would widen the gap against them further, not narrow it.</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding.</li>
        <li class="mb-1.5">This is a single, fixed 18-year historical path — a different window, or a market regime with more genuine (non-recovering) crashes, could rank these three variants differently.</li>
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
      {stoploss_sample_panels}
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
