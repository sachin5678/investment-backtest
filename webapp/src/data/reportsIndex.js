// Mirrors dashboard.html's GROUPS structure — same ids, same grouping, same
// icons — but each entry also carries the primary results*.json file this
// report's own numbers live in (see backtest.py mapping notes in
// extract_report_content.py / the project's build_html*.py files).

const ICON_TRENDING = "M3 17l6-6 4 4 8-8 M15 7h6v6";
const ICON_BARS = "M4 20V10 M10 20V6 M16 20V3";
const ICON_WALLET = "M3 7h18v12H3z M3 11h18";
const ICON_REFRESH = "M20 11a8 8 0 1 0-2.3 5.7 M20 4v7h-7";
const ICON_CALENDAR = "M3 5h18v16H3z M3 10h18 M8 3v4 M16 3v4";
const ICON_BOLT = "M13 2 4 14h7l-2 8 11-12h-7z";
const ICON_FLASK = "M9 2v6.5l-5.2 9A2 2 0 0 0 5.6 21h12.8a2 2 0 0 0 1.8-3.5L15 8.5V2 M7 2h10 M8 15h8";
const ICON_GRID = "M3,3h8v8h-8z M13,3h8v8h-8z M3,13h8v8h-8z M13,13h8v8h-8z";
const ICON_SHIELD = "M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z M9 12l2.2 2.2L15.5 9.5";
const ICON_GLOBE = "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M12 3c-3 4-3 14 0 18 M12 3c3 4 3 14 0 18 M3 12h18";
const ICON_PULSE = "M3 12h5l2-6 4 12 2-6h5";
const ICON_COINS = "M9,3a6,6 0 1 0 0,12a6,6 0 1 0 0,-12 M15,9a6,6 0 1 1 0,10.5a6,6 0 1 1 -6,-4.5";
const ICON_LEDGER = "M4 3h16v18h-16z M8 8h8 M8 12h8 M8 16h5";
const ICON_COMPASS = "M12,3a9,9 0 1 0 0,18a9,9 0 1 0 0,-18 M15 9l-2 4-4 2 2-4z";
const ICON_STOPWATCH = "M12,21a8,8 0 1 0 0,-16a8,8 0 1 0 0,16 M12 13V8 M9 2h6 M12 2v3";
const ICON_LOCK = "M5 11h14v10h-14z M8 11V7a4 4 0 0 1 8 0v4";
const ICON_LINK = "M9 15 15 9 M12 6l2-2a4 4 0 1 1 6 6l-2 2 M12 18l-2 2a4 4 0 1 1-6-6l2-2";
const ICON_SCALE = "M12,3v18 M5,7h14 M5,7l-3,6a3,3 0 0 0 6,0z M19,7l-3,6a3,3 0 0 0 6,0z";
const ICON_TUNE = "M4 6h16 M9 4v4 M4 12h16 M15 10v4 M4 18h16 M7 16v4";
const ICON_COMPARE = "M12 3v18 M7 7 3 12l4 5 M17 7l4 5-4 5";
const ICON_FLIP = "M4 7h11l-3-3 M20 17H9l3 3";
const ICON_PEAK = "M3 19l5-9 4 5 4-9 5 13 M16 6h4v4";
const ICON_WEIGHT = "M12,3a3,3 0 1 0 0,6a3,3 0 1 0 0,-6 M7 21l2-9h6l2 9 M6 21h12";
const ICON_SPLIT = "M6 4v6a6,6 0 0 0 6,6v4 M18 4v6a6,6 0 0 1 -6,6";
const ICON_LAYERS = "M12 3 21 8 12 13 3 8z M3 13l9 5 9-5 M3 18l9 5 9-5";
const ICON_SPROUT = "M12 21V11 M12 11C12 6 8 4 4 4c0 4 2 8 8 8 M12 14c0-4 4-6 8-6 0 4-2 7-8 8";
const ICON_FUNNEL = "M4 4h16l-6 8v6l-4 2v-8z";
const ICON_SHIELD_OFF = "M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z M8 8l8 8 M16 8l-8 8";
const ICON_SHIELD_500 = "M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z M9 12l2.2 2.2L15.5 9.5";
const ICON_SHIELD_SPROUT = "M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z M12 16v-6 M12 10c0-3-2.5-4-5-4 0 3 1.5 5 5 5";
const ICON_SHIELD_FUNNEL = "M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z M9 8h6l-2.2 3v3l-1.6.8v-3.8z";
const ICON_RULER = "M4 15l5-9 11 6-5 9z M12 8l1.5 2.5 M10 11.5l1.5 2.5 M8 15l1.5 2.5";
const ICON_HOURGLASS = "M6 3h12 M6 21h12 M7 3c0 5 5 6 5 9s-5 4-5 9 M17 3c0 5-5 6-5 9s5 4 5 9";
const ICON_COIN_SHIELD = "M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z M12 8a3 3 0 1 0 0 6 3 3 0 0 0 0-6z";
const ICON_SCALE_10 = "M6,3a3,3 0 1 0 0,6a3,3 0 1 0 0,-6 M12,7.8a2.2,2.2 0 1 0 0,4.4a2.2,2.2 0 1 0 0,-4.4 M18,4.6a1.4,1.4 0 1 0 0,2.8a1.4,1.4 0 1 0 0,-2.8 M4 18h16 M6 9v9 M12 12.2v5.8 M18 7.4v9.6";
const ICON_TARGET_SELF = "M12,3a9,9 0 1 0 0,18a9,9 0 1 0 0,-18 M12,7a5,5 0 1 0 0,10a5,5 0 1 0 0,-10 M12 10.5v3 M10.5 12h3";
const ICON_BREADTH = "M3 21v-7 M8 21v-12 M13 21v-17 M18 21v-10 M3 7l6-3 5 2 7-4";
const ICON_TRAIL_STOP = "M3 18l4-8 5 3 5-9 4 3 M7 10v11 M17 4v17";
const ICON_FORK_SPEED = "M12 3v6 M12 9l-7 4v8 M12 9l7 4v8 M16 9l3 4-4 1";
const ICON_GATE = "M4 21V9l8-6 8 6v12 M4 15h16";
const ICON_DIMMER = "M12,3a9,9 0 1 0 0,18a9,9 0 1 0 0,-18";
const ICON_DIMMER_COIN = "M10,4a8,8 0 1 0 0,16a8,8 0 1 0 0,-16 M19,2.8a3.2,3.2 0 1 0 0,6.4a3.2,3.2 0 1 0 0,-6.4";

