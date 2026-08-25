import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import LoginModal from "./LoginModal";

/** Drop this anywhere in the app shell — the landing page's TopNav and the
 * report-page Layout's top bar both use it. Shows "Log in" when signed
 * out, "Logged in as sachin · Log out" when signed in. */
export default function AuthButton({ className = "" }) {
  const { isLoggedIn, logout } = useAuth();
  const [modalOpen, setModalOpen] = useState(false);

  if (isLoggedIn) {
    return (
      <div className={`flex items-center gap-2 shrink-0 ${className}`}>
        <span className="hidden sm:inline text-[12.5px] text-muted">Logged in as sachin</span>
        <button
          onClick={logout}
          className="inline-flex items-center text-[13px] font-medium text-muted border border-border rounded-full px-3.5 py-1.5 transition-colors hover:text-text hover:border-muted cursor-pointer focus-visible:outline-2 focus-visible:outline-accent"
        >
          Log out
        </button>
      </div>
    );
  }

  return (
    <>
      <button
        onClick={() => setModalOpen(true)}
        className={`inline-flex items-center text-[13px] font-semibold text-accent border border-accent/40 rounded-full px-3.5 py-1.5 shrink-0 transition-colors hover:bg-accent-dim cursor-pointer focus-visible:outline-2 focus-visible:outline-accent ${className}`}
      >
        Log in
      </button>
      {modalOpen && <LoginModal onClose={() => setModalOpen(false)} />}
    </>
  );
}
