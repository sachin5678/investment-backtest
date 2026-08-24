"""Builds dashboard.html — the unified hub for all reports in this project.
Left sidebar groups every strategy by family; clicking one loads its
existing, already-verified standalone report into the main iframe. No
report content is duplicated or re-authored here — this is a navigation
shell only, per the design-system guidance from the ui-ux-pro-max skill
(dark/dense dashboard pattern, Fira Sans/Fira Code typography), kept on the
project's existing color palette for consistency across every report.
"""
import json

TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fira+Sans:wght@400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet">'

# --- simple, hand-verified geometric SVG icons (no icon-library paths, no emoji) ---
ICON_TRENDING = '<polyline points="3,17 9,11 13,15 21,7"/><polyline points="15,7 21,7 21,13"/>'
ICON_BARS = '<rect x="4" y="10" width="3.5" height="10" rx="0.5"/><rect x="10.25" y="6" width="3.5" height="14" rx="0.5"/><rect x="16.5" y="3" width="3.5" height="17" rx="0.5"/>'
ICON_WALLET = '<rect x="3" y="7" width="18" height="12" rx="2"/><line x1="3" y1="11" x2="21" y2="11"/><circle cx="17" cy="15" r="1.3" fill="currentColor" stroke="none"/>'
ICON_REFRESH = '<path d="M20 11a8 8 0 1 0-2.3 5.7" fill="none"/><polyline points="20,4 20,11 13,11"/>'
ICON_CALENDAR = '<rect x="3" y="5" width="18" height="16" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="3" x2="8" y2="7"/><line x1="16" y1="3" x2="16" y2="7"/>'
ICON_BOLT = '<polygon points="13,2 4,14 11,14 9,22 20,10 13,10"/>'
ICON_FLASK = '<path d="M9 2v6.5l-5.2 9A2 2 0 0 0 5.6 21h12.8a2 2 0 0 0 1.8-3.5L15 8.5V2" fill="none"/><line x1="7" y1="2" x2="17" y2="2"/><line x1="8" y1="15" x2="16" y2="15"/>'
ICON_GRID = '<rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/>'
ICON_SHIELD = '<path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z" fill="none"/><path d="M9 12l2.2 2.2L15.5 9.5" fill="none"/>'
ICON_GLOBE = '<circle cx="12" cy="12" r="9" fill="none"/><ellipse cx="12" cy="12" rx="4" ry="9" fill="none"/><line x1="3" y1="12" x2="21" y2="12"/>'
ICON_PULSE = '<polyline points="3,12 8,12 10,6 14,18 16,12 21,12" fill="none"/>'
ICON_COINS = '<ellipse cx="9" cy="9" rx="6" ry="6" fill="none"/><path d="M15 9a6 6 0 0 1 0 10.5A6 6 0 0 1 9 15" fill="none"/>'
ICON_LEDGER = '<rect x="4" y="3" width="16" height="18" rx="1.5" fill="none"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="13" y2="16"/>'
ICON_COMPASS = '<circle cx="12" cy="12" r="9" fill="none"/><polygon points="15,9 13,13 9,15 11,11"/>'

