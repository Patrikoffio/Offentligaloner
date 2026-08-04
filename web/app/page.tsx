import type { Metadata } from "next";
import { supabaseAdmin } from "@/lib/supabase";
import HomeTop from "./HomeTop";

// Kanonisk URL för startsidan (metadataBase gör den absolut: https://
// offentligaloner.se/). Titel/beskrivning ärvs från layout.
export const metadata: Metadata = {
  alternates: { canonical: "/" },
  openGraph: { url: "/" },
};

export default async function Home() {
  // Nyckeltal ur datan (live) + två topplistor. "Högst lön" kräver n>=100 så
  // den inte fylls av småyrken med tunt underlag. Samma n>=100-underlag används
  // även för "flest anställda" (topptitlarna har stora n).
  const [salaries, employers, titles, highNRes] = await Promise.all([
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
      .gte("n", 100)
      .order("n", { ascending: false })
      .limit(1000),
  ]);

  const highN = (highNRes.data ?? []).filter((r: any) => r.generalized_titles);
  const mostCommon = [...highN].sort((a: any, b: any) => b.n - a.n).slice(0, 5);
  const highestPay = [...highN]
    .sort((a: any, b: any) => b.median - a.median)
    .slice(0, 5);

  return (
    <HomeTop
      count_salaries={salaries.count ?? 534293}
      count_employers={employers.count ?? 156}
      count_titles={titles.count ?? 2378}
      mostCommon={mostCommon}
      highestPay={highestPay}
    />
  );
}
