"""Builds 21_nasdaq100_momentum10.html from results20.json. Same
self-contained contract, smooth Catmull-Rom charts, first report on a
non-Indian market."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results20.json") as f:
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
ACCENT_2 = "#8B5CF6"   # 4th chart hue, needed for the NASDAQ-vs-Midcap 4-series comparison


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
      .scrollbox{max-height:240px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
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
    mom, qqq, spx = R["nasdaq100_momentum10"], R["qqq"], R["sp500"]
    sym = R["currency_symbol"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">"NASDAQ100 Momentum 10" — the First Non-Indian Reconstruction</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">The identical momentum formula used throughout this project (reports 11, 12, 14-19), applied to today's Nasdaq-100 constituents instead of an NSE universe — starting right before the dot-com crash.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {R['universe_size']}-stock universe, {esc(R['start_date'])}–{esc(R['end_date'])} · all figures in USD<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">Read this before the number below impresses you</h2>
          {pill('not a real Nasdaq index', 'negative')}{pill('the strongest survivorship bias in this whole project', 'negative')}{pill('backtest starts right before the dot-com crash', 'neutral')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          This backtest's universe is TODAY's 102 Nasdaq-100 constituents — companies we know, with 26 years of hindsight, turned out to be winners —
          applied retroactively all the way back to 2000. The real Nasdaq-100 in 2000 looked very different: dozens of names that were actually in the
          index back then (many dot-com-era darlings among them) were removed over the following few years as they collapsed or were delisted, and this
          backtest cannot see any of them — it only ever sees the 102 survivors sitting in the index today. Every other reconstruction in this project
          carries the same "today's fixed list, applied backward" bias, but it matters MUCH more here: this window includes the 2000-2002 crash, exactly
          the period when the real Nasdaq-100's membership churned hardest.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          None of that means the number below is fake — the formula runs correctly, and today's 102 constituents genuinely did produce these prices. It
          means <span class="font-semibold">an investor actually running this exact strategy in 2000, using the REAL Nasdaq-100 list as it existed then,
          would almost certainly have gotten a substantially worse result</span> than what's shown here — likely holding several of the crash's biggest
          losers at some point, which this backtest structurally cannot simulate.
        </p>
      </div>
    </div>
    """

    methodology_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — the formula, unchanged from every earlier reconstruction in this project.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          {pill('6m/12m risk-adjusted momentum, z-scored, asymmetrically normalised', 'assumption')} — identical formula throughout this project —
          {pill('equal-weighted top 10', 'assumption')}, rebalanced June/December (a borrowed convention — Nasdaq publishes no real "momentum" factor
          index to anchor a cadence to). {R['universe_size']}-stock universe, {esc(R['start_date'])}–{esc(R['end_date'])}, {R['num_rebalances']} rebalances.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['start_date'])} to {esc(R['end_date'])}, base 100.",
                  [("NASDAQ100 Momentum-10", pct(mom["net_return_pct"]), win_loss_kind(mom["net_return_pct"])),
                   ("QQQ (real ETF)", pct(qqq["net_return_pct"]), win_loss_kind(qqq["net_return_pct"])),
                   ("S&P 500", pct(spx["net_return_pct"]), win_loss_kind(spx["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate, identical 26-year window for all three.",
                  [("NASDAQ100 Momentum-10", pct(mom["cagr_pct"]), win_loss_kind(mom["cagr_pct"])),
                   ("QQQ (real ETF)", pct(qqq["cagr_pct"]), win_loss_kind(qqq["cagr_pct"])),
                   ("S&P 500", pct(spx["cagr_pct"]), win_loss_kind(spx["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline — QQQ's includes the full dot-com crash.",
                  [("NASDAQ100 Momentum-10", pct(mom["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("QQQ (real ETF)", pct(qqq["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("S&P 500", pct(spx["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("NASDAQ100 Momentum-10", f'{mom["longest_underwater_days"]:,}d', "neutral"),
                   ("QQQ (real ETF)", f'{qqq["longest_underwater_days"]:,}d', "neutral"),
                   ("S&P 500", f'{spx["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All three, side by side</h3>
        {pill('grey row = the real, un-reconstructed ETF', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the custom reconstruction against the real QQQ ETF and the S&P 500, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. All figures in USD.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("NASDAQ100 Momentum-10 (custom, not a real index)", mom)}
          {row("QQQ — Invesco Nasdaq-100 ETF (real)", qqq, "real-bench")}
          {row("S&P 500 (real)", spx, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "NASDAQ100 Momentum-10", "color": COL["positive"], "points": mom["equity_curve"]},
        {"name": "QQQ (real ETF)", "color": COL["text"], "points": qqq["equity_curve"], "dash": True},
        {"name": "S&P 500", "color": COL["muted"], "points": spx["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_21")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — on this linear scale QQQ and the S&P 500 look nearly flat purely because the momentum line's end value is so much larger; that's an honest consequence of the true numbers, not a distortion — see the exact figures in the table above, and read the survivorship-bias warning before treating the gap at face value.</p>
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
        {"name": "NASDAQ100 Momentum-10", "color": COL["positive"], "points": dd_points(mom["equity_curve"])},
        {"name": "QQQ (real ETF)", "color": COL["text"], "points": dd_points(qqq["equity_curve"]), "dash": True},
        {"name": "S&P 500", "color": COL["muted"], "points": dd_points(spx["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_21")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison — the dot-com crash, up close</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — QQQ's real drawdown ({pct(qqq['max_drawdown_pct'],1,signed=False)}) is far deeper than the momentum reconstruction's ({pct(mom['max_drawdown_pct'],1,signed=False)}) — a genuine effect of rotating toward whatever's working rather than holding a fixed 100-stock cap-weighted basket all the way down, though the survivorship bias above means even momentum's own drawdown is probably understated relative to what really happened to a 2000-era portfolio.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_rows(sample):
        return "".join(f"""<tr><td>{esc(s['date'])}</td><td class="text-left" style="text-align:left">{esc(', '.join(s['tickers']))}</td></tr>""" for s in sample)

    sel_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Sample rebalances — first 3 and last 3</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — which stocks got selected at the start and end of this reconstruction's 26-year history. The very first rebalance (June 2000) is the clearest illustration of the survivorship-bias warning above — it already includes names like NVDA and AMD that we now know became enormous winners, precisely because it's built from today's list looking backward.</p>
      <div class="scrollbox"><table class="data-table"><tbody>{sel_rows(R['selections_sample'])}</tbody></table></div>
    </div>
    """

    # --- last 5 years: the same strategy, a MUCH weaker survivorship-bias window ---
    mom5, qqq5, spx5 = R["nasdaq100_momentum10_5y"], R["qqq_5y"], R["sp500_5y"]

    five_yr_header = f"""
    <div class="px-10 pt-10">
      <div class="{PANEL} border-2 border-[#37F083]/50">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">The Last 5 Years — a Much Fairer Test</h2>
          {pill('same strategy, same formula, same rebalances', 'neutral')}{pill('far less survivorship bias', 'positive')}{pill('drawdown edge disappears', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Same exact reconstruction, windowed down to {esc(R['five_year_start_date'])}–{esc(R['five_year_end_date'])} ({R['five_year_num_rebalances']}
          rebalances) and rebased to 100 at that window's own start. Today's 102-constituent list is a MUCH more accurate reflection of what was actually
          investable 5 years ago than of the year 2000 — Nasdaq-100 membership simply hasn't churned nearly as much recently — so this is a genuinely
          fairer test of the formula than the headline 26-year number above.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The return edge holds up: {pct(mom5['cagr_pct'])} CAGR vs. QQQ's {pct(qqq5['cagr_pct'])} and the S&P 500's {pct(spx5['cagr_pct'])}. But the
          DRAWDOWN story flips: over the full 26 years, momentum's drawdown looked shallower than QQQ's largely because the survivorship-biased universe
          let it dodge the worst of the dot-com crash. Over this fairer 5-year window, with no crash of that scale to dodge, the concentrated 10-stock
          book actually has a <span class="font-semibold">DEEPER</span> drawdown than the diversified 100-stock QQQ
          ({pct(mom5['max_drawdown_pct'],1,signed=False)} vs. {pct(qqq5['max_drawdown_pct'],1,signed=False)}) — the honest risk profile of concentration,
          without the crash-avoidance artifact propping it up.
        </p>
      </div>
    </div>
    """

    kpis_5y = [
        kpi_card("Net return (5y)", f"{esc(R['five_year_start_date'])} to {esc(R['five_year_end_date'])}, base 100.",
                  [("NASDAQ100 Momentum-10", pct(mom5["net_return_pct"]), win_loss_kind(mom5["net_return_pct"])),
                   ("QQQ (real ETF)", pct(qqq5["net_return_pct"]), win_loss_kind(qqq5["net_return_pct"])),
                   ("S&P 500", pct(spx5["net_return_pct"]), win_loss_kind(spx5["net_return_pct"]))]),
        kpi_card("CAGR (5y)", "Compound annual growth rate, identical 5-year window for all three.",
                  [("NASDAQ100 Momentum-10", pct(mom5["cagr_pct"]), win_loss_kind(mom5["cagr_pct"])),
                   ("QQQ (real ETF)", pct(qqq5["cagr_pct"]), win_loss_kind(qqq5["cagr_pct"])),
                   ("S&P 500", pct(spx5["cagr_pct"]), win_loss_kind(spx5["cagr_pct"]))]),
        kpi_card("Max drawdown (5y)", "Largest peak-to-trough decline within this 5-year window only.",
                  [("NASDAQ100 Momentum-10", pct(mom5["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("QQQ (real ETF)", pct(qqq5["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("S&P 500", pct(spx5["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater (5y)", "Longest stretch, in calendar days, below a prior peak within this window.",
                  [("NASDAQ100 Momentum-10", f'{mom5["longest_underwater_days"]:,}d', "neutral"),
                   ("QQQ (real ETF)", f'{qqq5["longest_underwater_days"]:,}d', "neutral"),
                   ("S&P 500", f'{spx5["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid_5y = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis_5y)}</div>'

    eq_series_5y = [
        {"name": "NASDAQ100 Momentum-10 (5y)", "color": COL["positive"], "points": mom5["equity_curve"]},
        {"name": "QQQ (real ETF, 5y)", "color": COL["text"], "points": qqq5["equity_curve"], "dash": True},
        {"name": "S&P 500 (5y)", "color": COL["muted"], "points": spx5["equity_curve"], "dash": True},
    ]
    eq_svg_5y, eq_legend_5y = line_chart(eq_series_5y, height=380, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_21_5y")
    eq_panel_5y = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — last 5 years only</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the same three series, rebased fresh at {esc(R['five_year_start_date'])} so the recent-period comparison isn't dominated by the 26-year chart's scale.</p>
      <div class="flex items-center mb-2">{eq_legend_5y}</div>
      {eq_svg_5y}
    </div>
    """

    dd_series_5y = [
        {"name": "NASDAQ100 Momentum-10 (5y)", "color": COL["positive"], "points": dd_points(mom5["equity_curve"])},
        {"name": "QQQ (real ETF, 5y)", "color": COL["text"], "points": dd_points(qqq5["equity_curve"]), "dash": True},
        {"name": "S&P 500 (5y)", "color": COL["muted"], "points": dd_points(spx5["equity_curve"]), "dash": True},
    ]
    dd_svg_5y, dd_legend_5y = area_underwater_chart(dd_series_5y, height=220, chart_id="dd_21_5y")
    dd_panel_5y = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown — last 5 years only</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — without a dot-com-scale crash to dodge, the concentrated 10-stock book's own drawdown ({pct(mom5['max_drawdown_pct'],1,signed=False)}) is now the DEEPEST of the three, not the shallowest.</p>
      <div class="flex items-center mb-2">{dd_legend_5y}</div>
      {dd_svg_5y}
    </div>
    """

    sel_table_5y = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Every rebalance in the last 5 years, in full</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all {R['five_year_num_rebalances']} rebalances since {esc(R['five_year_start_date'])} — small enough to show every one, not a sample. Compare these picks (NVDA, META, PLTR, MSTR, CRWD, RKLB...) to the 2000-era sample above — these are today's actual momentum leaders, not hindsight-selected dot-com survivors.</p>
      <div class="scrollbox"><table class="data-table"><tbody>{sel_rows(R['five_year_selections'])}</tbody></table></div>
    </div>
    """

    # --- vs. Midcap150 Momentum 10 (report 16), same 2009-today window ---
    cn, cm = R["cmp_nasdaq_momentum10"], R["cmp_midcap_momentum10"]
    cq, cnf = R["cmp_qqq"], R["cmp_nifty50"]
    nasdaq_edge = cn["cagr_pct"] - cq["cagr_pct"]
    midcap_edge = cm["cagr_pct"] - cnf["cagr_pct"]

    vs_header = f"""
    <div class="px-10 pt-10">
      <div class="{PANEL} border-2 border-[#8B5CF6]/50">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">NASDAQ100 vs. Midcap150 Momentum-10 — the Same Window</h2>
          {pill('India wins on both return and risk here', 'positive')}{pill('not FX-adjusted — USD vs INR, each in its own currency', 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          Both reconstructions, recomputed fresh at full daily resolution and intersected onto the IDENTICAL calendar window —
          {esc(R['vs_midcap_start_date'])} to {esc(R['vs_midcap_end_date'])} (~17.6 years), the longest span both can share since Midcap150 Momentum 10's
          own history only starts December 2008. No currency conversion is applied: this overlays USD growth and INR growth on the same rebased-to-100
          scale, comparing how much each market's version of the strategy grew in its OWN currency — not what a single investor converting between the
          two would have actually realised after FX moves.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          On that basis: <span class="font-semibold">Midcap150 Momentum 10 beat NASDAQ100 Momentum 10 on both CAGR ({pct(cm['cagr_pct'])} vs.
          {pct(cn['cagr_pct'])}) AND max drawdown ({pct(cm['max_drawdown_pct'],1,signed=False)} vs. {pct(cn['max_drawdown_pct'],1,signed=False)})</span> —
          despite NIFTY 50 itself badly trailing QQQ as a plain passive benchmark over the same window ({pct(cnf['cagr_pct'])} vs. {pct(cq['cagr_pct'])}
          CAGR). See the honesty note below for what that combination actually implies.
        </p>
      </div>
    </div>
    """

    def row_vs(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    vs_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All four, side by side — identical window</h3>
        {pill('grey rows = passive benchmarks, not momentum strategies', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — {esc(R['vs_midcap_start_date'])} to {esc(R['vs_midcap_end_date'])}, both momentum reconstructions plus each market's own real passive benchmark.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row_vs("Midcap150 Momentum-10 (India, ₹)", cm)}
          {row_vs("NASDAQ100 Momentum-10 (USA, $)", cn)}
          {row_vs("NIFTY 50 (India, real, ₹)", cnf, "real-bench")}
          {row_vs("QQQ (USA, real ETF, $)", cq, "real-bench")}
        </tbody>
      </table>
    </div>
    """

    eq_series_vs = [
        {"name": "Midcap150 Momentum-10 (₹)", "color": COL["positive"], "points": cm["equity_curve"]},
        {"name": "NASDAQ100 Momentum-10 ($)", "color": ACCENT_2, "points": cn["equity_curve"]},
        {"name": "NIFTY 50 (₹, real)", "color": COL["muted"], "points": cnf["equity_curve"], "dash": True},
        {"name": "QQQ ($, real)", "color": COL["text"], "points": cq["equity_curve"], "dash": True},
    ]
    eq_svg_vs, eq_legend_vs = line_chart(eq_series_vs, height=420, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_21_vs")
    eq_panel_vs = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — same window, each currency rebased separately</h3>
        {pill('not FX-adjusted', 'assumption')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — Midcap150 Momentum-10 (green, ₹) pulls ahead of NASDAQ100 Momentum-10 (violet, $) for most of this shared window.</p>
      <div class="flex items-center mb-2">{eq_legend_vs}</div>
      {eq_svg_vs}
    </div>
    """

    dd_series_vs = [
        {"name": "Midcap150 Momentum-10 (₹)", "color": COL["positive"], "points": dd_points(cm["equity_curve"])},
        {"name": "NASDAQ100 Momentum-10 ($)", "color": ACCENT_2, "points": dd_points(cn["equity_curve"])},
        {"name": "NIFTY 50 (₹, real)", "color": COL["muted"], "points": dd_points(cnf["equity_curve"]), "dash": True},
        {"name": "QQQ ($, real)", "color": COL["text"], "points": dd_points(cq["equity_curve"]), "dash": True},
    ]
    dd_svg_vs, dd_legend_vs = area_underwater_chart(dd_series_vs, height=260, chart_id="dd_21_vs")
    dd_panel_vs = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown — same window</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — Midcap150 Momentum-10's drawdown ({pct(cm['max_drawdown_pct'],1,signed=False)}) is shallower than NASDAQ100 Momentum-10's ({pct(cn['max_drawdown_pct'],1,signed=False)}) over this identical window — the opposite of what the full 26-year NASDAQ figure alone would have suggested, since that figure benefited from dodging the dot-com crash via survivorship bias, a crash this shorter shared window doesn't include at all.</p>
      <div class="flex items-center mb-2">{dd_legend_vs}</div>
      {dd_svg_vs}
    </div>
    """

    vs_honesty = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">What "India wins" actually means here</h3>{pill('the momentum EDGE, not just the raw number', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — separating "which market did better passively" from "where did the momentum formula add more value."</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        As a plain passive bet with no strategy at all, the US market clearly won this window: QQQ compounded at {pct(cq['cagr_pct'])} vs. NIFTY 50's
        {pct(cnf['cagr_pct'])}. But the momentum FORMULA's own added value — its CAGR minus its own market's passive benchmark — was
        <span class="font-semibold">+{midcap_edge:.1f} percentage points in India</span> (Midcap150 Momentum-10 vs. NIFTY 50) versus only
        <span class="font-semibold">+{nasdaq_edge:.1f} points in the US</span> (NASDAQ100 Momentum-10 vs. QQQ) over the identical window. The momentum
        effect itself was simply stronger, relative to each market's own baseline, in India than in the US over these 17.6 years.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        Both reconstructions still carry this project's usual survivorship bias (today's fixed constituent list applied backward), and neither market's
        version of that bias is identical in strength — India's post-2008 window includes far less constituent churn than the same window would for
        Nasdaq, but it isn't zero either. Treat the size of the gap, not just its direction, with appropriate caution.
      </p>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">How this compares to the Indian reconstructions</h3>{pill('cross-market framing, not a rigorous comparison', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — putting this result next to report 16's Midcap150 Momentum 10 (India), for interest only.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Report 16's Midcap150 Momentum 10 produced +40.6% CAGR over 2008-12-31–2026-08-24 (₹, India); this NASDAQ100 Momentum 10 produced
        {pct(mom['cagr_pct'])} CAGR over {esc(R['start_date'])}–{esc(R['end_date'])} ($, USA) — a longer window that includes the dot-com crash the
        Indian backtest's post-2008 window never faces. These are NOT directly comparable numbers: different currencies with no FX adjustment,
        different time windows, different market regimes, and — as detailed above — meaningfully different DEGREES of survivorship bias baked into
        each reconstruction's starting universe.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        What both share: applying the identical price-only momentum formula to a fixed, present-day equity universe and rolling it backward produced a
        large, positive edge over that market's own passive benchmark in BOTH cases. That's a consistent pattern across two very different markets — but
        given how much of each result rests on hindsight-selected survivors, it's evidence that the FORMULA behaves sensibly, not proof that either
        number is achievable by a real investor starting from scratch at that historical date.
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
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Survivorship bias, more severe than any other report in this project</span> — today's 102 Nasdaq-100 constituents, applied retroactively through the 2000-2002 dot-com crash, when the real index's membership churned heavily. See the lead disclosure above.</li>
        <li class="mb-1.5">"NASDAQ100 Momentum 10" is not a real Nasdaq or Invesco product — no such index exists; this is a custom construction using this project's own formula.</li>
        <li class="mb-1.5">Equal-weighted, not free-float-market-cap × score — no official weighting rule exists here to defer to.</li>
        <li class="mb-1.5">June/December rebalance cadence is borrowed from this project's NIFTY200 Momentum convention, not a real Nasdaq schedule.</li>
        <li class="mb-1.5">Zero transaction costs, slippage, or taxes modeled on any of the {R['num_rebalances']} rebalances.</li>
        <li class="mb-1.5">Prices are unadjusted (no dividends) for every series shown, including QQQ and the S&P 500 — both indices' real total-return histories, with dividends reinvested, would show meaningfully higher CAGR than the price-only figures here.</li>
        <li class="mb-1.5">Several of today's constituents (Palantir, CoreWeave, SpaceX, Nebius, Rocket Lab, Astera Labs, and others) IPO'd within the last few years — they simply weren't eligible (via the 6m/12m price-history screen) for most of this backtest's rebalances, and only entered the selectable pool recently.</li>
        <li class="mb-1.5">This is a single, fixed historical path with no out-of-sample validation — 2000-2026 is one specific 26-year window, not a guarantee of future behaviour.</li>
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
      {sel_table}
    </div>
    {five_yr_header}
    <div class="px-10 py-6">
      {kpi_grid_5y}
      {eq_panel_5y}
      {dd_panel_5y}
      {sel_table_5y}
    </div>
    {vs_header}
    <div class="px-10 py-6">
      {vs_table}
      {eq_panel_vs}
      {dd_panel_vs}
      {vs_honesty}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>NASDAQ100 Momentum 10</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("21_nasdaq100_momentum10.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 21_nasdaq100_momentum10.html")
