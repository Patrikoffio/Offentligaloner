import type { Metadata } from "next";
import { supabaseAdmin } from "@/lib/supabase";
import Link from "next/link";
import HomeTop from "./HomeTop";
import { availablePaymentLogos } from "@/lib/paymentLogos";

// Kanonisk URL för startsidan (metadataBase gör den absolut: https://
// offentligaloner.se/). Titel/beskrivning ärvs från layout.
export const metadata: Metadata = {
  alternates: { canonical: "/" },
  openGraph: { url: "/" },
};

function formatSalary(n: number | null): string {
  if (n == null) return "–";
  return Math.round(n).toLocaleString("sv-SE") + " kr";
}

export default async function Home() {
  // Nyckeltal ur datan (live) + vanligaste yrkena.
  const [salaries, employers, titles, topRes] = await Promise.all([
    supabaseAdmin
      .from("salary_records")
      .select("*", { count: "exact", head: true }),
    supabaseAdmin.from("employers").select("*", { count: "exact", head: true }),
    supabaseAdmin
      .from("title_national_stats")
      .select("*", { count: "exact", head: true })
      .gte("n", 5),
    supabaseAdmin
      .from("title_national_stats")
      .select("n, median, generalized_titles(title, slug)")
      .gte("n", 5)
      .order("n", { ascending: false })
      .limit(12),
  ]);

  const topTitles = topRes.data ?? [];

  return (
    <div>
      <HomeTop
        count_salaries={salaries.count ?? 534293}
        count_employers={employers.count ?? 156}
        count_titles={titles.count ?? 2151}
        paymentLogos={availablePaymentLogos()}
      />

      {/* Vanligaste yrkena */}
      <section className="max-w-3xl mx-auto px-4 pb-16">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          Vanligaste yrkena
        </h2>
        <ul>
          {topTitles.map((row: any) => {
            const t = row.generalized_titles;
            if (!t) return null;
            return (
              <li key={t.slug} className="border-b border-gray-100">
                <Link
                  href={`/yrken/${t.slug}`}
                  className="flex flex-col gap-0.5 py-3 group sm:flex-row sm:items-center sm:justify-between sm:gap-4"
                >
                  <span className="text-brand-mid group-hover:underline font-medium break-words min-w-0">
                    {t.title}
                  </span>
                  <span className="tnum text-sm text-gray-500 shrink-0">
                    median {formatSalary(row.median)} ·{" "}
                    {row.n.toLocaleString("sv-SE")} anställda
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
        <p className="mt-4 text-sm">
          <Link href="/#sok" className="text-brand-mid hover:underline">
            Sök bland alla yrkestitlar →
          </Link>
        </p>
      </section>
    </div>
  );
}
