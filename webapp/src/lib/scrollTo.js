/** In-page "jump to section" links can't use plain <a href="#id"> in this
 * app: HashRouter owns the entire URL hash as its routing namespace, so a
 * raw anchor click rewrites the hash to "#id" (no leading slash), which
 * matches no route and renders a blank page instead of scrolling. This
 * intercepts the click and scrolls manually, and never touches the hash.
 *
 * The actual scroll is a hand-rolled rAF animation rather than
 * `scrollIntoView({behavior:"smooth"})` — the native smooth option turned
 * out to be a no-op in at least one automated Chrome test harness (likely
 * disabled there for deterministic testing), and there's no reason to bet
 * a real user's experience on a browser feature that can silently do
 * nothing with no error and no fallback. This version always works: it's
 * plain scrollTo() calls under the hood. */
export function scrollToSection(e, id) {
  e.preventDefault();
  const el = document.getElementById(id);
  if (!el) return;

  const prefersReducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const target = el.getBoundingClientRect().top + window.scrollY;

  if (prefersReducedMotion) {
    window.scrollTo(0, target);
    return;
  }

  const start = window.scrollY;
  const distance = target - start;
  const duration = 500;
  let startTime = null;

  function easeInOutQuad(t) {
    return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  }

  function step(now) {
    if (startTime === null) startTime = now;
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    window.scrollTo(0, start + distance * easeInOutQuad(progress));
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
