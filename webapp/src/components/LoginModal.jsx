import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function LoginModal({ onClose }) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    const { error: err } = await login(username, password);
    setSubmitting(false);
    if (err) {
      setError(err);
      return;
    }
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="w-full max-w-[380px] bg-panel border border-border rounded-2xl p-6"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="login-title"
      >
        <h2 id="login-title" className="text-lg font-bold text-text mb-1">
          Log in
        </h2>
        <p className="text-[13px] text-muted mb-5 leading-relaxed">
          Unlocks every strategy from report 11 onward, plus the full logic, disclosures &amp; limitations write-up on every report.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="login-username" className="block text-[12px] font-semibold text-muted mb-1.5">
              Username
            </label>
            <input
              id="login-username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-ground text-text border border-border rounded-lg px-3 py-2 text-[14px] focus-visible:outline-2 focus-visible:outline-accent"
              autoFocus
            />
          </div>
          <div>
            <label htmlFor="login-password" className="block text-[12px] font-semibold text-muted mb-1.5">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-ground text-text border border-border rounded-lg px-3 py-2 text-[14px] focus-visible:outline-2 focus-visible:outline-accent"
            />
          </div>
          {error && <p className="text-[13px] text-negative">{error}</p>}
          <div className="flex items-center gap-3 pt-1">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 inline-flex items-center justify-center text-[13px] font-semibold rounded-full bg-text text-ground px-4 py-2.5 transition-opacity hover:opacity-85 disabled:opacity-50 cursor-pointer focus-visible:outline-2 focus-visible:outline-accent"
            >
              {submitting ? "Logging in…" : "Log in"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="text-[13px] font-medium text-muted hover:text-text transition-colors cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
