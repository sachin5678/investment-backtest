import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { GROUPS, ALL_ITEMS, isPremiumReport } from "../data/reportsIndex";
import { useAuth } from "../context/AuthContext";
import { extractSeries } from "../lib/viewmodel";
import { pct } from "../lib/format";
import Icon from "../components/Icon";
import Logo from "../components/Logo";
import TopNav from "../components/TopNav";
import Sparkline from "../components/Sparkline";
import Typewriter from "../components/Typewriter";
import JokeCard from "../components/JokeCard";
import Reveal from "../components/Reveal";
import { scrollToSection } from "../lib/scrollTo";
import { colorForCategory } from "../lib/categoryColors";

// each word completes "Does the edge survive ___?" — kept to single,
// similar-length words on purpose: a multi-word phrase can push the
// headline from 2 lines to 3 mid-type, jerking everything below it down
// and back up as it types/deletes. One short word never does that.
const SURVIVAL_TESTS = ["crashes?", "drawdowns?", "decades?", "scrutiny?", "Trump?"];

const DATA_BASE = "./data/";

const METHOD_STEPS = [
  {
    icon: "M4 19h16 M8 15l3-4 3 3 4-6",
    heading: "Pick a rule, not a hunch",
    body: "Every strategy here starts as a plain-English rule — a breakout threshold, a rebalance date, a drawdown trigger — written down before a single line of backtest code exists.",
  },
  {
    icon: "M12 2v20 M2 12h20 M7 7l10 10 M17 7l-10 10",
    heading: "Run it on real daily prices",
    body: "No simulated returns, no smoothed curves. Every equity curve on this site is built from real daily closing prices, run through a hand-written event loop.",
  },
  {
    icon: "M9 11l3 3 8-8 M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9",
    heading: "Read the honest result",
    body: "Every assumption is disclosed, every limitation is listed, and a weak result is reported as a weak result — several strategies here underperform doing nothing at all, on purpose.",
  },
];

function downsampleCurve(curve, maxPoints = 36) {
  if (!curve || curve.length <= maxPoints) return curve ?? [];
  const step = (curve.length - 1) / (maxPoints - 1);
  const out = [];
  for (let i = 0; i < maxPoints; i += 1) out.push(curve[Math.round(i * step)]);
  return out;
}