GROUPS = [
    {
        "label": "NIFTY 50 Breakout System",
        "items": [
            {"id": "01", "file": "01_backtest.html", "icon": ICON_TRENDING,
             "title": "Backtest: 20-day High / 10-day Low", "subtitle": "Frictionless vs. cost-loaded, QQQ & NIFTY 50"},
            {"id": "02", "file": "02_benchmark.html", "icon": ICON_BARS,
             "title": "vs. Buy-and-Hold Benchmark", "subtitle": "Same instrument, same start, side by side"},
        ],
    },
    {
        "label": "Cash Timing (NIFTY 50)",
        "items": [
            {"id": "03", "file": "03_dip_buying.html", "icon": ICON_WALLET,
             "title": "Wait for the Dip", "subtitle": "Annual cash/NIFTY switch on a -10% YTD dip"},
        ],
    },
    {
        "label": "Midcap Rotation",
        "items": [
            {"id": "04", "file": "04_midcap_rotation.html", "icon": ICON_REFRESH,
             "title": "Flight to Midcap", "subtitle": "NIFTY 50 → midcap on a -15% ATH drawdown"},
        ],
    },
    {
        "label": "SIP + Tactical Overlays (Midcap)",
        "items": [
            {"id": "05", "file": "05_sip_dip_overlay.html", "icon": ICON_CALENDAR,
             "title": "SIP + Dip Lump-Sums", "subtitle": "+₹5k / +₹10k at -10% / -20% from ATH"},
            {"id": "06", "file": "06_breakout_recovery.html", "icon": ICON_CALENDAR,
             "title": "SIP + Confirmed-Recovery Lump-Sum", "subtitle": "Buy strength after a full round-trip, not the dip"},
            {"id": "07", "file": "07_double_sip.html", "icon": ICON_CALENDAR,
             "title": "SIP Doubles on Drawdown (15%)", "subtitle": "Recurring SIP itself doubles through a decline"},
            {"id": "08", "file": "08_double_sip_10pct.html", "icon": ICON_CALENDAR,
             "title": "SIP Doubles on Drawdown (10%)", "subtitle": "Same rule, more sensitive 10% trigger"},
            {"id": "09", "file": "09_sip_day_of_month.html", "icon": ICON_CALENDAR,
             "title": "Does the SIP Date Matter?", "subtitle": "1st vs. 10th vs. 20th vs. last day of month"},
        ],
    },
    {
        "label": "Momentum Factor",
        "items": [
            {"id": "10", "file": "10_momentum_sip.html", "icon": ICON_BOLT,
             "title": "SIP in a Momentum ETF", "subtitle": "HDFCMOMENT.NS vs. midcap vs. NIFTY, ~2.8yr"},
            {"id": "11", "file": "11_momentum_reconstruction.html", "icon": ICON_FLASK,
             "title": "Momentum Formula, 18 Years", "subtitle": "NIFTY200/Top-30 reconstruction — survivorship-biased"},
            {"id": "12", "file": "12_momentum10_reconstruction.html", "icon": ICON_FLASK,
             "title": "“NIFTY100 Momentum 10”", "subtitle": "Custom variant — not a real NSE index"},
        ],
    },
    {
        "label": "Quality Factor",
        "items": [
            {"id": "13", "file": "13_quality50_basket.html", "icon": ICON_FLASK,
             "title": "Quality-50 Static Basket", "subtitle": "Today's fundamentals, bought once — not a rebalanced index"},
        ],
    },
    {
        "label": "Midcap Momentum + Gold",
        "items": [
            {"id": "14", "file": "14_midcap_momentum20_gold.html", "icon": ICON_BOLT,
             "title": "Midcap Momentum-20 + Gold Blend", "subtitle": "Custom top-20 variant, plus a 50/50 gold diversification test"},
            {"id": "15", "file": "15_midcap_momentum20_quarterly.html", "icon": ICON_BOLT,
             "title": "Momentum-20 — Quarterly Rebalance", "subtitle": "Same setup, rebalanced 4x/year instead of 2x"},
            {"id": "16", "file": "16_smallcap_midcap_momentum_compare.html", "icon": ICON_BOLT,
             "title": "Smallcap vs. Midcap Momentum", "subtitle": "Momentum-20 vs Momentum-10 vs Midcap Momentum-10, side by side"},
            {"id": "17", "file": "17_monthly_rebalance_compare.html", "icon": ICON_REFRESH,
             "title": "Monthly Rebalance — All 6 Compared", "subtitle": "Every momentum reconstruction, monthly vs its original cadence"},
            {"id": "18", "file": "18_midcap30_nifty500_10_15.html", "icon": ICON_BOLT,
             "title": "Midcap-30 & NIFTY500 Momentum 10/15", "subtitle": "Real rebalance months this time — May/Nov and June/Dec"},
        ],
    },
    {
        "label": "Sector Rotation",
        "items": [
            {"id": "19", "file": "19_sector_momentum_rotation.html", "icon": ICON_GRID,
             "title": "Sector-First Momentum Rotation", "subtitle": "Rank sectors by momentum first, then top 3 stocks within the leader"},
        ],
    },
    {
        "label": "Momentum + Gold, Drawdown-Triggered",
        "items": [
            {"id": "20", "file": "20_momentum_gold_catch_blend.html", "icon": ICON_SHIELD,
             "title": "Momentum + Gold, With a Drawdown Catch", "subtitle": "-20% drawdown sells all gold into momentum, until a full recovery"},
        ],
    },
    {
        "label": "Beyond India",
        "items": [
            {"id": "21", "file": "21_nasdaq100_momentum10.html", "icon": ICON_GLOBE,
             "title": "“NASDAQ100 Momentum 10”", "subtitle": "The same formula, applied to the Nasdaq-100 since 2000"},
        ],
    },
    {
        "label": "Technical Signals",
        "items": [
            {"id": "22", "file": "22_rsi70_monthly_rotation.html", "icon": ICON_PULSE,
             "title": "Monthly RSI-70 Crossover Rotation", "subtitle": "Any NSE stock above ₹2,000 Cr — up to 5 positions, 15% stop or month-end"},
        ],
    },
    {
        "label": "Commodities",
        "items": [
            {"id": "23", "file": "23_gold_silver_momentum_rotation.html", "icon": ICON_COINS,
             "title": "Gold/Silver Absolute Momentum Rotation", "subtitle": "Hold each metal only while its own momentum is positive, else cash"},
        ],
    },
    {
        "label": "Trade-Level Detail",
        "items": [
            {"id": "24", "file": "24_midcap_momentum10_last2yr_tradelog.html", "icon": ICON_LEDGER,
             "title": "Midcap Momentum 10 — Last 2 Years, Trade Log", "subtitle": "Every stock bought and sold, with entry/exit price and P&L, vs. the midcap ETF"},
            {"id": "25", "file": "25_midcap_momentum10_rebalance_offsets.html", "icon": ICON_COMPASS,
             "title": "Midcap Momentum 10 — Rebalance Offsets Compared", "subtitle": "Jan/Jul, Feb/Aug, Mar/Sep, Apr/Oct, May/Nov, Jun/Dec — all six, side by side"},
        ],
    },
]

