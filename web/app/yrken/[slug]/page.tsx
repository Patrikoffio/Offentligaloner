import { supabaseAdmin } from "@/lib/supabase";
import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import {
  PROJECTION_ENABLED,
  projectedSalary,
  PROJECTION_METHOD_NOTE,
} from "@/lib/projections";
import OrderReport, {
  ContactLine,
  type TitleOption,
  type EmployerOption,
} from "./OrderReport";
import EmployerTable from "./EmployerTable";
import DistributionBand from "@/components/DistributionBand";
import { coverageNote } from "@/lib/copy";
import { availablePaymentLogos } from "@/lib/paymentLogos";

// ─── Typer ──────────────────────────────────────────────────────────────────

interface NationalStats {
  n: number;
  n_hourly: number;
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

interface SmallEmployer {
  employer_name: string;
  n: number;
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
    .select("id, title, ai_description, seo_keywords")
    .eq("slug", slug)
    .single();

  if (!data) return { title: "Yrke" };

  // Kanonisk URL per yrke (utan www; metadataBase gör den absolut).
  const canonicalPath = `/yrken/${slug}`;

  // Nationell statistik (kan saknas → informationssida utan siffror).
  const { data: national } = await supabaseAdmin
    .from("title_national_stats")
    .select("n, median, p10, p90, collection_year")
    .eq("generalized_title_id", data.id)
    .maybeSingle();

  if (national) {
    // Antal arbetsgivare = SAMMA tal som sidan renderar (sourceList.length =
    // rader i title_employer_all för titeln). collection_year ur datan.
    const { count } = await supabaseAdmin
      .from("title_employer_all")
      .select("*", { count: "exact", head: true })
      .eq("generalized_title_id", data.id);
    const employers = count ?? 0;

    // Samma avrundning/format som formatSalary och DistributionBand (sv-SE).
    const kr = (n: number) => Math.round(n).toLocaleString("sv-SE");

    // Titel < 60 tecken: släpp varumärkesdelen när yrkesnamnet är långt.
    const core = `${data.title} lön ${national.collection_year} – median ${kr(national.median)} kr`;
    const withBrand = `${core} | Offentligalöner`;
    const title = withBrand.length <= 60 ? withBrand : core;

    const description =
      `Median ${kr(national.median)} kr/mån för ${data.title} i kommuner och ` +
      `regioner. ${national.n.toLocaleString("sv-SE")} faktiska löner från ${employers} ` +
      `arbetsgivare, utlämnade enligt offentlighetsprincipen. ` +
      `Spridning ${kr(national.p10)}–${kr(national.p90)} kr.`;

    return {
      title: { absolute: title }, // absolute = kringgå layoutens "%s | …"-mall
      description,
      keywords: data.seo_keywords ?? undefined,
      alternates: { canonical: canonicalPath },
      openGraph: { url: canonicalPath, title, description },
    };
  }

  // Utan statistik: behåll nuvarande (ingen årsangivelse i titeln).
  const description =
    descriptionPlain(data.ai_description) ||
    `Lönestatistik för ${data.title} i kommuner och regioner i Sverige.`;

