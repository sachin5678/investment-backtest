/** A minimal inline equity-curve preview for a strategy card — no axes, no
 * gridlines, no tooltip, just the shape of the line. Colored by the
 * strategy's own polarity (green if it ended up, red if it ended down),
 * keeping the financial pos/neg convention even at this small a scale. */
export default function Sparkline({ points, positive = true, width = 240, height = 48 }) {
  if (!points || points.length < 2) return null;
  const vals = points.map((p) => p[1]);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const span = max - min || 1;
  const n = points.length;

  const coords = points.map((p, i) => {
    const x = (i / (n - 1)) * width;
    const y = height - ((p[1] - min) / span) * (height - 4) - 2;
    return [x, y];
  });
  const d = coords.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const areaD = `${d} L${width},${height} L0,${height} Z`;
  const color = positive ? "var(--color-positive)" : "var(--color-negative)";

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} preserveAspectRatio="none" aria-hidden="true">
      <path d={areaD} fill={color} opacity="0.12" />
      <path d={d} fill="none" stroke={color} strokeWidth="1.75" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
