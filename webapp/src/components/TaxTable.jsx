import { money } from "../lib/format";

function lossCell(v, symbol) {
  if (!v) return <span className="text-muted">—</span>;
  return <span className="text-negative font-mono">{money(-Math.abs(v), symbol, 0)}</span>;
}

/** Per-financial-year capital-gains table — shared by the Tax page and the
 * report page's tax panel. Works off a tax_report-shaped object (report
 * 93's embedded block or build_ms_lab.py's per-report version — same shape). */
export default function TaxTable({ report, symbol = "₹" }) {
  const years = report?.years || [];
  if (years.length === 0) return null;

  const sum = (k) => years.reduce((a, y) => a + (y[k] || 0), 0);

  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-[12.5px] border-collapse">
        <thead>
          <tr>
            {[
              "FY",
              "Trades",
              "STCG gains",
              "STCG losses",
              "LTCG gains",
              "LTCG losses",
              "Exemption",
              "Taxable",
              "Tax",
              "Cess",
              "Total tax",
              "Carry fwd",
            ].map((h, i) => (
              <th
                key={h}
                className={`sticky top-0 bg-panel-2 text-muted font-semibold px-3 py-2 text-[11px] uppercase tracking-wide border-b border-border ${
                  i === 0 ? "text-left" : "text-right"
                }`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {years.map((y) => {
            const tax = (y.tax_stcg || 0) + (y.tax_ltcg || 0);
            const taxable = (y.taxable_stcg || 0) + (y.taxable_ltcg || 0);
            const carry = (y.carry_out_stcl || 0) + (y.carry_out_ltcl || 0);
            return (
              <tr key={y.fy} className="border-b border-border/60">
                <td className="px-3 py-1.5 text-left font-mono text-muted-2 whitespace-nowrap">{y.fy}</td>
                <td className="px-3 py-1.5 text-right font-mono text-muted-2">{y.n_trades_closed}</td>
                <td className="px-3 py-1.5 text-right font-mono text-positive">
                  {y.stcg_gains ? money(y.stcg_gains, symbol, 0) : <span className="text-muted">—</span>}
                </td>
                <td className="px-3 py-1.5 text-right">{lossCell(y.stcg_losses, symbol)}</td>
                <td className="px-3 py-1.5 text-right font-mono text-positive">
                  {y.ltcg_gains ? money(y.ltcg_gains, symbol, 0) : <span className="text-muted">—</span>}
                </td>
                <td className="px-3 py-1.5 text-right">{lossCell(y.ltcg_losses, symbol)}</td>
                <td className="px-3 py-1.5 text-right font-mono text-muted-2">
                  {y.exemption_used ? money(y.exemption_used, symbol, 0) : <span className="text-muted">—</span>}
                </td>
                <td className="px-3 py-1.5 text-right font-mono text-text">
                  {taxable ? money(taxable, symbol, 0) : <span className="text-muted">—</span>}
                </td>
                <td
                  className="px-3 py-1.5 text-right font-mono text-muted-2"
                  title={`STCG ${money(y.tax_stcg || 0, symbol, 0)} · LTCG ${money(y.tax_ltcg || 0, symbol, 0)}`}
                >
                  {tax ? money(tax, symbol, 0) : <span className="text-muted">—</span>}
                </td>
                <td className="px-3 py-1.5 text-right font-mono text-muted-2">
                  {y.cess ? money(y.cess, symbol, 0) : <span className="text-muted">—</span>}
                </td>
                <td className="px-3 py-1.5 text-right font-mono text-text font-semibold">
                  {y.total_tax ? money(y.total_tax, symbol, 0) : <span className="text-muted">—</span>}
                </td>
                <td
                  className="px-3 py-1.5 text-right font-mono text-assumption"
                  title={`STCL carried ${money(y.carry_out_stcl || 0, symbol, 0)} · LTCL carried ${money(y.carry_out_ltcl || 0, symbol, 0)}`}
                >
                  {carry ? money(carry, symbol, 0) : <span className="text-muted">—</span>}
                </td>
              </tr>
            );
          })}
          <tr className="bg-panel-2/60">
            <td className="px-3 py-2 text-left font-semibold">Total</td>
            <td className="px-3 py-2 text-right font-mono">{sum("n_trades_closed")}</td>
            <td className="px-3 py-2 text-right font-mono text-positive">{money(sum("stcg_gains"), symbol, 0)}</td>
            <td className="px-3 py-2 text-right font-mono text-negative">{money(-sum("stcg_losses"), symbol, 0)}</td>
            <td className="px-3 py-2 text-right font-mono text-positive">{money(sum("ltcg_gains"), symbol, 0)}</td>
            <td className="px-3 py-2 text-right font-mono text-negative">{money(-sum("ltcg_losses"), symbol, 0)}</td>
            <td className="px-3 py-2 text-right font-mono">{money(sum("exemption_used"), symbol, 0)}</td>
            <td className="px-3 py-2 text-right font-mono">{money(sum("taxable_stcg") + sum("taxable_ltcg"), symbol, 0)}</td>
            <td className="px-3 py-2 text-right font-mono">{money(sum("tax_stcg") + sum("tax_ltcg"), symbol, 0)}</td>
            <td className="px-3 py-2 text-right font-mono">{money(sum("cess"), symbol, 0)}</td>
            <td className="px-3 py-2 text-right font-mono font-bold text-text">{money(sum("total_tax"), symbol, 0)}</td>
            <td className="px-3 py-2 text-right font-mono text-assumption">
              {money(sum("carry_out_stcl") + sum("carry_out_ltcl"), symbol, 0)}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
