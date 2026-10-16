import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ITEM_BY_ID, isPremiumReport } from "../data/reportsIndex";
import { useAuth } from "../context/AuthContext";
import { extractSeries } from "../lib/viewmodel";
import KpiTable from "../components/KpiTable";
import SmoothChart from "../components/SmoothChart";
import DrawdownChart from "../components/DrawdownChart";
import ProseSection from "../components/ProseSection";
import TradeLog from "../components/TradeLog";
import LockedReportGate from "../components/LockedReportGate";
import Panel, { WhatThisShows } from "../components/Panel";
import ReviewPanels from "../components/ReviewPanels";
import { downloadCsv } from "../lib/csv";

const DATA_BASE = "./data/";

export default function ReportPage() {
  const { id } = useParams();
  const item = ITEM_BY_ID[id];
  const { isLoggedIn } = useAuth();
  const premium = item ? isPremiumReport(id) : false;
  const locked = premium && !isLoggedIn;

  const [series, setSeries] = useState(null);
  const [symbol, setSymbol] = useState("₹");
  const [content, setContent] = useState(null);
  const [proseOpen, setProseOpen] = useState(false);
  const [error, setError] = useState(null);
  const [trades, setTrades] = useState(null);
  const [tradeStats, setTradeStats] = useState(null);
  const [raw, setRaw] = useState(null);

  useEffect(() => {
    setSeries(null);
    setContent(null);
    setProseOpen(false);
    setError(null);
    setTrades(null);
    setTradeStats(null);
    setRaw(null);
    // A locked premium report skips the fetch entirely — it's a UI gate
    // only (every report's data actually sits in the public static
    // webapp/public/data/ files, reachable directly by anyone who looks),
    // but there's no reason to pull the bytes down just to immediately
    // hide them.
    if (!item || locked) return;

    // Findings are static HTML write-ups, not a results JSON — skip the
    // fetch and let the early return below render the iframe instead.
    if (item.file.endsWith(".html")) {
      setSeries([]);
      return;
    }

    Promise.all([
      fetch(DATA_BASE + item.file).then((r) => {
        if (!r.ok) throw new Error(`Could not load ${item.file}`);
        return r.json();
      }),
      // Prose (strategy logic, disclosures & limitations) lives in one
      // shared public file for every report — always fetched, but only
      // ever DISPLAYED when logged in (see ProseSection's locked prop
      // below), matching "always hide analysis from free users."
      fetch(DATA_BASE + "report_content.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ])
      .then(([raw, allContent]) => {
        const found = extractSeries(raw);
        setSeries(found);
        setSymbol(raw.currency_symbol || "₹");
        setContent(allContent?.[id] ?? null);
        // only present on reports that carry a full trade-by-trade log —
        // every other report simply has no "trades" key and TradeLog
        // renders nothing.
        setTrades(raw.trades ?? null);
        setTradeStats(raw.trade_stats ?? null);
        // kept whole for the review panels (health/robustness/tax/rebalances/
        // ranks blocks) — only reports that carry those keys render them.
        setRaw(raw);
      })
      .catch((e) => setError(e.message));
  }, [id, item, locked]);

  if (!item) {
    return (
      <Panel>
        <p className="text-text">Unknown report id “{id}”.</p>
      </Panel>
    );
  }

  if (locked) {
    return <LockedReportGate title={item.title} />;
  }

  if (item.file.endsWith(".html")) {
    return (
      <iframe
        src={`./data/${item.file}`}
        title={item.title}
        className="w-full min-h-[80vh] rounded-xl border border-border bg-ground"
      />
    );
  }

  if (error) {
    return (
      <Panel accent="danger">
        <p className="text-text">Couldn't load this report's data: {error}</p>
        <p className="text-muted text-sm mt-2">
          If you're running this locally, make sure <code className="font-mono">{item.file}</code> exists in{" "}
          <code className="font-mono">public/data/</code>.
        </p>
      </Panel>
    );
  }

  if (!series) {
    return (
      <div className="text-muted text-sm animate-pulse">Loading {item.title}…</div>
    );
  }

  return (
    <div className="space-y-6 w-full">
      <Panel tight>
        <div className="flex items-start justify-between gap-3">
          <WhatThisShows>
            Every series this report's data actually contains, detected automatically — net return, {series[0]?.growthLabel ?? "CAGR"}, max
            drawdown and longest time underwater, exactly as computed in the original backtest (no numbers are recalculated here).
          </WhatThisShows>
          <button
            onClick={() =>
              downloadCsv(
                `${item.file.replace(/\.json$/, "")}_kpis.csv`,
                series.map((s) => ({
                  label: s.label,
                  path: s.path,
                  net_return_pct: s.netReturnPct,
                  growth_pct: s.growthPct,
                  growth_label: s.growthLabel,
                  max_drawdown_pct: s.maxDrawdownPct,
                  longest_underwater_days: s.longestUnderwaterDays,
                }))
              )
            }
            className="text-[11.5px] font-semibold text-muted hover:text-text transition-colors cursor-pointer shrink-0 mt-0.5"
            title="Download this table as CSV"
          >
            ⇩ CSV
          </button>
        </div>
        <KpiTable series={series} symbol={symbol} />
      </Panel>

      <Panel>
        <h3 className="text-base font-bold text-text mb-1">Growth of 100 (rebased)</h3>
        <WhatThisShows>
          Every detected series, rebased to 100 at its own first data point so differently-scaled series overlay sensibly — smooth monotone curve
          through real, downsampled points (not a synthetic average).
        </WhatThisShows>
        <SmoothChart series={series} valuePrefix="" />
      </Panel>

      <Panel>
        <h3 className="text-base font-bold text-text mb-1">Drawdown comparison</h3>
        <WhatThisShows>
          % below each series' own running peak. Computed for illustration on the data available to this page — the precise max-drawdown figure
          for each series is the one shown in the table above, from the original full-resolution backtest.
        </WhatThisShows>
        <DrawdownChart series={series} />
      </Panel>

      <TradeLog trades={trades} tradeStats={tradeStats} symbol={symbol} />

      <ReviewPanels raw={raw} file={item.file} symbol={symbol} />

      <ProseSection content={content} open={proseOpen} onToggle={() => setProseOpen((v) => !v)} locked={!isLoggedIn} />
    </div>
  );
}
