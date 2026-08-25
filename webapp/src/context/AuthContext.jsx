import { createContext, useContext, useEffect, useState } from "react";
import { supabase, SUPABASE_CONFIGURED, usernameToEmail } from "../lib/supabaseClient";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(SUPABASE_CONFIGURED);

  useEffect(() => {
    if (!SUPABASE_CONFIGURED) return;
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  async function login(username, password) {
    if (!SUPABASE_CONFIGURED) {
      return { error: "Login isn't configured yet — this deployment has no Supabase project connected." };
    }
    const email = usernameToEmail(username);
    if (!email) {
      return { error: "Unknown username." };
    }
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      return { error: "Incorrect username or password." };
    }
    return { error: null };
  }

  async function logout() {
    if (!SUPABASE_CONFIGURED) return;
    await supabase.auth.signOut();
  }

  const value = {
    isLoggedIn: Boolean(session),
    loading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an AuthProvider");
  return ctx;
}
