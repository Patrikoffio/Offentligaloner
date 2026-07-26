"use client";

// Förhandsvisning av spridningsbandet (punkt A3): mata in en lön och se
// hero-markören röra sig på skalan. Skriver sessionStorage (offlon:egen_lon)
// + skickar custom-event så DistributionBand uppdaterar live. Endast intern
// granskning – sidan är noindex (se page.tsx). Exempeldata, inte en riktig rapport.

import { useEffect, useState } from "react";
import DistributionBand from "@/components/DistributionBand";

const SAMPLE = { p10: 28000, p25: 31500, median: 34000, p75: 37500, p90: 43000 };

function apply(v: number | null) {
  try {
    if (v && v > 0) sessionStorage.setItem("offlon:egen_lon", String(v));
    else sessionStorage.removeItem("offlon:egen_lon");
  } catch {
    /* saknas sessionStorage – markören utelämnas då bara */
  }
  window.dispatchEvent(new Event("offlon:egen-lon"));
}

export default function BandPreview() {
  const [lon, setLon] = useState(35000);
  useEffect(() => {
    apply(lon);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const set = (v: number | null) => {
    setLon(v ?? 0);
    apply(v);
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="font-serif text-2xl text-gray-900 mb-1">
        Förhandsvisning – spridningsband
      </h1>
      <p className="text-sm text-gray-500 mb-6">
        Exempeldata. Dra i reglaget eller skriv en lön – hero-markören ska vara
        den mest framträdande, medianen ett tickmärke, kommunringen sekundär.
      </p>

      <div className="flex flex-wrap items-center gap-3 mb-2">
        <input
          type="range"
          min={20000}
          max={50000}
          step={100}
          value={lon}
          onChange={(e) => set(Number(e.target.value))}
          className="flex-1 min-w-[200px] accent-brand"
          aria-label="Din lön (reglage)"
        />
        <input
          type="number"
          value={lon || ""}
          onChange={(e) => set(e.target.value ? Number(e.target.value) : null)}
          className="w-28 border border-gray-300 rounded px-2 py-1 text-sm tnum"
          aria-label="Din lön (kr)"
        />
        <span className="text-sm text-gray-500">kr/mån</span>
        <button
          type="button"
          onClick={() => set(null)}
          className="text-sm text-brand-mid hover:text-brand-dark hover:underline"
        >
          Rensa (dölj markören)
        </button>
      </div>

      <p className="text-xs text-gray-400 mb-6">
        Skala: {SAMPLE.p10.toLocaleString("sv-SE")}–
        {SAMPLE.p90.toLocaleString("sv-SE")} kr (± marginal). Prova värden under
        p10 och över p90 för att se kantklampningen.
      </p>

      <DistributionBand
        p10={SAMPLE.p10}
        p25={SAMPLE.p25}
        median={SAMPLE.median}
        p75={SAMPLE.p75}
        p90={SAMPLE.p90}
      />
    </div>
  );
}
