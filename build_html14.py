"""Builds 14_midcap_momentum20_gold.html from results13.json. Same
self-contained contract, smooth Catmull-Rom charts, leads with disclosures:
not a real index, survivorship bias, and a data-quality fix applied to gold."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results13.json") as f:
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
            f'<div class="flex-1 min-w-[110px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
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
    sym = R["currency_symbol"]
    mom, nif, mid, gold, blend = R["momentum20"], R["nifty"], R["midcap"], R["gold"], R["blend_50_50"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum-20, and a 50/50 Blend With Gold</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same real NSE momentum formula applied to NIFTY Midcap 150, top 20 instead of the real index's top 50 — then a 50% momentum / 50% gold portfolio, rebalanced semi-annually.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: Yahoo Finance daily OHLC for {R['universe_size']} NIFTY Midcap 150 constituents + {esc(R['gold_ticker'])} + ^NSEI + MID150BEES.NS<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">Three things to know before the numbers below</h2>
          {pill('not a real NSE product', 'negative')}{pill('survivorship bias', 'negative')}{pill('gold data fixed', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          <span class="font-semibold">First:</span> there is no NSE index called "Midcap150 Momentum 20." The real one is
          <span class="font-semibold">Nifty Midcap150 Momentum 50</span> (top 50, not top 20). What follows is the real, published formula applied to a
          smaller, invented selection — same situation as the "NIFTY100 Momentum 10" report earlier in this series.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          <span class="font-semibold">Second, the same survivorship bias as every reconstruction in this series</span> — today's NIFTY Midcap 150 roster is
          used retroactively back to 2008. Midcap membership churns even more than large-cap membership, so this bias is plausibly the strongest of any
          reconstruction so far.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          <span class="font-semibold">Third, a data-quality fix:</span> the gold ETF's raw Yahoo Finance data has a 2-day glitch (2019-12-19/20) where the
          price briefly shows a fake ~99% crash and recovery — verified by hand and excluded before running any of the numbers below (the same kind of fix
          applied to the momentum ETF's listing-day artifact in an earlier report).
        </p>
      </div>
    </div>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — the formula, the universe, and the blend rule.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-2">
          Universe: {pill('NIFTY Midcap 150', 'assumption')} (today's list). Selection: {pill('top 20', 'assumption')} by the same normalised momentum
          score used throughout this project (6m/12m risk-adjusted return, z-scored, asymmetrically normalised). {pill('Equal-weighted', 'assumption')}, not
          free-float-market-cap × score. Rebalanced every {pill('May/November', 'assumption')} (the real Midcap150 Momentum 50's actual cutoff months,
          unlike the June/December used by the other momentum indices in this project). {R['num_rebalances']} rebalances computed,
          {esc(R['start_date'])} to {esc(R['end_date'])}.
        </p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          The 50/50 blend holds the momentum-20 basket and {esc(R['gold_ticker'])} at exactly half-and-half, {pill('reset to 50/50 at the same May/November dates', 'assumption')}
          as the momentum leg's own rebalancing — a judgment call, since no blend-rebalancing frequency was specified.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100. Midcap ETF only from {esc(R['midcap_start_date'])} — shorter window, see Limitations.",
                  [("Momentum-20", pct(mom["net_return_pct"]), win_loss_kind(mom["net_return_pct"])),
                   ("Gold", pct(gold["net_return_pct"]), win_loss_kind(gold["net_return_pct"])),
                   ("50/50 blend", pct(blend["net_return_pct"]), win_loss_kind(blend["net_return_pct"])),
                   ("NIFTY 50", pct(nif["net_return_pct"]), win_loss_kind(nif["net_return_pct"])),
                   ("Midcap ETF (shorter)", pct(mid["net_return_pct"]), win_loss_kind(mid["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate — same window caveat as above.",
                  [("Momentum-20", pct(mom["cagr_pct"]), win_loss_kind(mom["cagr_pct"])),
                   ("Gold", pct(gold["cagr_pct"]), win_loss_kind(gold["cagr_pct"])),
                   ("50/50 blend", pct(blend["cagr_pct"]), win_loss_kind(blend["cagr_pct"])),
                   ("NIFTY 50", pct(nif["cagr_pct"]), win_loss_kind(nif["cagr_pct"])),
                   ("Midcap ETF (shorter)", pct(mid["cagr_pct"]), win_loss_kind(mid["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline — same window caveat as above.",
                  [("Momentum-20", pct(mom["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Gold", pct(gold["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("50/50 blend", pct(blend["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap ETF (shorter)", pct(mid["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("Momentum-20", f'{mom["longest_underwater_days"]:,}d', "neutral"),
                   ("Gold", f'{gold["longest_underwater_days"]:,}d', "neutral"),
                   ("50/50 blend", f'{blend["longest_underwater_days"]:,}d', "positive"),
                   ("NIFTY 50", f'{nif["longest_underwater_days"]:,}d', "neutral"),
                   ("Midcap ETF (shorter)", f'{mid["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    eq_series = [
        {"name": "Momentum-20 (this report)", "color": COL["negative"], "points": mom["equity_curve"]},
        {"name": "50/50 blend with gold", "color": COL["positive"], "points": blend["equity_curve"]},
        {"name": "Gold (GOLDBEES.NS)", "color": COL["assumption"], "points": gold["equity_curve"], "dash": True},
        {"name": "NIFTY 50 (actual)", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_mc20")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the momentum-20 line towers over everything else (for the reasons disclosed above), which is exactly why the blend line sitting so much lower, but so much smoother, is the more informative comparison here.</p>
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
        {"name": "Momentum-20", "color": COL["negative"], "points": dd_points(mom["equity_curve"])},
        {"name": "50/50 blend", "color": COL["positive"], "points": dd_points(blend["equity_curve"])},
        {"name": "Gold", "color": COL["assumption"], "points": dd_points(gold["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=280, chart_id="dd_mc20")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison — the actual finding here</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the 50/50 blend's worst drawdown ({pct(blend['max_drawdown_pct'],1,signed=False)}) is shallower than EITHER leg on its own (momentum-20: {pct(mom['max_drawdown_pct'],1,signed=False)}, gold: {pct(gold['max_drawdown_pct'],1,signed=False)}) — a genuine diversification effect from combining two assets that don't fall at the same time, not an artifact of the momentum reconstruction's own biases.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    rows = []
    for s in R["selections_sample"]:
        rows.append(f"""<tr><td>{esc(s['date'])}</td><td class="text-left" style="text-align:left">{esc(', '.join(t.replace('.NS','') for t in s['tickers']))}</td></tr>""")
    sel_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Sample rebalances — first 3 and last 3 of {R['num_rebalances']}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all 20 selected tickers each time, so you can see the composition genuinely turns over.</p>
      <div class="scrollbox">
      <table class="data-table">
        <thead><tr><th>Rebalance date</th><th class="text-left" style="text-align:left">All 20 selected tickers</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">What's real here and what isn't</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — separating the one trustworthy finding from the ones that aren't.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The blend's absolute return numbers ({pct(blend['net_return_pct'])} net, {pct(blend['cagr_pct'])} CAGR) inherit ALL of the momentum-20 leg's
        survivorship bias — half the portfolio is still "today's known winners projected backward." Don't trust those numbers as real achievable returns.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        The <span class="font-semibold text-[#E6EDF0]">drawdown reduction</span> is a more defensible finding: it comes from gold and midcap-momentum
        stocks not falling at the same time, which is a structural diversification property, not a product of which specific midcap stocks got selected.
        Still worth a caveat: this is ONE ~18-year historical path (2008-2026), which happens to include several periods where gold rallied while equities
        fell (2008, 2011-2012, 2020) — a different window could show a smaller, or larger, diversification benefit.
      </p>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every other simplification made to get this built.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Not a real index (repeated)</span> — "Midcap150 Momentum 20" does not exist at NSE; only Midcap150 Momentum 50 does.</li>
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Survivorship bias (repeated)</span> — today's Midcap 150 roster, applied retroactively, likely the strongest bias of any reconstruction in this series given how much midcap membership turns over.</li>
        <li class="mb-1.5">Weighting is equal-weight, not the real free-float-market-cap × score (capped at the lower of 5% or 5× the stock's Midcap 150 float weight); F&O-eligibility is not modelled.</li>
        <li class="mb-1.5">Midcap ETF's comparison figures cover only {esc(R['midcap_start_date'])}–{esc(R['end_date'])} (its real trading history), not the full window used for momentum-20, gold, and NIFTY 50.</li>
        <li class="mb-1.5">The 50/50 blend's semi-annual rebalance-to-target cadence was not specified by you — it reuses the momentum leg's own schedule as a reasonable default, not an independently justified choice. Monthly or annual rebalancing would give a different result.</li>
        <li class="mb-1.5">All 150 midcap tickers' price data were reused from automated fetches across this project — not individually inspected for corporate-action artifacts the way the gold ETF's glitch was (that one was caught because its magnitude was extreme and obvious).</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for any series, and gold ETFs have a small tracking/storage cost drag versus spot gold that isn't separately called out here.</li>
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
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum-20 + Gold Blend</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("14_midcap_momentum20_gold.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 14_midcap_momentum20_gold.html")
