import { createClient as createSupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

/**
 * Creates a browser-side Supabase client for React client components.
 */
export function createClient() {
  if (!supabaseUrl || !supabaseAnonKey) {
    console.warn(
      "Warning: Supabase credentials missing (NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY)"
    );
  }
  return createSupabaseClient(supabaseUrl, supabaseAnonKey);
}

export const supabase = createClient();
