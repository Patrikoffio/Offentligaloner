// Tokenserad lönerapport. Token = access (ingen inloggning). Innehåll byggs
// ENBART ur matviews (n≥5). Ingen individdata. Utgångsdatum synligt, print-CSS.
//
// Produkt (39 kr): max 5 yrken × max 5 valda kommuner/regioner. Per yrke visas
// nationell spridning som referens + tabellrader ENDAST för de valda
// arbetsgivarna (n≥5-regeln oförändrad).
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { supabaseAdmin } from "@/lib/supabase";
import { buildReport, type ReportTitle } from "@/lib/report";
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

// ── En titelsektion ──────────────────────────────────────────────────────────
function TitleSection({ t }: { t: ReportTitle }) {
  const n = t.national;
  const dist = [
    { label: "10:e percentilen", value: n.p10 },
    { label: "25:e percentilen", value: n.p25 },
    { label: "Median", value: n.median, highlight: true },
    { label: "75:e percentilen", value: n.p75 },
    { label: "90:e percentilen", value: n.p90 },
    { label: "Medellön", value: n.mean_salary },
  ];
  const maxVal = n.p90 || 1;

  return (
    <section className="mb-10 break-inside-avoid">
      <h2 className="text-xl font-semibold border-b border-gray-200 pb-1 mb-3">
        {t.title}
        {t.category && (
          <span className="ml-2 text-sm font-normal text-gray-500">{t.category}</span>
        )}
      </h2>

      {/* Nationell spridning – referens (hela landet) */}
      <h3 className="text-sm font-semibold text-gray-700 mb-1">
        Nationell lönespridning (referens)
      </h3>
      <p className="text-xs text-gray-500 mb-3">
        Hela landet, {n.n.toLocaleString("sv-SE")} anställda hos {t.nationalSourceCount}{" "}
        arbetsgivare. Heltidsekvivalent månadslön, {n.collection_year}.
      </p>
      <div className="space-y-2 mb-6">
        {dist.map(({ label, value, highlight }) => (
          <div key={label} className="flex items-center gap-3">
            <span
              className={`w-40 text-sm text-right shrink-0 ${
                highlight ? "font-semibold" : "text-gray-600"
              }`}
            >
              {label}
            </span>
            <div className="flex-1 bg-gray-100 rounded-full h-4 relative print:border print:border-gray-300">
              <div
                className={`h-4 rounded-full ${highlight ? "bg-blue-500" : "bg-blue-300"}`}
                style={{ width: `${Math.round((value / maxVal) * 100)}%` }}
              />
            </div>
            <span
              className={`w-24 text-sm ${highlight ? "font-semibold" : "text-gray-700"}`}
            >
              {formatSalary(value)}
            </span>
          </div>
        ))}
      </div>

      {/* Dina valda arbetsgivare (n≥5) */}
      <h3 className="text-sm font-semibold text-gray-700 mb-2">
        Dina valda kommuner/regioner
      </h3>
      {t.employers.length > 0 ? (
        <table className="w-full text-sm border-collapse mb-2">
          <thead>
            <tr className="border-b border-gray-200 text-left text-gray-500">
              <th className="pb-1 pr-4 font-medium">Arbetsgivare</th>
              <th className="pb-1 pr-4 font-medium text-right">Antal</th>
              <th className="pb-1 pr-4 font-medium text-right">Median</th>
              <th className="pb-1 font-medium text-right">Medellön</th>
            </tr>
          </thead>
          <tbody>
            {t.employers.map((e) => (
              <tr key={e.employer_name} className="border-b border-gray-100">
                <td className="py-1 pr-4">{e.employer_name}</td>
                <td className="py-1 pr-4 text-right text-gray-500">{e.n}</td>
                <td className="py-1 pr-4 text-right font-medium">{formatSalary(e.median)}</td>
                <td className="py-1 text-right text-gray-600">{formatSalary(e.mean_salary)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="text-sm text-gray-500 mb-2">
          Ingen av dina valda arbetsgivare har minst 5 anställda med titeln{" "}
          {t.title.toLowerCase()} – därför visas ingen lönestatistik per arbetsgivare
          här. Den nationella spridningen ovan gäller som referens.
        </p>
      )}
      {t.emptyEmployers.length > 0 && t.employers.length > 0 && (
        <p className="text-xs text-gray-400 mb-2">
          Utan publicerbart underlag för detta yrke (färre än 5 anställda):{" "}
          {t.emptyEmployers.join(", ")}.
        </p>
      )}

      {/* Källhänvisning per titel */}
      <p className="text-xs text-gray-500">
        Källa: uppgifter utlämnade enligt offentlighetsprincipen. Nationell spridning
        bygger på samtliga {t.nationalSourceCount} arbetsgivare som lämnat ut uppgifter
        för yrket {n.collection_year}; arbetsgivartabellen visar dina valda
        arbetsgivare med minst 5 anställda.
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
    .select("report_token, selected_slugs, selected_employers, status, expires_at, created_at")
    .eq("report_token", token)
    .maybeSingle();

  if (!purchase || purchase.status !== "paid") notFound();

  const expiresAt = purchase.expires_at ? new Date(purchase.expires_at) : null;
  const expired = expiresAt != null && expiresAt.getTime() < Date.now();

  if (expired) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16">
        <h1 className="text-2xl font-bold mb-3">Rapporten har gått ut</h1>
        <p className="text-gray-600 mb-6">
          Den här rapportlänken var giltig t.o.m.{" "}
          <strong>{formatDate(purchase.expires_at)}</strong> och kan inte längre visas.
          Rapporter är giltiga i tre månader från köptillfället.
        </p>
        <a href="/" className="inline-block bg-blue-600 text-white text-sm px-4 py-2 rounded hover:bg-blue-700">
          Till startsidan
        </a>
      </div>
    );
  }

  const slugs = (purchase.selected_slugs as string[] | null) ?? [];
  const employerIds = (purchase.selected_employers as number[] | null) ?? [];
  const { titles, employerNames } = await buildReport(slugs, employerIds);

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      {/* Sidhuvud */}
      <div className="flex items-start justify-between gap-4 mb-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-400">Lönerapport</p>
          <h1 className="text-2xl font-bold">Offentliga löner</h1>
        </div>
        <PrintButton />
      </div>

      {employerNames.length > 0 && (
        <p className="text-sm text-gray-600 mb-1">
          Valda kommuner/regioner: <strong>{employerNames.join(", ")}</strong>.
        </p>
      )}
      <p className="text-sm text-gray-500 mb-1">
        Skapad {formatDate(purchase.created_at)}. Giltig t.o.m.{" "}
        <strong>{formatDate(purchase.expires_at)}</strong>.
      </p>
      <p className="text-xs text-gray-400 mb-8">
        Spara länken – den fungerar utan inloggning under giltighetstiden.
      </p>

      {titles.length === 0 ? (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-5 text-sm text-amber-800">
          Det finns för närvarande ingen publicerbar lönestatistik för de valda
          yrkena (minst 5 individer krävs). Kontakta oss om du tror att detta är fel.
        </div>
      ) : (
        titles.map((t) => <TitleSection key={t.slug} t={t} />)
      )}

      {/* Metodnot */}
      <section className="border-t border-gray-200 pt-6 mt-4 text-xs text-gray-500 space-y-2 break-inside-avoid">
        <h3 className="font-medium text-gray-700">Metod och källa</h3>
        <p>
          Uppgifterna är inhämtade via offentlighetsprincipen från kommuner och
          regioner och avser 2024 års löner. Lönerna är omräknade till
          heltidsekvivalent månadslön. Statistik visas endast när minst 5 individer
          har samma titel hos samma arbetsgivare respektive nationellt –
          individuella löner publiceras aldrig.
        </p>
        <p>
          Median = mittenvärdet. Percentiler anger spridningen: 10:e percentilen är
          den nivå som 10 % tjänar under, 90:e den nivå som 10 % tjänar över.
        </p>
        <p className="pt-2 text-gray-400">
          Offentliga löner, offentligaloner.se · Tillhandahållare och ansvarig
          utgivare: Patrik Larsson · Utgivningsbevis nr 2024-077 (Mediemyndigheten).
        </p>
      </section>
    </div>
  );
}
