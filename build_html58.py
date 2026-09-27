"""Builds 58_midcap_momentum10_trailing_stop.html from results57.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results57.json") as f:
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
VARIANT_COLORS = {"fixed_15": "#8B5CF6", "trailing_15": "#F2643C", "fixed_30": "#6AE4FF", "trailing_30": "#37F083"}
VARIANT_LABELS = {"fixed_15": "Fixed 15% (report 27)", "trailing_15": "Trailing 15%", "fixed_30": "Fixed 30% (report 27)", "trailing_30": "Trailing 30%"}


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
    orig = R["original"]
    V = R["variants"]
    f15, t15, f30, t30 = V["fixed_15"], V["trailing_15"], V["fixed_30"], V["trailing_30"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Per-Stock Trailing Stop vs. Report 27's Fixed Stop</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Report 27 tested a FIXED stop-loss (15% and 30% below each position's own ENTRY price, never moving). This report tests the same two thresholds measured off each position's own PEAK price since entry instead — a trailing stop that ratchets UP as a winning position's peak rises, cutting individual losers without needing report 42-57's portfolio-wide regime switch at all. Same realistic Low/Open fill methodology as report 27, cash until the next rebalance.</p>
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
          {pill('a tight trailing stop is far more destructive than a tight fixed one', 'negative')}
          {pill(f"15% trailing stopped out {t15['trade_stats']['stop_loss_pct_of_positions']}% of ALL positions", 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          At 15%, trailing is dramatically WORSE than fixed: CAGR collapses from {pct(f15['metrics']['cagr_pct'])} (fixed) to
          <span class="font-semibold">{pct(t15['metrics']['cagr_pct'])}</span> (trailing) — because a stop that RATCHETS UP with
          every new high triggers on completely normal volatility, not just genuine reversals. It stopped out
          {t15['trade_stats']['stop_loss_pct_of_positions']}% of every position ever held, at an AVERAGE return of
          {pct(t15['trade_stats']['avg_stop_loss_return'])} — often a small gain, not a loss, because the stop was simply too
          tight to survive ordinary price noise.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          At 30%, the picture flips: trailing BEATS fixed on drawdown — {pct(f30['metrics']['max_drawdown_pct'],1,signed=False)}
          (fixed) improves to <span class="font-semibold">{pct(t30['metrics']['max_drawdown_pct'],1,signed=False)}</span> (trailing) —
          for a modest CAGR cost, {pct(f30['metrics']['cagr_pct'])} to {pct(t30['metrics']['cagr_pct'])}. A WIDE trailing stop
          genuinely locks in gains on winners without over-triggering; a TIGHT one just adds noise-driven churn.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR", "Compound annual growth rate, identical window for every variant.",
                  [("No stop (original)", pct(orig["cagr_pct"]), "neutral"),
                   ("Fixed 15%", pct(f15["metrics"]["cagr_pct"]), "neutral"),
                   ("Trailing 15%", pct(t15["metrics"]["cagr_pct"]), "negative"),
                   ("Fixed 30%", pct(f30["metrics"]["cagr_pct"]), "neutral"),
                   ("Trailing 30%", pct(t30["metrics"]["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("No stop (original)", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Fixed 15%", pct(f15["metrics"]["max_drawdown_pct"], 1, signed=False), "neutral"),
                   ("Trailing 15%", pct(t15["metrics"]["max_drawdown_pct"], 1, signed=False), "neutral"),
                   ("Fixed 30%", pct(f30["metrics"]["max_drawdown_pct"], 1, signed=False), "neutral"),
                   ("Trailing 30%", pct(t30["metrics"]["max_drawdown_pct"], 1, signed=False), "positive")]),
        kpi_card("How often does each stop actually trigger", "Share of every position ever held that was stopped out (vs. exited at a normal rebalance).",
                  [("Fixed 15%", f"{f15['trade_stats']['stop_loss_pct_of_positions']}%", "neutral"),
                   ("Trailing 15%", f"{t15['trade_stats']['stop_loss_pct_of_positions']}%", "negative"),
                   ("Fixed 30%", f"{f30['trade_stats']['stop_loss_pct_of_positions']}%", "neutral"),
                   ("Trailing 30%", f"{t30['trade_stats']['stop_loss_pct_of_positions']}%", "assumption")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, m, ts, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(m['net_return_pct'])}</td><td>{pct(m['cagr_pct'])}</td>
        <td>{pct(m['max_drawdown_pct'],1,signed=False)}</td><td>{m['longest_underwater_days']:,}d</td>
        <td>{ts['stop_loss_exits']}/{ts['total_positions']} ({ts['stop_loss_pct_of_positions']}%)</td>
        <td>{pct(ts['avg_stop_loss_return'])}</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">All five, side by side</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — original (no stop), fixed and trailing stops at both thresholds, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. "Avg stop return" is the average % return of positions that were ACTUALLY stopped out (not all positions).</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th><th>Stopped out</th><th>Avg stop return</th></tr></thead>
        <tbody>
          <tr><td>No stop-loss (original)</td><td>{pct(orig['net_return_pct'])}</td><td>{pct(orig['cagr_pct'])}</td><td>{pct(orig['max_drawdown_pct'],1,signed=False)}</td><td>{orig['longest_underwater_days']:,}d</td><td>—</td><td>—</td></tr>
          {row("Fixed stop, 15% off entry (report 27)", f15['metrics'], f15['trade_stats'])}
          {row("Trailing stop, 15% off peak", t15['metrics'], t15['trade_stats'])}
          {row("Fixed stop, 30% off entry (report 27)", f30['metrics'], f30['trade_stats'])}
          {row("Trailing stop, 30% off peak", t30['metrics'], t30['trade_stats'])}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "No stop (original)", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
        {"name": VARIANT_LABELS["fixed_15"], "color": VARIANT_COLORS["fixed_15"], "points": f15["metrics"]["equity_curve"]},
        {"name": VARIANT_LABELS["trailing_15"], "color": VARIANT_COLORS["trailing_15"], "points": t15["metrics"]["equity_curve"]},
        {"name": VARIANT_LABELS["fixed_30"], "color": VARIANT_COLORS["fixed_30"], "points": f30["metrics"]["equity_curve"]},
        {"name": VARIANT_LABELS["trailing_30"], "color": VARIANT_COLORS["trailing_30"], "points": t30["metrics"]["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_58")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {R['currency_symbol']}100 invested at the start of the window grew under each stop-loss variant, linear axis, not log-scaled. Trailing 15% (red) falls far behind everything else — the visual signature of a stop that's simply too tight to let any winner run.</p>
      <div class="flex items-center mb-2 flex-wrap">{eq_legend}</div>
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
        {"name": VARIANT_LABELS["fixed_30"], "color": VARIANT_COLORS["fixed_30"], "points": dd_points(f30["metrics"]["equity_curve"])},
        {"name": VARIANT_LABELS["trailing_30"], "color": VARIANT_COLORS["trailing_30"], "points": dd_points(t30["metrics"]["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_58")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison — the 30% pair only</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — at the WIDE 30% threshold, trailing's drawdown ({pct(t30['metrics']['max_drawdown_pct'],1,signed=False)}) is shallower than fixed's ({pct(f30['metrics']['max_drawdown_pct'],1,signed=False)}) — the one place in this report where trailing genuinely wins outright. The 15% pair is omitted here since trailing-15's collapse would dwarf the chart's scale.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why "trailing" isn't automatically "better"</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        A fixed stop is anchored to the ENTRY price for the whole holding period — a stock that rallies 40% then pulls back
        15% from its peak is nowhere near a 15%-off-entry fixed stop (it's still up ~19% from entry), so it survives. A
        TRAILING stop has no such cushion: the moment that same stock's peak rises, the stop level rises right along with
        it, so a routine 15% pullback from ANY new high — completely normal for a volatile midcap stock, several times a
        year even during a genuine uptrend — triggers an exit. That's exactly why {t15['trade_stats']['stop_loss_pct_of_positions']}%
        of every position held was stopped out at 15% trailing, at a barely-positive average return: the stop was firing on
        ordinary noise, not on actual reversals.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        A wide trailing stop (30%) avoids that failure mode — normal volatility rarely swings 30% from a recent peak within
        a 6-month window, so it mostly triggers on genuine, sustained reversals, which is exactly the scenario where locking
        in a rising floor pays off. The lesson generalizes beyond stop-losses: any rule that reacts to a MOVING reference
        point (a trailing peak, a moving average, a recent high) needs to be set wide enough to filter out routine noise, or
        it ends up reacting to volatility itself rather than to the trend it was meant to protect against — the same lesson
        report 46 found for EMA span and report 47 found for confirmation delay.
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
        <li class="mb-1.5">Today's peak folds in AFTER today's stop check (using yesterday's peak to avoid same-day look-ahead) — a same-day update would be slightly more optimistic and is NOT what's modeled here.</li>
        <li class="mb-1.5">Only two thresholds (15%, 30%) were tested — the true "sweet spot" between trailing-15's collapse and trailing-30's modest win could sit anywhere in between, or beyond 30%.</li>
        <li class="mb-1.5">Money freed by any stop-loss sits in cash (0% return) until the next scheduled rebalance — no rule for reinvesting it into a new stock mid-period, same as report 27.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled beyond the realistic Low/Open fill mechanics — a strategy that stops out {t15['trade_stats']['stop_loss_pct_of_positions']}% of positions (trailing 15%) would incur FAR more real-world brokerage than the 36-rebalance baseline (see report 32 for what real charges do to even the un-stopped strategy).</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other reconstruction here. This is a single, fixed 18-year historical path.</li>
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
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Trailing Stop vs. Fixed Stop</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("58_midcap_momentum10_trailing_stop.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 58_midcap_momentum10_trailing_stop.html")
