import { supabaseAdmin } from "@/lib/supabase";
import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";

// ─── Typer ──────────────────────────────────────────────────────────────────

interface NationalStats {
  n: number;
  mean_salary: number;
  p10: number;
  p25: number;
  median: number;
  p75: number;
  p90: number;
  collection_year: number;
}

interface EmployerStat {
  employer_name: string;
  n: number;
  median: number;
  mean_salary: number;
}

interface Title {
  id: number;
  title: string;
  slug: string;
  category: string | null;
  ai_description: string | null;
  seo_keywords: string[] | null;
  similar_jobs: string[] | null;
}

interface SourceInfo {
  employer_name: string;
  received_at: string | null;
  salary_date: string | null;
}

interface SimilarJobLink {
  title: string;
  slug: string;
  median: number;
  n: number;
}

interface CategoryStats {
  num_titles: number;
  total_n: number;
  median_median: number;
}

// ─── Statisk generering – ALLA generaliserade titlar ─────────────────────────
// Titlar utan n>=5-data får en informationssida i stället för 404.

export async function generateStaticParams() {
  const pageSize = 1000;
  let from = 0;
  const slugs: { slug: string }[] = [];

  while (true) {
    const { data, error } = await supabaseAdmin
      .from("generalized_titles")
      .select("slug")
      .range(from, from + pageSize - 1);

    if (error || !data || data.length === 0) break;
    slugs.push(...data.map((row: any) => ({ slug: row.slug })));
    if (data.length < pageSize) break;
    from += pageSize;
  }

  return slugs;
}

// ─── Metadata ────────────────────────────────────────────────────────────────

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const { data } = await supabaseAdmin
    .from("generalized_titles")
    .select("title, ai_description, seo_keywords")
    .eq("slug", slug)
    .single();

  if (!data) return { title: "Yrke" };

  return {
    title: `Lön – ${data.title}`,
    description:
      descriptionPlain(data.ai_description) ||
      `Lönestatistik för ${data.title} i kommuner och regioner i Sverige.`,
    keywords: data.seo_keywords ?? undefined,
  };
}

// ─── Hjälpfunktioner ─────────────────────────────────────────────────────────

