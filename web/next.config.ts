import type { NextConfig } from "next";
import legacySlugRedirects from "./legacy_slug_redirects.json";

// SEO-kontinuitet vid migreringen (KRITISKT):
//  * Gamla sajten använde /loner/<slug>; v2 använder /yrken/<slug>.
//  * 248 gamla numrerade slugs (oktoberformat, t.ex. 1e-arbetsterapeut) döptes om
//    på källsajten och mappas till nuvarande slug (arbetsterapeut-forste).
//  * Ordning: specifika legacy-mappningar FÖRE den generella /loner/:slug-regeln.
// Alla 301 (permanent).

const nextConfig: NextConfig = {
  async redirects() {
    // statusCode: 301 (inte permanent:true som ger 308) – uttryckligt krav.
    const legacy = Object.entries(
      legacySlugRedirects as Record<string, string>,
    ).map(([from, to]) => ({
      source: `/loner/${from}`,
      destination: `/yrken/${to}`,
      statusCode: 301 as const,
    }));

    return [
      // 1. Retirerade numrerade slugs → nuvarande slug (måste ligga före generella)
      ...legacy,

      // 2. Gamla informationssidor → startsidan (footern bär utgivningsbevis-uppgifter)
      //    OBS: /integritetspolicy INTE här längre – v2 har en egen sida på den
      //    URL:en (footer-länk). En redirect här körs före filsystemsrutten och
      //    skulle dölja sidan.
      { source: "/loner/alla", destination: "/", statusCode: 301 },
      { source: "/utgivningsbevis", destination: "/", statusCode: 301 },
      { source: "/cookies", destination: "/", statusCode: 301 },
      { source: "/anvandarvillkor", destination: "/kopvillkor", statusCode: 301 },
      { source: "/arbetsgivare-journalister", destination: "/", statusCode: 301 },

      // 3. Generell strukturell ändring: /loner/<slug> → /yrken/<slug>
      { source: "/loner/:slug", destination: "/yrken/:slug", statusCode: 301 },
    ];
  },
};

export default nextConfig;
