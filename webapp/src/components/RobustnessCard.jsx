import MsPill from "./MsPill";
import { pct } from "../lib/format";

function HalvesTable({ halves }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-[12.5px] border-collapse">
        <thead>
          <tr>
            {["Half", "Period", "Strategy CAGR", "NIFTY 50 CAGR", "Verdict"].map((h, i) => (
              <th
                key={h}
                className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                  i === 4 ? "text-right" : "text-left"
                }`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {halves.halves.map((h) => (
            <tr key={h.label} className="border-b border-border/60 last:border-0">
              <td className="px-3 py-1.5 text-left capitalize">{h.label} half</td>
              <td className="px-3 py-1.5 text-left font-mono text-muted-2">
                {h.start} → {h.end}
              </td>
              <td className="px-3 py-1.5 text-left font-mono text-text font-semibold">{pct(h.strategy_cagr_pct)}</td>
              <td className="px-3 py-1.5 text-left font-mono text-muted-2">{pct(h.benchmark_cagr_pct)}</td>
              <td className="px-3 py-1.5 text-right">
                {h.passed ? <MsPill kind="pass">BEATS</MsPill> : <MsPill kind="fail">LAGS</MsPill>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DateLuckTable({ dateLuck }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-[12.5px] border-collapse">
        <thead>
          <tr>
            {["Review calendar", "Period", "Strategy CAGR", "NIFTY 50 CAGR", "Verdict"].map((h, i) => (
              <th
                key={h}
                className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                  i === 4 ? "text-right" : "text-left"
                }`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dateLuck.variants.map((v) => (
            <tr key={v.label} className="border-b border-border/60 last:border-0">
              <td className="px-3 py-1.5 text-left">{v.label}</td>
              <td className="px-3 py-1.5 text-left font-mono text-muted-2">
                {v.start} → {v.end}
              </td>
              <td className="px-3 py-1.5 text-left font-mono text-text font-semibold">{pct(v.strategy_cagr_pct)}</td>
              <td className="px-3 py-1.5 text-left font-mono text-muted-2">{pct(v.benchmark_cagr_pct)}</td>
              <td className="px-3 py-1.5 text-right">
                {v.passed ? <MsPill kind="pass">BEATS</MsPill> : <MsPill kind="fail">LAGS</MsPill>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Both-halves and date-luck robustness — handles both the engine-embedded
 * block (report 93: halves + date_luck) and build_ms_lab.py's lighter
 * per-series block (halves only). */
export default function RobustnessCard({ robustness }) {
  if (!robustness) return null;
  const { halves, date_luck: dateLuck } = robustness;
  return (
    <div className="space-y-5">
      {halves && (
        <div>
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <h4 className="text-[13px] font-bold text-text">Both halves — sound, or one lucky stretch?</h4>
            {halves.passed_both ? (
              <MsPill kind="pass">PASS — beats NIFTY in both halves</MsPill>
            ) : halves.passed_any ? (
              <MsPill kind="warn">MIXED — only one half beats</MsPill>
            ) : (
              <MsPill kind="fail">FAIL — lags in both halves</MsPill>
            )}
          </div>
          <HalvesTable halves={halves} />
          <p className="text-muted-2 text-[12px] italic mt-2">
            Split at {halves.split_date} — the midpoint of the benchmark&rsquo;s own history, not a cherry-picked date.
          </p>
        </div>
      )}
      {dateLuck && (
        <div>
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <h4 className="text-[13px] font-bold text-text">Date luck — does the review calendar matter?</h4>
            {dateLuck.verdict === "pass" ? (
              <MsPill kind="pass">
                PASS — {dateLuck.n_pass}/{dateLuck.n_variants} calendars beat NIFTY
              </MsPill>
            ) : (
              <MsPill kind="fail">
                FAIL — only {dateLuck.n_pass}/{dateLuck.n_variants} calendars beat NIFTY
              </MsPill>
            )}
          </div>
          <DateLuckTable dateLuck={dateLuck} />
          <p className="text-muted-2 text-[12px] italic mt-2">
            Identical engine, universe and rule — only the day of the rebalance month moves. An edge that needs one
            calendar day usually isn&rsquo;t an edge.
          </p>
        </div>
      )}
    </div>
  );
}
