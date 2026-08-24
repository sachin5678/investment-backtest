import { useEffect, useState } from "react";

const TYPE_SPEED = 55;
const DELETE_SPEED = 30;
const PAUSE_AT_FULL = 1800;
const PAUSE_AT_EMPTY = 300;

/** Cycles through `words`, typing each one out character by character,
 * pausing, then deleting it before typing the next — the same effect as
 * the reference site's hero. Respects prefers-reduced-motion by skipping
 * the animation entirely and just showing the first word, static. */
export default function Typewriter({ words, className = "" }) {
  const [index, setIndex] = useState(0);
  const [text, setText] = useState("");
  const [phase, setPhase] = useState("typing"); // typing | pausedFull | deleting | pausedEmpty
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    setReducedMotion(!!mq?.matches);
  }, []);

  useEffect(() => {
    if (reducedMotion) {
      setText(words[0] ?? "");
      return;
    }
    const current = words[index % words.length];
    let timer;

    if (phase === "typing") {
      if (text.length < current.length) {
        timer = setTimeout(() => setText(current.slice(0, text.length + 1)), TYPE_SPEED);
      } else {
        timer = setTimeout(() => setPhase("pausedFull"), PAUSE_AT_FULL);
      }
    } else if (phase === "pausedFull") {
      timer = setTimeout(() => setPhase("deleting"), 0);
    } else if (phase === "deleting") {
      if (text.length > 0) {
        timer = setTimeout(() => setText(text.slice(0, -1)), DELETE_SPEED);
      } else {
        timer = setTimeout(() => setPhase("pausedEmpty"), PAUSE_AT_EMPTY);
      }
    } else if (phase === "pausedEmpty") {
      timer = setTimeout(() => {
        setIndex((i) => (i + 1) % words.length);
        setPhase("typing");
      }, 0);
    }
    return () => clearTimeout(timer);
  }, [text, phase, index, words, reducedMotion]);

  return (
    <span className={className}>
      {text}
      <span className="inline-block w-[3px] sm:w-[5px] ml-1 -mb-1 h-[0.85em] bg-accent motion-safe:animate-pulse" aria-hidden="true" />
      <span className="sr-only">{words.join(", ")}</span>
    </span>
  );
}