ALL_ITEMS = [item for g in GROUPS for item in g["items"]]


def nav_group_html(group, active_id):
    rows = []
    for item in group["items"]:
        active = item["id"] == active_id
        cls = "nav-item active" if active else "nav-item"
        rows.append(f"""
        <button class="{cls}" data-file="{item['file']}" data-id="{item['id']}"
                data-title="{item['title']}" data-subtitle="{item['subtitle']}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="nav-icon">{item['icon']}</svg>
          <span class="nav-text">
            <span class="nav-title">{item['title']}</span>
            <span class="nav-subtitle">{item['subtitle']}</span>
          </span>
          <span class="nav-num mono">{item['id']}</span>
        </button>""")
    return f"""
    <div class="nav-group">
      <div class="nav-group-label">{group['label']}</div>
      {''.join(rows)}
    </div>
    """


def jump_select_html(default_id):
    groups_html = []
    for g in GROUPS:
        opts = "".join(
            f'<option value="{item["id"]}"{" selected" if item["id"] == default_id else ""}>'
            f'{item["id"]} — {item["title"]}</option>'
            for item in g["items"]
        )
        groups_html.append(f'<optgroup label="{g["label"]}">{opts}</optgroup>')
    return f"""
    <div id="jumpWrap">
      <label id="jumpLabel" for="jumpSelect">Jump to a report</label>
      <select id="jumpSelect" aria-label="Jump to a report">{''.join(groups_html)}</select>
    </div>
    """


