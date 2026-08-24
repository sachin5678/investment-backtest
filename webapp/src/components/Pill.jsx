const KIND_CLASSES = {
  positive: "bg-positive/15 text-positive border-positive/40",
  negative: "bg-negative/15 text-negative border-negative/40",
  assumption: "bg-assumption/15 text-assumption border-assumption/40",
  neutral: "bg-muted/15 text-muted border-muted/40",
};

const KIND_DOT = {
  positive: "●",
  negative: "●",
  assumption: "▲",
  neutral: "●",
};

export default function Pill({ children, kind = "assumption" }) {
  return (
    <span
      className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap border ${KIND_CLASSES[kind]}`}
    >
      <span aria-hidden="true">{KIND_DOT[kind]}</span>
      {children}
    </span>
  );
}
