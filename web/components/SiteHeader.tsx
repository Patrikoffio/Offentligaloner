// Sajthuvud – renderas på varje sida via layouten. Döljs vid utskrift
// (print:hidden) så lönerapporten trycks utan navigering.
// Logotyp: v1-identitetens transparenta SVG (symbol + ordbild i ett).
import Link from "next/link";

export default function SiteHeader() {
  return (
    <header className="print:hidden border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <Link href="/" className="flex items-center group shrink-0" aria-label="Offentliga löner – startsida">
          {/* Hela loggan (symbol + ordbild + tagline) på ALLA bredder.
              Ordmärket får aldrig döljas. Mätt: h-8 (131 px) ryms vid 320 px
              med 47 px marginal när navet trimmas < sm (se nedan). Skulle en
              framtida bredare logga inte rymmas vid 320 – krymp höjden
              proportionellt, dölj aldrig namnet. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/offlon-logo.svg"
            alt="Offentliga löner"
            className="h-8 w-auto"
          />
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          <Link
            href="/#sok"
            className="text-gray-600 hover:text-brand-dark px-2 py-2 rounded transition-colors whitespace-nowrap"
          >
            Beställ rapport
          </Link>
          {/* "Om tjänsten" döljs < sm för att ge ordmärket plats; nås via
              footern. Från sm ryms hela navet. */}
          <span aria-hidden className="hidden sm:inline text-gray-300">
            ·
          </span>
          <Link
            href="/om-tjansten"
            className="hidden sm:inline-flex text-gray-600 hover:text-brand-dark px-2 py-2 rounded transition-colors"
          >
            Om tjänsten
          </Link>
        </nav>
      </div>
    </header>
  );
}
