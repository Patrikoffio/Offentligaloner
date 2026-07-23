"use client";

import { useEffect, useRef, useState } from "react";

export interface TitleOption {
  slug: string;
  title: string;
}
export interface EmployerOption {
  id: number;
  name: string;
}

const MAX_TITLES = 5;
const MAX_EMPLOYERS = 5;
const CONTACT_EMAIL = "kontakt@offentligaloner.se";

// Beställningskomponent (39 kr): två urvalssteg med samma chips-mönster.
//  (a) yrken – snabbval + sökfält med autocomplete (n≥5).
//  (b) kommuner/regioner – sökfält med autocomplete över arbetsgivare.
// Klientstate; pris och validering bestäms server-side i /api/checkout.
export default function OrderReport({
  defaultSlug,
  defaultTitle,
  titleCandidates,
  employers,
}: {
  defaultSlug: string;
  defaultTitle: string;
  titleCandidates: TitleOption[];
  employers: EmployerOption[];
}) {
  const [titles, setTitles] = useState<TitleOption[]>([
    { slug: defaultSlug, title: defaultTitle },
  ]);
  const [emps, setEmps] = useState<EmployerOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const titleSlugs = new Set(titles.map((t) => t.slug));
  const empIds = new Set(emps.map((e) => e.id));

  function addTitle(t: TitleOption) {
    setError(null);
    setTitles((prev) =>
      prev.some((x) => x.slug === t.slug) || prev.length >= MAX_TITLES
        ? prev
        : [...prev, t],
    );
  }
  function removeTitle(slug: string) {
    setTitles((prev) => prev.filter((t) => t.slug !== slug));
  }
  function addEmp(e: EmployerOption) {
    setError(null);
    setEmps((prev) =>
      prev.some((x) => x.id === e.id) || prev.length >= MAX_EMPLOYERS
        ? prev
        : [...prev, e],
    );
  }
  function removeEmp(id: number) {
    setEmps((prev) => prev.filter((e) => e.id !== id));
  }

  async function order() {
    if (titles.length === 0) return setError("Välj minst ett yrke.");
    if (emps.length === 0) return setError("Välj minst en kommun/region.");
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slugs: titles.map((t) => t.slug),
          employers: emps.map((e) => e.id),
        }),
      });
      const data = (await res.json()) as { url?: string; error?: string };
      if (!res.ok || !data.url) {
        setError(data.error ?? "Kunde inte starta betalningen. Försök igen.");
        setLoading(false);
        return;
      }
      window.location.href = data.url; // → Stripe Checkout
    } catch {
      setError("Nätverksfel. Försök igen.");
      setLoading(false);
    }
  }

  const titlesFull = titles.length >= MAX_TITLES;
  const empsFull = emps.length >= MAX_EMPLOYERS;

  return (
    <section className="border border-gray-200 rounded-lg p-5 mb-4 bg-gray-50">
      <h2 className="text-lg font-semibold mb-1">Beställ lönerapport</h2>
      <p className="text-sm text-gray-600 mb-5">
        Välj upp till {MAX_TITLES} yrken och upp till {MAX_EMPLOYERS} kommuner/regioner.
        Du får en samlad, PDF-vänlig rapport (giltig i tre månader) med nationell
        lönespridning och statistik för dina valda arbetsgivare.
        <span className="font-medium"> 39 kr.</span>
      </p>

      {/* ── Steg (a): yrken ───────────────────────────────────────────────── */}
      <div className="mb-6">
        <p className="text-sm font-medium text-gray-800 mb-2">
          1. Yrken <span className="text-gray-400">({titles.length}/{MAX_TITLES})</span>
        </p>
        <Chips items={titles.map((t) => ({ key: t.slug, label: t.title }))} onRemove={(k) => removeTitle(k)} />

        {/* Snabbval: syskon i kategorin */}
        {titleCandidates.filter((c) => !titleSlugs.has(c.slug)).length > 0 && !titlesFull && (
          <div className="flex flex-wrap gap-2 mt-2 mb-2">
            {titleCandidates
              .filter((c) => !titleSlugs.has(c.slug))
              .map((c) => (
                <button
                  key={c.slug}
                  type="button"
                  onClick={() => addTitle(c)}
                  className="text-xs border border-gray-300 rounded-full px-3 py-1 hover:bg-white text-gray-700"
                >
                  + {c.title}
                </button>
              ))}
          </div>
        )}

        <TitleSearch onPick={addTitle} disabled={titlesFull} chosen={titleSlugs} />
        {titlesFull && (
          <p className="text-xs text-gray-400 mt-1">Max {MAX_TITLES} yrken valda.</p>
        )}
      </div>

      {/* ── Steg (b): kommuner/regioner ───────────────────────────────────── */}
      <div className="mb-6">
        <p className="text-sm font-medium text-gray-800 mb-2">
          2. Kommuner/regioner{" "}
          <span className="text-gray-400">({emps.length}/{MAX_EMPLOYERS})</span>
        </p>
        <Chips items={emps.map((e) => ({ key: String(e.id), label: e.name }))} onRemove={(k) => removeEmp(Number(k))} />
        <EmployerSearch
          employers={employers}
          onPick={addEmp}
          disabled={empsFull}
          chosen={empIds}
        />
        {emps.length === 0 && (
          <p className="text-xs text-gray-400 mt-1">Välj minst en kommun eller region.</p>
        )}
        {empsFull && (
          <p className="text-xs text-gray-400 mt-1">Max {MAX_EMPLOYERS} kommuner/regioner valda.</p>
        )}
      </div>

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <button
        onClick={order}
        disabled={loading || titles.length === 0 || emps.length === 0}
        className="bg-blue-600 text-white text-sm px-5 py-2.5 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Öppnar betalning…" : "Beställ lönerapport (39 kr)"}
      </button>
      <p className="text-xs text-gray-400 mt-3">
        Betalning via kort eller Klarna. Rapporten bygger på aggregerad statistik
        (minst 5 individer) – ingen individdata.
      </p>
    </section>
  );
}

