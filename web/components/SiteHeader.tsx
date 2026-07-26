// Sajthuvud – renderas på varje sida via layouten. Döljs vid utskrift
// (print:hidden) så lönerapporten trycks utan navigering.
// Logotyp: v1-identitetens transparenta SVG (symbol + ordbild i ett).
import Link from "next/link";

export default function SiteHeader() {
  return (
    <header className="print:hidden border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <Link href="/" className="flex items-center group" aria-label="Offentliga löner – startsida">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/offlon-logo.svg"
            alt="Offentligalöner.se"
            className="h-8 w-auto"
          />
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          <Link
            href="/#sok"
            className="text-gray-600 hover:text-brand-dark px-2 py-1 rounded transition-colors"
          >
            Beställ rapport
          </Link>
          <span aria-hidden className="text-gray-300">
            ·
          </span>
          <Link
            href="/om-tjansten"
            className="text-gray-600 hover:text-brand-dark px-2 py-1 rounded transition-colors"
          >
            Om tjänsten
          </Link>
        </nav>
      </div>
    </header>
  );
}
