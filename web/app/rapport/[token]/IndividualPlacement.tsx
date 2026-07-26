"use client";

// Individualiserad placering i lönerapporten.
//
// DATASKYDD: den lön kunden anger skickas ALDRIG till servern och sparas ALDRIG
// i någon databas. Den skrivs av beställningsformuläret till sessionStorage och
// läses HÄR, i webbläsaren, enbart för att räkna fram placeringen nedan. Alla
// beräkningar sker klientsidan; servern får aldrig se värdet. Rangordningen av
// vald kommun (kommunRank/kommunTotal) är löneoberoende aggregat som räknas
// serversidan – kundens lön ingår inte i den.
//
// Ton: KONSTATERANDE, aldrig rekommendation. Ingen text om vad kunden "bör"
// begära – det tillhör en dyrare produkt.

import { useEffect, useState } from "react";

const STORAGE_KEY = "offlon:egen_lon";

function fmt(n: number): string {
  return Math.round(n).toLocaleString("sv-SE") + " kr";
}

// Svensk ordinal: 1:a, 2:a, annars n:e.
function ord(n: number): string {
  return n === 1 ? "1:a" : n === 2 ? "2:a" : `${n}:e`;
}

// Uppskatta percentil ur de fem publicerade percentilpunkterna (styckvis linjärt).
function estPercentile(
  s: number,
  pts: { v: number; p: number }[],
): { pct: number; bound: "below" | "above" | "mid" } {
  if (s <= pts[0].v) return { pct: pts[0].p, bound: "below" };
  const last = pts[pts.length - 1];
  if (s >= last.v) return { pct: last.p, bound: "above" };
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i];
    const b = pts[i + 1];
    if (s >= a.v && s <= b.v) {
      const frac = b.v === a.v ? 0 : (s - a.v) / (b.v - a.v);
      return { pct: Math.round(a.p + frac * (b.p - a.p)), bound: "mid" };
    }
  }
  return { pct: 50, bound: "mid" };
}

export default function IndividualPlacement({
  title,
  p10,
  p25,
  median,
  p75,
  p90,
  kommunName,
  kommunMedian,
  kommunRank,
  kommunTotal,
}: {
  title: string;
  p10: number;
  p25: number;
  median: number;
  p75: number;
  p90: number;
  kommunName: string | null;
  kommunMedian: number | null;
  kommunRank: number | null;
  kommunTotal: number | null;
}) {
  // Läs enbart klientsidan (undviker hydration-mismatch); värdet finns bara här.
  const [salary, setSalary] = useState<number | null>(null);
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      const n = raw ? Number(raw.replace(/\D/g, "")) : NaN;
      setSalary(Number.isFinite(n) && n > 0 ? n : null);
    } catch {
      setSalary(null);
    }
  }, []);

  if (salary == null) return null;

  const pts = [
    { v: p10, p: 10 },
    { v: p25, p: 25 },
    { v: median, p: 50 },
    { v: p75, p: 75 },
    { v: p90, p: 90 },
  ];
  const { pct, bound } = estPercentile(salary, pts);

  // Placering nationellt (konstaterande).
  const nationalLine =
    bound === "below"
      ? `Din lön ligger under den 10:e percentilen nationellt för ${title}.`
      : bound === "above"
        ? `Din lön ligger över den 90:e percentilen nationellt för ${title}.`
        : `Din lön motsvarar ungefär den ${ord(pct)} percentilen nationellt för ${title} – omkring ${pct} % tjänar mindre.`;

  // I förhållande till vald kommuns median, i kronor.
  let kommunLine: string | null = null;
  if (kommunName && kommunMedian != null) {
    const d = salary - kommunMedian;
    if (d > 0)
      kommunLine = `Det är ${fmt(d)} mer än medianen i ${kommunName} (${fmt(kommunMedian)}).`;
    else if (d < 0)
      kommunLine = `Det är ${fmt(-d)} mindre än medianen i ${kommunName} (${fmt(kommunMedian)}).`;
    else
      kommunLine = `Det är i nivå med medianen i ${kommunName} (${fmt(kommunMedian)}).`;
  }

  // Kommunens placering bland samtliga arbetsgivare (löneoberoende fakta).
  const rankLine =
    kommunName && kommunRank != null && kommunTotal != null && kommunTotal > 0
      ? `${kommunName} har den ${ord(kommunRank)} högsta medianlönen av ${kommunTotal} arbetsgivare som redovisat ${title}.`
      : null;

  // Över medianen: säg det rakt ut, utan säljande vinkling. Under: ingen extra rad.
  const aboveMedianLine =
    salary > median
      ? `Du ligger över riksmedianen för ${title} (${fmt(median)}).`
      : null;

  return (
    <div className="border-l-[3px] border-brand pl-4 my-6 break-inside-avoid">
      <h3 className="text-sm font-semibold text-gray-900 mb-1">Din placering</h3>
      <p className="text-xs text-gray-500 mb-2">
        Utifrån lönen du angav ({fmt(salary)}), jämförd med {title} i hela landet
        {kommunName ? ` och i ${kommunName}` : ""}.
      </p>
      <ul className="text-sm text-gray-700 leading-relaxed max-w-2xl space-y-1 list-disc pl-5">
        <li>{nationalLine}</li>
        {kommunLine && <li>{kommunLine}</li>}
        {rankLine && <li>{rankLine}</li>}
        {aboveMedianLine && <li>{aboveMedianLine}</li>}
      </ul>
      <p className="text-[11px] text-gray-400 mt-3 max-w-2xl">
        Lönen du angav skickas aldrig till våra servrar och sparas inte i någon
        databas. Den finns bara i din webbläsare medan du har rapporten öppen och
        används enbart för placeringen ovan.
      </p>
    </div>
  );
}