export default function Overview() {
  const [cards, setCards] = useState(null); // null = loading
  const [activeGroup, setActiveGroup] = useState("All");

  useEffect(() => {
    let cancelled = false;
    Promise.all(
      ALL_ITEMS.map((item) =>
        fetch(DATA_BASE + item.file)
          .then((r) => (r.ok ? r.json() : null))
          .then((raw) => ({ item, raw }))
          .catch(() => ({ item, raw: null }))
      )
    ).then((results) => {
      if (cancelled) return;
      const built = results.map(({ item, raw }) => {
        if (!raw) return { item, headline: null, currency: null };
        const series = extractSeries(raw);
        const headline = series[0] ?? null;
        return { item, headline, currency: raw.currency_symbol ?? "₹" };
      });
      setCards(built);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const groupOf = useMemo(() => {
    const map = {};
    GROUPS.forEach((g) => g.items.forEach((it) => (map[it.id] = g.label)));
    return map;
  }, []);

  const groupLabels = ["All", ...GROUPS.map((g) => g.label)];
  const visible = cards?.filter((c) => activeGroup === "All" || groupOf[c.item.id] === activeGroup) ?? [];

  const stats = useMemo(() => {
    if (!cards) return null;
    const withHeadline = cards.filter((c) => c.headline);
    const bestCagr = Math.max(...withHeadline.map((c) => c.headline.growthPct ?? -Infinity));
    const currencies = new Set(cards.map((c) => c.currency).filter(Boolean));
    const allDates = withHeadline.flatMap((c) => c.headline.curve.map((p) => p[0]));
    const years =
      allDates.length > 0
        ? (new Date(Math.max(...allDates.map((d) => new Date(d)))) - new Date(Math.min(...allDates.map((d) => new Date(d))))) /
          (365.25 * 24 * 3600 * 1000)
        : 0;
    return { count: ALL_ITEMS.length, bestCagr, markets: currencies.size, years: Math.round(years) };
  }, [cards]);

  return (
    <div className="min-h-full">
      <TopNav />

      {/* ---------- Hero ---------- */}
      <section className="relative overflow-hidden">
        <div className="signal-glow" />
        <div className="relative z-10 max-w-[1400px] mx-auto px-6 sm:px-10 pt-20 pb-16 sm:pt-28 sm:pb-24">
          <div className="flex items-start justify-between gap-12">
            <div className="min-w-0">
              <div className="inline-flex items-center gap-2 text-[12px] font-semibold uppercase tracking-[0.08em] text-accent border border-accent/30 rounded-full px-3 py-1 mb-8">
                <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                {ALL_ITEMS.length} strategies · updated {new Date().toLocaleDateString(undefined, { month: "short", year: "numeric" })}
              </div>
              <h1 className="font-extrabold leading-[0.98] tracking-tight text-text max-w-4xl text-[clamp(2.5rem,7vw,6rem)] min-h-[2.1em]">
                Does the edge survive <Typewriter words={SURVIVAL_TESTS} className="text-accent" />
              </h1>
              <p className="text-muted text-[16px] sm:text-[18px] mt-6 max-w-xl leading-relaxed">
                Momentum, quality, sector rotation, SIP timing, drawdown triggers — every trading idea in this lab, run as an honest,
                hand-built backtest against real market history. No result is dressed up.
              </p>
              <div className="flex items-center gap-4 mt-9">
                <a
                  href="#strategies"
                  onClick={(e) => scrollToSection(e, "strategies")}
                  className="inline-flex items-center text-[14px] font-semibold rounded-full bg-text text-ground px-5 py-3 transition-opacity hover:opacity-85 focus-visible:outline-2 focus-visible:outline-accent"
                >
                  Browse all strategies
                </a>
                <a
                  href="#methodology"
                  onClick={(e) => scrollToSection(e, "methodology")}
                  className="inline-flex items-center gap-1.5 text-[14px] font-medium text-accent border border-accent/40 rounded-full px-5 py-3 transition-colors hover:bg-accent-dim focus-visible:outline-2 focus-visible:outline-accent"
                >
                  How this works →
                </a>
              </div>
            </div>
            <JokeCard />
          </div>
        </div>
      </section>

      {/* ---------- Stat strip ---------- */}
      <section className="border-t border-border">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-10 py-14 sm:py-20">
          <Reveal>
            <Eyebrow>The numbers</Eyebrow>
          </Reveal>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 sm:gap-6 mt-6">
            <Reveal delay={0}>
              <StatBlock label="Strategies tested" value={stats ? stats.count : "—"} />
            </Reveal>
            <Reveal delay={60}>
              <StatBlock label="Best CAGR found" value={stats ? pct(stats.bestCagr, 1) : "—"} kind="positive" />
            </Reveal>
            <Reveal delay={120}>
              <StatBlock label="Markets covered" value={stats ? stats.markets : "—"} />
            </Reveal>
            <Reveal delay={180}>
              <StatBlock label="Longest backtest" value={stats ? `${stats.years}y` : "—"} />
            </Reveal>
          </div>
        </div>
      </section>

      {/* ---------- Trust / data-source strip ---------- */}
      <section className="border-t border-border bg-panel/40">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-10 py-10 sm:py-12">
          <Reveal>
            <p className="text-[11px] uppercase tracking-[0.1em] text-muted mb-5 text-center sm:text-left">
              Built on real, unadjusted daily prices from
            </p>
            <div className="flex items-center justify-center sm:justify-start gap-x-10 gap-y-3 flex-wrap opacity-60">
              {["NSE India", "NASDAQ-100", "S&P 500", "NIFTY Midcap 150", "NIFTY Smallcap 250"].map((name) => (
                <span key={name} className="text-[15px] font-semibold text-muted whitespace-nowrap">
                  {name}
                </span>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ---------- Methodology ---------- */}
      <section id="methodology" className="border-t border-border">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-10 py-16 sm:py-24">
          <Reveal>
            <Eyebrow>How this works</Eyebrow>
            <h2 className="text-[26px] sm:text-[34px] font-bold text-text mt-3 max-w-2xl leading-tight">
              Three rules this lab never breaks.
            </h2>
          </Reveal>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 sm:gap-10 mt-12">
            {METHOD_STEPS.map((s, i) => (
              <Reveal key={s.heading} delay={i * 70}>
                <Icon path={s.icon} className="w-11 h-11 text-accent mb-5" />
                <h3 className="text-[17px] font-bold text-text mb-2">{s.heading}</h3>
                <p className="text-[13.5px] text-muted leading-relaxed">{s.body}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Strategy grid ---------- */}
      <section id="strategies" className="border-t border-border">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-10 py-16 sm:py-24">
          <Reveal>
            <Eyebrow>All strategies</Eyebrow>
            <h2 className="text-[26px] sm:text-[34px] font-bold text-text mt-3 mb-8 leading-tight">Pick one to see the full breakdown.</h2>
          </Reveal>

          <div className="flex items-center gap-2 flex-wrap mb-8">
            {groupLabels.map((label) => {
              const active = label === activeGroup;
              return (
                <button
                  key={label}
                  onClick={() => setActiveGroup(label)}
                  className={`text-[13px] font-medium rounded-full px-4 py-1.5 border cursor-pointer transition-colors whitespace-nowrap
                    ${active ? "bg-text text-ground border-text" : "bg-transparent text-muted border-border hover:text-text hover:border-muted"}
                    focus-visible:outline-2 focus-visible:outline-accent`}
                >
                  {label}
                </button>
              );
            })}
          </div>

          {!cards ? (
            <div className="text-muted text-sm animate-pulse py-10">Loading all {ALL_ITEMS.length} strategies…</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {visible.map(({ item, headline, currency }, i) => (
                <Reveal key={item.id} delay={(i % 3) * 60}>
                  <StrategyCard item={item} headline={headline} currency={currency} category={groupOf[item.id]} />
                </Reveal>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ---------- Footer ---------- */}
      <footer className="border-t border-border">
        <div className="max-w-[1400px] mx-auto px-6 sm:px-10 py-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <Logo size={18} />
          <p className="text-[12.5px] text-muted max-w-md leading-relaxed">
            A personal research project, not investment advice. Every figure is a backtest on historical data — past performance doesn't
            guarantee future results.
          </p>
        </div>
      </footer>
    </div>
  );
}

function Eyebrow({ children }) {
  return (
    <div className="flex items-center gap-2 text-[11.5px] font-semibold uppercase tracking-[0.1em] text-accent">
      <span className="w-3 h-px bg-accent" />
      {children}
    </div>
  );
}

function StatBlock({ label, value, kind = "neutral" }) {
  const color = kind === "positive" ? "text-positive" : "text-text";
  return (
    <div>
      <div className={`text-[clamp(1.75rem,4vw,2.75rem)] font-bold tracking-tight ${color} mono`}>{value}</div>
      <div className="text-[12.5px] text-muted mt-1">{label}</div>
    </div>
  );
}

const ICON_LOCK = "M6 11h12v9h-12z M9 11V7a3 3 0 0 1 6 0v4";

function StrategyCard({ item, headline, currency, category }) {
  const { isLoggedIn } = useAuth();
  const locked = isPremiumReport(item.id) && !isLoggedIn;
  const positive = (headline?.growthPct ?? headline?.netReturnPct ?? 0) >= 0;
  const sparkPoints = headline ? downsampleCurve(headline.curve) : null;
  const color = colorForCategory(category);

  return (
    <Link
      to={`/report/${item.id}`}
      className="group block bg-panel border border-border rounded-2xl p-5 transition-[transform,border-color,box-shadow] duration-300 ease-out hover:-translate-y-1 hover:scale-[1.015] hover:border-transparent focus-visible:outline-2 focus-visible:outline-accent"
      onMouseEnter={(e) => (e.currentTarget.style.boxShadow = `0 12px 32px -8px ${color}40, 0 0 0 1px ${color}66`)}
      onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
    >
      <div className="flex items-start justify-between gap-3 mb-4">
        <div
          className="w-11 h-11 rounded-full flex items-center justify-center shrink-0 transition-transform duration-300 group-hover:scale-110"
          style={{ background: `radial-gradient(circle, ${color}2e, transparent 75%)` }}
        >
          <Icon path={item.icon} className="w-[19px] h-[19px]" style={{ color }} />
        </div>
        <span className="text-[11px] text-muted font-mono shrink-0 pt-1">{item.id}</span>
      </div>

      <div className="text-[11px] font-semibold uppercase tracking-wide mb-1.5" style={{ color }}>
        {category}
      </div>
      <h3 className="text-[15px] font-semibold text-text leading-snug mb-1">{item.title}</h3>
      <p className="text-[12.5px] text-muted leading-snug mb-4 line-clamp-2">{item.subtitle}</p>

      {headline ? (
        <>
          <div className="flex items-end justify-between gap-3 mb-2">
            <div>
              <div className="text-[11px] text-muted uppercase tracking-wide mb-0.5">{headline.growthLabel ?? "CAGR"}</div>
              <div className={`text-[22px] font-bold mono ${positive ? "text-positive" : "text-negative"}`}>
                {pct(headline.growthPct ?? headline.netReturnPct, 1)}
              </div>
            </div>
            <div className="text-right">
              <div className="text-[11px] text-muted uppercase tracking-wide mb-0.5">Max drawdown</div>
              <div className="text-[13px] font-mono text-negative">{pct(headline.maxDrawdownPct, 1, false)}</div>
            </div>
          </div>
          <Sparkline points={sparkPoints} positive={positive} />
        </>
      ) : locked ? (
        <div className="flex items-center gap-2 text-[12px] text-assumption py-4">
          <Icon path={ICON_LOCK} className="w-[14px] h-[14px] shrink-0" />
          Log in to see performance
        </div>
      ) : (
        <div className="text-[12px] text-muted italic py-4">Data unavailable</div>
      )}
    </Link>
  );
}
