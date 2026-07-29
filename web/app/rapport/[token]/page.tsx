// Tokenserad lönerapport. Token = access (ingen inloggning). Innehåll byggs
// ENBART ur matviews (n≥5). Ingen individdata. Print-CSS, utgångsdatum i mejlet.
//
// Produkt (99 kr): max 5 yrken × max 5 valda kommuner/regioner. Per yrke visas
// nationell spridning som referens + tabellrader ENDAST för de valda
// arbetsgivarna (n≥5-regeln oförändrad). Datainnehållet är oförändrat mot
// tidigare – detta är rendering/CSS.
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { supabaseAdmin } from "@/lib/supabase";
import { buildReport, type ReportTitle } from "@/lib/report";
import { METHOD_NOTE, coverageNote } from "@/lib/copy";
import Logo from "@/components/Logo"; // enda logokällan (inline, symbol + ordbild)
import DistributionBand from "@/components/DistributionBand";
import IndividualPlacement from "./IndividualPlacement";
import PrintButton from "./PrintButton";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Lönerapport",
  robots: { index: false, follow: false },
};

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

// Δ mot riksmedian i procent, som text.
function deltaText(value: number, median: number): string {
  if (!median) return "";
  const pct = Math.round(((value - median) / median) * 100);
  if (pct === 0) return "i nivå med mitten i landet";
  if (pct > 0) return `${pct} % över mitten i landet`;
  return `${Math.abs(pct)} % under mitten i landet`;
}

// ── Nyckeltalskort ───────────────────────────────────────────────────────────
function StatCard({
  label,
  value,
  caption,
  plate,
  valueClass = "text-gray-900",
}: {
  label: string;
  value: string;
  caption: string;
  plate: "blue" | "orange";
  valueClass?: string;
}) {
  const bg = plate === "orange" ? "bg-plate-orange" : "bg-plate-blue";
  return (
    <div className={`${bg} rounded-lg p-4 break-inside-avoid`}>
      <div className="text-xs text-gray-500 mb-1 truncate" title={label}>
        {label}
      </div>
      <div className={`tnum text-2xl font-semibold leading-tight ${valueClass}`}>
        {value}
      </div>
      <div className="text-[11px] text-gray-500 mt-1">{caption}</div>
    </div>
  );
}

