import { useNavigate, useParams } from "react-router-dom";
import { GROUPS, ALL_ITEMS } from "../data/reportsIndex";
import Icon from "./Icon";
import Logo from "./Logo";

export default function Sidebar({ open, onClose }) {
  const navigate = useNavigate();
  const { id: activeId } = useParams();

  function go(id) {
    navigate(`/report/${id}`);
    onClose?.();
  }

  return (
    <aside
      className={`fixed md:static inset-y-0 left-0 z-40 w-[320px] bg-panel border-r border-border flex flex-col overflow-y-auto transition-transform duration-200
        ${open ? "translate-x-0" : "-translate-x-full"} md:translate-x-0`}
    >
      <div className="px-5 pt-6 pb-4 border-b border-border">
        <button
          onClick={() => {
            navigate("/");
            onClose?.();
          }}
          className="cursor-pointer focus-visible:outline-2 focus-visible:outline-accent rounded-md"
          aria-label="Go to overview"
        >
          <Logo />
        </button>
        <p className="text-xs text-muted mt-2 leading-snug">
          {ALL_ITEMS.length} backtested strategies, live-tested against real market data
        </p>
      </div>

      <div className="px-5 py-3 border-b border-border">
        <label htmlFor="jumpSelect" className="block text-[11px] font-semibold uppercase tracking-wide text-muted mb-1.5">
          Jump to a report
        </label>
        <select
          id="jumpSelect"
          value={activeId ?? ""}
          onChange={(e) => go(e.target.value)}
          className="w-full bg-ground text-text border border-border rounded-lg px-3 py-2 text-[13px] cursor-pointer focus-visible:outline-2 focus-visible:outline-accent"
        >
          {GROUPS.map((g) => (
            <optgroup key={g.label} label={g.label}>
              {g.items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.id} — {item.title}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      {GROUPS.map((g) => (
        <div key={g.label} className="px-2.5 pt-3.5 pb-1">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-muted px-2.5 pb-2">{g.label}</div>
          {g.items.map((item) => {
            const active = item.id === activeId;
            return (
              <button
                key={item.id}
                onClick={() => go(item.id)}
                className={`w-full flex items-center gap-2.5 text-left px-2.5 py-2.5 rounded-[10px] mb-0.5 border-l-2 cursor-pointer transition-colors
                  ${active ? "bg-accent-dim border-accent text-text" : "border-transparent text-muted hover:bg-white/[0.03] hover:text-text"}
                  focus-visible:outline-2 focus-visible:outline-accent`}
              >
                <Icon path={item.icon} className={`w-[18px] h-[18px] shrink-0 ${active ? "text-accent" : "text-muted"}`} />
                <span className="flex-1 min-w-0">
                  <span className="block text-[13px] font-semibold leading-tight">{item.title}</span>
                  <span className="block text-[11px] text-muted leading-tight truncate">{item.subtitle}</span>
                </span>
                <span className="text-[11px] text-muted font-mono shrink-0">{item.id}</span>
              </button>
            );
          })}
        </div>
      ))}
    </aside>
  );
}
