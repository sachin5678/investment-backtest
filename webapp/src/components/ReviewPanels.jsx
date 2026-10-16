import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Panel, { WhatThisShows } from "./Panel";
import MsPill from "./MsPill";
import HealthCard from "./HealthCard";
import RobustnessCard from "./RobustnessCard";
import TaxTable from "./TaxTable";
import RanksTable from "./RanksTable";
import { loadLab } from "../lib/mslab";
import { downloadCsv } from "../lib/csv";
import { money } from "../lib/format";

/** Health & robustness card for any report: prefers the report's own
 * engine-embedded health_check (exact, full-resolution — report 93), and
 * falls back to build_ms_lab.py's scored entry for the report's primary
 * series (chart-resolution approximation) for every other report. */
function LabHealthPanel({ raw, file }) {
  const [lab, setLab] = useState(null);
  useEffect(() => {
    let on = true;
    loadLab()
      .then((j) => on && setLab(j))
      .catch(() => {});
    return () => {
      on = false;
    };
  }, []);

  const embedded = raw.health_check || null;
  const entry = lab?.reports?.[file];
  const fallback = entry
    ? entry.series.find((s) => s.path === "after_costs") ||
      entry.series.find((s) => s.kind === "strategy") ||
      entry.series[0]
    : null;
  const health = embedded || fallback?.health || null;
  const robustness = raw.robustness || fallback?.robustness || null;
  if (!health) return null;

  return (
    <Panel>
      <h3 className="text-base font-bold text-text mb-1">Health &amp; robustness — the MomentumScore-style review</h3>
      <WhatThisShows>
        {embedded
          ? "The same 10 target ranges MomentumScore scores strategies on, computed by this report's own engine on full-resolution daily data and this trade log — score = share of ranges met."
          : "The same 10 target ranges MomentumScore scores strategies on, computed on this report's archived chart series (≤1500 points — close, not bit-exact) and its trade log when one exists."}
      </WhatThisShows>
      <HealthCard health={health} />
      {robustness && (
        <div className="mt-6">
          <RobustnessCard robustness={robustness} />
        </div>
      )}
    </Panel>
  );
}