// ── En titelsektion (≈ en utskriven sida) ────────────────────────────────────
function TitleSection({
  t,
  employerNames,
  pageBreak,
}: {
  t: ReportTitle;
  employerNames: string[];
  pageBreak: boolean;
}) {
  const n = t.national;
  // Primär kommun = den med störst underlag bland de valda (buildReport
  // sorterar n desc). Övriga hamnar i tabellen.
  const primary = t.employers[0] ?? null;

  // Primära kommunens placering bland samtliga arbetsgivare (n≥5) efter medianlön.
  // Löneoberoende aggregat – kundens egen lön ingår aldrig i denna beräkning.
  const kommunTotal = t.allEmployerMedians.length || null;
  const kommunRank = primary
    ? t.allEmployerMedians.filter((m) => m > primary.median).length + 1
    : null;

  // Underrad: valda kommuner/regioner för yrket (de med data först, annars val).
  const kommunLabel =
    (t.employers.length > 0
      ? t.employers.map((e) => e.employer_name)
      : employerNames
    ).join(", ") || "Hela landet";

  // Positionsnot
  let noteNeutral: string;
  let noteHighlight: string | null = null;
  if (primary && primary.median < n.p75) {
    noteNeutral =
      "Din valda kommun ligger under den övre fjärdedelen av lönespannet.";
    noteHighlight = "Där finns ditt förhandlingsutrymme.";
  } else if (primary) {
    noteNeutral =
      "Din valda kommun ligger redan i den övre fjärdedelen av lönespannet – ett starkt utgångsläge.";
  } else {
    noteNeutral =
      "Ingen av dina valda kommuner har minst 5 anställda i det här yrket, så jämförelsen bygger på hela landet.";
  }

  return (
    <section className={pageBreak ? "break-before-page pt-2" : ""}>
      {/* Kicker + titel + underrad */}
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent-strong">
        Lönerapport
      </p>
      <h2 className="font-serif text-[24px] leading-tight text-gray-900 mt-0.5">
        {t.title}
      </h2>
      <p className="text-sm text-gray-500 mt-1 mb-5">
        {kommunLabel} · 2024 års löner · heltidsekvivalent månadslön
      </p>

      {/* Tre nyckeltalskort */}
      <div className="grid gap-3 sm:grid-cols-3 mb-6 break-inside-avoid">
        <StatCard
          label="Mitten i landet"
          value={formatSalary(n.median)}
          caption="median · hela landet"
          plate="blue"
        />
        {primary ? (
          <StatCard
            label={primary.employer_name}
            value={formatSalary(primary.median)}
            caption={deltaText(primary.median, n.median)}
            plate="orange"
            valueClass="text-accent-strong"
          />
        ) : (
          <StatCard
            label="Dina valda kommuner"
            value="–"
            caption="ingen med minst 5 anställda i yrket"
            plate="orange"
          />
        )}
        <StatCard
          label="Ett rimligt mål"
          value={formatSalary(n.p75)}
          caption="var fjärde tjänar mer än så"
          plate="blue"
        />
      </div>

      {/* Spridningsband */}
      <DistributionBand
        p10={n.p10}
        p25={n.p25}
        median={n.median}
        p75={n.p75}
        p90={n.p90}
      />

      {/* Täckningsredovisning – samma rad som på yrkessidan (lib/copy.ts) */}
      <p className="text-xs text-gray-500 text-center mt-2">
        {coverageNote(n.n, n.n_raw)}
      </p>

      {/* Positionsnot */}
      <p className="font-serif italic text-gray-600 text-center max-w-[460px] mx-auto my-6">
        {noteNeutral}
        {noteHighlight && (
          <>
            {" "}
            <span className="underline decoration-accent-strong decoration-2 underline-offset-4">
              {noteHighlight}
            </span>
          </>
        )}
      </p>

      {/* Tabell med bokrygglinjer */}
      <table className="w-full text-sm border-collapse mb-1 break-inside-avoid">
        <thead>
          <tr className="text-left text-gray-500">
            <th
              className="pb-1.5 pr-4 font-medium"
              style={{ borderTop: "1.5px solid #13201F" }}
            >
              Arbetsgivare
            </th>
            <th
              className="pb-1.5 pr-4 font-medium text-right"
              style={{ borderTop: "1.5px solid #13201F" }}
            >
              Anställda
            </th>
            <th
              className="pb-1.5 pr-4 font-medium text-right"
              style={{ borderTop: "1.5px solid #13201F" }}
            >
              Median
            </th>
            <th
              className="pb-1.5 font-medium text-right"
              style={{ borderTop: "1.5px solid #13201F" }}
            >
              Medellön
            </th>
          </tr>
        </thead>
        <tbody>
          {t.employers.map((e) => (
            <tr key={e.employer_name} style={{ borderBottom: "0.5px solid #DAE3E4" }}>
              <td className="py-1.5 pr-4 pt-2.5">{e.employer_name}</td>
              <td className="tnum py-1.5 pr-4 text-right text-gray-500">{e.n}</td>
              <td
                className="tnum py-1.5 pr-4 text-right font-medium"
                style={{ color: "#0F5563" }}
              >
                {formatSalary(e.median)}
              </td>
              <td className="tnum py-1.5 text-right text-gray-600">
                {formatSalary(e.mean_salary)}
              </td>
            </tr>
          ))}
          {/* Referensrad: hela landet */}
          <tr
            className="italic text-gray-500"
            style={{ borderBottom: "1.5px solid #13201F" }}
          >
            <td className="py-1.5 pr-4">Hela landet, referens</td>
            <td className="tnum py-1.5 pr-4 text-right">
              {n.n.toLocaleString("sv-SE")}
            </td>
            <td className="tnum py-1.5 pr-4 text-right">{formatSalary(n.median)}</td>
            <td className="tnum py-1.5 text-right">{formatSalary(n.mean_salary)}</td>
          </tr>
        </tbody>
      </table>
      {t.emptyEmployers.length > 0 && (
        <p className="text-xs text-gray-400 mb-2">
          Utan publicerbart underlag för detta yrke (färre än 5 anställda):{" "}
          {t.emptyEmployers.join(", ")}.
        </p>
      )}

      {/* Individualiserad placering – renderas ENDAST om kunden angav en egen lön
          (läses klientsidan ur sessionStorage; når aldrig servern/databasen). */}
      <IndividualPlacement
        title={t.title}
        p10={n.p10}
        p25={n.p25}
        median={n.median}
        p75={n.p75}
        p90={n.p90}
        kommunName={primary?.employer_name ?? null}
        kommunMedian={primary?.median ?? null}
        kommunRank={kommunRank}
        kommunTotal={kommunTotal}
      />

      {/* Inför din löneförhandling */}
      <div className="border-l-[3px] border-brand pl-4 my-6 break-inside-avoid">
        <h3 className="text-sm font-semibold text-gray-900 mb-1">
          Inför din löneförhandling
        </h3>
        <p className="text-sm text-gray-700 leading-relaxed max-w-2xl">
          Utgå från mitten – <span className="tnum">{formatSalary(n.median)}</span>{" "}
          är varken golv eller tak, det är utgångsläget. Med erfarenhet eller
          utökat ansvar är <span className="tnum">{formatSalary(n.p75)}</span> ett
          rimligt mål att sätta. Och kom ihåg: det här är faktiska utbetalda löner
          enligt offentlighetsprincipen, inte enkätsvar.
        </p>
      </div>

      {/* Källhänvisning per titel */}
      <p className="text-xs text-gray-400 mt-4">
        Källa: uppgifter utlämnade enligt offentlighetsprincipen,{" "}
        {n.collection_year}. {t.nationalSourceCount} arbetsgivare lämnade
        uppgifter för yrket och ligger bakom de nationella siffrorna. Tabellen
        ovan visar bara de arbetsgivare som har minst 5 anställda i yrket.
      </p>
    </section>
  );
}