def build():
    default_item = ALL_ITEMS[0]
    nav_html = "".join(nav_group_html(g, default_item["id"]) for g in GROUPS)
    jump_html = jump_select_html(default_item["id"])
    items_json = json.dumps({i["id"]: {"file": i["file"], "title": i["title"], "subtitle": i["subtitle"]} for i in ALL_ITEMS})

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>NIFTY &amp; Midcap Strategy Lab</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
{TAILWIND_CDN}
{FONTS}
<style>
  :root {{
    --ground:#08171E; --panel:#0F2630; --border:#1E3A45;
    --positive:#37F083; --assumption:#F2B03C; --negative:#F2643C; --text:#E6EDF0; --muted:#7E97A0;
  }}
  html,body{{height:100%;margin:0;background:var(--ground);color:var(--text);
    font-family:'Fira Sans',ui-sans-serif,system-ui,-apple-system,sans-serif;}}
  .mono{{font-family:'Fira Code',ui-monospace,SFMono-Regular,Menlo,monospace;}}
  #shell{{display:flex;height:100vh;overflow:hidden;}}
  #sidebar{{width:320px;flex:0 0 320px;background:var(--panel);border-right:1px solid var(--border);
    display:flex;flex-direction:column;overflow-y:auto;}}
  #sidebar::-webkit-scrollbar{{width:8px;}}
  #sidebar::-webkit-scrollbar-thumb{{background:var(--border);border-radius:4px;}}
  #brand{{padding:22px 20px 16px;border-bottom:1px solid var(--border);}}
  #brand h1{{font-size:16px;font-weight:700;margin:0;color:var(--text);letter-spacing:-0.01em;}}
  #brand p{{font-size:12px;color:var(--muted);margin:4px 0 0;line-height:1.4;}}
  #jumpWrap{{padding:14px 20px 12px;border-bottom:1px solid var(--border);}}
  #jumpLabel{{font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;
    color:var(--muted);display:block;margin-bottom:6px;}}
  #jumpSelect{{width:100%;background:var(--ground);color:var(--text);border:1px solid var(--border);
    border-radius:10px;padding:9px 34px 9px 12px;font-size:13px;font-family:inherit;cursor:pointer;
    appearance:none;-webkit-appearance:none;-moz-appearance:none;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237E97A0' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6,9 12,15 18,9'/%3E%3C/svg%3E");
    background-repeat:no-repeat;background-position:right 10px center;background-size:16px;
    transition:border-color 150ms ease;}}
  #jumpSelect:hover{{border-color:var(--muted);}}
  #jumpSelect:focus-visible{{outline:2px solid var(--positive);outline-offset:1px;border-color:var(--positive);}}
  #jumpSelect option{{background:var(--panel);color:var(--text);}}
  #jumpSelect optgroup{{background:var(--panel);color:var(--muted);font-style:normal;}}
  .nav-group{{padding:14px 10px 4px;}}
  .nav-group-label{{font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;
    color:var(--muted);padding:0 10px 8px;}}
  .nav-item{{display:flex;align-items:center;gap:10px;width:100%;text-align:left;padding:10px 10px;
    border-radius:10px;border:1px solid transparent;border-left:2px solid transparent;background:transparent;
    color:var(--muted);cursor:pointer;transition:background 150ms ease, border-color 150ms ease, color 150ms ease;
    margin-bottom:2px;}}
  .nav-item:hover{{background:rgba(255,255,255,0.03);color:var(--text);}}
  .nav-item:focus-visible{{outline:2px solid var(--positive);outline-offset:1px;}}
  .nav-item.active{{background:rgba(55,240,131,0.07);border-left-color:var(--positive);color:var(--text);}}
  .nav-icon{{width:18px;height:18px;flex:0 0 18px;color:var(--muted);}}
  .nav-item.active .nav-icon, .nav-item:hover .nav-icon{{color:var(--positive);}}
  .nav-text{{display:flex;flex-direction:column;flex:1;min-width:0;}}
  .nav-title{{font-size:13px;font-weight:600;line-height:1.3;}}
  .nav-subtitle{{font-size:11px;color:var(--muted);line-height:1.3;margin-top:1px;
    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
  .nav-num{{font-size:11px;color:var(--muted);flex:0 0 auto;}}
  #main{{flex:1;display:flex;flex-direction:column;min-width:0;}}
  #topbar{{display:flex;align-items:center;justify-content:space-between;gap:16px;
    padding:14px 22px;border-bottom:1px solid var(--border);background:rgba(15,38,48,0.5);}}
  #topbar h2{{font-size:15px;font-weight:600;margin:0;color:var(--text);}}
  #topbar p{{font-size:12px;color:var(--muted);margin:2px 0 0;}}
  #openNewTab{{font-size:12px;color:var(--muted);text-decoration:none;border:1px solid var(--border);
    border-radius:8px;padding:6px 12px;white-space:nowrap;transition:color 150ms ease, border-color 150ms ease;}}
  #openNewTab:hover{{color:var(--positive);border-color:var(--positive);}}
  #openNewTab:focus-visible{{outline:2px solid var(--positive);outline-offset:1px;}}
  #frameWrap{{flex:1;position:relative;}}
  #reportFrame{{width:100%;height:100%;border:0;display:block;background:var(--ground);}}
  #menuToggle{{display:none;}}
  @media (max-width: 900px) {{
    #sidebar{{position:fixed;inset:0 30% 0 0;z-index:40;transform:translateX(-100%);
      transition:transform 200ms ease;box-shadow:24px 0 48px rgba(0,0,0,0.4);}}
    #sidebar.open{{transform:translateX(0);}}
    #menuToggle{{display:inline-flex;}}
  }}
