import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const service = process.env.SUPABASE_SERVICE_ROLE_KEY!;

// Anon-klient för klientkomponenter (läsning av publika tabeller)
export const supabase = createClient(url, anon);

// Service-role för serverfunktioner och statisk generering (kringgår RLS)
export const supabaseAdmin = createClient(url, service, {
  auth: { persistSession: false },
});
