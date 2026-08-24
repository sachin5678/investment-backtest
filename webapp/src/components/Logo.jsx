/** The one brand mark in the app: a rising three-bar signal glyph (an
 * abstracted candlestick/equity-curve tick, not a literal chart — reads
 * clearly at 20px) in the signal cyan, paired with a tracked-out wordmark.
 * Used once in the sidebar header and once in the Overview hero. */
export default function Logo({ size = 22, withWordmark = true, className = "" }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="3" y="13" width="4" height="8" rx="1" fill="var(--color-accent)" opacity="0.55" />
        <rect x="10" y="7" width="4" height="14" rx="1" fill="var(--color-accent)" opacity="0.8" />
        <rect x="17" y="2" width="4" height="19" rx="1" fill="var(--color-accent)" />
      </svg>
      {withWordmark && (
        <span className="font-extrabold text-[15px] tracking-[0.02em] text-text">
          SIGNAL<span className="text-accent">LAB</span>
        </span>
      )}
    </span>
  );
}
