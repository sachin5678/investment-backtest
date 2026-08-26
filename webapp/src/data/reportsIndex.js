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
    ],
  },
];

export const ALL_ITEMS = GROUPS.flatMap((g) => g.items);
export const ITEM_BY_ID = Object.fromEntries(ALL_ITEMS.map((i) => [i.id, i]));

// Reports 01-10 (breakout, cash-timing, basic SIP overlays) are the free
// tier. Everything from 11 onward — every momentum/rotation/RSI/gold
// reconstruction and every trade-level-detail report — is premium: its
// full results data lives only in Supabase's RLS-protected
// premium_reports table, not in a public static file (see
// supabase/schema.sql). Every report's disclosure/analysis text (prose)
// is ALSO always gated behind login, including for the free tier — see
// report_prose in the same schema.
export const PREMIUM_MIN_ID = 11;
export function isPremiumReport(id) {
  return Number(id) >= PREMIUM_MIN_ID;
}
