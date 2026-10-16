"""Builds the Builder Lab HTML reports (94-98) from the results93-97.json
lab files written by backtest94-98.py. One generic renderer: header, hero
strip, the full variant table (Δ vs hero), the rebased overlay chart, the
fine print, and a reproduction card per variant with its exact config.

Run:  py -3 build_html_lab.py            (builds every lab file that exists)
"""
import html
import json

from svg_charts import line_chart, COL

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

PALETTE = ["#6AE4FF", "#C77DFF", "#F2B03C", "#37F083", "#F2643C", "#9FB4BB",
           "#5EC8F2", "#F2E86A", "#FF8A5C", "#B39DFF", "#7EE0C0", "#E38FB0"]

LABS = [
    (94, "results93.json", "94_protect_lab.html", "Protect Lab"),
    (95, "results94.json", "95_conditions_lab.html", "Conditions Lab"),
    (96, "results95.json", "96_money_lab.html", "Money Lab"),
    (97, "results96.json", "97_pick_rebalance_lab.html", "Pick & Rebalance Lab"),
    (98, "results97.json", "98_max_strategy.html", "Max Strategy — everything stacked"),
]

# hand-written lead findings per report — the actual conclusion, up front
FINDINGS = {
    94: [
        "The protect layer survives every challenge. Checking the NIFTY 50 200-EMA only at the Jun/Dec "
        "reviews instead of daily costs 2.8pp of CAGR (36.7% vs 39.5%) — the daily check is what catches "
        "the cracks between reviews. Replacing the gold park with plain cash costs 3.2pp (36.3%): gold's "
        "hedge earns its keep beyond safety.",
        "Alternatives to the signal itself are all worse. NIFTY 500 as the trend index buys a shallower "
        "drawdown (-22.9% vs -25.4%) at the price of 2.4pp of CAGR and the health score. Supertrend (10, 3) "
        "on either index costs 9–10pp. The 2-of-3 EMA/Supertrend/VIX ensemble costs 5.8pp. Any VIX-based "
        "regime — as an OR-filter or alone — is destructive (23.7–24.3% CAGR; VIX-only draws down -46.1%). "
        "One mild alternative: a 50% gold + 25% silver + 25% cash park lands within 1.4pp of the hero with "
        "a slightly shallower drawdown (silver's share sits in cash before Feb 2022).",
    ],
    95: [
        "The Conditions tab is mostly a trap on this strategy — and two of its most popular gates are exact "
        "no-ops. 'Above the 200-day EMA' and 'golden cross' produce curves identical to the hero to the last "
        "paisa: across 17 years and 686 trades, the top-10 momentum names were never bought below their "
        "200-EMA or outside a golden cross. Not a rounding coincidence — a property of what the ranking "
        "already selects.",
        "The only keepers are the gentle half of the momentum-discipline pair: 'buy only what is rising' "
        "(+0.16pp) and 'keep-if 6m return > 0' (+0.08pp, drawdown improving to -24.0%). Everything heavier "
        "subtracts: swings cap 13.5pp, turnover floor 9pp, near-ATH 8.6pp, VIX-calm 12.2pp, the "
        "five-condition quality gate 20.1pp. The daily 'sell when 6m turns negative' rule collapses the "
        "strategy to 4.6% CAGR — it sells every dip and re-enters late, the whipsaw in its purest form.",
    ],
    96: [
        "Compounding is the engine, not a preference: fixed ₹10,000 per position — profits accumulating as "
        "cash instead of sizing up new positions — drops CAGR from 39.5% to 15.6%.",
        "The SIP and dip rows must not be compared by CAGR (the contribution base grows, so CAGR flatters "
        "them by construction). On the honest measure — multiple on money contributed — the dip top-ups win: "
        "₹9L contributed at NIFTY RSI(14) < 30 closes (once a month) turned into ₹5.94 Cr, 66×. SIP ₹25k/month "
        "contributed ₹50L and closed at ₹24.1 Cr (48×); with the 10%/yr step-up, ₹1.31 Cr contributed → "
        "₹35.6 Cr (27×); the full stack closes at ₹39.3 Cr on ₹1.39 Cr contributed (28×). Money deployed at "
        "panic prices is the best deployment method tested anywhere in these labs.",
        "The Money tab's momentum-discipline pair fails here too: 'only buy rising + sell when negative' ends "
        "at 4.5% CAGR — same whipsaw, same verdict as the Conditions lab.",
    ],
    97: [
        "Exit rank 30 — a tighter leash than the hero's 52 — is the only winner: +0.4pp of CAGR (39.9%) with "
        "a marginally shallower drawdown and the same health score. The leash has an optimum: rank 20 gives "
        "the gain back (39.3%), rank 10 loses 1.1pp, rank 100 loses 3.4pp, and checking the rank daily instead "
        "of at reviews loses 1.1pp for a slightly shallower drawdown.",
        "The destructive knobs are the restricting ones: buy only from the top 5 drops to 25.7% (slots sit in "
        "cash waiting for a top-5 name), 3-per-sector caps collapse to 16.7%, 5-per-sector to 22.0% — this "
        "strategy's returns need the full breadth of its top 10. Whole units cost 0.3pp (39.2%) — the honest "
        "real-broker version of the same strategy. Friction stress: 0.3%/side → 35.0%, 0.5%/side → 30.7%.",
    ],
    98: [
        "The winners stack into a modest, honest improvement. keep-if 6m > 0 + exit rank 30 — 'max stack A' — "
        "gives 40.0% CAGR at -24.0% max drawdown and health 70/100, against the hero's 39.5% / -25.4% / 60. "
        "Adding the buy-only-if gate (stack B) nudges CAGR to 40.1% but gives back some of the drawdown gain.",
        "The honesty battery: whole units 39.8% / -23.9%; 0.5%/side friction still 31.1%; both-halves "
        "robustness passes on every row; and all six rebalance calendars — the same six report 92 tested — "
        "land between 38.2% and 40.1% for both stacks, so the result is not a June/December artifact (though "
        "Jun/Dec does happen to be the best of the six — a 1.8pp date-luck spread worth knowing about).",
        "The money plan on top — SIP ₹25k/month with a 10%/yr step-up plus ₹25k dip top-ups — turns ₹1.39 Cr "
        "of contributions into ₹41.4 Cr at the window's end (30×), the fullest version of this strategy these "
        "labs produced.",
    ],
}


