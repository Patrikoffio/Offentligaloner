"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { PaymentTrust, type PaymentLogo } from "@/components/PaymentTrust";

interface TitleHit {
  slug: string;
  title: string;
}

const STEPS = [
  { n: 1, title: "Sök ditt yrke", body: (titles: string) => `bland ${titles} yrkestitlar med lönestatistik.` },
  {
    n: 2,
    title: "Välj upp till 5 yrken och 5 kommuner",
    body: () => "jämför det som är relevant för just dig.",
  },
  {
    n: 3,
    title: "Få din lönerapport på mejlen – 99 kr",
    body: () => "betala med Klarna eller kort.",
  },
];

// Startsidans övre del (hero + sök + nyckeltal + "så funkar det" + betalförtroende).
// Klientkomponent: sökfält med autocomplete (samma /api/search/titles som
// beställnings-UI:t) och "så funkar det"-kort som fokuserar sökfältet.
export default function HomeTop({
  count_salaries,
  count_employers,
  count_titles,
  paymentLogos = [],
}: {
  count_salaries: number;
  count_employers: number;
  count_titles: number;
  paymentLogos?: PaymentLogo[];
}) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [q, setQ] = useState("");
  const [results, setResults] = useState<TitleHit[]>([]);
  const [open, setOpen] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const nf = (n: number) => n.toLocaleString("sv-SE");
  const titlesFmt = nf(count_titles);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    if (q.trim().length < 2) {
      setResults([]);
      return;
    }
    timer.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/search/titles?q=${encodeURIComponent(q.trim())}`,
        );
        const data = (await res.json()) as { results?: TitleHit[] };
        setResults(data.results ?? []);
        setOpen(true);
      } catch {
        setResults([]);
      }
    }, 250);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [q]);

  function focusSearch() {
    inputRef.current?.focus();
    inputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  const stats = [
    { value: nf(count_salaries), label: "Löneuppgifter" },
    { value: nf(count_employers), label: "Kommuner och regioner" },
    { value: titlesFmt, label: "Yrkestitlar med lönestatistik" },
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 pt-14 pb-10">
      {/* Hero */}
      <h1 className="font-serif text-4xl sm:text-5xl leading-tight text-gray-900 text-center">
        Vad tjänar man egentligen?
      </h1>
      <p className="text-gray-600 text-center max-w-xl mx-auto mt-4 text-[15px] leading-relaxed">
        Faktiska löner från kommuner och regioner, utlämnade enligt
        offentlighetsprincipen. Inga enkäter, inga uppskattningar.
      </p>
      <p className="text-gray-400 text-center max-w-xl mx-auto mt-2 text-xs leading-relaxed">
        Utlämnade av {nf(count_employers)} kommuner och regioner under 2024 års
        insamling. Publicerad under utgivningsbevis nr 2024-077.
      </p>

      {/* Sökfält */}
      <div className="relative mt-8" id="sok">
        <input
          ref={inputRef}
          type="text"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder={`Sök bland ${titlesFmt} yrkestitlar – t.ex. undersköterska`}
          aria-label="Sök yrkestitel"
          className="w-full rounded-[10px] border-[1.5px] border-brand px-4 py-3.5 text-base text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand/25"
        />
        {open && results.length > 0 && (
          <ul className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-md max-h-72 overflow-auto">
            {results.map((r) => (
              <li key={r.slug}>
                <button
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    router.push(`/yrken/${r.slug}`);
                  }}
                  className="w-full text-left px-4 py-2.5 text-sm hover:bg-plate-blue"
                >
                  {r.title}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Nyckeltal ur datan */}
      <div className="grid grid-cols-3 gap-3 mt-6">
        {stats.map((s) => (
          <div
            key={s.label}
            className="bg-plate-blue rounded-lg px-3 py-4 text-center"
          >
            <div className="tnum text-2xl sm:text-3xl font-semibold text-brand leading-none">
              {s.value}
            </div>
            <div className="text-xs text-gray-500 mt-1.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Så funkar det */}
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mt-9 mb-3">
        Så funkar det
      </h2>
      <div className="grid gap-3 sm:grid-cols-3">
        {STEPS.map((step) => (
          <button
            key={step.n}
            type="button"
            onClick={focusSearch}
            className="text-left rounded-lg border border-gray-200 p-4 hover:border-brand hover:bg-plate-blue/50 transition-colors"
          >
            <span className="inline-flex items-center justify-center h-7 w-7 rounded-full bg-brand text-white text-sm font-semibold">
              {step.n}
            </span>
            <div className="font-medium text-gray-900 mt-2.5 text-sm">
              {step.title}
            </div>
            <div className="text-xs text-gray-500 mt-1 leading-relaxed">
              {step.body(titlesFmt)}
            </div>
          </button>
        ))}
      </div>

      {/* Betalförtroende */}
      <PaymentTrust logos={paymentLogos} />
    </div>
  );
}
