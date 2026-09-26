import { createClient as createSupabaseClient } from "@supabase/supabase-js";

/**
 * Creates a server-side Supabase client with optional service role privilege.
 */
export function createServerClient(useServiceRole: boolean = false) {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || "";
  const key = useServiceRole
    ? process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""
    : process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY || "";

  if (!supabaseUrl || !key) {
    console.warn("Warning: Supabase credentials missing for server client");
  }

  return createSupabaseClient(supabaseUrl, key, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });
}