def esc(s):
    return html.escape(str(s))


def pct(v, decimals=1, signed=True):
    if v is None:
        return "—"
    s = "+" if (signed and v > 0) else ""
    return f"{s}{v:,.{decimals}f}%"


def money(v, decimals=0):
    if v is None:
        return "—"
    sign = "-" if v < 0 else ""
    return f"{sign}₹{abs(v):,.{decimals}f}"


def pill(text, kind="neutral"):
    cls = {"positive": PILL_POS, "negative": PILL_NEG, "assumption": PILL_ASSUM, "neutral": PILL_NEUTRAL}[kind]
    dot = {"positive": "●", "negative": "●", "assumption": "▲", "neutral": "●"}[kind]
    return f'<span class="{cls}">{dot} {esc(text)}</span>'


def base_style():
    return """
    <style>
      html,body{background:#08171E;color:#E6EDF0;font-family:'Inter',ui-sans-serif,system-ui,-apple-system,sans-serif;}
      .mono{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace;}
      table.data-table{width:100%;border-collapse:collapse;font-size:13px;}
      table.data-table th{text-align:right;color:#7E97A0;font-weight:600;padding:8px 12px;border-bottom:1px solid #1E3A45;background:#132B36;font-size:11px;letter-spacing:0.03em;text-transform:uppercase;}
      table.data-table th:first-child, table.data-table td:first-child{text-align:left;}
      table.data-table td{text-align:right;padding:7px 12px;border-bottom:1px solid #16303a;white-space:nowrap;}
      table.data-table tbody tr:nth-child(even) td{background:rgba(255,255,255,0.015);}
      table.data-table tbody tr:hover td{background:rgba(55,240,131,0.06);}
      tr.hero-row td{background:rgba(106,228,255,0.07) !important;}
      .kpi-val{font-size:22px;font-weight:700;letter-spacing:-0.01em;}
      .pos{color:#37F083;} .neg{color:#F2643C;} .amb{color:#F2B03C;} .mut{color:#7E97A0;} .cy{color:#6AE4FF;}
      details.config-card summary{cursor:pointer;color:#9FB4BB;font-size:12.5px;font-weight:600;}
      details.config-card pre{background:#0B1D26;border:1px solid #1E3A45;border-radius:10px;padding:12px;margin-top:8px;font-size:11.5px;color:#B8CBD2;overflow-x:auto;}
    </style>
    """