// ── Chips ─────────────────────────────────────────────────────────────────────
function Chips({
  items,
  onRemove,
}: {
  items: { key: string; label: string }[];
  onRemove: (key: string) => void;
}) {
  if (items.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2 mb-2">
      {items.map((it) => (
        <span
          key={it.key}
          className="inline-flex items-center gap-1 bg-blue-600 text-white text-xs rounded-full pl-3 pr-1 py-1"
        >
          {it.label}
          <button
            type="button"
            onClick={() => onRemove(it.key)}
            aria-label={`Ta bort ${it.label}`}
            className="ml-1 h-4 w-4 rounded-full hover:bg-blue-700 flex items-center justify-center"
          >
            ×
          </button>
        </span>
      ))}
    </div>
  );
}

// ── Titel-autocomplete (serversök) ─────────────────────────────────────────────
function TitleSearch({
  onPick,
  disabled,
  chosen,
}: {
  onPick: (t: TitleOption) => void;
  disabled: boolean;
  chosen: Set<string>;
}) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<TitleOption[]>([]);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    if (q.trim().length < 2) {
      setResults([]);
      return;
    }
    timer.current = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search/titles?q=${encodeURIComponent(q.trim())}`);
        const data = (await res.json()) as { results?: TitleOption[] };
        setResults(data.results ?? []);
      } catch {
        setResults([]);
      }
    }, 250);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [q]);

  const visible = results.filter((r) => !chosen.has(r.slug));

  return (
    <div className="relative">
      <input
        type="text"
        value={q}
        disabled={disabled}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Sök fler yrken…"
        className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
      />
      {visible.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded shadow-sm max-h-56 overflow-auto">
          {visible.map((r) => (
            <li key={r.slug}>
              <button
                type="button"
                onClick={() => {
                  onPick(r);
                  setQ("");
                  setResults([]);
                }}
                className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50"
              >
                {r.title}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ── Arbetsgivar-autocomplete (klientfilter över inpassad lista) ─────────────────
function EmployerSearch({
  employers,
  onPick,
  disabled,
  chosen,
}: {
  employers: EmployerOption[];
  onPick: (e: EmployerOption) => void;
  disabled: boolean;
  chosen: Set<number>;
}) {
  const [q, setQ] = useState("");
  const term = q.trim().toLowerCase();
  const visible =
    term.length < 1
      ? []
      : employers
          .filter((e) => !chosen.has(e.id) && e.name.toLowerCase().includes(term))
          .slice(0, 10);

  return (
    <div className="relative">
      <input
        type="text"
        value={q}
        disabled={disabled}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Sök kommun eller region…"
        className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
      />
      {visible.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded shadow-sm max-h-56 overflow-auto">
          {visible.map((e) => (
            <li key={e.id}>
              <button
                type="button"
                onClick={() => {
                  onPick(e);
                  setQ("");
                }}
                className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50"
              >
                {e.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// Diskret kontaktrad under modulen (exporteras för att kunna placeras separat).
export function ContactLine() {
  return (
    <p className="text-xs text-gray-500 mb-10">
      Behöver du fler yrken, hela landet eller fullständiga datauttag?{" "}
      <a href={`mailto:${CONTACT_EMAIL}`} className="text-blue-600 hover:underline">
        Kontakta oss
      </a>
      .
    </p>
  );
}
