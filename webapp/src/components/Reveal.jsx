import { useInView } from "../lib/useInView";

/** Fades + lifts its children into view the first time they scroll into
 * the viewport — subtle by design (12px of travel, ~380ms), per
 * ui-ux-pro-max's scroll-reveal guidance. `delay` (ms) staggers a group of
 * siblings without needing a stagger library. */
export default function Reveal({ children, delay = 0, className = "" }) {
  const [ref, inView] = useInView();
  return (
    <div
      ref={ref}
      className={`transition-[opacity,transform] duration-[420ms] ease-out ${
        inView ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3"
      } ${className}`}
      style={{ transitionDelay: inView ? `${delay}ms` : "0ms" }}
    >
      {children}
    </div>
  );
}
