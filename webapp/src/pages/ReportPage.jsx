import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ITEM_BY_ID, isPremiumReport } from "../data/reportsIndex";
import { useAuth } from "../context/AuthContext";
import { supabase, SUPABASE_CONFIGURED } from "../lib/supabaseClient";
import { extractSeries } from "../lib/viewmodel";
import KpiTable from "../components/KpiTable";
import SmoothChart from "../components/SmoothChart";
import DrawdownChart from "../components/DrawdownChart";
import ProseSection from "../components/ProseSection";
import TradeLog from "../components/TradeLog";
import LockedReportGate from "../components/LockedReportGate";
import Panel, { WhatThisShows } from "../components/Panel";

const DATA_BASE = "./data/";

export default function ReportPage() {
  const { id } = useParams();
  const item = ITEM_BY_ID[id];
  const { isLoggedIn, loading: authLoading } = useAuth();
  const premium = item ? isPremiumReport(id) : false;
  const locked = premium && !isLoggedIn;

  const [series, setSeries] = useState(null);
  const [symbol, setSymbol] = useState("₹");
  const [content, setContent] = useState(null);
  const [proseOpen, setProseOpen] = useState(false);
  const [error, setError] = useState(null);
  const [trades, setTrades] = useState(null);
  const [tradeStats, setTradeStats] = useState(null);

  useEffect(() => {
    setSeries(null);
    setContent(null);
    setProseOpen(false);
    setError(null);
    setTrades(null);
    setTradeStats(null);
    // Locked premium reports never fetch anything at all — the KPI/chart
    // data genuinely doesn't reach the browser in this state, not just
    // hidden by CSS. Wait for auth state to resolve first so a logged-in
    // visitor doesn't briefly flash the locked gate on page load.
    if (!item || authLoading || locked) return;

    // Results: free reports (id < 11) still come from the public static
    // files; premium reports (id >= 11) come only from Supabase's
    // RLS-protected premium_reports table, readable only because we're
    // logged in at this point.
    const resultsPromise = premium
      ? supabase
          .from("premium_reports")
          .select("results")
          .eq("report_id", id)
          .single()
          .then(({ data, error: err }) => {
            if (err) throw new Error(`Could not load premium data for report ${id}: ${err.message}`);
            return data.results;
          })
      : fetch(DATA_BASE + item.file).then((r) => {
          if (!r.ok) throw new Error(`Could not load ${item.file}`);
          return r.json();
        });

    // Prose (strategy logic, disclosures & limitations) is ALWAYS gated
    // behind login, for every report including the free tier — only
    // fetched here because we already know isLoggedIn is true (locked
    // covers premium-and-signed-out; free-and-signed-out falls through to
    // this effect but skips the prose fetch below).
    const prosePromise = isLoggedIn && SUPABASE_CONFIGURED
      ? supabase
          .from("report_prose")
          .select("content")
          .eq("report_id", id)
          .single()
          .then(({ data }) => data?.content ?? null)
          .catch(() => null)
      : Promise.resolve(null);

    Promise.all([resultsPromise, prosePromise])
      .then(([raw, proseContent]) => {
        const found = extractSeries(raw);
        setSeries(found);
        setSymbol(raw.currency_symbol || "₹");
        setContent(proseContent);
        // only present on reports that carry a full trade-by-trade log —
        // every other report simply has no "trades" key and TradeLog
        // renders nothing.
        setTrades(raw.trades ?? null);
        setTradeStats(raw.trade_stats ?? null);
      })
      .catch((e) => setError(e.message));
  }, [id, item, premium, locked, isLoggedIn, authLoading]);

  if (!item) {
    return (
      <Panel>
        <p className="text-text">Unknown report id “{id}”.</p>
      </Panel>
    );
  }

  if (authLoading) {
    return <div className="text-muted text-sm animate-pulse">Loading…</div>;
  }

  if (locked) {
    return <LockedReportGate title={item.title} />;
  }

  if (error) {
    return (
      <Panel accent="danger">
        <p className="text-text">Couldn't load this report's data: {error}</p>
        <p className="text-muted text-sm mt-2">
          {premium
            ? "Premium report data comes from Supabase — make sure the project is configured and seeded (see scripts/seed_supabase.py)."
            : (
              <>
                If you're running this locally, make sure <code className="font-mono">{item.file}</code> exists in{" "}
                <code className="font-mono">public/data/</code>.
              </>
            )}
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
        <WhatThisShows>
          Every series this report's data actually contains, detected automatically — net return, {series[0]?.growthLabel ?? "CAGR"}, max
          drawdown and longest time underwater, exactly as computed in the original backtest (no numbers are recalculated here).
        </WhatThisShows>
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

      <ProseSection content={content} open={proseOpen} onToggle={() => setProseOpen((v) => !v)} locked={!isLoggedIn} />
    </div>
  );
}
