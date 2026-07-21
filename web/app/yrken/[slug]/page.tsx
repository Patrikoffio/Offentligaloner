import { supabaseAdmin } from "@/lib/supabase";
import { notFound } from "next/navigation";
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
}

interface SourceInfo {
  employer_name: string;
  received_at: string | null;
  salary_date: string | null;
}

// ─── Statisk generering – ALLA generaliserade titlar ─────────────────────────
// Titlar utan n>=5-data får en "ingen data ännu"-sida i stället för 404.

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
      data.ai_description ??
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

// ─── Sida ────────────────────────────────────────────────────────────────────

export default async function YrkeSida({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  // Hämta titel
  const { data: title } = await supabaseAdmin
    .from("generalized_titles")
    .select("id, title, slug, category, ai_description, seo_keywords")
    .eq("slug", slug)
    .single<Title>();

  if (!title) notFound();

  // Hämta nationell statistik (kan saknas — titlar utan n>=5 data får ingen-data-sida)
  const { data: national } = await supabaseAdmin
    .from("title_national_stats")
    .select("n, mean_salary, p10, p25, median, p75, p90, collection_year")
    .eq("generalized_title_id", title.id)
    .single<NationalStats>();

  // Hämta per-arbetsgivare statistik (top 20 per median)
  const { data: employers } = await supabaseAdmin
    .rpc("get_employer_stats_for_title", { p_title_id: title.id })
    .limit(20) as { data: EmployerStat[] | null };

  // Fallback: hämta employer stats direkt om RPC saknas
  const { data: employerStatsDirect } = await supabaseAdmin
    .from("title_employer_stats")
    .select("employer_id, n, median, mean_salary, employers(name)")
    .eq("generalized_title_id", title.id)
    .gte("n", 5)
    .order("n", { ascending: false })
    .limit(20);

  const employerList = (employerStatsDirect ?? []).map((r: any) => ({
    employer_name: r.employers?.name ?? "Okänd",
    n: r.n,
    median: r.median,
    mean_salary: r.mean_salary,
  }));

  // Hämta källhänvisningar
  const { data: sources } = await supabaseAdmin
    .from("source_documents")
    .select(
      "received_at, salary_date, collection_requests(employer_id, employers(name))"
    )
    .order("salary_date", { ascending: false })
    .limit(5);

  const sourceList: SourceInfo[] = (sources ?? []).map((s: any) => ({
    employer_name: s.collection_requests?.employers?.name ?? "Okänd",
    received_at: s.received_at,
    salary_date: s.salary_date,
  }));

  const year = national?.collection_year ?? 2024;

  // Lönedistribution — percentiler
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

  // Stapelbredd relativt p90
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
      {title.ai_description && (
        <p className="text-gray-600 mb-8 max-w-2xl">{title.ai_description}</p>
      )}

      {/* Ingen data ännu */}
      {!national && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-8">
          <p className="text-gray-700 font-medium mb-1">
            Ingen publicerbar statistik ännu
          </p>
          <p className="text-sm text-gray-500">
            För att statistik ska visas krävs uppgifter från minst 5 individer
            med denna titel i vår insamling. Antingen saknas titeln i 2024 års
            data, eller har den för få förekomster för att publiceras.
            Statistiken uppdateras när ny data samlas in.
          </p>
        </div>
      )}

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
                    <td className="py-2 pr-4 text-right text-gray-500">
                      {e.n}
                    </td>
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
