// Stripe-webhook = LEVERANSENS SANNINGSKÄLLA (variant C, härdad).
//
// Klarna är asynkron: kunden kan stänga fliken före retur, och betalningen kan
// bekräftas långt efter checkout.session.completed. Därför levereras rapporten
// ALDRIG enbart på retur-URL:en – bara här, efter signaturverifierad bekräftelse.
//
// Idempotens: en purchases-rad per stripe_session (unikt index). Mejl skickas
// exakt en gång – vid den insert/uppgradering som faktiskt flippar raden till paid.
//
// Hårda regler: ingen individdata (endast report_token + valda slugs lagras),
// secrets endast server-side.
import { NextResponse } from "next/server";
import crypto from "node:crypto";
import type Stripe from "stripe";
import { getStripe, RAPPORT_PRIS_SEK } from "@/lib/stripe";
import { supabaseAdmin } from "@/lib/supabase";
import { sendReportEmail } from "@/lib/email";

export const runtime = "nodejs";
// Ingen caching – varje webhook-leverans ska köra handlern.
export const dynamic = "force-dynamic";

function slugsFromSession(session: Stripe.Checkout.Session): string[] {
  const csv = session.metadata?.selected_slugs ?? "";
  return csv
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 5);
}

function employersFromSession(session: Stripe.Checkout.Session): number[] {
  const csv = session.metadata?.selected_employers ?? "";
  return csv
    .split(",")
    .map((s) => parseInt(s.trim(), 10))
    .filter((n) => Number.isInteger(n) && n > 0)
    .slice(0, 5);
}

function emailFromSession(session: Stripe.Checkout.Session): string | null {
  return session.customer_details?.email ?? session.customer_email ?? null;
}

function expiryFromNow(): Date {
  const d = new Date();
  d.setMonth(d.getMonth() + 3);
  return d;
}

// Skapar/uppgraderar en BETALD rad idempotent och mejlar token-länken exakt en
// gång (vid den operation som faktiskt levererar). Anropas när betalning är
// bekräftad (card-completed med payment_status=paid, eller async_payment_succeeded).
async function fulfill(session: Stripe.Checkout.Session): Promise<void> {
  const email = emailFromSession(session);
  const slugs = slugsFromSession(session);
  const employers = employersFromSession(session);
  const token = crypto.randomBytes(32).toString("hex"); // 64 hex = 256 bit
  const expires = expiryFromNow();
  // Belopp till kvittots momsspec: Stripes faktiska totalbelopp (öre → kr) om det
  // finns i payloaden, annars priskonstanten. Rör inte betal-/leveranslogiken.
  const amountSek =
    session.amount_total != null ? session.amount_total / 100 : RAPPORT_PRIS_SEK;

  if (!email) {
    console.error(`[stripe-webhook] fulfill utan e-post, session ${session.id}`);
  }

  // 1. Försök skapa betald rad idempotent (ON CONFLICT (stripe_session) DO NOTHING).
  const { data: inserted, error: insErr } = await supabaseAdmin
    .from("purchases")
    .upsert(
      {
        email: email ?? "",
        product: "lonerapport",
        amount_sek: RAPPORT_PRIS_SEK,
        stripe_session: session.id,
        selected_slugs: slugs,
        selected_employers: employers,
        report_token: token,
        status: "paid",
        expires_at: expires.toISOString(),
      },
      { onConflict: "stripe_session", ignoreDuplicates: true },
    )
    .select("report_token, email, expires_at");

  if (insErr) {
    console.error(`[stripe-webhook] insert-fel ${session.id}:`, insErr.message);
    throw insErr; // → 500 så Stripe försöker igen
  }

  if (inserted && inserted.length > 0) {
    // Nyskapad betald rad → leverera.
    await deliverEmail(
      inserted[0].email,
      inserted[0].report_token,
      inserted[0].expires_at,
      session.id,
      new Date(),
      amountSek,
    );
    return;
  }

  // 2. Rad fanns redan (pending från Klarna-completed, eller redan paid).
  const { data: existing } = await supabaseAdmin
    .from("purchases")
    .select("status, report_token, email, expires_at, selected_slugs, selected_employers")
    .eq("stripe_session", session.id)
    .single();

  if (!existing) return; // extrem race; nästa leverans städar
  if (existing.status === "paid") return; // redan levererad → idempotent, ingen dubbelmejl

  // pending → paid. Fyll i token/expiry/slugs/arbetsgivare/e-post om de saknas.
  const finalToken = existing.report_token ?? token;
  const finalExpires = existing.expires_at ?? expires.toISOString();
  const finalEmail = existing.email || email || "";
  const finalSlugs =
    existing.selected_slugs && existing.selected_slugs.length > 0
      ? existing.selected_slugs
      : slugs;
  const finalEmployers =
    existing.selected_employers && existing.selected_employers.length > 0
      ? existing.selected_employers
      : employers;

  // .neq('status','paid') → bara den uppgradering som verkligen flippar raden
  // returnerar en rad; skyddar mot dubbelmejl vid samtidiga leveranser.
  const { data: upgraded, error: updErr } = await supabaseAdmin
    .from("purchases")
    .update({
      status: "paid",
      report_token: finalToken,
      expires_at: finalExpires,
      email: finalEmail,
      selected_slugs: finalSlugs,
      selected_employers: finalEmployers,
    })
    .eq("stripe_session", session.id)
    .neq("status", "paid")
    .select("report_token, email, expires_at");

  if (updErr) {
    console.error(`[stripe-webhook] uppgradering-fel ${session.id}:`, updErr.message);
    throw updErr;
  }
  if (upgraded && upgraded.length > 0) {
    await deliverEmail(
      upgraded[0].email,
      upgraded[0].report_token,
      upgraded[0].expires_at,
      session.id,
      new Date(),
      amountSek,
    );
  }
}

