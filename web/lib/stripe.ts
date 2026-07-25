// Stripe-klient (ENDAST server-side). STRIPE_SECRET_KEY får aldrig NEXT_PUBLIC-
// prefix och importeras aldrig i en klientkomponent. Test- och prodnyckel byts
// via miljövariabeln – ingen nyckel i repo.
//
// LAT instansiering: klienten skapas först vid anrop (i en request), inte vid
// modulladdning. Annars kastar bygget ("Collecting page data") eftersom
// route-modulerna evalueras då utan runtime-secrets i miljön.
import Stripe from "stripe";

let _stripe: Stripe | null = null;

export function getStripe(): Stripe {
  if (_stripe) return _stripe;
  const secret = process.env.STRIPE_SECRET_KEY;
  if (!secret) throw new Error("STRIPE_SECRET_KEY saknas i miljön.");
  // apiVersion utelämnas → kontots pinnade default (undviker versionsdrift).
  _stripe = new Stripe(secret);
  return _stripe;
}

// Priset ligger i Stripe (99 kr). Id byts test↔prod via env STRIPE_PRICE_ID.
// OBS: id:na nedan avser det tidigare 39 kr-priset och MÅSTE ersättas med en
// 99 kr-price i Stripe (test + prod) – annars debiteras fel belopp:
//   gammalt test:  price_1TwOjJLNrfBYc0easXBKp8ih  (39 kr)
//   gammalt prod:  price_1QGSQ3LNrfBYc0eaEvsidyX0  (39 kr)
// Läses lazily så bygget aldrig kräver värdet.
export function stripePriceId(): string {
  return process.env.STRIPE_PRICE_ID ?? "";
}

// Registreras som amount_sek på köp-raden (webhooken). Ska spegla Stripe-priset.
export const RAPPORT_PRIS_SEK = 99;
