"""Builds 11_momentum_reconstruction.html from results10.json. Same
self-contained contract, smooth Catmull-Rom charts — but this report leads
with a large, unmissable survivorship-bias disclosure BEFORE any KPI number,
per the honesty rule against dressing up an inflated result."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results10.json") as f:
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
      .scrollbox{max-height:260px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
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
    mom, nif, mid = R["reconstructed_momentum"], R["nifty"], R["midcap"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Reconstructing the Momentum Formula Over 18 Years</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">NSE's real NIFTY200 Momentum 30 methodology, hand-computed on today's NIFTY 200 roster applied retroactively — because the real index's own history isn't downloadable through any source available in this session.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: daily OHLC price data for {R['universe_size']} NIFTY 200 constituents + ^NSEI + MID150BEES.NS<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    # THE lead disclosure — must appear before any KPI number.
    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">Read this BEFORE the numbers below — the headline result is very likely inflated</h2>
          {pill('survivorship bias', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          This reconstruction applies the real momentum-selection formula to <span class="font-semibold">today's</span> list of NIFTY 200 companies, projected
          backward to {esc(R['start_date'])}. That list is, by definition, the roster of companies that <span class="font-semibold">survived and stayed large enough
          to still be in the NIFTY 200 today</span>. Any company that got picked for its momentum in, say, 2011, then collapsed, got delisted, merged away, or simply
          shrank out of the top 200 by now — is invisible to this backtest. It could never be selected, because it isn't on the list this reconstruction searches from.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          That is a one-directional bias: it can only make the reconstructed strategy look better than any momentum strategy actually experienced in real time,
          never worse. The real historical index picked from whichever ~200 stocks were actually in the NIFTY 200 <span class="font-semibold">at each past date</span> —
          including plenty of companies that are gone or irrelevant today. Treat the numbers below as an upper-bound, best-case sketch of "if the momentum formula
          only ever had access to hindsight's winners" — not a claim about what an investor following this rule since 2008 would actually have earned.
        </p>
      </div>
    </div>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — exactly what was computed, and the other simplifications made beyond the survivorship-bias issue above.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          Every {pill('30 June and 31 December', 'assumption')}, each of the {R['universe_size']} stocks with at least a year of price history gets a
          6-month and 12-month "momentum ratio" (return ÷ volatility), which are z-scored against each other and combined into a normalised momentum score
          exactly per NSE's published formula. The {pill('top 30 by that score', 'assumption')} are selected and {pill('equal-weighted', 'assumption')} —
          the real index instead weights by free-float market cap × score (capped 5%), which needs historical market-cap data this project doesn't have access to.
          {R['num_rebalances']} rebalances were computed this way, from {esc(R['start_date'])} (the first date with enough eligible stocks) to {esc(R['end_date'])}.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"Reconstructed momentum and NIFTY 50: {esc(R['start_date'])} to {esc(R['end_date'])} (~17.6 years), base 100. Midcap: only {esc(R['midcap_start_date'])} to {esc(R['end_date'])} — that ETF simply doesn't exist before then, so it is NOT the same window as the other two.",
                  [("Reconstructed momentum", pct(mom["net_return_pct"]), win_loss_kind(mom["net_return_pct"])),
                   ("NIFTY 50 (actual, full window)", pct(nif["net_return_pct"]), win_loss_kind(nif["net_return_pct"])),
                   ("Midcap (actual, shorter window)", pct(mid["net_return_pct"]), win_loss_kind(mid["net_return_pct"]))]),
        kpi_card("CAGR", f"Reconstructed momentum and NIFTY 50 over the same ~17.6-year window; midcap over its own shorter {esc(R['midcap_start_date'])}–{esc(R['end_date'])} window only.",
                  [("Reconstructed momentum", pct(mom["cagr_pct"]), win_loss_kind(mom["cagr_pct"])),
                   ("NIFTY 50 (actual, full window)", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"])),
                   ("Midcap (actual, shorter window)", pct(mid["cagr_pct"]), win_loss_kind(mid["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline — momentum/NIFTY over the full window, midcap over its own shorter window.",
                  [("Reconstructed momentum", pct(mom["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50 (actual, full window)", pct(nif["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap (actual, shorter window)", pct(mid["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak — same window caveat as above.",
                  [("Reconstructed momentum", f'{mom["longest_underwater_days"]:,} days', "neutral"),
                   ("NIFTY 50 (actual, full window)", f'{nif["longest_underwater_days"]:,} days', "neutral"),
                   ("Midcap (actual, shorter window)", f'{mid["longest_underwater_days"]:,} days', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    eq_series = [
        {"name": "Reconstructed momentum (approximation)", "color": COL["assumption"], "points": mom["equity_curve"]},
        {"name": "NIFTY 50 (actual, full window)", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
        {"name": f"Midcap (actual, only from {R['midcap_start_date']})", "color": COL["positive"], "points": mid["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_recon", smooth=True)
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — NIFTY 50's actual line looks almost flat only because the reconstructed line's scale is so much larger (that gap is itself a signal of how much the survivorship bias above is doing the work, not proof of real skill). The midcap line only starts partway through, at {esc(R['midcap_start_date'])} — that ETF didn't exist before then, so it is plotted on a shorter, later stretch of the same time axis, each rebased to 100 at ITS OWN start.</p>
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
        {"name": "Reconstructed momentum", "color": COL["assumption"], "points": dd_points(mom["equity_curve"])},
        {"name": "NIFTY 50 (actual, full window)", "color": COL["text"], "points": dd_points(nif["equity_curve"]), "dash": True},
        {"name": f"Midcap (actual, only from {R['midcap_start_date']})", "color": COL["positive"], "points": dd_points(mid["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_recon", smooth=True)
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — even the survivorship-biased reconstruction doesn't dodge real drawdowns; it fell about as hard as the actual NIFTY and midcap series did (midcap only plotted from its own {esc(R['midcap_start_date'])} start), it just climbed back faster and further.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    first3 = R["selections_sample"][:3]
    last3 = R["selections_sample"][-3:] if len(R["selections_sample"]) > 3 else []
    def sel_row(s):
        return f"""<tr><td>{esc(s['date'])}</td><td>{s['num_selected']}</td>
        <td class="text-left" style="text-align:left">{esc(', '.join(t.replace('.NS','') for t in s['tickers'][:12]))}{'…' if len(s['tickers'])>12 else ''}</td></tr>"""
    sel_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Sample rebalances — first 3 and last 3 of {R['num_rebalances']}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — which of today's NIFTY 200 names got selected, at the start and end of the reconstruction, so you can see the composition is genuinely date-varying, not static.</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Rebalance date</th><th># selected</th><th class="text-left" style="text-align:left">Sample of selected tickers</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in first3)}{'<tr><td colspan="3" style="text-align:center;color:#7E97A0">⋯</td></tr>' if last3 else ''}{''.join(sel_row(s) for s in last3)}</tbody>
      </table>
      </div>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations (in addition to the survivorship-bias warning above)</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every other simplification made to get this reconstruction to run at all.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Survivorship bias (repeated for emphasis)</span> — this is the dominant, likely-inflating factor. See the panel at the top.</li>
        <li class="mb-1.5">Midcap's comparison figures cover only {esc(R['midcap_start_date'])}–{esc(R['end_date'])} (that ETF's real trading history) — NOT the full {esc(R['start_date'])}–{esc(R['end_date'])} window used for the reconstructed momentum series and NIFTY 50. The three are not a like-for-like three-way comparison; midcap is there for context over its own shorter span only.</li>
        <li class="mb-1.5">Weighting is equal-weight across the 30 selected stocks, not the real free-float-market-cap × score weighting (capped 5%) — historical free-float data wasn't available to this project.</li>
        <li class="mb-1.5">The F&O-eligibility screen in the real methodology is not modelled — some selected stocks here may not actually have been F&O-eligible at that historical date.</li>
        <li class="mb-1.5">Rebalance dates are approximated as the last trading day of June/December; the real index rebalances a few weeks later, after a review period.</li>
        <li class="mb-1.5">Several of the 200 stocks show a data start date of exactly 1996-01-01 for multiple different companies at once — almost certainly our data source's own historical-data cutoff for older listings, not each company's true IPO date. This doesn't change results after ~1997 but means "≥1 year of listing history" is really "≥1 year of available price data" for the oldest names.</li>
        <li class="mb-1.5">All 200 tickers were fetched and used automatically — unlike the single-ETF data-quality check done for the momentum ETF in the last report, this dataset was NOT manually inspected stock-by-stock for listing-day pricing artifacts, corporate-action jumps, or bad prints. A bad data point in even one of the 200 series could distort a rebalance's selection or the resulting index level.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for any of the three series shown.</li>
        <li class="mb-1.5">This is a single, fixed reconstruction of one published formula — it is not the official NSE index, has not been checked against any real published historical value of it, and should not be quoted as "the NIFTY200 Momentum 30 Index's actual historical performance."</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      {eq_panel}
      {dd_panel}
      {sel_table}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Momentum Formula Reconstruction — 18 Years</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("11_momentum_reconstruction.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 11_momentum_reconstruction.html")
