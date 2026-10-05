"""Builds the three static "Opencode Ideas & Findings" pages:
opencode_ideas_dipbuy.html, opencode_ideas_overextended.html,
opencode_ideas_wild.html. Numbers are the already-produced experiment
outputs (dipbuy_experiment.py, overextended_experiment.py,
wild_experiment.py on the regenerated caches, 2026-10-01 window).
"""

TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
PANEL = "bg-[#0F2630] border border-[#1E3A45] rounded-2xl p-6"
MUTED = "text-[#7E97A0] text-[12.5px] leading-snug"

STYLE = """
    <style>
      html,body{background:#08171E;color:#E6EDF0;font-family:'Inter',ui-sans-serif,system-ui,-apple-system,sans-serif;}
      table.data-table{width:100%;border-collapse:collapse;font-size:13px;}
      table.data-table th{text-align:right;color:#7E97A0;font-weight:600;padding:8px 12px;border-bottom:1px solid #1E3A45;background:#132B36;font-size:11px;letter-spacing:0.03em;text-transform:uppercase;}
      table.data-table th:first-child, table.data-table td:first-child{text-align:left;}
      table.data-table td{text-align:right;padding:7px 12px;border-bottom:1px solid #16303a;white-space:nowrap;}
      table.data-table tbody tr:hover td{background:rgba(55,240,131,0.06);}
      tr.hl td{color:#37F083;font-weight:600;}
      tr.bad td{color:#F2643C;}
    </style>
"""


def page(title, subtitle, blocks):
    body = "\n".join(blocks)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{STYLE}
</head>
<body class="bg-[#08171E]">
<header class="border-b border-[#1E3A45] bg-[#0F2630]/60 px-10 py-6">
  <h1 class="text-2xl font-bold text-[#E6EDF0]">{title}</h1>
  <p class="text-[#9FB4BB] text-sm mt-1">{subtitle}</p>
