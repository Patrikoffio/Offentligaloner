// Bygger rapportdata ENBART ur matviews (n≥5). Ingen individdata.
// Återanvänds av /rapport/[token]. Samma aggregat som de publika yrkessidorna.
import { supabaseAdmin } from "./supabase";

export interface ReportNational {
  n: number;
  n_raw: number;
  mean_salary: number;
  p10: number;
  p25: number;
  median: number;
  p75: number;
  p90: number;
  collection_year: number;
}

export interface ReportEmployer {
  employer_name: string;
  n: number;
  median: number;
  mean_salary: number;
}

export interface ReportTitle {
  slug: string;
  title: string;
  category: string | null;
  national: ReportNational;
  employers: ReportEmployer[]; // ENDAST valda arbetsgivare med n≥5
  emptyEmployers: string[]; // valda arbetsgivare utan publicerbart underlag för yrket
  nationalSourceCount: number; // antal arbetsgivare bakom den nationella spridningen
  allEmployerMedians: number[]; // alla arbetsgivares medianlön (n≥5), fallande – för
  // kommunens placering i den individualiserade sektionen. Endast aggregat.
}

export interface ReportMeta {
  titles: ReportTitle[];
  employerNames: string[]; // valda arbetsgivares namn (för rubrik/inledning)
}

// Bygger rapport för valda yrken × valda arbetsgivare. Nationell spridning som
// referens (samtliga arbetsgivare) + arbetsgivartabell ENBART för de valda
// (n≥5-regeln oförändrad). Endast yrken med publicerbar nationell statistik tas
// med (kan ha tappat n≥5 sedan köpet – tokens lever i 3 mån).
export async function buildReport(
  slugs: string[],
  employerIds: number[],
): Promise<ReportMeta> {
  const clean = Array.from(
    new Set(slugs.map((s) => s.trim()).filter(Boolean)),
  ).slice(0, 5);
  const empIds = Array.from(new Set(employerIds.filter((n) => Number.isInteger(n) && n > 0))).slice(0, 5);
  if (clean.length === 0) return { titles: [], employerNames: [] };

  const { data: titles } = await supabaseAdmin
    .from("generalized_titles")
    .select("id, slug, title, category")
    .in("slug", clean);

  if (!titles || titles.length === 0) return { titles: [], employerNames: [] };

  const ids = titles.map((t) => t.id);

  // Namn på de valda arbetsgivarna (för rubrik + "utan underlag"-noteringar).
  const { data: empRows } = await supabaseAdmin
    .from("employers")
    .select("id, name")
    .in("id", empIds.length > 0 ? empIds : [-1]);
  const empNameById = new Map((empRows ?? []).map((e) => [e.id, e.name]));
  const employerNames = empIds
    .map((id) => empNameById.get(id))
    .filter((n): n is string => !!n);

  const { data: nationals } = await supabaseAdmin
    .from("title_national_stats")
    .select("generalized_title_id, n, n_raw, mean_salary, p10, p25, median, p75, p90, collection_year")
    .in("generalized_title_id", ids);
  const nationalById = new Map((nationals ?? []).map((r) => [r.generalized_title_id, r]));

  // Endast VALDA arbetsgivare, n≥5.
  const { data: empStats } = await supabaseAdmin
    .from("title_employer_stats")
    .select("generalized_title_id, employer_id, n, median, mean_salary, employers(name)")
    .in("generalized_title_id", ids)
    .in("employer_id", empIds.length > 0 ? empIds : [-1])
    .gte("n", 5)
    .order("n", { ascending: false });

  // Antal arbetsgivare bakom den nationella spridningen (samtliga, för källhänvisning).
  const { data: allEmp } = await supabaseAdmin
    .from("title_employer_all")
    .select("generalized_title_id, employer_id")
    .in("generalized_title_id", ids);

  // Alla arbetsgivares medianlön (n≥5) per titel – för att placera vald kommun i
  // den individualiserade sektionen. Endast aggregat (medianer), inga namn/individer.
  const { data: allMedians } = await supabaseAdmin
    .from("title_employer_stats")
    .select("generalized_title_id, median")
    .in("generalized_title_id", ids)
    .gte("n", 5);

  const bySlug = new Map(titles.map((t) => [t.slug, t]));

  const result: ReportTitle[] = [];
  for (const slug of clean) {
    const t = bySlug.get(slug);
    if (!t) continue;
    const national = nationalById.get(t.id);
    if (!national) continue;

    const rows = (empStats ?? []).filter((r) => r.generalized_title_id === t.id);
    const employers: ReportEmployer[] = rows.map((r: any) => ({
      employer_name: r.employers?.name ?? empNameById.get(r.employer_id) ?? "Okänd",
      n: r.n,
      median: r.median,
      mean_salary: r.mean_salary,
    }));

    // Valda arbetsgivare som INTE fick en rad (n<5 eller ingen data för yrket).
    const withData = new Set(rows.map((r: any) => r.employer_id));
    const emptyEmployers = empIds
      .filter((id) => !withData.has(id))
      .map((id) => empNameById.get(id))
      .filter((n): n is string => !!n);

    const nationalSourceCount = new Set(
      (allEmp ?? [])
        .filter((r) => r.generalized_title_id === t.id)
        .map((r: any) => r.employer_id),
    ).size;

    const allEmployerMedians = (allMedians ?? [])
      .filter((r) => r.generalized_title_id === t.id)
      .map((r: any) => r.median as number)
      .filter((m) => typeof m === "number")
      .sort((a, b) => b - a);

    result.push({
      slug: t.slug,
      title: t.title,
      category: t.category,
      national: national as ReportNational,
      employers,
      emptyEmployers,
      nationalSourceCount,
      allEmployerMedians,
    });
  }

  return { titles: result, employerNames };
}
