"""Builds 80_etf_momentum_rotation_top5.html from results79.json."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results79.json") as f:
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
    mo, qt, sa = R["monthly"], R["quarterly"], R["semiannual"]
    nif, ew = R["nifty"], R["equal_weight_all_etfs"]
    sym = R["currency_symbol"]
    top_n, min_elig, uni_size = R["top_n"], R["min_eligible"], R["universe_size"]
    nrb = R["num_rebalances"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">ETF Momentum Rotation — Top {top_n} Out of {uni_size} Distinct NSE ETFs</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">This project's usual momentum formula (6m/12m risk-adjusted return, Z-scored, equal-weight top-{top_n}) applied to a universe of {uni_size} DISTINCT NSE-listed ETFs — sectoral, smart-beta/factor, commodity, and international — instead of individual stocks, at three rebalance cadences: monthly, quarterly, and semi-annual (this project's usual cadence). Compared against NIFTY 50 and against simply holding all {uni_size} ETFs equally weighted, no picking at all.</p>
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
          {pill('picking the top 5 ETFs by momentum LOSES to just holding all of them equally', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Every single cadence tested here — monthly ({pct(mo['cagr_pct'])} CAGR), quarterly ({pct(qt['cagr_pct'])}), and
          semi-annual ({pct(sa['cagr_pct'])}) — trails simply holding all {uni_size} ETFs equally weighted, no picking at all:
          <span class="font-semibold">{pct(ew['cagr_pct'])}</span> CAGR, with a SHALLOWER drawdown too
          ({pct(ew['max_drawdown_pct'],1,signed=False)} vs. every momentum variant's {pct(mo['max_drawdown_pct'],1,signed=False)}–{pct(sa['max_drawdown_pct'],1,signed=False)}).
          All four comfortably beat NIFTY 50 ({pct(nif['cagr_pct'])}) in absolute terms — this is a genuinely strong period for
          ETFs broadly — but concentrating in the "best" 5 by momentum was, over this specific window, a worse idea than not
          picking at all.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          On cadence itself: monthly clearly beats quarterly and semi-annual here — the opposite of report 77's finding on
          individual stocks, where more frequent rebalancing hurt the hero design. ETF-level sector/factor leadership seems
          to rotate faster than individual-stock momentum does, so refreshing the picks more often paid off here even though
          it didn't for report 48's stock-picking design.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — by rebalance cadence, top-5 ETFs", "Compound annual growth rate, identical window for every series.",
                  [("Monthly", pct(mo["cagr_pct"]), win_loss_kind(mo["cagr_pct"])),
                   ("Quarterly", pct(qt["cagr_pct"]), win_loss_kind(qt["cagr_pct"])),
                   ("Semi-annual", pct(sa["cagr_pct"]), win_loss_kind(sa["cagr_pct"])),
                   ("Equal-weight, all ETFs", pct(ew["cagr_pct"]), "positive"),
                   ("NIFTY 50", pct(nif["cagr_pct"]), "neutral")]),
        kpi_card("Max drawdown — by rebalance cadence, top-5 ETFs", "Largest peak-to-trough decline, identical window for every series.",
                  [("Monthly", pct(mo["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Quarterly", pct(qt["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Semi-annual", pct(sa["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Equal-weight, all ETFs", pct(ew["max_drawdown_pct"], 1, signed=False), "positive"),
                   ("NIFTY 50", pct(nif["max_drawdown_pct"], 1, signed=False), "positive")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-1 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All five, side by side</h3>
        {pill('grey row = real benchmark, not a reconstruction', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every series over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row(f"Top-{top_n} ETF momentum — monthly", mo)}
          {row(f"Top-{top_n} ETF momentum — quarterly", qt)}
          {row(f"Top-{top_n} ETF momentum — semi-annual", sa)}
          {row("Equal-weight, all ETFs (no picking)", ew)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Monthly", "color": COL["positive"], "points": mo["equity_curve"]},
        {"name": "Quarterly", "color": "#8B5CF6", "points": qt["equity_curve"]},
        {"name": "Semi-annual", "color": COL["negative"], "points": sa["equity_curve"]},
        {"name": "Equal-weight, all ETFs", "color": COL["assumption"], "points": ew["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_80")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how {sym}100 invested at the start of the window grew under each cadence, linear axis, not log-scaled. The equal-weight (amber, dashed) line sits ABOVE every actively-picked variant.</p>
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
        {"name": "Monthly", "color": COL["positive"], "points": dd_points(mo["equity_curve"])},
        {"name": "Quarterly", "color": "#8B5CF6", "points": dd_points(qt["equity_curve"])},
        {"name": "Semi-annual", "color": COL["negative"], "points": dd_points(sa["equity_curve"])},
        {"name": "Equal-weight, all ETFs", "color": COL["assumption"], "points": dd_points(ew["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=220, chart_id="dd_80")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the equal-weight line is consistently the shallowest — diversifying across all {uni_size} ETFs smooths out sector/factor rotation risk better than concentrating in whichever 5 are currently strongest.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def freq_rows(freq_list):
        return "".join(f"<tr><td>{esc(t)}</td><td>{c}</td></tr>" for t, c in freq_list)

    mechanism_note = f"""
    <div class="{PANEL} mt-6 border-[#6AE4FF]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">The universe, and what actually got picked</h3>{pill('mechanism', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the {uni_size}-ETF candidate universe, real listing dates spanning 2009 to 2024-2025, and which names showed up most often in the top-{top_n} at each cadence.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        A universe-wide floor of {min_elig} simultaneously-eligible ETFs (out of {uni_size} candidates — 26 attempted, 25
        resolved with real data, only REALTYIETF.NS failed) means this backtest only starts once enough of the newer
        sector/factor ETFs have a full year of their own trading history — {esc(R['start_date'])} here, a real but far
        shorter window than the 18-year stock-momentum reports, bounded by how recently many of these ETFs actually
        launched. Monthly ran {nrb['monthly']} rebalances, quarterly {nrb['quarterly']}, semi-annual {nrb['semiannual']} —
        all sharing the identical momentum formula and top-{top_n} selection rule.
      </p>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <p class="{WHAT_THIS_SHOWS} mb-1">Most-picked, monthly</p>
          <table class="data-table"><thead><tr><th>ETF</th><th>Times picked</th></tr></thead><tbody>{freq_rows(mo['pick_frequency'])}</tbody></table>
        </div>
        <div>
          <p class="{WHAT_THIS_SHOWS} mb-1">Most-picked, quarterly</p>
          <table class="data-table"><thead><tr><th>ETF</th><th>Times picked</th></tr></thead><tbody>{freq_rows(qt['pick_frequency'])}</tbody></table>
        </div>
        <div>
          <p class="{WHAT_THIS_SHOWS} mb-1">Most-picked, semi-annual</p>
          <table class="data-table"><thead><tr><th>ETF</th><th>Times picked</th></tr></thead><tbody>{freq_rows(sa['pick_frequency'])}</tbody></table>
        </div>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why picking lost to not picking, here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        This window (roughly 2020-2026) was a strong, broad-based run for almost every ETF in this universe — gold, Nasdaq
        100, FANG+, S&P 500 top 50, and most Indian sectors all rose substantially. When nearly everything in a universe is
        going up, concentrating in only 5 names gives up the benefit of just owning everything — and adds real risk if the
        formula's "top 5" happen to be whichever sector or factor is near the END of its own run rather than the start
        (chasing recent strength is exactly what momentum does, and it doesn't distinguish between a trend that's about to
        continue and one that's about to reverse).
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        This is a genuinely different result from the stock-level momentum reports in this project, where concentrating in
        the top 10 out of 150 stocks clearly beat the broader index. A likely reason: individual stocks have much more
        dispersion in outcomes than a basket of already-diversified ETFs does — momentum has more real signal to find among
        150 individual companies than among 25 ETFs that are each already a basket of dozens of stocks, several of which
        overlap in what they're actually exposed to (e.g. NIFTYBEES and JUNIORBEES both hold large-cap Indian equities).
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
        <li class="mb-1.5">This is a ~6-year window (2020-2026), not 18 years — bounded by how recently many of these ETFs
        actually launched, not by an arbitrary choice. A different, longer-history period could tell a different story.</li>
        <li class="mb-1.5">The {uni_size}-ETF candidate list was hand-picked to be "distinct" (avoiding multiple ETFs tracking
        the identical index) but is not exhaustive — other NSE ETFs exist that weren't included, and some categories (e.g.
        REALTYIETF.NS, attempted but not found on yfinance) are missing entirely.</li>
        <li class="mb-1.5">Some ETFs in this universe are NOT mutually exclusive exposures — NIFTYBEES and JUNIORBEES both
        hold large-cap Indian equities, for instance — so "top 5 out of {uni_size}" isn't guaranteed to be 5 genuinely
        uncorrelated bets.</li>
        <li class="mb-1.5">Zero transaction costs on any rebalance — same disclosed omission as every other reconstruction
        here; the monthly cadence trades far more often per year than semi-annual, so real-world costs would erode its
        currently-best CAGR the most.</li>
        <li class="mb-1.5">ETF prices used here are market prices (Close), not NAV — a thinly-traded ETF's market price can
        diverge briefly from its underlying NAV, a real but usually small effect for these instruments. No dividends
        modeled, unadjusted prices.</li>
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
      {mechanism_note}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>ETF Momentum Rotation — Top 5</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("80_etf_momentum_rotation_top5.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 80_etf_momentum_rotation_top5.html")