def halves_cell(halves):
    if not halves or not isinstance(halves.get("halves"), list):
        return '<span class="mut mono">—</span>'
    total = len(halves["halves"])
    passed = sum(1 for h in halves["halves"] if h.get("passed") is True)
    cls = "pos" if passed == total else ("neg" if passed == 0 else "amb")
    return f'<span class="mono {cls}" style="font-weight:700">{passed}/{total}</span>'


def build_lab(report_no, lab, title):
    variants = lab["variants"]
    hero_label = lab.get("hero_label")
    hero = variants.get(hero_label, {})
    hero_cagr = hero.get("cagr_pct")

    rows = []
    for label, v in variants.items():
        delta = None
        if hero_cagr is not None and v.get("cagr_pct") is not None:
            delta = v["cagr_pct"] - hero_cagr
        rows.append((label, v, delta))
    rows.sort(key=lambda r: r[1].get("cagr_pct") or float("-inf"), reverse=True)

    challengers = [r for r in rows if r[0] != hero_label]
    best = challengers[0] if challengers else None

    header = f"""
    <header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
      <div class="flex items-start justify-between gap-6">
        <div>
          <div class="text-[11px] font-bold tracking-widest text-[#6AE4FF] mb-1">REPORT {report_no} · BUILDER LABS</div>
          <h1 class="text-2xl font-bold text-[#E6EDF0]">{esc(title)}</h1>
          <p class="text-[#9FB4BB] text-sm mt-1 max-w-[900px]">{esc(lab.get('lab_title', ''))}</p>
        </div>
        <div class="text-right {MUTED} mono shrink-0">
          {esc(lab['start_date'])}–{esc(lab['end_date'])}<br/>Report generated {esc(lab['generated'])}
        </div>
      </div>
    </header>
    """

    paras = FINDINGS.get(report_no) or [
        "The hero row of this lab is report 93's exact configuration — every other row is that engine with one "
        "knob changed, so each gap is the isolated cost or benefit of that single builder feature."
    ]
    paras_html = "".join(
        f'<p class="text-[14px] text-[#E6EDF0] leading-relaxed mb-2">{esc(p)}</p>' for p in paras
    )

    hero_strip = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL} border-2 border-[#6AE4FF]">
        <div class="flex items-center gap-2 mb-3 flex-wrap">
          {pill(f'Hero: {hero_label}', 'assumption')}
          {pill(f'Hero CAGR {pct(hero.get("cagr_pct"))} at {pct(hero.get("max_drawdown_pct"), 1, False)} max drawdown', 'positive')}
          {pill(f'{len(variants)} variants, every one the same engine with one knob changed', 'neutral')}
        </div>
        {paras_html}
      </div>
    </div>
    """

    trs = []
    for label, v, delta in rows:
        is_hero = label == hero_label
        dcls = "mut" if delta is None else ("pos" if delta > 0.05 else ("neg" if delta < -0.05 else "mut"))
        health = (v.get("health") or {}).get("score")
        hcls = "pos" if (health or 0) >= 60 else ("amb" if (health or 0) >= 40 else "neg")
        final = v.get("final_value")
        contrib = v.get("contributed_total")
        contrib_html = (f'<span class="block mut" style="font-size:10.5px">contributed {money(contrib)}</span>'
                        if contrib and contrib > 100000 else "")
        trs.append(f"""
        <tr class="{'hero-row' if is_hero else ''}">
          <td>{esc(label)}{' <span class="cy" style="font-size:10.5px;font-weight:700">· HERO · REPORT 93</span>' if is_hero else ''}
              <span class="block mut" style="font-size:11px">{(v.get('stats') or {}).get('total_trades', '—')} trades</span></td>
          <td class="mono" style="font-weight:700;font-size:14px">{pct(v.get('cagr_pct'))}</td>
          <td class="mono {dcls}">{'—' if delta is None else f'{delta:+.1f}pp'}</td>
          <td class="mono">{pct(v.get('max_drawdown_pct'), 1, False)}</td>
          <td class="mono mut">{pct(v.get('net_return_pct'))}</td>
          <td class="mono {hcls}">{'—' if health is None else f'{health}/100'}</td>
          <td>{halves_cell(v.get('halves'))}</td>
          <td class="mono mut" style="font-size:12.5px">{money((v.get('tax') or {}).get('total_tax'))}</td>
          <td class="mono mut" style="font-size:12.5px">{money(final)}{contrib_html}</td>
        </tr>""")

    table = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Every variant, one table</h3>
        <div class="{WHAT_THIS_SHOWS}">Sorted by CAGR. Δ vs hero is the CAGR difference against this lab's hero row
        (report 93's exact configuration). Halves = how many half-periods the variant beat NIFTY 50 in. Tax is the
        capital-gains estimate on the realised trades; final value is the closing portfolio at the window's end.</div>
        <div style="overflow-x:auto">
        <table class="data-table">
          <thead><tr>
            <th>Variant</th><th>CAGR</th><th>Δ vs hero</th><th>Max DD</th><th>Net return</th>
            <th>Health</th><th>Halves</th><th>Tax paid</th><th>Final value</th>
          </tr></thead>
          <tbody>{''.join(trs)}</tbody>
        </table>
        </div>
      </div>
    </div>
    """

    # rebased overlay: every variant + NIFTY 50 dashed
    series = []
    for idx, (label, v, _d) in enumerate(rows):
        pts = v.get("equity_curve") or []
        series.append({"name": label, "color": PALETTE[idx % len(PALETTE)],
                       "points": [[p[0], p[1]] for p in pts], "dash": False})
    nif = lab.get("nifty") or {}
    if nif.get("equity_curve"):
        series.append({"name": "NIFTY 50", "color": "#9FB4BB",
                       "points": [[p[0], p[1]] for p in nif["equity_curve"]], "dash": True})
    chart_svg, chart_legend = line_chart(series, height=460,
                                         value_fmt=lambda v: f"{v:,.0f}", chart_id=f"lab{report_no}")

    chart = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL}">
        <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Growth of 100 — every variant of this lab</h3>
        <div class="{WHAT_THIS_SHOWS}">Each variant rebased to 100 at the window's start, after 0.1%/side costs
        (except friction variants). The hero's curve is the same one report 93 ships.</div>
        {chart_svg}
        <div class="mt-3 flex flex-wrap gap-x-4 gap-y-1">{chart_legend}</div>
      </div>
    </div>
    """

    notes = lab.get("notes") or []
    notes_html = "".join(f'<li class="flex gap-2 text-[13px] text-[#9FB4BB] leading-relaxed"><span class="cy">•</span><span>{esc(n)}</span></li>'
                         for n in notes)
    notes_block = f"""
    <div class="px-10 pt-6">
      <div class="{PANEL_TIGHT}">
        <h3 class="text-base font-bold text-[#E6EDF0] mb-2">How to read this lab — the fine print</h3>
        <ul class="space-y-2">{notes_html}</ul>
      </div>
    </div>
    """ if notes else ""

    cfg_cards = []
    for label, v, _d in rows:
        cfg_json = json.dumps(v.get("config") or {}, indent=1, ensure_ascii=False)
        cfg_cards.append(f"""
        <details class="config-card {PANEL_TIGHT}" style="margin-bottom:10px">
          <summary>{esc(label)}</summary>
          <pre>{esc(cfg_json)}</pre>
        </details>""")
    configs_block = f"""
    <div class="px-10 pt-6 pb-12">
      <div class="{PANEL_TIGHT}">
        <h3 class="text-base font-bold text-[#E6EDF0] mb-1">Exact configurations — reproduction cards</h3>
        <div class="{WHAT_THIS_SHOWS}">Every knob of every variant as the engine saw it. The hero's card is report
        93's configuration; run it through check_builder_regression.py to reproduce report 93 exactly.</div>
        {''.join(cfg_cards)}
      </div>
    </div>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Report {report_no} — {esc(title)}</title>
{TAILWIND_CDN}
{base_style()}
</head>
<body>
{header}
{hero_strip}
{table}
{chart}
{notes_block}
{configs_block}
</body>
</html>
"""


def main():
    for report_no, lab_file, out_file, title in LABS:
        try:
            with open(lab_file, encoding="utf-8") as f:
                lab = json.load(f)
        except FileNotFoundError:
            print(f"skip {lab_file} (not run yet)")
            continue
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(build_lab(report_no, lab, title))
        print(f"{out_file} written ({len(lab['variants'])} variants)")


if __name__ == "__main__":
    main()
