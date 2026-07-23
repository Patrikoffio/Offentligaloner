// /rapport/skicka-igen: ommejlar giltiga (ej utgångna) rapportlänkar för en
// e-postadress. Rate-limitad + ALLTID generiskt svar → ingen enumeration
// (avslöjar aldrig om en adress finns eller har köpt).
import { NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";
import { sendResendEmail } from "@/lib/email";
import { rateLimit, clientIp } from "@/lib/ratelimit";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// Samma svar oavsett utfall.
const GENERIC = {
  message:
    "Om det finns giltiga rapporter kopplade till adressen skickar vi länkarna dit. " +
    "Kolla din inkorg (och skräppost).",
};

export async function POST(req: Request): Promise<Response> {
  // IP-baserad broms: 5 försök / 10 min.
  if (!rateLimit(`resend:ip:${clientIp(req)}`, 5, 10 * 60 * 1000)) {
    return NextResponse.json(
      { message: "För många försök. Försök igen om en stund." },
      { status: 429 },
    );
  }

  let email = "";
  try {
    const body = (await req.json()) as { email?: unknown };
    if (typeof body.email === "string") email = body.email.trim().toLowerCase();
  } catch {
    return NextResponse.json(GENERIC); // svälj – generiskt svar
  }

  // Grundläggande formatkontroll; ogiltig adress → generiskt svar (inget läckage).
  if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return NextResponse.json(GENERIC);
  }

  // Extra broms per adress: 3 försök / 10 min.
  if (!rateLimit(`resend:email:${email}`, 3, 10 * 60 * 1000)) {
    return NextResponse.json(GENERIC);
  }

  const nowIso = new Date().toISOString();
  const { data } = await supabaseAdmin
    .from("purchases")
    .select("report_token, expires_at, status")
    .eq("email", email)
    .eq("status", "paid")
    .gt("expires_at", nowIso);

  const links = (data ?? [])
    .filter((r) => r.report_token && r.expires_at)
    .map((r) => ({ token: r.report_token as string, expiresAt: new Date(r.expires_at as string) }));

  if (links.length > 0) {
    const res = await sendResendEmail({ to: email, links });
    if (!res.ok) console.error("[resend] Postmark-fel:", res.error);
  }

  // Alltid samma svar.
  return NextResponse.json(GENERIC);
}