</style>
</head>
<body>
<div id="shell">
  <aside id="sidebar">
    <div id="brand">
      <h1>NIFTY &amp; Midcap Strategy Lab</h1>
      <p>{len(ALL_ITEMS)} backtested strategies &middot; NIFTY 50, NIFTY Midcap 150 &amp; a momentum factor &middot; each report is a full standalone analysis</p>
    </div>
    {jump_html}
    {nav_html}
  </aside>
  <main id="main">
    <div id="topbar">
      <button id="menuToggle" aria-label="Toggle navigation" class="text-[var(--muted)] border border-[var(--border)] rounded-lg px-3 py-2 text-sm">&#9776;</button>
      <div>
        <h2 id="topTitle">{default_item['title']}</h2>
        <p id="topSubtitle">{default_item['subtitle']}</p>
      </div>
      <a id="openNewTab" href="{default_item['file']}" target="_blank" rel="noopener">Open in new tab &#8599;</a>
    </div>
    <div id="frameWrap">
      <iframe id="reportFrame" src="{default_item['file']}" title="Strategy report"></iframe>
    </div>
  </main>
</div>
<script>
  const ITEMS = {items_json};
  const frame = document.getElementById('reportFrame');
  const topTitle = document.getElementById('topTitle');
  const topSubtitle = document.getElementById('topSubtitle');
  const openLink = document.getElementById('openNewTab');
  const sidebar = document.getElementById('sidebar');
  const jumpSelect = document.getElementById('jumpSelect');

  function selectItem(id, pushHash) {{
    const item = ITEMS[id];
    if (!item) return;
    frame.src = item.file;
    topTitle.textContent = item.title;
    topSubtitle.textContent = item.subtitle;
    openLink.href = item.file;
    document.querySelectorAll('.nav-item').forEach(el => {{
      el.classList.toggle('active', el.getAttribute('data-id') === id);
    }});
    if (jumpSelect.value !== id) jumpSelect.value = id;
    if (pushHash !== false) history.replaceState(null, '', '#' + id);
    sidebar.classList.remove('open');
  }}

  document.querySelectorAll('.nav-item').forEach(el => {{
    el.addEventListener('click', () => selectItem(el.getAttribute('data-id')));
  }});

  jumpSelect.addEventListener('change', () => selectItem(jumpSelect.value));

  document.getElementById('menuToggle').addEventListener('click', () => {{
    sidebar.classList.toggle('open');
  }});

  const initial = (location.hash || '').replace('#', '');
  if (initial && ITEMS[initial]) selectItem(initial, false);
</script>
</body></html>"""


if __name__ == "__main__":
    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(build())
    print("Wrote dashboard.html")
