import type { MetadataRoute } from "next";
import { supabaseAdmin } from "@/lib/supabase";
import { siteUrl } from "@/lib/site";

// Sitemap byggs vid build (statisk). Bara publika, indexerbara sidor:
// startsidan + yrkessidor MED nationell statistik (n≥5). Informationssidor
// utan data listas INTE längre i sitemapen. Rapport-/API-vägar utelämnas
// (de är noindex och disallowade i robots.ts). Kanonisk bas utan www via
// siteUrl() (NEXT_PUBLIC_SITE_URL = https://offentligaloner.se i produktion).
export const dynamic = "force-static";

async function allSlugs(): Promise<string[]> {
  const pageSize = 1000;
  let from = 0;
  const slugs: string[] = [];

  // Endast titlar med publicerbar nationell statistik (n≥5): obligatorisk join
  // (!inner) mot title_national_stats filtrerar bort informationssidorna
  // (5821 → 2378). Samma !inner-mönster som api/search/titles. Pagineringen är
  // oförändrad. Info-sidorna finns kvar (ej 404); noindex hanteras separat.
  while (true) {
    const { data, error } = await supabaseAdmin
      .from("generalized_titles")
      .select("slug, title_national_stats!inner(generalized_title_id)")
      .range(from, from + pageSize - 1);

    if (error || !data || data.length === 0) break;
    slugs.push(...data.map((row: { slug: string }) => row.slug));
    if (data.length < pageSize) break;
    from += pageSize;
  }

  return slugs;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = siteUrl();
  const slugs = await allSlugs();

  const staticEntries: MetadataRoute.Sitemap = [
    { url: `${base}/`, changeFrequency: "weekly", priority: 1 },
    { url: `${base}/om-tjansten`, changeFrequency: "monthly", priority: 0.5 },
  ];

  const titleEntries: MetadataRoute.Sitemap = slugs.map((slug) => ({
    url: `${base}/yrken/${slug}`,
    changeFrequency: "monthly",
    priority: 0.7,
  }));

  return [...staticEntries, ...titleEntries];
}
