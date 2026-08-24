"""Builds 01_backtest.html and 02_benchmark.html from results.json.
Self-contained: Tailwind via Play CDN, all data inlined as a JS object, charts are
hand-written inline SVG (svg_charts.py). No backtesting/chart libraries used anywhere.
"""
import json
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results.json") as f:
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


def pill(text, kind="assumption"):
    cls = {"positive": PILL_POS, "negative": PILL_NEG, "assumption": PILL_ASSUM, "neutral": PILL_NEUTRAL}[kind]
    dot = {"positive": "●", "negative": "●", "assumption": "▲", "neutral": "●"}[kind]
    return f'<span class="{cls}">{dot} {text}</span>'


def money(v, symbol, decimals=0):
    sign = "-" if v < 0 else ""
    return f"{sign}{symbol}{abs(v):,.{decimals}f}"


def pct(v, decimals=1, signed=True):
    if v is None:
        return "—"
    s = "+" if (signed and v > 0) else ""
    return f"{s}{v:,.{decimals}f}%"


def esc(s):
    return html.escape(str(s))


# ----------------------------------------------------------------------------
# shared page chrome
# ----------------------------------------------------------------------------

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
      .scrollbox{max-height:340px;overflow:auto;}
      .scrollbox::-webkit-scrollbar{width:8px;}
      .scrollbox::-webkit-scrollbar-thumb{background:#1E3A45;border-radius:4px;}
      .tab-btn.active{background:#16303a;color:#E6EDF0;border-color:#37F083;}
      .tab-btn{transition:all .12s ease;}
      .kpi-val{font-size:28px;font-weight:700;letter-spacing:-0.01em;}
    </style>
    """


def header(title, subtitle, source_line):
    return f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">{title}</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">{subtitle}</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {source_line}<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """


def instrument_toggle(active_key):
    btns = []
    for key in R["instruments"]:
        inst = R["instruments"][key]
        active = " active" if key == active_key else ""
        btns.append(
            f'<button class="tab-btn{active} px-4 py-2 rounded-lg border border-[#1E3A45] text-sm font-semibold '
            f'text-[#9FB4BB] hover:text-[#E6EDF0]" data-inst-btn="{key}" onclick="showInstrument(\'{key}\')">'
            f'{esc(inst["label"])}</button>'
        )
    return f'<div class="flex gap-3 px-10 pt-6" id="instrumentTabs">{"".join(btns)}</div>'


def toggle_script():
    return """
    <script>
      function showInstrument(key){
        document.querySelectorAll('[data-inst-section]').forEach(el=>{
          el.classList.toggle('hidden', el.getAttribute('data-inst-section')!==key);
        });
        document.querySelectorAll('[data-inst-btn]').forEach(el=>{
          el.classList.toggle('active', el.getAttribute('data-inst-btn')===key);
        });
      }
    </script>
    """


DEFINITIONS_STRIP = f"""
  <div class="px-10 pt-6">
    <div class="{PANEL_TIGHT}">
      <p class="{WHAT_THIS_SHOWS} mb-2">WHAT THIS SHOWS — plain-English recap of the rule being tested, so every number below can be read without the spec doc.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        <span class="font-semibold text-[#E6EDF0]">Entry:</span> go long when today's close finishes above the highest daily high of the prior 20 trading days.
        <span class="font-semibold text-[#E6EDF0]">Exit:</span> close the position when today's close finishes below the lowest daily low of the prior 10 trading days.
        Long-or-flat only — the strategy never shorts. Each new position uses
        {pill("10% of equity", "assumption")} at the time of entry, compounding as equity changes; the other 90% sits in cash earning nothing.
        Orders are assumed to fill at the <span class="font-semibold text-[#E6EDF0]">next bar's open</span> after a signal, never at the signal's own close.
      </p>
    </div>
  </div>
"""


def limitations_panel(extra_points=None):
    points = [
        "This is a single, fixed rule set tested once over history — there is no out-of-sample test, no walk-forward validation, and no check for whether 20/10-day lookbacks were curve-fit to this data.",
        "Prices are the raw (unadjusted) Close/High/Low from our data source — QQQ dividends are not modelled or reinvested anywhere in this report, including the buy-and-hold comparison.",
        "Execution is assumed to always fill at the next bar's open, in full, regardless of gap size, liquidity, or halt — real fills could be materially worse on large gaps.",
        "NIFTY 50 is backtested on the raw index level (^NSEI), which is not directly tradable. A real implementation would need futures, options, or an ETF — each with its own costs, tick size, and tracking error not modelled here.",
        "The cost-loaded variant models only a flat 0.05% commission and a fixed one-tick slippage per fill. It does not model bid-ask spread widening, market impact from larger orders, financing/borrow cost, or India-specific transaction taxes (STT, stamp duty, GST on brokerage).",
        "A trade still open on the last available bar is marked-to-market into the equity curve but excluded from the trade-level statistics (win rate, average win/loss, top-5 contribution) — it isn't a closed, realized outcome yet.",
        "Only 10% of equity is ever deployed at a time, so this report's net return and CAGR are not comparable to a fully-invested return without adjusting for that — see 02_benchmark.html.",
    ]
    if extra_points:
        points += extra_points
    lis = "".join(f'<li class="mb-1.5">{p}</li>' for p in points)
    return f"""
    <div class="{PANEL} border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2">
        <h3 class="text-base font-bold text-[#E6EDF0]">Limitations</h3>
        {pill("read before trusting any number above", "assumption")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the concrete ways this backtest can mislead you if taken at face value.</p>
      <ul class="text-[13px] text-[#C9D6DA] list-disc pl-5 leading-relaxed">{lis}</ul>
    </div>
    """


def kpi_card(label, definition, cols):
    """cols: list of (col_label, value_str, kind) tuples rendered side by side."""
    col_html = []
    for col_label, value_str, kind in cols:
        color = {"positive": "#37F083", "negative": "#F2643C", "neutral": "#E6EDF0", "assumption": "#F2B03C"}[kind]
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


def win_loss_kind(v):
    if v is None:
        return "neutral"
    return "positive" if v > 0 else ("negative" if v < 0 else "neutral")


# ----------------------------------------------------------------------------
# PAGE 1 — 01_backtest.html
# ----------------------------------------------------------------------------

def build_page1():
    sections = []
    for key, inst in R["instruments"].items():
        sym = inst["currency_symbol"]
        fr = inst["variants"]["frictionless"]
        cl = inst["variants"]["cost_loaded"]
        sf, sc = fr["stats"], cl["stats"]

        kpis = []
        kpis.append(kpi_card(
            "Number of trades",
            'A "trade" is one full round trip: an entry fill followed by its exit fill. Signal timing is identical in both variants — commission/slippage only change the fill price, not when trades happen.',
            [("Both variants", str(sf["num_trades"]), "neutral")],
        ))
        kpis.append(kpi_card(
            "Win rate",
            "Share of closed trades whose net profit (after any costs) was positive.",
            [("Frictionless", pct(sf["win_rate"], 1, signed=False), win_loss_kind(1)),
             ("Cost-loaded", pct(sc["win_rate"], 1, signed=False), win_loss_kind(1))],
        ))
        kpis.append(kpi_card(
            "Average win",
            f"Mean profit across winning trades only, as % return on the {sym} committed to that trade.",
            [("Frictionless", pct(sf["avg_win_pct"]), "positive"),
             ("Cost-loaded", pct(sc["avg_win_pct"]), "positive")],
        ))
        kpis.append(kpi_card(
            "Average loss",
            f"Mean loss across losing trades only, as % return on the {sym} committed to that trade.",
            [("Frictionless", pct(sf["avg_loss_pct"]), "negative"),
             ("Cost-loaded", pct(sc["avg_loss_pct"]), "negative")],
        ))
        kpis.append(kpi_card(
            "Net return",
            "Total % change in account equity from the first to the last bar, including the ~90% that sits in idle cash the whole time.",
            [("Frictionless", pct(fr["net_return_pct"]), win_loss_kind(fr["net_return_pct"])),
             ("Cost-loaded", pct(cl["net_return_pct"]), win_loss_kind(cl["net_return_pct"]))],
        ))
        kpis.append(kpi_card(
            "CAGR",
            "Compound Annual Growth Rate — the constant yearly % rate that would turn the starting equity into the ending equity over the actual number of years tested.",
            [("Frictionless", pct(fr["cagr_pct"]), win_loss_kind(fr["cagr_pct"])),
             ("Cost-loaded", pct(cl["cagr_pct"]), win_loss_kind(cl["cagr_pct"]))],
        ))
        kpis.append(kpi_card(
            "Max drawdown",
            "The largest peak-to-trough decline the equity curve ever experienced, in %.",
            [("Frictionless", pct(fr["max_drawdown_pct"], 1, signed=False), "negative"),
             ("Cost-loaded", pct(cl["max_drawdown_pct"], 1, signed=False), "negative")],
        ))
        kpis.append(kpi_card(
            "Longest time underwater",
            "The longest stretch, in calendar days, equity spent below a previous peak before finally setting a new all-time high.",
            [("Frictionless", f'{fr["longest_underwater_days"]:,} days', "neutral"),
             ("Cost-loaded", f'{cl["longest_underwater_days"]:,} days', "neutral")],
        ))
        top5_note = "Sum of the 5 single most profitable trades, divided by total net profit (all trades combined). Above 100% means the other trades were a net loss overall — common in trend-following systems that rely on a few large winners."
        kpis.append(kpi_card(
            "Top-5 trade profit contribution",
            top5_note,
            [("Frictionless", pct(sf["top5_pct_of_profit"], 0, signed=False) if sf["top5_pct_of_profit"] is not None else "—", "assumption"),
             ("Cost-loaded", pct(sc["top5_pct_of_profit"], 0, signed=False) if sc["top5_pct_of_profit"] is not None else "—", "assumption")],
        ))

        kpi_grid = f'<div class="grid grid-cols-3 gap-4 mt-6">{"".join(kpis)}</div>'

        # equity chart
        eq_series = [
            {"name": "Frictionless", "color": COL["positive"], "points": fr["equity_curve"]},
            {"name": "Cost-loaded (0.05% + 1 tick per side)", "color": COL["assumption"], "points": cl["equity_curve"], "dash": True},
        ]
        eq_svg, eq_legend = line_chart(eq_series, y_prefix=sym, value_fmt=lambda v: f"{v:,.0f}", chart_id=f"eq_{key}")

        eq_panel = f"""
        <div class="{PANEL} mt-6">
          <div class="flex items-center justify-between mb-1">
            <h3 class="text-base font-bold text-[#E6EDF0]">Equity curve — {sym}{inst['initial_capital']:,.0f} start</h3>
            {pill('axis starts at zero — no truncation', 'neutral')}
          </div>
          <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — account equity day by day, only 10% of which is ever actually at risk in the market at once; the rest is idle cash, which is why the line is relatively flat.</p>
          <div class="flex items-center mb-2">{eq_legend}</div>
          {eq_svg}
          <div class="{MUTED} mt-2">Source: computed from daily OHLC price data for {esc(inst['ticker'])}, {esc(inst['data_start'])} to {esc(inst['data_end'])} ({inst['num_bars']:,} bars). Chart is downsampled to ≤1,500 points for file size; KPI cards above use the full daily series.</div>
        </div>
        """

        # drawdown chart — recompute running max from the (downsampled) equity points
        def dd_points(points):
            out, peak = [], None
            for d, v in points:
                peak = v if peak is None else max(peak, v)
                out.append([d, (v / peak - 1.0) * 100.0])
            return out

        dd_series = [
            {"name": "Frictionless", "color": COL["positive"], "points": dd_points(fr["equity_curve"])},
            {"name": "Cost-loaded", "color": COL["negative"], "points": dd_points(cl["equity_curve"]), "dash": True},
        ]
        dd_svg, dd_legend = area_underwater_chart(dd_series, chart_id=f"dd_{key}")
        dd_panel = f"""
        <div class="{PANEL} mt-6">
          <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown (% below prior peak) — {esc(inst['label'])}</h3>
          <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — how far equity ever fell below its own running high-water mark; the exact max-drawdown % is the KPI card above (computed on the full daily series, not this downsampled chart).</p>
          <div class="flex items-center mb-2">{dd_legend}</div>
          {dd_svg}
        </div>
        """

        # trades table — merged, both variants side by side
        rows = []
        n = len(fr["trades"])
        for i in range(n):
            tf, tc = fr["trades"][i], cl["trades"][i]
            win_f = tf["pnl"] > 0
            rows.append(f"""
            <tr>
              <td>{esc(tf['entry_date'])}</td><td>{esc(tf['exit_date'])}</td><td>{tf['holding_days']}</td>
              <td>{money(tf['entry_price'], sym, 2)}</td><td>{money(tf['exit_price'], sym, 2)}</td>
              <td style="color:{'#37F083' if win_f else '#F2643C'}">{money(tf['pnl'], sym, 0)}</td>
              <td style="color:{'#37F083' if win_f else '#F2643C'}">{pct(tf['return_pct'])}</td>
              <td style="color:{'#37F083' if tc['pnl']>0 else '#F2643C'}">{money(tc['pnl'], sym, 0)}</td>
              <td style="color:{'#37F083' if tc['pnl']>0 else '#F2643C'}">{pct(tc['return_pct'])}</td>
            </tr>""")
        open_trade_note = ""
        if fr.get("open_trade"):
            ot = fr["open_trade"]
            open_trade_note = (f'<div class="{MUTED} mt-2">Not counted above: a position opened {esc(ot["entry_date"])} at '
                                f'{money(ot["entry_price"], sym, 2)} is still open at the end of data ({esc(ot["still_open_at"])}), '
                                f'marked-to-market at {money(ot["mark_to_market_value"], sym, 0)}.</div>')

        top5_ids_fr = sorted(range(n), key=lambda i: fr["trades"][i]["pnl"], reverse=True)[:5]
        top5_rows = "".join(
            f"<tr><td>{esc(fr['trades'][i]['entry_date'])}</td><td>{esc(fr['trades'][i]['exit_date'])}</td>"
            f"<td style='color:#37F083'>{money(fr['trades'][i]['pnl'], sym, 0)}</td>"
            f"<td>{pct(fr['trades'][i]['pnl']/sf['net_profit']*100 if sf['net_profit'] else 0, 1, signed=False)}</td></tr>"
            for i in top5_ids_fr
        )

        trades_panel = f"""
        <div class="{PANEL} mt-6">
          <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Top 5 trades by profit (frictionless) {pill(pct(sf['top5_pct_of_profit'],0,signed=False) + ' of net profit', 'assumption')}</h3>
          <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the five single biggest winning trades and how much of total net profit each one alone represents.</p>
          <div class="scrollbox">
          <table class="data-table"><thead><tr><th>Entry</th><th>Exit</th><th>P&amp;L</th><th>% of net profit</th></tr></thead>
          <tbody>{top5_rows}</tbody></table>
          </div>
        </div>

        <div class="{PANEL} mt-6">
          <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Full trade log — {esc(inst['label'])} ({n} closed trades)</h3>
          <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every closed round trip, frictionless vs. cost-loaded outcome side by side, so you can see exactly what 0.05% commission + 1 tick of slippage per side costs on each individual trade.</p>
          <div class="scrollbox">
          <table class="data-table">
            <thead><tr><th>Entry</th><th>Exit</th><th>Days held</th><th>Entry px (frict.)</th><th>Exit px (frict.)</th>
            <th>P&amp;L (frict.)</th><th>Return % (frict.)</th><th>P&amp;L (cost-loaded)</th><th>Return % (cost-loaded)</th></tr></thead>
            <tbody>{''.join(rows)}</tbody>
          </table>
          </div>
          {open_trade_note}
        </div>
        """

        section = f"""
        <section data-inst-section="{key}" class="{'hidden' if key != list(R['instruments'].keys())[0] else ''} px-10 py-6">
          {kpi_grid}
          {eq_panel}
          {dd_panel}
          {trades_panel}
        </section>
        """
        sections.append(section)

    limitations = f'<div class="px-10 py-6">{limitations_panel()}</div>'

    first_key = list(R["instruments"].keys())[0]
    body = f"""
    {header(
        "Breakout Backtest — 20-day High Entry / 10-day Low Exit",
        "Long-or-flat, hand-written event-loop backtest on QQQ and NIFTY 50, run in two cost variants. No backtesting library was used.",
        f"Data: daily OHLC (unadjusted) price data"
    )}
    {instrument_toggle(first_key)}
    {DEFINITIONS_STRIP}
    {''.join(sections)}
    {limitations}
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Breakout Backtest — QQQ &amp; NIFTY 50</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
{toggle_script()}
</body></html>"""


# ----------------------------------------------------------------------------
# PAGE 2 — 02_benchmark.html
# ----------------------------------------------------------------------------

def build_page2():
    sections = []
    for key, inst in R["instruments"].items():
        sym = inst["currency_symbol"]
        fr = inst["variants"]["frictionless"]
        cl = inst["variants"]["cost_loaded"]
        bh = inst["benchmark"]

        kind_color = {"positive": "#37F083", "negative": "#F2643C", "neutral": "#E6EDF0", "assumption": "#F2B03C"}

        def cmp_card(label, definition, values):
            # values: list of (name, val_str, kind)
            cols = "".join(
                f'<div class="flex-1"><div class="text-[11px] text-[#7E97A0] mb-1 uppercase tracking-wide">{esc(n)}</div>'
                f'<div class="kpi-val mono" style="color:{kind_color[k]}">{v}</div></div>'
                for n, v, k in values
            )
            return f"""
            <div class="{PANEL_TIGHT}">
              <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">{esc(label)}</div>
              <div class="{MUTED} mb-3">{definition}</div>
              <div class="flex gap-4">{cols}</div>
            </div>
            """

        cards = []
        cards.append(cmp_card(
            "Net return",
            "Total % change in equity from first to last bar. Strategy figures include the ~90% that sits in idle cash; buy-and-hold has 100% deployed the entire time — this is not an apples-to-apples measure of signal quality, see Limitations.",
            [("Strategy — frictionless", pct(fr["net_return_pct"]), win_loss_kind(fr["net_return_pct"])),
             ("Strategy — cost-loaded", pct(cl["net_return_pct"]), win_loss_kind(cl["net_return_pct"])),
             ("Buy & hold", pct(bh["net_return_pct"]), win_loss_kind(bh["net_return_pct"]))],
        ))
        cards.append(cmp_card(
            "CAGR",
            "Compound annual growth rate over the identical date range and starting balance for all three.",
            [("Strategy — frictionless", pct(fr["cagr_pct"]), win_loss_kind(fr["cagr_pct"])),
             ("Strategy — cost-loaded", pct(cl["cagr_pct"]), win_loss_kind(cl["cagr_pct"])),
             ("Buy & hold", pct(bh["cagr_pct"]), win_loss_kind(bh["cagr_pct"]))],
        ))
        cards.append(cmp_card(
            "Max drawdown",
            "Largest peak-to-trough decline in equity. Smaller (closer to 0%) is a shallower worst-case loss.",
            [("Strategy — frictionless", pct(fr["max_drawdown_pct"], 1, signed=False), "negative"),
             ("Strategy — cost-loaded", pct(cl["max_drawdown_pct"], 1, signed=False), "negative"),
             ("Buy & hold", pct(bh["max_drawdown_pct"], 1, signed=False), "negative")],
        ))
        cards.append(cmp_card(
            "Longest time underwater",
            "Longest stretch, in calendar days, spent below a prior equity peak before a new all-time high.",
            [("Strategy — frictionless", f'{fr["longest_underwater_days"]:,} days', "neutral"),
             ("Strategy — cost-loaded", f'{cl["longest_underwater_days"]:,} days', "neutral"),
             ("Buy & hold", f'{bh["longest_underwater_days"]:,} days', "neutral")],
        ))
        # a fair risk-adjusted cut: return per unit of max drawdown (Calmar-style)
        def calmar(ret_cagr, mdd):
            return None if mdd == 0 else ret_cagr / abs(mdd)
        cal_fr, cal_cl, cal_bh = calmar(fr["cagr_pct"], fr["max_drawdown_pct"]), calmar(cl["cagr_pct"], cl["max_drawdown_pct"]), calmar(bh["cagr_pct"], bh["max_drawdown_pct"])
        cards.append(cmp_card(
            "CAGR ÷ Max drawdown (risk-adjusted)",
            "Not one of the requested metrics — added as an ASSUMPTION-tagged extra: annual growth rate per 1% of worst-case drawdown suffered. Higher means more return for each unit of pain endured; it does not make a low absolute return \"good\" on its own.",
            [("Strategy — frictionless", f"{cal_fr:.2f}" if cal_fr is not None else "—", win_loss_kind(cal_fr)),
             ("Strategy — cost-loaded", f"{cal_cl:.2f}" if cal_cl is not None else "—", win_loss_kind(cal_cl)),
             ("Buy & hold", f"{cal_bh:.2f}" if cal_bh is not None else "—", win_loss_kind(cal_bh))],
        ))

        kpi_grid = f'<div class="grid grid-cols-3 gap-4 mt-6">{"".join(cards)}</div>' + f'<div class="mt-2">{pill("CAGR/MDD ratio is an added, non-requested metric", "assumption")}</div>'

        eq_series = [
            {"name": "Strategy — frictionless", "color": COL["positive"], "points": fr["equity_curve"]},
            {"name": "Strategy — cost-loaded", "color": COL["assumption"], "points": cl["equity_curve"], "dash": True},
            {"name": "Buy & hold", "color": COL["text"], "points": bh["equity_curve"]},
        ]
        eq_svg, eq_legend = line_chart(eq_series, y_prefix=sym, value_fmt=lambda v: f"{v:,.0f}", height=420, chart_id=f"eqcmp_{key}")
        eq_panel = f"""
        <div class="{PANEL} mt-6">
          <div class="flex items-center justify-between mb-1">
            <h3 class="text-base font-bold text-[#E6EDF0]">Equity curve — strategy vs. buy &amp; hold, {sym}{inst['initial_capital']:,.0f} start</h3>
            {pill('linear axis, starts at zero — not log-scaled', 'neutral')}
          </div>
          <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the true scale of the gap: buy-and-hold keeps 100% invested the whole time, the strategy only ever risks 10% of equity, so the strategy line looking flat by comparison is real, not a rendering artifact.</p>
          <div class="flex items-center mb-2">{eq_legend}</div>
          {eq_svg}
          <div class="{MUTED} mt-2">Buy &amp; hold: {sym}{inst['initial_capital']:,.0f} invested at the open of the first available bar ({esc(bh['start_date'])}, price {money(bh['entry_price'], sym, 2)}), held with no rebalancing to the last close. No dividends reinvested (same convention as the strategy).</div>
        </div>
        """

        def dd_points(points):
            out, peak = [], None
            for d, v in points:
                peak = v if peak is None else max(peak, v)
                out.append([d, (v / peak - 1.0) * 100.0])
            return out
        dd_series = [
            {"name": "Strategy — frictionless", "color": COL["positive"], "points": dd_points(fr["equity_curve"])},
            {"name": "Buy & hold", "color": COL["negative"], "points": dd_points(bh["equity_curve"]), "dash": True},
        ]
        dd_svg, dd_legend = area_underwater_chart(dd_series, chart_id=f"ddcmp_{key}")
        dd_panel = f"""
        <div class="{PANEL} mt-6">
          <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison — {esc(inst['label'])}</h3>
          <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — buy-and-hold's much deeper drawdowns are the direct cost of being 100% invested at all times; the strategy trades that pain away by only being 10% invested, at the cost of much lower return shown above.</p>
          <div class="flex items-center mb-2">{dd_legend}</div>
          {dd_svg}
        </div>
        """

        honesty_note = f"""
        <div class="{PANEL} mt-6 border-[#F2B03C]/40">
          <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Read this before concluding "the strategy beats/loses to buy-and-hold"</h3>{pill('framing', 'assumption')}</div>
          <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the single biggest driver of the return gap above, stated plainly.</p>
          <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
            The strategy's net return ({pct(fr['net_return_pct'])} frictionless) is dramatically lower than buy-and-hold's ({pct(bh['net_return_pct'])})
            for {esc(inst['label'])}. A large part of that gap is mechanical: this backtest only ever commits 10% of equity to a position, so 90% of the account
            earns nothing while buy-and-hold has 100% working the whole time. The strategy also suffered a far smaller max drawdown
            ({pct(fr['max_drawdown_pct'], 1, signed=False)} vs. {pct(bh['max_drawdown_pct'], 1, signed=False)}) — that risk reduction is real, but it does not
            offset the return gap on the numbers as sized here. Neither fact cancels the other out; both are true at once.
          </p>
        </div>
        """

        section = f"""
        <section data-inst-section="{key}" class="{'hidden' if key != list(R['instruments'].keys())[0] else ''} px-10 py-6">
          {kpi_grid}
          {eq_panel}
          {dd_panel}
          {honesty_note}
        </section>
        """
        sections.append(section)

    extra_lims = [
        "Buy-and-hold is sized at 100% of the same starting balance the strategy starts with — it is a benchmark for the instrument's raw price path, not a risk-matched comparison to a 10%-sized strategy.",
        "Buy-and-hold, like the strategy, uses unadjusted prices with no dividends reinvested — real total-return buy-and-hold (with dividends) would be higher than shown here for QQQ.",
        "The CAGR ÷ max-drawdown ratio shown is a simple, non-standard risk-adjusted cut added for this report; it is not the Calmar ratio's official definition (which typically uses trailing 36-month drawdown) and should not be quoted as such.",
    ]
    limitations = f'<div class="px-10 py-6">{limitations_panel(extra_lims)}</div>'

    first_key = list(R["instruments"].keys())[0]
    body = f"""
    {header(
        "Strategy vs. Buy-and-Hold Benchmark",
        "Same instrument, same start date, same starting balance — net return, CAGR, max drawdown and longest time underwater side by side.",
        "Data: daily OHLC (unadjusted) price data"
    )}
    {instrument_toggle(first_key)}
    {''.join(sections)}
    {limitations}
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Strategy vs. Buy-and-Hold — QQQ &amp; NIFTY 50</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
{toggle_script()}
</body></html>"""


if __name__ == "__main__":
    with open("01_backtest.html", "w", encoding="utf-8") as f:
        f.write(build_page1())
    with open("02_benchmark.html", "w", encoding="utf-8") as f:
        f.write(build_page2())
    print("Wrote 01_backtest.html and 02_benchmark.html")
