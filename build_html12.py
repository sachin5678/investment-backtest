"""Builds 12_momentum10_reconstruction.html from results11.json (+ results10.json
for the side-by-side comparison against the NIFTY200/Top-30 reconstruction).
Same self-contained contract, smooth Catmull-Rom charts, leads with the
"this isn't a real index" + survivorship-bias disclosures."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results11.json") as f:
    R = json.load(f)
with open("results10.json") as f:
    R30 = json.load(f)

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
    mom30 = R30["reconstructed_momentum"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">"NIFTY100 Momentum 10" — A Custom Variant, Not a Real Index</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same published NSE momentum formula as the last report, applied to NIFTY 100 (not 200) selecting the top 10 (not 30) — a smaller, more concentrated construction with no official NSE equivalent.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: Yahoo Finance daily OHLC for {R['universe_size']} NIFTY 100 constituents + ^NSEI + MID150BEES.NS (all already cached from the last report)<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">Two things to know before the numbers below</h2>
          {pill('not a real NSE product', 'negative')}{pill('survivorship bias', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          <span class="font-semibold">First:</span> there is no NSE index called "NIFTY100 Momentum 10" (or Momentum 30). Searched for it directly — the real
          NSE momentum family is NIFTY200 Momentum 30, NIFTY500 Momentum 50, and a couple of midcap/smallcap "Momentum Quality" variants. What follows is the
          real, published Momentum 30 <span class="font-semibold">formula</span>, applied to a different, smaller setup (NIFTY 100 universe, top 10 selected)
          as a custom construction — not a real product you could ever buy, and not validated against any official benchmark.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          <span class="font-semibold">Second, the same survivorship-bias problem from the last report applies here, likely even more so</span>: today's NIFTY 100
          list is used retroactively, and now only 10 stocks are picked at each rebalance — smaller, more concentrated selections tend to swing harder in
          either direction, and here that concentration is being applied to an already hindsight-filtered "winners only" universe. Treat everything below as
          an even more extreme best-case sketch than the last report, not a real strategy result.
        </p>
      </div>
    </div>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — exactly what changed from the last report, and what stayed the same.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          Universe: {pill('NIFTY 100', 'assumption')} (100 stocks, today's list) instead of NIFTY 200. Selection: {pill('top 10', 'assumption')} by the identical
          normalised momentum score, instead of top 30. Everything else is unchanged: 6m/12m risk-adjusted momentum ratios, cross-sectional z-scoring,
          the same asymmetric normalisation, {pill('equal-weighted', 'assumption')} (not free-float market cap × score), rebalanced every June/December.
          {R['num_rebalances']} rebalances computed, {esc(R['start_date'])} to {esc(R['end_date'])} — the same ~17.6-year window as the last report, since all
          100 of today's NIFTY 100 stocks were already in the 200-stock dataset already fetched.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"Reconstructed and NIFTY 50: {esc(R['start_date'])} to {esc(R['end_date'])}, base 100. Midcap: only from {esc(R['midcap_start_date'])} — shorter window, see Limitations.",
                  [("NIFTY100/Top-10 (this report)", pct(mom["net_return_pct"]), win_loss_kind(mom["net_return_pct"])),
                   ("NIFTY200/Top-30 (last report)", pct(mom30["net_return_pct"]), win_loss_kind(mom30["net_return_pct"])),
                   ("NIFTY 50 (actual, full window)", pct(nif["net_return_pct"]), win_loss_kind(nif["net_return_pct"])),
                   ("Midcap (actual, shorter window)", pct(mid["net_return_pct"]), win_loss_kind(mid["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate — same window caveats as above.",
                  [("NIFTY100/Top-10 (this report)", pct(mom["cagr_pct"]), win_loss_kind(mom["cagr_pct"])),
                   ("NIFTY200/Top-30 (last report)", pct(mom30["cagr_pct"]), win_loss_kind(mom30["cagr_pct"])),
                   ("NIFTY 50 (actual, full window)", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"])),
                   ("Midcap (actual, shorter window)", pct(mid["cagr_pct"]), win_loss_kind(mid["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline — same window caveats as above.",
                  [("NIFTY100/Top-10 (this report)", pct(mom["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY200/Top-30 (last report)", pct(mom30["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY 50 (actual, full window)", pct(nif["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap (actual, shorter window)", pct(mid["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("NIFTY100/Top-10 (this report)", f'{mom["longest_underwater_days"]:,} days', "neutral"),
                   ("NIFTY200/Top-30 (last report)", f'{mom30["longest_underwater_days"]:,} days', "neutral"),
                   ("NIFTY 50 (actual, full window)", f'{nif["longest_underwater_days"]:,} days', "neutral"),
                   ("Midcap (actual, shorter window)", f'{mid["longest_underwater_days"]:,} days', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    eq_series = [
        {"name": "NIFTY100/Top-10 (this report)", "color": COL["negative"], "points": mom["equity_curve"]},
        {"name": "NIFTY200/Top-30 (last report)", "color": COL["assumption"], "points": mom30["equity_curve"], "dash": True},
        {"name": "NIFTY 50 (actual, full window)", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
        {"name": f"Midcap (actual, only from {R['midcap_start_date']})", "color": COL["positive"], "points": mid["equity_curve"]},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_recon10", smooth=True)
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the more concentrated top-10 version (red) tracks slightly ahead of the top-30 version (amber) for most of the period; both dwarf the actual NIFTY 50 and midcap lines, for the reasons explained above, not because either reconstruction found a real edge.</p>
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
        {"name": "NIFTY100/Top-10 (this report)", "color": COL["negative"], "points": dd_points(mom["equity_curve"])},
        {"name": "NIFTY200/Top-30 (last report)", "color": COL["assumption"], "points": dd_points(mom30["equity_curve"]), "dash": True},
        {"name": "NIFTY 50 (actual, full window)", "color": COL["text"], "points": dd_points(nif["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_recon10", smooth=True)
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the more concentrated top-10 version actually drew down slightly LESS than the top-30 version on this data ({pct(mom['max_drawdown_pct'],1,signed=False)} vs. {pct(mom30['max_drawdown_pct'],1,signed=False)}) — with only 10-15 years of semi-annual rebalances to judge from, that's more likely to be which specific stocks got picked than a real property of "fewer holdings = less risk."</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    first3 = R["selections_sample"][:3]
    last3 = R["selections_sample"][-3:] if len(R["selections_sample"]) > 3 else []
    def sel_row(s):
        return f"""<tr><td>{esc(s['date'])}</td><td class="text-left" style="text-align:left">{esc(', '.join(t.replace('.NS','') for t in s['tickers']))}</td></tr>"""
    sel_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Sample rebalances — first 3 and last 3 of {R['num_rebalances']}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all 10 selected tickers each time (small enough now to show in full), so you can see how much the picks turn over.</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Rebalance date</th><th class="text-left" style="text-align:left">All 10 selected tickers</th></tr></thead>
        <tbody>{''.join(sel_row(s) for s in first3)}{'<tr><td colspan="2" style="text-align:center;color:#7E97A0">⋯</td></tr>' if last3 else ''}{''.join(sel_row(s) for s in last3)}</tbody>
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
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every other simplification, unchanged from the last report.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Not a real index (repeated for emphasis)</span> — "NIFTY100 Momentum 10" does not exist at NSE; this is the real formula applied to an invented setup.</li>
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Survivorship bias (repeated for emphasis)</span> — today's NIFTY 100 roster, applied retroactively, only contains companies that survived and stayed large to this day.</li>
        <li class="mb-1.5">Only 10 holdings at a time means idiosyncratic, single-stock risk dominates far more than in the top-30 version — one bad pick has 3x the impact.</li>
        <li class="mb-1.5">Midcap's comparison figures cover only {esc(R['midcap_start_date'])}–{esc(R['end_date'])} (that ETF's real trading history), not the full window used for the reconstruction and NIFTY 50.</li>
        <li class="mb-1.5">Weighting is equal-weight, not the real free-float-market-cap × score weighting; F&O-eligibility is not modelled; rebalance dates are approximated as the last trading day of June/December.</li>
        <li class="mb-1.5">All 100 tickers were reused from the last report's automated fetch — not independently re-inspected for listing-day pricing artifacts or bad prints.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for any series shown.</li>
        <li class="mb-1.5">This is a single, fixed reconstruction of an invented setup — it has no real benchmark to check itself against, official or otherwise.</li>
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
<html lang="en"><head><meta charset="utf-8"/><title>NIFTY100 Momentum 10 — Custom Reconstruction</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("12_momentum10_reconstruction.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 12_momentum10_reconstruction.html")