// Skapar en pending-rad för Klarna-flöden där completed kommer före betalning.
// Ingen token, inget mejl – leverans sker först vid async_payment_succeeded.
async function ensurePending(session: Stripe.Checkout.Session): Promise<void> {
  const email = emailFromSession(session);
  if (!email) return; // utan e-post: vänta på async_payment_succeeded (har då detaljer)

  const { error } = await supabaseAdmin.from("purchases").upsert(
    {
      email,
      product: "lonerapport",
      amount_sek: RAPPORT_PRIS_SEK,
      stripe_session: session.id,
      selected_slugs: slugsFromSession(session),
      selected_employers: employersFromSession(session),
      status: "pending",
    },
    { onConflict: "stripe_session", ignoreDuplicates: true },
  );
  if (error) console.error(`[stripe-webhook] pending-fel ${session.id}:`, error.message);
}

async function markFailed(session: Stripe.Checkout.Session): Promise<void> {
  const { error } = await supabaseAdmin
    .from("purchases")
    .update({ status: "failed" })
    .eq("stripe_session", session.id)
    .neq("status", "paid");
  if (error) console.error(`[stripe-webhook] failed-fel ${session.id}:`, error.message);
}

// Skickar rapportmejlet. Ett mejlfel får INTE fälla webhooken (raden är redan
// skapad → kunden kan använda /rapport/skapad och /rapport/skicka-igen).
async function deliverEmail(
  email: string | null,
  token: string | null,
  expiresAt: string | null,
  orderRef: string,
  purchaseDate: Date,
  amountSek: number,
): Promise<void> {
  if (!email || !token || !expiresAt) return;
  const res = await sendReportEmail({
    to: email,
    token,
    expiresAt: new Date(expiresAt),
    orderRef,
    purchaseDate,
    amountSek,
  });
  if (!res.ok) {
    console.error(`[stripe-webhook] Postmark-fel:`, res.error);
  }
}

export async function POST(req: Request): Promise<Response> {
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!secret) {
    console.error("[stripe-webhook] STRIPE_WEBHOOK_SECRET saknas");
    return NextResponse.json({ error: "server misconfigured" }, { status: 500 });
  }

  const sig = req.headers.get("stripe-signature");
  const rawBody = await req.text(); // rå kropp krävs för signaturverifiering

  let event: Stripe.Event;
  try {
    event = getStripe().webhooks.constructEvent(rawBody, sig ?? "", secret);
  } catch (e) {
    console.error("[stripe-webhook] signaturverifiering misslyckades:", (e as Error).message);
    return NextResponse.json({ error: "invalid signature" }, { status: 400 });
  }

  try {
    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session;
        if (session.payment_status === "paid") {
          await fulfill(session); // kort (card) – betalt direkt
        } else {
          await ensurePending(session); // Klarna async – vänta på bekräftelse
        }
        break;
      }
      case "checkout.session.async_payment_succeeded": {
        await fulfill(event.data.object as Stripe.Checkout.Session);
        break;
      }
      case "checkout.session.async_payment_failed": {
        await markFailed(event.data.object as Stripe.Checkout.Session);
        break;
      }
      default:
        // Övriga event ignoreras men kvitteras.
        break;
    }
  } catch (e) {
    // DB-fel → 500 så Stripe gör om leveransen (idempotensen håller).
    console.error("[stripe-webhook] hanteringsfel:", (e as Error).message);
    return NextResponse.json({ error: "handler error" }, { status: 500 });
  }

  return NextResponse.json({ received: true });
}
