// Sajthuvud – renderas på varje sida via layouten. Döljs vid utskrift
// (print:hidden) så lönerapporten trycks utan navigering.
import Link from "next/link";
import Logo from "./Logo";

export default function SiteHeader() {
  return (
    <header className="print:hidden border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2.5 group">
          <Logo size={32} />
          <span className="text-brand font-medium text-lg tracking-tight">
            Offentliga löner
          </span>
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          <Link
            href="/#sok"
            className="text-gray-600 hover:text-brand px-2 py-1 rounded transition-colors"
          >
            Beställ rapport
          </Link>
          <span aria-hidden className="text-gray-300">
            ·
          </span>
          <Link
            href="/om-tjansten"
            className="text-gray-600 hover:text-brand px-2 py-1 rounded transition-colors"
          >
            Om tjänsten
          </Link>
        </nav>
      </div>
    </header>
  );
}
