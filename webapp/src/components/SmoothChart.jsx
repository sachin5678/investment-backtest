import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { COLORS, seriesColor } from "../lib/colors";
import { mergeSeriesForChart, downsampleRows } from "../lib/viewmodel";

function formatDate(d) {
  return d ? d.slice(0, 7) : "";
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-panel-2 border border-border rounded-lg px-3 py-2 text-[12px] shadow-lg">
      <div className="text-muted mb-1 font-mono">{label}</div>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2" style={{ color: p.color }}>
          <span className="inline-block w-2 h-2 rounded-full" style={{ background: p.color }} />
          {p.name}: {p.value?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        </div>
      ))}
    </div>
  );
}

/** A multi-series "growth of 100" style line chart — smooth (monotone) curve
 * through a manageable number of real, downsampled points, zero-based axis
 * unless told otherwise. */
export default function SmoothChart({ series, height = 380, rebase = true, valuePrefix = "" }) {
  const merged = mergeSeriesForChart(series, { rebase });
  const rows = downsampleRows(merged, 300);
  const labels = series.map((s) => s.label);

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid stroke={COLORS.border} strokeDasharray="2 3" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke={COLORS.muted}
            tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
            minTickGap={40}
          />
          <YAxis
            domain={[0, "auto"]}
            stroke={COLORS.muted}
            tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
            tickFormatter={(v) => `${valuePrefix}${v.toLocaleString()}`}
            width={70}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: COLORS.text }} />
          {labels.map((label, i) => (
            <Line
              key={label}
              type="monotone"
              dataKey={label}
              name={label}
              stroke={seriesColor(i)}
              strokeWidth={2}
              strokeDasharray={i % 2 === 1 ? "6 4" : undefined}
              dot={false}
              isAnimationActive={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
