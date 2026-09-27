"""Builds 57_midcap_momentum10_breadth_confirmation.html from results56.json."""
import json
import html
from svg_charts import line_chart, COL

with open("results56.json") as f:
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
THRESHOLD_COLORS = {30: "#6AE4FF", 50: "#37F083", 70: "#8B5CF6", 90: "#F2643C"}


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
      tr.highlight td{background:rgba(55,240,131,0.06);}
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
    orig, nonly, nif = R["original"], R["nifty_only"], R["nifty"]
    variants = R["variants"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap150 Momentum 10 — Breadth Confirmation for the Regime Filter</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Reports 42-56 triggered the cash/invested switch purely from NIFTY 50's own 200-day EMA. This report adds a second condition: NIFTY 50 must be above its own 200-EMA AND at least a minimum share of the relevant top-10 candidates must ALSO be above their own 200-day EMA — so one index's price alone isn't the sole trigger. Four thresholds tested (30%/50%/70%/90%), same Midcap150 Momentum 10 formula throughout.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#7E97A0]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill('barely moves the needle at any reasonable threshold', 'neutral')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          At 30%, 50%, and 70% breadth thresholds, CAGR and max drawdown are essentially IDENTICAL to the NIFTY-50-only
          filter ({pct(nonly['cagr_pct'])} / {pct(nonly['max_drawdown_pct'],1,signed=False)}) — the breadth condition is almost
          always already satisfied whenever NIFTY 50 itself is above its 200-EMA. Only at a strict 90% threshold does the
          filter start behaving noticeably differently, and even then it's WORSE, not better: re-entries climb to
          {variants[3]['num_regime_reentries']} (vs. {nonly['num_regime_reentries']} for NIFTY-only) for essentially the
          same CAGR and drawdown.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The honest reading: in this Midcap150 universe, breadth and NIFTY 50's own trend are highly correlated — when the
          broad market is above its 200-day average, more than half (often more than 70%) of midcap stocks tend to be too,
          simply because they're all reacting to the same broad economic and market conditions. Requiring extra breadth
          confirmation adds complexity without adding much genuinely NEW information, at least at the thresholds tested here.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR by breadth threshold", "Compound annual growth rate, identical window for every variant.",
                  [("No filter", pct(orig["cagr_pct"]), "neutral"),
                   ("NIFTY 50 only", pct(nonly["cagr_pct"]), "neutral")] +
                  [(f"Breadth ≥{v['breadth_threshold_pct']:.0f}%", pct(v["cagr_pct"]), "neutral") for v in variants] +
                  [("NIFTY 50 (bench)", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown by breadth threshold", "Largest peak-to-trough decline, identical window for every variant.",
                  [("No filter", pct(orig["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50 only", pct(nonly["max_drawdown_pct"], 1, signed=False), "positive")] +
                  [(f"Breadth ≥{v['breadth_threshold_pct']:.0f}%", pct(v["max_drawdown_pct"], 1, signed=False), "neutral") for v in variants] +
                  [("NIFTY 50 (bench)", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, cagr, dd, net, uw, reentries=None, cash_pct=None, cls="", highlight=False):
        c = f' class="{cls} highlight"' if highlight else (f' class="{cls}"' if cls else "")
        reentries_str = f"{reentries}" if reentries is not None else "—"
        cash_str = f"{cash_pct:.1f}%" if cash_pct is not None else "—"
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(net)}</td><td>{pct(cagr)}</td>
        <td>{pct(dd,1,signed=False)}</td><td>{uw:,}d</td><td>{cash_str}</td><td>{reentries_str}</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Every breadth threshold, side by side</h3>
        {pill("highlighted row = report 42's NIFTY-50-only filter", 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every breadth threshold tested against the unfiltered strategy, the NIFTY-50-only filter, and the real NIFTY 50 index, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th><th>Time in cash</th><th>Re-entries</th></tr></thead>
        <tbody>
          {row("No filter (always invested)", orig['cagr_pct'], orig['max_drawdown_pct'], orig['net_return_pct'], orig['longest_underwater_days'])}
          {row("NIFTY-50-only filter (report 42)", nonly['cagr_pct'], nonly['max_drawdown_pct'], nonly['net_return_pct'], nonly['longest_underwater_days'], nonly['num_regime_reentries'], nonly['pct_time_in_cash'], highlight=True)}
          {"".join(row(f"NIFTY 50 + breadth ≥{v['breadth_threshold_pct']:.0f}%", v['cagr_pct'], v['max_drawdown_pct'], v['net_return_pct'], v['longest_underwater_days'], v['num_regime_reentries'], v['pct_time_in_cash']) for v in variants)}
          {row("NIFTY 50 (real index)", nif['cagr_pct'], nif['max_drawdown_pct'], nif['net_return_pct'], nif['longest_underwater_days'], cls="real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [{"name": "No filter", "color": COL["muted"], "points": orig["equity_curve"], "dash": True},
                 {"name": "NIFTY 50 only", "color": COL["negative"], "points": nonly["equity_curve"]}]
    for v in variants:
        eq_series.append({"name": f"Breadth ≥{v['breadth_threshold_pct']:.0f}%", "color": THRESHOLD_COLORS[int(v['breadth_threshold_pct'])], "points": v["equity_curve"]})
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_57")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — every threshold, {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {R['currency_symbol']}100 invested at the start of the window grew under each breadth threshold, linear axis, not log-scaled. The 30%/50%/70% lines sit almost exactly on top of the NIFTY-50-only line (red) — visually indistinguishable for most of the window.</p>
      <div class="flex items-center mb-2 flex-wrap">{eq_legend}</div>
      {eq_svg}
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why breadth confirmation didn't add much here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Breadth confirmation is a real, commonly-used idea in technical analysis — the logic is that a "healthy" market
        advance should be broad, not just a few large names pulling the index up while everything else lags, and a market
        where the index looks fine but breadth is deteriorating underneath is sometimes flagged as an early warning sign.
        That logic didn't pay off here because Midcap150 and NIFTY 50, despite trading different stocks, are both driven by
        the SAME broad economic and liquidity conditions — interest rates, FII flows, macro sentiment — so their trend
        signals move together far more often than they diverge. A confirmation rule only helps when the two signals
        genuinely disagree often enough to matter, and in this dataset, they mostly don't.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The 90% threshold's slightly WORSE result (more re-entries for no better CAGR or drawdown) is itself instructive: a
        very strict breadth requirement doesn't wait for a genuinely different signal, it just makes the SAME underlying
        NIFTY-50 signal jumpier, since requiring near-unanimous participation is itself sensitive to whichever single stock
        happens to be right at its own 200-EMA on a given day. This is a cautionary example against reflexively adding
        "confirmation" conditions without checking whether they're independent enough of the base signal to actually change
        anything.
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
        <li class="mb-1.5">Breadth is checked against the CURRENTLY HELD top-10 while invested, and against a freshly recomputed candidate top-10 while in cash — a different, arguably stricter design (e.g. checking breadth across the FULL 150-stock universe rather than just the top-10) could behave differently.</li>
        <li class="mb-1.5">The per-stock breadth EMA uses the same 200-day span as the main NIFTY 50 signal — this wasn't varied independently.</li>
        <li class="mb-1.5">Zero transaction costs on ANY regime switch — same disclosed omission as reports 42-56.</li>
        <li class="mb-1.5">Cash earns exactly 0% while any variant is out of the market, same convention as reports 03, 42-56.</li>
        <li class="mb-1.5">Only ONE universe (Midcap150) and ONE historical window were tested — a market with more genuine large-cap/midcap divergence than 2008-2026 India could show a bigger effect from breadth confirmation.</li>
        <li class="mb-1.5">Today's fixed Midcap150 constituent list is applied retroactively (survivorship bias). Equal weighting, no F&O-eligibility screen, unadjusted prices, no dividends modeled — same as every other reconstruction here.</li>
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
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap150 Momentum 10 — Breadth Confirmation</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("57_midcap_momentum10_breadth_confirmation.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 57_midcap_momentum10_breadth_confirmation.html")
