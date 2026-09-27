import { createContext, useContext, useEffect, useState } from "react";

// Pure client-side gate — no backend. This is a soft gate for casual
// browsing, not real security: anyone who opens dev tools can read
// USERNAME/PASSWORD below, or just flip the localStorage flag directly.
// It was originally built this way, then moved to a Supabase-backed
// version for genuine access control, then moved back here because a
// paused free-tier database and per-platform build env vars (GitHub
// Pages vs. Vercel) were real deployment friction for a personal
// portfolio site where that tradeoff isn't worth it. If real content
// secrecy is ever needed again, the report gating (see reportsIndex.js's
// isPremiumReport) will also need report data to live somewhere other
// than a static public file, since anyone can already fetch
// webapp/public/data/*.json directly regardless of what this component
// does.
const STORAGE_KEY = "signal_lab_auth";
const USERNAME = "sachin";
const PASSWORD = "121101";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    try {
      setIsLoggedIn(localStorage.getItem(STORAGE_KEY) === "true");
    } catch {
      // private window / blocked storage — just stay logged out
    }
  }, []);

  function login(username, password) {
    const ok = username.trim().toLowerCase() === USERNAME && password === PASSWORD;
    if (!ok) {
      return { error: "Incorrect username or password." };
    }
    try {
      localStorage.setItem(STORAGE_KEY, "true");
    } catch {
      // storage blocked — login still works for this tab/session via state
    }
    setIsLoggedIn(true);
    return { error: null };
  }

  function logout() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setIsLoggedIn(false);
  }

  return <AuthContext.Provider value={{ isLoggedIn, loading: false, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an AuthProvider");
  return ctx;
}
