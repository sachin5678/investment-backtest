const KIND_CLASS = {
  pass: "bg-positive/15 text-positive border-positive/40",
  fail: "bg-negative/15 text-negative border-negative/40",
  warn: "bg-assumption/15 text-assumption border-assumption/40",
  info: "bg-accent/15 text-accent border-accent/40",
  neutral: "bg-muted/15 text-muted border-muted/40",
};

/** Compact status pill for the MomentumScore-style review surfaces (health
 * checks, robustness verdicts, rank actions) — same visual language as
 * components/Pill.jsx, extended with pass/fail tones. */
export default function MsPill({ kind = "neutral", children, className = "" }) {
  return (
    <span
      className={`inline-flex items-center text-[10.5px] font-semibold px-1.5 py-0.5 rounded border whitespace-nowrap ${
        KIND_CLASS[kind] || KIND_CLASS.neutral
      } ${className}`}
    >
      {children}
    </span>
  );
}
