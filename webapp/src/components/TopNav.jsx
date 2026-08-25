import Logo from "./Logo";
import { scrollToSection } from "../lib/scrollTo";
import AuthButton from "./AuthButton";

/** Transparent, full-bleed navigation for the landing page only — the
 * sidebar app-shell (Layout.jsx) has its own, separate top bar for report
 * pages. Sticky, blurred rather than fully transparent so it stays legible
 * once the hero's glow has scrolled out of view. */
export default function TopNav() {
  return (
    <header className="sticky top-0 z-30 bg-ground/75 backdrop-blur-md border-b border-border">
      <div className="max-w-[1400px] mx-auto px-6 sm:px-10 h-[68px] flex items-center justify-between gap-6">
        <Logo />
        <nav className="hidden md:flex items-center gap-8 text-[13.5px] font-medium text-muted">
          <a href="#strategies" onClick={(e) => scrollToSection(e, "strategies")} className="hover:text-text transition-colors">
            Strategies
          </a>
          <a href="#methodology" onClick={(e) => scrollToSection(e, "methodology")} className="hover:text-text transition-colors">
            Methodology
          </a>
        </nav>
        <div className="flex items-center gap-3 shrink-0">
          <AuthButton />
          <a
            href="#strategies"
            onClick={(e) => scrollToSection(e, "strategies")}
            className="hidden sm:inline-flex items-center text-[13px] font-semibold rounded-full bg-text text-ground px-4 py-2 shrink-0 transition-opacity hover:opacity-85 focus-visible:outline-2 focus-visible:outline-accent"
          >
            Browse strategies
          </a>
        </div>
      </div>
    </header>
  );
}
