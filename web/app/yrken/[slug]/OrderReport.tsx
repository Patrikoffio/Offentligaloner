"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { PaymentTrust, type PaymentLogo } from "@/components/PaymentTrust";

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

// Beställningskomponent (99 kr): två urvalssteg med samma chips-mönster.
//  (a) yrken – snabbval + sökfält med autocomplete (n≥5).
//  (b) kommuner/regioner – sökfält med autocomplete över arbetsgivare.
// Klientstate; pris och validering bestäms server-side i /api/checkout.
export default function OrderReport({
  defaultSlug,
  defaultTitle,
  titleCandidates,
  employers,
  paymentLogos = [],
}: {
  defaultSlug: string;
  defaultTitle: string;
  titleCandidates: TitleOption[];
  employers: EmployerOption[];
  paymentLogos?: PaymentLogo[];
}) {
  const [titles, setTitles] = useState<TitleOption[]>([
    { slug: defaultSlug, title: defaultTitle },
  ]);
  const [emps, setEmps] = useState<EmployerOption[]>([]);
  const [consent, setConsent] = useState(false);
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
    if (!consent)
      return setError(
        "Bekräfta samtycket till omedelbar leverans för att slutföra köpet.",
      );
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slugs: titles.map((t) => t.slug),
          employers: emps.map((e) => e.id),
          consent,
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
        lönespridning och statistik för de kommuner och regioner du väljer.
        <span className="font-medium"> 99 kr.</span>
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

      {/* Vad du får för 99 kr – tre frågor läsaren ställer sig, i klarspråk.
          Teknisk proveniens ligger i den finstilta raden under. Beskriver endast
          innehåll som faktiskt finns i rapportmallen. */}
      <div className="rounded-lg bg-plate-blue p-4 mb-4 text-sm text-gray-700">
        <p className="font-medium text-gray-900 mb-3">
          Ett faktaunderlag att ta med till lönesamtalet
        </p>
        <ul className="space-y-3">
          <li>
            <span className="block font-medium text-gray-900">
              Vad tjänar andra i min roll?
            </span>
            Se lönespridningen för yrket i hela landet – från de lägst till de
            högst betalda.
          </li>
          <li>
            <span className="block font-medium text-gray-900">
              Vad betalar min arbetsgivare?
            </span>
            Se vad din kommun eller region betalar, och hur det står sig mot resten
            av landet.
          </li>
          <li>
            <span className="block font-medium text-gray-900">
              Hur ligger olika yrken och arbetsgivare mot varandra?
            </span>
            Jämför upp till 5 yrken och 5 kommuner eller regioner i samma rapport.
          </li>
        </ul>
        <p className="text-xs text-gray-500 mt-3">
          En löneökning på 500 kr/mån är 6 000 kr på ett år – och följer med varje
          år framåt.
        </p>
        <p className="text-[11px] leading-relaxed text-gray-400 mt-3">
          Bygger på faktiska löner utlämnade enligt offentlighetsprincipen, endast
          där minst 5 anställda har samma roll. 2024 års insamling, omräknat till
          heltidsekvivalent månadslön. Kan skrivas ut eller sparas som PDF; länken
          är giltig i tre månader.
        </p>
      </div>

      {/* Uttryckligt samtycke till omedelbar leverans (ångerrätten upphör).
          Krävs för att kunna slutföra köpet – gate:ar knappen nedan och
          skickas till /api/checkout som validerar den server-side. */}
      <label className="flex items-start gap-2 mb-4 text-xs text-gray-600">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => {
            setConsent(e.target.checked);
            if (e.target.checked) setError(null);
          }}
          className="mt-0.5 h-4 w-4 shrink-0 accent-brand"
        />
        <span>
          Jag samtycker till att rapporten (en digital tjänst) levereras omedelbart
          och är införstådd med att ångerrätten därmed går förlorad. Jag har tagit
          del av{" "}
          <Link href="/kopvillkor" className="text-brand-mid hover:underline">
            köpvillkoren
          </Link>{" "}
          och{" "}
          <Link href="/integritetspolicy" className="text-brand-mid hover:underline">
            integritetspolicyn
          </Link>
          .
        </span>
      </label>

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <button
        onClick={order}
        disabled={
          loading || titles.length === 0 || emps.length === 0 || !consent
        }
        className="bg-brand text-white text-sm px-5 py-2.5 rounded-lg hover:opacity-90 disabled:opacity-50"
      >
        {loading
          ? "Öppnar betalning…"
          : emps.length === 0
            ? "Välj kommun för att beställa"
            : "Beställ lönerapport (99 kr)"}
      </button>

      <PaymentTrust logos={paymentLogos} />

      <p className="text-xs text-gray-400 mt-3 text-center">
        Rapporten bygger på aggregerad statistik (minst 5 individer) – ingen
        individdata.
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
          className="inline-flex items-center gap-1 bg-brand text-white text-xs rounded-full pl-3 pr-1 py-1"
        >
          {it.label}
          <button
            type="button"
            onClick={() => onRemove(it.key)}
            aria-label={`Ta bort ${it.label}`}
            className="ml-1 h-4 w-4 rounded-full hover:bg-brand-mid flex items-center justify-center"
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
        className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:bg-gray-100"
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
                className="w-full text-left px-3 py-2 text-sm hover:bg-plate-blue"
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
        className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:bg-gray-100"
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
                className="w-full text-left px-3 py-2 text-sm hover:bg-plate-blue"
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

// Diskret B2B-rad (exporteras för att placeras längst ner på yrkessidan). Egen
// avgränsad yta med svag bakgrund, skild från källhänvisningen. "Kontakta oss" är
// en mailto-länk med förifylld ämnesrad. Ingen knapp, ingen ram.
export function ContactLine() {
  return (
    <div className="mt-8 rounded-lg bg-gray-50 px-4 py-3 text-xs leading-relaxed text-gray-500">
      Arbetsgivare, forskare eller journalist? Vi levererar bredare uttag – fler
      yrken, hela landet, flera insamlingsår.{" "}
      <a
        href={`mailto:${CONTACT_EMAIL}?subject=Datauttag`}
        className="text-brand-mid hover:underline"
      >
        Kontakta oss
      </a>
      .
    </div>
  );
}
