// Uppräkning 2024 → 2026 enligt centrala avtal (avtalsområde → procent).
//
// Feature-flagga: aktiveras separat via env NEXT_PUBLIC_SHOW_PROJECTION_2026=true.
// AV som default. Talen nedan är PLACEHOLDERS – fylls i separat innan aktivering.
// När flaggan är på men ett tal saknas returneras null (inget 2026-värde visas).

export const PROJECTION_ENABLED =
  process.env.NEXT_PUBLIC_SHOW_PROJECTION_2026 === "true";

// Avtalsområde → sammanlagd uppräkningsprocent 2024→2026 (decimal, 0.06 = 6 %).
// TODO(verksamheten): fyll i från centrala avtal.
export const AGREEMENT_INCREASE: Record<string, number> = {
  // "HÖK/OK (SKR/Sobona)": 0.00,
  // "AB Kommunal":         0.00,
};

// Kategori → avtalsområde (grov mappning; justeras separat).
// TODO(verksamheten): mappa de 24 kategorierna till rätt avtalsområde.
export const CATEGORY_TO_AGREEMENT: Record<string, string> = {
  // "Vård och Omsorg": "HÖK/OK (SKR/Sobona)",
};

export function agreementAreaFor(category: string | null): string | null {
  if (!category) return null;
  return CATEGORY_TO_AGREEMENT[category] ?? null;
}

// Uppskattad 2026-lön ur ett uppmätt 2024-värde. null = ska inte visas
// (flagga av, saknad kategori/avtalsområde eller saknat tal).
export function projectedSalary(
  value2024: number | null,
  category: string | null,
): number | null {
  if (!PROJECTION_ENABLED || value2024 == null) return null;
  const area = agreementAreaFor(category);
  if (!area) return null;
  const pct = AGREEMENT_INCREASE[area];
  if (pct == null) return null;
  return Math.round(value2024 * (1 + pct));
}

export const PROJECTION_METHOD_NOTE =
  "2026 uppskattad = 2024 års uppmätta värde uppräknat med den centralt avtalade " +
  "löneökningen för yrkets avtalsområde. Det är en schablon per avtalsområde, inte " +
  "en prognos för enskild lön. Faktiska löner fastställs lokalt och kan avvika.";