export const GROUPS = [
  {
    label: "NIFTY 50 Breakout System",
    items: [
      { id: "01", file: "results.json", icon: ICON_TRENDING, title: "Backtest: 20-day High / 10-day Low", subtitle: "Frictionless vs. cost-loaded, QQQ & NIFTY 50" },
      { id: "02", file: "results.json", icon: ICON_BARS, title: "vs. Buy-and-Hold Benchmark", subtitle: "Same instrument, same start, side by side" },
    ],
  },
  {
    label: "Cash Timing (NIFTY 50)",
    items: [
      { id: "03", file: "results2.json", icon: ICON_WALLET, title: "Wait for the Dip", subtitle: "Annual cash/NIFTY switch on a -10% YTD dip" },
    ],
  },
  {
    label: "Midcap Rotation",
    items: [
      { id: "04", file: "results3.json", icon: ICON_REFRESH, title: "Flight to Midcap", subtitle: "NIFTY 50 → midcap on a -15% ATH drawdown" },
    ],
  },
  {
    label: "SIP + Tactical Overlays (Midcap)",
    items: [
      { id: "05", file: "results4.json", icon: ICON_CALENDAR, title: "SIP + Dip Lump-Sums", subtitle: "+₹5k / +₹10k at -10% / -20% from ATH" },
      { id: "06", file: "results5.json", icon: ICON_CALENDAR, title: "SIP + Confirmed-Recovery Lump-Sum", subtitle: "Buy strength after a full round-trip, not the dip" },
      { id: "07", file: "results6.json", icon: ICON_CALENDAR, title: "SIP Doubles on Drawdown (15%)", subtitle: "Recurring SIP itself doubles through a decline" },
      { id: "08", file: "results7.json", icon: ICON_CALENDAR, title: "SIP Doubles on Drawdown (10%)", subtitle: "Same rule, more sensitive 10% trigger" },
      { id: "09", file: "results8.json", icon: ICON_CALENDAR, title: "Does the SIP Date Matter?", subtitle: "1st vs. 10th vs. 20th vs. last day of month" },
    ],
  },
  {
    label: "Momentum Factor",
    items: [
      { id: "10", file: "results9.json", icon: ICON_BOLT, title: "SIP in a Momentum ETF", subtitle: "HDFCMOMENT.NS vs. midcap vs. NIFTY, ~2.8yr" },
      { id: "11", file: "results10.json", icon: ICON_FLASK, title: "Momentum Formula, 18 Years", subtitle: "NIFTY200/Top-30 reconstruction — survivorship-biased" },
      { id: "12", file: "results11.json", icon: ICON_FLASK, title: "“NIFTY100 Momentum 10”", subtitle: "Custom variant — not a real NSE index" },
      { id: "28", file: "results27.json", icon: ICON_FLASK, title: "“NIFTY100 Momentum 5”", subtitle: "More concentrated: top 5 instead of top 10, vs. report 12" },
    ],
  },
  {
    label: "Quality Factor",
    items: [
      { id: "13", file: "results12.json", icon: ICON_FLASK, title: "Quality-50 Static Basket", subtitle: "Today's fundamentals, bought once — not a rebalanced index" },
    ],
  },
  {
    label: "Midcap Momentum + Gold",
    items: [
      { id: "14", file: "results13.json", icon: ICON_BOLT, title: "Midcap Momentum-20 + Gold Blend", subtitle: "Custom top-20 variant, plus a 50/50 gold diversification test" },
      { id: "15", file: "results14.json", icon: ICON_REFRESH, title: "Momentum-20 — Quarterly Rebalance", subtitle: "Same setup, rebalanced 4x/year instead of 2x" },
      { id: "16", file: "results15.json", icon: ICON_BOLT, title: "Smallcap vs. Midcap Momentum", subtitle: "Momentum-20 vs Momentum-10 vs Midcap Momentum-10" },
      { id: "17", file: "results16.json", icon: ICON_REFRESH, title: "Monthly Rebalance — All 6 Compared", subtitle: "Every momentum reconstruction, monthly vs its original cadence" },
      { id: "18", file: "results17.json", icon: ICON_BOLT, title: "Midcap-30 & NIFTY500 Momentum 10/15", subtitle: "Real rebalance months this time — May/Nov and June/Dec" },
      { id: "29", file: "results28.json", icon: ICON_BOLT, title: "Smallcap250 Momentum 10 & 5", subtitle: "Concentration test — more names wins here, unlike NIFTY100" },
    ],
  },
  {
    label: "Sector Rotation",
    items: [
      { id: "19", file: "results18.json", icon: ICON_GRID, title: "Sector-First Momentum Rotation", subtitle: "Rank sectors by momentum first, then top 3 stocks within the leader" },
    ],
  },
  {
    label: "Momentum + Gold, Drawdown-Triggered",
    items: [
      { id: "20", file: "results19.json", icon: ICON_SHIELD, title: "Momentum + Gold, With a Drawdown Catch", subtitle: "-20% drawdown sells all gold into momentum, until a full recovery" },
    ],
  },
  {
    label: "Beyond India",
    items: [
      { id: "21", file: "results20.json", icon: ICON_GLOBE, title: "“NASDAQ100 Momentum 10”", subtitle: "The same formula, applied to the Nasdaq-100 since 2000" },
    ],
  },
  {
    label: "Technical Signals",
    items: [
      { id: "22", file: "results21.json", icon: ICON_PULSE, title: "Monthly RSI-70 Crossover Rotation", subtitle: "Any NSE stock above ₹2,000 Cr — up to 5 positions, 15% stop or month-end" },
    ],
  },
  {
    label: "Commodities",
    items: [
      { id: "23", file: "results22.json", icon: ICON_COINS, title: "Gold/Silver Absolute Momentum Rotation", subtitle: "Hold each metal only while its own momentum is positive, else cash" },
    ],
  },
  {
    label: "Trade-Level Detail",
    items: [
      { id: "24", file: "results23.json", icon: ICON_LEDGER, title: "Midcap Momentum 10 — Last 2 Years, Trade Log", subtitle: "Every stock bought and sold, with entry/exit price and P&L, vs. the midcap ETF" },
      { id: "25", file: "results24.json", icon: ICON_COMPASS, title: "Midcap Momentum 10 — Rebalance Offsets Compared", subtitle: "Jan/Jul, Feb/Aug, Mar/Sep, Apr/Oct, May/Nov, Jun/Dec — all six, side by side" },
      { id: "26", file: "results25.json", icon: ICON_LEDGER, title: "Midcap Momentum 10 — 2020-2023, Trade Log", subtitle: "The COVID crash and V-recovery window, every buy and sell shown" },
      { id: "27", file: "results26.json", icon: ICON_STOPWATCH, title: "Midcap Momentum 10 — Stop-Loss: 15% vs. 30%", subtitle: "Two thresholds compared against the original, no stop" },
      { id: "30", file: "results29.json", icon: ICON_LOCK, title: "Midcap Momentum 10 — Breakeven Profit-Lock", subtitle: "No stop-loss — just lock in cost if a +30% winner fully reverses" },
      { id: "31", file: "results30.json", icon: ICON_LINK, title: "Midcap Momentum 10 — Carried-Position Trade Log", subtitle: "New / Carried / Exited tags — one row per real holding, 2015 to date" },
      { id: "32", file: "results31.json", icon: ICON_SCALE, title: "Midcap Momentum 10 — 2x Kotak Neo MTF Leverage", subtitle: "Real MTF interest, doubled charges, and modeled margin-call risk" },
      { id: "33", file: "results32.json", icon: ICON_TUNE, title: "Midcap Momentum 10 — 12-1 Skip-Month Formula", subtitle: "The academic momentum convention, tested against the original" },
      { id: "34", file: "results33.json", icon: ICON_COMPARE, title: "Midcap Momentum 10 — Relative Momentum vs. NIFTY 50", subtitle: "Rank on excess return over the market, not absolute return" },
      { id: "35", file: "results34.json", icon: ICON_FLIP, title: "Midcap Momentum 10 — Bottom-10 Reversal Sanity Check", subtitle: "Deliberately buy the worst-ranked stocks — does momentum survive the flip test?" },
      { id: "36", file: "results35.json", icon: ICON_PEAK, title: "Midcap Momentum 10 — 52-Week-High Proximity", subtitle: "A genuinely different momentum proxy, tested against the original" },
      { id: "37", file: "results36.json", icon: ICON_WEIGHT, title: "Midcap Momentum 10 — Front-Loaded 3m/6m/12m Weights", subtitle: "50/30/20 weighting toward recent momentum — a real risk/return trade-off" },
      { id: "38", file: "results37.json", icon: ICON_SPLIT, title: "Midcap Momentum 10 — Front-Loaded Weighting, Two Splits", subtitle: "50/30/20 vs. a gentler 40/35/25 — the trade-off isn't a smooth dial" },
      { id: "39", file: "results38.json", icon: ICON_LAYERS, title: "NIFTY500 Momentum 10 — Front-Loaded vs. Old Logic", subtitle: "Same reformulation, different universe — the opposite result from Midcap150" },
      { id: "40", file: "results39.json", icon: ICON_SPROUT, title: "Smallcap250 Momentum 10 — Front-Loaded vs. Old Logic", subtitle: "A third universe confirms NIFTY500's clean win, not Midcap150's trade-off" },
      { id: "41", file: "results40.json", icon: ICON_FUNNEL, title: "NIFTY100 Momentum 10 — Front-Loaded vs. Old Logic", subtitle: "The narrowest universe yet — front-loading loses on both CAGR and drawdown" },
      { id: "42", file: "results41.json", icon: ICON_SHIELD_OFF, title: "Midcap Momentum 10 — 200-Day EMA Regime Filter", subtitle: "Cash whenever NIFTY 50 is below its own 200-EMA — small CAGR cost, big drawdown cut" },
      { id: "43", file: "results42.json", icon: ICON_SHIELD_500, title: "NIFTY500 Momentum 10 — 200-Day EMA Regime Filter", subtitle: "Same filter, second universe — the same trade-off holds" },
      { id: "44", file: "results43.json", icon: ICON_SHIELD_SPROUT, title: "Smallcap250 Momentum 10 — 200-Day EMA Regime Filter", subtitle: "The most volatile universe gets the biggest drawdown cut" },
      { id: "45", file: "results44.json", icon: ICON_SHIELD_FUNNEL, title: "NIFTY100 Momentum 10 — 200-Day EMA Regime Filter", subtitle: "Almost a free lunch — unlike front-loading, this filter doesn't break down on a narrow universe" },
      { id: "46", file: "results45.json", icon: ICON_RULER, title: "Midcap Momentum 10 — EMA-Span Sensitivity (100/150/200/250)", subtitle: "Wider isn't always better — 250 days is the worst span on both CAGR and drawdown" },
      { id: "47", file: "results46.json", icon: ICON_HOURGLASS, title: "Midcap Momentum 10 — Confirmation-Delay Sensitivity", subtitle: "Waiting a few days to reduce whipsaw cuts trades but costs more CAGR than it saves" },
      { id: "48", file: "results47.json", icon: ICON_COIN_SHIELD, title: "Midcap Momentum 10 — Gold Instead of Cash", subtitle: "Gold beats cash on CAGR without giving up any drawdown protection" },
      { id: "49", file: "results48.json", icon: ICON_COIN_SHIELD, title: "Smallcap250 Momentum 10 — Gold Instead of Cash", subtitle: "The same clean win as Midcap150, on a second universe" },
      { id: "50", file: "results49.json", icon: ICON_COIN_SHIELD, title: "NIFTY100 Momentum 10 — Gold Instead of Cash", subtitle: "Three for three — gold beats cash on every universe tested" },
      { id: "51", file: "results50.json", icon: ICON_SCALE_10, title: "Midcap Momentum 10 — Inverse-Volatility Weighting", subtitle: "Down-weighting shaky picks costs more CAGR than it saves in drawdown" },
      { id: "52", file: "results51.json", icon: ICON_SCALE_10, title: "Smallcap250 Momentum 10 — Inverse-Volatility Weighting", subtitle: "Same modest trade-off as Midcap150, on a second universe" },
      { id: "53", file: "results52.json", icon: ICON_SCALE_10, title: "NIFTY100 Momentum 10 — Inverse-Volatility Weighting", subtitle: "Consistent everywhere, unlike front-loaded momentum's NIFTY100 breakdown" },
      { id: "54", file: "results53.json", icon: ICON_TARGET_SELF, title: "Midcap Momentum 10 — Universe-Specific Trend Filter", subtitle: "Inconclusive — the midcap ETF proxy's short history limits this test" },
      { id: "55", file: "results54.json", icon: ICON_TARGET_SELF, title: "Smallcap250 Momentum 10 — Universe-Specific Trend Filter", subtitle: "A real index, full history — better drawdown, some CAGR cost" },
      { id: "56", file: "results55.json", icon: ICON_TARGET_SELF, title: "NIFTY100 Momentum 10 — Universe-Specific Trend Filter", subtitle: "Same trade-off as Smallcap250 — two of three full-history tests agree" },
      { id: "57", file: "results56.json", icon: ICON_BREADTH, title: "Midcap Momentum 10 — Breadth Confirmation for the Regime Filter", subtitle: "Barely moves the needle — breadth and NIFTY 50's trend are highly correlated" },
      { id: "58", file: "results57.json", icon: ICON_TRAIL_STOP, title: "Midcap Momentum 10 — Trailing Stop vs. Report 27's Fixed Stop", subtitle: "A tight trailing stop backfires badly; a wide one genuinely beats the fixed version" },
      { id: "59", file: "results58.json", icon: ICON_FORK_SPEED, title: "Midcap Momentum 10 — Asymmetric EMA (Fast Re-Entry)", subtitle: "Catching the recovery sooner backfires — more than double the whipsaw, worse drawdown" },
      { id: "60", file: "results59.json", icon: ICON_FORK_SPEED, title: "Smallcap250 Momentum 10 — Asymmetric EMA (Fast Re-Entry)", subtitle: "Same false-start problem as Midcap150, on a second universe" },
      { id: "61", file: "results60.json", icon: ICON_FORK_SPEED, title: "NIFTY100 Momentum 10 — Asymmetric EMA (Fast Re-Entry)", subtitle: "Three for three against the asymmetric design" },
      { id: "62", file: "results61.json", icon: ICON_GATE, title: "Midcap Momentum 10 — Absolute Momentum Gate", subtitle: "The gate almost never fires, so almost nothing changes" },
      { id: "63", file: "results62.json", icon: ICON_GATE, title: "Smallcap250 Momentum 10 — Absolute Momentum Gate", subtitle: "Same non-event, but a bigger CAGR cost this time" },
      { id: "64", file: "results63.json", icon: ICON_GATE, title: "NIFTY100 Momentum 10 — Absolute Momentum Gate", subtitle: "Three for three — the gate never helps, only costs" },
      { id: "65", file: "results64.json", icon: ICON_DIMMER, title: "Midcap Momentum 10 — Volatility-Scaled Smooth Exposure", subtitle: "Beats the binary filter on CAGR at every band width tested" },
      { id: "66", file: "results65.json", icon: ICON_DIMMER, title: "Smallcap250 Momentum 10 — Volatility-Scaled Smooth Exposure", subtitle: "Wider bands dominate the binary filter outright — better CAGR AND drawdown" },
      { id: "67", file: "results66.json", icon: ICON_DIMMER, title: "NIFTY100 Momentum 10 — Volatility-Scaled Smooth Exposure", subtitle: "The pattern reverses — the binary filter dominates every smooth band" },
      { id: "68", file: "results67.json", icon: ICON_DIMMER_COIN, title: "Midcap Momentum 10 — Smooth Exposure + Gold / Liquid Fund", subtitle: "Gold wins outright; a liquid-fund yield assumption gives a smaller, still-real edge over cash" },
      { id: "69", file: "results68.json", icon: ICON_DIMMER_COIN, title: "Smallcap250 Momentum 10 — Smooth Exposure + Gold / Liquid Fund", subtitle: "Gold wins clearly on CAGR here too — drawdown differences are noise, not a real trade-off" },
      { id: "70", file: "results69.json", icon: ICON_DIMMER_COIN, title: "NIFTY100 Momentum 10 — Smooth Exposure + Gold / Liquid Fund", subtitle: "Gold wins clearly on CAGR everywhere tested — drawdown effect ranges from a bonus to a wash" },
      { id: "71", file: "results70.json", icon: ICON_SPLIT, title: "Midcap Momentum 10 — Core-Satellite (70/30) + Full Gold Switch", subtitle: "The shallowest drawdown of any combination tested here — at a real CAGR cost" },
      { id: "72", file: "results71.json", icon: ICON_SPLIT, title: "Midcap Momentum 10 — Core-Satellite (50/50) + Full Gold Switch", subtitle: "More gold, more CAGR given up — but zero extra drawdown protection here" },
      { id: "73", file: "results72.json", icon: ICON_LAYERS, title: "Midcap150 Momentum 50 — A Much Wider Basket", subtitle: "Loses on BOTH CAGR and drawdown against the flagship top-10" },
      { id: "74", file: "results73.json", icon: ICON_FLASK, title: "NIFTY500 Quality 50 — A Real Rebalanced Backtest", subtitle: "Only ~14 months of data support this, but it's a genuine rebalance, not a snapshot" },
      { id: "75", file: "results74.json", icon: ICON_FLASK, title: "Midcap150 Quality 10 — A Real Rebalanced Backtest", subtitle: "Quality lost money outright here — the momentum flagship did not" },
      { id: "76", file: "results75.json", icon: ICON_RULER, title: "Midcap150 Momentum 10 — 400-Day EMA + Gold, Rebalance Cadence", subtitle: "Wider EMA loses on both metrics; more frequent rebalancing shallows drawdown" },
      { id: "77", file: "results76.json", icon: ICON_HOURGLASS, title: "Midcap150 Momentum 10 — Report 48, Rebalance Cadence", subtitle: "The hero design's own semi-annual cadence already looks close to right" },
      { id: "78", file: "results77.json", icon: ICON_LAYERS, title: "Midcap150 Momentum — Report 48 at 5 and 15 Stocks", subtitle: "The gold-hedge filter barely helps at 5 stocks, but helps even more at 15" },
      { id: "79", file: "results78.json", icon: ICON_LAYERS, title: "Midcap150 Momentum — Report 48's Design, Now Through Top-20", subtitle: "Drawdown keeps improving; CAGR keeps falling — the filter stops closing the gap" },
      { id: "80", file: "results79.json", icon: ICON_REFRESH, title: "ETF Momentum Rotation — Top 5 Out of 25 Distinct ETFs", subtitle: "Picking the top 5 by momentum loses to just holding all of them equally" },
      { id: "81", file: "results80.json", icon: ICON_SCALE_10, title: "Midcap150 Momentum 10 — Averaging Down Within the Holding Period", subtitle: "Basically a wash on CAGR, but makes the drawdown meaningfully worse" },
      { id: "82", file: "results81.json", icon: ICON_SCALE_10, title: "Midcap150 Momentum 10 — Averaging With Wider Triggers (25%/40%)", subtitle: "Wider triggers flip the result — CAGR improves, drawdown cost shrinks" },
      { id: "83", file: "results82.json", icon: ICON_SCALE_10, title: "Midcap150 Momentum 10 — Pyramiding Up Instead of Averaging Down", subtitle: "Buying more of a winner beats buying more of a loser, on both CAGR and drawdown" },
      { id: "85", file: "results84.json", icon: ICON_COMPASS, title: "Midcap150 Momentum 10 — Report 48, Rebalance Month Offset", subtitle: "June/December is the safest of five calendars tested, not the highest-CAGR one" },
    ],
  },
];

export const ALL_ITEMS = GROUPS.flatMap((g) => g.items);
export const ITEM_BY_ID = Object.fromEntries(ALL_ITEMS.map((i) => [i.id, i]));

// Reports 01-10 (breakout, cash-timing, basic SIP overlays) are the free
// tier. Everything from 11 onward — every momentum/rotation/RSI/gold
// reconstruction and every trade-level-detail report — is premium.
// NOTE: this is a UI-only gate (see AuthContext.jsx) — every report's
// results file and the shared report_content.json prose file are public
// static assets like any other, reachable directly by anyone who looks;
// login just controls whether the app SHOWS them. Every report's
// disclosure/analysis text is ALSO always hidden until logged in,
// including for the free tier.
export const PREMIUM_MIN_ID = 11;
export function isPremiumReport(id) {
  return Number(id) >= PREMIUM_MIN_ID;
}
