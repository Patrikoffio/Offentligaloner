import { supabaseAdmin } from "@/lib/supabase";
import Link from "next/link";

export default async function Home() {
  const { data: topTitles } = await supabaseAdmin
    .from("title_national_stats")
    .select("n, generalized_titles(title, slug, category)")
    .gte("n", 5)
    .order("n", { ascending: false })
    .limit(20);

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">Offentliga löner</h1>
      <p className="text-gray-600 mb-8 max-w-xl">
        Lönestatistik för kommuner och regioner i Sverige, insamlad via
        offentlighetsprincipen. Data avser 2024.
      </p>

      <h2 className="text-lg font-semibold mb-4">Vanligaste yrkena</h2>
      <ul className="divide-y divide-gray-100">
        {(topTitles ?? []).map((row: any) => {
          const t = row.generalized_titles;
          if (!t) return null;
          return (
            <li key={t.slug}>
              <Link
                href={`/yrken/${t.slug}`}
                className="flex items-center justify-between py-3 hover:bg-gray-50 px-2 -mx-2 rounded"
              >
                <span className="font-medium">{t.title}</span>
                <span className="text-sm text-gray-400">
                  {row.n.toLocaleString("sv-SE")} anställda
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
