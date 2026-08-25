import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Both are safe to expose in the browser bundle: the anon key can only do
// what the database's Row Level Security policies allow (see
// supabase/schema.sql) — for the gated tables here, that's "nothing
// unless logged in." Real access control lives in Postgres, not in this
// file.
export const supabase = url && anonKey ? createClient(url, anonKey) : null;

export const SUPABASE_CONFIGURED = Boolean(supabase);

// The login is a single fixed username, but Supabase Auth requires an
// email — this internal, never-emailed-to address is just how that one
// account is identified inside Supabase. See scripts/seed_supabase.py.
export const LOGIN_USERNAME = "sachin";
const LOGIN_EMAIL = "sachin@signal-lab.local";

export function usernameToEmail(username) {
  return username.trim().toLowerCase() === LOGIN_USERNAME ? LOGIN_EMAIL : null;
}