  return {
    title: `Lön – ${data.title}`,
    description,
    keywords: data.seo_keywords ?? undefined,
    alternates: { canonical: canonicalPath },
    openGraph: {
      url: canonicalPath,
      title: `Lön – ${data.title}`,
      description,
    },
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

// ai_description är städad till ren text med tomrad mellan stycken (se
// pipeline/clean_ai_descriptions.py). Dela i stycken vid tomrad; behåll </p>-
// och tagg-strippning som skydd ifall otvättat innehåll skulle dyka upp.
function descriptionParagraphs(text: string | null): string[] {
  if (!text) return [];
  return text
    .split(/(?:<\/p\s*>|\n\s*\n)/i)
    .map((s) => s.replace(/<[^>]*>/g, "").replace(/[ \t\r]+/g, " ").trim())
    .filter(Boolean);
}

// Plain text (utan taggar/styckesindelning) – för meta-description.
function descriptionPlain(html: string | null): string {
  return descriptionParagraphs(html).join(" ");
}

const SV_MONTHS = ["januari","februari","mars","april","maj","juni","juli",
  "augusti","september","oktober","november","december"];

// Svenskt månadsintervall ur en lista datum, t.ex. "mars–maj 2024" / "mars 2024".
function monthRange(dates: (string | null)[]): string {
  const ds = dates
    .filter(Boolean)
    .map((d) => new Date(d as string))
    .filter((d) => !isNaN(d.getTime()))
    .sort((a, b) => a.getTime() - b.getTime());
  if (ds.length === 0) return "";
  const first = ds[0];
  const last = ds[ds.length - 1];
  const m1 = SV_MONTHS[first.getMonth()];
  const m2 = SV_MONTHS[last.getMonth()];
  return m1 === m2 ? `${m1} ${last.getFullYear()}` : `${m1}–${m2} ${last.getFullYear()}`;
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
    .select("n, n_hourly, mean_salary, p10, p25, median, p75, p90, collection_year")
    .eq("generalized_title_id", title.id)
    .single<NationalStats>();

  // ── Datahämtning för sidor MED statistik ─────────────────────────────────

  const employerList: EmployerStat[] = [];
  let sourceList: SourceInfo[] = [];
  let smallEmployers: SmallEmployer[] = [];
  let orderCandidates: TitleOption[] = [];
  let allEmployers: EmployerOption[] = [];

  if (national) {
    // Hämta per-arbetsgivare statistik. Hämtar ALLA n≥5-arbetsgivare (inte bara 20)
    // så arbetsgivartabellens expander kan visa hela listan. n≥5-regeln oförändrad.
    const { data: employerStatsDirect } = await supabaseAdmin
      .from("title_employer_stats")
      .select("employer_id, n, median, mean_salary, employers(name)")
      .eq("generalized_title_id", title.id)
      .gte("n", 5)
      .order("n", { ascending: false })
      .limit(1000);

    employerList.push(
      ...(employerStatsDirect ?? []).map((r: any) => ({
        employer_name: r.employers?.name ?? "Okänd",
        n: r.n,
        median: r.median,
        mean_salary: r.mean_salary,
      }))
    );

    // Alla arbetsgivare som lämnat ut uppgifter för denna titel (även n<5) –
    // driver källhänvisningen och n<5-raderna. Inga lönevärden här.
    const { data: allEmp } = await supabaseAdmin
      .from("title_employer_all")
      .select("employer_name, n, received_at, salary_date")
      .eq("generalized_title_id", title.id)
      .order("received_at", { ascending: true });

    sourceList = (allEmp ?? []).map((r: any) => ({
      employer_name: r.employer_name ?? "Okänd",
      received_at: r.received_at,
      salary_date: r.salary_date,
    }));

    // Arbetsgivare med för litet underlag för lönestatistik (n<5) – visas med
    // antal anställda men utan lönesiffror.
    smallEmployers = (allEmp ?? [])
      .filter((r: any) => r.n < 5)
      .map((r: any) => ({ employer_name: r.employer_name ?? "Okänd", n: r.n }))
      .sort((a: SmallEmployer, b: SmallEmployer) => b.n - a.n);

    // Kandidater till rapportbeställningen: aktuell titel + syskon i samma
    // kategori som har publicerbar statistik (n≥5). Endast titlar med data –
    // rapporten byggs ur matviews.
    orderCandidates = [{ slug: title.slug, title: title.title }];
    if (title.category) {
      const { data: siblings } = await supabaseAdmin
        .from("title_national_stats")
        .select("n, generalized_titles!inner(title, slug, category)")
        .eq("generalized_titles.category", title.category)
        .order("n", { ascending: false })
        .limit(12);

      for (const row of (siblings ?? []) as any[]) {
        const gt = row.generalized_titles;
        if (!gt || gt.slug === title.slug) continue;
        if (orderCandidates.some((c) => c.slug === gt.slug)) continue;
        orderCandidates.push({ slug: gt.slug, title: gt.title });
        if (orderCandidates.length >= 8) break;
      }
    }

    // Arbetsgivarlista för kommun/region-autocomplete (alla, klientfiltreras).
    const { data: empData } = await supabaseAdmin
      .from("employers")
      .select("id, name")
      .order("name", { ascending: true });
    allEmployers = (empData ?? []).map((e: any) => ({ id: e.id, name: e.name }));
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


  // Månadsintervall för källhänvisningens aggregerade rad (punkt 2)
  const sourceCitationRange = monthRange(
    sourceList.map((s) => s.received_at ?? s.salary_date),
  );

  // Lönespridning mellan arbetsgivarna i tabellen: skillnaden mellan högsta och
  // lägsta publicerade medianlön. Endast arbetsgivare med minst 20 anställda i
  // titeln räknas, så små underlag inte ger ett orimligt tal. Färre än 5
  // kvalificerade → ingen rad (medianSpread = null). Redovisas som skillnad,
  // aldrig som möjlighet.
  // Beräknas på samma underlag som tidigare (de 20 arbetsgivarna med störst
  // underlag) så rubrikvärdet är oförändrat trots att tabellen nu hämtar alla.
  const spreadQualified = employerList.slice(0, 20).filter(
    (e) => e.n >= 20 && e.median != null,
  );
  const medianSpread =
    spreadQualified.length >= 5
      ? Math.max(...spreadQualified.map((e) => e.median)) -
        Math.min(...spreadQualified.map((e) => e.median))
      : null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      {/* Brödsmula */}
      <nav className="text-sm text-gray-500 mb-4 break-words hyphens-auto">
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
      <h1 className="text-3xl font-bold tracking-tight mb-1 break-words hyphens-auto">{title.title}</h1>
      {title.category && (
        <p className="text-sm text-brand-mid mb-4">{title.category}</p>
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
                  Medianen av alla titlars medianer i kategorin. Överenskommen månadslön vid heltid.
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
                className="inline-block bg-brand text-white text-sm px-4 py-2 rounded-lg hover:opacity-90"
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
          <p className="text-sm text-gray-500 mb-2">
            Överenskommen månadslön vid heltid. Källa:{" "}
            {national.n.toLocaleString("sv-SE")} individer hos{" "}
            {sourceList.length} arbetsgivare.
          </p>

          {/* Datering (punkt 3) */}
          <p className="text-xs text-gray-500 mb-4">
            Statistiken bygger på 2024 års insamling. Nästa rikstäckande insamling
            inleds i augusti 2026.
          </p>

          {PROJECTION_ENABLED &&
            projectedSalary(national.median, title.category) != null && (
              <p className="text-xs text-gray-500 mb-3">
                Kolumner: <strong>2024 uppmätt</strong> /{" "}
                <span className="text-emerald-700">2026 uppskattad enligt centrala avtal</span>.
              </p>
            )}

          <DistributionBand
            p10={national.p10}
            p25={national.p25}
            median={national.median}
            p75={national.p75}
            p90={national.p90}
            showOwnSalary={false}
          />
          <p className="text-sm text-gray-600 mt-2">
            Medellön:{" "}
            <span className="tnum font-medium text-gray-900">
              {formatSalary(national.mean_salary)}
            </span>
          </p>
          {/* Täckningsredovisning – hur stor del av de utlämnade månadslönerna
              medianen vilar på. Visas alltid, även vid full täckning. */}
          <p className="text-xs text-gray-500 mt-1">
            {coverageNote(national.n, national.n_hourly)}
          </p>

          {/* Lönespridning som eget budskap direkt under grafen – sidans
              starkaste argument. Samma X (medianSpread) som i beställningsblockets
              värderad. Formulerad som skillnad, aldrig som möjlighet. */}
          {medianSpread != null && medianSpread > 0 && (
            <p className="font-serif text-xl sm:text-2xl leading-snug text-gray-900 max-w-2xl mt-7">
              Mellan kommunerna skiljer det{" "}
              <span className="text-accent-strong">
                {formatSalary(medianSpread)}
              </span>{" "}
              i månaden för {title.title} – samma yrke, olika arbetsgivare.{" "}
              Vet du var du ligger?
            </p>
          )}

          {/* Proveniens – flyttad till UNDER grafen (mindre text före grafen) */}
          <p className="border-l-[3px] border-brand pl-3 mt-6 text-sm text-gray-600 max-w-2xl">
            Faktiska, utbetalda löner – utlämnade av arbetsgivarna enligt
            offentlighetsprincipen, inte enkätsvar eller uppskattningar. Underlaget
            kommer från {sourceList.length} arbetsgivare
            {sourceCitationRange ? `, ${sourceCitationRange}` : ` ${year}`} och
            publiceras under utgivningsbevis nr 2024-077.
          </p>

          {/* Metodnot för uppräkning (punkt 4) – visas bara när flaggan är på */}
          {PROJECTION_ENABLED &&
            projectedSalary(national.median, title.category) != null && (
              <p className="text-xs text-gray-400 mt-3 max-w-2xl">
                {PROJECTION_METHOD_NOTE}
              </p>
            )}
        </section>
      )}

      {/* Beställ lönerapport – endast på sidor med publicerbar statistik */}
      {national && (
        <>
          <OrderReport
            defaultSlug={title.slug}
            defaultTitle={title.title}
            titleCandidates={orderCandidates}
            employers={allEmployers}
            paymentLogos={availablePaymentLogos()}
          />
        </>
      )}

      {/* Per arbetsgivare – dölj helt när ingen arbetsgivare når n>=5 (ingen
          median att visa). Då återstår bara n<5-rader utan lönevärden, vilket
          inte tillför något. Berör 595 titlar. */}
      {employerList.length > 0 && (
        <section className="mb-10">
          <h2 className="text-xl font-semibold mb-4">Per arbetsgivare</h2>
          {/* De 15 med flest anställda visas direkt; resten ligger kvar i DOM:en
              bakom en expander (indexerbara) + klientsidefilter. */}
          <EmployerTable
            full={employerList.map((e) => ({
              name: e.employer_name,
              n: e.n,
              median: formatSalary(e.median),
              mean: formatSalary(e.mean_salary),
            }))}
            small={smallEmployers.map((e) => ({
              name: e.employer_name,
              n: e.n,
            }))}
          />
          <p className="text-xs text-gray-400 mt-2">
            Lönesiffror visas endast för arbetsgivare med minst 5 anställda i denna
            titel. Arbetsgivare med färre visas med antal anställda men utan
            lönevärden.
          </p>
        </section>
      )}

      {/* Källhänvisning — hård regel: ska alltid visas */}
      <section className="border-t border-gray-100 pt-6 text-xs text-gray-500">
        <h3 className="font-medium text-gray-700 mb-2">Källhänvisning</h3>
        {sourceList.length > 0 ? (
          <>
            {/* Aggregerad rad (punkt 2) */}
            <p>
              Uppgifter utlämnade av <strong>{sourceList.length}</strong> arbetsgivare
              enligt offentlighetsprincipen
              {sourceCitationRange ? `, ${sourceCitationRange}` : ` ${year}`}.
            </p>
            {/* Utfällbar komplett lista */}
            <details className="mt-2">
              <summary className="cursor-pointer hover:text-gray-700">
                Visa fullständig lista över arbetsgivare ({sourceList.length})
              </summary>
              <ul className="mt-2 space-y-1 pl-1">
                {sourceList.map((s, i) => (
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
            </details>
          </>
        ) : (
          <p>
            Statistiken avser lönedata för år <strong>{year}</strong>, insamlad
            via offentlighetsprincipen.
          </p>
        )}
        <p className="mt-2">
          Individdata visas aldrig — aggregat kräver minst 5 individer.
        </p>
      </section>

      {/* B2B/bredare uttag – diskret rad längst ner, efter arbetsgivartabellen */}
      {national && <ContactLine />}
    </div>
  );
}
