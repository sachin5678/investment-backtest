import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { COLORS, seriesColor } from "../lib/colors";
import { mergeSeriesForChart, drawdownRows, downsampleRows } from "../lib/viewmodel";

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
          {p.name}: {p.value?.toFixed(1)}%
        </div>
      ))}
    </div>
  );
}

/** Underwater / drawdown chart — % below each series' own running peak,
 * computed on the merged (pre-downsample) rows for accuracy, then
 * downsampled only for display. Never positive by construction, so the
 * y-axis max is pinned at 0 rather than "auto". */
export default function DrawdownChart({ series, height = 260 }) {
  const merged = mergeSeriesForChart(series, { rebase: true });
  const labels = series.map((s) => s.label);
  const dd = drawdownRows(merged, labels);
  const rows = downsampleRows(dd, 300);

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <AreaChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid stroke={COLORS.border} strokeDasharray="2 3" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke={COLORS.muted}
            tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
            minTickGap={40}
          />
          <YAxis
            domain={["auto", 0]}
            stroke={COLORS.muted}
            tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
            tickFormatter={(v) => `${v.toFixed(0)}%`}
            width={50}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: COLORS.text }} />
          {labels.map((label, i) => (
            <Area
              key={label}
              type="monotone"
              dataKey={label}
              name={label}
              stroke={seriesColor(i)}
              fill={seriesColor(i)}
              fillOpacity={0.12}
              strokeWidth={1.6}
              strokeDasharray={i % 2 === 1 ? "6 4" : undefined}
              dot={false}
              isAnimationActive={false}
              connectNulls
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
