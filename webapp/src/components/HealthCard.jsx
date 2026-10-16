import MsPill from "./MsPill";

function scoreTone(score) {
  if (score >= 70) return "text-positive";
  if (score >= 50) return "text-assumption";
  return "text-negative";
}

/** The 10-check scorecard, rendered from a health object shaped like
 * ms_port.health.health_check()'s output (embedded in report 93's own
 * results file) or build_ms_lab.py's lighter per-series version. */
export default function HealthCard({ health, footnote }) {
  if (!health) return null;
  const checks = health.checks || [];
  const noTrades = health.has_trades === false;
  return (
    <div>
      <div className="flex items-start gap-4 flex-wrap mb-4">
        <div className={`text-[42px] leading-none font-extrabold font-mono ${scoreTone(health.score)}`}>
          {health.score}
          <span className="text-lg text-muted font-semibold"> / 100</span>
        </div>
        <p className="text-[12.5px] text-muted-2 leading-snug max-w-[560px]">
          Share of MomentumScore&rsquo;s 10 target ranges met — {health.checks_met} of {health.checks_available} evaluated
          checks pass
          {noTrades && " (this series carries no trade log, so the 5 trade-based checks are scored met/available out of the curve checks only)"}
          .
        </p>
      </div>
      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-[12.5px] border-collapse">
          <thead>
            <tr>
              {["Check", "Target", "This strategy", "Verdict"].map((h, i) => (
                <th
                  key={h}
                  className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                    i === 3 ? "text-right" : "text-left"
                  }`}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {checks.map((c) => (
              <tr key={c.id} className="border-b border-border/60 last:border-0">
                <td className="px-3 py-1.5 text-left">{c.label}</td>
                <td className="px-3 py-1.5 text-left text-muted font-mono">{c.target_text}</td>
                <td className="px-3 py-1.5 text-left font-mono text-muted-2">{c.value_text ?? "—"}</td>
                <td className="px-3 py-1.5 text-right">
                  {c.passed === null || c.passed === undefined ? (
                    <MsPill kind="neutral">n/a</MsPill>
                  ) : c.passed ? (
                    <MsPill kind="pass">PASS</MsPill>
                  ) : (
                    <MsPill kind="fail">MISS</MsPill>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {(footnote || health.note) && (
        <p className="text-muted-2 text-[12px] italic mt-2.5">{footnote || health.note}</p>
      )}
    </div>
  );
}
