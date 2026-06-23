import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "./supabaseTypes";

export function createSupabaseBrowserClient(): SupabaseClient<Database> | null {
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
  const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    return null;
  }

  return createClient<Database>(supabaseUrl, supabaseAnonKey);
}
