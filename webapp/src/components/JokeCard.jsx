import { useEffect, useRef, useState } from "react";
import { JOKES } from "../data/jokes";

const ROTATE_MS = 10000;

function randomIndex(excluding) {
  if (JOKES.length <= 1) return 0;
  let i = excluding;
  while (i === excluding) i = Math.floor(Math.random() * JOKES.length);
  return i;
}

/** Fills the hero's otherwise-empty right-hand space with a rotating
 * trading joke — pure flavor, unrelated to the actual backtest numbers.
 * Picks a fresh random joke (never immediately repeating) every 10s. */
export default function JokeCard() {
  const [index, setIndex] = useState(() => Math.floor(Math.random() * JOKES.length));
  const indexRef = useRef(index);
  indexRef.current = index;

  useEffect(() => {
    const id = setInterval(() => {
      setIndex((current) => randomIndex(current));
    }, ROTATE_MS);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="hidden lg:block w-[300px] shrink-0 bg-panel border border-border rounded-2xl p-5">
      <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted mb-4">
        <span className="w-3 h-px bg-accent" />
        Trader's lounge
      </div>
      <p key={index} className="fade-in text-[14px] text-text leading-relaxed min-h-[95px]">
        “{JOKES[index]}”
      </p>
    </div>
  );
}
