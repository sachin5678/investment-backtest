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
ICON_STOPWATCH = '<circle cx="12" cy="13" r="8" fill="none"/><line x1="12" y1="13" x2="12" y2="8"/><line x1="9" y1="2" x2="15" y2="2"/><line x1="12" y1="2" x2="12" y2="5"/>'
ICON_LOCK = '<rect x="5" y="11" width="14" height="10" rx="1.5" fill="none"/><path d="M8 11V7a4 4 0 0 1 8 0v4" fill="none"/>'
ICON_LINK = '<path d="M9 15 15 9" fill="none"/><path d="M12 6l2-2a4 4 0 1 1 6 6l-2 2" fill="none"/><path d="M12 18l-2 2a4 4 0 1 1-6-6l2-2" fill="none"/>'
ICON_SCALE = '<path d="M12 3v18" fill="none"/><path d="M5 7h14" fill="none"/><path d="M5 7l-3 6a3 3 0 0 0 6 0z" fill="none"/><path d="M19 7l-3 6a3 3 0 0 0 6 0z" fill="none"/>'
ICON_TUNE = '<line x1="4" y1="6" x2="20" y2="6"/><circle cx="9" cy="6" r="2" fill="currentColor" stroke="none"/><line x1="4" y1="12" x2="20" y2="12"/><circle cx="15" cy="12" r="2" fill="currentColor" stroke="none"/><line x1="4" y1="18" x2="20" y2="18"/><circle cx="7" cy="18" r="2" fill="currentColor" stroke="none"/>'
ICON_COMPARE = '<path d="M12 3v18" fill="none"/><path d="M7 7 3 12l4 5" fill="none"/><path d="M17 7l4 5-4 5" fill="none"/>'
ICON_FLIP = '<path d="M4 7h11l-3-3" fill="none"/><path d="M20 17H9l3 3" fill="none"/>'
ICON_PEAK = '<polyline points="3,19 8,10 12,15 16,6 21,19" fill="none"/><line x1="16" y1="6" x2="20" y2="6"/><line x1="16" y1="6" x2="16" y2="10"/>'
ICON_WEIGHT = '<circle cx="12" cy="6" r="3" fill="none"/><path d="M7 21l2-9h6l2 9" fill="none"/><line x1="6" y1="21" x2="18" y2="21"/>'
ICON_SPLIT = '<path d="M6 4v6a6 6 0 0 0 6 6v4" fill="none"/><path d="M18 4v6a6 6 0 0 1-6 6" fill="none"/><circle cx="6" cy="4" r="1.5" fill="currentColor" stroke="none"/><circle cx="18" cy="4" r="1.5" fill="currentColor" stroke="none"/>'
ICON_LAYERS = '<polygon points="12,3 21,8 12,13 3,8" fill="none"/><polyline points="3,13 12,18 21,13" fill="none"/><polyline points="3,18 12,23 21,18" fill="none"/>'
ICON_SPROUT = '<path d="M12 21V11" fill="none"/><path d="M12 11C12 6 8 4 4 4c0 4 2 8 8 8" fill="none"/><path d="M12 14c0-4 4-6 8-6 0 4-2 7-8 8" fill="none"/>'
ICON_FUNNEL = '<path d="M4 4h16l-6 8v6l-4 2v-8z" fill="none"/>'
ICON_SHIELD_OFF = '<path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z" fill="none"/><line x1="8" y1="8" x2="16" y2="16"/><line x1="16" y1="8" x2="8" y2="16"/>'
ICON_SHIELD_500 = '<path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z" fill="none"/><path d="M9 12l2.2 2.2L15.5 9.5" fill="none"/><circle cx="18" cy="6" r="3" fill="currentColor" stroke="none"/>'
ICON_SHIELD_SPROUT = '<path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z" fill="none"/><path d="M12 16v-6" fill="none"/><path d="M12 10c0-3-2.5-4-5-4 0 3 1.5 5 5 5" fill="none"/>'
ICON_SHIELD_FUNNEL = '<path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z" fill="none"/><path d="M9 8h6l-2.2 3v3l-1.6.8v-3.8z" fill="none"/>'
ICON_RULER = '<path d="M4 15l5-9 11 6-5 9z" fill="none"/><path d="M12 8l1.5 2.5" fill="none"/><path d="M10 11.5l1.5 2.5" fill="none"/><path d="M8 15l1.5 2.5" fill="none"/>'
ICON_HOURGLASS = '<path d="M6 3h12" fill="none"/><path d="M6 21h12" fill="none"/><path d="M7 3c0 5 5 6 5 9s-5 4-5 9" fill="none"/><path d="M17 3c0 5-5 6-5 9s5 4 5 9" fill="none"/>'
ICON_COIN_SHIELD = '<path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z" fill="none"/><circle cx="12" cy="11" r="3" fill="none"/><path d="M12 9v.5" fill="none"/><path d="M12 12.5v.5" fill="none"/>'
ICON_SCALE_10 = '<circle cx="6" cy="6" r="3" fill="none"/><circle cx="12" cy="10" r="2.2" fill="none"/><circle cx="18" cy="6" r="1.4" fill="none"/><path d="M4 18h16" fill="none"/><path d="M6 9v9" fill="none"/><path d="M12 12.2v5.8" fill="none"/><path d="M18 7.4v9.6" fill="none"/>'
ICON_TARGET_SELF = '<circle cx="12" cy="12" r="9" fill="none"/><circle cx="12" cy="12" r="5" fill="none"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/>'

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
            {"id": "28", "file": "28_nifty100_momentum5.html", "icon": ICON_FLASK,
             "title": "“NIFTY100 Momentum 5”", "subtitle": "More concentrated: top 5 instead of top 10, vs. report 12"},
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
            {"id": "29", "file": "29_smallcap250_momentum10_5.html", "icon": ICON_BOLT,
             "title": "Smallcap250 Momentum 10 & 5", "subtitle": "Concentration test — more names wins here, unlike NIFTY100"},
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
            {"id": "26", "file": "26_midcap_momentum10_2020_2023_tradelog.html", "icon": ICON_LEDGER,
             "title": "Midcap Momentum 10 — 2020-2023, Trade Log", "subtitle": "The COVID crash and V-recovery window, every buy and sell shown"},
            {"id": "27", "file": "27_midcap_momentum10_stoploss_compare.html", "icon": ICON_STOPWATCH,
             "title": "Midcap Momentum 10 — Stop-Loss: 15% vs. 30%", "subtitle": "Two thresholds compared against the original, no stop"},
            {"id": "30", "file": "30_midcap_momentum10_breakeven_lock.html", "icon": ICON_LOCK,
             "title": "Midcap Momentum 10 — Breakeven Profit-Lock", "subtitle": "No stop-loss — just lock in cost if a +30% winner fully reverses"},
            {"id": "31", "file": "31_midcap_momentum10_carried_tradelog.html", "icon": ICON_LINK,
             "title": "Midcap Momentum 10 — Carried-Position Trade Log", "subtitle": "New / Carried / Exited tags — one row per real holding, 2015 to date"},
            {"id": "32", "file": "32_midcap_momentum10_kotak_mtf_2x.html", "icon": ICON_SCALE,
             "title": "Midcap Momentum 10 — 2x Kotak Neo MTF Leverage", "subtitle": "Real MTF interest, doubled charges, and modeled margin-call risk"},
            {"id": "33", "file": "33_midcap_momentum10_12_1_skip_month.html", "icon": ICON_TUNE,
             "title": "Midcap Momentum 10 — 12-1 Skip-Month Formula", "subtitle": "The academic momentum convention, tested against the original"},
            {"id": "34", "file": "34_midcap_momentum10_relative_momentum.html", "icon": ICON_COMPARE,
             "title": "Midcap Momentum 10 — Relative Momentum vs. NIFTY 50", "subtitle": "Rank on excess return over the market, not absolute return"},
            {"id": "35", "file": "35_midcap_momentum10_bottom10_reversal.html", "icon": ICON_FLIP,
             "title": "Midcap Momentum 10 — Bottom-10 Reversal Sanity Check", "subtitle": "Deliberately buy the worst-ranked stocks — does momentum survive the flip test?"},
            {"id": "36", "file": "36_midcap_momentum10_52wk_high.html", "icon": ICON_PEAK,
             "title": "Midcap Momentum 10 — 52-Week-High Proximity", "subtitle": "A genuinely different momentum proxy, tested against the original"},
            {"id": "37", "file": "37_midcap_momentum10_frontloaded_weights.html", "icon": ICON_WEIGHT,
             "title": "Midcap Momentum 10 — Front-Loaded 3m/6m/12m Weights", "subtitle": "50/30/20 weighting toward recent momentum — a real risk/return trade-off"},
            {"id": "38", "file": "38_midcap_momentum10_frontloaded_two_splits.html", "icon": ICON_SPLIT,
             "title": "Midcap Momentum 10 — Front-Loaded Weighting, Two Splits", "subtitle": "50/30/20 vs. a gentler 40/35/25 — the trade-off isn't a smooth dial"},
            {"id": "39", "file": "39_nifty500_momentum10_frontloaded_vs_old.html", "icon": ICON_LAYERS,
             "title": "NIFTY500 Momentum 10 — Front-Loaded vs. Old Logic", "subtitle": "Same reformulation, different universe — the opposite result from Midcap150"},
            {"id": "40", "file": "40_smallcap250_momentum10_frontloaded_vs_old.html", "icon": ICON_SPROUT,
             "title": "Smallcap250 Momentum 10 — Front-Loaded vs. Old Logic", "subtitle": "A third universe confirms NIFTY500's clean win, not Midcap150's trade-off"},
            {"id": "41", "file": "41_nifty100_momentum10_frontloaded_vs_old.html", "icon": ICON_FUNNEL,
             "title": "NIFTY100 Momentum 10 — Front-Loaded vs. Old Logic", "subtitle": "The narrowest universe yet — front-loading loses on both CAGR and drawdown"},
            {"id": "42", "file": "42_midcap_momentum10_200ema_regime_filter.html", "icon": ICON_SHIELD_OFF,
             "title": "Midcap Momentum 10 — 200-Day EMA Regime Filter", "subtitle": "Cash whenever NIFTY 50 is below its own 200-EMA — small CAGR cost, big drawdown cut"},
            {"id": "43", "file": "43_nifty500_momentum10_200ema_regime_filter.html", "icon": ICON_SHIELD_500,
             "title": "NIFTY500 Momentum 10 — 200-Day EMA Regime Filter", "subtitle": "Same filter, second universe — the same trade-off holds"},
            {"id": "44", "file": "44_smallcap250_momentum10_200ema_regime_filter.html", "icon": ICON_SHIELD_SPROUT,
             "title": "Smallcap250 Momentum 10 — 200-Day EMA Regime Filter", "subtitle": "The most volatile universe gets the biggest drawdown cut"},
            {"id": "45", "file": "45_nifty100_momentum10_200ema_regime_filter.html", "icon": ICON_SHIELD_FUNNEL,
             "title": "NIFTY100 Momentum 10 — 200-Day EMA Regime Filter", "subtitle": "Almost a free lunch — unlike front-loading, this filter doesn't break down on a narrow universe"},
            {"id": "46", "file": "46_midcap_momentum10_ema_span_sensitivity.html", "icon": ICON_RULER,
             "title": "Midcap Momentum 10 — EMA-Span Sensitivity (100/150/200/250)", "subtitle": "Wider isn't always better — 250 days is the worst span on both CAGR and drawdown"},
            {"id": "47", "file": "47_midcap_momentum10_confirmation_delay_sensitivity.html", "icon": ICON_HOURGLASS,
             "title": "Midcap Momentum 10 — Confirmation-Delay Sensitivity", "subtitle": "Waiting a few days to reduce whipsaw cuts trades but costs more CAGR than it saves"},
            {"id": "48", "file": "48_midcap_momentum10_gold_vs_cash.html", "icon": ICON_COIN_SHIELD,
             "title": "Midcap Momentum 10 — Gold Instead of Cash", "subtitle": "Gold beats cash on CAGR without giving up any drawdown protection"},
            {"id": "49", "file": "49_smallcap250_momentum10_gold_vs_cash.html", "icon": ICON_COIN_SHIELD,
             "title": "Smallcap250 Momentum 10 — Gold Instead of Cash", "subtitle": "The same clean win as Midcap150, on a second universe"},
            {"id": "50", "file": "50_nifty100_momentum10_gold_vs_cash.html", "icon": ICON_COIN_SHIELD,
             "title": "NIFTY100 Momentum 10 — Gold Instead of Cash", "subtitle": "Three for three — gold beats cash on every universe tested"},
            {"id": "51", "file": "51_midcap_momentum10_invvol_weighting.html", "icon": ICON_SCALE_10,
             "title": "Midcap Momentum 10 — Inverse-Volatility Weighting", "subtitle": "Down-weighting shaky picks costs more CAGR than it saves in drawdown"},
            {"id": "52", "file": "52_smallcap250_momentum10_invvol_weighting.html", "icon": ICON_SCALE_10,
             "title": "Smallcap250 Momentum 10 — Inverse-Volatility Weighting", "subtitle": "Same modest trade-off as Midcap150, on a second universe"},
            {"id": "53", "file": "53_nifty100_momentum10_invvol_weighting.html", "icon": ICON_SCALE_10,
             "title": "NIFTY100 Momentum 10 — Inverse-Volatility Weighting", "subtitle": "Consistent everywhere, unlike front-loaded momentum's NIFTY100 breakdown"},
            {"id": "54", "file": "54_midcap_momentum10_own_index_trend_filter.html", "icon": ICON_TARGET_SELF,
             "title": "Midcap Momentum 10 — Universe-Specific Trend Filter", "subtitle": "Inconclusive — the midcap ETF proxy's short history limits this test"},
            {"id": "55", "file": "55_smallcap250_momentum10_own_index_trend_filter.html", "icon": ICON_TARGET_SELF,
             "title": "Smallcap250 Momentum 10 — Universe-Specific Trend Filter", "subtitle": "A real index, full history — better drawdown, some CAGR cost"},
            {"id": "56", "file": "56_nifty100_momentum10_own_index_trend_filter.html", "icon": ICON_TARGET_SELF,
             "title": "NIFTY100 Momentum 10 — Universe-Specific Trend Filter", "subtitle": "Same trade-off as Smallcap250 — two of three full-history tests agree"},
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
