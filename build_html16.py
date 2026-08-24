"""Builds 16_smallcap_midcap_momentum_compare.html from results15.json.
Same self-contained contract, smooth Catmull-Rom charts, leads with the
"none of these are real products" + survivorship-bias disclosures."""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results15.json") as f:
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
      .scrollbox{max-height:220px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
      tr.real-bench td{color:#9FB4BB;}
    </style>
    """


def kpi_card(label, definition, cols):
    col_html = []
    for col_label, value_str, kind in cols:
        color = KIND_COLOR[kind]
        col_html.append(
            f'<div class="flex-1 min-w-[100px]"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(col_label)}</div>'
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
    sc20, sc10, mc10 = R["smallcap20"], R["smallcap10"], R["midcap10"]
    nif, scidx, midetf = R["nifty"], R["smallcap_index"], R["midcap_etf"]

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Smallcap Momentum-20 vs. Smallcap Momentum-10 vs. Midcap Momentum-10</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Three custom momentum reconstructions, same formula, different universes and selection sizes — none of them a real NSE product.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          Data: daily OHLC price data for {R['smallcap_universe_size']} NIFTY Smallcap 250 + {R['midcap_universe_size']} NIFTY Midcap 150 constituents + ^NSEI + NIFTYSMLCAP250.NS + MID150BEES.NS<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3">
          <h2 class="text-lg font-bold text-[#E6EDF0]">None of these three are real NSE products</h2>
          {pill('not real indices', 'negative')}{pill('survivorship bias', 'negative')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          There is no pure-momentum-only smallcap index at NSE — the real one, <span class="font-semibold">Nifty Smallcap250 Momentum Quality 100</span>,
          combines momentum AND quality (ROE/debt/EPS) into one hybrid score, selects the top 100, and caps weights at 3%. That's a different formula
          from what's used here. The real midcap index is <span class="font-semibold">Nifty Midcap150 Momentum 50</span> (top 50, not top 10). All three
          reconstructions below apply the plain momentum-only formula used throughout this project instead, so they're directly comparable to each other —
          but not to any product you could actually buy.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          Same survivorship bias as every reconstruction in this series — today's fixed universe, applied retroactively to 2008. This is likely the
          <span class="font-semibold">strongest bias of any report so far</span>: smallcap index membership churns even faster than midcap's, so "today's
          NIFTY Smallcap 250" excludes an especially large fraction of whatever actually made up the smallcap universe back in 2008-2015.
        </p>
      </div>
    </div>
    """

    definitions_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — the shared formula, and the one data gap encountered.</p>
        <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
          All three: {pill('6m/12m risk-adjusted momentum, z-scored, asymmetrically normalised', 'assumption')} — the identical formula used throughout this
          project — {pill('equal-weighted', 'assumption')} (not free-float market cap × score), rebalanced every {pill('June/December', 'assumption')}
          (smallcap has no real momentum index to anchor a rebalance calendar to, so this reuses the NIFTY200 Momentum 30 convention). 2 of 250 smallcap
          tickers ({esc(', '.join(t.replace('.NS','') for t in R['excluded_smallcap_tickers']))}) returned no price data at all and are
          excluded — a data gap, not a judgment call.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("Net return", f"{esc(R['common_start'])} to {esc(R['common_end'])}, base 100.",
                  [("Smallcap Momentum-20", pct(sc20["net_return_pct"]), win_loss_kind(sc20["net_return_pct"])),
                   ("Smallcap Momentum-10", pct(sc10["net_return_pct"]), win_loss_kind(sc10["net_return_pct"])),
                   ("Midcap Momentum-10", pct(mc10["net_return_pct"]), win_loss_kind(mc10["net_return_pct"]))]),
        kpi_card("CAGR", "Compound annual growth rate, identical ~17.6-year window for all three.",
                  [("Smallcap Momentum-20", pct(sc20["cagr_pct"]), win_loss_kind(sc20["cagr_pct"])),
                   ("Smallcap Momentum-10", pct(sc10["cagr_pct"]), win_loss_kind(sc10["cagr_pct"])),
                   ("Midcap Momentum-10", pct(mc10["cagr_pct"]), win_loss_kind(mc10["cagr_pct"]))]),
        kpi_card("Max drawdown", "Largest peak-to-trough decline over the same window.",
                  [("Smallcap Momentum-20", pct(sc20["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Smallcap Momentum-10", pct(sc10["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Midcap Momentum-10", pct(mc10["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Longest time underwater", "Longest stretch, in calendar days, below a prior peak.",
                  [("Smallcap Momentum-20", f'{sc20["longest_underwater_days"]:,}d', "neutral"),
                   ("Smallcap Momentum-10", f'{sc10["longest_underwater_days"]:,}d', "neutral"),
                   ("Midcap Momentum-10", f'{mc10["longest_underwater_days"]:,}d', "neutral")]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, is_bench=False):
        cls = ' class="real-bench"' if is_bench else ""
        return f"""<tr{cls}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">All six, side by side</h3>
        {pill('grey rows = real, un-reconstructed indices', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the three custom reconstructions against the three real, actually-tradable/trackable series over the identical {esc(R['common_start'])}–{esc(R['common_end'])} window.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Smallcap Momentum-20 (custom)", sc20)}
          {row("Smallcap Momentum-10 (custom)", sc10)}
          {row("Midcap Momentum-10 (custom)", mc10)}
          {row("NIFTY 50 (real index)", nif, True)}
          {row("NIFTY Smallcap 250 (real index)", scidx, True)}
          {row(f"Midcap 150 ETF, MID150BEES.NS (real, only from {R['midcap_etf_start']})", midetf, True)}
        </tbody>
      </table>
    </div>
    """

    eq_series = [
        {"name": "Smallcap Momentum-20", "color": COL["negative"], "points": sc20["equity_curve"]},
        {"name": "Smallcap Momentum-10", "color": COL["assumption"], "points": sc10["equity_curve"], "dash": True},
        {"name": "Midcap Momentum-10", "color": COL["positive"], "points": mc10["equity_curve"]},
        {"name": "NIFTY 50 (real)", "color": COL["text"], "points": nif["equity_curve"], "dash": True},
        {"name": "NIFTY Smallcap 250 (real)", "color": COL["muted"], "points": scidx["equity_curve"], "dash": True},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, value_fmt=lambda v: f"{v:,.0f}", chart_id="eq_3way")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['common_start'])} to {esc(R['common_end'])}</h3>
        {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all three custom reconstructions dwarf the real indices, for the survivorship-bias reasons disclosed above, not because any of them found a real edge.</p>
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
        {"name": "Smallcap Momentum-20", "color": COL["negative"], "points": dd_points(sc20["equity_curve"])},
        {"name": "Smallcap Momentum-10", "color": COL["assumption"], "points": dd_points(sc10["equity_curve"]), "dash": True},
        {"name": "Midcap Momentum-10", "color": COL["positive"], "points": dd_points(mc10["equity_curve"])},
        {"name": "NIFTY Smallcap 250 (real)", "color": COL["muted"], "points": dd_points(scidx["equity_curve"]), "dash": True},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=280, chart_id="dd_3way")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the more concentrated Smallcap Momentum-10 (10 stocks) fell hardest of the three reconstructions ({pct(sc10['max_drawdown_pct'],1,signed=False)}) — fewer holdings means more idiosyncratic risk in both directions, and it shows up here as a deeper worst-case loss, not just a better best-case gain.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def sel_rows(sample):
        return "".join(f"""<tr><td>{esc(s['date'])}</td><td class="text-left" style="text-align:left">{esc(', '.join(t.replace('.NS','') for t in s['tickers']))}</td></tr>""" for s in sample)

    sel_tables = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Sample rebalances — first 2 and last 2, each strategy</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — which stocks got selected, at the start and end of each reconstruction's history.</p>
      <div class="grid grid-cols-1 gap-4">
        <div>
          <div class="text-[12px] font-semibold text-[#9FB4BB] mb-1">Smallcap Momentum-20</div>
          <div class="scrollbox"><table class="data-table"><tbody>{sel_rows(sc20['selections_sample'])}</tbody></table></div>
        </div>
        <div>
          <div class="text-[12px] font-semibold text-[#9FB4BB] mb-1">Smallcap Momentum-10</div>
          <div class="scrollbox"><table class="data-table"><tbody>{sel_rows(sc10['selections_sample'])}</tbody></table></div>
        </div>
        <div>
          <div class="text-[12px] font-semibold text-[#9FB4BB] mb-1">Midcap Momentum-10</div>
          <div class="scrollbox"><table class="data-table"><tbody>{sel_rows(mc10['selections_sample'])}</tbody></table></div>
        </div>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">The one pattern worth taking seriously here</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — what's structural (likely to hold in general) vs. what's specific to this one historical path.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Going from 20 holdings to 10 within the same smallcap universe increased BOTH the CAGR ({pct(sc20['cagr_pct'])} → {pct(sc10['cagr_pct'])}) AND the
        max drawdown ({pct(sc20['max_drawdown_pct'],1,signed=False)} → {pct(sc10['max_drawdown_pct'],1,signed=False)}) — fewer, higher-conviction picks
        cut both ways, which is a structural property of concentration, not a coincidence of this particular data. That pattern is worth trusting more than
        the absolute numbers.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        What's much less trustworthy: comparing smallcap to midcap here. Midcap Momentum-10 shows the best CAGR AND a shallower drawdown than either
        smallcap version — but midcap's survivorship bias, while still real, is one notch weaker than smallcap's (per the lead disclosure), so part of
        that apparent "midcap is just better" result may be an artifact of which universe suffers more from using today's roster retroactively, not a
        real, tradeable advantage of midcap momentum over smallcap momentum.
      </p>
    </div>
    """

    limitations = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every simplification behind these three reconstructions.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Not real products, and not even matched to the real hybrid smallcap formula</span> — see the lead disclosure.</li>
        <li class="mb-1.5"><span class="font-semibold text-[#E6EDF0]">Survivorship bias, strongest for smallcap</span> — see the lead disclosure. Comparing the three reconstructions' absolute returns to each other is comparing three different amounts of hindsight bias, not three equally-fair tests.</li>
        <li class="mb-1.5">2 of 250 smallcap tickers had no price data available at all and were dropped entirely — a small, disclosed data gap.</li>
        <li class="mb-1.5">Equal-weighted, not free-float-market-cap × score; no F&O-eligibility screen; June/December rebalance dates are borrowed from the NIFTY200 Momentum 30 convention, not derived from any smallcap-specific published rule.</li>
        <li class="mb-1.5">The Midcap 150 ETF benchmark's real trading history only starts {esc(R['midcap_etf_start'])} — shown in the comparison table for context, but it doesn't cover the full {esc(R['common_start'])}–{esc(R['common_end'])} window the other five series do.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modelled for any series shown.</li>
        <li class="mb-1.5">This is three single, fixed reconstructions computed once — there is no sensitivity sweep beyond the 20-vs-10 and smallcap-vs-midcap comparisons already shown, and no out-of-sample check.</li>
      </ul>
    </div>
    """

    body = f"""
    {header}
    {lead_disclosure}
    {definitions_strip}
    <div class="px-10 py-6">
      {kpi_grid}
      {full_table}
      {eq_panel}
      {dd_panel}
      {sel_tables}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Smallcap &amp; Midcap Momentum Comparison</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("16_smallcap_midcap_momentum_compare.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 16_smallcap_midcap_momentum_compare.html")
