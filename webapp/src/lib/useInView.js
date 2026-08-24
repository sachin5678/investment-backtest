import { useEffect, useRef, useState } from "react";

/** Reports whether an element has entered the viewport, once — used to
 * drive scroll-reveal animations. Unobserves after the first intersection
 * (matches ui-ux-pro-max's scroll-reveal guidance: reveal-once, don't
 * re-trigger on scroll-direction changes) and never marks anything "not
 * yet visible" for people with prefers-reduced-motion set. */
export function useInView(options = {}) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
      setInView(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.unobserve(el);
        }
      },
      { threshold: 0.1, rootMargin: "0px 0px -10% 0px", ...options }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return [ref, inView];
}
