import { useEffect, useState } from "react";
import { ITEM_BY_ID } from "../data/reportsIndex";
import { fetchResults } from "../lib/datacache";
import Panel, { WhatThisShows } from "../components/Panel";
import MsPill from "../components/MsPill";
import RanksTable from "../components/RanksTable";

/** The MomentumScore-style ranking preview — report 93's review engine
 * recomputes the full ranking at the latest close and shows what a review
 * on this data would actually do under the exit-rank-52 rule. */
export default function Ranks() {
  const [raw, setRaw] = useState(null);
  const [error, setError] = useState(null);
  const item = ITEM_BY_ID["93"];

  useEffect(() => {
    if (!item) return;
    let on = true;
    fetchResults(item.file)
      .then((j) => on && setRaw(j))
      .catch((e) => on && setError(e.message));
    return () => {
      on = false;
    };
  }, [item]);

  const ranks = raw?.ranks || null;

  return (
    <div className="space-y-6 w-full">
      <Panel>
        <h3 className="text-base font-bold text-text mb-1">
          Ranking preview — report 93&rsquo;s review engine, as of the latest close
        </h3>
        <WhatThisShows>
          The full current ranking from the MomentumScore-style review engine: exit rank 52 (a held stock is sold only
          when it falls below rank 52 of the eligible universe), fit percentile against all eligible names, each
          row&rsquo;s Δ versus the last review, and the action a review on the latest close would take.
        </WhatThisShows>
        {error && <p className="text-negative text-[13px]">{error}</p>}
        {!raw && !error && <p className="text-muted text-sm animate-pulse">Loading the latest ranking…</p>}
        {raw && !ranks && (
          <p className="text-muted-2 text-[13px]">This report&rsquo;s data doesn&rsquo;t carry a ranks table.</p>
        )}
        {ranks && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 flex-wrap text-[12.5px]">
              <span className="text-muted-2">
                As of <span className="font-mono text-text">{ranks.as_of}</span>
              </span>
              <span className="text-muted-2">
                last review <span className="font-mono text-text">{ranks.last_review || "—"}</span>
              </span>
              <span className="text-muted-2">
                next scheduled <span className="font-mono text-text">{ranks.next_rebalance}</span>
              </span>
              {ranks.regime_on ? (
                <MsPill kind="pass">REGIME ON — stocks</MsPill>
              ) : (
                <MsPill kind="warn">
                  REGIME OFF — gold hedge{ranks.regime_since ? ` since ${ranks.regime_since}` : ""}
                </MsPill>
              )}
              <MsPill kind="neutral">sell below rank {ranks.exit_rank}</MsPill>
            </div>

            {ranks.regime_on ? (
              <div className="text-[13px] space-y-1">
                {ranks.preview.sells.length > 0 ? (
                  <div>
                    <span className="text-negative font-semibold">Sell (fell out of top {ranks.exit_rank}):</span>{" "}
                    <span className="font-mono text-muted-2">{ranks.preview.sells.join(", ")}</span>
                  </div>
                ) : (
                  <div className="text-muted-2">
                    <span className="text-positive font-semibold">No sells</span> — every held name still ranks inside
                    the top {ranks.exit_rank}.
                  </div>
                )}
                {ranks.preview.buys.length > 0 ? (
                  <div>
                    <span className="text-positive font-semibold">Buy (refill slots):</span>{" "}
                    <span className="font-mono text-muted-2">{ranks.preview.buys.join(", ")}</span>
                  </div>
                ) : (
                  <div className="text-muted-2">
                    <span className="font-semibold text-text">{ranks.preview.keeps} names carried</span> — no refill
                    needed.
                  </div>
                )}
              </div>
            ) : (
              <p className="text-assumption text-[13px]">
                No stock actions while the regime filter is off — the engine holds the gold hedge until NIFTY 50
                closes back above its 200-day EMA. The table below still shows where everything stands.
              </p>
            )}

            <RanksTable ranks={ranks} />
            <p className="text-muted-2 text-[12px] italic">{ranks.note}</p>
          </div>
        )}
      </Panel>
    </div>
  );
}
