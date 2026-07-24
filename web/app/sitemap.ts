import type { MetadataRoute } from "next";
import { supabaseAdmin } from "@/lib/supabase";
import { siteUrl } from "@/lib/site";

// Sitemap byggs vid build (statisk). Bara publika, indexerbara sidor:
// startsidan + alla yrkessidor (/yrken/<slug>). Rapport-/API-vägar utelämnas
// (de är noindex och disallowade i robots.ts). Kanonisk bas utan www via
// siteUrl() (NEXT_PUBLIC_SITE_URL = https://offentligaloner.se i produktion).
export const dynamic = "force-static";

async function allSlugs(): Promise<string[]> {
  const pageSize = 1000;
  let from = 0;
  const slugs: string[] = [];

  // Samma paginering som generateStaticParams i yrken/[slug] – alla titlar,
  // även de utan n>=5-data (de får en indexerbar informationssida, ej 404).
  while (true) {
    const { data, error } = await supabaseAdmin
      .from("generalized_titles")
      .select("slug")
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
