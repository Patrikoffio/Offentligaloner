import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/site";

// Tillåt indexering av publika sidor. Utestäng API-rutter och rapportflödet
// (token-URL:er får aldrig indexeras – de är även noindex per sida). Peka
// sökmotorer på sitemapen. Kanonisk host utan www via siteUrl().
export default function robots(): MetadataRoute.Robots {
  const base = siteUrl();
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/api/", "/rapport/"],
      },
    ],
    sitemap: `${base}/sitemap.xml`,
    host: base,
  };
}