function TaxPanel({ tax, symbol }) {
  if (!tax?.totals) return null;
  return (
    <Panel>
      <h3 className="text-base font-bold text-text mb-1">Capital-gains tax estimate — Indian rules</h3>
      <WhatThisShows>
        15%/10% (LTCG above ₹1,00,000) before 23 Jul 2024; 20%/12.5% (above ₹1,25,000) on/after; 4% cess; loss
        set-off with 8-year carry-forward; s.112A grandfathering via the 31-Jan-2025 FMV. An estimate over this
        report&rsquo;s own trade log — not tax advice.
      </WhatThisShows>
      <div className="flex gap-4 flex-wrap mb-4 text-[12.5px] text-muted-2">
        <span>
          Total tax <span className="font-mono text-text font-semibold">{money(tax.totals.total_tax, symbol, 0)}</span>
        </span>
        <span>
          on realized P&amp;L{" "}
          <span className="font-mono text-text">{money(tax.totals.total_realised_pnl, symbol, 0)}</span>
        </span>
        <span>
          effective{" "}
          <span className="font-mono text-text font-semibold">{tax.totals.tax_pct_of_realised_pnl}%</span>
        </span>
        {typeof tax.growth_after_tax_pct === "number" && typeof tax.growth_before_tax_pct === "number" && (
          <span>
            growth <span className="font-mono text-text">{tax.growth_before_tax_pct.toFixed(1)}%</span> a year before
            tax → <span className="font-mono text-text font-semibold">{tax.growth_after_tax_pct.toFixed(1)}%</span>{" "}
            after tax
          </span>
        )}
      </div>
      <TaxTable report={tax} symbol={symbol} />
      {tax.notes?.length > 0 && (
        <ul className="mt-3 space-y-1">
          {tax.notes.map((n) => (
            <li key={n} className="text-muted-2 text-[12px] list-disc ml-4">
              {n}
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

const TRIGGER_PILL = {
  regime_exit: "fail",
  regime_reentry: "pass",
  scheduled_rebalance: "neutral",
  initial_entry: "info",
};

function RebalancesPanel({ rebalances, symbol }) {
  const [showAll, setShowAll] = useState(false);
  if (!rebalances?.length) return null;
  const ordered = [...rebalances].reverse();
  const shown = showAll ? ordered : ordered.slice(0, 10);

  const exportCsv = () => {
    const rows = [];
    for (const e of rebalances) {
      for (const s of e.sells || [])
        rows.push({
          date: e.date,
          trigger: e.trigger,
          side: "sell",
          ticker: s.ticker,
          reason: s.reason || "",
          rank: s.rank_out ?? "",
          fit: s.fit_out ?? "",
          amount: s.proceeds ?? s.amount ?? "",
        });
      for (const b of e.buys || [])
        rows.push({
          date: e.date,
          trigger: e.trigger,
          side: "buy",
          ticker: b.ticker,
          reason: "",
          rank: b.rank_in ?? "",
          fit: b.fit_in ?? "",
          amount: b.amount ?? "",
        });
      for (const k of e.keeps || [])
        rows.push({
          date: e.date,
          trigger: e.trigger,
          side: "carry",
          ticker: k.ticker,
          reason: "still ranked",
          rank: k.rank ?? "",
          fit: k.fit ?? "",
          amount: "",
        });
    }
    downloadCsv("rebalances.csv", rows);
  };

  return (
    <Panel>
      <div className="flex items-center justify-between flex-wrap gap-2 mb-1">
        <h3 className="text-base font-bold text-text">Rebalance log — every review, and why</h3>
        <div className="flex items-center gap-2">
          <MsPill kind="neutral">{rebalances.length} reviews</MsPill>
          <button
            onClick={exportCsv}
            className="text-[11px] font-semibold text-muted hover:text-text transition-colors cursor-pointer"
            title="Download every action as CSV"
          >
            ⇩ CSV
          </button>
          <button
            onClick={() => setShowAll((v) => !v)}
            className="text-[11px] font-semibold text-muted hover:text-text transition-colors cursor-pointer"
          >
            {showAll ? "▲ latest 10" : `▼ show all ${rebalances.length}`}
          </button>
        </div>
      </div>
      <WhatThisShows>
        Each review the engine ran — scheduled (June/December), regime exits and re-entries — with the exact per-name
        action: which positions carried (still ranked), which fell out of the exit rank, and which names refilled the
        slots, at what rank and fit.
      </WhatThisShows>
      <div className="space-y-2.5">
        {shown.map((e) => (
          <div key={e.date + e.trigger} className="rounded-xl border border-border px-4 py-3">
            <div className="flex items-center gap-2.5 flex-wrap text-[12.5px]">
              <span className="font-mono text-muted-2">{e.date}</span>
              <MsPill kind={TRIGGER_PILL[e.trigger] || "neutral"}>{e.trigger.replace(/_/g, " ")}</MsPill>
              {e.value_after != null && (
                <span className="text-muted text-[12px]">
                  value after <span className="font-mono text-muted-2">{money(e.value_after, symbol, 0)}</span>
                </span>
              )}
              {e.cash_left > 0 && <MsPill kind="warn">{money(e.cash_left, symbol, 0)} left in cash</MsPill>}
            </div>
            <div className="mt-1.5 text-[12px] leading-relaxed space-y-0.5">
              {e.sells?.length > 0 && (
                <div>
                  <span className="text-negative font-semibold">Sold:</span>{" "}
                  <span className="text-muted-2">
                    {e.sells
                      .map((s) => `${s.ticker}${s.rank_out ? ` (rank ${s.rank_out})` : ""} — ${s.reason}`)
                      .join(" · ")}
                  </span>
                </div>
              )}
              {e.buys?.length > 0 && (
                <div>
                  <span className="text-positive font-semibold">Bought:</span>{" "}
                  <span className="text-muted-2">
                    {e.buys
                      .map((b) => `${b.ticker}${b.rank_in ? ` (rank ${b.rank_in}, fit ${b.fit_in}%)` : ""}`)
                      .join(" · ")}
                  </span>
                </div>
              )}
              {e.keeps?.length > 0 && (
                <div>
                  <span className="text-muted font-semibold">Carried:</span>{" "}
                  <span className="text-muted-2">
                    {e.keeps.map((k) => `${k.ticker} (rank ${k.rank})`).join(" · ")}
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function RanksPanel({ ranks }) {
  if (!ranks?.rows?.length) return null;
  return (
    <Panel>
      <div className="flex items-center gap-2.5 flex-wrap mb-1">
        <h3 className="text-base font-bold text-text">Latest ranking preview — what a review today would do</h3>
        {ranks.regime_on ? (
          <MsPill kind="pass">REGIME ON — stocks</MsPill>
        ) : (
          <MsPill kind="warn">
            REGIME OFF — gold hedge{ranks.regime_since ? ` since ${ranks.regime_since}` : ""}
          </MsPill>
        )}
      </div>
      <WhatThisShows>
        The full current ranking (top of the book plus everything held), recomputed at the latest close with the same
        formula and exit-rank rule the engine uses; Δ columns are vs the last review.{" "}
        <Link to="/ranks" className="text-accent hover:underline">
          Open the full ranking page →
        </Link>
      </WhatThisShows>
      <RanksTable ranks={ranks} limit={15} />
    </Panel>
  );
}

/** Everything the MomentumScore-style review run adds on top of the generic
 * report view (KPI table, charts, trade log): health + robustness, the
 * capital-gains estimate, the rebalance log and the latest rank preview.
 * Renders only the sections the report's data actually carries. */
export default function ReviewPanels({ raw, file, symbol = "₹" }) {
  if (!raw) return null;
  return (
    <>
      <LabHealthPanel raw={raw} file={file} />
      <TaxPanel tax={raw.tax_report} symbol={symbol} />
      <RebalancesPanel rebalances={raw.rebalances} symbol={symbol} />
      <RanksPanel ranks={raw.ranks} />
    </>
  );
}
