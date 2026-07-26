"use client";

// Arbetsgivartabell på yrkessidan.
//  1. De 15 arbetsgivarna med flest anställda visas direkt.
//  2. Resten ligger KVAR i DOM:en men döljs via CSS (klassen "hidden") tills
//     expandern öppnas – de renderas server-side (SSG) och är därför indexerbara,
//     de laddas aldrig via JS.
//  3. Filterfältet filtrerar klientsidan (ingen serverrundtur); en träff visas
//     även om den ligger i den hopfällda delen.
// n<5-raderna och deras regel är oförändrade – de renderas som förut, utan
// lönevärden, och räknas in i totalen först efter n≥5-arbetsgivarna.

import { useState } from "react";

const VISIBLE = 15;

export interface FullRow {
  name: string;
  n: number;
  median: string; // förformaterad server-side
  mean: string;
}
export interface SmallRow {
  name: string;
  n: number;
}

export default function EmployerTable({
  full,
  small,
}: {
  full: FullRow[];
  small: SmallRow[];
}) {
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState(false);

  const q = query.trim().toLowerCase();
  const filtering = q.length > 0;
  const total = full.length + small.length;
  const hasExtra = total > VISIBLE;

  // Global ordning: n≥5 (fallande) följt av n<5 (fallande) = flest anställda först.
  const rows = [
    ...full.map((r) => ({ kind: "full" as const, r })),
    ...small.map((r) => ({ kind: "small" as const, r })),
  ];

  const matches = (name: string) => !filtering || name.toLowerCase().includes(q);
  const matchCount = filtering
    ? rows.filter((x) => matches(x.r.name)).length
    : rows.length;

  // Dold om: vid filtrering styr träffen (expandern ignoreras); annars visas de
  // 15 första och resten bara när expandern är öppen.
  const isHidden = (i: number, name: string) =>
    filtering ? !matches(name) : !(i < VISIBLE || expanded);

  return (
    <>
      {/* Filter – klientsidan, ingen serverrundtur */}
      <div className="mb-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Sök kommun eller region"
          aria-label="Sök kommun eller region"
          className="w-full sm:w-72 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
        />
      </div>

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
            {rows.map((x, i) =>
              x.kind === "full" ? (
                <tr
                  key={`full-${x.r.name}`}
                  className={`border-b border-gray-100 hover:bg-gray-50${
                    isHidden(i, x.r.name) ? " hidden" : ""
                  }`}
                >
                  <td className="py-2 pr-4">{x.r.name}</td>
                  <td className="py-2 pr-4 text-right text-gray-500">{x.r.n}</td>
                  <td className="py-2 pr-4 text-right font-medium">{x.r.median}</td>
                  <td className="py-2 text-right text-gray-600">{x.r.mean}</td>
                </tr>
              ) : (
                <tr
                  key={`small-${x.r.name}`}
                  className={`border-b border-gray-100 text-gray-400${
                    isHidden(i, x.r.name) ? " hidden" : ""
                  }`}
                >
                  <td className="py-2 pr-4">{x.r.name}</td>
                  <td className="py-2 pr-4 text-right">{x.r.n}</td>
                  <td className="py-2 text-right italic" colSpan={2}>
                    Underlag för litet för lönestatistik
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </div>

      {filtering && matchCount === 0 && (
        <p className="text-sm text-gray-500 mt-2">
          Ingen arbetsgivare matchar ”{query.trim()}”.
        </p>
      )}

      {/* Expander – döljs vid filtrering (då visas alla träffar oavsett). */}
      {hasExtra && !filtering && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          className="mt-3 text-sm text-brand-mid hover:text-brand-dark hover:underline"
        >
          {expanded ? "Visa färre" : `Visa alla ${total} arbetsgivare`}
        </button>
      )}
    </>
  );
}