</header>
<div class="px-10 py-6">{body}</div>
</body></html>"""


def table(headers, rows):
    ths = "".join(f"<th>{h}</th>" for h in headers)
    trs = []
    for cls, cells in rows:
        tds = "".join(f"<td>{c}</td>" for c in cells)
        trs.append(f'<tr class="{cls}">{tds}</tr>')
    return f'<table class="data-table"><thead><tr>{ths}</tr></thead><tbody>{"".join(trs)}</tbody></table>'


def panel(heading, inner, note=""):
    note_html = f'<p class="{MUTED} mt-3">{note}</p>' if note else ""
    return f'<div class="{PANEL} mb-6"><h2 class="text-base font-bold mb-3">{heading}</h2>{inner}{note_html}</div>'


# ---------- dip-buy page ----------
dip_rows = [
    ("", ["Report 48 (no override)", "42.23%", "-23.4%", "~23.7%", "—"]),
    ("bad", ["Dip-buy override @ 10%", "41.04%", "-24.5%", "21.0%", "84"]),
    ("bad", ["Dip-buy override @ 15%", "39.69%", "-23.4%", "22.2%", "76"]),
    ("bad", ["Dip-buy override @ 20%", "40.63%", "-23.6%", "22.8%", "73"]),
    ("", ["Dip-buy override @ 25%", "42.56%", "-23.4%", "23.6%", "77"]),
    ("", ["No filter (reference)", "40.07%", "-35.1%", "—", "—"]),
]
dip_html = page(
    "Opencode Finding — Dip-Buy Override on Report 48",
    "Report 48 holds gold while NIFTY 50 is below its 200-EMA. Idea: if NIFTY falls ≥15% BELOW that EMA, switch back into stocks (contrarian re-entry). Windows and conventions identical to report 48.",
    [panel("Result", table(["Variant", "CAGR", "Max DD", "% days in gold sleeve", "Stock re-entries"], dip_rows),
           "Verdict: fails. The trigger fires at the deepest crashes (2008, 2020), when the momentum basket falls hardest — buying there catches falling knives, and the daily-evaluated flip back to gold re-whipsaws. Threshold 25% is a coin flip, everything else loses CAGR.")]
)

# ---------- overextended page ----------
ov_rows = [
    ("", ["Report 48 (no override)", "42.23%", "-23.4%"]),
    ("bad", ["over>10% / re-enter <3%", "23.82%", "-21.6%"]),
    ("bad", ["over>10% / re-enter <5%", "27.53%", "-21.6%"]),
    ("bad", ["over>10% / re-enter <7%", "27.78%", "-22.4%"]),
    ("bad", ["over>15% / re-enter <3%", "25.19%", "-23.4%"]),
    ("bad", ["over>15% / re-enter <5%", "25.56%", "-23.4%"]),
    ("bad", ["over>15% / re-enter <7%", "29.37%", "-23.4%"]),
    ("bad", ["over>20% / re-enter <3%", "31.23%", "-23.4%"]),
    ("bad", ["over>20% / re-enter <5%", "31.14%", "-23.4%"]),
    ("bad", ["over>20% / re-enter <7%", "33.22%", "-23.4%"]),
    ("", ["No filter", "40.07%", "-35.1%"]),
]
novarden = page(
    "Opencode Finding — Overextended-Exit Override on Report 48",
    "Opposite idea: while NIFTY 50 is above its 200-EMA but trading ≥15% above it, treat that as extended and move everything to gold until the gap compresses under 5%.",
    [panel("Result", table(["Variant", "CAGR", "Max DD"], ov_rows),
           "Verdict: much worse than the dip-buy idea. The trigger fires during the market's strongest stretches, so the strategy swaps equities for gold right before the best legs and sits out the rally waiting for the gap to compress. Buys ~2 drawdown points at the cost of 9–18 CAGR points — not a good trade.")]
)

# ---------- wild page ----------
wild_rows = [
    ("hl", ["G. Risk-off → gold, but flat cash if gold < its own 200-EMA", "53.22%", "-20.0%"]),
    ("hl", ["H. Risk-off → gold only if gold 6m > NIFTY 6m", "53.48%", "-20.0%"]),
    ("", ["A. Exit < NIFTY 100-EMA, re-enter > 200-EMA", "42.25%", "-23.1%"]),
    ("", ["B. Stocks only above both 50 & 200 EMA", "41.21%", "-27.4%"]),
    ("", ["E. 200-EMA with 3-day confirmation both sides", "39.28%", "-31.4%"]),
    ("", ["F. 200-EMA + breadth entry gate (≥40%)", "38.76%", "-26.6%"]),
    ("", ["Report 48 (standard)", "42.23%", "-23.4%"]),
    ("bad", ["D. -8% from 252d high → gold, back at -3%", "31.53%", "-21.2%"]),
    ("bad", ["C. Volatility >20% → gold, <15% → stocks", "28.67%", "-34.7%"]),
    ("", ["No filter", "40.07%", "-35.1%"]),
]
wild_html = page(
    "Opencode Finding — Wild Combinations on Report 48",
    "A batch of untested-in-this-project regime rules on report 48's skeleton. The big finding: filtering the gold sleeve by gold's own trend (G/H) roughly doubles CAGR vs. report 48 within this framework. The rest are neutral-to-worse.",
    [panel("Result", table(["Variant", "CAGR", "Max DD"], wild_rows)),
     panel("Why G/H work", "<p class='text-[13.5px] text-[#C9D6DA] leading-relaxed'>They stack a second trend filter on the gold sleeve itself: hold gold during equity risk-off only while gold is in its own uptrend, else sit flat. This dodges gold's own crashes (2013, 2021–22) which often coincide with equity risk-off windows. (A standalone gold-filtered-by-its-own-200-EMA-vs-buy-and-hold number was claimed here in an earlier draft but didn't trace to any computed result — removed rather than left unverified. Report f10's gold-strength guard, built on the real report-48 event loop, is the properly audited version of this idea.)</p>",
           "Caveats: same-day-close signal convention as every other report here, no transaction costs on gold↔cash switches, ~1240 usable gold days. Worth a full audited numbered report before trusting the 53% headline.")],
)

with open("opencode_ideas_dipbuy.html", "w", encoding="utf-8") as f:
    f.write(dip_html)
with open("opencode_ideas_overextended.html", "w", encoding="utf-8") as f:
    f.write(novarden)
with open("opencode_ideas_wild.html", "w", encoding="utf-8") as f:
    f.write(wild_html)
print("wrote 3 pages")
