"""Builds 19_sector_momentum_rotation.html from results18.json. Same
self-contained contract, smooth Catmull-Rom charts, plus one new visual not
used in any earlier report: a sector win-count bar (which sectors actually
led, and how often) since that's the whole new idea being tested here."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results18.json") as f:
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
ACCENT_2 = "#8B5CF6"   # 5th chart hue, needed because this report compares 5 series (COL only has 3 accents)

SECTOR_BAR_COLORS = ["#37F083", "#5B9CF6", "#F2B03C", "#8B5CF6", "#F2643C", "#2DD4BF",
                     "#F472B6", "#A3E635", "#FB923C", "#60A5FA", "#E879F9"]


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
      .scrollbox{max-height:280px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
      tr.real-bench td{color:#9FB4BB;}
      .sectorbar{display:flex;height:28px;border-radius:6px;overflow:hidden;border:1px solid #1E3A45;}
      .sectorbar > div{display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;color:#08171E;min-width:0;overflow:hidden;white-space:nowrap;}
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


def sector_bar(win_counts, colors=SECTOR_BAR_COLORS):
    total = sum(win_counts.values())
    segs, legend = [], []
    for i, (sector, n) in enumerate(win_counts.items()):
        c = colors[i % len(colors)]
        w = (n / total) * 100
        label = sector if w > 9 else ""
        segs.append(f'<div style="width:{w:.2f}%;background:{c}" title="{esc(sector)}: {n} rebalance(s)">{esc(label)}</div>')
        legend.append(
            f'<span class="inline-flex items-center gap-1.5 mr-3 mb-1"><span class="inline-block w-2.5 h-2.5 rounded-sm" '
            f'style="background:{c}"></span><span class="text-[12px]" style="color:{COL["text"]}">{esc(sector)} ({n})</span></span>'
        )
    return f'<div class="sectorbar">{"".join(segs)}</div>', "".join(legend)


def build():
    t1, t2 = R["top1x3"], R["top2x3"]
    n10, nif, midetf = R["nifty500_momentum10"], R["nifty"], R["midcap_etf"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Sector-First Momentum Rotation</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Instead of picking momentum stocks out of one fixed index, rank NIFTY 500's sectors by their OWN momentum first, then take the top 3 momentum stocks from whichever sector currently leads.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {R['universe_size']}-stock universe, {R['num_sectors_used']} sectors (third-party classification), {esc(R['start_date'])}–{esc(R['end_date'])}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">The idea, and the honest result up front</h2>
          {pill('a genuinely different selection process', 'neutral')}{pill('underperforms plain top-down momentum', 'negative')}{pill('extreme turnover', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Every earlier momentum reconstruction in this project (reports 11, 12, 14, 16-18) fixes a universe first (NIFTY 200, Midcap 150, NIFTY 500...) and
          ranks stocks within it. This one flips that order: at each rebalance, first rank NIFTY 500's 11 third-party-classified sectors by their own average
          momentum score, then take the top 3 momentum stocks from ONLY the single strongest sector (or top 2 sectors, in the second variant) —
          a bet that sector leadership is itself a useful, exploitable signal on top of stock-level momentum.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          It isn't, on this data. Both rotation variants below <span class="font-semibold">underperform a plain "top 10 momentum stocks straight out of
          the whole NIFTY 500" benchmark</span> — run on the identical universe, dates, and formula — on every measure: lower CAGR, deeper drawdown, and
          longer time underwater. Adding a sector-selection step before the stock picks didn't help; it hurt.
        </p>
      </div>
    </div>
    """

    methodology_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — how the sector call and the stock picks are actually computed. Full derivation in this report's source code.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          Per-stock momentum score: {pill('identical 6m/12m risk-adjusted, cross-sectionally Z-scored formula used in every reconstruction here', 'assumption')}
          — nothing new. Sector score: {pill("simple average of that Z-score across a sector's eligible members", 'assumption')}
          (not cap-weighted — the only market-cap data in this project is a single present-day snapshot, and using it at every historical rebalance would add
          a second look-ahead assumption on top of the sector-tag one that already exists). Rebalanced June/December — the real NIFTY500 Momentum index's
          actual cadence — so this overlays cleanly on the NIFTY500 Momentum-10 benchmark shown throughout. A sector needs
          {pill('5+ eligible members to be ranked at all', 'assumption')}, well below every real sector's actual size (11-97 stocks).
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("Top1x3 (this idea)", pct(t1["net_return_pct"]), win_loss_kind(t1["net_return_pct"])),
                   ("Top2x3", pct(t2["net_return_pct"]), win_loss_kind(t2["net_return_pct"])),
                   ("NIFTY500 Mom-10 (benchmark)", pct(n10["net_return_pct"]), win_loss_kind(n10["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate, identical window for all three.",
                  [("Top1x3 (this idea)", pct(t1["cagr_pct"]), win_loss_kind(t1["cagr_pct"])),
                   ("Top2x3", pct(t2["cagr_pct"]), win_loss_kind(t2["cagr_pct"])),
                   ("NIFTY500 Mom-10 (benchmark)", pct(n10["cagr_pct"]), win_loss_kind(n10["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Top1x3 (this idea)", pct(t1["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Top2x3", pct(t2["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("NIFTY500 Mom-10 (benchmark)", pct(n10["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("Top1x3 (this idea)", f'{t1["longest_underwater_days"]:,}d', "neutral"),
                   ("Top2x3", f'{t2["longest_underwater_days"]:,}d', "neutral"),
                   ("NIFTY500 Mom-10 (benchmark)", f'{n10["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All five, side by side</h3>
        {pill('grey rows = real, un-reconstructed benchmarks', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the two sector-rotation variants against a same-universe, same-dates, same-formula top-down momentum benchmark, plus NIFTY 50 and the real Midcap 150 ETF, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Top1x3 — leading sector, top 3 stocks (this idea)", t1)}
          {row("Top2x3 — top 2 sectors, top 3 stocks each", t2)}
          {row("NIFTY500 Momentum-10 (top-down benchmark)", n10)}
          {row("NIFTY 50 (real index)", nif, "real-bench")}
          {row(f"Midcap 150 ETF, MID150BEES.NS (real, only from {R['midcap_etf_start']})", midetf, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Top1x3 (this idea)", "color": COL["negative"], "points": t1["equity_curve"]},
        {"name": "Top2x3", "color": ACCENT_2, "points": t2["equity_curve"], "dash": True},
        {"name": "NIFTY500 Momentum-10 (benchmark)", "color": COL["positive"], "points": n10["equity_curve"]},
        {"name": "NIFTY 50 (real)", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_19")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the top-down benchmark (green) pulls ahead of both sector-rotation variants for most of the window, not just at the very end.</p>
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
        {"name": "Top1x3 (this idea)", "color": COL["negative"], "points": dd_points(t1["equity_curve"])},
        {"name": "Top2x3", "color": ACCENT_2, "points": dd_points(t2["equity_curve"]), "dash": True},
        {"name": "NIFTY500 Momentum-10 (benchmark)", "color": COL["positive"], "points": dd_points(n10["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_19")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — Top1x3's deepest drawdown ({pct(t1['max_drawdown_pct'],1,signed=False)}) is meaningfully worse than the benchmark's ({pct(n10['max_drawdown_pct'],1,signed=False)}) — concentrating into 3 stocks from one sector adds risk on top of already-losing return.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    t1_bar, t1_legend = sector_bar(t1["sector_win_counts"])
    t2_bar, t2_legend = sector_bar(t2["sector_win_counts"])
    full_turn_pct_1 = t1["full_turnover_rebalances"] / t1["total_rebalances_after_first"] * 100
    full_turn_pct_2 = t2["full_turnover_rebalances"] / t2["total_rebalances_after_first"] * 100

    turnover_panel = f"""
    <div class="{PANEL} mt-6 border-[#F2643C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Which sector actually led, and how often it changed</h3>
        {pill('the real cost of this idea, beyond the return numbers', 'negative')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every rebalance's winning sector(s), counted across all {t1['num_rebalances']} rebalances (June/December, {esc(R['start_date'])}–{esc(R['end_date'])}). No single sector dominates for long — leadership rotates constantly.</p>

      <div class="mb-5">
        <div class="text-[12px] font-semibold text-[#9FB4BB] mb-2">Top1x3 — sector win counts ({t1['num_unique_sectors_used']} of 11 sectors led at least once)</div>
        {t1_bar}
        <div class="mt-2 flex flex-wrap">{t1_legend}</div>
      </div>
      <div class="mb-5">
        <div class="text-[12px] font-semibold text-[#9FB4BB] mb-2">Top2x3 — sector win counts ({t2['num_unique_sectors_used']} of 11 sectors led at least once)</div>
        {t2_bar}
        <div class="mt-2 flex flex-wrap">{t2_legend}</div>
      </div>

      <div class="grid grid-cols-2 gap-4 mt-4">
        <div class="{PANEL_TIGHT}">
          <div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Top1x3 — full portfolio turnover</div>
          <div class="kpi-val mono" style="color:{KIND_COLOR['negative']}">{t1['full_turnover_rebalances']} / {t1['total_rebalances_after_first']} rebalances ({full_turn_pct_1:.0f}%)</div>
          <div class="{MUTED} mt-1">Rebalances where ALL 3 holdings changed — none of the prior 3 stocks carried over. Average overlap with the previous period's holdings: just {t1['avg_ticker_overlap_with_prev_rebalance_pct']}%.</div>
        </div>
        <div class="{PANEL_TIGHT}">
          <div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">Top2x3 — full portfolio turnover</div>
          <div class="kpi-val mono" style="color:{KIND_COLOR['negative']}">{t2['full_turnover_rebalances']} / {t2['total_rebalances_after_first']} rebalances ({full_turn_pct_2:.0f}%)</div>
          <div class="{MUTED} mt-1">Average overlap with the previous period's 6 holdings: {t2['avg_ticker_overlap_with_prev_rebalance_pct']}%.</div>
        </div>
      </div>
      <p class="text-[13px] text-[#C9D6DA] leading-relaxed mt-4">
        Neither of these turnover figures has any transaction cost, slippage, or capital-gains tax charged against it anywhere in this report — see
        Limitations. A strategy that swaps out its entire holding list this often would be considerably more expensive to actually run than a 10-30 stock
        index that reshuffles partially.
      </p>
    </div>
    """

    def sel_rows(sample):
        rows = []
        for s in sample:
            sectors = ", ".join(s["sectors"])
            tickers = ", ".join(t.replace(".NS", "") for t in s["tickers"])
            rows.append(f"""<tr><td>{esc(s['date'])}</td><td class="text-left" style="text-align:left">{esc(sectors)}</td>
            <td class="text-left" style="text-align:left">{esc(tickers)}</td></tr>""")
        return "".join(rows)

    sel_tables = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Sample rebalances — first 3 and last 3</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — which sector(s) led and which stocks got picked, at the start and end of this reconstruction's history.</p>
      <div class="grid grid-cols-1 gap-4">
        <div>
          <div class="text-[12px] font-semibold text-[#9FB4BB] mb-1">Top1x3</div>
          <div class="scrollbox"><table class="data-table">
            <thead><tr><th>Date</th><th style="text-align:left">Leading sector</th><th style="text-align:left">Stocks picked</th></tr></thead>
            <tbody>{sel_rows(t1['selections_sample'])}</tbody></table></div>
        </div>
        <div>
          <div class="text-[12px] font-semibold text-[#9FB4BB] mb-1">Top2x3</div>
          <div class="scrollbox"><table class="data-table">
            <thead><tr><th>Date</th><th style="text-align:left">Leading sectors</th><th style="text-align:left">Stocks picked</th></tr></thead>
            <tbody>{sel_rows(t2['selections_sample'])}</tbody></table></div>
        </div>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why the sector-first idea didn't help here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism behind the weaker result, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        The top-down benchmark picks its top 10 stocks by momentum score from ALL 500 names, wherever they happen to sit sector-wise — if the 10 best
        momentum stocks all happen to cluster in 2-3 sectors, it captures all of them. Top1x3 instead commits FIRST to one sector (by that sector's
        average score) and only THEN looks for winners inside it — so it can end up holding sector #1's 3rd- and 4th-best momentum names while sector
        #2's actual best individual stock, sitting just outside the winning sector, is ignored entirely. Averaging dilutes the signal: a sector with one
        spectacular stock and several mediocre ones can easily be out-ranked by a sector that is uniformly decent, even though the single spectacular
        stock might have been the better pick on its own.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Combined with the extreme turnover shown above (leadership rotating almost every 6 months, {t1['num_unique_sectors_used']} different sectors
        taking a turn at #1), the sector step adds a layer of noise and concentration risk without adding a compensating edge — on this data, momentum
        is a stock-level effect that a sector-averaging step mostly gets in the way of, rather than sharpens.
      </p>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every simplification behind this reconstruction.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5">Sector tags are a third-party present-day classification, applied retroactively to 2008 — NSE does not publish a fetchable sector taxonomy in this project's data sources; a company's ACTUAL sector rarely changes, but this is still a fixed, single-snapshot label used across the whole history, same style of assumption as every quality/fundamentals report in this series.</li>
        <li class="mb-1.5">Sector momentum is a simple (equal-weighted) average of member stocks' Z-scores — a judgment call, not an NSE-published formula (sector rotation isn't a real NSE index methodology at all).</li>
        <li class="mb-1.5">Survivorship bias — today's fixed NIFTY 500 constituent list, applied retroactively to 2008, same as every reconstruction in this project.</li>
        <li class="mb-1.5">Equal-weighted stock picks (33.3% or 16.7% each); no free-float-market-cap × score weighting; no F&O-eligibility screen.</li>
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Zero transaction costs, slippage, or taxes modeled anywhere</span> — the single biggest reason not to read the return numbers as achievable in practice, given the turnover shown above is far higher than any other reconstruction in this project.</li>
        <li class="mb-1.5">Only two variants tested (top 1 sector and top 2 sectors, always 3 stocks per sector) — top-N-per-sector, more sectors, or a cap-weighted sector score are all untested alternatives that could change this result.</li>
        <li class="mb-1.5">A sector needing 5+ eligible members to be "rankable" and the whole-universe 80-stock eligibility floor both bind hardest in the earliest years (2008-2010), when far fewer of today's 500 constituents had 12 months of price history yet.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for any series shown.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    {methodology_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      {full_table}
      {eq_panel}
      {dd_panel}
      {turnover_panel}
      {sel_tables}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Sector-First Momentum Rotation</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("19_sector_momentum_rotation.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 19_sector_momentum_rotation.html")
