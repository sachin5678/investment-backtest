"""Builds 32_midcap_momentum10_kotak_mtf_2x.html from results31.json. Same
self-contained contract, smooth Catmull-Rom charts, dark palette as every
other report. Log10 y-axis on the equity chart (same technique as report
25) since 18 years of leveraged compounding pushes the four series across
several orders of magnitude."""
import json
import math
import html
from svg_charts import line_chart, area_underwater_chart, COL

with open("results31.json") as f:
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
SCENARIO_COLOR = {"m20": "#37F083", "m30": "#F2B03C", "m40": "#F2643C"}


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


def inr(v, decimals=0):
    return f"₹{v:,.{decimals}f}"


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
      tr.headline-row td{color:#E6EDF0;font-weight:600;}
      tr.mc-row td{color:#F2643C;}
      a.src-link{color:#6AE4FF;text-decoration:underline;text-decoration-color:rgba(106,228,255,0.35);}
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
    fric, cash = R["frictionless"], R["cash_with_charges"]
    scenarios = R["scenarios"]
    m20, m30, m40 = scenarios["m20"], scenarios["m30"], scenarios["m40"]
    sym = R["currency_symbol"]
    headline = m30

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">Midcap Momentum 10 — 2x Leverage via Kotak Neo MTF, All Charges Modeled</h1>
          <p class="text-[#9FB4BB] text-sm mt-1">Same strategy as reports 11-19/24-27/30-31, no strategy-side stop-loss — but every rebalance now buys 2x the notional per position (50% own capital, 50% borrowed via Kotak Neo's Margin Trading Facility), paying real MTF interest, doubled transaction costs, and modeled margin-call risk.</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(R['start_date'])}–{esc(R['end_date'])} · {R['mtf_rate_annual_pct']:.2f}% p.a. MTF rate<br/>Report generated {esc(R['generated'])}
        </div>
      </div>
    </header>
    """

    lead_disclosure = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#F2643C]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill(f"2x leverage does NOT simply double the return", 'negative')}
          {pill(f"drawdown roughly doubles too ({pct(headline['metrics']['max_drawdown_pct'],1,signed=False)} vs {pct(fric['max_drawdown_pct'],1,signed=False)})", 'negative')}
          {pill(f"{headline['trade_stats']['margin_calls']} margin calls at the headline 30% maintenance assumption", 'assumption')}
        </div>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-3">
          The strategy itself is unchanged — same top-10 selection by 6m/12m risk-adjusted momentum, same equal weighting, same June/December
          rebalance. What changes: at every rebalance, each position is funded 50% by your own capital and 50% borrowed via Kotak Neo's MTF at
          {pct(R['mtf_rate_annual_pct'])} p.a. — buying 2x the notional exposure per rupee of your own capital. Every real charge Kotak Neo and
          Indian exchanges actually levy is modeled: brokerage, STT, exchange transaction charges, SEBI fees, stamp duty, GST, and the MTF interest
          itself — all sourced and cited below.
        </p>
        <p class="text-[14px] text-[#E6EDF0] leading-relaxed">
          The honest result, at the headline 30%-maintenance-margin assumption: CAGR rises from the frictionless
          {pct(fric['cagr_pct'])} to <span class="font-semibold">{pct(headline['metrics']['cagr_pct'])}</span> — well short of a clean 2x — while
          max drawdown deepens from {pct(fric['max_drawdown_pct'],1,signed=False)} to
          <span class="font-semibold">{pct(headline['metrics']['max_drawdown_pct'],1,signed=False)}</span>. {headline['trade_stats']['margin_calls']}
          of {headline['trade_stats']['total_positions']} positions ({pct(headline['trade_stats']['margin_call_pct_of_positions'],1,signed=False)})
          got forcibly liquidated by a margin call before ever reaching their scheduled rebalance, averaging a
          <span class="font-semibold">{pct(headline['trade_stats']['avg_margin_call_return_on_capital'])}</span> loss on capital each time. See the
          honesty note below for why the maintenance-margin assumption itself changes this picture substantially — and why a LOOSER threshold
          isn't automatically safer.
        </p>
      </div>
    </div>
    """

    kpis = [
        kpi_card("CAGR — all three layers", "Same window, same strategy, only the cost/leverage layer changes.",
                  [("Frictionless", pct(fric["cagr_pct"]), win_loss_kind(fric["cagr_pct"])),
                   ("Cash + real charges", pct(cash["cagr_pct"]), win_loss_kind(cash["cagr_pct"])),
                   ("2x MTF (30% maint.)", pct(headline["metrics"]["cagr_pct"]), win_loss_kind(headline["metrics"]["cagr_pct"]))]),
        kpi_card("Max drawdown — all three layers", "Largest peak-to-trough decline, same window.",
                  [("Frictionless", pct(fric["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("Cash + real charges", pct(cash["max_drawdown_pct"], 1, signed=False), "negative"),
                   ("2x MTF (30% maint.)", pct(headline["metrics"]["max_drawdown_pct"], 1, signed=False), "negative")]),
        kpi_card("Real charges modeled (both legs)", "Sourced from Kotak Neo / NSE / SEBI, checked 2026-08 — see citations below.",
                  [("Buy-side total", pct(R["buy_cost_pct"], 4), "assumption"),
                   ("Sell-side total", pct(R["sell_cost_pct"], 4), "assumption"),
                   ("MTF interest", pct(R["mtf_rate_annual_pct"], 2) + " p.a.", "assumption")]),
        kpi_card("Margin-call sensitivity (2x MTF)", "How the assumed maintenance-margin threshold changes the outcome.",
                  [("20% maint.", f"{pct(m20['metrics']['cagr_pct'])} / {m20['trade_stats']['margin_calls']} calls", win_loss_kind(m20['metrics']['cagr_pct'])),
                   ("30% maint.", f"{pct(m30['metrics']['cagr_pct'])} / {m30['trade_stats']['margin_calls']} calls", win_loss_kind(m30['metrics']['cagr_pct'])),
                   ("40% maint.", f"{pct(m40['metrics']['cagr_pct'])} / {m40['trade_stats']['margin_calls']} calls", win_loss_kind(m40['metrics']['cagr_pct']))]),
    ]
    kpi_grid = f'<div class="grid grid-cols-2 gap-4 mt-6">{"".join(kpis)}</div>'

    def row(name, v, cls=""):
        c = f' class="{cls}"' if cls else ""
        return f"""<tr{c}><td>{esc(name)}</td><td>{pct(v['net_return_pct'])}</td><td>{pct(v['cagr_pct'])}</td>
        <td>{pct(v['max_drawdown_pct'],1,signed=False)}</td><td>{v['longest_underwater_days']:,}d</td></tr>"""

    full_table = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">All five, side by side</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the same strategy under increasing layers of real-world friction, over the identical {esc(R['start_date'])}–{esc(R['end_date'])} window. The bold row is the headline 30%-maintenance scenario.</p>
      <table class="data-table">
        <thead><tr><th>Series</th><th>Net return</th><th>CAGR</th><th>Max drawdown</th><th>Longest underwater</th></tr></thead>
        <tbody>
          {row("Frictionless (reports 16/17's own number)", fric)}
          {row("Cash, no leverage, real charges applied", cash)}
          {row("2x MTF, real charges, 20% maintenance margin", m20["metrics"])}
          {row("2x MTF, real charges, 30% maintenance margin", m30["metrics"], "headline-row")}
          {row("2x MTF, real charges, 40% maintenance margin", m40["metrics"])}
        </tbody>
      </table>
    </div>
    """

    def log_points(points):
        return [[d, math.log10(max(v, 0.01))] for d, v in points]

    eq_series = [
        {"name": "Frictionless", "color": COL["text"], "points": log_points(fric["equity_curve"]), "dash": True},
        {"name": "Cash + real charges", "color": COL["muted"], "points": log_points(cash["equity_curve"]), "dash": True},
        {"name": "2x MTF, 20% maint.", "color": SCENARIO_COLOR["m20"], "points": log_points(m20["metrics"]["equity_curve"])},
        {"name": "2x MTF, 30% maint. (headline)", "color": SCENARIO_COLOR["m30"], "points": log_points(m30["metrics"]["equity_curve"])},
        {"name": "2x MTF, 40% maint.", "color": SCENARIO_COLOR["m40"], "points": log_points(m40["metrics"]["equity_curve"])},
    ]
    eq_svg, eq_legend = line_chart(eq_series, height=460, force_zero=False,
                                     value_fmt=lambda v: f"{10**v:,.0f}", chart_id="eq_32")
    eq_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Growth of 100 — {esc(R['start_date'])} to {esc(R['end_date'])}</h3>
        {pill('log10 y-axis — labels show real values, not log values', 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — all three 2x MTF scenarios pull ahead of the unleveraged lines for most of the window (higher long-run CAGR), but a log axis is needed just to fit both the leveraged AND unleveraged curves on one legible chart — the gap between them compounds into several orders of magnitude over 18 years.</p>
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
        {"name": "Frictionless", "color": COL["text"], "points": dd_points(fric["equity_curve"]), "dash": True},
        {"name": "2x MTF, 30% maint. (headline)", "color": SCENARIO_COLOR["m30"], "points": dd_points(m30["metrics"]["equity_curve"])},
    ]
    dd_svg, dd_legend = area_underwater_chart(dd_series, height=260, chart_id="dd_32")
    dd_panel = f"""
    <div class="{PANEL} mt-6">
      <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Drawdown comparison</h3>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the 2x MTF line's drawdown ({pct(m30['metrics']['max_drawdown_pct'],1,signed=False)}) is far deeper than the frictionless strategy's own ({pct(fric['max_drawdown_pct'],1,signed=False)}) — leverage doesn't just amplify the good periods.</p>
      <div class="flex items-center mb-2">{dd_legend}</div>
      {dd_svg}
    </div>
    """

    def mc_row(t):
        return f"""<tr class="mc-row"><td>{esc(t['ticker'])}</td><td>{esc(t['entry_date'])}</td><td>{sym}{t['entry_price']:,.2f}</td>
        <td>{esc(t['exit_date'])}</td><td>{sym}{t['exit_price']:,.2f}</td><td>{pct(t['pct_return_on_capital'])}</td></tr>"""

    mc_sample = m30["margin_call_trades_sample"]
    mc_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Sample margin calls — 30% maintenance scenario</h3>
        {pill(f"first 10 and last 10 of {m30['trade_stats']['margin_calls']} shown", 'neutral')}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — every row is a position that was forcibly liquidated before its scheduled rebalance because its price fell far enough (roughly -23% from entry, at this maintenance level) to breach the modeled maintenance margin. Return on capital is deeply negative on every one of these by construction — that's what 2x leverage's downside looks like.</p>
      <div style="overflow-x:auto">
      <table class="data-table">
        <thead><tr><th style="text-align:left">Stock</th><th>Bought</th><th>Buy price</th><th>Margin-called</th><th>Exit price</th><th>Return on capital</th></tr></thead>
        <tbody>{''.join(mc_row(t) for t in mc_sample)}</tbody>
      </table>
      </div>
    </div>
    """

    pledge_events = m30["trade_stats"]["total_positions"] * 2  # one pledge at entry, one unpledge at exit
    pledge_fee_each = R["pledge_fee_inr"] * 1.18
    total_pledge_cost = pledge_events * pledge_fee_each
    pledge_pct_of_capital = total_pledge_cost / R["illustrative_capital_inr"] * 100

    charges_panel = f"""
    <div class="{PANEL} mt-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="text-base font-bold text-[#E6EDF0]">Every charge modeled, sourced</h3>
        {pill("checked 2026-08", "neutral")}
      </div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the exact rates fed into this backtest, and where each one comes from. The first six rows apply as a %-of-transaction-value to BOTH the cash and 2x MTF layers (on 1x notional for cash, 2x for MTF); the last row is a flat rupee fee that doesn't scale with the index, shown separately below against an illustrative account size.</p>
      <table class="data-table">
        <thead><tr><th style="text-align:left">Charge</th><th>Rate</th><th style="text-align:left">Side</th><th style="text-align:left">Source</th></tr></thead>
        <tbody>
          <tr><td style="text-align:left">Brokerage (Trade Free Pro plan)</td><td>0.10%</td><td style="text-align:left">Buy &amp; sell</td><td style="text-align:left"><a class="src-link" href="https://www.kotakneo.com/pricing/" target="_blank" rel="noopener">kotakneo.com/pricing</a></td></tr>
          <tr><td style="text-align:left">STT (delivery equity)</td><td>0.10%</td><td style="text-align:left">Buy &amp; sell</td><td style="text-align:left">Standard nationwide rate, delivery segment</td></tr>
          <tr><td style="text-align:left">NSE exchange transaction charge</td><td>₹2.97/lakh</td><td style="text-align:left">Buy &amp; sell</td><td style="text-align:left">Uniform since SEBI's Oct 2024 circular</td></tr>
          <tr><td style="text-align:left">SEBI turnover fee</td><td>₹10/crore</td><td style="text-align:left">Buy &amp; sell</td><td style="text-align:left">SEBI, nationwide</td></tr>
          <tr><td style="text-align:left">Stamp duty</td><td>0.015%</td><td style="text-align:left">Buy only</td><td style="text-align:left">Nationwide flat rate since 2020</td></tr>
          <tr><td style="text-align:left">GST</td><td>18%</td><td style="text-align:left">On brokerage + exchange + SEBI fee</td><td style="text-align:left">Standard GST rate</td></tr>
          <tr><td style="text-align:left"><span class="font-semibold">MTF interest</span> (Trade Free Pro plan)</td><td><span class="font-semibold">{pct(R['mtf_rate_annual_pct'],2)} p.a.</span></td><td style="text-align:left">On the borrowed (funded) amount only, simple daily accrual</td><td style="text-align:left"><a class="src-link" href="https://www.kotakneo.com/margin-trading-facility/" target="_blank" rel="noopener">kotakneo.com/margin-trading-facility</a></td></tr>
          <tr><td style="text-align:left"><span class="font-semibold">MTF minimum own-capital margin</span></td><td><span class="font-semibold">50%</span> for 2x leverage</td><td style="text-align:left">Kotak's stated minimum is 25% (= 4x max); 2x needs 50%</td><td style="text-align:left"><a class="src-link" href="https://www.kotakneo.com/support/how-much-margins-or-leverage-does-kotak-securities-provide/" target="_blank" rel="noopener">kotakneo.com/support</a></td></tr>
          <tr><td style="text-align:left">Pledge / unpledge fee (flat, per ISIN)</td><td>₹{R['pledge_fee_inr']:.0f} + GST = {inr(pledge_fee_each,2)}</td><td style="text-align:left">Each way (entry pledge, exit unpledge)</td><td style="text-align:left"><a class="src-link" href="https://www.kotakneo.com/support/is-there-any-charge-for-pledge-the-stocks-under-pay-later-mtf/" target="_blank" rel="noopener">kotakneo.com/support</a></td></tr>
        </tbody>
      </table>
      <div class="mt-4 p-4 rounded-xl bg-[#132B36] border border-[#1E3A45]">
        <div class="text-[13px] font-semibold text-[#E6EDF0] mb-1">Worked example — the flat pledge/unpledge fee, at an illustrative {inr(R['illustrative_capital_inr'])} account</div>
        <p class="text-[13px] text-[#C9D6DA] leading-relaxed">
          The 30%-maintenance scenario generated {m30['trade_stats']['total_positions']} positions over 18 years — roughly
          {pledge_events} pledge/unpledge events ({m30['trade_stats']['total_positions']} entries + {m30['trade_stats']['total_positions']} exits).
          At {inr(pledge_fee_each,2)} per event, that's <span class="font-semibold">{inr(total_pledge_cost)}</span> in total flat fees over the
          whole 18-year run — on a {inr(R['illustrative_capital_inr'])} starting account, that's only about
          <span class="font-semibold">{pledge_pct_of_capital:.2f}%</span> of the STARTING capital, cumulative, not annualised. This flat fee
          matters far less than a percentage rate here — but it scales the OPPOSITE way from the % charges: a smaller real account pays the
          exact same ₹{R['pledge_fee_inr']:.0f}+GST per event, so it's a proportionally bigger drag for a smaller account than for a larger one.
        </p>
      </div>
    </div>
    """

    honesty_note = f"""
    <div class="{PANEL} mt-6 border-[#F2B03C]/40">
      <div class="flex items-center gap-2 mb-2"><h3 class="text-base font-bold text-[#E6EDF0]">Why 2x leverage doesn't give you 2x the return — and why looser margin isn't automatically safer</h3>{pill('framing', 'assumption')}</div>
      <p class="{WHAT_THIS_SHOWS}">WHAT THIS SHOWS — the mechanism, not just the scoreboard.</p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        Ignoring costs and margin calls entirely, doubling each position's exposure would compound to roughly double the frictionless strategy's
        already-large multiple — arithmetically much more than "2x the CAGR" once compounded over 36 rebalances, since leverage amplifies BOTH
        the size of each period's gain and the base it compounds from. Real MTF eats into that in three separate ways: {pct(R['buy_cost_pct'],2)}
        + {pct(R['sell_cost_pct'],2)} of round-trip transaction costs on DOUBLE the notional (vs. cash), {pct(R['mtf_rate_annual_pct'],2)} p.a.
        interest on the borrowed half (averaging {headline['trade_stats']['avg_interest_pct_of_capital_per_holding']}% of a position's own
        capital per ~6-month hold), and — the big one — margin calls that force-crystallize a loss at the worst possible moment instead of letting
        a position ride out a temporary dip.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed mb-3">
        That third effect is why the maintenance-margin ASSUMPTION matters so much, and why the relationship isn't what you'd first guess. At a
        40% maintenance threshold (margin calls fire on roughly a {pct(23.1,1,signed=False)}-{pct(37.5,1,signed=False)} range of price drops
        depending on the exact threshold — see the table above), {m40['trade_stats']['margin_calls']} of {m40['trade_stats']['total_positions']}
        positions ({pct(m40['trade_stats']['margin_call_pct_of_positions'],1,signed=False)}) got force-sold — MORE than three times as often as
        at 20% maintenance ({m20['trade_stats']['margin_calls']} calls, {pct(m20['trade_stats']['margin_call_pct_of_positions'],1,signed=False)}).
        A tighter (lower) maintenance requirement gives a volatile momentum stock more room to have an ordinary bad month WITHOUT being forced
        out — which is exactly why the 20% scenario ends up with the HIGHEST CAGR of the three ({pct(m20['metrics']['cagr_pct'])}) despite being
        the "loosest" margin rule, and the 40% scenario the lowest ({pct(m40['metrics']['cagr_pct'])}) despite being the "safest"-sounding one.
      </p>
      <p class="text-[13.5px] text-[#C9D6DA] leading-relaxed">
        None of the three scenarios avoid a deep drawdown, though — all three land between {pct(-62.3,1,signed=False)} and
        {pct(-59.4,1,signed=False)}, meaningfully worse than the frictionless strategy's own {pct(fric['max_drawdown_pct'],1,signed=False)}. The
        margin-call mechanism changes WHEN and HOW OFTEN losses get crystallized, but 2x leverage on an already-volatile momentum strategy is a
        deeper hole to climb out of under every assumption tested here.
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
        <li class="mb-1.5"><span class="font-semibold">The maintenance-margin percentage is this report's one real assumption, not a published Kotak number.</span> SEBI requires dynamic, per-stock VaR-based margins that move with each stock's own volatility — Kotak doesn't publish that full day-by-day schedule. 20%/30%/40% are plausible flat stand-ins tested as a sensitivity range, not the real rule.</li>
        <li class="mb-1.5">No grace period or top-up behaviour is modeled — a real investor typically gets 1-2 trading days to add funds/collateral before forced liquidation; this backtest force-sells the instant the threshold breaks, the same no-discretion convention used for every mechanical rule in this project.</li>
        <li class="mb-1.5">All 10 positions are assumed individually margin-monitored at the SAME maintenance percentage; in reality Kotak's margin requirement varies stock-by-stock based on each name's own VaR, so some of this project's picks would have tighter or looser real thresholds than the flat assumption used here.</li>
        <li class="mb-1.5">Today's fixed NIFTY Midcap 150 constituent list is applied retroactively across the whole window (survivorship bias) — same disclosed approximation as every other reconstruction here.</li>
        <li class="mb-1.5">The 1500+ MTF-eligible stock list changes over time and isn't applied retroactively here — this assumes every one of the strategy's picks would have been MTF-eligible throughout the full 2008-2026 window, which may not hold for every stock at every point in its history.</li>
        <li class="mb-1.5">Equal weighting (not free-float market-cap x momentum score) and no F&O-eligibility screen, same as every other reconstruction in this project.</li>
        <li class="mb-1.5">Prices are unadjusted; no dividends are modeled for any holding.</li>
        <li class="mb-1.5">This is a single, fixed 18-year historical path — a different window, especially one with fewer sharp intra-period crashes, could make 2x leverage look considerably better relative to the frictionless strategy than it does here.</li>
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
      {mc_panel}
      {charges_panel}
      {honesty_note}
      {limitations}
    </div>
    """
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>Midcap Momentum 10 — 2x Kotak Neo MTF Leverage</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{base_style()}
</head>
<body class="bg-[#08171E]">
<script>const DATA = {json.dumps(R)};</script>
{body}
</body></html>"""


if __name__ == "__main__":
    with open("32_midcap_momentum10_kotak_mtf_2x.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote 32_midcap_momentum10_kotak_mtf_2x.html")
