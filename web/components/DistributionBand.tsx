// Spridningsband för en yrkestitel (lönerapporten).
//
//   ▸ ljus teal-band  = 10:e–90:e percentilen (hela spannet)
//   ▸ primär teal-band= 25:e–75:e percentilen (var hälften ligger), tjockare
//   ▸ mörk linje      = median
//   ▸ mörk teal-punkt = vald kommuns median, med vit ring + pil + etikett ovanför
//   ▸ värdeetiketter  = 10:e perc./median/75:e perc./90:e perc. under bandet
//
// Skala: 10:e perc −8 % till 90:e perc +8 %. Ren rendering, inga schemaändringar.

interface Props {
  p10: number;
  p25: number;
  median: number;
  p75: number;
  p90: number;
  employer?: { name: string; value: number } | null;
  formatSalary: (n: number) => string;
}

const CENTER = 74; // bandets mittlinje (px från containerns topp)

export default function DistributionBand({
  p10,
  p25,
  median,
  p75,
  p90,
  employer,
  formatSalary,
}: Props) {
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
  const empx = employer ? pos(employer.value) : null;
  // Etiketten centreras men klampas så den aldrig svämmar ut / skymmer.
  const labelLeft = empx == null ? 0 : Math.max(15, Math.min(85, empx));

  // Nedre värdeetikett: kantjustera vid ytterlägena så de inte klipps.
  const bottomLabel = (
    x: number,
    value: number,
    caption: string,
    strong = false,
  ) => {
    const align = x < 12 ? "left" : x > 88 ? "right" : "center";
    const transform =
      align === "left"
        ? "translateX(0)"
        : align === "right"
          ? "translateX(-100%)"
          : "translateX(-50%)";
    return (
      <div
        key={caption}
        style={{ position: "absolute", left: `${x}%`, top: CENTER + 20, transform }}
        className="whitespace-nowrap"
      >
        <div
          className={`tnum text-[11px] leading-none ${
            strong ? "font-semibold text-gray-900" : "text-gray-700"
          }`}
          style={{ textAlign: align }}
        >
          {formatSalary(value)}
        </div>
        <div className="text-[9.5px] leading-tight text-gray-400 mt-0.5" style={{ textAlign: align }}>
          {caption}
        </div>
      </div>
    );
  };

  return (
    <figure className="my-5">
      <div className="relative w-full" style={{ height: 150 }}>
        {/* Ljusblått band: 10:e–90:e */}
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
        {/* Primär teal-band: 25:e–75:e (tjockare) */}
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
        {/* Medianlinje */}
        <div
          className="absolute"
          style={{
            left: `${medx}%`,
            top: CENTER - 16,
            height: 32,
            width: 2,
            transform: "translateX(-1px)",
            background: "#13201F",
          }}
        />

        {/* Kommun-punkt (mörk teal) + etikett + pil (ovanför bandet) */}
        {empx != null && employer && (
          <>
            <div
              style={{
                position: "absolute",
                left: `${labelLeft}%`,
                top: CENTER - 52,
                transform: "translateX(-50%)",
              }}
              className="whitespace-nowrap"
            >
              <span className="tnum inline-block rounded-full border border-accent-strong bg-white px-2.5 py-1 text-[11px] font-medium text-accent-dark shadow-sm">
                {employer.name} · {formatSalary(employer.value)}
              </span>
            </div>
            {/* Pil ned mot punkten (sitter vid punktens x, ej etikettens) */}
            <div
              style={{
                position: "absolute",
                left: `${empx}%`,
                top: CENTER - 20,
                transform: "translateX(-50%)",
                width: 0,
                height: 0,
                borderLeft: "5px solid transparent",
                borderRight: "5px solid transparent",
                borderTop: "6px solid #0F5563",
              }}
            />
            {/* Punkt med vit ring */}
            <div
              style={{
                position: "absolute",
                left: `${empx}%`,
                top: CENTER,
                transform: "translate(-50%, -50%)",
                width: 15,
                height: 15,
                borderRadius: "9999px",
                background: "#0F5563",
                border: "3px solid #FFFFFF",
                boxShadow: "0 0 0 1px rgba(15,85,99,0.45)",
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
        Det mörkblå bandet visar var hälften av alla löner ligger:{" "}
        <span className="tnum">
          {formatSalary(p25)}–{formatSalary(p75)}
        </span>
        .
      </figcaption>
    </figure>
  );
}
