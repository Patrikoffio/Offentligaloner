"use client";

// Spridningsband för lönerapporten.
//
// Hierarki (punkt A3): ANVÄNDARENS EGNA LÖN är den mest framträdande markören.
// Medianen är ett tickmärke. Kommunens median visas INTE på bandet (den finns i
// nyckeltalskortet + arbetsgivartabellen; en omärkt ring gick inte att tolka).
//   ▸ ljus teal-band   = 10:e–90:e percentilen
//   ▸ primär teal-band = 25:e–75:e percentilen
//   ▸ median           = tunt tickmärke
//   ▸ DIN LÖN          = kraftig linje + fylld etikett (hero), klientsidan
//
// DATASKYDD: din lön läses ENBART klientsidan ur sessionStorage (offlon:egen_lon)
// och skickas aldrig till servern. Bandets bas är serverrenderad; egna-lön-
// markören dyker upp efter hydrering (och i utskrift, sidan är laddad då).
// Custom-eventet "offlon:egen-lon" låter förhandsvisningen uppdatera live.

import { useEffect, useState } from "react";

interface Props {
  p10: number;
  p25: number;
  median: number;
  p75: number;
  p90: number;
  showOwnSalary?: boolean; // false på fria yrkessidan (ingen inmatad lön)
}

const STORAGE_KEY = "offlon:egen_lon";
const CENTER = 96; // bandets mittlinje (px från containerns topp)
const HEIGHT = 188;

function fmt(n: number): string {
  return Math.round(n).toLocaleString("sv-SE") + " kr";
}

// Kantmedveten horisontell justering: förankra vid x men undvik att svämma ut.
function edgeTransform(x: number): string {
  return x < 15 ? "translateX(0)" : x > 85 ? "translateX(-100%)" : "translateX(-50%)";
}

export default function DistributionBand({
  p10,
  p25,
  median,
  p75,
  p90,
  showOwnSalary = true,
}: Props) {
  // Egen lön – klientsidan. Läs vid mount + lyssna på custom-event (förhandsvisning).
  const [salary, setSalary] = useState<number | null>(null);
  useEffect(() => {
    if (!showOwnSalary) return; // yrkessidan: läs aldrig sessionStorage, ingen hero
    const read = () => {
      try {
        const raw = sessionStorage.getItem(STORAGE_KEY);
        const n = raw ? Number(raw.replace(/\D/g, "")) : NaN;
        setSalary(Number.isFinite(n) && n > 0 ? n : null);
      } catch {
        setSalary(null);
      }
    };
    read();
    window.addEventListener("offlon:egen-lon", read);
    return () => window.removeEventListener("offlon:egen-lon", read);
  }, [showOwnSalary]);

  const axisMin = p10 * 0.92;
  const axisMax = p90 * 1.08;
  const span = axisMax - axisMin || 1;
  const pos = (v: number) =>
    Math.max(0, Math.min(100, ((v - axisMin) / span) * 100));

  const p10x = pos(p10);
  const p25x = pos(p25);
  const medx = pos(median);
  const p75x = pos(p75);
  const p90x = pos(p90);
  const userX = salary != null ? pos(salary) : null;

  const bottomLabel = (
    x: number,
    value: number,
    caption: string,
    strong = false,
  ) => {
    const align = x < 12 ? "left" : x > 88 ? "right" : "center";
    return (
      <div
        key={caption}
        style={{ position: "absolute", left: `${x}%`, top: CENTER + 20, transform: edgeTransform(x) }}
        className="whitespace-nowrap"
      >
        <div
          className={`tnum text-[11px] leading-none ${
            strong ? "font-semibold text-gray-900" : "text-gray-600"
          }`}
          style={{ textAlign: align }}
        >
          {fmt(value)}
        </div>
        <div
          className="text-[9.5px] leading-tight text-gray-400 mt-0.5"
          style={{ textAlign: align }}
        >
          {caption}
        </div>
      </div>
    );
  };

  return (
    <figure className="my-5">
      <div className="relative w-full" style={{ height: HEIGHT }}>
        {/* Ljus teal-band: 10:e–90:e */}
        <div
          className="absolute rounded-full"
          style={{
            left: `${p10x}%`,
            width: `${p90x - p10x}%`,
            top: CENTER - 6,
            height: 12,
            background: "#96BEC6",
          }}
        />
        {/* Primär teal-band: 25:e–75:e */}
        <div
          className="absolute rounded-full"
          style={{
            left: `${p25x}%`,
            width: `${p75x - p25x}%`,
            top: CENTER - 11,
            height: 22,
            background: "#166F81",
          }}
        />

        {/* Median – tunt tickmärke (sekundärt) */}
        <div
          className="absolute"
          style={{
            left: `${medx}%`,
            top: CENTER - 9,
            height: 18,
            width: 2,
            transform: "translateX(-1px)",
            background: "#13201F",
            opacity: 0.55,
          }}
        />

        {/* DIN LÖN – hero: kraftig linje + fylld etikett + pil. Etiketten är
            förankrad vid linjens x (kantmedveten) så de aldrig glider isär. */}
        {userX != null && salary != null && (
          <>
            <div
              style={{
                position: "absolute",
                left: `${userX}%`,
                top: 6,
                transform: edgeTransform(userX),
              }}
              className="whitespace-nowrap"
            >
              <span className="tnum inline-block rounded-md bg-brand px-2.5 py-1 text-[12px] font-semibold text-white shadow-sm">
                Din lön · {fmt(salary)}
              </span>
            </div>
            {/* Kraftig lodrät linje ned genom bandet */}
            <div
              style={{
                position: "absolute",
                left: `${userX}%`,
                top: 30,
                height: CENTER - 30 + 18,
                width: 3,
                transform: "translateX(-1.5px)",
                background: "#13201F",
              }}
            />
            {/* Pil ned mot bandet */}
            <div
              style={{
                position: "absolute",
                left: `${userX}%`,
                top: 28,
                transform: "translateX(-50%)",
                width: 0,
                height: 0,
                borderLeft: "5px solid transparent",
                borderRight: "5px solid transparent",
                borderTop: "7px solid #13201F",
              }}
            />
            {/* Kraftig punkt där linjen korsar bandet (vit ring) */}
            <div
              style={{
                position: "absolute",
                left: `${userX}%`,
                top: CENTER,
                transform: "translate(-50%, -50%)",
                width: 18,
                height: 18,
                borderRadius: "9999px",
                background: "#13201F",
                border: "3px solid #FFFFFF",
                boxShadow: "0 0 0 1.5px #13201F",
              }}
            />
          </>
        )}

        {/* Nedre värdeetiketter */}
        {bottomLabel(p10x, p10, "10:e perc.")}
        {bottomLabel(medx, median, "median", true)}
        {bottomLabel(p75x, p75, "75:e perc.")}
        {bottomLabel(p90x, p90, "90:e perc.")}
      </div>

      <figcaption className="text-xs text-gray-500 mt-1">
        Det mörka bandet visar var hälften av alla löner ligger:{" "}
        <span className="tnum">
          {fmt(p25)}–{fmt(p75)}
        </span>
        .
      </figcaption>
    </figure>
  );
}
