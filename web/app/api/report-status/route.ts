// Lättviktig statusslagning för /rapport/skapad-pollningen.
// Returnerar { ready, token } för en Stripe-session. Token lämnas bara ut när
// betalningen är bekräftad (status=paid) – webhooken är sanningskälla.
import { NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request): Promise<Response> {
  const { searchParams } = new URL(req.url);
  const sessionId = searchParams.get("session_id");
  if (!sessionId) {
    return NextResponse.json({ ready: false }, { status: 400 });
  }

  const { data } = await supabaseAdmin
    .from("purchases")
    .select("status, report_token")
    .eq("stripe_session", sessionId)
    .maybeSingle();

  if (data?.status === "paid" && data.report_token) {
    return NextResponse.json({ ready: true, token: data.report_token });
  }
  // pending/failed/saknas → inte klar (avslöjar inget mer)
  return NextResponse.json({ ready: false });
}
