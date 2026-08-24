import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ITEM_BY_ID } from "../data/reportsIndex";
import { extractSeries } from "../lib/viewmodel";
import KpiTable from "../components/KpiTable";
import SmoothChart from "../components/SmoothChart";
import DrawdownChart from "../components/DrawdownChart";
import ProseSection from "../components/ProseSection";
import Panel, { WhatThisShows } from "../components/Panel";

const DATA_BASE = "./data/";

export default function ReportPage() {
  const { id } = useParams();
  const item = ITEM_BY_ID[id];
  const [series, setSeries] = useState(null);
  const [symbol, setSymbol] = useState("₹");
  const [content, setContent] = useState(null);
  const [proseOpen, setProseOpen] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setSeries(null);
    setContent(null);
    setProseOpen(false);
    setError(null);
    if (!item) return;

    Promise.all([
      fetch(DATA_BASE + item.file).then((r) => {
        if (!r.ok) throw new Error(`Could not load ${item.file}`);
        return r.json();
      }),
      fetch(DATA_BASE + "report_content.json").then((r) => (r.ok ? r.json() : null)),
    ])
      .then(([raw, allContent]) => {
        const found = extractSeries(raw);
        setSeries(found);
        setSymbol(raw.currency_symbol || "₹");
        setContent(allContent?.[id] ?? null);
      })
      .catch((e) => setError(e.message));
  }, [id, item]);

  if (!item) {
    return (
      <Panel>
        <p className="text-text">Unknown report id “{id}”.</p>
      </Panel>
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
      <div className="text-muted text-sm animate-pulse">Loading {item.file}…</div>
    );
  }

  return (
    <div className="space-y-6 max-w-[1400px]">
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

      <ProseSection content={content} open={proseOpen} onToggle={() => setProseOpen((v) => !v)} />
    </div>
  );
}
