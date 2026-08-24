"""Builds 13_quality50_basket.html from results12.json. Same self-contained
contract, smooth Catmull-Rom charts — leads with two disclosures: this is a
static, unrebalanced snapshot (not a real index reconstruction), and it
carries a hindsight/look-ahead bias distinct from (but related to) the
momentum reports' survivorship bias."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results12.json") as f:
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
      .kpi-val{font-size:26px;font-weight:700;letter-spacing:-0.01em;}
      .scrollbox{max-height:420px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
      tr.dropped td{color:#5C737A;text-decoration:line-through;}
    </style>
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


def build():
    sym = R["currency_symbol"]
    q44, q50 = R["quality44"], R["quality50"]
    nif = R["nifty_vs_44"]
    mid = R["midcap_vs_44"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Today's Quality-50 Basket, Bought Once and Held</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">NSE's real Quality-score formula applied to NIFTY 500, ONE snapshot only — bought and never rebalanced, backtested as far back as its constituents' prices allow.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: daily OHLC price data for {R['num_universe']} NIFTY 500 constituents + ~5yr fundamentals per stock + ^NSEI + MID150BEES.NS<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">Two things to know before the numbers below</h2>
          {pill('not a rebalanced index', 'negative')}{pill('hindsight bias', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          <span class="font-semibold">First:</span> this is NOT a simulation of the real, periodically-rebalanced NIFTY500 Quality 50 index — it's a
          basket built ONCE, using today's fundamentals, then bought and held with zero rebalancing for however long the backtest runs. The real index
          re-scores and reshuffles its 50 holdings on a schedule; this doesn't, because it can't — our data source only has ~5 years of annual fundamentals per
          company, with no way to see what any company's ROE or debt looked like as of a rebalance date years ago. Momentum (reports 11-12) could be
          reconstructed over 18 years because its score only needs prices, which are available for decades. Quality's score needs fundamentals, which it doesn't.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          <span class="font-semibold">Second, a different but related bias:</span> the 50 stocks below were picked because they look financially strong
          <span class="font-semibold">today</span>. Company quality (high ROE, low debt, stable earnings) tends to be a slow-moving, persistent
          characteristic — so a company that looks strong now was quite likely also relatively strong a few years ago. Backtesting today's winners
          against yesterday's prices will tend to look good almost by construction. That's not the same one-way survivorship bias as the momentum reports,
          but it rhymes with it: this is not proof "quality investing" beats the market, it's a demonstration of what today's already-known winners' stock
          prices did.
        </p>
      </div>
    </div>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — the exact formula used, and why two baskets are shown, not one.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-2">
          Quality Score = {pill('0.33×Z(ROE) − 0.33×Z(Debt/Equity) − 0.33×Z(5yr EPS growth variability)', 'assumption')}, each metric averaged/measured
          over the trailing ~5 annual fundamentals available (real methodology calls for 5 years; that's also our data source's entire depth, so this happens to
          match by coincidence, not by choice). Of {R['num_universe']} NIFTY 500 stocks, {pill(f"{R['num_eligible']} had usable fundamentals", 'assumption')}
          for all three metrics. The top 50 are weighted by {pill('√(market cap) × score, capped 5%/stock', 'assumption')} — current market cap stands in
          for free-float since this is one snapshot, not a time series.
        </p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          {pill('Six of the top 50 are very recent IPOs', 'assumption')} (under ~3.5 years of trading, some under a year) — including them forces the whole
          basket's backtest down to just {esc(q50['start_date'])}–{esc(q50['end_date'])} (about 9 months). So a second basket, {pill('"Quality-44"', 'assumption')},
          drops those 6 and reweights the remaining 44 — giving a {esc(q44['start_date'])}–{esc(q44['end_date'])} window (~4.4 years) that's far more useful,
          at the cost of no longer being literally "the actual top 50."
        </p>
      </div>
    </div>
    """

    kpis_44 = [
        kpi_card("Net return", f"{esc(q44['start_date'])} to {esc(q44['end_date'])}, base 100.",
                  [("Quality-44 basket", pct(q44["net_return_pct"]), win_loss_kind(q44["net_return_pct"])),
                   ("Midcap (actual)", pct(mid["net_return_pct"]), win_loss_kind(mid["net_return_pct"])),
                   ("NIFTY 50 (actual)", pct(nif["net_return_pct"]), win_loss_kind(nif["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate, identical ~4.4-year window for all three.",
                  [("Quality-44 basket", pct(q44["cagr_pct"]), win_loss_kind(q44["cagr_pct"])),
                   ("Midcap (actual)", pct(mid["cagr_pct"]), win_loss_kind(mid["cagr_pct"])),
                   ("NIFTY 50 (actual)", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Quality-44 basket", pct(q44["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap (actual)", pct(mid["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50 (actual)", pct(nif["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("Quality-44 basket", f'{q44["longest_underwater_days"]:,} days', "neutral"),
                   ("Midcap (actual)", f'{mid["longest_underwater_days"]:,} days', "neutral"),
                   ("NIFTY 50 (actual)", f'{nif["longest_underwater_days"]:,} days', "neutral")]),
    ]
    kpi_grid_44 = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis_44)}</div>'

    kpi_50 = kpi_card(
        f"For completeness — the actual, full top-50 basket (only {esc(q50['start_date'])} to {esc(q50['end_date'])}, ~9 months)",
        "Too short a window to draw any real conclusion from — shown only so the literal top-50 isn't hidden.",
        [("Net return", pct(q50["net_return_pct"]), win_loss_kind(q50["net_return_pct"])),
         ("CAGR", pct(q50["cagr_pct"]), win_loss_kind(q50["cagr_pct"])),
         ("Max drawdown", pct(q50["max_drawdown_pct"], 1, signed=False), "negative"),
         ("Longest underwater", f'{q50["longest_underwater_days"]} days', "neutral")],
    )

    eq_series = [
        {"name": "Quality-44 basket (static, unrebalanced)", "color": COL["positive"], "points": q44["equity_curve"]},
        {"name": "Midcap (actual, same window)", "color": COL["text"], "points": R["midcap_vs_44"]["equity_curve"], "dash": True},
        {"name": "NIFTY 50 (actual, same window)", "color": COL["negative"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=440, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_q44")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(q44['start_date'])} to {esc(q44['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the static quality basket well ahead of both benchmarks over this window; remember this is 44 already-known-strong companies' prices, bought with hindsight of their fundamentals, not a rule that was actually followed in real time.</p>
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
        {"name": "Quality-44 basket", "color": COL["positive"], "points": dd_points(q44["equity_curve"])},
        {"name": "Midcap (actual)", "color": COL["text"], "points": dd_points(R["midcap_vs_44"]["equity_curve"]), "dash": True},
        {"name": "NIFTY 50 (actual)", "color": COL["negative"], "points": dd_points(nif["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_q44")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the quality basket's worst drawdown was actually deeper than NIFTY 50's over this stretch, even though it "should" be the more defensive, low-leverage, stable-earnings basket — a reminder that a handful of individual stock moves can dominate a 44-name equal-conviction basket more than sector-level quality characteristics do.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    rows = []
    for s in R["top50"]:
        dropped = s["days_history"] < R["cutoff_days"]
        rows.append(f"""
        <tr{' class="dropped"' if dropped else ''}>
          <td>{esc(s['ticker'].replace('.NS',''))}</td><td>{pct(s['roe_avg']*100, 1)}</td>
          <td>{s['de_avg']:.2f}</td><td>{s['eps_var']:.2f}</td><td>{s['quality_score']:.3f}</td>
          <td>{pct(s['weight_50']*100, 2, signed=False)}</td><td>{s['days_history']:,}d</td>
        </tr>""")
    top50_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">The full top-50 selection</h3>
        {pill('strikethrough rows = dropped from the 44-basket as recent IPOs', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every stock's inputs (avg. ROE, avg. Debt/Equity, EPS growth variability), its composite score, its weight in the 50-basket, and how many days of price history it actually has.</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Ticker</th><th>Avg. ROE</th><th>Avg. D/E</th><th>EPS-growth variability</th><th>Quality score</th><th>Weight (50-basket)</th><th>Price history</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
      </div>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations (in addition to the two warnings above)</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every other simplification made to get this basket built at all.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Not a rebalanced index, and never will be re-scored in this report</span> — it's frozen at today's fundamentals forever; a real quality index would drop a company the moment its ROE or debt deteriorated, this basket would not.</li>
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Hindsight bias</span> — see the lead disclosure. Persistent-characteristic selection bias is real even though it's not identical to momentum's survivorship bias.</li>
        <li class="mb-1.5">{R['num_universe'] - R['num_eligible']} of 500 stocks were excluded for missing/unusable fundamentals (no balance sheet or income statement data, non-positive equity, or too few years of EPS to measure variability) — not because they're low quality, but because our data source's coverage of them is incomplete.</li>
        <li class="mb-1.5">ROE and D/E are averaged over whatever annual fundamentals our data source provides (often exactly 4-5 data points) — a genuinely noisy estimate for a "5-year" characteristic, and financial-sector companies' balance sheets (with debt inherent to their business model) may not compare meaningfully to industrials' on the same D/E scale.</li>
        <li class="mb-1.5">None of the 500 companies' fundamentals were individually spot-checked against their actual annual reports — a few outliers (e.g. unusually negative D/E for at least one selected stock) suggest at least some noise or data quirks from the automated data extraction.</li>
        <li class="mb-1.5">Weighting uses TODAY's market cap as the free-float proxy — reasonable for a single snapshot, but not how the real index (which re-measures free-float at every rebalance) actually works.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for the basket or either benchmark.</li>
        <li class="mb-1.5">This is a single, fixed selection computed once — there is no sensitivity test on the ~3.5-year IPO cutoff, the weighting formula, or the eligibility rules, and no comparison against the real index's own published returns.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid_44}
      <div class="mt-6">{kpi_50}</div>
      {eq_panel}
      {dd_panel}
      {top50_table}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Quality-50 Static Basket — NIFTY 500</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("13_quality50_basket.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 13_quality50_basket.html")
