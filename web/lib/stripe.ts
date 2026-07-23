// Stripe-klient (ENDAST server-side). STRIPE_SECRET_KEY får aldrig NEXT_PUBLIC-
// prefix och importeras aldrig i en klientkomponent. Test- och prodnyckel byts
// via miljövariabeln – ingen nyckel i repo.
import Stripe from "stripe";

const secret = process.env.STRIPE_SECRET_KEY;
if (!secret) {
  // Kastar vid modulladdning i en serverkontext utan nyckel – aldrig i klienten
  // (klienten importerar inte denna modul).
  throw new Error("STRIPE_SECRET_KEY saknas i miljön.");
}

// apiVersion utelämnas → kontots pinnade default (undviker versionsdrift).
export const stripe = new Stripe(secret);

// Priset ligger i Stripe (39 kr). Id byts test↔prod via env:
//   test:  price_1TwOjJLNrfBYc0easXBKp8ih
//   prod:  price_1QGSQ3LNrfBYc0eaEvsidyX0 (byts vid go-live)
export const STRIPE_PRICE_ID = process.env.STRIPE_PRICE_ID ?? "";

export const RAPPORT_PRIS_SEK = 39;
