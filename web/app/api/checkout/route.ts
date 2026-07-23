// Skapar en Stripe Checkout Session SERVER-SIDE. Klienten skickar valda slugs;
// pris (39 kr) och betalmetoder bestäms här, aldrig i klienten.
//
// Validering (hård regel 1): varje vald slug måste ha publicerbar nationell
// statistik (n≥5 i title_national_stats). Titlar utan underlag kan inte köpas –
// rapporten byggs enbart ur matviews.
import { NextResponse } from "next/server";
import type Stripe from "stripe";
import { getStripe, stripePriceId } from "@/lib/stripe";
import { supabaseAdmin } from "@/lib/supabase";
import { siteUrl } from "@/lib/site";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_TITLES = 5;
const MAX_EMPLOYERS = 5;

export async function POST(req: Request): Promise<Response> {
  const priceId = stripePriceId();
  if (!priceId) {
    return NextResponse.json({ error: "STRIPE_PRICE_ID saknas i miljön." }, { status: 500 });
  }

  // ── Läs och normalisera valda slugs ──────────────────────────────────────
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Ogiltig begäran." }, { status: 400 });
  }

  const rawSlugs = (body as { slugs?: unknown })?.slugs;
  const rawEmployers = (body as { employers?: unknown })?.employers;
  if (!Array.isArray(rawSlugs)) {
    return NextResponse.json({ error: "slugs saknas." }, { status: 400 });
  }
  if (!Array.isArray(rawEmployers)) {
    return NextResponse.json({ error: "employers saknas." }, { status: 400 });
  }

  // Avdubbla, trimma, behåll ordning.
  const slugs = Array.from(
    new Set(
      rawSlugs
        .filter((s): s is string => typeof s === "string")
        .map((s) => s.trim())
        .filter(Boolean),
    ),
  );

  // Arbetsgivare kommer som numeriska id:n (accepterar även sifferstr).
  const employerIds = Array.from(
    new Set(
      rawEmployers
        .map((e) => (typeof e === "number" ? e : typeof e === "string" ? parseInt(e, 10) : NaN))
        .filter((n) => Number.isInteger(n) && n > 0),
    ),
  );

  if (slugs.length < 1) {
    return NextResponse.json({ error: "Välj minst ett yrke." }, { status: 400 });
  }
  if (slugs.length > MAX_TITLES) {
    return NextResponse.json(
      { error: `Högst ${MAX_TITLES} yrken per rapport.` },
      { status: 400 },
    );
  }
  if (employerIds.length < 1) {
    return NextResponse.json({ error: "Välj minst en kommun/region." }, { status: 400 });
  }
  if (employerIds.length > MAX_EMPLOYERS) {
    return NextResponse.json(
      { error: `Högst ${MAX_EMPLOYERS} kommuner/regioner per rapport.` },
      { status: 400 },
    );
  }

  // ── Validera n≥5: slug → generalized_title → title_national_stats ─────────
  const { data: titles, error: titleErr } = await supabaseAdmin
    .from("generalized_titles")
    .select("id, slug, title")
    .in("slug", slugs);

  if (titleErr) {
    return NextResponse.json({ error: "Databasfel vid validering." }, { status: 500 });
  }

  const foundSlugs = new Set((titles ?? []).map((t) => t.slug));
  const missing = slugs.filter((s) => !foundSlugs.has(s));
  if (missing.length > 0) {
    return NextResponse.json(
      { error: `Okänd titel: ${missing.join(", ")}` },
      { status: 400 },
    );
  }

  const idBySlug = new Map((titles ?? []).map((t) => [t.slug, t.id]));
  const ids = slugs.map((s) => idBySlug.get(s)!);

  const { data: stats, error: statsErr } = await supabaseAdmin
    .from("title_national_stats")
    .select("generalized_title_id")
    .in("generalized_title_id", ids);

  if (statsErr) {
    return NextResponse.json({ error: "Databasfel vid validering." }, { status: 500 });
  }

  const publishableIds = new Set((stats ?? []).map((r) => r.generalized_title_id));
  const nonPublishable = slugs.filter((s) => !publishableIds.has(idBySlug.get(s)!));
  if (nonPublishable.length > 0) {
    return NextResponse.json(
      {
        error:
          "Följande yrken saknar publicerbar lönestatistik (minst 5 individer krävs): " +
          nonPublishable.join(", "),
      },
      { status: 400 },
    );
  }

  // ── Validera arbetsgivare: id:na måste finnas i employers ────────────────
  const { data: emps, error: empErr } = await supabaseAdmin
    .from("employers")
    .select("id")
    .in("id", employerIds);

  if (empErr) {
    return NextResponse.json({ error: "Databasfel vid validering." }, { status: 500 });
  }
  const foundEmpIds = new Set((emps ?? []).map((e) => e.id));
  const missingEmp = employerIds.filter((id) => !foundEmpIds.has(id));
  if (missingEmp.length > 0) {
    return NextResponse.json(
      { error: `Okänd arbetsgivare: ${missingEmp.join(", ")}` },
      { status: 400 },
    );
  }

  // ── Skapa Checkout Session ───────────────────────────────────────────────
  const base = siteUrl();

  const params: Stripe.Checkout.SessionCreateParams = {
    mode: "payment",
    line_items: [{ price: priceId, quantity: 1 }],
    payment_method_types: ["card", "klarna"],
    automatic_tax: { enabled: true },
    locale: "sv",
    // Ångerrätts-waiver: digital tjänst som levereras omedelbart.
    consent_collection: { terms_of_service: "required" },
    custom_text: {
      terms_of_service_acceptance: {
        message:
          "Rapporten är en digital tjänst som levereras direkt efter köp. Genom att " +
          "godkänna villkoren samtycker du till omedelbar leverans och att ångerrätten " +
          "därmed upphör när tjänsten fullgjorts.",
      },
    },
    allow_promotion_codes: true,
    metadata: {
      // Webhooken läser dessa. Max 5 vardera, avdubblade.
      selected_slugs: slugs.join(","),
      selected_employers: employerIds.join(","),
    },
    success_url: `${base}/rapport/skapad?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${base}/rapport/avbruten`,
  };

  try {
    const session = await getStripe().checkout.sessions.create(params);
    return NextResponse.json({ url: session.url });
  } catch (e) {
    const msg = (e as Error).message;
    console.error("[checkout] Stripe-fel:", msg);
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}