function formatSalary(n: number | null): string {
  if (n == null) return "–";
  return Math.round(n).toLocaleString("sv-SE") + " kr";
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "okänt datum";
  return new Date(dateStr).toLocaleDateString("sv-SE", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

// AI-beskrivningarna är lagrade som HTML (<p>…</p>, ofta flera stycken).
// Normalisera vid rendering (muterar inte det bevarade innehållet): dela i
// stycken vid </p>, strippa kvarvarande taggar, trimma whitespace.
function descriptionParagraphs(html: string | null): string[] {
  if (!html) return [];
  return html
    .split(/<\/p\s*>/i)
    .map((s) => s.replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim())
    .filter(Boolean);
}

// Plain text (utan taggar/styckesindelning) – för meta-description.
function descriptionPlain(html: string | null): string {
  return descriptionParagraphs(html).join(" ");
}

// ─── Sida ────────────────────────────────────────────────────────────────────

export default async function YrkeSida({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  // Hämta titel (inkl. similar_jobs för informationssidan)
  const { data: title } = await supabaseAdmin
    .from("generalized_titles")
    .select("id, title, slug, category, ai_description, seo_keywords, similar_jobs")
    .eq("slug", slug)
    .single<Title>();

  if (!title) notFound();

  // Hämta nationell statistik (kan saknas — titlar utan n>=5 data får informationssida)
  const { data: national } = await supabaseAdmin
    .from("title_national_stats")
    .select("n, mean_salary, p10, p25, median, p75, p90, collection_year")
    .eq("generalized_title_id", title.id)
    .single<NationalStats>();

  // ── Datahämtning för sidor MED statistik ─────────────────────────────────

  const employerList: EmployerStat[] = [];
  let sourceList: SourceInfo[] = [];

  if (national) {
    // Hämta per-arbetsgivare statistik
    const { data: employerStatsDirect } = await supabaseAdmin
      .from("title_employer_stats")
      .select("employer_id, n, median, mean_salary, employers(name)")
      .eq("generalized_title_id", title.id)
      .gte("n", 5)
      .order("n", { ascending: false })
      .limit(20);

    employerList.push(
      ...(employerStatsDirect ?? []).map((r: any) => ({
        employer_name: r.employers?.name ?? "Okänd",
        n: r.n,
        median: r.median,
        mean_salary: r.mean_salary,
      }))
    );

    // Hämta källhänvisningar
    const { data: sources } = await supabaseAdmin
      .from("source_documents")
      .select("received_at, salary_date, collection_requests(employer_id, employers(name))")
      .order("salary_date", { ascending: false })
      .limit(5);

    sourceList = (sources ?? []).map((s: any) => ({
      employer_name: s.collection_requests?.employers?.name ?? "Okänd",
      received_at: s.received_at,
      salary_date: s.salary_date,
    }));
  }

  // ── Datahämtning för sidor UTAN statistik ────────────────────────────────

  let similarJobLinks: SimilarJobLink[] = [];
  let categoryStats: CategoryStats | null = null;

  if (!national) {
    // Similar_jobs med publicerbar data (lookup via titel-namn → slug)
    if (title.similar_jobs && title.similar_jobs.length > 0) {
      const { data: similarData } = await supabaseAdmin
        .from("generalized_titles")
        .select("title, slug, title_national_stats(n, median)")
        .in("title", title.similar_jobs)
        .limit(10);

      similarJobLinks = (similarData ?? [])
        .filter((r: any) => r.title_national_stats && r.title_national_stats.length > 0)
        .map((r: any) => ({
          title: r.title,
          slug: r.slug,
          median: r.title_national_stats[0].median,
          n: r.title_national_stats[0].n,
        }))
        .sort((a, b) => b.n - a.n)
        .slice(0, 5);
    }

    // Kategoristatistik
    if (title.category) {
      const { data: catData } = await supabaseAdmin
        .from("title_national_stats")
        .select("median, n, generalized_titles!inner(category)")
        .eq("generalized_titles.category", title.category);

      if (catData && catData.length > 0) {
        const medians = (catData as any[]).map((r) => r.median).sort((a, b) => a - b);
        const mid = Math.floor(medians.length / 2);
        categoryStats = {
          num_titles: medians.length,
          total_n: (catData as any[]).reduce((s, r) => s + r.n, 0),
          median_median:
            medians.length % 2 === 0
              ? Math.round((medians[mid - 1] + medians[mid]) / 2)
              : Math.round(medians[mid]),
        };
      }
    }
  }

  const year = national?.collection_year ?? 2024;

  const distribution = national
    ? [
        { label: "10:e percentilen", value: national.p10 },
        { label: "25:e percentilen", value: national.p25 },
        { label: "Median", value: national.median, highlight: true },
        { label: "75:e percentilen", value: national.p75 },
        { label: "90:e percentilen", value: national.p90 },
        { label: "Medellön", value: national.mean_salary },
      ]
    : [];

  const maxVal = national?.p90 ?? 1;

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      {/* Brödsmula */}
      <nav className="text-sm text-gray-500 mb-4">
        <a href="/" className="hover:underline">Startsida</a>
        {" › "}
        {title.category && (
          <>
            <span>{title.category}</span>
            {" › "}
          </>
        )}
        <span className="text-gray-700">{title.title}</span>
      </nav>

      {/* Rubrik */}
      <h1 className="text-3xl font-bold tracking-tight mb-1">{title.title}</h1>
      {title.category && (
        <p className="text-sm text-blue-600 mb-4">{title.category}</p>
      )}
      {descriptionParagraphs(title.ai_description).length > 0 && (
        <div className="text-gray-600 mb-8 max-w-2xl space-y-3">
          {descriptionParagraphs(title.ai_description).map((para, i) => (
            <p key={i}>{para}</p>
          ))}
        </div>
      )}

      {/* ── Informationssida (ingen publicerbar data) ────────────────────── */}
      {!national && (
        <div className="space-y-8">
          {/* Förklaring */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
            <p className="font-medium text-amber-900 mb-2">
              Ingen publicerbar lönestatistik för {title.title} ännu
            </p>
            <p className="text-sm text-amber-800">
              Statistik visas bara när vi har uppgifter från minst 5 individer med samma
              titel. Det kan bero på att titeln är ovanlig, att den stavades annorlunda
              i inlämnade filer, eller att den enbart förekom hos arbetsgivare som inte
              deltog i 2024 års insamling. Nästa datainsamling sker 2026.
            </p>
          </div>

          {/* Kategoristatistik */}
          {title.category && categoryStats && (
            <section>
              <h2 className="text-lg font-semibold mb-3">
                Löner inom {title.category}
              </h2>
              <p className="text-sm text-gray-500 mb-4">
                Baserat på {categoryStats.num_titles.toLocaleString("sv-SE")} yrkestitlar
                och {categoryStats.total_n.toLocaleString("sv-SE")} anställda i denna
                kategori i 2024 års data.
              </p>
              <div className="bg-gray-50 rounded-lg p-4 inline-block">
                <p className="text-sm text-gray-500 mb-1">
                  Typisk medianlön inom kategorin
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {categoryStats.median_median.toLocaleString("sv-SE")} kr/mån
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Medianen av alla titlars medianer i kategorin. Heltidsekvivalent.
                </p>
              </div>
            </section>
          )}

          {/* Liknande yrken med data */}
          {similarJobLinks.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-3">
                Liknande yrken med tillgänglig statistik
              </h2>
              <ul className="divide-y divide-gray-100 border border-gray-100 rounded-lg overflow-hidden">
                {similarJobLinks.map((job) => (
                  <li key={job.slug}>
                    <Link
                      href={`/yrken/${job.slug}`}
                      className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
                    >
                      <span className="font-medium text-gray-800">{job.title}</span>
                      <span className="text-sm text-gray-500 ml-4 shrink-0">
                        {formatSalary(job.median)} median &middot;{" "}
                        {job.n.toLocaleString("sv-SE")} anst.
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Fallback om inga similar_jobs heller */}
          {similarJobLinks.length === 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-3">Utforska fler yrken</h2>
              <p className="text-sm text-gray-500 mb-3">
                Bläddra bland yrken med tillgänglig lönestatistik.
              </p>
              <Link
                href="/"
                className="inline-block bg-blue-600 text-white text-sm px-4 py-2 rounded hover:bg-blue-700"
              >
                Tillbaka till startsidan
              </Link>
            </section>
          )}
        </div>
      )}

      {/* ── Sida MED statistik ──────────────────────────────────────────────── */}

      {/* Lönedistribution */}
      {national && (
        <section className="mb-10">
          <h2 className="text-xl font-semibold mb-1">
            Löner {year} — {national.n.toLocaleString("sv-SE")} anställda
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            Omräknat till heltidslön. Källa:{" "}
            {national.n.toLocaleString("sv-SE")} individer hos{" "}
            {employerList.length} arbetsgivare.
          </p>

          <div className="space-y-3">
            {distribution.map(({ label, value, highlight }) => (
              <div key={label} className="flex items-center gap-3">
                <span
                  className={`w-44 text-sm text-right shrink-0 ${
                    highlight ? "font-semibold" : "text-gray-600"
                  }`}
                >
                  {label}
                </span>
                <div className="flex-1 bg-gray-100 rounded-full h-5 relative">
                  <div
                    className={`h-5 rounded-full ${
                      highlight ? "bg-blue-500" : "bg-blue-300"
                    }`}
                    style={{ width: `${Math.round((value / maxVal) * 100)}%` }}
                  />
                </div>
                <span
                  className={`w-28 text-sm ${
                    highlight ? "font-semibold" : "text-gray-700"
                  }`}
                >
                  {formatSalary(value)}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Per arbetsgivare */}
      {employerList.length > 0 && (
        <section className="mb-10">
          <h2 className="text-xl font-semibold mb-4">Per arbetsgivare</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-gray-200 text-left text-gray-500">
                  <th className="pb-2 pr-4 font-medium">Arbetsgivare</th>
                  <th className="pb-2 pr-4 font-medium text-right">Antal</th>
                  <th className="pb-2 pr-4 font-medium text-right">Median</th>
                  <th className="pb-2 font-medium text-right">Medellön</th>
                </tr>
              </thead>
              <tbody>
                {employerList.map((e) => (
                  <tr
                    key={e.employer_name}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-2 pr-4">{e.employer_name}</td>
                    <td className="py-2 pr-4 text-right text-gray-500">{e.n}</td>
                    <td className="py-2 pr-4 text-right font-medium">
                      {formatSalary(e.median)}
                    </td>
                    <td className="py-2 text-right text-gray-600">
                      {formatSalary(e.mean_salary)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Visas bara för arbetsgivare med minst 5 anställda i denna titel.
          </p>
        </section>
      )}

      {/* Källhänvisning — hård regel: ska alltid visas */}
      <section className="border-t border-gray-100 pt-6 text-xs text-gray-500">
        <h3 className="font-medium text-gray-700 mb-2">Källhänvisning</h3>
        <p>
          Statistiken avser lönedata för år <strong>{year}</strong>, insamlad
          via offentlighetsprincipen. Arbetsgivarna har lämnat ut uppgifterna
          på begäran.
        </p>
        {sourceList.length > 0 && (
          <ul className="mt-2 space-y-1">
            {sourceList.slice(0, 3).map((s, i) => (
              <li key={i}>
                {s.employer_name}
                {s.received_at
                  ? `, utlämnat ${formatDate(s.received_at)}`
                  : s.salary_date
                  ? `, lönedata ${formatDate(s.salary_date)}`
                  : ""}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-2">
          Individdata visas aldrig — aggregat kräver minst 5 individer.
        </p>
      </section>
    </div>
  );
}
