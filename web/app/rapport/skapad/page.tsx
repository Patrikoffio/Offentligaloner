// Retur-URL efter Stripe Checkout (SNABBVÄG, inte enda leveransväg).
// Finns en betald purchases-rad för session_id → visa token-länk direkt.
// Annars (Klarna async ej bekräftad) → poll + "mejlas när betalningen bekräftats".
import type { Metadata } from "next";
import { supabaseAdmin } from "@/lib/supabase";
import Poller from "./Poller";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Tack för ditt köp",
  robots: { index: false, follow: false },
};

export default async function SkapadSida({
  searchParams,
}: {
  searchParams: Promise<{ session_id?: string }>;
}) {
  const { session_id: sessionId } = await searchParams;

  let token: string | null = null;
  if (sessionId) {
    const { data } = await supabaseAdmin
      .from("purchases")
      .select("report_token, status")
      .eq("stripe_session", sessionId)
      .maybeSingle();
    if (data?.status === "paid" && data.report_token) token = data.report_token;
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold mb-2">Tack för ditt köp!</h1>
      <p className="text-gray-600 mb-8">
        Din lönerapport på 99 kr. Länken är giltig i tre månader.
      </p>

      {token ? (
        // Betalning redan bekräftad (kort/redan-klart) – visa länken direkt.
        <div className="bg-green-50 border border-green-200 rounded-lg p-5">
          <p className="font-medium text-green-900 mb-3">Din rapport är klar!</p>
          <a
            href={`/rapport/${token}`}
            className="inline-block bg-brand text-white text-sm px-4 py-2 rounded-lg hover:opacity-90"
          >
            Öppna lönerapporten
          </a>
          <p className="text-xs text-green-800 mt-3">
            Vi har även mejlat länken till dig. Spara den – den fungerar utan inloggning.
          </p>
        </div>
      ) : sessionId ? (
        // Ännu inte bekräftad (t.ex. Klarna async) – polla och fall tillbaka på mejl.
        <Poller sessionId={sessionId} />
      ) : (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-5 text-sm text-amber-800">
          Ingen betalningssession angavs. Om du precis har köpt en rapport mejlar vi
          länken till dig så fort betalningen är bekräftad.{" "}
          <a href="/rapport/skicka-igen" className="underline">
            Skicka länken igen
          </a>
          .
        </div>
      )}
    </div>
  );
}