// ── Sida ─────────────────────────────────────────────────────────────────────
export default async function RapportSida({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;

  const { data: purchase } = await supabaseAdmin
    .from("purchases")
    .select(
      "report_token, selected_slugs, selected_employers, status, expires_at, created_at",
    )
    .eq("report_token", token)
    .maybeSingle();

  if (!purchase || purchase.status !== "paid") notFound();

  const expiresAt = purchase.expires_at ? new Date(purchase.expires_at) : null;
  const expired = expiresAt != null && expiresAt.getTime() < Date.now();

  if (expired) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16">
        <h1 className="font-serif text-2xl text-gray-900 mb-3">
          Rapporten har gått ut
        </h1>
        <p className="text-gray-600 mb-6">
          Den här rapportlänken var giltig t.o.m.{" "}
          <strong>{formatDate(purchase.expires_at)}</strong> och kan inte längre
          visas. Rapporter är giltiga i tre månader från köptillfället.
        </p>
        <a
          href="/"
          className="inline-block bg-brand text-white text-sm px-4 py-2 rounded-lg hover:opacity-90"
        >
          Till startsidan
        </a>
      </div>
    );
  }

  const slugs = (purchase.selected_slugs as string[] | null) ?? [];
  const employerIds = (purchase.selected_employers as number[] | null) ?? [];
  const { titles, employerNames } = await buildReport(slugs, employerIds);

  return (
    <div className="report-root max-w-3xl mx-auto px-4 py-8">
      {/* Skriv ut (döljs i tryck) */}
      <div className="print:hidden flex justify-end mb-3">
        <PrintButton />
      </div>

      {/* Dokumenthuvud */}
      <header className="flex items-end justify-between gap-4 pb-3 border-b border-gray-900">
        <Logo className="h-7 w-auto" />
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wide text-gray-400">
            Rapportdatum
          </div>
          <div className="tnum text-sm text-gray-800">
            {formatDate(purchase.created_at)}
          </div>
        </div>
      </header>

      {titles.length === 0 ? (
        <div className="bg-plate-orange border border-accent/40 rounded-lg p-5 text-sm text-accent-dark mt-8">
          Det finns för närvarande ingen publicerbar lönestatistik för de valda
          yrkena (minst 5 individer krävs). Kontakta oss om du tror att detta är
          fel.
        </div>
      ) : (
        <div className="mt-8 space-y-10">
          {titles.map((t, i) => (
            <TitleSection
              key={t.slug}
              t={t}
              employerNames={employerNames}
              pageBreak={i > 0}
            />
          ))}
        </div>
      )}

      {/* Metod och källa (skärm) */}
      <section className="border-t border-gray-200 pt-6 mt-10 text-xs text-gray-500 space-y-2 break-inside-avoid">
        <h3 className="font-medium text-gray-700">Metod och källa</h3>
        {METHOD_NOTE.map((para, i) => (
          <p key={i}>{para}</p>
        ))}
        <p className="pt-2 text-gray-400">
          Offentliga löner, offentligaloner.se · Tillhandahållare och ansvarig
          utgivare: Patrik Larsson · Utgivningsbevis nr 2024-077 (Mediemyndigheten).
        </p>
      </section>

      {/* Sidfot vid UTSKRIFT – upprepas på varje sida (position: fixed).
          Källa + n≥5 + utgivningsbevis enligt beställningen. */}
      <footer className="hidden print:block fixed inset-x-0 bottom-0 text-[9px] text-gray-500 px-[14mm] pb-2 leading-tight">
        Källa: uppgifter utlämnade enligt offentlighetsprincipen · Endast aggregat
        med minst 5 individer visas · Offentliga löner, offentligaloner.se ·
        Utgivningsbevis nr 2024-077 (Mediemyndigheten)
      </footer>
    </div>
  );
}
