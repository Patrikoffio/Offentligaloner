// Kanonisk bas-URL för att bygga absoluta länkar (Stripe success/cancel,
// rapport-token-URL i mejlet). NEXT_PUBLIC_SITE_URL är källa; faller tillbaka
// på Vercel-deployens URL, annars localhost för lokal utveckling.
export function siteUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_SITE_URL;
  if (explicit) return explicit.replace(/\/+$/, "");
  const vercel = process.env.VERCEL_URL;
  if (vercel) return `https://${vercel}`;
  return "http://localhost:3000";
}

// Absolut URL till en tokenserad rapport.
export function reportUrl(token: string): string {
  return `${siteUrl()}/rapport/${token}`;
}
