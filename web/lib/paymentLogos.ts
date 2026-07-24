import fs from "node:fs";
import path from "node:path";
import type { PaymentLogo } from "@/components/PaymentTrust";

// Server-side: vilka officiella betalmärken finns i /public/payment/?
// Ligger filen där renderas märket; saknas den visas bara textvarianten.
// Skapa ALDRIG egna logotyper eller platshållare – lägg endast officiella
// brand-assets på dessa sökvägar.
const CANDIDATES = [
  { file: "visa.svg", alt: "Visa" },
  { file: "mastercard.svg", alt: "Mastercard" },
  { file: "klarna.svg", alt: "Klarna" },
];

export function availablePaymentLogos(): PaymentLogo[] {
  const dir = path.join(process.cwd(), "public", "payment");
  return CANDIDATES.filter((c) => {
    try {
      return fs.existsSync(path.join(dir, c.file));
    } catch {
      return false;
    }
  }).map((c) => ({ src: `/payment/${c.file}`, alt: c.alt }));
}
